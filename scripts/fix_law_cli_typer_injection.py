from __future__ import annotations

from pathlib import Path

MAIN = Path("agents/law-cli/main.py")
if not MAIN.exists():
    raise SystemExit(f"ERRO: não encontrei {MAIN}")

s = MAIN.read_text(encoding="utf-8")

# 1) extrair e remover o helper que foi inserido no lugar errado
start = s.find("AGENT_DIR = Path(__file__).resolve().parent")
if start == -1:
    raise SystemExit(
        "ERRO: não achei o bloco AGENT_DIR... no arquivo (nada para corrigir)."
    )

end_marker = "return default if cur is None else cur"
end = s.find(end_marker, start)
if end == -1:
    raise SystemExit("ERRO: não consegui localizar o fim do helper (_cfg_get).")

end = s.find("\n", end)
end = len(s) if end == -1 else end + 1

helper_block = s[start:end].strip("\n")
s2 = (s[:start] + s[end:]).replace("\n\n\n", "\n\n")

# 2) localizar o final da chamada app = typer.Typer(...) (inclusive multi-linha)
app_pos = s2.find("app = typer.Typer")
if app_pos == -1:
    raise SystemExit("ERRO: não encontrei 'app = typer.Typer' no arquivo.")

paren_pos = s2.find("(", app_pos)
if paren_pos == -1:
    raise SystemExit("ERRO: não encontrei '(' após 'app = typer.Typer'.")

i = paren_pos
count = 0
in_quote = None  # "'" ou '"'
triple = False

while i < len(s2):
    ch = s2[i]

    if in_quote is not None:
        # dentro de string
        if ch == "\\":
            i += 2
            continue
        if triple:
            if s2.startswith(in_quote * 3, i):
                in_quote = None
                triple = False
                i += 3
                continue
            i += 1
            continue
        else:
            if ch == in_quote:
                in_quote = None
                i += 1
                continue
            i += 1
            continue

    # fora de string
    if s2.startswith("'''", i):
        in_quote = "'"
        triple = True
        i += 3
        continue
    if s2.startswith('"""', i):
        in_quote = '"'
        triple = True
        i += 3
        continue
    if ch == "'":
        in_quote = "'"
        triple = False
        i += 1
        continue
    if ch == '"':
        in_quote = '"'
        triple = False
        i += 1
        continue

    if ch == "(":
        count += 1
    elif ch == ")":
        count -= 1
        if count == 0:
            end_call = i + 1
            break

    i += 1
else:
    raise SystemExit(
        "ERRO: não consegui fechar os parênteses do app = typer.Typer(...)."
    )

# inserir após a linha que termina a chamada
insert_at = s2.find("\n", end_call)
insert_at = len(s2) if insert_at == -1 else insert_at + 1

s_fixed = s2[:insert_at] + "\n" + helper_block + "\n\n" + s2[insert_at:]
MAIN.write_text(s_fixed, encoding="utf-8")

print("OK: helper reposicionado após o app = typer.Typer(...)")
