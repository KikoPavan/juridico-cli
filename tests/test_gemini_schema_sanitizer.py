#!/usr/bin/env python3
"""
Unit tests for the Gemini Schema Sanitizer in packages/shared-llm/gemini_client.py.
"""

import json
import sys
from pathlib import Path

import importlib.util

# Adiciona o diretório shared-llm ao pythonpath e registra client_mod/gemini_client dinamicamente para compatibilidade
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "packages" / "shared-llm"))

# Carrega client dinamicamente para evitar missing-import no linter
client_path = str(ROOT_DIR / "packages" / "shared-llm" / "client.py")
spec_client = importlib.util.spec_from_file_location("client_mod", client_path)
client_mod = importlib.util.module_from_spec(spec_client)
sys.modules["client_mod"] = client_mod
sys.modules["client"] = client_mod
spec_client.loader.exec_module(client_mod)

# Carrega gemini_client dinamicamente para evitar missing-import no linter
gemini_path = str(ROOT_DIR / "packages" / "shared-llm" / "gemini_client.py")
spec_gemini = importlib.util.spec_from_file_location("gemini_client_mod", gemini_path)
gemini_client_mod = importlib.util.module_from_spec(spec_gemini)
sys.modules["gemini_client"] = gemini_client_mod
spec_gemini.loader.exec_module(gemini_client_mod)

GeminiLLMClient = gemini_client_mod.GeminiLLMClient

SHARED_SCHEMAS_DIR = ROOT_DIR / "packages" / "shared-schemas"
sys.path.insert(0, str(SHARED_SCHEMAS_DIR))
from local_resolver import load_validator  # noqa: E402


SCHEMA_PATH = ROOT_DIR / "platform" / "skills" / "extr-peticao-processo" / "assets" / "peticao_processo.schema.json"


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _assert_no_prohibited_keys(node, path="root"):
    """Verifica recursivamente que nenhuma chave proibida existe em qualquer profundidade."""
    prohibited_keys = {
        "$schema", "$id", "$defs", "$ref", "defs/common.schema.json",
        "$vocabulary", "$anchor", "$dynamicRef", "$dynamicAnchor",
        "unevaluatedProperties", "patternProperties", "dependentSchemas",
        "if", "then", "else", "not", "oneOf", "allOf"
    }
    
    if isinstance(node, dict):
        for k, v in node.items():
            current_path = f"{path} -> {k}"
            assert k not in prohibited_keys, f"Forbidden key '{k}' found at path: {current_path}"
            _assert_no_prohibited_keys(v, current_path)
    elif isinstance(node, list):
        for idx, item in enumerate(node):
            _assert_no_prohibited_keys(item, f"{path}[{idx}]")


def test_gemini_schema_sanitizer():
    """Garante que a sanitização remove todas as chaves proibidas e resolve refs por inline."""
    schema = load_json(SCHEMA_PATH)
    
    # Instancia o cliente do Gemini com chave mockada
    client = GeminiLLMClient(api_key="ficticia")
    
    # Executa a normalização/sanitização
    sanitized = client._normalize_schema(schema)
    
    # 1. Verifica chaves proibidas em toda a árvore do schema
    _assert_no_prohibited_keys(sanitized)
    
    # 2. Verifica se a estrutura de chaves permitidas está correta na raiz
    allowed_keys = {
        "type", "title", "description",
        "properties", "required", "additionalProperties",
        "items", "prefixItems", "minItems", "maxItems",
        "enum", "format", "minimum", "maximum", "anyOf",
    }
    for k in sanitized.keys():
        assert k in allowed_keys, f"Key '{k}' in root is not in the allowed list"
        
    # 3. Garante que os $ref foram de fato resolvidos inline
    # Exemplo: process_number deve ser um objeto inline, e não {"$ref": ...}
    props = sanitized.get("properties", {})
    assert "process_number" in props
    process_num_prop = props["process_number"]
    assert process_num_prop["type"] == "object"
    assert "value" in process_num_prop["properties"]
    assert "anchors" in process_num_prop["properties"]
    
    # Exemplo: As âncoras dentro de process_number devem conter o schema do Anchor inline
    anchors_prop = process_num_prop["properties"]["anchors"]
    assert anchors_prop["type"] == "array"
    anchor_item = anchors_prop["items"]
    assert anchor_item["type"] == "object"
    assert "kind" in anchor_item["properties"]
    assert "page_marker" in anchor_item["properties"]
    assert "quote" in anchor_item["properties"]
    
    # 4. Garante que a conversão de const para enum funciona
    assert sanitized["properties"]["document_type"]["type"] == "string"
    assert sanitized["properties"]["document_type"]["enum"] == ["peticao_processo"]


