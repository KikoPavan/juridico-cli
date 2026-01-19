# agents/evidence-agent/main.py
import argparse
import json
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, Tuple

try:
    import yaml  # type: ignore
except Exception as e:  # pragma: no cover
    raise RuntimeError(
        "Dependência ausente: pyyaml. Instale no seu venv (uv/pip)."
    ) from e

try:
    import jsonschema  # type: ignore
except Exception as e:  # pragma: no cover
    raise RuntimeError(
        "Dependência ausente: jsonschema. Instale no seu venv (uv/pip)."
    ) from e


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _write_text(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _read_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _extract_json_object(raw: str) -> Dict[str, Any]:
    raw = raw.strip()

    # tentativa direta
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    # encontrar o primeiro objeto { ... } no texto
    m = re.search(r"\{", raw)
    if not m:
        raise ValueError(
            "Não foi possível localizar início de objeto JSON na resposta do modelo."
        )
    start = m.start()

    # tentar pelo último }
    end = raw.rfind("}")
    if end == -1 or end <= start:
        raise ValueError(
            "JSON parece truncado: não foi encontrado fechamento do objeto."
        )

    candidate = raw[start : end + 1]
    try:
        obj = json.loads(candidate)
    except Exception as e:
        raise ValueError("Falha ao parsear JSON extraído da resposta do modelo.") from e

    if not isinstance(obj, dict):
        raise ValueError("O JSON retornado não é um objeto (dict).")
    return obj


def _validate_schema(schema_path: str, envelope: Dict[str, Any]) -> None:
    schema = _read_json(schema_path)
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(envelope), key=lambda e: list(e.path))
    if errors:
        lines = ["Falha de validacao JSON Schema:"]
        for err in errors:
            lines.append(f"- {list(err.path)}: {err.message}")
        raise ValueError("\n".join(lines))


def _severity_map(val: Any) -> str:
    s = str(val or "").strip().lower()
    mapping = {
        "low": "baixa",
        "medium": "media",
        "high": "alta",
        "critical": "critica",
        "baixa": "baixa",
        "media": "media",
        "média": "media",
        "alta": "alta",
        "crítica": "critica",
        "critica": "critica",
    }
    return mapping.get(s, s or "media")


def _normalize_docs_apresentados(obj: Any) -> Dict[str, Any]:
    # objetivo: garantir {total_documentos, por_tipo, lista} e remover extras.
    lista = []
    if isinstance(obj, list):
        lista = obj
    elif isinstance(obj, dict):
        # aceitamos 'lista' ou variações
        lista = obj.get("lista") or obj.get("itens") or obj.get("items") or []
        if not isinstance(lista, list):
            lista = []
    else:
        lista = []

    # normalizar itens
    norm_lista = []
    for it in lista:
        if not isinstance(it, dict):
            continue
        norm_lista.append(
            {
                "id_doc": str(
                    it.get("id_doc") or it.get("id") or it.get("doc_id") or ""
                ),
                "tipo": str(it.get("tipo") or it.get("type") or "desconhecido"),
                "descricao": str(it.get("descricao") or it.get("description") or ""),
                "referencia": str(
                    it.get("referencia") or it.get("ref") or it.get("fonte") or ""
                ),
                "observacao": it.get("observacao")
                if "observacao" in it
                else it.get("note"),
            }
        )

    por_tipo: Dict[str, int] = {}
    for it in norm_lista:
        t = (it.get("tipo") or "desconhecido").strip() or "desconhecido"
        por_tipo[t] = por_tipo.get(t, 0) + 1

    return {
        "total_documentos": len(norm_lista),
        "por_tipo": por_tipo,
        "lista": norm_lista,
    }


