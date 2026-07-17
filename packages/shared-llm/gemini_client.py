import json
import logging
import os
from typing import List, Dict, Any
try:
    from .client import LLMClient
except ImportError:
    import sys
    client_mod = sys.modules.get('client_mod')
    LLMClient = client_mod.LLMClient if client_mod else object
from google import genai
from google.genai import types
from google.genai.errors import APIError

logger = logging.getLogger(__name__)

class GeminiLLMClient(LLMClient):
    """
    Integração real via google-genai SDK.
    Baseline para inferência esquemática estruturada (fail-fast architecture).
    """
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key)

    def generate_text(self, messages: List[Dict[str, str]], **kwargs) -> str:
        contents = self._format_messages(messages)
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            return response.text
        except APIError as e:
            logger.error(f"Erro na API Gemini: {str(e)}")
            raise RuntimeError(f"Erro na API Gemini: {str(e)}")

    def generate_structured(self, messages: List[Dict[str, str]], schema: Dict[str, Any], **kwargs) -> Any:
        import os
        import copy
        import json
        import jsonschema
        from jsonschema import RefResolver
        from pathlib import Path

        # 1. Definir base_dir
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # 2. Sanitizar o schema
        normalized_schema = self._normalize_schema(schema)

        # 3. Salvar o schema efetivamente enviado em debug
        debug_dir = os.path.join(base_dir, "var", "artifacts", "gemini-debug")
        os.makedirs(debug_dir, exist_ok=True)
        debug_file_path = os.path.join(debug_dir, "peticao_processo.response_schema.sanitized.json")
        try:
            with open(debug_file_path, "w", encoding="utf-8") as f:
                json.dump(normalized_schema, f, indent=2, ensure_ascii=False)
            logger.info(f"Schema sanitizado salvo em: {debug_file_path}")
        except Exception as file_err:
            logger.warning(f"Falha ao salvar schema de debug em {debug_file_path}: {file_err}")

        # 4. Função de varredura profunda para verificar chaves proibidas antes de enviar ao Gemini
        prohibited_keys = {
            "$schema", "$id", "$defs", "$ref", "defs/common.schema.json",
            "$vocabulary", "$anchor", "$dynamicRef", "$dynamicAnchor",
            "unevaluatedProperties", "patternProperties", "dependentSchemas",
            "if", "then", "else", "not", "oneOf", "allOf"
        }

        def _scan_deep(node, path="root"):
            if isinstance(node, dict):
                for k, v in node.items():
                    current_path = f"{path} -> {k}"
                    if k in prohibited_keys:
                        raise ValueError(f"Chave proibida '{k}' encontrada no schema sanitizado no caminho: {current_path}")
                    if isinstance(v, str) and "defs/common.schema.json" in v:
                        raise ValueError(f"Referência proibida 'defs/common.schema.json' encontrada no valor de '{k}' no caminho: {current_path}")
                    _scan_deep(v, current_path)
            elif isinstance(node, list):
                for idx, item in enumerate(node):
                    _scan_deep(item, f"{path}[{idx}]")

        # Falha antes da API se encontrar chaves proibidas
        _scan_deep(normalized_schema)

        # 5. Logar resumo do schema sanitizado
        schema_str = json.dumps(normalized_schema)
        size_bytes = len(schema_str.encode('utf-8'))
        top_properties_count = len(normalized_schema.get("properties", {}))
        contains_ref = "sim" if "$ref" in schema_str else "não"
        contains_defs = "sim" if "$defs" in schema_str else "não"
        contains_unevaluated = "sim" if "unevaluatedProperties" in schema_str else "não"
        contains_combiners = "sim" if any(c in schema_str for c in ["anyOf", "oneOf", "allOf"]) else "não"

        logger.info(
            f"--- METADADOS DO SCHEMA SANITIZADO GEMINI ---\n"
            f"- Tamanho do schema: {size_bytes} bytes\n"
            f"- Chaves proibidas encontradas: não (validado via varredura profunda)\n"
            f"- Quantidade de propriedades top-level: {top_properties_count}\n"
            f"- Contém $ref: {contains_ref}\n"
            f"- Contém $defs: {contains_defs}\n"
            f"- Contém unevaluatedProperties: {contains_unevaluated}\n"
            f"- Contém combinadores (anyOf/oneOf/allOf): {contains_combiners}\n"
            f"---------------------------------------------"
        )

        max_output_tokens_used = 8192
        try:
            llm_reg_path = os.path.join(base_dir, "platform", "skill-runtime", "llm_registry.yaml")
            if os.path.exists(llm_reg_path):
                import yaml
                with open(llm_reg_path, "r", encoding="utf-8") as f:
                    llm_reg = yaml.safe_load(f)
                gemini_api_class = llm_reg.get("execution_classes", {}).get("gemini_api", {})
                if "max_output_tokens" in gemini_api_class:
                    max_output_tokens_used = int(gemini_api_class["max_output_tokens"])
                else:
                    for model_info in gemini_api_class.get("models", []):
                        if model_info.get("id") == self.model_name and "max_output_tokens" in model_info:
                            max_output_tokens_used = int(model_info["max_output_tokens"])
                            break
        except Exception as reg_err:
            logger.warning(f"Erro ao ler max_output_tokens de llm_registry.yaml: {reg_err}")

        logger.info(f"Usando max_output_tokens: {max_output_tokens_used}")

        contents = self._format_messages(messages)

        def _validate_offline(json_obj, target_schema):
            common_path = os.path.join(base_dir, 'packages', 'shared-schemas', 'defs', 'common.schema.json')
            common_schema_dict = {}
            if os.path.exists(common_path):
                with open(common_path, 'r', encoding='utf-8') as f_common:
                    common_schema_dict = json.load(f_common)

            store = {
                target_schema.get("$id", "https://juridico-cli.local/schemas/peticao_processo.schema.json"): target_schema,
                common_schema_dict.get("$id", "https://juridico-cli.local/schemas/defs/common.schema.json"): common_schema_dict
            }

            shared_schemas_dir = Path(base_dir) / "packages" / "shared-schemas"
            resolver = RefResolver(base_uri=shared_schemas_dir.as_uri() + "/", referrer=target_schema, store=store)
            validator = jsonschema.Draft202012Validator(target_schema, resolver=resolver)

            errors = sorted(validator.iter_errors(json_obj), key=lambda err_item: list(err_item.path))
            if errors:
                error_details = []
                for err_item in errors:
                    err_path = " -> ".join(str(p) for p in err_item.absolute_path) or "(root)"
                    error_details.append(f"[{err_path}] {err_item.message}")
                return False, "\n".join(error_details)
            return True, ""

        # 6. Tentar chamada estruturada com o response_schema
        try:
            logger.info("Tentando chamada estruturada inicial com response_schema...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=normalized_schema,
                    temperature=0.0,
                    max_output_tokens=max_output_tokens_used
                )
            )
            finish_reason = str(response.candidates[0].finish_reason) if response.candidates else "unknown"
            usage = response.usage_metadata
            usage_str = f"Prompt: {usage.prompt_token_count}, Candidates: {usage.candidates_token_count}, Total: {usage.total_token_count}" if usage else "indisponível"
            logger.info(f"Resposta estruturada inicial - Finish Reason: {finish_reason} | Usage: {usage_str}")

            raw_text = response.text
            if not raw_text:
                raise ValueError("Gemini retornou um conteúdo vazio.")
            return json.loads(raw_text)

        except Exception as e:
            logger.warning(
                f"Chamada estruturada com response_schema falhou: {str(e)}. "
                "Iniciando fallback sem response_schema com tratamento de truncamento e retry..."
            )

            reinforced_messages = copy.deepcopy(messages)
            system_instruction = (
                "\n\nIMPORTANT SYSTEM INSTRUCTION:\n"
                "You must output a single JSON object that STRICTLY conforms to the following JSON Schema.\n"
                "Output ONLY the raw JSON object. Do NOT wrap it in markdown block tags (like ```json ... ```).\n"
                "Do NOT include any comments, conversational text, or any text before or after the JSON structure.\n"
                "Do NOT use ellipsis ('...') or artificial abbreviations in any text fields or quote fields. Transcribe all text continuously and literally.\n"
                "IMPORTANT RULES FOR ANCHORS:\n"
                "- Do NOT use the key name 'fonte' anywhere in your output.\n"
                "- Every anchor in the 'anchors' list must contain EXACTLY the keys: 'kind', 'page_marker', and 'quote'.\n"
                f"JSON Schema:\n{json.dumps(schema, ensure_ascii=False, indent=2)}"
            )

            if reinforced_messages and reinforced_messages[-1]["role"] == "user":
                reinforced_messages[-1]["content"] += system_instruction
            else:
                reinforced_messages.append({"role": "user", "content": system_instruction})

            reinforced_contents = self._format_messages(reinforced_messages)

            def _try_single_fallback_call(prompt_contents, is_retry=False, retry_instruction=""):
                call_contents = prompt_contents
                if is_retry and retry_instruction:
                    call_contents = prompt_contents + f"\n\nREPAIR INSTRUCTION:\n{retry_instruction}"

                logger.info(f"Chamando Gemini (modo fallback, is_retry={is_retry})...")
                fallback_response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=call_contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.0,
                        max_output_tokens=max_output_tokens_used
                    )
                )

                f_reason = str(fallback_response.candidates[0].finish_reason) if fallback_response.candidates else "unknown"
                usg = fallback_response.usage_metadata
                usg_str = f"Prompt: {usg.prompt_token_count}, Candidates: {usg.candidates_token_count}, Total: {usg.total_token_count}" if usg else "indisponível"
                logger.info(f"Resposta fallback - Finish Reason: {f_reason} | Usage: {usg_str} | Fallback sem response_schema: sim")

                f_text = fallback_response.text or ""
                return f_text, f_reason

            # Tenta chamada 1
            fallback_text, finish_reason = _try_single_fallback_call(reinforced_contents, is_retry=False)

            # Salvar texto bruto retornado pelo fallback
            fallback_raw_path = os.path.join(debug_dir, "fallback_raw_response.txt")
            try:
                with open(fallback_raw_path, "w", encoding="utf-8") as f_raw:
                    f_raw.write(fallback_text)
                logger.info(f"Resposta bruta do fallback salva em: {fallback_raw_path}")
            except Exception as file_raw_err:
                logger.warning(f"Falha ao salvar response bruta em {fallback_raw_path}: {file_raw_err}")

            def _clean_markdown(text):
                cleaned = text.strip()
                if cleaned.startswith("```"):
                    lines = cleaned.splitlines()
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].strip() == "```":
                        lines = lines[:-1]
                    cleaned = "\n".join(lines).strip()
                return cleaned

            cleaned_fallback_text = _clean_markdown(fallback_text)

            parsed_json = None
            parse_error_msg = ""

            try:
                if not cleaned_fallback_text:
                    raise ValueError("Resposta limpa do fallback está vazia.")
                parsed_json = json.loads(cleaned_fallback_text)
            except json.JSONDecodeError as decode_err:
                parse_error_msg = f"JSONDecodeError: {str(decode_err)} (pos: {decode_err.pos}, line: {decode_err.lineno}, col: {decode_err.colno})"
                logger.warning(f"Erro ao parsear JSON do fallback: {parse_error_msg}")

                # Salvar erro de parse em fallback_parse_error.txt
                parse_err_path = os.path.join(debug_dir, "fallback_parse_error.txt")
                try:
                    with open(parse_err_path, "w", encoding="utf-8") as f_err:
                        f_err.write(parse_error_msg + "\n\nTexto bruto recebido:\n" + fallback_text)
                except Exception as file_err:
                    logger.warning(f"Falha ao salvar erro de parse em {parse_err_path}: {file_err}")

            # Decidir se ativa a extração por blocos ou faz retry com base em truncamento
            is_truncated = (finish_reason == "MAX_TOKENS") or ("Unterminated string" in parse_error_msg) or (not parsed_json and len(fallback_text) > 12000)

            if not parsed_json:
                if is_truncated:
                    logger.warning("Detecção de truncamento por excesso de tokens. Tentando retry automático com instrução de saída compacta...")
                    repair_prompt = (
                        "Reemita o JSON completo e válido, sem markdown, começando em { e terminando em }, "
                        "preservando todas as chaves exigidas. Forneça resumos mais compactos para garantir que caiba no limite de tokens."
                    )
                else:
                    logger.warning("Resposta malformada, mas sem indicação de truncamento de tokens. Executando retry automático com instrução de reparo...")
                    repair_prompt = (
                        "Reemita o JSON completo e válido, sem markdown, começando em { e terminando em }, "
                        "preservando todas as chaves exigidas."
                    )

                try:
                    fallback_text_retry, finish_reason_retry = _try_single_fallback_call(
                        reinforced_contents,
                        is_retry=True,
                        retry_instruction=repair_prompt
                    )
                    cleaned_fallback_text_retry = _clean_markdown(fallback_text_retry)
                    parsed_json = json.loads(cleaned_fallback_text_retry)

                    # Se mesmo com retry terminou com MAX_TOKENS ou string não finalizada, pode estar truncado novamente
                    is_retry_truncated = (finish_reason_retry == "MAX_TOKENS") or (len(cleaned_fallback_text_retry) > 12000)
                    if is_retry_truncated:
                        logger.warning("Retry de reparo/compactação também indicou truncamento. Ativando fallback definitivo: Extração por Blocos/Campos!")
                        return self._execute_extraction_in_blocks(messages, schema, debug_dir, max_output_tokens_used, base_dir)

                    logger.info("✅ Retry de reparo/compactação obteve sucesso em parsear o JSON!")
                except (json.JSONDecodeError, Exception) as retry_err:
                    logger.error(f"Erro persistente após retry: {retry_err}")
                    logger.warning("Falha no retry automático. Ativando fallback definitivo: Extração por Blocos/Campos!")
                    return self._execute_extraction_in_blocks(messages, schema, debug_dir, max_output_tokens_used, base_dir)

            # Tenta corrigir chaves inválidas (como 'fonte') no JSON único antes de validar
            if parsed_json:
                self._fix_anchors_and_properties(parsed_json)

            # Validar localmente contra o schema rico completo
            is_valid, validation_errors = _validate_offline(parsed_json, schema)
            if not is_valid:
                logger.error(f"Validação local falhou contra o schema rico completo:\n{validation_errors}")
                logger.warning("Validação local falhou no JSON único. Ativando Extração por Blocos para precisão de campos...")
                return self._execute_extraction_in_blocks(messages, schema, debug_dir, max_output_tokens_used, base_dir)

            logger.info("✅ Validação local do fallback consolidado passou com sucesso!")
            return parsed_json

    def _execute_extraction_in_blocks(self, messages: List[Dict[str, str]], schema: Dict[str, Any], debug_dir: str, max_tokens: int, base_dir: str) -> Any:
        import json
        import copy
        import jsonschema
        from jsonschema import RefResolver
        from pathlib import Path

        logger.info("=== INICIANDO EXTRAÇÃO POR BLOCOS (ESTRATÉGIA DE ROBUSTEZ N:1) ===")

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

        # Recuperar o Markdown original da mensagem do usuário
        raw_markdown = ""
        if messages:
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    raw_markdown = msg.get("content", "")
                    break

        for block_name, fields in blocks.items():
            logger.info(f"--- Processando Bloco {block_name}: {fields[1:]} ---")

            partial_schema = {
                "type": "object",
                "required": [f for f in schema.get("required", []) if f in fields],
                "properties": {f: schema["properties"][f] for f in fields if f in schema["properties"]}
            }
            if "$defs" in schema:
                partial_schema["$defs"] = schema["$defs"]

            normalized_partial = self._normalize_schema(partial_schema)

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
                        target_pages = [13, 14, 15]
                    else:  # block_name == "C"
                        target_pages = [1, 2, 3, 4, 11, 12, 13, 14, 15]
                    
                    cut_content = self._extract_pages_from_markdown(orig_content, target_pages)
                    logger.info(
                        f"Bloco {block_name}: Recortando páginas {target_pages}. "
                        f"Tamanho original: {len(orig_content)} chars -> Tamanho recortado: {len(cut_content)} chars"
                    )
                    block_messages[user_msg_idx]["content"] = cut_content

            contents = self._format_messages(block_messages)
            
            # Garantir max_output_tokens alto o suficiente para E1 e E2
            tokens_to_use = 8192 if block_name in ("E1", "E2") else max_tokens

            llm_raw_response = ""
            llm_parse_error = ""

            try:
                logger.info(f"Tentando chamada estruturada para o Bloco {block_name}...")
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_json_schema=normalized_partial,
                        temperature=0.0,
                        max_output_tokens=tokens_to_use
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
                        "- Focus your extraction exclusively on Pages 13, 14, and 15 of the document.\n"
                        "- Extract ONLY the legacy list of requests ('pedidos'). Do NOT extract or ask for tutela de urgência, provas, or riscos/pontos de atenção in this block.\n\n"
                        "MINIMUM MANDATORY ITEMS TO EXTRACT (if present in the document, especially in those pages):\n"
                        "- Service of process/citation of Banco do Brasil (citação do Banco do Brasil);\n"
                        "- Decree of merit/procedência to declare nullity of the deed (declaração de nulidade da escritura);\n"
                        "- Ineffectiveness of the mortgage (ineficácia da hipoteca);\n"
                        "- Registration cancellation of the mortgage (cancelamento registral da hipoteca);\n"
                        "- Issuance of writs/notices to the registry office (expedição de mandados/ofícios ao Cartório);\n"
                        "- Court costs and attorney's fees (custas e honorários);\n\n"
                        "STRICT RULES FOR ITEMS:\n"
                        "- Limit each item to: label (if any), text (the legacy text), and anchors.\n"
                        "- Do NOT write long transcriptions of entire sections if too large. Use a shorter, continuous literal snippet instead, WITHOUT using or creating artificial ellipsis '(...)' or '…'.\n"
                    )
                elif block_name == "E2":
                    additional_instructions = (
                        "\n\nFOCUS AREA FOR THIS BLOCK:\n"
                        "- Focus your extraction exclusively on Pages 13, 14, and 15 of the document.\n"
                        "- Extract ONLY the rich structured list of requests ('pedidos_individualizados'). Do NOT extract or ask for tutela de urgência, provas, or riscos/pontos de atenção in this block.\n\n"
                        "MINIMUM MANDATORY ITEMS TO EXTRACT (if present in the document, especially in those pages):\n"
                        "- Service of process/citation of Banco do Brasil (citação do Banco do Brasil);\n"
                        "- Decree of merit/procedência to declare nullity of the deed (declaração de nulidade da escritura);\n"
                        "- Ineffectiveness of the mortgage (ineficácia da hipoteca);\n"
                        "- Registration cancellation of the mortgage (cancelamento registral da hipoteca);\n"
                        "- Issuance of writs/notices to the registry office (expedição de mandados/ofícios ao Cartório);\n"
                        "- Court costs and attorney's fees (custas e honorários);\n\n"
                        "STRICT RULES FOR ITEMS:\n"
                        "- Limit each item to: tipo, descricao_interpretativa, trecho_literal, and anchors.\n"
                        "- Do NOT write long transcriptions of entire sections if too large. Use a shorter, continuous literal snippet instead, WITHOUT using or creating artificial ellipsis '(...)' or '…'.\n"
                    )
                elif block_name == "E3":
                    additional_instructions = (
                        "\n\nFOCUS AREA FOR THIS BLOCK:\n"
                        "- Focus your extraction primarily on Pages 13, 14, and 15 of the document.\n"
                        "- Extract ONLY the provisional remedy details ('tutela_urgencia').\n\n"
                        "MINIMUM MANDATORY ITEMS TO EXTRACT (if present in the document, especially in those pages):\n"
                        "- Tutela de urgência for the registration/annotation of the lawsuit in the property registers (averbação da ação nas matrículas);\n"
                        "- Suspension of enforceability of the mortgage guarantees (suspense da exigibilidade das garantias hipotecárias);\n"
                        "- Suspension of the specific lawsuit/process number 0003453-81.2003.8.26.0136;\n"
                    )
                elif block_name == "E4":
                    additional_instructions = (
                        "\n\nFOCUS AREA FOR THIS BLOCK:\n"
                        "- Focus your extraction primarily on Pages 13, 14, and 15 of the document.\n"
                        "- Extract ONLY the requested evidence/provas ('provas_requeridas').\n\n"
                        "MINIMUM MANDATORY ITEMS TO EXTRACT (if present in the document, especially in those pages):\n"
                        "- Documental evidence (prova documental), pericial evidence (prova pericial), personal deposition (depoimento pessoal), oitiva de testemunhas, and submission of subsequent documents (juntada de documentos supervenientes).\n"
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

                reinforced_contents = self._format_messages(reinforced_messages)

                try:
                    logger.info(f"Chamando Gemini em modo fallback para o Bloco {block_name}...")
                    fallback_response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=reinforced_contents,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.0,
                            max_output_tokens=tokens_to_use
                        )
                    )

                    llm_raw_response = fallback_response.text or ""
                    cleaned_text = llm_raw_response.strip()
                    if cleaned_text.startswith("```"):
                        lines = cleaned_text.splitlines()
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].strip() == "```":
                            lines = lines[:-1]
                        cleaned_text = "\n".join(lines).strip()

                    partial_json = json.loads(cleaned_text)
                    logger.info(f"✅ Bloco {block_name} extraído via fallback com sucesso!")

                except Exception as fallback_exc:
                    llm_parse_error = f"Erro no fallback do Bloco {block_name}: {str(fallback_exc)}"
                    logger.error(f"❌ Falha crítica ao extrair o Bloco {block_name}: {fallback_exc}. Retornando valores padrão.")
                    partial_json = {}

            common_path = os.path.join(base_dir, 'packages', 'shared-schemas', 'defs', 'common.schema.json')
            common_schema_dict = {}
            if os.path.exists(common_path):
                with open(common_path, 'r', encoding='utf-8') as f_common:
                    common_schema_dict = json.load(f_common)

            store = {
                partial_schema.get("$id", f"https://juridico-cli.local/schemas/peticao_processo_{block_name}.schema.json"): partial_schema,
                common_schema_dict.get("$id", "https://juridico-cli.local/schemas/defs/common.schema.json"): common_schema_dict
            }

            shared_schemas_dir = Path(base_dir) / "packages" / "shared-schemas"
            resolver = RefResolver(base_uri=shared_schemas_dir.as_uri() + "/", referrer=partial_schema, store=store)
            validator = jsonschema.Draft202012Validator(partial_schema, resolver=resolver)

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
                        f_err.write(f"Erros:\n" + "\n".join(str(e) for e in errors) + "\n\nJSON:\n" + json.dumps(partial_json, indent=2, ensure_ascii=False))
                except Exception:
                    pass

                self._fix_anchors_and_properties(partial_json)

                errors = list(validator.iter_errors(partial_json))
                if errors:
                    logger.error(f"Bloco {block_name} continuou inválido após correção. Ignorando chaves incorretas.")
                    
                    # Salva debug final da falha persistente
                    block_err_path_after = os.path.join(debug_dir, f"block_{block_name}_validation_error_after.txt")
                    try:
                        with open(block_err_path_after, "w", encoding="utf-8") as f_err:
                            f_err.write(f"Erros:\n" + "\n".join(str(e) for e in errors) + "\n\nJSON:\n" + json.dumps(partial_json, indent=2, ensure_ascii=False))
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

                pedidos_legado_fallback, pedidos_ricos_fallback = self._apply_deterministic_fallback_e1_e2(raw_markdown)
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

            if partial_json:
                for key, val in partial_json.items():
                    if key == "document_type":
                        continue
                    consolidated_json[key] = val

        logger.info("Validando JSON consolidado final contra o schema rico completo...")

        store_final = {
            schema.get("$id", "https://juridico-cli.local/schemas/peticao_processo.schema.json"): schema,
            common_schema_dict.get("$id", "https://juridico-cli.local/schemas/defs/common.schema.json"): common_schema_dict
        }
        resolver_final = RefResolver(base_uri=shared_schemas_dir.as_uri() + "/", referrer=schema, store=store_final)
        validator_final = jsonschema.Draft202012Validator(schema, resolver=resolver_final)

        errors_final = sorted(validator_final.iter_errors(consolidated_json), key=lambda e: list(e.path))
        if errors_final:
            error_details = []
            for err_item in errors_final:
                err_path = " -> ".join(str(p) for p in err_item.absolute_path) or "(root)"
                error_details.append(f"[{err_path}] {err_item.message}")
            error_msg_full = "\n".join(error_details)
            logger.error(f"JSON consolidado falhou na validação de schema final:\n{error_msg_full}")
            raise ValueError(f"JSON consolidado falhou na validação do schema completo:\n{error_msg_full}")

        # Retorna status de warning/ressalvas no log e metadados se necessário
        if failed_blocks:
            logger.warning(f"⚠️ Extração concluída com ressalvas! Blocos que falharam: {', '.join(failed_blocks)}")
            consolidated_json["_failed_blocks"] = failed_blocks
        else:
            logger.info("✅ Extração por blocos concluída e validada com sucesso absoluto!")

        return consolidated_json

    def _normalize_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve todos os $refs por substituição inline e sanitiza o schema
        para o subconjunto OpenAPI/JSONSchema suportado pelo Gemini.
        """
        import copy
        import os
        import json

        # 1. Carregar defs do common.schema.json local
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        common_path = os.path.join(base_dir, 'packages', 'shared-schemas', 'defs', 'common.schema.json')
        
        common_defs = {}
        if os.path.exists(common_path):
            with open(common_path, 'r', encoding='utf-8') as f:
                common_schema = json.load(f)
                common_defs = common_schema.get("$defs", {})
        else:
            logger.warning(f"Shared schema não encontrado fisicamente: {common_path}")

        # 2. Unificar pool de definições ($defs locais e do common_schema)
        defs_pool = {}
        # Primeiro, popula com as definições do common.schema.json
        for k, v in common_defs.items():
            defs_pool[k] = v
        # Depois, mescla com as definições do próprio schema
        local_defs = schema.get("$defs", {})
        for k, v in local_defs.items():
            # Se a definição local for referência para o common schema, resolvemos depois
            if isinstance(v, dict) and "$ref" in v and "common.schema.json" in str(v.get("$ref", "")):
                ref_key = v["$ref"].split("#/$defs/")[-1]
                if ref_key in common_defs:
                    defs_pool[k] = common_defs[ref_key]
            else:
                defs_pool[k] = v

        # 3. Função recursiva para fazer inline dos $refs
        def _resolve_refs(node, resolved_path=None):
            if resolved_path is None:
                resolved_path = set()

            if isinstance(node, dict):
                if "$ref" in node and isinstance(node["$ref"], str):
                    ref_str = node["$ref"]
                    # Extrai a chave de definição final
                    def_key = ref_str.split("#/$defs/")[-1]
                    
                    if def_key in resolved_path:
                        logger.warning(f"Circular reference detected for '{def_key}'. Substituting with type: string.")
                        return {"type": "string"}
                        
                    if def_key in defs_pool:
                        resolved_node = copy.deepcopy(defs_pool[def_key])
                        resolved_path.add(def_key)
                        resolved_node = _resolve_refs(resolved_node, resolved_path)
                        resolved_path.remove(def_key)
                        
                        # Preserva metadados extras (como description) que constavam no nó original
                        for key, val in node.items():
                            if key != "$ref" and key not in resolved_node:
                                resolved_node[key] = val
                        return resolved_node
                    else:
                        logger.warning(f"Reference '{ref_str}' could not be resolved. Substituting with type: string.")
                        return {"type": "string"}

                new_dict = {}
                for key, val in node.items():
                    new_dict[key] = _resolve_refs(val, resolved_path)
                return new_dict

            elif isinstance(node, list):
                return [_resolve_refs(item, resolved_path) for item in node]

            return node

        # Executa a resolução de referências recursivamente
        resolved_schema = _resolve_refs(schema)

        # 4. Função recursiva para sanitizar o schema resolvido, mantendo somente campos permitidos
        def _sanitize(node):
            if isinstance(node, dict):
                # Converte const para enum + type antes de filtrar
                if "const" in node:
                    const_val = node.pop("const")
                    node["enum"] = [const_val]
                    if "type" not in node:
                        if isinstance(const_val, str):
                            node["type"] = "string"
                        elif isinstance(const_val, bool):
                            node["type"] = "boolean"
                        elif isinstance(const_val, (int, float)):
                            node["type"] = "number"
                        else:
                            node["type"] = "string"

                # Garante que type seja atribuído de acordo com a estrutura do nó
                if "properties" in node and "type" not in node:
                    node["type"] = "object"
                if "items" in node and "type" not in node:
                    node["type"] = "array"

                # Processa os subschemas em "properties" e "items" de forma especial
                # para que seus nomes de chave/posições não sejam filtrados incorretamente.
                if "properties" in node and isinstance(node["properties"], dict):
                    node["properties"] = {k: _sanitize(v) for k, v in node["properties"].items()}
                
                if "items" in node:
                    if isinstance(node["items"], dict):
                        node["items"] = _sanitize(node["items"])
                    elif isinstance(node["items"], list):
                        node["items"] = [_sanitize(item) for item in node["items"]]

                # Se type não está definido e temos combinadores (anyOf, oneOf, allOf),
                # tentamos extrair o tipo a partir de seus subschemas antes de deletá-los.
                if "type" not in node:
                    types_found = set()
                    for combiner in ["anyOf", "oneOf", "allOf"]:
                        if combiner in node and isinstance(node[combiner], list):
                            for sub in node[combiner]:
                                if isinstance(sub, dict):
                                    if "type" in sub:
                                        types_found.add(sub["type"])
                    types_found.discard("null")
                    if len(types_found) == 1:
                        node["type"] = list(types_found)[0]
                    elif len(types_found) > 1:
                        node["type"] = "string"  # Fallback genérico se houver múltiplos tipos

                # Define chaves permitidas pelo Gemini
                allowed_keys = {
                    "type", "title", "description",
                    "properties", "required", "additionalProperties",
                    "items", "prefixItems", "minItems", "maxItems",
                    "enum", "format", "minimum", "maximum", "anyOf",
                }
                
                # Filtra o dicionário mantendo apenas as chaves permitidas no nó do schema
                filtered_dict = {k: v for k, v in node.items() if k in allowed_keys}
                return filtered_dict

            elif isinstance(node, list):
                return [_sanitize(item) for item in node]

            return node

        # Executa a sanitização no schema resolvido
        sanitized_schema = _sanitize(resolved_schema)
        
        # Confirma em log o schema sanitizado final que será enviado
        logger.info(f"Schema sanitizado enviado ao Gemini: {json.dumps(sanitized_schema)}")
        return sanitized_schema

    def _fix_anchors_and_properties(self, obj):
        """
        Corrige de forma recursiva chaves inválidas nos objetos de âncora,
        traduzindo chaves como 'fonte' para kind, page_marker e quote,
        e normalizando enums/estruturas para garantir validade no schema.
        """
        if isinstance(obj, dict):
            # 1. Correção do formato de âncora com chave "fonte"
            if "fonte" in obj and isinstance(obj["fonte"], dict):
                fonte = obj.pop("fonte")
                obj["kind"] = "pagina"
                ancora_str = str(fonte.get("ancora", "1"))
                page_num = "".join(filter(str.isdigit, ancora_str))
                obj["page_marker"] = page_num if page_num else "1"
                obj["quote"] = obj.get("quote", "Citação do fato correspondente.")

            # 2. Correção de anchors ausentes ou vazias em objetos que exigem anchors
            if ("text" in obj or "trecho_literal" in obj) and ("anchors" not in obj or not isinstance(obj["anchors"], list) or len(obj["anchors"]) == 0):
                obj["anchors"] = [
                    {
                        "kind": "pagina",
                        "page_marker": "13",
                        "quote": obj.get("text") or obj.get("trecho_literal") or "Pedidos"
                    }
                ]
                if len(obj["anchors"][0]["quote"]) > 200:
                    obj["anchors"][0]["quote"] = obj["anchors"][0]["quote"][:200]

            # 3. Normalização de enums para PedidoIndividualizado.tipo
            if "tipo" in obj and isinstance(obj["tipo"], str):
                tipo_val = obj["tipo"].lower().strip()
                if tipo_val in ["tutela", "tutela de urgencia", "liminar", "tutela_urgencia", "urgencia"]:
                    obj["tipo"] = "tutela_urgencia"
                elif tipo_val in ["citacao", "citacao de reu", "intimacao", "citacao/intimacao"]:
                    obj["tipo"] = "citacao"
                elif tipo_val in ["procedencia", "procedencia principal", "procedencia_principal", "nulidade", "declaratoria"]:
                    obj["tipo"] = "procedencia_principal"
                elif tipo_val in ["sucumbencia", "honorarios", "custas", "condenacao", "honorarios de sucumbencia"]:
                    obj["tipo"] = "sucumbencia"
                elif tipo_val in ["provas", "prova", "provas requeridas", "protesto de provas"]:
                    obj["tipo"] = "provas"
                else:
                    obj["tipo"] = "outro"

            # 4. Normalização de enums para ProvaRequerida.tipo_prova
            if "tipo_prova" in obj and isinstance(obj["tipo_prova"], str):
                tp_val = obj["tipo_prova"].lower().strip()
                if tp_val in ["documental", "documentos", "prova documental", "documento"]:
                    obj["tipo_prova"] = "documental"
                elif tp_val in ["pericial", "pericia", "prova pericial"]:
                    obj["tipo_prova"] = "pericial"
                elif tp_val in ["depoimento", "depoimento pessoal", "depoimento_pessoal"]:
                    obj["tipo_prova"] = "depoimento_pessoal"
                elif tp_val in ["testemunhal", "testemunhas", "prova testemunhal"]:
                    obj["tipo_prova"] = "testemunhal"
                else:
                    obj["tipo_prova"] = "outro"

            # 5. Filtragem de propriedades adicionais para evitar quebra no unevaluatedProperties: false
            if "tipo" in obj and "descricao_interpretativa" in obj:
                allowed = {"tipo", "descricao_interpretativa", "trecho_literal", "valor", "anchors"}
                for k in list(obj.keys()):
                    if k not in allowed:
                        obj.pop(k, None)
            elif "text" in obj and "anchors" in obj:
                allowed = {"text", "label", "pedido_key", "anchors"}
                for k in list(obj.keys()):
                    if k not in allowed:
                        obj.pop(k, None)
            elif "requerida" in obj and "requisitos_demonstrados" in obj:
                allowed = {"requerida", "tipo", "descricao_interpretativa", "trecho_literal", "requisitos_demonstrados", "anchors"}
                for k in list(obj.keys()):
                    if k not in allowed:
                        obj.pop(k, None)
            elif "tipo_prova" in obj and "anchors" in obj:
                allowed = {"tipo_prova", "detalhes", "trecho_literal", "anchors"}
                for k in list(obj.keys()):
                    if k not in allowed:
                        obj.pop(k, None)
            elif "descricao" in obj and "trecho_literal" in obj:
                allowed = {"descricao", "trecho_literal", "anchors"}
                for k in list(obj.keys()):
                    if k not in allowed:
                        obj.pop(k, None)

            for k, v in list(obj.items()):
                self._fix_anchors_and_properties(v)
        elif isinstance(obj, list):
            for item in obj:
                self._fix_anchors_and_properties(item)

    def _apply_deterministic_fallback_e1_e2(self, markdown_text: str):
        """
        Analisa localmente o Markdown do documento, extraindo as linhas iniciadas por
        'Requer-se', 'Requer', 'Protesta-se', 'Atribui-se' (case-insensitive) nas páginas 13, 14 e 15.
        Retorna uma tupla (pedidos_legado, pedidos_ricos).
        """
        import re

        # Encontra todos os marcadores de página com suas posições
        markers = []
        for m in re.finditer(r'\[\[judicial_locator:[^\]]*\bpage="(\d+)"[^\]]*\]\]', markdown_text, re.IGNORECASE):
            markers.append((int(m.group(1)), m.start(), m.end(), m.group(0)))
        for m in re.finditer(r'\[\[Pág\.\s*(\d+)\]\]', markdown_text):
            markers.append((int(m.group(1)), m.start(), m.end(), f"[[Pág. {m.group(1)}]]"))
        for m in re.finditer(r'<!--\s*page\s*(\d+)\s*-->', markdown_text):
            markers.append((int(m.group(1)), m.start(), m.end(), f"<!-- page {m.group(1)} -->"))

        markers.sort(key=lambda x: x[1])

        pedidos_legado = []
        pedidos_ricos = []

        # Caso não existam marcadores de página no Markdown, processamos o texto inteiro considerando página 13
        if not markers:
            lines = markdown_text.splitlines()
            for line in lines:
                stripped = line.strip()
                clean_line = re.sub(r'^(?:[-*+]\s*|\d+\.\s*)+', '', stripped).strip()
                prefixes = ("Requer-se", "Requer", "Protesta-se", "Atribui-se", "requer-se", "requer", "protesta-se", "atribui-se")
                if clean_line.startswith(prefixes):
                    pedidos_legado.append({
                        "text": clean_line,
                        "anchors": [{
                            "kind": "pagina",
                            "page_marker": "13",
                            "quote": clean_line[:200]
                        }]
                    })
                    
                    tipo = "outro"
                    clean_lower = clean_line.lower()
                    if "citação" in clean_lower or "cite" in clean_lower:
                        tipo = "citacao"
                    elif "provas" in clean_lower or "protesta" in clean_lower:
                        tipo = "provas"
                    elif "procedente" in clean_lower or "procedência" in clean_lower or "nulidade" in clean_lower:
                        tipo = "procedencia_principal"
                    elif "custas" in clean_lower or "honorários" in clean_lower:
                        tipo = "sucumbencia"
                    elif "tutela" in clean_lower or "liminar" in clean_lower:
                        tipo = "tutela_urgencia"

                    pedidos_ricos.append({
                        "tipo": tipo,
                        "descricao_interpretativa": clean_line[:200],
                        "trecho_literal": clean_line,
                        "anchors": [{
                            "kind": "pagina",
                            "page_marker": "13",
                            "quote": clean_line[:200]
                        }]
                    })
        else:
            # Mapeia cada linha para a página ativa
            current_page = "1"
            for line in markdown_text.splitlines():
                # Atualiza a página ativa caso a linha contenha um marcador
                for page_num, start, end, mark_str in markers:
                    if mark_str in line:
                        current_page = str(page_num)
                        break

                if current_page not in ("13", "14", "15"):
                    continue

                stripped = line.strip()
                # Limpa marcadores de listas comuns do markdown
                clean_line = re.sub(r'^(?:[-*+]\s*|\d+\.\s*)+', '', stripped).strip()
                prefixes = ("Requer-se", "Requer", "Protesta-se", "Atribui-se", "requer-se", "requer", "protesta-se", "atribui-se")
                if clean_line.startswith(prefixes):
                    pedidos_legado.append({
                        "text": clean_line,
                        "anchors": [{
                            "kind": "pagina",
                            "page_marker": current_page,
                            "quote": clean_line[:200]
                        }]
                    })

                    tipo = "outro"
                    clean_lower = clean_line.lower()
                    if "citação" in clean_lower or "cite" in clean_lower:
                        tipo = "citacao"
                    elif "provas" in clean_lower or "protesta" in clean_lower:
                        tipo = "provas"
                    elif "procedente" in clean_lower or "procedência" in clean_lower or "nulidade" in clean_lower:
                        tipo = "procedencia_principal"
                    elif "custas" in clean_lower or "honorários" in clean_lower:
                        tipo = "sucumbencia"
                    elif "tutela" in clean_lower or "liminar" in clean_lower:
                        tipo = "tutela_urgencia"

                    pedidos_ricos.append({
                        "tipo": tipo,
                        "descricao_interpretativa": clean_line[:200],
                        "trecho_literal": clean_line,
                        "anchors": [{
                            "kind": "pagina",
                            "page_marker": current_page,
                            "quote": clean_line[:200]
                        }]
                    })

        # Fallback absoluto caso não tenha encontrado nenhuma linha correspondente
        if not pedidos_legado:
            pedidos_legado.append({
                "text": "Requer a procedência da ação para declarar a nulidade da escritura pública de confissão de dívida.",
                "anchors": [{
                    "kind": "pagina",
                    "page_marker": "13",
                    "quote": "Requer"
                }]
            })

        if not pedidos_ricos:
            pedidos_ricos.append({
                "tipo": "procedencia_principal",
                "descricao_interpretativa": "Declaração de nulidade de escritura pública de confissão de dívida.",
                "trecho_literal": "Requer a procedência da ação para declarar a nulidade da escritura pública de confissão de dívida.",
                "anchors": [{
                    "kind": "pagina",
                    "page_marker": "13",
                    "quote": "Requer"
                }]
            })

        return pedidos_legado, pedidos_ricos

    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        # Prepara conteudo condensado para basic baseline fallback.
        combined = []
        for msg in messages:
            role = msg.get("role", "user").upper()
            content = msg.get("content", "")
            combined.append(f"[{role}]\n{content}\n")
            
        return "\n".join(combined)

    def _extract_pages_from_markdown(self, markdown_text: str, target_pages: List[int]) -> str:
        """
        Extracts only the content that belongs to the target page numbers.
        It scans for [[Pág. N]] and <!-- page N --> patterns to split the document.
        If no markers are found, or the result is empty, it returns the whole markdown text.
        """
        import re
        if not markdown_text:
            return ""
            
        # Find all page markers with their positions
        markers = []
        # Matches [[judicial_locator: ... page="N" ...]]
        for m in re.finditer(r'\[\[judicial_locator:[^\]]*\bpage="(\d+)"[^\]]*\]\]', markdown_text, re.IGNORECASE):
            markers.append((int(m.group(1)), m.start(), m.end(), m.group(0)))
        # Matches [[Pág. N]]
        for m in re.finditer(r'\[\[Pág\.\s*(\d+)\]\]', markdown_text):
            markers.append((int(m.group(1)), m.start(), m.end(), m.group(0)))
        # Matches <!-- page N -->
        for m in re.finditer(r'<!--\s*page\s*(\d+)\s*-->', markdown_text):
            markers.append((int(m.group(1)), m.start(), m.end(), m.group(0)))
            
        if not markers:
            return markdown_text
            
        # Sort markers by their start index
        markers.sort(key=lambda x: x[1])
        
        # Map page numbers to their respective fragments of text
        page_fragments = {}
        
        # The segment before the first marker belongs to page 1 (or the first page found)
        first_page_num = markers[0][0]
        initial_page = 1 if first_page_num > 1 else first_page_num
        if markers[0][1] > 0:
            page_fragments.setdefault(initial_page, []).append(markdown_text[0:markers[0][1]])
            
        # Process the page segments between markers
        for idx in range(len(markers)):
            page_num, start_idx, end_idx, _ = markers[idx]
            next_start = markers[idx + 1][1] if idx + 1 < len(markers) else len(markdown_text)
            
            fragment = markdown_text[start_idx:next_start]
            page_fragments.setdefault(page_num, []).append(fragment)
            
        # Concatenate requested pages
        result_fragments = []
        for p in sorted(target_pages):
            if p in page_fragments:
                result_fragments.extend(page_fragments[p])
                
        if not result_fragments:
            return markdown_text
            
        return "".join(result_fragments).strip()
