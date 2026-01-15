import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RuntimeConfig:
    provider: str
    mode: str
    model: str
    temperature: float
    top_p: float
    max_output_tokens: int


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(_read_text(path))


def _read_yaml(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(_read_text(path))


def _load_runtime(cfg: Dict[str, Any]) -> RuntimeConfig:
    rt = cfg.get("runtime") or {}
    return RuntimeConfig(
        provider=str(rt.get("provider", "gemini")),
        mode=str(rt.get("mode", "google.genai")),
        model=str(rt.get("model", "gemini-2.5-flash")),
        temperature=float(rt.get("temperature", 0.0)),
        top_p=float(rt.get("top_p", 0.95)),
        max_output_tokens=int(rt.get("max_output_tokens", 8192)),
    )


def _select_job(cfg: Dict[str, Any], job_id: Optional[str]) -> Dict[str, Any]:
    jobs = cfg.get("jobs")
    if isinstance(jobs, list):
        if not jobs:
            raise ValueError("config.yaml: 'jobs' está vazio.")
        if job_id is None:
            return jobs[0]
        for j in jobs:
            if j.get("id") == job_id:
                return j
        raise ValueError(f"config.yaml: job id '{job_id}' não encontrado em 'jobs'.")
    if isinstance(jobs, dict):
        # suporte para layout antigo: jobs: { nome: [ {..} ] }
        if not jobs:
            raise ValueError("config.yaml: 'jobs' (dict) está vazio.")
        if job_id is None:
            first_key = next(iter(jobs.keys()))
            job_list = jobs[first_key]
            if not isinstance(job_list, list) or not job_list:
                raise ValueError("config.yaml: formato inválido em jobs.<key> (esperado lista).")
            return job_list[0]
        # tentar por chave e por id
        if job_id in jobs:
            job_list = jobs[job_id]
            if not isinstance(job_list, list) or not job_list:
                raise ValueError(f"config.yaml: jobs.{job_id} inválido (esperado lista não-vazia).")
            return job_list[0]
        for k, lst in jobs.items():
            if isinstance(lst, list):
                for j in lst:
                    if j.get("id") == job_id:
                        return j
        raise ValueError(f"config.yaml: job id '{job_id}' não encontrado em 'jobs'.")
    raise ValueError("config.yaml: 'jobs' precisa ser uma lista (recomendado) ou dict (legado).")


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
                if isinstance(obj, dict):
                    rows.append(obj)
                else:
                    rows.append({"_value": obj})
            except json.JSONDecodeError:
                rows.append({"_parse_error": True, "_line_no": line_no, "_raw": s})
    return rows


def _read_reports_md(reports_dir: Path) -> Dict[str, str]:
    if not reports_dir.exists():
        return {}
    out: Dict[str, str] = {}
    for p in sorted(reports_dir.glob("*.md")):
        out[p.name] = _read_text(p)
    return out


def _infer_tipo_processo(context: Dict[str, Any]) -> str:
    # aceitar variações comuns do seu projeto
    if not context:
        return ""
    if isinstance(context.get("tipo_processo"), str):
        return context["tipo_processo"].strip()
    cc = context.get("contexto_caso")
    if isinstance(cc, dict) and isinstance(cc.get("tipo_processo"), str):
        return cc["tipo_processo"].strip()
    return ""


def _select_skill_hint(job: Dict[str, Any], tipo_processo: str) -> Tuple[str, str]:
    target = str(job.get("process_type_target", "")).strip()

    # nomes diferentes (alguns configs usam skill_id_*, outros skill_name_*)
    default_skill = (
        job.get("skill_id_default")
        or job.get("skill_name_default")
        or job.get("skill_key_default")
        or ""
    )
    target_skill = (
        job.get("skill_id_target")
        or job.get("skill_name_target")
        or job.get("skill_key_target")
        or ""
    )

    default_skill = str(default_skill).strip()
    target_skill = str(target_skill).strip()

    if target and tipo_processo and tipo_processo == target and target_skill:
        return target_skill, "target"
    if default_skill:
        return default_skill, "default"
    return "", "none"


def _build_input_payload(
    job: Dict[str, Any],
    dataset_dir: Path,
    reports_dir: Optional[Path],
    context_file: Optional[Path],
    relacoes_file: Optional[Path],
) -> Dict[str, Any]:
    # dataset tables (JSONL)
    dataset = {
        "contratos_operacoes": _read_jsonl(dataset_dir / "contratos_operacoes.jsonl"),
        "documentos": _read_jsonl(dataset_dir / "documentos.jsonl"),
        "imoveis": _read_jsonl(dataset_dir / "imoveis.jsonl"),
        "links": _read_jsonl(dataset_dir / "links.jsonl"),
        "novacoes_detectadas": _read_jsonl(dataset_dir / "novacoes_detectadas.jsonl"),
        "onus_obrigacoes": _read_jsonl(dataset_dir / "onus_obrigacoes.jsonl"),
        "partes": _read_jsonl(dataset_dir / "partes.jsonl"),
        "pendencias": _read_jsonl(dataset_dir / "pendencias.jsonl"),
        "property_events": _read_jsonl(dataset_dir / "property_events.jsonl"),
    }

    reports = {}
    if reports_dir is not None:
        reports = _read_reports_md(reports_dir)

    contexto_caso = {}
    contexto_relacoes = {}
    if context_file is not None and context_file.exists():
        contexto_caso = _read_json(context_file)
    if relacoes_file is not None and relacoes_file.exists():
        contexto_relacoes = _read_json(relacoes_file)

    tipo_processo = _infer_tipo_processo(contexto_caso)
    skill_hint, skill_hint_mode = _select_skill_hint(job, tipo_processo)

    payload: Dict[str, Any] = {
        "dataset_dir": str(dataset_dir.as_posix()),
        "dataset": dataset,
        "reports_dir": str(reports_dir.as_posix()) if reports_dir is not None else "",
        "reports": reports,
        "contexto_caso": contexto_caso,
        "contexto_relacoes": contexto_relacoes,
        "tipo_processo": tipo_processo,
        "skill_hint": {"id": skill_hint, "mode": skill_hint_mode},
    }
    return payload


def _inject_skills_xml(prompt_md: str, skills_prompt_xml: str) -> str:
    return prompt_md.replace("{{SKILLS_PROMPT_XML}}", skills_prompt_xml)


def _call_gemini_json(
    runtime: RuntimeConfig,
    full_prompt: str,
) -> str:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "API key não encontrada. Defina GOOGLE_API_KEY ou GEMINI_API_KEY no ambiente."
        )

    # google-genai (novo)
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        config = types.GenerateContentConfig(
            temperature=runtime.temperature,
            top_p=runtime.top_p,
            max_output_tokens=runtime.max_output_tokens,
            response_mime_type="application/json",
        )
        resp = client.models.generate_content(
            model=runtime.model,
            contents=full_prompt,
            config=config,
        )
        return (resp.text or "").strip()
    except ImportError:
        # fallback: google.generativeai (mais antigo)
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=runtime.model,
            generation_config={
                "temperature": runtime.temperature,
                "top_p": runtime.top_p,
                "max_output_tokens": runtime.max_output_tokens,
            },
        )
        resp = model.generate_content(full_prompt)
        return str(getattr(resp, "text", "")).strip()