def _normalize_evidencias(evs: Any) -> list:
    out = []
    if not isinstance(evs, list):
        return out
    for ev in evs:
        if not isinstance(ev, dict):
            continue
        fonte = (
            ev.get("fonte")
            or ev.get("source")
            or ev.get("ref")
            or ev.get("arquivo")
            or ""
        )
        trecho = (
            ev.get("trecho")
            or ev.get("text")
            or ev.get("excerpt")
            or ev.get("fragmento")
            or ""
        )
        obs = (
            ev.get("observacao")
            or ev.get("note")
            or ev.get("comentario")
            or ev.get("why")
            or ""
        )
        out.append(
            {
                "fonte": str(fonte) if fonte is not None else "",
                "trecho": str(trecho) if trecho is not None else "",
                "observacao": str(obs) if obs is not None else "",
            }
        )
    return out


def _normalize_findings(findings: Any) -> list:
    if not isinstance(findings, list):
        return []
    norm = []
    for f in findings:
        if not isinstance(f, dict):
            continue

        fid = f.get("id") or f.get("finding_id") or f.get("findingId") or ""
        titulo = f.get("titulo") or f.get("title") or ""
        descricao = f.get("descricao") or f.get("summary") or f.get("description") or ""
        sev = f.get("severidade") or f.get("severity") or ""

        evidencias = f.get("evidencias") or f.get("evidence") or f.get("snippets") or []
        evidencias_norm = _normalize_evidencias(evidencias)

        recomendacoes = f.get("recomendacoes") or f.get("recommendations") or []
        if not isinstance(recomendacoes, list):
            recomendacoes = []

        # limpar para o formato esperado (sem propriedades extras)
        norm.append(
            {
                "id": str(fid) if fid is not None else "",
                "titulo": str(titulo) if titulo is not None else "",
                "descricao": str(descricao) if descricao is not None else "",
                "severidade": _severity_map(sev),
                "evidencias": evidencias_norm,
                "recomendacoes": [str(x) for x in recomendacoes if x is not None],
            }
        )
    return norm


def _ensure_result_shape(result: Dict[str, Any]) -> Dict[str, Any]:
    resumo = (
        result.get("resumo_executivo")
        or result.get("executive_summary")
        or result.get("summary")
        or ""
    )
    findings = _normalize_findings(
        result.get("findings") or result.get("achados") or []
    )

    inv = result.get("inventario_documental") or result.get("inventario") or {}
    if not isinstance(inv, dict):
        inv = {}

    docs_apr = _normalize_docs_apresentados(
        inv.get("documentos_apresentados") or inv.get("docs_apresentados") or []
    )
    docs_falt = inv.get("documentos_faltantes") or inv.get("missing_documents") or []
    rec_colheita = (
        inv.get("documentos_recomendados_para_colheita")
        or inv.get("docs_recomendados")
        or []
    )

    if not isinstance(docs_falt, list):
        docs_falt = []
    if not isinstance(rec_colheita, list):
        rec_colheita = []

    # garantir resumo_executivo se vazio
    if not str(resumo).strip():
        if findings:
            resumo = "; ".join([f["titulo"] for f in findings[:3] if f.get("titulo")])
        else:
            resumo = "Nenhum finding consolidado a partir do pack."

    return {
        "resumo_executivo": str(resumo),
        "findings": findings,
        "inventario_documental": {
            "documentos_apresentados": docs_apr,
            "documentos_faltantes": [str(x) for x in docs_falt if x is not None],
            "documentos_recomendados_para_colheita": [
                str(x) for x in rec_colheita if x is not None
            ],
        },
    }


def _render_prompt(template_path: str, skill_text: str, pack_obj: Any) -> str:
    tpl = _read_text(template_path)
    pack_json = json.dumps(pack_obj, ensure_ascii=False, indent=2)
    return tpl.replace("{{SKILL_TEXT}}", skill_text).replace("{{PACK_JSON}}", pack_json)


def _load_skill_text(skill_path: str) -> str:
    return _read_text(skill_path).strip()