def test_gemini_live_schema():
    """Teste live opcional que valida se a chamada com o schema sanitizado é aceita pela API do Gemini.
    Só é executado se GEMINI_API_KEY estiver presente no ambiente.
    """
    import os
    import pytest
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY não configurada no ambiente. Pulando teste live.")
        
    schema = load_json(SCHEMA_PATH)
    client = GeminiLLMClient(api_key=api_key)
    
    # 1. Testar schema mínimo para ver se conexão básica e auth estão OK
    minimal_schema = {
        "type": "object",
        "required": ["document_type"],
        "properties": {
            "document_type": {
                "type": "string",
                "enum": ["peticao_processo"]
            }
        }
    }
    
    try:
        res_min = client.generate_structured([{"role": "user", "content": "retorne o document_type como peticao_processo"}], minimal_schema)
        assert res_min.get("document_type") == "peticao_processo"
        print("Live: Schema mínimo passou!")
    except Exception as exc:
        pytest.fail(f"Erro na conexão com schema mínimo: {exc}")
        
    # 2. Testar o schema completo sanitizado
    try:
        res_full = client.generate_structured([{"role": "user", "content": "retorne um JSON vazio ou com dados mínimos coerentes"}], schema)
        print("Live: Schema completo sanitizado passou com sucesso!")
        assert isinstance(res_full, dict)
    except Exception as exc:
        # Se falhar aqui, indica que o schema sanitizado causou a rejeição da API
        pytest.fail(
            f"O schema mínimo passou, mas o schema completo sanitizado causou falha na API do Gemini. "
            f"Isso indica complexidade/incompatibilidade no schema sanitizado. Erro: {exc}"
        )


def test_gemini_fallback_logic_and_blocks():
    """Valida a esteira de blocos e a auto-correção de formato de anchors para o
    schema completo de extr-peticao-processo.

    O schema completo tem 25 propriedades top-level, 34.5KB e 370 nós — acima
    dos limiares de preflight de compatibilidade com response_schema
    (_SCHEMA_PREFLIGHT_*, ver gemini-response-schema-preflight). Por isso, o
    sistema nunca tenta a chamada estruturada inicial nem o fallback livre para
    esse schema: escala direto para a extração por blocos. A cobertura do
    caminho de fallback livre para schemas compatíveis está em
    test_gemini_fallback_low_risk_uses_free_form_path.
    """
    import os
    import tempfile
    import json
    from unittest.mock import MagicMock, patch

    schema = load_json(SCHEMA_PATH)
    client = GeminiLLMClient(api_key="mock")

    # Como o preflight decide pular a chamada estruturada inicial para esse
    # schema, a primeira chamada real a generate_content já é a do Bloco A.
    # Vamos mockar o self.client.models.generate_content para:
    # 1ª a 9ª chamada (blocos A, B, C, D, E1-E5): retornam JSONs parciais válidos

    # Retornos para os blocos A, B, C, D, E
    # Bloco A: ["document_type", "peticao_identification", "process_number", "parties", "representations", "valor_da_causa"]
    mock_block_A = MagicMock()
    mock_block_A.text = json.dumps({
        "document_type": "peticao_processo",
        "process_number": {
            "value": "0001234-56.2026.8.26.0100",
            "anchors": [{"kind": "pagina", "page_marker": "1", "quote": "Proc. 0001234"}]
        }
    })
    
    # Bloco B: ["document_type", "fatos", "fatos_cronologicos", "atos_juridicos", "documentos_citados"]
    # Aqui vamos retornar uma âncora com formato inválido "fonte" no bloco B para testar a auto-correção!
    mock_block_B = MagicMock()
    mock_block_B.text = json.dumps({
        "document_type": "peticao_processo",
        "fatos": [{
            "text": "O autor firmou contrato...",
            "anchors": [{
                "fonte": {
                    "arquivo_md": "peticao.md",
                    "ancora": "Pág. 3"
                },
                "quote": "O autor firmou contrato..."
            }]
        }]
    })
    
    # Bloco C: ["document_type", "pessoas_mencionadas", "empresas_mencionadas", "imoveis_e_matriculas", "garantias_e_gravames"]
    mock_block_C = MagicMock()
    mock_block_C.text = json.dumps({
        "document_type": "peticao_processo",
        "pessoas_mencionadas": []
    })
    
    # Bloco D: ["document_type", "fundamentos_legais", "teses_juridicas", "processos_relacionados"]
    mock_block_D = MagicMock()
    mock_block_D.text = json.dumps({
        "document_type": "peticao_processo",
        "fundamentos_legais": []
    })
    
    # Bloco E1: ["document_type", "pedidos"]
    mock_block_E1 = MagicMock()
    mock_block_E1.text = json.dumps({
        "document_type": "peticao_processo",
        "pedidos": [{
            "text": "Seja julgado procedente o pedido...",
            "anchors": [{"kind": "pagina", "page_marker": "12", "quote": "Seja julgado..."}]
        }]
    })

    # Bloco E2: ["document_type", "pedidos_individualizados"]
    mock_block_E2 = MagicMock()
    mock_block_E2.text = json.dumps({
        "document_type": "peticao_processo",
        "pedidos_individualizados": [{
            "tipo": "procedencia_principal",
            "descricao_interpretativa": "Declarar a nulidade",
            "trecho_literal": "Seja julgado procedente o pedido para declarar nula a escritura",
            "anchors": [{"kind": "pagina", "page_marker": "14", "quote": "declarar nula"}]
        }]
    })

    # Bloco E3: ["document_type", "tutela_urgencia"]
    mock_block_E3 = MagicMock()
    mock_block_E3.text = json.dumps({
        "document_type": "peticao_processo",
        "tutela_urgencia": {
            "requerida": True,
            "tipo": "antecipada",
            "descricao_interpretativa": "Suspensão de leilão",
            "trecho_literal": "Requer tutela antecipada para suspensão",
            "requisitos_demonstrados": [
                {
                    "requisito": "perigo_dano",
                    "argumento": "Leilão iminente",
                    "trecho_literal": "perigo na demora do provimento"
                }
            ],
            "anchors": [{"kind": "pagina", "page_marker": "13", "quote": "tutela antecipada"}]
        }
    })

    # Bloco E4: ["document_type", "provas_requeridas"]
    mock_block_E4 = MagicMock()
    mock_block_E4.text = json.dumps({
        "document_type": "peticao_processo",
        "provas_requeridas": [{
            "tipo_prova": "pericial",
            "detalhes": "Perícia contábil",
            "trecho_literal": "Protesta por prova pericial",
            "anchors": [{"kind": "pagina", "page_marker": "15", "quote": "prova pericial"}]
        }]
    })

    # Bloco E5: ["document_type", "riscos_ou_pontos_de_atencao"]
    mock_block_E5 = MagicMock()
    mock_block_E5.text = json.dumps({
        "document_type": "peticao_processo",
        "riscos_ou_pontos_de_atencao": []
    })
    
    # Mockando generate_content sequencialmente: só os 9 blocos, sem chamada
    # estruturada inicial nem fallback livre (pulados pelo preflight).
    # 1ª chamada estruturada bloco A
    # 2ª chamada estruturada bloco B
    # 3ª chamada estruturada bloco C
    # 4ª chamada estruturada bloco D
    # 5ª chamada estruturada bloco E1
    # 6ª chamada estruturada bloco E2
    # 7ª chamada estruturada bloco E3
    # 8ª chamada estruturada bloco E4
    # 9ª chamada estruturada bloco E5
    mock_generate = MagicMock(side_effect=[
        mock_block_A,                          # bloco A
        mock_block_B,                          # bloco B
        mock_block_C,                          # bloco C
        mock_block_D,                          # bloco D
        mock_block_E1,                         # bloco E1
        mock_block_E2,                         # bloco E2
        mock_block_E3,                         # bloco E3
        mock_block_E4,                         # bloco E4
        mock_block_E5                          # bloco E5
    ])

    with patch.object(client.client.models, 'generate_content', mock_generate):
        # Executa a chamada structured que deve escalar direto para os blocos
        result = client.generate_structured([{"role": "user", "content": "teste"}], schema)

        # 1. Verifica se retornou consolidado válido
        assert isinstance(result, dict)
        assert result.get("document_type") == "peticao_processo"
        assert result["process_number"]["value"] == "0001234-56.2026.8.26.0100"

        # 2. Verifica se a âncora do Bloco B que continha a chave 'fonte' foi adequadamente corrigida!
        fatos = result.get("fatos", [])
        assert len(fatos) == 1
        fatos_anchors = fatos[0]["anchors"]
        assert len(fatos_anchors) == 1
        anchor = fatos_anchors[0]
        # Não pode conter a chave 'fonte'
        assert "fonte" not in anchor
        # Deve conter as chaves corretas
        assert anchor["kind"] == "pagina"
        assert anchor["page_marker"] == "3"
        assert anchor["quote"] == "O autor firmou contrato..."

        # 3. Verifica que nem a chamada estruturada inicial nem o fallback livre
        # foram feitos: apenas as 9 chamadas de bloco.
        assert mock_generate.call_count == 9

        # 4. Verifica que as chaves do Bloco E estão presentes e não são None
        for campo in ["pedidos", "pedidos_individualizados", "tutela_urgencia", "provas_requeridas", "riscos_ou_pontos_de_atencao"]:
            assert campo in result, f"Chave {campo} deve estar presente no JSON final"
            assert result[campo] is not None, f"Chave {campo} não deve ser None"
            
        # 5. Verifica se os valores estruturados do Bloco E estão preenchidos com os dados reais/mockados correspondentes
        assert len(result["pedidos"]) == 1
        assert result["pedidos"][0]["text"] == "Seja julgado procedente o pedido..."
        assert len(result["pedidos_individualizados"]) == 1
        assert result["pedidos_individualizados"][0]["tipo"] == "procedencia_principal"
        assert result["tutela_urgencia"]["requerida"] is True
        assert len(result["provas_requeridas"]) == 1
        assert result["provas_requeridas"][0]["tipo_prova"] == "pericial"
        assert isinstance(result["riscos_ou_pontos_de_atencao"], list)


