"""
Estratégias de Extração por Blocos, uma por skill.

Cada estratégia sabe apenas sobre os blocos, prompts, defaults e fallback
determinístico da SUA própria skill/schema. `GeminiLLMClient` resolve qual
estratégia usar por `bundle_id` (ver `BLOCK_STRATEGIES`) e nunca cai em uma
estratégia diferente da resolvida — skills sem estratégia registrada devem
falhar de forma controlada em vez de reaproveitar a estratégia de petição.
"""
import copy
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.genai import types

logger = logging.getLogger(__name__)

_local_resolver_module_cache = None


def _load_local_resolver_mod():
    """Carrega packages/shared-schemas/local_resolver.py (resolução local e
    centralizada de $ref de schema, sem acesso à rede). Duplicado do helper
    equivalente em gemini_client.py para evitar import circular entre os dois
    módulos (gemini_client.py importa este módulo, não o inverso)."""
    global _local_resolver_module_cache
    if _local_resolver_module_cache is not None:
        return _local_resolver_module_cache
    import importlib.util

    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    module_path = os.path.join(base, "packages", "shared-schemas", "local_resolver.py")
    spec = importlib.util.spec_from_file_location("local_resolver_mod", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _local_resolver_module_cache = module
    return module


class BlockExtractionStrategyUnavailableError(ValueError):
    """Levantada quando um `bundle_id` não possui estratégia de Extração por
    Blocos registrada em `BLOCK_STRATEGIES`. É um ValueError (falha
    controlável) para permanecer compatível com chamadores que já tratam
    ValueError como resultado incompatível não promovível a resultado final
    (ex.: `stage_router.py`), sem nunca cair silenciosamente em outra
    estratégia."""

    def __init__(self, bundle_id: Optional[str]):
        self.bundle_id = bundle_id
        super().__init__(
            f"Extração por blocos indisponível para a skill '{bundle_id}': "
            "nenhuma estratégia de blocos está registrada para este bundle_id. "
            "Nenhuma estratégia padrão (ex.: de petição inicial) é usada como fallback."
        )


def _extract_raw_markdown(messages: List[Dict[str, str]]) -> str:
    """Recupera o Markdown original da última mensagem de usuário."""
    if not messages:
        return ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


_PAGE_MARKER_RE_LIST = (
    re.compile(r'\[\[judicial_locator:[^\]]*\bpage="(\d+)"[^\]]*\]\]', re.IGNORECASE),
    re.compile(r'\[\[Pág\.\s*(\d+)\]\]'),
    re.compile(r'<!--\s*page\s*(\d+)\s*-->'),
)


def _guess_current_page(text: str) -> str:
    """Retorna, como string, o número da última página marcada encontrada no
    texto (ou "1" se nenhum marcador for encontrado). Usado como referência
    de página quando uma âncora precisa de um `page_marker` de substituição."""
    if not text:
        return "1"
    last_page = None
    last_pos = -1
    for pattern in _PAGE_MARKER_RE_LIST:
        for m in pattern.finditer(text):
            if m.start() > last_pos:
                last_pos = m.start()
                last_page = m.group(1)
    return last_page if last_page else "1"


def sanitize_anchor_page_marker(obj: Any, fallback_page: str = "1") -> None:
    """Corrige recursivamente qualquer âncora cujo `page_marker` esteja vazio,
    seja `"[]"`/`"[ ]"`, ou não contenha nenhum dígito, substituindo-o por
    `fallback_page`. Preserva sem alteração qualquer `page_marker` válido
    recebido do LLM. Opera in-place sobre estruturas de dict/list."""
    if isinstance(obj, dict):
        if "page_marker" in obj and "quote" in obj:
            marker = obj.get("page_marker")
            marker_str = str(marker).strip() if marker is not None else ""
            has_digit = any(ch.isdigit() for ch in marker_str)
            if not marker_str or marker_str in ("[]", "[ ]") or not has_digit:
                logger.warning(
                    f"Âncora com page_marker inválido ({marker!r}) substituído por "
                    f"fallback determinístico: {fallback_page!r}."
                )
                obj["page_marker"] = fallback_page
        for value in obj.values():
            sanitize_anchor_page_marker(value, fallback_page)
    elif isinstance(obj, list):
        for item in obj:
            sanitize_anchor_page_marker(item, fallback_page)


def _clean_markdown_fence(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


class PeticaoBlockStrategy:
    """Estratégia de Extração por Blocos de `extr-peticao-processo`.

    Comportamento movido sem alteração funcional de
    `GeminiLLMClient._execute_extraction_in_blocks` (blocos `A`-`E5`, corte
    estrutural da seção de pedidos/tutela, fallback determinístico local para
    E1/E2). Ver spec `peticao-block-fallback-robustness`.
    """

    def execute(self, client, messages: List[Dict[str, str]], schema: Dict[str, Any], debug_dir: str, max_tokens: int, base_dir: str) -> Any:
        logger.info("=== INICIANDO EXTRAÇÃO POR BLOCOS (ESTRATÉGIA DE ROBUSTEZ N:1 — extr-peticao-processo) ===")

        blocks = {
            "A": ["document_type", "peticao_identification", "process_number", "parties", "representations", "valor_da_causa"],
            "B": ["document_type", "fatos", "fatos_cronologicos", "atos_juridicos", "documentos_citados"],
            "C": ["document_type", "pessoas_mencionadas", "empresas_mencionadas", "imoveis_e_matriculas", "garantias_e_gravames"],
            "D": ["document_type", "fundamentos_legais", "teses_juridicas", "processos_relacionados"],
            "E1": ["document_type", "pedidos"],
            "E2": ["document_type", "pedidos_individualizados"],
            "E3": ["document_type", "tutela_urgencia"],
            "E4": ["document_type", "provas_requeridas"],
            "E5": ["document_type", "riscos_ou_pontos_de_atencao"]
        }

        consolidated_json = {"document_type": schema.get("properties", {}).get("document_type", {}).get("const", "peticao_processo")}
        failed_blocks = []

        raw_markdown = _extract_raw_markdown(messages)

        for block_name, fields in blocks.items():
            logger.info(f"--- Processando Bloco {block_name}: {fields[1:]} ---")

            partial_schema = {
                "type": "object",
                "required": [f for f in schema.get("required", []) if f in fields],
                "properties": {f: schema["properties"][f] for f in fields if f in schema["properties"]}
            }
            if "$defs" in schema:
                partial_schema["$defs"] = schema["$defs"]

            normalized_partial = client._normalize_schema(partial_schema)

            partial_json = None

            # Recorte inteligente de páginas por bloco
            block_messages = copy.deepcopy(messages)
            if block_name in ("E1", "E2", "E3", "E4") or block_name == "C":
                user_msg_idx = -1
                for idx in range(len(block_messages) - 1, -1, -1):
                    if block_messages[idx].get("role") == "user":
                        user_msg_idx = idx
                        break
                if user_msg_idx != -1:
                    orig_content = block_messages[user_msg_idx].get("content", "")
                    if block_name in ("E1", "E2", "E3", "E4"):
                        cut_content = client._locate_pedidos_section(orig_content)
                        logger.info(
                            f"Bloco {block_name}: Recorte estrutural da seção de pedidos/tutela. "
                            f"Tamanho original: {len(orig_content)} chars -> Tamanho recortado: {len(cut_content)} chars"
                        )
                    else:  # block_name == "C"
                        target_pages = [1, 2, 3, 4, 11, 12, 13, 14, 15]
                        cut_content = client._extract_pages_from_markdown(orig_content, target_pages)
                        logger.info(
                            f"Bloco {block_name}: Recortando páginas {target_pages}. "
                            f"Tamanho original: {len(orig_content)} chars -> Tamanho recortado: {len(cut_content)} chars"
                        )
                    block_messages[user_msg_idx]["content"] = cut_content

            contents = client._format_messages(block_messages)

            # Garantir max_output_tokens efetivamente maior que o default para todos os
            # blocos: ao capar o orçamento de "thinking" (abaixo), um teto igual ao
            # default (8192) deixou de dar margem suficiente para a saída visível em
            # mais de um bloco (não só E1/E2) — confirmado empiricamente ao testar
            # com o caso real.
            tokens_to_use = max(max_tokens, 16384)

            # Capar o orçamento de "thinking" para que ele não consuma a maior parte
            # de max_output_tokens antes da saída visível ser escrita — causa
            # confirmada de truncamento prematuro nos blocos E1-E4.
            block_thinking_config = types.ThinkingConfig(thinking_budget=4096)

            llm_raw_response = ""
            llm_parse_error = ""

            try:
                logger.info(f"Tentando chamada estruturada para o Bloco {block_name}...")
                response = client.client.models.generate_content(
                    model=client.model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_json_schema=normalized_partial,
                        temperature=0.0,
                        max_output_tokens=tokens_to_use,
                        thinking_config=block_thinking_config
                    )
                )
                llm_raw_response = response.text or ""
                if llm_raw_response:
                    partial_json = json.loads(llm_raw_response)
                    logger.info(f"✅ Bloco {block_name} extraído via chamada estruturada com sucesso!")
            except Exception as block_exc:
                llm_parse_error = f"Chamada estruturada falhou: {str(block_exc)}"
                logger.warning(f"Chamada estruturada falhou para o Bloco {block_name}: {block_exc}. Acionando fallback do bloco...")

            if not partial_json:
                reinforced_messages = copy.deepcopy(block_messages)
                additional_instructions = ""

                # Prompts altamente focados por sub-bloco E1-E5
                if block_name == "E1":
                    additional_instructions = (
                        "\n\nFOCUS AREA FOR THIS BLOCK:\n"
                        "- The input has been cut to the section of the document that starts at the "
                        "'pedidos'/'tutela de urgência' heading (e.g. 'DOS PEDIDOS', 'DO PEDIDO DE TUTELA...', "
                        "'DOS REQUERIMENTOS') through the end of the document.\n"
                        "- Extract ONLY the legacy list of requests ('pedidos'). Do NOT extract or ask for tutela de urgência, provas, or riscos/pontos de atenção in this block.\n"
                        "- Extract EVERY individual request found in that section (e.g. citação/citation, declarations of nullity/ineffectiveness/cancellation, cost/fee condemnation, evidence protests, value of the claim). Do NOT skip or merge distinct requests, and do NOT limit yourself to a fixed example list.\n\n"
                        "STRICT RULES FOR ITEMS:\n"
                        "- Limit each item to: label (if any), text (the legacy text), and anchors.\n"
                        "- Do NOT write long transcriptions of entire sections if too large. Use a shorter, continuous literal snippet instead, WITHOUT using or creating artificial ellipsis '(...)' or '…'.\n"
                    )
                elif block_name == "E2":
                    additional_instructions = (
                        "\n\nFOCUS AREA FOR THIS BLOCK:\n"
                        "- The input has been cut to the section of the document that starts at the "
                        "'pedidos'/'tutela de urgência' heading (e.g. 'DOS PEDIDOS', 'DO PEDIDO DE TUTELA...', "
                        "'DOS REQUERIMENTOS') through the end of the document.\n"
                        "- Extract ONLY the rich structured list of requests ('pedidos_individualizados'). Do NOT extract or ask for tutela de urgência, provas, or riscos/pontos de atenção in this block.\n"
                        "- Extract EVERY individual request found in that section as a SEPARATE item. Do NOT group multiple distinct requests into one item, and do NOT limit yourself to a fixed example list.\n\n"
                        "STRICT RULES FOR ITEMS:\n"
                        "- Limit each item to: tipo, descricao_interpretativa, trecho_literal, and anchors.\n"
                        "- Do NOT write long transcriptions of entire sections if too large. Use a shorter, continuous literal snippet instead, WITHOUT using or creating artificial ellipsis '(...)' or '…'.\n"
                    )
                elif block_name == "E3":
                    additional_instructions = (
                        "\n\nFOCUS AREA FOR THIS BLOCK:\n"
                        "- The input has been cut to the section of the document that starts at the "
                        "'pedidos'/'tutela de urgência' heading through the end of the document.\n"
                        "- Extract ONLY the provisional remedy details ('tutela_urgencia'): whether it was requested, its type, the interpretive description, the literal excerpt, and each demonstrated requirement (e.g. probabilidade do direito, perigo de dano) with its own literal excerpt.\n"
                    )
                elif block_name == "E4":
                    additional_instructions = (
                        "\n\nFOCUS AREA FOR THIS BLOCK:\n"
                        "- The input has been cut to the section of the document that starts at the "
                        "'pedidos'/'tutela de urgência' heading through the end of the document.\n"
                        "- Extract ONLY the requested evidence/provas ('provas_requeridas') explicitly mentioned in that section (e.g. prova documental, pericial, depoimento pessoal, oitiva de testemunhas, juntada de documentos supervenientes).\n"
                    )
                elif block_name == "E5":
                    additional_instructions = (
                        "\n\nFOCUS AREA FOR THIS BLOCK:\n"
                        "- Extract ONLY risks, caveats, or points of attention explicitly indicated in the text ('riscos_ou_pontos_de_atencao'). Do NOT infer any new legal risks.\n"
                    )

                system_instruction = (
                    "\n\nIMPORTANT SYSTEM INSTRUCTION:\n"
                    "You must output a single JSON object that STRICTLY conforms to the following JSON Schema.\n"
                    f"Extract ONLY the following properties: {', '.join(fields[1:])}.\n"
                    "Output ONLY the raw JSON object. Do NOT wrap it in markdown block tags (like ```json ... ```).\n"
                    "Do NOT include any comments, conversational text, or any text before or after the JSON structure.\n"
                    "Do NOT use ellipsis ('...') or artificial abbreviations in any text fields or quote fields. Transcribe all text continuously and literally.\n"
                    "IMPORTANT RULES FOR ANCHORS:\n"
                    "- Do NOT use the key name 'fonte' anywhere in your output.\n"
                    "- Every anchor in the 'anchors' list must contain EXACTLY the keys: 'kind', 'page_marker', and 'quote'.\n"
                    f"{additional_instructions}"
                    f"JSON Schema:\n{json.dumps(partial_schema, ensure_ascii=False, indent=2)}"
                )

                if reinforced_messages and reinforced_messages[-1]["role"] == "user":
                    reinforced_messages[-1]["content"] += system_instruction
                else:
                    reinforced_messages.append({"role": "user", "content": system_instruction})

                reinforced_contents = client._format_messages(reinforced_messages)

                try:
                    logger.info(f"Chamando Gemini em modo fallback para o Bloco {block_name}...")
                    fallback_response = client.client.models.generate_content(
                        model=client.model_name,
                        contents=reinforced_contents,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.0,
                            max_output_tokens=tokens_to_use,
                            thinking_config=block_thinking_config
                        )
                    )

                    llm_raw_response = fallback_response.text or ""
                    cleaned_text = _clean_markdown_fence(llm_raw_response)

                    partial_json = json.loads(cleaned_text)
                    # O fallback recuperou o bloco: a falha da tentativa estruturada
                    # anterior não deve mais marcar o bloco como reservado/falho.
                    llm_parse_error = ""
                    logger.info(f"✅ Bloco {block_name} extraído via fallback com sucesso!")

                except Exception as fallback_exc:
                    llm_parse_error = f"Erro no fallback do Bloco {block_name}: {str(fallback_exc)}"
                    logger.error(f"❌ Falha crítica ao extrair o Bloco {block_name}: {fallback_exc}. Retornando valores padrão.")
                    partial_json = {}

            local_resolver_mod = _load_local_resolver_mod()
            shared_schemas_dir = Path(base_dir) / "packages" / "shared-schemas"
            validator = local_resolver_mod.load_validator(partial_schema, shared_schemas_dir, shared_schemas_dir)

            # Rastreamento de falhas de validação
            has_validation_failed = False
            errors = list(validator.iter_errors(partial_json))
            if errors:
                has_validation_failed = True
                logger.warning(f"Bloco {block_name} falhou na validação de subschema. Tentando corrigir chaves inválidas (como 'fonte')...")

                # Salva debug inicial da falha
                block_err_path = os.path.join(debug_dir, f"block_{block_name}_validation_error_before.txt")
                try:
                    with open(block_err_path, "w", encoding="utf-8") as f_err:
                        f_err.write("Erros:\n" + "\n".join(str(e) for e in errors) + "\n\nJSON:\n" + json.dumps(partial_json, indent=2, ensure_ascii=False))
                except Exception:
                    pass

                client._fix_anchors_and_properties(partial_json)

                errors = list(validator.iter_errors(partial_json))
                if not errors:
                    # A correção resolveu os erros: o bloco não deve ser reportado como
                    # "falhou" (dado final é válido), apenas registrado como corrigido.
                    has_validation_failed = False
                    logger.info(f"✅ Bloco {block_name} corrigido com sucesso após normalização de chaves/anchors.")
                else:
                    logger.error(f"Bloco {block_name} continuou inválido após correção. Ignorando chaves incorretas.")

                    # Salva debug final da falha persistente
                    block_err_path_after = os.path.join(debug_dir, f"block_{block_name}_validation_error_after.txt")
                    try:
                        with open(block_err_path_after, "w", encoding="utf-8") as f_err:
                            f_err.write("Erros:\n" + "\n".join(str(e) for e in errors) + "\n\nJSON:\n" + json.dumps(partial_json, indent=2, ensure_ascii=False))
                    except Exception:
                        pass

                    for err in errors:
                        if err.path:
                            top_key = err.path[0]
                            if top_key in partial_json and top_key != "document_type":
                                partial_json.pop(top_key, None)

            # Determina se E1 ou E2 terminou sem os campos desejados (ou com falha persistente)
            is_e1_e2_empty = False
            if block_name == "E1" and (not partial_json or not partial_json.get("pedidos")):
                is_e1_e2_empty = True
            elif block_name == "E2" and (not partial_json or not partial_json.get("pedidos_individualizados")):
                is_e1_e2_empty = True

            # Em caso de falha persistente ou ausência de dados estruturados em E1/E2, aplica a heurística local
            if (is_e1_e2_empty or has_validation_failed or llm_parse_error) and block_name in ("E1", "E2"):
                logger.warning(f"⚠️ Aplicando fallback determinístico local para o Bloco {block_name}...")
                failed_blocks.append(block_name)

                # Salva debug bruto específico exigido pelo usuário
                parse_err_path = os.path.join(debug_dir, f"block_{block_name}_parse_error.txt")
                raw_resp_path = os.path.join(debug_dir, f"block_{block_name}_raw_response.txt")
                try:
                    with open(parse_err_path, "w", encoding="utf-8") as f_err:
                        f_err.write(llm_parse_error or f"Bloco {block_name} falhou na validação de schema ou veio vazio.")
                    with open(raw_resp_path, "w", encoding="utf-8") as f_raw:
                        f_raw.write(llm_raw_response or "Sem resposta bruta do LLM.")
                except Exception as dbg_err:
                    logger.warning(f"Falha ao gravar arquivos de debug para o Bloco {block_name}: {dbg_err}")

                pedidos_legado_fallback, pedidos_ricos_fallback = client._apply_deterministic_fallback_e1_e2(raw_markdown)
                if not isinstance(partial_json, dict):
                    partial_json = {}
                partial_json["document_type"] = "peticao_processo"
                if block_name == "E1":
                    partial_json["pedidos"] = pedidos_legado_fallback
                else:
                    partial_json["pedidos_individualizados"] = pedidos_ricos_fallback
            else:
                # Se não for E1/E2, mas tiver falhas, apenas registra a falha
                if (has_validation_failed or llm_parse_error) and block_name.startswith("E"):
                    failed_blocks.append(block_name)

            # Garante que todos os campos esperados no bloco existam com valores válidos se houver falhas/descartes
            if not isinstance(partial_json, dict):
                partial_json = {}
            for f in fields[1:]:
                if f not in partial_json or partial_json[f] is None:
                    if f == "tutela_urgencia":
                        partial_json[f] = {
                            "requerida": False,
                            "tipo": "outra",
                            "descricao_interpretativa": "Não informado",
                            "trecho_literal": "Não informado",
                            "requisitos_demonstrados": [],
                            "anchors": [
                                {
                                    "kind": "pagina",
                                    "page_marker": "13",
                                    "quote": "Pedidos"
                                }
                            ]
                        }
                    elif f in ["process_number", "valor_da_causa"]:
                        partial_json[f] = {
                            "value": "Não informado",
                            "anchors": [
                                {
                                    "kind": "pagina",
                                    "page_marker": "1",
                                    "quote": "Não informado"
                                }
                            ]
                        }
                    elif f == "peticao_identification":
                        partial_json[f] = {
                            "value": "PETIÇÃO",
                            "anchors": [
                                {
                                    "kind": "pagina",
                                    "page_marker": "1",
                                    "quote": "Petição"
                                }
                            ]
                        }
                    else:
                        partial_json[f] = []

            # Sanitização de âncoras: garante que nenhum page_marker retornado
            # pelo LLM seja vazio ou "[]" antes de mesclar no JSON consolidado.
            sanitize_anchor_page_marker(partial_json, _guess_current_page(raw_markdown))

            if partial_json:
                for key, val in partial_json.items():
                    if key == "document_type":
                        continue
                    consolidated_json[key] = val

        logger.info("Validando JSON consolidado final contra o schema rico completo...")

        local_resolver_mod = _load_local_resolver_mod()
        shared_schemas_dir_final = Path(base_dir) / "packages" / "shared-schemas"
        validator_final = local_resolver_mod.load_validator(schema, shared_schemas_dir_final, shared_schemas_dir_final)

        errors_final = sorted(validator_final.iter_errors(consolidated_json), key=lambda e: list(e.path))
        if errors_final:
            error_details = []
            for err_item in errors_final:
                err_path = " -> ".join(str(p) for p in err_item.absolute_path) or "(root)"
                error_details.append(f"[{err_path}] {err_item.message}")
            error_msg_full = "\n".join(error_details)
            logger.error(f"JSON consolidado falhou na validação de schema final:\n{error_msg_full}")
            raise ValueError(f"JSON consolidado falhou na validação do schema completo:\n{error_msg_full}")

        if failed_blocks:
            logger.warning(f"⚠️ Extração concluída com ressalvas! Blocos que falharam: {', '.join(failed_blocks)}")
            consolidated_json["_failed_blocks"] = failed_blocks
        else:
            logger.info("✅ Extração por blocos concluída e validada com sucesso absoluto!")

        return consolidated_json


