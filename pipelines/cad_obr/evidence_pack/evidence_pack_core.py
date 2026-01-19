"""Evidence Pack generator (pack_global)

Gera um pack compacto a partir de:
- reports: outputs/cad_obr/04_reconciler/reports/<dataset_id>/*.md
- dataset jsonl: outputs/cad_obr/04_reconciler/<dataset_id>/*.jsonl

Este gerador é propositalmente conservador e determinístico:
- 12 findings (2 resumo, 3 timeline, 3 onus, 2 novacoes, 2 pendencias)
- até 20 support_rows por finding

Sem depender de nomes rígidos de colunas no JSONL.
"""

from __future__ import annotations

import dataclasses
import datetime as _dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _try_import_duckdb():
    try:
        import duckdb  # type: ignore

        return duckdb
    except Exception:
        return None


def build_duckdb_views(dataset_dir: Path, duckdb_path: Path) -> Dict[str, Any]:
    """Cria/atualiza um arquivo DuckDB com views para cada *.jsonl do dataset.

    - Cada view tem o nome do arquivo sem extensão (stem).
    - Também cria a tabela __dataset_files (hash/linhas) para rastreabilidade.

    Observação: se a lib duckdb não estiver instalada, retorna status=skipped.
    """
    duckdb = _try_import_duckdb()
    if duckdb is None:
        return {"status": "skipped", "reason": "duckdb não instalado no ambiente"}

    duckdb_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(duckdb_path))

    files_meta = []
    for f in sorted(dataset_dir.glob("*.jsonl")):
        view = f.stem
        # read_json_auto detecta newline-delimited JSON
        con.execute(
            f"CREATE OR REPLACE VIEW {view} AS SELECT * FROM read_json_auto('{str(f)}');"
        )
        # Usar helpers locais (definidos neste módulo)
        sha = sha256_file(f)
        lines = count_jsonl_lines(f)
        files_meta.append((f.name, str(f), sha, int(lines)))

    con.execute(
        "CREATE TABLE IF NOT EXISTS __dataset_files (filename VARCHAR, path VARCHAR, sha256 VARCHAR, rows BIGINT);"
    )
    con.execute("DELETE FROM __dataset_files;")
    con.executemany("INSERT INTO __dataset_files VALUES (?, ?, ?, ?);", files_meta)
    con.close()

    return {
        "status": "ok",
        "duckdb_path": str(duckdb_path),
        "views": [x[0].replace(".jsonl", "") for x in files_meta],
        "files": len(files_meta),
    }


JSONDict = Dict[str, Any]


def now_iso() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def read_jsonl_rows(
    path: Path, limit: Optional[int] = None
) -> Iterable[Tuple[int, JSONDict]]:
    """Itera linhas de um JSONL, retornando (rownum_1based, obj)."""
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                yield idx, obj
                if limit and idx >= limit:
                    return


def count_jsonl_lines(path: Path) -> int:
    c = 0
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.strip():
                c += 1
    return c


def trim_value(
    v: Any, max_str: int = 400, max_list: int = 20, max_dict: int = 40
) -> Any:
    if isinstance(v, str):
        return v if len(v) <= max_str else v[: max_str - 1] + "…"
    if isinstance(v, list):
        out = [trim_value(x, max_str=max_str) for x in v[:max_list]]
        if len(v) > max_list:
            out.append("…")
        return out
    if isinstance(v, dict):
        out: Dict[str, Any] = {}
        for i, (k, val) in enumerate(v.items()):
            if i >= max_dict:
                out["…"] = "…"
                break
            out[str(k)] = trim_value(val, max_str=max_str)
        return out
    return v


def trim_row(row: JSONDict) -> JSONDict:
    # remove campos potencialmente enormes
    drop_keys = {"texto", "content", "raw_text", "md", "markdown", "html"}
    out: JSONDict = {}
    for k, v in row.items():
        if k in drop_keys:
            continue
        out[k] = trim_value(v)
    return out


def extract_matriculas(text: str) -> List[str]:
    # Captura números com e sem ponto; preserva como aparece mais frequentemente.
    candidates = re.findall(r"\b\d{1,3}(?:\.\d{3})+\b|\b\d{3,6}\b", text)
    # Dedup mantendo ordem
    seen = set()
    out = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def pick_nonempty_lines(md: str, max_lines: int) -> List[str]:
    lines = []
    for ln in md.splitlines():
        s = ln.strip()
        if not s:
            continue
        # pular headings muito genéricos
        if s.startswith("#"):
            continue
        lines.append(s)
        if len(lines) >= max_lines:
            break
    return lines