def test_gemini_fallback_low_risk_uses_free_form_path():
    """Para um schema pequeno (poucas propriedades top-level) e um Markdown de
    entrada curto — abaixo dos limiares de risco de truncamento —, a falha da
    chamada estruturada deve continuar caindo no fallback livre existente
    (schema embutido no prompt, sem response_schema), em vez de escalar direto
    para a extração por blocos."""
    from unittest.mock import MagicMock, patch

    client = GeminiLLMClient(api_key="mock")

    small_schema = {
        "type": "object",
        "required": ["document_type"],
        "properties": {
            "document_type": {"type": "string", "enum": ["peticao_processo"]},
            "valor_da_causa": {"type": "string"},
        },
    }

    mock_free_form_response = MagicMock()
    mock_free_form_response.text = json.dumps({
        "document_type": "peticao_processo",
        "valor_da_causa": "R$ 1.000,00",
    })
    mock_free_form_response.candidates = [MagicMock(finish_reason="STOP")]
    mock_free_form_response.usage_metadata = MagicMock(
        prompt_token_count=50, candidates_token_count=20, total_token_count=70
    )

    mock_generate = MagicMock(side_effect=[
        Exception("Schema 400 rejection"),  # chamada estruturada inicial falha
        mock_free_form_response,            # fallback livre (sem response_schema) sucede
    ])

    with patch.object(client.client.models, "generate_content", mock_generate):
        result = client.generate_structured(
            [{"role": "user", "content": "petição curta"}], small_schema
        )

        assert result == {
            "document_type": "peticao_processo",
            "valor_da_causa": "R$ 1.000,00",
        }
        # Só duas chamadas: a estruturada (que falhou) e o fallback livre que
        # sucedeu — nenhuma chamada de bloco foi feita.
        assert mock_generate.call_count == 2


