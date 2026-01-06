import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ["main.py", "pipelines", "agents", "scripts"]


def iter_py_files():
    for rel in TARGETS:
        p = ROOT / rel
        if not p.exists():
            continue
        if p.is_file() and p.suffix == ".py":
            yield p
        elif p.is_dir():
            yield from p.rglob("*.py")


def test_project_python_syntax_is_valid():
    files = list(iter_py_files())
    assert files, "Nenhum arquivo .py encontrado nos alvos do smoke test."

    for f in files:
        src = f.read_text(encoding="utf-8", errors="replace")
        try:
            ast.parse(src, filename=str(f))
        except SyntaxError as e:
            raise AssertionError(
                f"SyntaxError em {f}: {e.msg} (linha {e.lineno})"
            ) from e
