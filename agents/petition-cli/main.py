import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml
from dotenv import load_dotenv

# --- IMPORTAÇÃO DA NOVA SDK DO GOOGLE (google-genai) ---
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("ERRO CRÍTICO: Biblioteca 'google-genai' não instalada.")
    print("Instale no seu venv: pip install -U google-genai")
    sys.exit(1)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_file(p: Path) -> Optional[str]:
    if not p.exists() or not p.is_file():
        return None
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_text(p: Path, required: bool = False) -> str:
    if p.exists() and p.is_file():
        return p.read_text(encoding="utf-8")
    if required:
        raise FileNotFoundError(f"Arquivo obrigatório não encontrado: {p}")
    return ""


def _read_json(p: Path) -> Optional[Dict[str, Any]]:
    if p.exists() and p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return None


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _repo_root() -> Path:
    # .../juridico-cli/agents/petition-cli/main.py -> root = parents[2]
    return Path(__file__).resolve().parents[2]


def _agent_dir() -> Path:
    return Path(__file__).resolve().parent


def _load_config(config_path: Path) -> Dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _get(d: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def _pick_path(*candidates: Optional[str], default: Optional[str] = None) -> Path:
    for c in candidates:
        if c and str(c).strip():
            return Path(str(c))
    return Path(default) if default else Path()


def _pack_preview(pack: Dict[str, Any]) -> Dict[str, Any]:
    # Mantém apenas um recorte útil e estável (evita inflar tokens)
    keep_keys = [
        "pack_version",
        "inputs",
        "duckdb_info",
        "premissas",
        "questoes",
        "p0",
        "p1",
        "context",
        "contexto_relacoes",
        "case_id",
        "case_meta",
    ]
    out: Dict[str, Any] = {}
    for k in keep_keys:
        if k in pack:
            out[k] = pack[k]
    # fallback: se nada bateu, retorna só topo básico
    if not out:
        for k in list(pack.keys())[:8]:
            out[k] = pack[k]
    return out


def build_user_contents(
    firac_md_path: Path,
    firac_json_path: Optional[Path],
    juris_md_path: Optional[Path],
    juris_json_path: Optional[Path],
    pack_path: Optional[Path],
    input_hashes: Dict[str, Any],
    max_chars: int,
) -> Tuple[str, Dict[str, Any]]:
    meta: Dict[str, Any] = {"truncated": {}}

    firac_md = _read_text(firac_md_path, required=True)
    firac_json = _read_text(firac_json_path, required=False) if firac_json_path else ""
    juris_md = _read_text(juris_md_path, required=False) if juris_md_path else ""
    juris_json = _read_text(juris_json_path, required=False) if juris_json_path else ""

    pack_preview_text = ""
    if pack_path and pack_path.exists():
        pack_obj = _read_json(pack_path)
        if isinstance(pack_obj, dict):
            preview = _pack_preview(pack_obj)
            pack_preview_text = json.dumps(preview, ensure_ascii=False, indent=2)

    def clamp(label: str, s: str) -> str:
        if not s:
            return s
        if len(s) <= max_chars:
            meta["truncated"][label] = False
            return s
        meta["truncated"][label] = True
        return s[:max_chars] + "\n\n[TRUNCADO PARA CABER NO ORÇAMENTO]\n"

    firac_md = clamp("firac_md", firac_md)
    firac_json = clamp("firac_json", firac_json)
    juris_md = clamp("juris_md", juris_md)
    juris_json = clamp("juris_json", juris_json)
    pack_preview_text = clamp("pack_preview", pack_preview_text)

    parts = []
    parts.append(
        "Você receberá insumos do pipeline local (juridico-cli). "
        "Gere APENAS a petição-esqueleto em Markdown, com placeholders e remissões claras.\n"
        "Regras: não afirmar fatos sem referência; separar premissa vs prova; quando faltar prova, "
        "registrar lacuna e/ou documento recomendado (P0/P1)."
    )

    parts.append(
        "\n## Inputs (paths + sha256)\n"
        + json.dumps(input_hashes, ensure_ascii=False, indent=2)
    )

    parts.append(
        f"\n## FIRAC_MD ({firac_md_path.as_posix()})\n\n```md\n{firac_md}\n```"
    )

    if firac_json_path and firac_json.strip():
        parts.append(
            f"\n## FIRAC_JSON ({firac_json_path.as_posix()})\n\n```json\n{firac_json}\n```"
        )

    if juris_md_path and juris_md.strip():
        parts.append(
            f"\n## JURIS_MD ({juris_md_path.as_posix()})\n\n```md\n{juris_md}\n```"
        )

    if juris_json_path and juris_json.strip():
        parts.append(
            f"\n## JURIS_JSON ({juris_json_path.as_posix()})\n\n```json\n{juris_json}\n```"
        )

    if pack_path and pack_preview_text.strip():
        parts.append(
            f"\n## PACK_GLOBAL_PREVIEW ({pack_path.as_posix()})\n\n```json\n{pack_preview_text}\n```"
        )

    user_text = "\n\n---\n\n".join(parts)
    return user_text, meta


def main() -> None:
    load_dotenv()

    root = _repo_root()
    os.chdir(root)

    agent_dir = _agent_dir()
    default_cfg = agent_dir / "config.yaml"

    ap = argparse.ArgumentParser(prog="petition-cli", add_help=True)
    ap.add_argument(
        "--config",
        default=str(default_cfg),
        help="Caminho do config.yaml do petition-cli",
    )
    args = ap.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = (root / cfg_path).resolve()

    config = _load_config(cfg_path)

    runtime = config.get("runtime", {}) or {}
    paths = config.get("paths", {}) or {}
    skills_map = config.get("skills_map", {}) or {}

    provider = str(runtime.get("provider", "gemini_api")).strip().lower()
    if provider not in {"gemini_api", "google_genai", "genai", "gemini"}:
        # Mantém execução previsível: este main.py foi migrado para SDK nova
        raise RuntimeError(
            f"provider não suportado neste main.py (após migração): {provider}"
        )

    # Model/config
    model = (
        runtime.get("model")
        or runtime.get("model_id")
        or runtime.get("gemini_model")
        or "gemini-2.0-flash-001"
    )
    temperature = float(runtime.get("temperature", 0.2))
    max_output_tokens = int(runtime.get("max_output_tokens", 4096))
    top_p = runtime.get("top_p", None)
    top_k = runtime.get("top_k", None)
    seed = runtime.get("seed", None)

    # API key
    api_key_env = runtime.get("api_key_env") or "GEMINI_API_KEY"
    api_key = os.getenv(api_key_env) or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            f"API key não encontrada. Defina {api_key_env} (ou GOOGLE_API_KEY) no ambiente/.env."
        )

    # Prompt + skill core (system_instruction)
    prompt_file = _pick_path(
        _get(runtime, "prompt_file", default=None),
        _get(paths, "prompt_file", default=None),
        _get(skills_map, "prompt_file", default=None),
        default="agents/petition-cli/prompt.md",
    )
    core_skill = _pick_path(
        _get(skills_map, "core", default=None),
        _get(runtime, "core", default=None),
        _get(paths, "core", default=None),
        default="agents/petition-cli/skills/SKILL.core.md",
    )

    prompt_text = _read_text(prompt_file, required=True)
    core_text = _read_text(core_skill, required=True)
    system_instruction = f"{prompt_text}\n\n---\n\n{core_text}"

    # Inputs
    firac_md = _pick_path(
        _get(paths, "input_relatorio_firac", default=None),
        default="outputs/relatorio_firac.md",
    )
    firac_json = _pick_path(
        _get(paths, "input_relatorio_firac_json", default=None),
        default="outputs/relatorio_firac.json",
    )
    if not firac_json.exists():
        firac_json = None

    juris_md = _pick_path(
        _get(paths, "input_jurisprudencia_md", default=None),
        default="outputs/jurisprudencia/jurisprudencia.md",
    )
    if not juris_md.exists():
        juris_md = None

    juris_json = _pick_path(
        _get(paths, "input_jurisprudencia_json", default=None),
        default="outputs/jurisprudencia/jurisprudencia.json",
    )
    if not juris_json.exists():
        juris_json = None

    pack_global = _pick_path(
        _get(paths, "input_pack_global", default=None),
        default="artifacts/evidence_packs/dataset_v1/pack_global.json",
    )
    if not pack_global.exists():
        pack_global = None

    # Outputs
    out_draft = _pick_path(
        _get(paths, "output_petition_draft", default=None),
        _get(paths, "output_draft", default=None),
        default="outputs/peticao/petition_draft.md",
    )
    logs_dir = _pick_path(
        _get(paths, "logs_dir", default=None),
        default="outputs/peticao/99_logs",
    )
    _ensure_dir(out_draft.parent)
    _ensure_dir(logs_dir)

    # Budget de texto para anexar aos contents (evita blow-up)
    max_chars = int(runtime.get("max_input_chars_per_section", 120_000))

    input_hashes: Dict[str, Any] = {
        "firac_md": {"path": firac_md.as_posix(), "sha256": _sha256_file(firac_md)},
        "firac_json": {
            "path": firac_json.as_posix() if firac_json else None,
            "sha256": _sha256_file(firac_json) if firac_json else None,
        },
        "juris_md": {
            "path": juris_md.as_posix() if juris_md else None,
            "sha256": _sha256_file(juris_md) if juris_md else None,
        },
        "juris_json": {
            "path": juris_json.as_posix() if juris_json else None,
            "sha256": _sha256_file(juris_json) if juris_json else None,
        },
        "pack_global": {
            "path": pack_global.as_posix() if pack_global else None,
            "sha256": _sha256_file(pack_global) if pack_global else None,
        },
    }

    user_text, meta = build_user_contents(
        firac_md_path=firac_md,
        firac_json_path=firac_json,
        juris_md_path=juris_md,
        juris_json_path=juris_json,
        pack_path=pack_global,
        input_hashes=input_hashes,
        max_chars=max_chars,
    )

    # Client + request
    client = genai.Client(api_key=api_key)

    gen_cfg_kwargs: Dict[str, Any] = {
        "system_instruction": system_instruction,
        "temperature": temperature,
        "max_output_tokens": max_output_tokens,
    }
    if top_p is not None:
        gen_cfg_kwargs["top_p"] = float(top_p)
    if top_k is not None:
        gen_cfg_kwargs["top_k"] = int(top_k)
    if seed is not None:
        gen_cfg_kwargs["seed"] = int(seed)

    response = client.models.generate_content(
        model=str(model),
        contents=user_text,
        config=types.GenerateContentConfig(**gen_cfg_kwargs),
    )

    draft_text = (response.text or "").strip()
    if not draft_text:
        raise RuntimeError("Resposta vazia do modelo (response.text vazio).")

    out_draft.write_text(draft_text + "\n", encoding="utf-8")

    # Logs (auditáveis)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_path = logs_dir / f"petition_raw_{run_id}.txt"
    raw_path.write_text(draft_text + "\n", encoding="utf-8")

    run_log = {
        "agent_name": runtime.get("agent_name", "petition-cli"),
        "cli_tool_name": runtime.get("cli_tool_name", "petition-cli"),
        "provider": provider,
        "model": str(model),
        "model_version": getattr(response, "model_version", None),
        "created_at": _now_iso(),
        "config_path": str(cfg_path),
        "inputs": input_hashes,
        "outputs": {
            "petition_draft_md": out_draft.as_posix(),
            "raw_response": raw_path.as_posix(),
        },
        "meta": meta,
        "generation_config": {
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
            "top_p": top_p,
            "top_k": top_k,
            "seed": seed,
            "max_input_chars_per_section": max_chars,
        },
    }
    (logs_dir / f"petition_run_{run_id}.json").write_text(
        json.dumps(run_log, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[OK] Draft gerado: {out_draft}")
    print(f"[OK] Logs: {logs_dir}/petition_run_{run_id}.json | {raw_path}")


if __name__ == "__main__":
    main()