def test_gemini_fallback_escalation_is_deterministic_across_runs():
    """A decisão de preflight de pular a chamada estruturada inicial para um
    schema de alto risco (grande/complexo) depende apenas do schema sanitizado
    em si, então deve ser a mesma em execuções independentes com a mesma
    entrada — sem depender de qualquer resposta do Gemini, e sem nunca chamar
    generate_content com o schema completo."""
    import json as json_mod
    from unittest.mock import MagicMock, patch

    schema = load_json(SCHEMA_PATH)  # schema real: 25 propriedades top-level, alto risco

    def _make_block_mock():
        mock_resp = MagicMock()
        mock_resp.text = json_mod.dumps({"document_type": "peticao_processo"})
        return mock_resp

    call_counts = []
    for _ in range(2):
        client = GeminiLLMClient(api_key="mock")
        mock_generate = MagicMock(side_effect=lambda *a, **kw: _make_block_mock())

        with patch.object(client.client.models, "generate_content", mock_generate):
            # Os blocos mockados só retornam "document_type"; a extração final
            # pode terminar com ressalvas (_failed_blocks) — irrelevante para o
            # que este teste verifica: quais chamadas foram feitas ao Gemini,
            # não se a extração final é válida.
            client.generate_structured([{"role": "user", "content": "teste"}], schema)

            # Nenhuma chamada usa o schema completo (a chamada estruturada
            # inicial nunca acontece: o preflight já decidiu ir para blocos) —
            # todas as chamadas feitas são chamadas de bloco, com no máximo 6
            # propriedades top-level cada.
            for call in mock_generate.call_args_list:
                config = call.kwargs.get("config")
                assert config is not None
                block_schema = getattr(config, "response_json_schema", None)
                assert block_schema is not None
                assert len(block_schema.get("properties", {})) <= 6

            call_counts.append(mock_generate.call_count)

    # A mesma quantidade de chamadas (uma por bloco, nenhuma chamada
    # estruturada de schema completo) ocorre em ambas as execuções.
    assert call_counts[0] == call_counts[1]