def _extract_json_object(text: str) -> Dict[str, Any]:
    s = text.strip()
    if not s:
        raise ValueError("Resposta vazia do modelo.")
    # se veio puro
    if s.startswith("{") and s.endswith("}"):
        return json.loads(s)

    # tentativa de extração (caso o modelo tenha colocado texto extra)
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Não foi possível localizar um objeto JSON na resposta do modelo.")
    candidate = s[start : end + 1].strip()
    return json.loads(candidate)


def _validate_output(schema_path: Path, output_obj: Dict[str, Any]) -> None:
    schema = _read_json(schema_path)
    Draft202012Validator(schema).validate(output_obj)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evidence-agent (config-driven, dataset_v1 JSONL)")
    parser.add_argument(
        "--config",
        default="agents/evidence-agent/config.yaml",
        help="Caminho do config.yaml (relativo ao repo root)",
    )
    parser.add_argument(
        "--job",
        default=None,
        help="ID do job (se omitido, usa o primeiro job do config)",
    )
    parser.add_argument(
        "--dataset-dir",
        default=None,
        help="Override do dataset_dir (se omitido, usa o do job)",
    )
    args = parser.parse_args()

    cfg_path = (REPO_ROOT / args.config).resolve()
    cfg = _read_yaml(cfg_path)
    runtime = _load_runtime(cfg)

    paths = cfg.get("paths") or {}
    prompt_file = str(paths.get("prompt_file", "agents/evidence-agent/prompt.md"))
    prompt_path = (REPO_ROOT / prompt_file).resolve()
    prompt_md = _read_text(prompt_path)

    skills_id = cfg.get("skills_id") or {}
    skills_prompt_file = str(skills_id.get("skills_prompt_file", "")).strip()
    if not skills_prompt_file:
        raise ValueError("config.yaml: skills_id.skills_prompt_file é obrigatório (XML de skills).")
    skills_prompt_path = (REPO_ROOT / skills_prompt_file).resolve()
    skills_prompt_xml = _read_text(skills_prompt_path)

    job = _select_job(cfg, args.job)

    schema_file = str(job.get("schema_file", "")).strip()
    if not schema_file:
        raise ValueError("config.yaml: job.schema_file é obrigatório.")
    schema_path = (REPO_ROOT / schema_file).resolve()

    dataset_dir_str = args.dataset_dir or str(job.get("dataset_dir", "")).strip()
    if not dataset_dir_str:
        raise ValueError("config.yaml: job.dataset_dir é obrigatório (diretório dataset_v1).")
    dataset_dir = (REPO_ROOT / dataset_dir_str).resolve()

    reports_dir = None
    reports_dir_str = str(job.get("reports_dir", "")).strip()
    if reports_dir_str:
        reports_dir = (REPO_ROOT / reports_dir_str).resolve()

    context_file = None
    context_file_str = str(job.get("context_file", "")).strip()
    if context_file_str:
        context_file = (REPO_ROOT / context_file_str).resolve()

    relacoes_file = None
    relacoes_file_str = str(job.get("relacoes_file", "")).strip()
    if relacoes_file_str:
        relacoes_file = (REPO_ROOT / relacoes_file_str).resolve()

    output_dir_str = str(job.get("output_dir", "")).strip()
    output_filename = str(job.get("output_filename", "")).strip()
    if not output_dir_str or not output_filename:
        raise ValueError("config.yaml: job.output_dir e job.output_filename são obrigatórios.")
    output_dir = (REPO_ROOT / output_dir_str).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Monta payload
    payload = _build_input_payload(job, dataset_dir, reports_dir, context_file, relacoes_file)

    # Monta prompt final
    prompt_with_skills = _inject_skills_xml(prompt_md, skills_prompt_xml)
    input_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    full_prompt = f"{prompt_with_skills}\n\nINPUT_JSON:\n{input_json}\n"

    # Chamada LLM
    raw = _call_gemini_json(runtime, full_prompt)

    # Parse + validação
    try:
        out_obj = _extract_json_object(raw)
        _validate_output(schema_path, out_obj)
    except Exception:
        # mantém rastreabilidade para depuração (sem “gambiarra”; é evidência técnica)
        (output_dir / "_last_raw.txt").write_text(raw, encoding="utf-8")
        (output_dir / "_last_prompt.txt").write_text(full_prompt, encoding="utf-8")
        raise

    out_path = output_dir / output_filename
    out_path.write_text(json.dumps(out_obj, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] evidence-agent output: {out_path.as_posix()}")


if __name__ == "__main__":
    main()