@dataclasses.dataclass
class FindingDraft:
    finding_id: str
    finding_type: str
    title: str
    summary: str
    severity: str
    report_file: str
    excerpt: str
    keys: Dict[str, Any]


def severity_from_text(s: str) -> str:
    s_low = s.lower()
    if any(
        w in s_low
        for w in [
            "diverg",
            "inconsist",
            "sem v",
            "sem vínculo",
            "contrad",
            "lacuna",
            "pendên",
            "pendenc",
        ]
    ):
        return "ALTA"
    return "MEDIA"


def build_report_index(reports_dir: Path) -> List[JSONDict]:
    idx = []
    for p in sorted(reports_dir.glob("*.md")):
        try:
            idx.append(
                {
                    "report_file": p.name,
                    "report_path": str(p),
                    "hash_sha256": sha256_file(p),
                    "mtime": _dt.datetime.fromtimestamp(
                        p.stat().st_mtime, tz=_dt.timezone.utc
                    ).isoformat(),
                }
            )
        except Exception:
            idx.append({"report_file": p.name, "report_path": str(p)})
    return idx


def draft_findings_from_reports(
    reports_dir: Path,
) -> Tuple[List[FindingDraft], Dict[str, Any]]:
    """Cria 12 FindingDraft determinísticos a partir dos reports."""
    files = {
        "resumo": reports_dir / "00_resumo_exec.md",
        "timeline": reports_dir / "01_timeline_por_matricula.md",
        "onus": reports_dir / "02_onus_por_matricula.md",
        "novacoes": reports_dir / "03_novacoes.md",
        "pendencias": reports_dir / "04_pendencias.md",
    }

    texts: Dict[str, str] = {}
    for k, p in files.items():
        texts[k] = read_text(p) if p.exists() else ""

    focus = {
        "matriculas": extract_matriculas("\n".join(texts.values())),
        "partes_chave": [],
        "datas_referidas": [],
        "temas": ["HIPOTECA", "NOVACAO", "PENDENCIA", "TIMELINE"],
    }

    drafts: List[FindingDraft] = []

    # 2 do resumo
    resumo_lines = pick_nonempty_lines(texts["resumo"], 2)
    for i in range(2):
        line = (
            resumo_lines[i]
            if i < len(resumo_lines)
            else "(Resumo não disponível no report)"
        )
        drafts.append(
            FindingDraft(
                finding_id=f"F{(i + 1):02d}",
                finding_type="RESUMO_EXEC",
                title=f"Resumo executivo {i + 1}",
                summary=line[:320],
                severity=severity_from_text(line),
                report_file="00_resumo_exec.md",
                excerpt=line[:500],
                keys={"matriculas": extract_matriculas(line)},
            )
        )

    # helpers para escolher matrículas por frequência
    def top_matriculas(md: str, n: int) -> List[str]:
        mats = re.findall(r"\b\d{1,3}(?:\.\d{3})+\b|\b\d{3,6}\b", md)
        freq: Dict[str, int] = {}
        for m in mats:
            freq[m] = freq.get(m, 0) + 1
        ranked = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
        return [m for m, _ in ranked[:n]]

    # 3 da timeline
    top3_tl = top_matriculas(texts["timeline"], 3)
    for i in range(3):
        mat = (
            top3_tl[i]
            if i < len(top3_tl)
            else (focus["matriculas"][i] if i < len(focus["matriculas"]) else None)
        )
        title = (
            f"Timeline (matrícula {mat})"
            if mat
            else "Timeline (matrícula não identificada)"
        )
        excerpt = ("\n".join(pick_nonempty_lines(texts["timeline"], 6)))[:600]
        drafts.append(
            FindingDraft(
                finding_id=f"F{(3 + i):02d}",
                finding_type="TIMELINE",
                title=title,
                summary=f"Eventos e marcos relevantes associados à matrícula {mat}."
                if mat
                else "Eventos e marcos relevantes do report de timeline.",
                severity=severity_from_text(texts["timeline"]),
                report_file="01_timeline_por_matricula.md",
                excerpt=excerpt,
                keys={"matricula": mat} if mat else {},
            )
        )

    # 3 de ônus
    top3_onus = top_matriculas(texts["onus"], 3)
    for i in range(3):
        mat = (
            top3_onus[i]
            if i < len(top3_onus)
            else (focus["matriculas"][i] if i < len(focus["matriculas"]) else None)
        )
        title = (
            f"Ônus/obrigações (matrícula {mat})"
            if mat
            else "Ônus/obrigações (matrícula não identificada)"
        )
        excerpt = ("\n".join(pick_nonempty_lines(texts["onus"], 6)))[:600]
        drafts.append(
            FindingDraft(
                finding_id=f"F{(6 + i):02d}",
                finding_type="ONUS",
                title=title,
                summary=f"Ônus e obrigações relevantes associados à matrícula {mat}."
                if mat
                else "Ônus e obrigações relevantes do report.",
                severity=severity_from_text(texts["onus"]),
                report_file="02_onus_por_matricula.md",
                excerpt=excerpt,
                keys={"matricula": mat} if mat else {},
            )
        )

    # 2 de novações
    nov_lines = pick_nonempty_lines(texts["novacoes"], 2)
    for i in range(2):
        line = (
            nov_lines[i] if i < len(nov_lines) else "(Novação não disponível no report)"
        )
        mat = extract_matriculas(line)
        drafts.append(
            FindingDraft(
                finding_id=f"F{(9 + i):02d}",
                finding_type="NOVACAO",
                title=f"Novação {i + 1}",
                summary=line[:320],
                severity=severity_from_text(line),
                report_file="03_novacoes.md",
                excerpt=line[:600],
                keys={"matriculas": mat} if mat else {},
            )
        )

    # 2 de pendências
    pen_lines = pick_nonempty_lines(texts["pendencias"], 2)
    for i in range(2):
        line = (
            pen_lines[i]
            if i < len(pen_lines)
            else "(Pendência não disponível no report)"
        )
        mat = extract_matriculas(line)
        drafts.append(
            FindingDraft(
                finding_id=f"F{(11 + i):02d}",
                finding_type="PENDENCIA",
                title=f"Pendência {i + 1}",
                summary=line[:320],
                severity=severity_from_text(line),
                report_file="04_pendencias.md",
                excerpt=line[:600],
                keys={"matriculas": mat} if mat else {},
            )
        )

    # Garantia de 12
    return drafts[:12], focus