def test_gemini_fallback_e1_e2_heuristic():
    from unittest.mock import MagicMock, patch
    client = GeminiLLMClient(api_key="mock")
    
    # Mock do schema rico
    schema = {
        "type": "object",
        "required": ["document_type", "pedidos", "pedidos_individualizados", "tutela_urgencia", "provas_requeridas", "riscos_ou_pontos_de_atencao"],
        "properties": {
            "document_type": { "const": "peticao_processo" },
            "pedidos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["text", "anchors"],
                    "properties": {
                        "text": { "type": "string" },
                        "anchors": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["kind", "page_marker", "quote"],
                                "properties": {
                                    "kind": { "type": "string" },
                                    "page_marker": { "type": "string" },
                                    "quote": { "type": "string" }
                                }
                            }
                        }
                    }
                }
            },
            "pedidos_individualizados": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["tipo", "descricao_interpretativa", "trecho_literal", "anchors"],
                    "properties": {
                        "tipo": { "type": "string" },
                        "descricao_interpretativa": { "type": "string" },
                        "trecho_literal": { "type": "string" },
                        "anchors": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["kind", "page_marker", "quote"],
                                "properties": {
                                    "kind": { "type": "string" },
                                    "page_marker": { "type": "string" },
                                    "quote": { "type": "string" }
                                }
                            }
                        }
                    }
                }
            },
            "tutela_urgencia": {
                "type": "object",
                "required": ["requerida", "tipo", "descricao_interpretativa", "trecho_literal", "requisitos_demonstrados", "anchors"],
                "properties": {
                    "requerida": { "type": "boolean" },
                    "tipo": { "type": "string" },
                    "descricao_interpretativa": { "type": "string" },
                    "trecho_literal": { "type": "string" },
                    "requisitos_demonstrados": { "type": "array", "items": { "type": "object" } },
                    "anchors": { "type": "array", "items": { "type": "object" } }
                }
            },
            "provas_requeridas": { "type": "array", "items": { "type": "object" } },
            "riscos_ou_pontos_de_atencao": { "type": "array", "items": { "type": "object" } }
        }
    }
    
    # Criamos um markdown de entrada simulando as paginas 13, 14, 15
    mock_md = (
        "Texto inicial da petição...\n"
        "[[Pág. 13]]\n"
        "Requer-se a citação do réu Banco do Brasil.\n"
        "[[Pág. 14]]\n"
        "Requer a procedência total para declarar a nulidade da escritura.\n"
        "[[Pág. 15]]\n"
        "Protesta-se por provas documentais e periciais.\n"
    )
    
    # Mockando responses
    mock_block_A_D = MagicMock()
    mock_block_A_D.text = json.dumps({
        "document_type": "peticao_processo"
    })

    mock_response_2 = MagicMock()
    mock_response_2.text = '{"document_type": "peticao_processo", "process_number": {"value": "' # truncado
    mock_candidate_2 = MagicMock()
    mock_candidate_2.finish_reason = "MAX_TOKENS"
    mock_response_2.candidates = [mock_candidate_2]
    mock_response_2.usage_metadata = MagicMock(prompt_token_count=100, candidates_token_count=8192, total_token_count=8292)

    mock_response_retry_failed = MagicMock()
    mock_response_retry_failed.text = '{"document_type": "peticao_processo", '  # JSON quebrado de novo
    mock_candidate_retry = MagicMock()
    mock_candidate_retry.finish_reason = "MAX_TOKENS"
    mock_response_retry_failed.candidates = [mock_candidate_retry]
    mock_response_retry_failed.usage_metadata = MagicMock(prompt_token_count=100, candidates_token_count=8192, total_token_count=8292)
    
    # Mockando generate_content sequencialmente
    # 1ª chamada estruturada falha
    # 2ª chamada fallback retorna truncado
    # 3ª chamada retry do fallback falha com json truncado -> ativando Extração em Blocos
    # 4ª chamada Bloco A (sucesso)
    # 5ª chamada Bloco B (sucesso)
    # 6ª chamada Bloco C (sucesso)
    # 7ª chamada Bloco D (sucesso)
    # 8ª chamada Bloco E1 (chamada estruturada falha)
    # 9ª chamada Bloco E1 (chamada fallback falha) -> ativando fallback determinístico de E1
    # 10ª chamada Bloco E2 (chamada estruturada falha)
    # 11ª chamada Bloco E2 (chamada fallback falha) -> ativando fallback determinístico de E2
    # 12ª chamada Bloco E3 (sucesso)
    # 13ª chamada Bloco E4 (sucesso)
    # 14ª chamada Bloco E5 (sucesso)
    mock_generate = MagicMock(side_effect=[
        Exception("API error"),         # chamada 1 (estruturada completa)
        mock_response_2,                # chamada 2 (fallback completo)
        mock_response_retry_failed,     # chamada 3 (retry do fallback)
        mock_block_A_D,                 # bloco A
        mock_block_A_D,                 # bloco B
        mock_block_A_D,                 # bloco C
        mock_block_A_D,                 # bloco D
        Exception("LLM E1 error"),      # bloco E1 estruturada
        Exception("LLM E1 error"),      # bloco E1 fallback
        Exception("LLM E2 error"),      # bloco E2 estruturada
        Exception("LLM E2 error"),      # bloco E2 fallback
        mock_block_A_D,                 # bloco E3
        mock_block_A_D,                 # bloco E4
        mock_block_A_D                  # bloco E5
    ])
    
    with patch.object(client.client.models, 'generate_content', mock_generate):
        messages = [{"role": "user", "content": mock_md}]
        result = client.generate_structured(messages, schema)
        
        # 1. Deve conter a chave privada dos blocos falhos
        assert "_failed_blocks" in result
        assert "E1" in result["_failed_blocks"]
        assert "E2" in result["_failed_blocks"]
        
        # 2. Verificar se a heurística de E1 (pedidos) extraiu as linhas certas com as páginas certas
        pedidos = result["pedidos"]
        assert len(pedidos) >= 2
        
        # Requer-se a citação...
        assert pedidos[0]["text"] == "Requer-se a citação do réu Banco do Brasil."
        assert pedidos[0]["anchors"][0]["page_marker"] == "13"
        
        # Requer a procedência...
        assert pedidos[1]["text"] == "Requer a procedência total para declarar a nulidade da escritura."
        assert pedidos[1]["anchors"][0]["page_marker"] == "14"
        
        # 3. Verificar se a heurística de E2 (pedidos_individualizados) extraiu e normalizou corretamente
        pedidos_ind = result["pedidos_individualizados"]
        assert len(pedidos_ind) >= 2
        assert pedidos_ind[0]["tipo"] == "citacao"
        assert pedidos_ind[0]["trecho_literal"] == "Requer-se a citação do réu Banco do Brasil."
        assert pedidos_ind[0]["anchors"][0]["page_marker"] == "13"
        
        assert pedidos_ind[1]["tipo"] == "procedencia_principal"
        assert pedidos_ind[1]["trecho_literal"] == "Requer a procedência total para declarar a nulidade da escritura."
        assert pedidos_ind[1]["anchors"][0]["page_marker"] == "14"
        
        # 4. Verificar se os arquivos de debug específicos foram gravados
        debug_dir = ROOT_DIR / "var" / "artifacts" / "gemini-debug"
        assert (debug_dir / "block_E1_parse_error.txt").exists()
        assert (debug_dir / "block_E2_parse_error.txt").exists()


