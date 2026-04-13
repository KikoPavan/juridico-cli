#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from textwrap import dedent

RELATORIO_MARKER = (
    "## Achado crítico — desalinhamento contratual no yaml-normalizador-juridico"
)
IMPLEMENTATION_MARKER = (
    "## Registro adicional — desalinhamento contratual no yaml-normalizador-juridico"
)


RELATORIO_BLOCK = dedent(
    """\
    ## Achado crítico — desalinhamento contratual no yaml-normalizador-juridico

    ### Evidência
    Na execução de:
    - `platform/skills/yaml-normalizador-juridico/scripts/apply_yaml_normalization.py`
    - `platform/skills/yaml-normalizador-juridico/scripts/validate_yaml_normalizador_juridico.py`

    o artefato gerado em:

    `var/staging/normalizador_teste/proc-2024-0042__peca_001.md`

    foi validado com sucesso, porém o frontmatter gerado usa campos diferentes dos descritos no contrato documental vigente.

    ### Divergência observada
    Documentação e exemplos de entrada indicam:
    - `acao_curatorial`
    - `impacto_sentenca_confirmado`

    Saída real gerada pelo script usa:
    - `curation_action`
    - `impacto_sentenca`

    ### Conclusão
    A skill está operacionalmente funcional e validada pelo script, mas existe desalinhamento entre:
    - `SKILL.md`
    - `references/example_input.json`
    - `references/example_output.md`
    - `assets/io.schema.json`
    - `apply_yaml_normalization.py`
    - `validate_yaml_normalizador_juridico.py`

    ### Impacto
    A esteira ainda não deve ser considerada madura para integração no pipeline executável enquanto esse contrato não for saneado.

    ### Próximo passo
    Definir a nomenclatura canônica do normalizador e alinhar documentação, schema, gerador e validador antes de novos testes de integração.
    """
)

IMPLEMENTATION_BLOCK = dedent(
    """\
    ## Registro adicional — desalinhamento contratual no yaml-normalizador-juridico

    ### Status
    Bloqueio real de maturidade da esteira jurídica.

    ### Evidência resumida
    O normalizador executa e valida com sucesso, porém a saída real gerada diverge do contrato documental vigente.

    ### Divergência
    Documentação/entrada:
    - `acao_curatorial`
    - `impacto_sentenca_confirmado`

    Saída real gerada:
    - `curation_action`
    - `impacto_sentenca`

    ### Impacto operacional
    A skill funciona, mas o contrato entre documentação, schema, gerador e validador ainda não está saneado.
    Portanto, a esteira não deve ser considerada madura para integração no pipeline executável.

    ### Próxima ação
    Alinhar nomenclatura canônica em:
    - `platform/skills/yaml-normalizador-juridico/SKILL.md`
    - `platform/skills/yaml-normalizador-juridico/references/example_input.json`
    - `platform/skills/yaml-normalizador-juridico/references/example_output.md`
    - `platform/skills/yaml-normalizador-juridico/assets/io.schema.json`
    - `platform/skills/yaml-normalizador-juridico/scripts/apply_yaml_normalization.py`
    - `platform/skills/yaml-normalizador-juridico/scripts/validate_yaml_normalizador_juridico.py`
    """
)


def backup_file(path: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.name}.bak.{ts}")
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    return backup


def append_block_if_missing(path: Path, marker: str, block: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        text = path.read_text(encoding="utf-8")
        if marker in text:
            print(f"[OK] Bloco já registrado em {path}")
            return
        backup = backup_file(path)
        print(f"[BK] Backup criado: {backup}")
        new_text = text.rstrip() + "\n\n" + block.rstrip() + "\n"
    else:
        new_text = block.rstrip() + "\n"

    path.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"[WR] Registro atualizado: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Registra o gap contratual do yaml-normalizador-juridico para continuidade entre agentes."
    )
    parser.add_argument(
        "--root", default=".", help="Raiz do repositório. Padrão: diretório atual."
    )
    parser.add_argument(
        "--report",
        default="docs/qwen_tasks/relatorio_validacao_esteira_juridica.md",
        help="Relatório de tarefa a atualizar.",
    )
    parser.add_argument(
        "--implementation-state",
        default="_bmad-output/implementation-artifacts/implementation-state.md",
        help="Arquivo de estado operacional a atualizar.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report_path = root / args.report
    implementation_path = root / args.implementation_state

    append_block_if_missing(report_path, RELATORIO_MARKER, RELATORIO_BLOCK)
    append_block_if_missing(
        implementation_path, IMPLEMENTATION_MARKER, IMPLEMENTATION_BLOCK
    )

    print("\nConcluído.")
    print("QWEN.md não foi alterado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