def _call_model(
    runtime: Dict[str, Any], prompt: str, api_key_override: str | None = None
) -> Tuple[str, str]:
    api_key_env = runtime.get("api_key_env") or "GOOGLE_API_KEY"
    api_key = (
        api_key_override
        or os.getenv(str(api_key_env))
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY não está definido no ambiente (nem GEMINI_API_KEY)."
        )

    from google import genai  # type: ignore
    from google.genai import types  # type: ignore

    client = genai.Client(api_key=api_key)

    model = str(runtime.get("model") or "gemini-2.5-flash")
    temperature = float(runtime.get("temperature", 0.0))
    top_p = float(runtime.get("top_p", 0.95))
    max_output_tokens = int(runtime.get("max_output_tokens", 8192))
    response_mime_type = str(runtime.get("response_mime_type") or "application/json")

    cfg = types.GenerateContentConfig(
        temperature=temperature,
        top_p=top_p,
        max_output_tokens=max_output_tokens,
        response_mime_type=response_mime_type,
    )

    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config=cfg,
    )

    raw = (resp.text or "").strip()
    model_used = model
    try:
        mv = getattr(resp, "model_version", None)
        if mv:
            model_used = str(mv)
    except Exception:
        pass

    return raw, model_used


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--job", default=None)
    ap.add_argument("--api-key", default=None)
    ap.add_argument("--pack", default=None)
    args = ap.parse_args()

    cfg = _read_yaml(args.config)
    runtime = cfg.get("runtime") or {}
    paths = cfg.get("paths") or {}
    skills_map = cfg.get("skills_map") or {}
    jobs = cfg.get("jobs") or {}

    prompt_file = str(paths["prompt_file"])
    schema_file = str(paths["schema_file"])
    pack_file = str(args.pack or paths.get("pack_file"))

    out_dir = str(paths.get("output_dir", "outputs/cad_obr/05_evidence/dataset_v1"))
    out_name = str(paths.get("output_filename", "evidence_out.json"))
    last_prompt_name = str(paths.get("last_prompt_filename", "_last_prompt.txt"))
    last_raw_name = str(paths.get("last_raw_filename", "_last_raw.txt"))

    # selecionar job
    selected_job = None
    if args.job:
        for lst in jobs.values():
            if isinstance(lst, list):
                for j in lst:
                    if isinstance(j, dict) and j.get("id") == args.job:
                        selected_job = j
                        break
            if selected_job:
                break
        if not selected_job:
            raise RuntimeError(f"Job não encontrado: {args.job}")
    else:
        # pega o primeiro job da primeira chave
        for lst in jobs.values():
            if isinstance(lst, list) and lst:
                selected_job = lst[0]
                break
        if not selected_job:
            raise RuntimeError("Nenhum job definido no config.yaml.")

    skill_key = selected_job.get("skill_key_default") or "core"
    skill_path = skills_map.get(skill_key)
    if not skill_path:
        raise RuntimeError(
            f"skill_key_default '{skill_key}' não encontrado em skills_map."
        )
    skill_text = _load_skill_text(str(skill_path))

    pack_obj = _read_json(pack_file)
    prompt = _render_prompt(prompt_file, skill_text, pack_obj)

    # debug files
    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_base = os.path.join(out_dir)
    os.makedirs(out_base, exist_ok=True)
    _write_text(os.path.join(out_base, last_prompt_name), prompt)

    raw, model_used = _call_model(runtime, prompt, api_key_override=args.api_key)
    _write_text(os.path.join(out_base, last_raw_name), raw)

    parsed = _extract_json_object(raw)

    # se veio envelope completo, usa; senão, monta
    if (
        isinstance(parsed, dict)
        and "outputs" in parsed
        and isinstance(parsed.get("outputs"), dict)
    ):
        envelope = parsed
        # normaliza apenas se existir result
        if "result" in envelope["outputs"] and isinstance(
            envelope["outputs"]["result"], dict
        ):
            envelope["outputs"]["result"] = _ensure_result_shape(
                envelope["outputs"]["result"]
            )
    else:
        result_obj = _ensure_result_shape(parsed)
        envelope = {
            "meta": {
                "model_used": model_used,
                "job_id": selected_job.get("id"),
            },
            "outputs": {"result": result_obj},
        }

    _validate_schema(schema_file, envelope)

    out_path = os.path.join(out_base, out_name)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(envelope, f, ensure_ascii=False, indent=2)

    print(f"OK: escrito: {out_path}")
    print(f"Model: {model_used}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
