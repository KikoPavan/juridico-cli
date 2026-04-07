#!/usr/bin/env python3
"""
md-frontmatter-yaml · apply_frontmatter.py
==========================================
Insere frontmatter YAML genérico no topo de um arquivo Markdown limpo.

Agnóstico de domínio: funciona para qualquer tipo de documento.
Não extrai metadados especializados (jurídicos, médicos, etc.).

Uso:
    python apply_frontmatter.py --input DOC.md --output DOC_FINAL.md [opções]

Opções:
    --input PATH         Arquivo .md de entrada (obrigatório)
    --output PATH        Arquivo .md de saída com frontmatter (obrigatório)
    --title TEXT         Sobrescreve título detectado
    --doc-type TEXT      Tipo do documento (padrão: "document")
    --author TEXT        Sobrescreve autor detectado
    --date TEXT          Data em ISO 8601 (sobrescreve detecção)
    --language TEXT      Idioma IETF BCP 47 (padrão: "pt-BR")
    --tags TEXT          Tags separadas por vírgula
    --status TEXT        Status do documento (padrão: "raw")
    --verbose            Log detalhado no stderr
    --report             Gerar frontmatter_report.md junto ao output
"""

import argparse
import datetime
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("[ERRO] pyyaml não instalado. Execute: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Exit codes
# ---------------------------------------------------------------------------
EXIT_OK = 0
EXIT_INPUT_ERROR = 1
EXIT_ALREADY_HAS_FM = 2
EXIT_YAML_ERROR = 3
EXIT_WRITE_ERROR = 4

OUTPUT_ENCODING = "utf-8"
SKILL_NAME = "md-frontmatter-yaml"

# ---------------------------------------------------------------------------
# Meses em português (para detecção de data)
# ---------------------------------------------------------------------------
_MONTH_PT = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3,
    "abril": 4, "maio": 5, "junho": 6, "julho": 7,
    "agosto": 8, "setembro": 9, "outubro": 10,
    "novembro": 11, "dezembro": 12,
}


# ---------------------------------------------------------------------------
# Detecção de título (primeiro H1)
# ---------------------------------------------------------------------------
def _detect_title(body: str) -> tuple[str | None, str]:
    """Detecta o primeiro heading H1 no corpo. Retorna (valor, método)."""
    for line in body.splitlines():
        # Remover marcadores de página antes de checar headings
        clean = re.sub(r"<!--[^>]*-->", "", line).strip()
        m = re.match(r"^#\s+(.+)", clean)
        if m:
            return m.group(1).strip(), "h1"
    return None, "null"


# ---------------------------------------------------------------------------
# Detecção de data (regex, primeiras 20 linhas)
# ---------------------------------------------------------------------------
def _detect_date(body: str) -> tuple[str | None, str]:
    """
    Detecta data nas primeiras 20 linhas do corpo.
    Retorna (valor ISO 8601 ou parcial, método).
    """
    lines = body.splitlines()[:20]

    for line in lines:
        # DD/MM/YYYY ou DD-MM-YYYY
        m = re.search(r"\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})\b", line)
        if m:
            d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if 1 <= mo <= 12 and 1 <= d <= 31:
                return f"{y:04d}-{mo:02d}-{d:02d}", "regex_dmy"

        # YYYY-MM-DD
        m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", line)
        if m:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if 1 <= mo <= 12 and 1 <= d <= 31:
                return f"{y:04d}-{mo:02d}-{d:02d}", "regex_iso"

        # "DD de Mês de YYYY" ou "Mês de YYYY"
        m = re.search(
            r"(\d{1,2}\s+de\s+)?(\w+)\s+de\s+(\d{4})", line, re.IGNORECASE
        )
        if m:
            day_part = m.group(1)
            month_str = m.group(2).lower().strip()
            year = int(m.group(3))
            month_num = _MONTH_PT.get(month_str)
            if month_num and 2000 <= year <= 2100:
                if day_part:
                    day = int(re.search(r"\d+", day_part).group())
                    return f"{year:04d}-{month_num:02d}-{day:02d}", "regex_ptbr"
                return f"{year:04d}-{month_num:02d}", "regex_month_year"

        # "Mês YYYY" (sem "de")
        m = re.search(r"\b([A-Za-záéíóúâêîôûãõç]+)\s+(\d{4})\b", line, re.IGNORECASE)
        if m:
            month_str = m.group(1).lower()
            year = int(m.group(2))
            month_num = _MONTH_PT.get(month_str)
            if month_num and 2000 <= year <= 2100:
                return f"{year:04d}-{month_num:02d}", "regex_month_year"

    return None, "null"