def test_gemini_block_page_cutting():
    """Valida o recorte de páginas inteligente baseado em marcadores no Markdown."""
    client = GeminiLLMClient(api_key="mock")
    
    # Caso 1: Sem marcadores de página (deve retornar o texto completo)
    md_sem_marcadores = "Este é um texto corrido sem marcadores de página."
    assert client._extract_pages_from_markdown(md_sem_marcadores, [1, 2]) == md_sem_marcadores
    
    # Caso 2: Marcadores com [[Pág. N]] e <!-- page N -->
    md_misto = (
        "Cabeçalho inicial da petição\n"
        "[[Pág. 1]]\n"
        "Texto da página um\n"
        "[[Pág. 2]]\n"
        "Texto da página dois\n"
        "<!-- page 3 -->\n"
        "Texto da página três\n"
        "[[Pág. 13]]\n"
        "Texto da página treze\n"
        "<!-- page 14 -->\n"
        "Texto da página quatorze\n"
        "[[Pág. 15]]\n"
        "Texto da página quinze\n"
    )
    
    # Testar extração de apenas páginas 13, 14, 15
    extracted_13_15 = client._extract_pages_from_markdown(md_misto, [13, 14, 15])
    assert "[[Pág. 13]]" in extracted_13_15
    assert "Texto da página treze" in extracted_13_15
    assert "<!-- page 14 -->" in extracted_13_15
    assert "Texto da página quatorze" in extracted_13_15
    assert "[[Pág. 15]]" in extracted_13_15
    assert "Texto da página quinze" in extracted_13_15
    # Não deve ter conteúdo de páginas iniciais
    assert "Texto da página um" not in extracted_13_15
    assert "Texto da página dois" not in extracted_13_15
    assert "Texto da página três" not in extracted_13_15
    
    # Testar extração de páginas 1 e 15
    extracted_1_15 = client._extract_pages_from_markdown(md_misto, [1, 15])
    assert "[[Pág. 1]]" in extracted_1_15
    assert "Texto da página um" in extracted_1_15
    assert "[[Pág. 15]]" in extracted_1_15
    assert "Texto da página quinze" in extracted_1_15
    assert "Texto da página dois" not in extracted_1_15
    assert "Texto da página treze" not in extracted_1_15

    # Caso 3: Fallback se nenhuma das páginas pedidas for encontrada
    extracted_fallback = client._extract_pages_from_markdown(md_misto, [99])
    assert extracted_fallback == md_misto

    # Caso 4: Simular a chamada de extração por blocos para garantir que os payloads das mensagens
    # passados para generate_content foram recortados adequadamente.
    from unittest.mock import MagicMock, patch
    
    # Mockando generate_content para retornar resposta fictícia imediata e parar
    mock_resp = MagicMock()
    mock_resp.text = json.dumps({"document_type": "peticao_processo"})
    
    schema = {
        "type": "object",
        "required": ["document_type", "pedidos", "pessoas_mencionadas"],
        "properties": {
            "document_type": {"const": "peticao_processo"},
            "pedidos": {"type": "array", "items": {"type": "object"}},
            "pessoas_mencionadas": {"type": "array", "items": {"type": "object"}}
        }
    }
    
    messages = [
        {"role": "user", "content": md_misto}
    ]
    
    # Mock do generate_content
    mock_generate = MagicMock(return_value=mock_resp)
    
    # md com um cabeçalho estrutural de pedidos na página 14 (não na 13), para provar
    # que o recorte de E1-E4 segue o cabeçalho e não um número de página fixo.
    md_com_cabecalho = (
        "Cabeçalho inicial da petição\n"
        "[[Pág. 1]]\n"
        "Texto da página um\n"
        "[[Pág. 2]]\n"
        "Texto da página dois\n"
        "<!-- page 3 -->\n"
        "Texto da página três\n"
        "[[Pág. 13]]\n"
        "Texto da página treze\n"
        "<!-- page 14 -->\n"
        "DOS PEDIDOS:\n"
        "Texto da página quatorze\n"
        "[[Pág. 15]]\n"
        "Texto da página quinze\n"
    )
    messages_com_cabecalho = [
        {"role": "user", "content": md_com_cabecalho}
    ]

    with patch.object(client.client.models, 'generate_content', mock_generate):
        try:
            client._execute_extraction_in_blocks(messages, schema, "/tmp", 2000, str(ROOT_DIR))
        except Exception:
            pass

        calls = mock_generate.call_args_list
        assert len(calls) > 0

        # A primeira chamada deve ser do bloco A (ou o primeiro bloco processado que esteja no schema)
        # O bloco A usa mensagens completas, sem recorte
        # Mas no schema de teste reduzido, quais blocos serão gerados?
        # blocks possui:
        # A: ["document_type", "peticao_identification", "process_number", "parties", "representations", "valor_da_causa"]
        # B: ["document_type", "fatos", "fatos_cronologicos", "atos_juridicos", "documentos_citados"]
        # C: ["document_type", "pessoas_mencionadas", "empresas_mencionadas", "imoveis_e_matriculas", "garantias_e_gravames"]
        # D: ["document_type", "fundamentos_legais", "teses_juridicas", "processos_relacionados"]
        # E1: ["document_type", "pedidos"]
        # Como no schema definimos "pedidos" (bloco E1) e "pessoas_mencionadas" (bloco C),
        # as propriedades correspondentes serão extraídas nos blocos C e E1.
        # Vamos verificar que as chamadas feitas para o bloco C e o bloco E1 foram recortadas.
        # As chamadas a generate_content ocorrem para cada bloco do dicionário blocks que tenha propriedades presentes no schema.
        # No nosso schema de teste, temos:
        # - "document_type" -> está em todos os blocos.
        # - "pessoas_mencionadas" -> bloco C.
        # - "pedidos" -> bloco E1.
        # Portanto, _execute_extraction_in_blocks vai tentar processar todos os blocos (A, B, C, D, E1, E2, E3, E4, E5),
        # mas só enviará para o Gemini os blocos que possuem propriedades (além do document_type) no schema,
        # ou se as propriedades forem vazias além de document_type?
        # Vejamos:
        # partial_schema = {
        #     "type": "object",
        #     "required": [f for f in schema.get("required", []) if f in fields],
        #     "properties": {f: schema["properties"][f] for f in fields if f in schema["properties"]}
        # }
        # Se partial_schema["properties"] contiver apenas "document_type", ele ainda executa!
        # Então ele executará chamadas para todos os blocos: A, B, C, D, E1, E2, E3, E4, E5.
        # Vamos mapear os índices de chamadas (supondo que todos os blocos executem generate_content):
        # idx 0: bloco A
        # idx 1: bloco B
        # idx 2: bloco C
        # idx 3: bloco D
        # idx 4: bloco E1
        # Vamos validar isso:
        assert len(calls) >= 5

        # Chamada 2 (bloco C): continua usando recorte por páginas fixas (fora de escopo desta correção)
        call_c_contents = calls[2][1]['contents']
        assert "Texto da página um" in call_c_contents
        assert "Texto da página quinze" in call_c_contents

    # Repete apenas o recorte do bloco E1 com o md que tem cabeçalho estrutural,
    # para validar que o recorte de E1-E4 agora segue o cabeçalho "DOS PEDIDOS"
    # (não um número de página fixo).
    mock_generate_2 = MagicMock(return_value=mock_resp)
    with patch.object(client.client.models, 'generate_content', mock_generate_2):
        try:
            client._execute_extraction_in_blocks(messages_com_cabecalho, schema, "/tmp", 2000, str(ROOT_DIR))
        except Exception:
            pass

        calls_2 = mock_generate_2.call_args_list
        assert len(calls_2) >= 5

        # Bloco E1 (idx 4): deve conter o conteúdo a partir do cabeçalho "DOS PEDIDOS"
        # (página 14), incluindo a página 15, mas NÃO a página 13 (antes do cabeçalho)
        # nem as páginas 1/2/3.
        call_e1_contents = calls_2[4][1]['contents']
        assert "DOS PEDIDOS" in call_e1_contents
        assert "Texto da página quatorze" in call_e1_contents
        assert "Texto da página quinze" in call_e1_contents
        assert "Texto da página treze" not in call_e1_contents
        assert "Texto da página um" not in call_e1_contents
        assert "Texto da página dois" not in call_e1_contents
        assert "Texto da página três" not in call_e1_contents


