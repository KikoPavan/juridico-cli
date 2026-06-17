#!/usr/bin/env python3
"""
Unit tests for schema validation and extraction rules.
Validates mock data against peticao_processo.schema.json and checks for prohibited ellipses.
"""

import json
import sys
from pathlib import Path
import pytest
import jsonschema
from jsonschema import RefResolver

SKILL_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = SKILL_DIR / "assets" / "peticao_processo.schema.json"
WORKSPACE_DIR = Path(__file__).resolve().parents[4]
SCHEMAS_DIR = WORKSPACE_DIR / "packages" / "shared-schemas"


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def test_schema_syntax():
    """Garante que o próprio arquivo de schema JSON é válido e parseável."""
    schema = load_json(SCHEMA_PATH)
    assert schema is not None
    assert schema["$id"] == "https://juridico-cli.local/schemas/peticao_processo.schema.json"


def test_mock_data_validation():
    """Valida um JSON mock completo e detalhado contendo todos os novos campos granulares contra o schema."""
    schema = load_json(SCHEMA_PATH)
    
    # Mock data representando os novos campos flexíveis (opcionais omitidos, sem enums fechados para papéis)
    mock_payload = {
        "document_type": "peticao_processo",
        "process_number": {
            "value": "4000153-37.2026.8.26.0136",
            "anchors": [
                {"kind": "pagina", "page_marker": "[[Pág. 1]]", "quote": "Processo 4000153-37.2026.8.26.0136/SP"}
            ]
        },
        "parties": [
            {
                "name": "JURACI PIRES PAVAN",
                "role": "autor",
                "qualification": "brasileira, viúva, pensionista",
                "document_ids": ["793.933.908-78", "4.294.873"],
                "anchors": [
                    {"kind": "pagina", "page_marker": "[[Pág. 1]]", "quote": "JURACI PIRES PAVAN, brasileira, viúva"}
                ]
            }
        ],
        "peticao_identification": {
            "value": "DECLARATÓRIA DE NULIDADE DE ESCRITURA PÚBLICA E CANCELAMENTO DE HIPOTECA",
            "anchors": [
                {"kind": "pagina", "page_marker": "[[Pág. 1]]", "quote": "AÇÃO DECLARATÓRIA DE NULIDADE DE ESCRITURA PÚBLICA E CANCELAMENTO DE HIPOTECA"}
            ]
        },
        "valor_da_causa": {
            "value": "R$ 2.481.566,27",
            "anchors": [
                {"kind": "pagina", "page_marker": "[[Pág. 15]]", "quote": "Atribui-se à causa o valor atualizado de R$ 2.481.566,27"}
            ]
        },
        
        # Retrocompatibilidade com campos antigos
        "fatos": [
            {
                "text": "A autora outorgou procuração pública ao Sr. Francisco Carlos Pavan que não concedia poderes para hipotecar.",
                "label": "Dos Fatos",
                "anchors": [
                    {"kind": "pagina", "page_marker": "[[Pág. 2]]", "quote": "procuração pública ao Sr. FRANCISCO CARLOS PAVAN"}
                ]
            }
        ],
        "fundamentos": [
            {
                "text": "A procuração não continha poderes especiais para onerar imóveis, violando o art. 1.295 §1º do CC/1916.",
                "label": "Do Direito",
                "anchors": [
                    {"kind": "pagina", "page_marker": "[[Pág. 6]]", "quote": "depende a procuração de poderes especiais e expressos"}
                ]
            }
        ],
        "pedidos": [
            {
                "text": "procedência total da ação, para declarar a nulidade absoluta da Escritura Pública",
                "label": "Dos Pedidos",
                "anchors": [
                    {"kind": "pagina", "page_marker": "[[Pág. 14]]", "quote": "procedência total da ação, para declarar a nulidade absoluta"}
                ]
            }
        ],

        # Novos campos de expansão granular
        "atos_juridicos": [
            {
                "nome": "Escritura Pública de Confissão de Dívidas com Garantias Hipotecárias",
                "data": "2002-06-28",
                "detalhes": "Escritura lavrada no Tabelionato de Águas de Santa Bárbara/SP contendo a hipoteca nula",
                "anchors": [
                    {"kind": "pagina", "page_marker": "[[Pág. 3]]", "quote": "foi lavrada a Escritura Pública de Confissão de Dívidas com Garantias Hipotecárias"}
                ]
            }
        ],
        "documentos_citados": [
            {
                "nome": "Contrato Social da JKMG",
                "tipo_documento": "contrato_social",
                "anchors": [
                    {"kind": "pagina", "page_marker": "[[Pág. 5]]", "quote": "Contrato Social registrado na JUCESP sob nº 35.217.364.283"}
                ]
            }
        ],
        "pessoas_mencionadas": [
            {
                "nome": "FRANCISCO CARLOS PAVAN",
                "papel_literal": "procurador",
                "papel_normalizado": "procurador",
                "anchors": [
                    {"kind": "pagina", "page_marker": "[[Pág. 2]]", "quote": "outorgaram procuração pública ao Sr. FRANCISCO CARLOS PAVAN"}
                ]
            }
        ],
        "empresas_mencionadas": [
            {
                "nome": "JKMG - COMERCIAL, INCORPORADORA E ADMINISTRADORA LTDA.",
                "papel_literal": "interveniente garante",
                "papel_normalizado": "interveniente_garante",
                "anchors": [
                    {"kind": "pagina", "page_marker": "[[Pág. 3]]", "quote": "Interveniente garante: JKMG - COMERCIAL, INCORPORADORA E ADMINISTRADORA LTDA."}
                ]
            }
        ],
        "imoveis_e_matriculas": [
            {
                "matricula": "7.013",
                "cri": "Cerqueira César/SP",
                "descricao": "lote nº 04, área de 2.352,00 m², situado na Rua Saldanha Marinho, Cerqueira César/SP",
                "anchors": [
                    {"kind": "pagina", "page_marker": "[[Pág. 4]]", "quote": "Matrícula nº 7.013 do CRI de Cerqueira César: lote nº 04, área de 2.352,00 m²"}
                ]
            }
        ],
        "garantias_e_gravames": [
            {
                "tipo": "hipoteca",
                "grau": "terceiro grau",
                "papel_literal": "hipoteca de terceiro grau sobre três imóveis urbanos",
                "imoveis_matriculas": ["7.013", "946", "905"],
                "anchors": [
                    {"kind": "pagina", "page_marker": "[[Pág. 3]]", "quote": "A escritura constituiu hipoteca de terceiro grau sobre três imóveis"}
                ]
            }
        ],
        "fundamentos_legais": [
            {
                "diploma": "Código Civil de 1916",
                "artigo": "1295",
                "paragrafo_inciso_alinea": "§1º",
                "texto_citado": "Para alienar, hipotecar, transigir, ou praticar outros quaisquer atos que exorbitem da administração ordinária, depende a procuração de poderes especiais e expressos.",
                "anchors": [
                    {"kind": "pagina", "page_marker": "[[Pág. 6]]", "quote": "depende a procuração de poderes especiais e expressos"}
                ]
            }
        ],
        "teses_juridicas": [
            {
                "titulo": "Nulidade absoluta por falta de poderes especiais para hipotecar",
                "descricao_interpretativa": "A outorga de garantia real exige procuração com poderes específicos e expressos para onerar e hipotecar imóveis. A ausência de tais poderes gera a nulidade absoluta do ato de hipoteca.",
                "trecho_literal": "Como a lei exige forma específica para o exercício da representação em ato que exorbita a administração ordinária (procuração com poderes especiais e expressos para hipotecar), a utilização de procuração sem tais poderes configura ato nulo",
                "normas_correlatas": ["art. 1.295, §1º do CC/1916", "art. 661, §1º do CC/2002"],
                "anchors": [
                    {"kind": "pagina", "page_marker": "[[Pág. 6]]", "quote": "Como a lei exige forma específica para o exercício da representação"}
                ]
            }
        ],
        "fatos_cronologicos": [
            {
                "data": "2002-06-28",
                "fato": "Outorga de procuração pública ao procurador Francisco Carlos Pavan e lavratura da escritura de confissão de dívidas com garantia hipotecária no mesmo dia",
                "trecho_literal": "Em 28 de junho de 2002, a autora JURACI PIRES PAVAN e a Sra. MARIA CECILIA HOLZHAUSEN PAVAN outorgaram procuração pública",
                "anchors": [
                    {"kind": "pagina", "page_marker": "[[Pág. 2]]", "quote": "Em 28 de junho de 2002, a autora JURACI PIRES PAVAN"}
                ]
            }
        ],
        "processos_relacionados": [
            {
                "numero_processo": "0003453-81.2003.8.26.0136",
                "relacao": "dependencia",
                "detalhes": "Ação Declaratória distribuída por dependência a esta execução",
                "anchors": [
                    {"kind": "pagina", "page_marker": "[[Pág. 1]]", "quote": "Por dependência ao Processo: 0003453-81.2003.8.26.0136"}
                ]
            }
        ],
        "pedidos_individualizados": [
            {
                "tipo": "tutela_urgencia",
                "descricao_interpretativa": "Pedido liminar de averbação da ação nas matrículas e suspensão da exigibilidade dos gravames e da execução correlata",
                "trecho_literal": "Requer-se a concessão de tutela de urgência para determinar a averbação da ação nas matrículas nºs 7.013, 946 e 905 do Cartório de Registro de Imóveis de Cerqueira César/SP",
                "anchors": [
                    {"kind": "pagina", "page_marker": "[[Pág. 14]]", "quote": "Requer-se a concessão de tutela de urgência para determinar a averbação"}
                ]
            }
        ],
        "tutela_urgencia": {
            "requerida": True,
            "tipo": "cautelar",
            "descricao_interpretativa": "Pedido de averbação imobiliária e suspensão da execução de origem",
            "trecho_literal": "concessão de tutela de urgência de natureza cautelar para determinar a averbação de ação no registro imobiliário e a suspensão da exigibilidade",
            "requisitos_demonstrados": [
                {
                    "requisito": "probabilidade_direito",
                    "argumento": "A hipoteca é nula na origem por ausência de poderes especiais na procuração",
                    "trecho_literal": "A probabilidade do direito resta amplamente demonstrada pela ausência total de poderes especiais"
                }
            ],
            "anchors": [
                {"kind": "pagina", "page_marker": "[[Pág. 13]]", "quote": "Presentes os requisitos do art. 300 do Código de Processo Civil"}
            ]
        },
        "provas_requeridas": [
            {
                "tipo_prova": "pericial",
                "detalhes": "Protesto geral de provas incluindo depoimento pessoal, oitiva de testemunhas e perícia",
                "trecho_literal": "Protesta-se provar o alegado por todos os meios de prova em direito admitidos, especialmente prova documental, pericial",
                "anchors": [
                    {"kind": "pagina", "page_marker": "[[Pág. 15]]", "quote": "Protesta-se provar o alegado por todos os meios de prova"}
                ]
            }
        ],
        "riscos_ou_pontos_de_atencao": [
            {
                "descricao": "Risco de excussão dos bens hipotecados e alienação a terceiros de boa-fé",
                "trecho_literal": "decorre de risco iminente de execução judicial da dívida com excussão dos bens hipotecados, alienação dos imóveis gravados a terceiros de boa-fé",
                "anchors": [
                    {"kind": "pagina", "page_marker": "[[Pág. 13]]", "quote": "perigo de dano decorre de risco iminente de execução judicial"}
                ]
            }
        ]
    }

    # Executar validação contra o schema local usando resolvedor para as refs externas
    common_schema_path = SCHEMAS_DIR / "defs" / "common.schema.json"
    common_schema = load_json(common_schema_path)
    
    store = {
        schema.get("$id", "https://juridico-cli.local/schemas/peticao_processo.schema.json"): schema,
        common_schema.get("$id", "https://juridico-cli.local/schemas/defs/common.schema.json"): common_schema
    }
    
    resolver = RefResolver(base_uri=SCHEMAS_DIR.as_uri() + "/", referrer=schema, store=store)
    validator = jsonschema.Draft202012Validator(schema, resolver=resolver)
    
    errors = list(validator.iter_errors(mock_payload))
    assert not errors, f"Validation failed with errors: {errors}"



def _check_no_ellipses(data):
    """Verifica recursivamente se qualquer string textual literal ou de quote contém reticências."""
    if isinstance(data, dict):
        for k, v in data.items():
            if k in ["trecho_literal", "quote", "text", "value"] and isinstance(v, str):
                assert "..." not in v, f"Encontrado '...' proibido no campo '{k}': {v}"
                assert "…" not in v, f"Encontrado '…' proibido no campo '{k}': {v}"
            else:
                _check_no_ellipses(v)
    elif isinstance(data, list):
        for item in data:
            _check_no_ellipses(item)


def test_no_ellipses_in_literal_quotes():
    """Garante que o validador do teste proíbe qualquer reticência no payload mock."""
    mock_payload_with_ellipses = {
        "document_type": "peticao_processo",
        "fatos": [
            {
                "text": "A autora outorgou procuração...",
                "anchors": [
                    {"kind": "pagina", "page_marker": "[[Pág. 2]]", "quote": "Em 28 de junho..."}
                ]
            }
        ]
    }
    
    with pytest.raises(AssertionError):
        _check_no_ellipses(mock_payload_with_ellipses)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
