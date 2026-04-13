#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path
from textwrap import dedent

IMPLEMENTATION_STATE = dedent(
    """\
    ---
    title: implementation-state
    generated_by: reorganize_bmad_brownfield.py
    purpose: espelho formal do estágio real pós-planning para projeto brownfield
    ---

    # Implementation State — juridico-cli

    ## 1. Objetivo deste arquivo
    Registrar, dentro de `_bmad-output/implementation-artifacts/`, o estágio real atual do projeto
    `juridico-cli`, evitando que LLMs interpretem o repositório como se estivesse apenas no planning.

    ## 2. Classificação atual do projeto
    - Tipo: projeto brownfield / monorepo Python 3.12+ / processamento documental jurídico orientado a skills
    - Baseline vigente:
      `PDF -> convert -> clean -> frontmatter/analyze -> extract -> JSON`
    - Status geral:
      planning BMad concluído, baseline parcialmente homologado, nova esteira jurídica preparada contratualmente,
      integração ainda não implementada

    ## 3. Artefatos de planning válidos
    - `_bmad-output/planning-artifacts/prd.md`
    - `_bmad-output/planning-artifacts/validation-report-2026-04-07.md`
    - `_bmad-output/planning-artifacts/epics_and_stories_2026-04-07.md`

    ## 4. Estado real já validado
    - Story 1.1 homologada no recorte extractor/LLM real (Gemini)
    - Story 1.3 aceita como homologada no recorte E2E do baseline
    - 3 novas skills configuradas estruturalmente e registradas:
      - `platform/skills/segmentador-juridico/`
      - `platform/skills/curador-relevancia/`
      - `platform/skills/yaml-normalizador-juridico/`
    - Contrato canônico da nova esteira consolidado
    - Revalidação contratual final:
      - Contrato A (`segmentador-juridico -> curador-relevancia`) compatível
      - Contrato B (`curador-relevancia -> yaml-normalizador-juridico`) compatível no mérito, com pendência documental residual

    ## 5. Pendência residual ativa
    - Arquivo:
      `platform/skills/yaml-normalizador-juridico/references/example_output.md`
    - Problema:
      contém enums legados detectados pelo validador do normalizador
    - Efeito:
      não quebra o mérito contratual, mas impede considerar a integração “limpa” sem ressalva

    ## 6. Próxima etapa autorizada
    Executar somente o **planejamento técnico da integração** da nova esteira jurídica ao pipeline executável, sem alterar código.

    ### Escopo da próxima etapa
    - inspecionar o ponto atual do pipeline após `clean`
    - mapear onde entram:
      - `segmentador-juridico`
      - `curador-relevancia`
      - `yaml-normalizador-juridico`
    - definir artefatos de entrada e saída de cada etapa
    - listar arquivos/áreas provavelmente impactados
    - manter registrada a pendência residual do normalizador
    - parar no plano, sem implementar

    ## 7. O que não deve ser feito agora
    - não reabrir o baseline já aceito
    - não rodar `bmad-sprint-planning` para esta esteira
    - não criar artificialmente `sprint-status.yaml`
    - não integrar a nova esteira ao pipeline antes do plano técnico
    - não misturar planning, validação contratual e implementação na mesma ação

    ## 8. Fontes documentais principais
    ### Documentação viva do projeto
    - `docs/architecture/juridico_cli_arquitetura_evolutiva.md`
    - `docs/architecture/juridico_cli_estado_real_consolidado.md`
    - `docs/architecture/juridico_cli_gaps_e_proximo_passo.md`
    - `docs/architecture/juridico_cli_documento_mestre.md`

    ### Contexto técnico
    - `_bmad-output/project-context.md`

    ### Apoio histórico
    - `docs/archive/juridico-cli/`

    ## 9. Interpretação correta do estágio
    O projeto não está “somente no planning”.
    O planning formal existe e continua válido, porém o estado real avançou para:
    - homologação parcial do baseline
    - preparação estrutural e contratual da nova esteira
    - necessidade atual de planejamento técnico de integração

    ## 10. Regra operacional
    Em caso de conflito entre leitura superficial do `_bmad-output/` e a documentação viva em `docs/architecture/`,
    considerar:
    1. `docs/architecture/juridico_cli_arquitetura_evolutiva.md`
    2. `docs/architecture/juridico_cli_estado_real_consolidado.md`
    3. este arquivo `implementation-state.md`
    como referência operacional prioritária para o estágio atual.
    """
)


def now_tag() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def backup_file(path: Path) -> Path:
    backup = path.with_name(f"{path.name}.bak.{now_tag()}")
    shutil.copy2(path, backup)
    return backup


def write_text_if_changed(path: Path, content: str, label: str) -> None:
    if path.exists():
        current = path.read_text(encoding="utf-8")
        if current == content:
            print(f"[OK] {label}: sem alterações -> {path}")
            return
        backup = backup_file(path)
        print(f"[BK] Backup criado -> {backup}")
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"[WR] {label}: atualizado -> {path}")


def copy_project_context(root: Path) -> None:
    src_root = root / "project-context.md"
    dst = root / "_bmad-output" / "project-context.md"

    if src_root.exists():
        src_content = src_root.read_text(encoding="utf-8")
        if dst.exists():
            dst_content = dst.read_text(encoding="utf-8")
            if dst_content == src_content:
                print(f"[OK] project-context canônico já está sincronizado -> {dst}")
                return
            backup = backup_file(dst)
            print(f"[BK] Backup do project-context canônico -> {backup}")
        dst.write_text(src_content, encoding="utf-8", newline="\n")
        print(f"[CP] project-context copiado para local canônico -> {dst}")
        return

    if dst.exists():
        print(f"[OK] project-context canônico já existe -> {dst}")
        return

    placeholder = dedent(
        """\
        ---
        title: project-context
        status: placeholder
        ---

        # Project Context

        Este arquivo foi criado porque não havia `project-context.md` na raiz do repositório.
        Substitua este conteúdo pelo contexto técnico canônico do projeto.

        Local padrão BMad:
        - `_bmad-output/project-context.md`
        """
    )
    dst.write_text(placeholder, encoding="utf-8", newline="\n")
    print(f"[WR] project-context placeholder criado -> {dst}")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    print(f"[DIR] garantido -> {path}")


def verify_repo_shape(root: Path) -> None:
    expected = [
        root / "docs" / "architecture",
        root / "_bmad-output",
    ]
    missing = [str(p) for p in expected if not p.exists()]
    if missing:
        raise SystemExit(
            "Estrutura mínima não encontrada. Verifique a raiz do repositório:\\n- "
            + "\\n- ".join(missing)
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normaliza a estrutura BMad de um projeto brownfield sem alterar pipeline."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Raiz do repositório juridico-cli. Padrão: diretório atual.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    print(f"[ROOT] {root}")

    verify_repo_shape(root)

    bmad_output = root / "_bmad-output"
    planning = bmad_output / "planning-artifacts"
    implementation = bmad_output / "implementation-artifacts"

    ensure_dir(bmad_output)
    ensure_dir(planning)
    ensure_dir(implementation)

    copy_project_context(root)

    implementation_state_path = implementation / "implementation-state.md"
    write_text_if_changed(
        implementation_state_path,
        IMPLEMENTATION_STATE,
        "implementation-state",
    )

    print("\\nConcluído.")
    print("Nenhum código do pipeline foi alterado.")
    print("Nenhum sprint-status.yaml foi criado.")
    print("Docs em docs/architecture/ e docs/archive/juridico-cli/ foram preservados.")


if __name__ == "__main__":
    main()