# ---------------------------------------------------------------------------
# Detecção de autor (regex, primeiras 30 linhas)
# ---------------------------------------------------------------------------
_AUTHOR_LABELS = re.compile(
    r"^(?:Responsável|Autor|Elaborado por|Preparado por|Redator|Autora)"
    r"\s*:\s*(.+)",
    re.IGNORECASE,
)


def _detect_author(body: str) -> tuple[str | None, str]:
    """Detecta autor por padrões de rótulo explícito nas primeiras 30 linhas."""
    for line in body.splitlines()[:30]:
        clean = re.sub(r"<!--[^>]*-->", "", line).strip()
        m = _AUTHOR_LABELS.match(clean)
        if m:
            value = m.group(1).strip()
            if value:
                return value, "regex_label"
    return None, "null"


# ---------------------------------------------------------------------------
# Construção do frontmatter
# ---------------------------------------------------------------------------
def build_frontmatter(meta: dict) -> str:
    """
    Gera o bloco YAML delimitado por --- usando pyyaml para serialização segura.
    Garante tipos corretos e evita representações inesperadas.
    """
    # Construir dicionário na ordem desejada
    fm: dict = {}
    fm["title"] = meta.get("title")  # None → null em YAML
    fm["document_type"] = meta.get("document_type", "document")
    fm["source_file"] = meta["source_file"]
    fm["source_path"] = str(meta["source_path"])
    fm["document_date"] = meta.get("document_date")
    fm["author"] = meta.get("author")
    fm["language"] = meta.get("language", "pt-BR")
    fm["tags"] = meta.get("tags", [])
    fm["status"] = meta.get("status", "raw")
    fm["created_by_skill"] = SKILL_NAME

    # Serializar com pyyaml, default_flow_style=False para bloco legível
    yaml_str = yaml.dump(
        fm,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        indent=2,
    )

    return f"---\n{yaml_str}---\n"


