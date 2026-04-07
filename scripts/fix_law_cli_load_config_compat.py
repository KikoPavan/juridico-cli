# scripts/fix_law_cli_load_config_compat.py
from __future__ import annotations

import re
from pathlib import Path

MAIN = Path("agents/law-cli/main.py")


NEW_LOAD_CONFIG = r'''
def load_config(root: Path) -> Config:
    """
    Compat:
      - Formato antigo:
          agent_name, agent_version, index_query: {script, doc_kind, top_k}
      - Formato novo (padrão do projeto):
          agent: {name, version}, jobs: [{script, doc_kind, top_k, ...}]
    """
    p = root / "agents" / "law-cli" / "config.yaml"
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("config.yaml inválido: esperado mapeamento YAML no topo.")

    # --- Formato antigo (legado) ---
    if "agent_name" in raw:
        iq = raw.get("index_query") or {}
        if not isinstance(iq, dict):
            iq = {}
        script = iq.get("script")
        if not script:
            raise KeyError("index_query.script ausente no config.yaml (formato antigo).")
        return Config(
            agent_name=raw["agent_name"],
            agent_version=raw.get("agent_version", "0.0.0"),
            script=script,
            doc_kind=iq.get("doc_kind", "lei"),
            top_k=int(iq.get("top_k", 10)),
        )

    # --- Formato novo (padrão do projeto) ---
    agent_block = raw.get("agent") or {}
    if not isinstance(agent_block, dict):
        agent_block = {}

    jobs = raw.get("jobs") or []
    job0 = jobs[0] if isinstance(jobs, list) and jobs and isinstance(jobs[0], dict) else {}

    script = job0.get("script")
    if not script:
        # fallback: caso alguém ainda tenha "index_query" junto do formato novo
        iq = raw.get("index_query") or {}
        script = iq.get("script") if isinstance(iq, dict) else None

    if not script:
        raise KeyError("script ausente no config.yaml (jobs[0].script ou index_query.script).")

    doc_kind = job0.get("doc_kind", "lei")
    top_k = int(job0.get("top_k", 10))

    return Config(
        agent_name=str(agent_block.get("name") or "law-cli"),
        agent_version=str(agent_block.get("version") or "0.0.0"),
        script=str(script),
        doc_kind=str(doc_kind),
        top_k=top_k,
    )
'''.lstrip("\n")


def main() -> None:
    if not MAIN.exists():
        raise SystemExit(f"ERRO: não encontrei {MAIN}")

    s = MAIN.read_text(encoding="utf-8")

    # substitui o bloco inteiro da função load_config
    pat = r"^def load_config\(root: Path\) -> Config:\n(?:(?:^[^\n]*\n)|(?:\n))*?(?=^def |\Z)"
    m = re.search(pat, s, flags=re.M)
    if not m:
        raise SystemExit(
            "ERRO: não consegui localizar 'def load_config(root: Path) -> Config:' no main.py"
        )

    s2 = s[: m.start()] + NEW_LOAD_CONFIG + "\n\n" + s[m.end() :]

    MAIN.write_text(s2, encoding="utf-8")
    print(
        "OK: load_config atualizado para aceitar config.yaml no formato novo e no legado."
    )


if __name__ == "__main__":
    main()