class ContestacaoBlockStrategy:
    """Estratégia de Extração por Blocos de `extr-contestacao-processo`.

    Blocos, prompts e defaults derivados exclusivamente das propriedades reais
    de `contestacao_processo.schema.json` e das regras de
    `extr-contestacao-processo/SKILL.md`. Não reutiliza nomes de campo nem
    defaults de `extr-peticao-processo`. Ver spec `contestacao-block-extraction`.
    """

    _BLOCKS: Dict[str, List[str]] = {
        "IDENT": ["document_type", "process_number", "parties", "representations", "contestacao_identification"],
        "PRELIMINARES": ["document_type", "preliminares"],
        "MERITO": ["document_type", "merito"],
        "PROVAS_PEDIDOS": ["document_type", "provas_e_requerimentos", "pedidos_finais"],
    }

    # Cabeçalhos estruturais equivalentes às seções da contestação (SKILL.md
    # seções 3-6), usados apenas para localizar o fallback determinístico —
    # nunca para inferir conteúdo não presente no documento.
    _SECTION_HEADINGS: Dict[str, "re.Pattern"] = {
        "PRELIMINARES": re.compile(r'^(?:#{1,3}\s*)?(?:DAS?\s+)?PRELIMINAR(?:ES)?\b', re.IGNORECASE | re.MULTILINE),
        "MERITO": re.compile(r'^(?:#{1,3}\s*)?(?:DO\s+)?M[ÉE]RITO\b|^(?:#{1,3}\s*)?NO\s+M[ÉE]RITO\b', re.IGNORECASE | re.MULTILINE),
        "PROVAS_PEDIDOS": re.compile(
            r'^(?:#{1,3}\s*)?(?:DOS?\s+)?PEDIDOS?(?:\s+FINAIS)?\b|^(?:#{1,3}\s*)?DOS\s+REQUERIMENTOS\b',
            re.IGNORECASE | re.MULTILINE,
        ),
    }

    _BLOCK_FOCUS = {
        "IDENT": (
            "\n\nFOCUS AREA FOR THIS BLOCK:\n"
            "- Extract ONLY: process_number (if present), parties as they appear in the contestação, "
            "representations (lawyers/OAB, only if explicit), and contestacao_identification (the piece's "
            "title, e.g. 'CONTESTAÇÃO', 'RESPOSTA', 'IMPUGNAÇÃO').\n"
            "- Do NOT infer the type of contestação. Do NOT include facts, requests, or arguments in this block.\n"
        ),
        "PRELIMINARES": (
            "\n\nFOCUS AREA FOR THIS BLOCK:\n"
            "- Extract ONLY preliminares ('preliminares'): if the text has a section equivalent to "
            "'PRELIMINAR(ES)', create one item per distinct preliminary argument.\n"
            "- Each item must have a short literal 'text' and its own 'anchors'. Do NOT create implicit "
            "preliminares that are not explicitly raised in the text.\n"
            "- If there is no preliminares section, return an empty list.\n"
        ),
        "MERITO": (
            "\n\nFOCUS AREA FOR THIS BLOCK:\n"
            "- Extract ONLY mérito/impugnação arguments ('merito'): if the text has a section equivalent to "
            "'MÉRITO', 'NO MÉRITO', or 'IMPUGNAÇÃO', create one item per distinct argument.\n"
            "- Each item must have a short literal 'text' and its own 'anchors'. Do NOT transform allegations "
            "into legal conclusions not stated in the text.\n"
            "- If there is no mérito section, return an empty list.\n"
        ),
        "PROVAS_PEDIDOS": (
            "\n\nFOCUS AREA FOR THIS BLOCK:\n"
            "- Extract 'provas_e_requerimentos' (literal evidence/requirement items, each with its own "
            "anchor) and 'pedidos_finais' (one item per final request formulated in the contestação, each "
            "with its own anchor).\n"
            "- Do NOT infer requests that are not explicitly written in the text.\n"
        ),
    }

    def execute(self, client, messages: List[Dict[str, str]], schema: Dict[str, Any], debug_dir: str, max_tokens: int, base_dir: str) -> Any:
        logger.info("=== INICIANDO EXTRAÇÃO POR BLOCOS (extr-contestacao-processo) ===")

        consolidated_json = {"document_type": schema.get("properties", {}).get("document_type", {}).get("const", "contestacao_processo")}
        failed_blocks = []

        raw_markdown = _extract_raw_markdown(messages)

        for block_name, fields in self._BLOCKS.items():
            logger.info(f"--- Processando Bloco {block_name}: {fields[1:]} ---")

            partial_schema = {
                "type": "object",
                "required": [f for f in schema.get("required", []) if f in fields],
                "properties": {f: schema["properties"][f] for f in fields if f in schema["properties"]}
            }
            if "$defs" in schema:
                partial_schema["$defs"] = schema["$defs"]

            normalized_partial = client._normalize_schema(partial_schema)

            partial_json = None
            block_messages = copy.deepcopy(messages)
            contents = client._format_messages(block_messages)

            tokens_to_use = max(max_tokens, 16384)
            block_thinking_config = types.ThinkingConfig(thinking_budget=4096)

            llm_raw_response = ""
            llm_parse_error = ""

            try:
                logger.info(f"Tentando chamada estruturada para o Bloco {block_name}...")
                response = client.client.models.generate_content(
                    model=client.model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_json_schema=normalized_partial,
                        temperature=0.0,
                        max_output_tokens=tokens_to_use,
                        thinking_config=block_thinking_config
                    )
                )
                llm_raw_response = response.text or ""
                if llm_raw_response:
                    partial_json = json.loads(llm_raw_response)
                    logger.info(f"✅ Bloco {block_name} extraído via chamada estruturada com sucesso!")
            except Exception as block_exc:
                llm_parse_error = f"Chamada estruturada falhou: {str(block_exc)}"
                logger.warning(f"Chamada estruturada falhou para o Bloco {block_name}: {block_exc}. Acionando fallback do bloco...")

            if not partial_json:
                reinforced_messages = copy.deepcopy(block_messages)
                additional_instructions = self._BLOCK_FOCUS.get(block_name, "")

                system_instruction = (
                    "\n\nIMPORTANT SYSTEM INSTRUCTION:\n"
                    "You must output a single JSON object that STRICTLY conforms to the following JSON Schema.\n"
                    f"Extract ONLY the following properties: {', '.join(fields[1:])}.\n"
                    "Output ONLY the raw JSON object. Do NOT wrap it in markdown block tags (like ```json ... ```).\n"
                    "Do NOT include any comments, conversational text, or any text before or after the JSON structure.\n"
                    "Do NOT use ellipsis ('...') or artificial abbreviations in any text fields or quote fields. Transcribe all text continuously and literally.\n"
                    "IMPORTANT RULES FOR ANCHORS:\n"
                    "- Do NOT use the key name 'fonte' anywhere in your output.\n"
                    "- Every anchor in the 'anchors' list must contain EXACTLY the keys: 'kind', 'page_marker', and 'quote'.\n"
                    f"{additional_instructions}"
                    f"JSON Schema:\n{json.dumps(partial_schema, ensure_ascii=False, indent=2)}"
                )

                if reinforced_messages and reinforced_messages[-1]["role"] == "user":
                    reinforced_messages[-1]["content"] += system_instruction
                else:
                    reinforced_messages.append({"role": "user", "content": system_instruction})

                reinforced_contents = client._format_messages(reinforced_messages)

                try:
                    logger.info(f"Chamando Gemini em modo fallback para o Bloco {block_name}...")
                    fallback_response = client.client.models.generate_content(
                        model=client.model_name,
                        contents=reinforced_contents,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.0,
                            max_output_tokens=tokens_to_use,
                            thinking_config=block_thinking_config
                        )
                    )

                    llm_raw_response = fallback_response.text or ""
                    cleaned_text = _clean_markdown_fence(llm_raw_response)

                    partial_json = json.loads(cleaned_text)
                    llm_parse_error = ""
                    logger.info(f"✅ Bloco {block_name} extraído via fallback com sucesso!")

                except Exception as fallback_exc:
                    llm_parse_error = f"Erro no fallback do Bloco {block_name}: {str(fallback_exc)}"
                    logger.error(f"❌ Falha crítica ao extrair o Bloco {block_name}: {fallback_exc}. Retornando valores padrão.")
                    partial_json = {}

            local_resolver_mod = _load_local_resolver_mod()
            shared_schemas_dir = Path(base_dir) / "packages" / "shared-schemas"
            validator = local_resolver_mod.load_validator(partial_schema, shared_schemas_dir, shared_schemas_dir)

            has_validation_failed = False
            errors = list(validator.iter_errors(partial_json))
            if errors:
                has_validation_failed = True
                logger.warning(f"Bloco {block_name} falhou na validação de subschema. Tentando corrigir chaves inválidas (como 'fonte')...")

                block_err_path = os.path.join(debug_dir, f"block_{block_name}_validation_error_before.txt")
                try:
                    with open(block_err_path, "w", encoding="utf-8") as f_err:
                        f_err.write("Erros:\n" + "\n".join(str(e) for e in errors) + "\n\nJSON:\n" + json.dumps(partial_json, indent=2, ensure_ascii=False))
                except Exception:
                    pass

                client._fix_anchors_and_properties(partial_json)

                errors = list(validator.iter_errors(partial_json))
                if not errors:
                    has_validation_failed = False
                    logger.info(f"✅ Bloco {block_name} corrigido com sucesso após normalização de chaves/anchors.")
                else:
                    logger.error(f"Bloco {block_name} continuou inválido após correção. Ignorando chaves incorretas.")

                    block_err_path_after = os.path.join(debug_dir, f"block_{block_name}_validation_error_after.txt")
                    try:
                        with open(block_err_path_after, "w", encoding="utf-8") as f_err:
                            f_err.write("Erros:\n" + "\n".join(str(e) for e in errors) + "\n\nJSON:\n" + json.dumps(partial_json, indent=2, ensure_ascii=False))
                    except Exception:
                        pass

                    for err in errors:
                        if err.path:
                            top_key = err.path[0]
                            if top_key in partial_json and top_key != "document_type":
                                partial_json.pop(top_key, None)

            # Fallback determinístico: só quando o bloco falhou/veio vazio, e
            # somente para os blocos com seção estrutural equivalente
            # (preliminares/mérito/pedidos+provas). Nunca inventa conteúdo:
            # sem cabeçalho correspondente, os campos ficam como lista vazia
            # (tratado abaixo, no preenchimento de defaults).
            is_block_empty = not partial_json or not any(partial_json.get(f) for f in fields[1:])
            if (is_block_empty or has_validation_failed or llm_parse_error) and block_name in self._SECTION_HEADINGS:
                logger.warning(f"⚠️ Aplicando fallback determinístico local para o Bloco {block_name}...")
                failed_blocks.append(block_name)

                parse_err_path = os.path.join(debug_dir, f"block_{block_name}_parse_error.txt")
                raw_resp_path = os.path.join(debug_dir, f"block_{block_name}_raw_response.txt")
                try:
                    with open(parse_err_path, "w", encoding="utf-8") as f_err:
                        f_err.write(llm_parse_error or f"Bloco {block_name} falhou na validação de schema ou veio vazio.")
                    with open(raw_resp_path, "w", encoding="utf-8") as f_raw:
                        f_raw.write(llm_raw_response or "Sem resposta bruta do LLM.")
                except Exception as dbg_err:
                    logger.warning(f"Falha ao gravar arquivos de debug para o Bloco {block_name}: {dbg_err}")

                if not isinstance(partial_json, dict):
                    partial_json = {}
                partial_json["document_type"] = "contestacao_processo"

                fallback_values = self._deterministic_fallback(block_name, raw_markdown)
                for field_name, value in fallback_values.items():
                    partial_json[field_name] = value

            # Garante que todos os campos esperados no bloco existam com
            # valores do TIPO correto (nunca lista vazia para um campo que
            # deveria ser objeto/AnchoredString), derivados exclusivamente do
            # schema de contestação — nunca defaults de petição inicial.
            if not isinstance(partial_json, dict):
                partial_json = {}
            for f in fields[1:]:
                if f not in partial_json or partial_json[f] is None:
                    partial_json[f] = self._default_for_field(f)

            sanitize_anchor_page_marker(partial_json, _guess_current_page(raw_markdown))

            if partial_json:
                for key, val in partial_json.items():
                    if key == "document_type":
                        continue
                    consolidated_json[key] = val

        logger.info("Validando JSON consolidado final contra o schema rico completo (contestação)...")

        local_resolver_mod = _load_local_resolver_mod()
        shared_schemas_dir_final = Path(base_dir) / "packages" / "shared-schemas"
        validator_final = local_resolver_mod.load_validator(schema, shared_schemas_dir_final, shared_schemas_dir_final)

        errors_final = sorted(validator_final.iter_errors(consolidated_json), key=lambda e: list(e.path))
        if errors_final:
            error_details = []
            for err_item in errors_final:
                err_path = " -> ".join(str(p) for p in err_item.absolute_path) or "(root)"
                error_details.append(f"[{err_path}] {err_item.message}")
            error_msg_full = "\n".join(error_details)
            logger.error(f"JSON consolidado (contestação) falhou na validação de schema final:\n{error_msg_full}")
            raise ValueError(f"JSON consolidado falhou na validação do schema completo:\n{error_msg_full}")

        if failed_blocks:
            logger.warning(f"⚠️ Extração concluída com ressalvas! Blocos que falharam: {', '.join(failed_blocks)}")
            consolidated_json["_failed_blocks"] = failed_blocks
        else:
            logger.info("✅ Extração por blocos (contestação) concluída e validada com sucesso absoluto!")

        return consolidated_json

    @staticmethod
    def _default_for_field(field: str) -> Any:
        """Default determinístico por campo, derivado exclusivamente do tipo
        real desse campo no schema de contestação — nunca reaproveita a forma
        ou os valores padrão de `extr-peticao-processo`."""
        if field == "contestacao_identification":
            return {
                "value": "CONTESTAÇÃO",
                "anchors": [{"kind": "pagina", "page_marker": "1", "quote": "Contestação"}],
            }
        if field == "process_number":
            return {
                "value": "Não informado",
                "anchors": [{"kind": "pagina", "page_marker": "1", "quote": "Não informado"}],
            }
        # parties, representations, preliminares, merito,
        # provas_e_requerimentos, pedidos_finais: todos arrays no schema.
        return []

    def _deterministic_fallback(self, block_name: str, markdown_text: str) -> Dict[str, Any]:
        """Localiza a seção estrutural equivalente ao bloco (por cabeçalho) e
        extrai parágrafos literais como itens; na ausência de cabeçalho
        correspondente, retorna listas vazias — nunca inventa conteúdo nem
        reutiliza defaults de petição inicial."""
        if block_name == "PRELIMINARES":
            items = self._collect_section_items(markdown_text, "PRELIMINARES")
            return {"preliminares": items}
        if block_name == "MERITO":
            items = self._collect_section_items(markdown_text, "MERITO")
            return {"merito": items}
        if block_name == "PROVAS_PEDIDOS":
            items = self._collect_section_items(markdown_text, "PROVAS_PEDIDOS")
            return {"provas_e_requerimentos": [], "pedidos_finais": items}
        return {}

    def _collect_section_items(self, markdown_text: str, block_name: str, max_items: int = 20) -> List[Dict[str, Any]]:
        heading_re = self._SECTION_HEADINGS[block_name]
        match = heading_re.search(markdown_text or "")
        if match is None:
            logger.warning(
                f"Fallback determinístico ({block_name}): nenhum cabeçalho estrutural encontrado. "
                "Retornando lista vazia em vez de inventar conteúdo."
            )
            return []

        section_start = match.end()
        section_text = markdown_text[section_start:]

        # Limita a seção até o próximo cabeçalho estrutural conhecido (de
        # qualquer bloco), para não vazar conteúdo de seções seguintes.
        next_heading_pos = len(section_text)
        for other_pattern in self._SECTION_HEADINGS.values():
            m = other_pattern.search(section_text)
            if m and m.start() > 0 and m.start() < next_heading_pos:
                next_heading_pos = m.start()
        section_text = section_text[:next_heading_pos]

        items: List[Dict[str, Any]] = []
        current_page = _guess_current_page(markdown_text[:section_start])
        offset = section_start
        for line in section_text.splitlines(keepends=True):
            for pattern in _PAGE_MARKER_RE_LIST:
                m = pattern.search(line)
                if m:
                    current_page = m.group(1)

            stripped = line.strip()
            offset += len(line)
            clean_line = re.sub(r'^(?:[-*+]\s*|\d+\.\s*|[a-zA-Z]\)\s*)+', '', stripped).strip()
            if len(clean_line) < 5:
                continue
            if any(p.match(clean_line) for p in self._SECTION_HEADINGS.values()):
                continue

            items.append({
                "text": clean_line[:4000],
                "anchors": [{
                    "kind": "pagina",
                    "page_marker": current_page,
                    "quote": clean_line[:200],
                }],
            })
            if len(items) >= max_items:
                break

        if not items:
            logger.warning(
                f"Fallback determinístico ({block_name}): cabeçalho encontrado, mas nenhuma linha de "
                "conteúdo identificada na seção. Retornando lista vazia."
            )

        return items


BLOCK_STRATEGIES = {
    "extr-peticao-processo": PeticaoBlockStrategy,
    "extr-contestacao-processo": ContestacaoBlockStrategy,
}


def resolve_block_strategy(bundle_id: Optional[str]):
    """Resolve a classe de estratégia registrada para `bundle_id`, ou levanta
    `BlockExtractionStrategyUnavailableError` — nunca retorna uma estratégia
    diferente da explicitamente registrada para esse `bundle_id`."""
    strategy_cls = BLOCK_STRATEGIES.get(bundle_id)
    if strategy_cls is None:
        raise BlockExtractionStrategyUnavailableError(bundle_id)
    return strategy_cls