# ---------------------------------------------------------------------------
# Relatório
# ---------------------------------------------------------------------------
def build_report(
    input_path: Path,
    output_path: Path,
    meta: dict,
    methods: dict,
    exit_code: int,
) -> str:
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    filled = sum(1 for v in meta.values() if v is not None and v != [] and v != "")
    null_count = sum(1 for v in meta.values() if v is None)
    status = "ok" if exit_code == EXIT_OK else "error"

    def fmt(val, method):
        if val is None:
            return f"`null` (método: {method})"
        return f"`{val}` (método: {method})"

    lines = [
        "# Relatório de Frontmatter — md-frontmatter-yaml",
        "",
        f"- **Arquivo de entrada:** `{input_path.name}`",
        f"- **Arquivo de saída:** `{output_path.name}`",
        f"- **Título detectado:** {fmt(meta.get('title'), methods.get('title', '?'))}",
        f"- **Data detectada:** {fmt(meta.get('document_date'), methods.get('date', '?'))}",
        f"- **Autor detectado:** {fmt(meta.get('author'), methods.get('author', '?'))}",
        f"- **Campos preenchidos:** {filled}",
        f"- **Campos nulos:** {null_count}",
        f"- **Status:** `{status}`",
        f"- **Data/hora:** {ts}",
        f"- **Exit code:** {exit_code}",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="md-frontmatter-yaml: insere frontmatter YAML em Markdown limpo."
    )
    parser.add_argument("--input", required=True, metavar="MD",
                        help="Arquivo .md de entrada")
    parser.add_argument("--output", required=True, metavar="MD",
                        help="Arquivo .md com frontmatter de saída")
    parser.add_argument("--title", default=None, help="Título (sobrescreve detecção)")
    parser.add_argument("--doc-type", default="document", dest="doc_type",
                        help="Tipo do documento (padrão: document)")
    parser.add_argument("--author", default=None, help="Autor (sobrescreve detecção)")
    parser.add_argument("--date", default=None, help="Data ISO 8601 (sobrescreve detecção)")
    parser.add_argument("--language", default="pt-BR", help="Idioma IETF BCP 47")
    parser.add_argument("--tags", default="", help="Tags separadas por vírgula")
    parser.add_argument("--status", default="raw", help="Status do documento")
    parser.add_argument("--verbose", action="store_true", help="Log no stderr")
    parser.add_argument("--report", action="store_true",
                        help="Gerar frontmatter_report.md junto ao output")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    # --- Validar entrada ---
    if not input_path.exists():
        print(f"[ERRO] Arquivo não encontrado: {input_path}", file=sys.stderr)
        sys.exit(EXIT_INPUT_ERROR)

    try:
        body = input_path.read_text(encoding=OUTPUT_ENCODING, errors="replace")
    except Exception as exc:
        print(f"[ERRO] Falha ao ler {input_path}: {exc}", file=sys.stderr)
        sys.exit(EXIT_INPUT_ERROR)

    # --- Verificar frontmatter existente ---
    if body.lstrip().startswith("---"):
        print(
            f"[ERRO] O arquivo já possui frontmatter YAML: {input_path}\n"
            "       Para re-aplicar, remova o frontmatter existente primeiro.",
            file=sys.stderr,
        )
        sys.exit(EXIT_ALREADY_HAS_FM)

    if args.verbose:
        print(f"[apply_frontmatter] Processando: {input_path}", file=sys.stderr)

    # --- Inferir metadados ---
    methods: dict[str, str] = {}

    if args.title:
        title, methods["title"] = args.title, "cli"
    else:
        title, methods["title"] = _detect_title(body)

    if args.date:
        document_date, methods["date"] = args.date, "cli"
    else:
        document_date, methods["date"] = _detect_date(body)

    if args.author:
        author, methods["author"] = args.author, "cli"
    else:
        author, methods["author"] = _detect_author(body)

    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []

    meta = {
        "title": title,
        "document_type": args.doc_type,
        "source_file": input_path.name,
        "source_path": input_path,
        "document_date": document_date,
        "author": author,
        "language": args.language,
        "tags": tags,
        "status": args.status,
    }

    if args.verbose:
        for k, v in meta.items():
            method = methods.get(k, "padrão")
            print(f"  {k}: {v!r}  [{method}]", file=sys.stderr)

    # --- Gerar frontmatter ---
    try:
        frontmatter_block = build_frontmatter(meta)
    except Exception as exc:
        print(f"[ERRO] Falha na geração do YAML: {exc}", file=sys.stderr)
        sys.exit(EXIT_YAML_ERROR)

    # --- Montar saída ---
    output_content = frontmatter_block + body

    # --- Escrever ---
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_content, encoding=OUTPUT_ENCODING)
    except Exception as exc:
        print(f"[ERRO] Falha ao escrever {output_path}: {exc}", file=sys.stderr)
        sys.exit(EXIT_WRITE_ERROR)

    if args.verbose:
        print(f"[apply_frontmatter] Saída: {output_path}", file=sys.stderr)

    exit_code = EXIT_OK

    # --- Relatório ---
    if args.report:
        report_path = output_path.parent / "frontmatter_report.md"
        try:
            report_path.write_text(
                build_report(input_path, output_path, meta, methods, exit_code),
                encoding=OUTPUT_ENCODING,
            )
            if args.verbose:
                print(f"[apply_frontmatter] Relatório: {report_path}", file=sys.stderr)
        except Exception as exc:
            print(f"[AVISO] Não foi possível escrever relatório: {exc}",
                  file=sys.stderr)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