def test_assess_response_schema_compatibility_small_schema_is_compatible():
    """Um schema pequeno (poucas propriedades, poucos bytes, poucos nós) é
    considerado compatível com response_schema pelo preflight."""
    small_schema = {
        "type": "object",
        "required": ["document_type"],
        "properties": {
            "document_type": {"type": "string", "enum": ["peticao_processo"]},
            "valor_da_causa": {"type": "string"},
        },
    }

    is_compatible, reason = GeminiLLMClient._assess_response_schema_compatibility(small_schema)

    assert is_compatible is True
    assert reason == ""


def test_assess_response_schema_compatibility_real_full_schema_is_incompatible():
    """O schema sanitizado completo de extr-peticao-processo (25 propriedades
    top-level, ~34.5KB, ~370 nós) excede os limiares de preflight e é
    considerado incompatível com response_schema, com um motivo explicando
    qual sinal de complexidade foi excedido."""
    schema = load_json(SCHEMA_PATH)
    client = GeminiLLMClient(api_key="ficticia")
    sanitized = client._normalize_schema(schema)

    is_compatible, reason = GeminiLLMClient._assess_response_schema_compatibility(sanitized)

    assert is_compatible is False
    assert "propriedades top-level" in reason


def test_gemini_preflight_incompatible_schema_never_attempts_structured_or_free_form_call():
    """Para o schema completo (incompatível pelo preflight), nem a chamada
    estruturada inicial nem o fallback livre devem ser tentados: a primeira
    chamada real ao Gemini já deve ser a de um bloco (schema reduzido, <= 6
    propriedades top-level), e nenhum arquivo de erro da chamada estruturada
    deve ser criado, já que nenhuma chamada incompatível foi enviada."""
    import json as json_mod
    from unittest.mock import MagicMock, patch

    schema = load_json(SCHEMA_PATH)
    client = GeminiLLMClient(api_key="mock")

    mock_block_response = MagicMock()
    mock_block_response.text = json_mod.dumps({"document_type": "peticao_processo"})
    mock_generate = MagicMock(side_effect=lambda *a, **kw: mock_block_response)

    debug_dir = ROOT_DIR / "var" / "artifacts" / "gemini-debug"
    structured_error_path = debug_dir / "structured_call_error.txt"
    if structured_error_path.exists():
        structured_error_path.unlink()

    with patch.object(client.client.models, "generate_content", mock_generate):
        client.generate_structured([{"role": "user", "content": "teste"}], schema)

        assert mock_generate.call_count > 0
        first_call_config = mock_generate.call_args_list[0].kwargs["config"]
        first_call_schema = getattr(first_call_config, "response_json_schema", None)
        assert first_call_schema is not None
        assert len(first_call_schema.get("properties", {})) <= 6

        # Nenhuma tentativa incompatível foi feita, então nenhum arquivo de erro
        # da chamada estruturada foi criado neste teste.
        assert not structured_error_path.exists()


def test_gemini_sanitizer_drops_required_only_anyof_branch():
    """Um anyOf cujos branches só têm 'required' (sem type/properties/items/enum/format)
    deve ser removido inteiramente do schema sanitizado: o Gemini rejeita nós de
    schema sem 'type' com 400 INVALID_ARGUMENT, e a restrição continua sendo
    aplicada depois pela validação local contra o schema rico completo."""
    client = GeminiLLMClient(api_key="ficticia")

    schema = {
        "type": "object",
        "properties": {
            "campo_a": {"type": "string"},
            "campo_b": {"type": "string"},
        },
        "anyOf": [
            {"required": ["campo_a"]},
            {"required": ["campo_b"]},
        ],
    }

    sanitized = client._normalize_schema(schema)

    assert "anyOf" not in sanitized