def _match_matricula_in_row(row: JSONDict, matricula: str) -> bool:
    # tenta chaves comuns
    for k in ("matricula", "matricula_id", "matricula_numero", "id_matricula"):
        if k in row and row.get(k) is not None:
            if str(row.get(k)) == str(matricula):
                return True
    # fallback: busca em string dump
    try:
        blob = json.dumps(row, ensure_ascii=False)
        return str(matricula) in blob
    except Exception:
        return False


def collect_support_rows(
    dataset_dir: Path,
    finding: FindingDraft,
    max_support_rows: int,
) -> List[JSONDict]:
    """Coleta support_rows do JSONL primário para o finding."""
    mapping = {
        "TIMELINE": "property_events.jsonl",
        "ONUS": "onus_obrigacoes.jsonl",
        "NOVACAO": "novacoes_detectadas.jsonl",
        "PENDENCIA": "pendencias.jsonl",
        "RESUMO_EXEC": "onus_obrigacoes.jsonl",
    }
    src_file = mapping.get(finding.finding_type, "onus_obrigacoes.jsonl")
    path = dataset_dir / src_file
    if not path.exists():
        return []

    matriculas = []
    if "matricula" in finding.keys and finding.keys.get("matricula"):
        matriculas.append(str(finding.keys["matricula"]))
    if "matriculas" in finding.keys and isinstance(
        finding.keys.get("matriculas"), list
    ):
        matriculas.extend([str(x) for x in finding.keys["matriculas"] if x])

    out: List[JSONDict] = []

    for rownum, obj in read_jsonl_rows(path):
        if matriculas:
            if not any(_match_matricula_in_row(obj, m) for m in matriculas):
                continue
        # add
        out.append(
            {
                "table": src_file.replace(".jsonl", ""),
                "_src_file": src_file,
                "_src_row": rownum,
                "row": trim_row(obj),
                "keys": {"matricula": matriculas[0]} if matriculas else {},
            }
        )
        if len(out) >= max_support_rows:
            break

    return out


