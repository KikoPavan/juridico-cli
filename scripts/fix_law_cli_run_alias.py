from __future__ import annotations

import re
from pathlib import Path

p = Path("agents/law-cli/main.py")
if not p.exists():
    raise SystemExit("ERRO: agents/law-cli/main.py não encontrado")

s = p.read_text(encoding="utf-8")

# 1) Remove qualquer alias "run" antigo (inclusive o que gerou NameError)
s2 = re.sub(
    r'^\s*app\.command\("run"\)\([A-Za-z_][A-Za-z0-9_]*\)\s*\n', "", s, flags=re.M
)

# 2) Descobre o nome real da função que está registrada como comando "build"
m = re.search(
    r'^\s*@app\.command\(\s*["\']build["\']\s*\)\s*\n^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(',
    s2,
    flags=re.M,
)
if not m:
    raise SystemExit(
        "ERRO: não encontrei @app.command('build') seguido de def ... em agents/law-cli/main.py"
    )

build_fn = m.group(1)

# 3) Insere o alias run depois do bloco do build_fn (top-level)
def_match = re.search(rf"^\s*def\s+{re.escape(build_fn)}\s*\(", s2, flags=re.M)
if not def_match:
    raise SystemExit("ERRO: não encontrei a linha def do build (inconsistência)")

after = s2[def_match.end() :]
marker = re.search(
    r'^(?:@app\.command|def |if __name__ == [\'"]__main__[\'"]\s*:)', after, flags=re.M
)
insert_at = def_match.end() + (marker.start() if marker else len(after))

alias = (
    "\n\n# Alias de compatibilidade: permite `law-cli run` (padrão dos outros agentes)\n"
    f'app.command("run")({build_fn})\n'
)

s3 = s2[:insert_at] + alias + s2[insert_at:]

if s3 != s:
    p.write_text(s3, encoding="utf-8")

print(
    f"OK: alias 'run' criado para apontar para '{build_fn}' (e alias antigo removido, se existia)."
)