def test_gemini_sanitizer_keeps_typed_anyof_branch_mixed():
    """Em um combinador misto (um branch tipado, um branch só com 'required'),
    o branch tipado deve ser preservado e o branch 'required'-only removido."""
    client = GeminiLLMClient(api_key="ficticia")

    schema = {
        "type": "object",
        "properties": {
            "valor": {
                "anyOf": [
                    {"type": "string"},
                    {"required": ["campo_a"]},
                ]
            },
        },
    }

    sanitized = client._normalize_schema(schema)

    valor_anyof = sanitized["properties"]["valor"]["anyOf"]
    assert valor_anyof == [{"type": "string"}]


def test_local_validation_still_enforces_dropped_anyof_constraint():
    """A sanitização remove o anyOf 'ao menos um destes campos' apenas do schema
    enviado ao Gemini. A validação local pós-geração (a mesma usada por
    _validate_offline em generate_structured e por DataExtractorApp.run_extraction)
    continua aplicando essa restrição contra o schema rico completo (não
    sanitizado), então uma resposta que a viola ainda é rejeitada antes da
    persistência."""
    schema = load_json(SCHEMA_PATH)
    validator = load_validator(schema, SCHEMA_PATH, SHARED_SCHEMAS_DIR)

    # Satisfaz o "required" de nível raiz (document_type), mas nenhum dos campos
    # do anyOf ("pedidos", "pedidos_individualizados", "fatos", "fundamentos",
    # "valor_da_causa", "parties").
    payload_missing_all_anyof_fields = {"document_type": "peticao_processo"}

    errors = list(validator.iter_errors(payload_missing_all_anyof_fields))
    assert errors, "Resposta sem nenhum campo do anyOf deveria falhar na validação local"

    # Confirma que ao menos um dos campos do anyOf já é suficiente para passar.
    payload_with_one_anyof_field = {
        "document_type": "peticao_processo",
        "valor_da_causa": {
            "value": "R$ 1.000,00",
            "anchors": [
                {"kind": "pagina", "page_marker": "1", "quote": "Valor da causa: R$ 1.000,00"}
            ],
        },
    }
    errors_ok = list(validator.iter_errors(payload_with_one_anyof_field))
    assert not errors_ok


def test_gemini_sanitizer_real_schema_root_has_no_required_only_anyof():
    """Regressão do caso real (processo 4000153-37.2026.8.26.0136/SP): o schema
    canônico de extr-peticao-processo declara, no nó raiz, um anyOf 'ao menos um
    destes campos' cujos branches são todos {"required": [...]} sem type. Após a
    correção, esse anyOf não deve mais chegar ao schema enviado ao Gemini."""
    schema = load_json(SCHEMA_PATH)
    client = GeminiLLMClient(api_key="ficticia")

    sanitized = client._normalize_schema(schema)

    assert "anyOf" not in sanitized
    # O schema canônico em si não foi alterado por essa correção.
    assert "anyOf" in schema
    assert all(set(branch.keys()) == {"required"} for branch in schema["anyOf"])


def test_gemini_block_mode_result_validates_against_full_local_schema():
    """O resultado consolidado da extração por blocos (acionada pelo preflight
    para o schema completo, sem nenhuma chamada 400) continua sendo validável
    localmente contra o schema rico completo antes de qualquer persistência —
    o preflight muda apenas qual chamada é feita ao Gemini, não a validação
    final."""
    import json as json_mod
    from unittest.mock import MagicMock, patch

    schema = load_json(SCHEMA_PATH)
    client = GeminiLLMClient(api_key="mock")

    def _payload_for(properties_requested):
        payload = {"document_type": "peticao_processo"}
        if "pedidos" in properties_requested:
            payload["pedidos"] = [{
                "text": "Pedido de procedência.",
                "anchors": [{"kind": "pagina", "page_marker": "1", "quote": "Pedido de procedência."}],
            }]
        if "pedidos_individualizados" in properties_requested:
            payload["pedidos_individualizados"] = [{
                "tipo": "procedencia_principal",
                "descricao_interpretativa": "Declarar procedente o pedido.",
                "trecho_literal": "Pedido de procedência.",
                "anchors": [{"kind": "pagina", "page_marker": "1", "quote": "Pedido de procedência."}],
            }]
        if "valor_da_causa" in properties_requested:
            payload["valor_da_causa"] = {
                "value": "R$ 1.000,00",
                "anchors": [{"kind": "pagina", "page_marker": "1", "quote": "Valor da causa: R$ 1.000,00"}],
            }
        return payload

    def _side_effect(*args, **kwargs):
        config = kwargs.get("config")
        block_schema = getattr(config, "response_json_schema", None) or {}
        properties_requested = set(block_schema.get("properties", {}).keys())
        mock_resp = MagicMock()
        mock_resp.text = json_mod.dumps(_payload_for(properties_requested))
        return mock_resp

    mock_generate = MagicMock(side_effect=_side_effect)

    with patch.object(client.client.models, "generate_content", mock_generate):
        result = client.generate_structured([{"role": "user", "content": "teste"}], schema)

    validator = load_validator(schema, SCHEMA_PATH, SHARED_SCHEMAS_DIR)
    errors = list(validator.iter_errors(result))
    assert not errors, f"Resultado do modo por blocos deveria ser válido: {errors}"