def build_document_inventory(
    dataset_dir: Path, max_list: int = 30
) -> Tuple[JSONDict, List[JSONDict]]:
    documentos = dataset_dir / "documentos.jsonl"
    links = dataset_dir / "links.jsonl"

    docs_list: List[JSONDict] = []
    counts: Dict[str, int] = {}
    seen: set = set()

    def doc_key(d: JSONDict) -> str:
        for k in ("document_id", "id_doc", "source_id", "hash", "sha256"):
            if k in d and d.get(k):
                return f"{k}:{d.get(k)}"
        return sha256_text(json.dumps(d, ensure_ascii=False))

    def doc_type(d: JSONDict) -> str:
        for k in ("tipo", "tipo_doc", "document_type", "categoria"):
            if k in d and d.get(k):
                return str(d.get(k))
        return "desconhecido"

    for p in (documentos, links):
        if not p.exists():
            continue
        for _rownum, obj in read_jsonl_rows(p):
            t = doc_type(obj)
            counts[t] = counts.get(t, 0) + 1
            k = doc_key(obj)
            if k in seen:
                continue
            seen.add(k)
            if len(docs_list) < max_list:
                docs_list.append(
                    {
                        "id_doc": obj.get("id_doc")
                        or obj.get("document_id")
                        or obj.get("source_id")
                        or None,
                        "tipo": t,
                        "descricao": trim_value(
                            obj.get("descricao")
                            or obj.get("titulo")
                            or obj.get("nome")
                            or ""
                        ),
                        "referencia": trim_value(
                            obj.get("referencia")
                            or obj.get("path")
                            or obj.get("url")
                            or ""
                        ),
                        "observacao": None,
                    }
                )

    inv = {
        "total_documentos": sum(counts.values()),
        "por_tipo": counts,
    }
    return inv, docs_list


def build_missing_docs(dataset_dir: Path, max_items: int = 30) -> List[JSONDict]:
    """Deriva recomendações a partir de pendencias.jsonl (quando existir)."""
    pend = dataset_dir / "pendencias.jsonl"
    out: List[JSONDict] = []
    if not pend.exists():
        return out

    i = 0
    for _rownum, obj in read_jsonl_rows(pend):
        if i >= max_items:
            break
        tipo = (
            obj.get("tipo_documento")
            or obj.get("tipo")
            or obj.get("documento")
            or "documento_recomendado"
        )
        desc = obj.get("descricao") or obj.get("motivo") or obj.get("detalhe") or ""
        prioridade = obj.get("prioridade") or "media"
        out.append(
            {
                "id_item": f"PEND-{i + 1:02d}",
                "tipo_documento": str(tipo),
                "descricao": trim_value(desc)
                if desc
                else "Não consta referência suficiente no conjunto fornecido; recomendável coligir documento correlato.",
                "prioridade": str(prioridade) if prioridade else "media",
                "status": "pendente",
                "relacionado_a_relacao": None,
                "relacionado_a_obrigacoes": None,
            }
        )
        i += 1

    return out


def generate_pack_global(
    dataset_dir: Path,
    reports_dir: Path,
    dataset_id: str,
    out_path: Path,
    max_findings: int = 12,
    max_support_rows: int = 20,
    duckdb_path: Optional[Path] = None,
) -> JSONDict:
    report_index = build_report_index(reports_dir) if reports_dir.exists() else []

    duckdb_info = None
    if duckdb_path:
        try:
            duckdb_info = build_duckdb_views(
                dataset_dir=dataset_dir, duckdb_path=duckdb_path
            )
        except Exception as e:
            duckdb_info = {
                "status": "error",
                "reason": str(e),
                "duckdb_path": str(duckdb_path),
            }
    drafts, focus = draft_findings_from_reports(reports_dir)
    drafts = drafts[:max_findings]

    stats = {
        "rows_by_table": {},
        "files_present": [],
    }
    for p in sorted(dataset_dir.glob("*.jsonl")):
        stats["files_present"].append(p.name)
        stats["rows_by_table"][p.stem] = count_jsonl_lines(p)

    inv_counts, inv_list = build_document_inventory(dataset_dir)
    missing_docs = build_missing_docs(dataset_dir)

    findings: List[JSONDict] = []
    for d in drafts:
        support = collect_support_rows(
            dataset_dir, d, max_support_rows=max_support_rows
        )
        findings.append(
            {
                "finding_id": d.finding_id,
                "finding_type": d.finding_type,
                "title": d.title,
                "summary": d.summary,
                "severity": d.severity,
                "report_refs": [
                    {
                        "report_file": d.report_file,
                        "section_hint": None,
                        "line_hint": None,
                        "excerpt": d.excerpt,
                    }
                ],
                "keys": d.keys,
                "support_rows": support,
            }
        )

    pack: JSONDict = {
        "pack_version": "evidence_pack.v1",
        "pack_id": f"{dataset_id}_pack_global_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "dataset_id": dataset_id,
        "generated_at": now_iso(),
        "inputs": {
            "dataset_dir": str(dataset_dir),
            "reports_dir": str(reports_dir),
            "duckdb_path": str(duckdb_path) if duckdb_path else None,
            "duckdb_info": duckdb_info,
        },
        "report_index": report_index,
        "focus": focus,
        "stats": stats,
        "findings": findings,
        "documentos_apresentados": {
            "resumo": inv_counts,
            "lista": inv_list,
        },
        "documentos_recomendados_para_colheita": missing_docs,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return pack
