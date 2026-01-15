# pipelines/cad_obr/reconciler/report_md_cli.py
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict, Counter
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


JSONL_FILES = [
    "documentos.jsonl",
    "partes.jsonl",
    "imoveis.jsonl",
    "contratos_operacoes.jsonl",
    "onus_obrigacoes.jsonl",
    "property_events.jsonl",
    "links.jsonl",
    "pendencias.jsonl",
    "novacoes_detectadas.jsonl",
]


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                # ignora linha inválida, mas mantém execução
                continue
    return rows


def is_iso_date(s: Any) -> bool:
    if not isinstance(s, str):
        return False
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", s.strip()))


def to_date(s: Any) -> Optional[date]:
    if not isinstance(s, str):
        return None
    s = s.strip()
    if not s or not is_iso_date(s):
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def md_escape(s: Any) -> str:
    if s is None:
        return ""
    txt = str(s)
    txt = txt.replace("|", "\\|")
    txt = txt.replace("\n", " ")
    return txt


def md_table(headers: List[str], rows: List[List[Any]]) -> str:
    if not rows:
        return "_(sem dados)_\n"
    h = "| " + " | ".join(md_escape(x) for x in headers) + " |\n"
    sep = "| " + " | ".join(["---"] * len(headers)) + " |\n"
    body = ""
    for r in rows:
        body += "| " + " | ".join(md_escape(x) for x in r) + " |\n"
    return h + sep + body + "\n"


def _first_nonempty_str(d: Dict[str, Any], keys: List[str]) -> str:
    for k in keys:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _pick_nested(d: Dict[str, Any], keys: List[str]) -> str:
    """
    Tenta achar texto em chaves comuns, primeiro no nível raiz,
    depois em contêineres comuns (meta/context/data/...).
    """
    msg = _first_nonempty_str(d, keys)
    if msg:
        return msg

    for container in ("meta", "context", "dados", "data", "info", "payload"):
        v = d.get(container)
        if isinstance(v, dict):
            msg = _first_nonempty_str(v, keys)
            if msg:
                return msg

    return ""


def _compact_json(r: Dict[str, Any], limit: int = 280) -> str:
    try:
        s = json.dumps(r, ensure_ascii=False, separators=(",", ":"))
        return s if len(s) <= limit else (s[: limit - 3] + "...")
    except Exception:
        return "<json inválido>"


def _iter_strings(obj: Any) -> Iterable[str]:
    if isinstance(obj, str):
        yield obj
        return
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _iter_strings(v)
        return
    if isinstance(obj, list):
        for it in obj:
            yield from _iter_strings(it)
        return


def _find_regex_in_record(rec: Dict[str, Any], pattern: str) -> str:
    rx = re.compile(pattern)
    for s in _iter_strings(rec):
        m = rx.search(s)
        if m:
            return m.group(1) if m.groups() else m.group(0)
    return ""


def _extract_doc_basename(rec: Dict[str, Any]) -> str:
    """
    Tenta extrair o nome do arquivo .json (collector_out_*.json / monetary_*.json)
    a partir de qualquer string do registro (incluindo paths completos).
    """
    # Prioriza arquivos do collector/monetary
    name = _find_regex_in_record(rec, r"(collector_out[^/\\]*\.json)")
    if name:
        return name
    name = _find_regex_in_record(rec, r"(monetary_[^/\\]*\.json)")
    if name:
        return name

    # Fallback: qualquer path que termine em .json -> basename
    for s in _iter_strings(rec):
        if isinstance(s, str) and ".json" in s:
            try:
                p = Path(s)
                if p.suffix.lower() == ".json":
                    return p.name
            except Exception:
                pass
    return ""


def pend_msg(r: Dict[str, Any]) -> str:
    msg = _pick_nested(
        r,
        ["mensagem", "message", "detail", "descricao", "description", "erro", "error", "texto", "reason", "motivo"],
    )
    return msg if msg else _compact_json(r)


def pend_property_id(r: Dict[str, Any]) -> str:
    pid = _pick_nested(r, ["property_id", "matricula_id", "imovel_id"])
    if pid:
        return pid
    # Heurística: procurar "matricula:7546"
    pid = _find_regex_in_record(r, r"(matricula:\d+)")
    return pid


def pend_doc_id(r: Dict[str, Any]) -> str:
    did = _pick_nested(r, ["source_doc_id", "doc_id", "documento_id", "source_id", "source_path", "source_file"])
    if isinstance(did, str) and did.strip():
        # se vier como path, mostrar só o arquivo
        if did.strip().endswith(".json"):
            return Path(did.strip()).name
        return did.strip()

    # fallback: tenta extrair o nome do arquivo
    name = _extract_doc_basename(r)
    return name


def pend_registro_ref(r: Dict[str, Any]) -> str:
    rr = _pick_nested(r, ["registro_ref", "registro", "ref_registro"])
    if rr:
        return rr

    # Heurística: tenta achar "R.11" ou "AV.5"
    rr = _find_regex_in_record(r, r"\b((?:R|AV)\.\d+)\b")
    if rr:
        return rr

    # Heurística: se vier em entity_id como "matricula:905#R.11-905"
    rr = _find_regex_in_record(r, r"#((?:R|AV)\.\d+)")
    return rr


def pend_group_key(r: Dict[str, Any]) -> str:
    """
    Agrupador mais útil: tenta entity_type/reason_code/regra_aplicada etc.
    """
    for k in ("tipo", "code", "kind", "categoria", "entity_type", "reason_code", "regra_aplicada"):
        v = r.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return "pendencia"


def sort_key_date_iso(rec: Dict[str, Any], key: str) -> Tuple[int, str]:
    v = rec.get(key)
    if isinstance(v, str) and is_iso_date(v):
        return (0, v)
    return (1, "")


def normalize_property_label(property_id: str) -> str:
    # Ex.: "matricula:7546" -> "Matrícula 7.546"
    m = re.search(r"(\d+)$", property_id or "")
    if not m:
        return property_id
    digits = m.group(1)
    # formata com separador de milhar se fizer sentido (7546 -> 7.546)
    if len(digits) > 3:
        return f"Matrícula {digits[:-3]}.{digits[-3:]}"
    return f"Matrícula {digits}"


@dataclass
class Dataset:
    dataset_dir: Path
    documentos: List[Dict[str, Any]]
    partes: List[Dict[str, Any]]
    imoveis: List[Dict[str, Any]]
    contratos_operacoes: List[Dict[str, Any]]
    onus_obrigacoes: List[Dict[str, Any]]
    property_events: List[Dict[str, Any]]
    links: List[Dict[str, Any]]
    pendencias: List[Dict[str, Any]]
    novacoes: List[Dict[str, Any]]


def load_dataset(dataset_dir: Path) -> Dataset:
    return Dataset(
        dataset_dir=dataset_dir,
        documentos=read_jsonl(dataset_dir / "documentos.jsonl"),
        partes=read_jsonl(dataset_dir / "partes.jsonl"),
        imoveis=read_jsonl(dataset_dir / "imoveis.jsonl"),
        contratos_operacoes=read_jsonl(dataset_dir / "contratos_operacoes.jsonl"),
        onus_obrigacoes=read_jsonl(dataset_dir / "onus_obrigacoes.jsonl"),
        property_events=read_jsonl(dataset_dir / "property_events.jsonl"),
        links=read_jsonl(dataset_dir / "links.jsonl"),
        pendencias=read_jsonl(dataset_dir / "pendencias.jsonl"),
        novacoes=read_jsonl(dataset_dir / "novacoes_detectadas.jsonl"),
    )


def guess_property_ids(ds: Dataset) -> List[str]:
    ids = set()
    for r in ds.property_events:
        pid = r.get("property_id")
        if isinstance(pid, str) and pid.strip():
            ids.add(pid.strip())
    for r in ds.imoveis:
        pid = r.get("property_id")
        if isinstance(pid, str) and pid.strip():
            ids.add(pid.strip())
    return sorted(ids)


def filter_by_property(rows: List[Dict[str, Any]], property_id: Optional[str]) -> List[Dict[str, Any]]:
    if not property_id:
        return rows
    out: List[Dict[str, Any]] = []
    for r in rows:
        if r.get("property_id") == property_id:
            out.append(r)
    return out


def pick_first_anuencia_date(events: List[Dict[str, Any]]) -> Optional[str]:
    # busca event_type == "ANUENCIA_BANCO" (se existir)
    anu = [e for e in events if e.get("event_type") == "ANUENCIA_BANCO" and isinstance(e.get("event_date"), str)]
    anu.sort(key=lambda x: x.get("event_date", ""))
    if anu:
        return anu[0].get("event_date")
    return None


def compute_onus_status(events: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Deriva status por onus_id a partir de property_events:
      - ONUS_REGISTRO -> registrado
      - ONUS_BAIXA    -> baixado
    """
    status: Dict[str, str] = {}
    # ordena por data para status final
    events_sorted = sorted(events, key=lambda e: sort_key_date_iso(e, "event_date"))
    for e in events_sorted:
        onus_id = e.get("onus_id")
        if not isinstance(onus_id, str) or not onus_id.strip():
            continue
        et = e.get("event_type")
        if et == "ONUS_REGISTRO":
            status[onus_id] = "registrado"
        elif et == "ONUS_BAIXA":
            status[onus_id] = "baixado"
    return status


def rank_match_level(level: Any) -> int:
    # A (melhor) -> 0, B -> 1, C -> 2, ...
    if not isinstance(level, str) or not level:
        return 9
    return max(0, ord(level.upper()[0]) - ord("A"))


def write_00_resumo(ds: Dataset, out_dir: Path, property_id: Optional[str]) -> None:
    pids = guess_property_ids(ds)
    if property_id:
        pids = [pid for pid in pids if pid == property_id]

    # contagem por tipo de evento
    evs = filter_by_property(ds.property_events, property_id)
    ev_type = Counter([e.get("event_type") for e in evs if isinstance(e.get("event_type"), str)])

    # datas min/max (event_date)
    dates: List[str] = []
    for e in evs:
        ed = e.get("event_date")
        if isinstance(ed, str) and is_iso_date(ed):
            dates.append(ed)

    date_min = min(dates) if dates else ""
    date_max = max(dates) if dates else ""


    content = []
    content.append("# 00 — Resumo de Execução (dataset_v1)\n")
    content.append(f"- Dataset: `{ds.dataset_dir}`\n")
    content.append(f"- Matrículas (property_id) encontradas: **{len(pids)}**\n")
    if pids:
        content.append("  - " + ", ".join(f"`{pid}`" for pid in pids) + "\n")
    if date_min and date_max:
        content.append(f"- Período (event_date): **{date_min} → {date_max}**\n")

    content.append("\n## Contagens (linhas por arquivo)\n")
    rows = []
    for fn in JSONL_FILES:
        rows.append([fn, len(read_jsonl(ds.dataset_dir / fn))])
    content.append(md_table(["Arquivo", "Linhas"], rows))

    content.append("\n## Tipos de eventos (property_events)\n")
    ev_rows = [[k, v] for k, v in ev_type.most_common()]
    content.append(md_table(["event_type", "qtde"], ev_rows))

    # pendências (se existirem)
    pend = filter_by_property(ds.pendencias, property_id)
    content.append("\n## Pendências (visão rápida)\n")
    content.append(f"- Total: **{len(pend)}**\n")
    if pend:
        sample = pend[:10]
        sample_rows = []
        for r in sample:
            sample_rows.append([
                r.get("tipo") or r.get("code") or r.get("kind") or "",
                r.get("mensagem") or r.get("message") or r.get("detail") or "",
                r.get("property_id") or "",
                r.get("source_doc_id") or r.get("doc_id") or "",
            ])
        content.append(md_table(["tipo", "mensagem", "property_id", "doc"], sample_rows))
        content.append("_Obs.: revisar `04_pendencias.md` para detalhe completo._\n")

    (out_dir / "00_resumo_exec.md").write_text("".join(content), encoding="utf-8")


def write_01_timeline(ds: Dataset, out_dir: Path, property_id: Optional[str]) -> None:
    pids = guess_property_ids(ds)
    if property_id:
        pids = [pid for pid in pids if pid == property_id]

    content = []
    content.append("# 01 — Timeline por matrícula (property_events)\n")
    content.append("Obs.: `event_date` segue a ordenação usada pelo reconciler.\n")
    content.append("Campos `data_registro` e `data_efetiva` são incluídos para auditoria (ex.: diferença entre data da operação e data do registro).\n")

    for pid in pids:
        events = [e for e in ds.property_events if e.get("property_id") == pid]
        events.sort(key=lambda e: sort_key_date_iso(e, "event_date"))

        anu_date = pick_first_anuencia_date(events)
        anu_dt = to_date(anu_date) if anu_date else None

        content.append(f"\n## {normalize_property_label(pid)} (`{pid}`)\n")
        if anu_date:
            content.append(f"- Anuência do banco detectada em: **{anu_date}**\n")

        rows = []
        for e in events:
            ed = e.get("event_date")
            flag_after_anu = ""
            if anu_dt is not None and isinstance(ed, str) and is_iso_date(ed):
                ed_dt = to_date(ed)
                if ed_dt is not None and ed_dt > anu_dt:
                    flag_after_anu = "pós-anuência"

            rows.append([
                ed or "",
                e.get("data_registro") or "",
                e.get("data_efetiva") or "",
                e.get("event_type") or "",
                e.get("registro_ref") or "",
                e.get("onus_id") or "",
                e.get("credor_id") or "",
                e.get("valor_divida_num") if e.get("valor_divida_num") is not None else "",
                flag_after_anu,
                e.get("delta_registro_efetiva_dias") if e.get("delta_registro_efetiva_dias") is not None else "",
                e.get("source_doc_id") or "",
            ])

        content.append(md_table(
            ["event_date", "data_registro", "data_efetiva", "event_type", "registro_ref", "onus_id", "credor_id", "valor_divida_num", "flag", "delta_registro_efetiva_dias", "source_doc_id"],
            rows
        ))

    (out_dir / "01_timeline_por_matricula.md").write_text("".join(content), encoding="utf-8")


def write_02_onus(ds: Dataset, out_dir: Path, property_id: Optional[str]) -> None:
    pids = guess_property_ids(ds)
    if property_id:
        pids = [pid for pid in pids if pid == property_id]

    content = []
    content.append("# 02 — Ônus por matrícula (derivado de property_events)\n")
    content.append("Este relatório deriva status de ônus a partir de `property_events.jsonl`.\n")
    content.append("Inclui `tipo_divida` (de `onus_obrigacoes.jsonl`) e classifica **restrições judiciais** (ex.: penhora/bloqueio) como *não relevantes* para a contagem principal.\n")

    # onus_id -> registro em onus_obrigacoes
    onus_meta: Dict[str, Dict[str, Any]] = {}
    for o in ds.onus_obrigacoes:
        oid = o.get("onus_id")
        if isinstance(oid, str) and oid:
            onus_meta[oid] = o

    def categoria_onus(tipo: str) -> str:
        t = (tipo or "").upper()
        if "PENHOR" in t or "BLOQUEIO" in t or "AÇÃO" in t or "ACAO" in t:
            return "RESTRICAO_JUDICIAL"
        return "ONUS_GARANTIA"

    for pid in pids:
        events = [e for e in ds.property_events if e.get("property_id") == pid]
        events.sort(key=lambda e: sort_key_date_iso(e, "event_date"))
        status = compute_onus_status(events)

        # último evento relevante por onus_id
        last: Dict[str, Dict[str, Any]] = {}
        for e in events:
            onus_id = e.get("onus_id")
            if not isinstance(onus_id, str) or not onus_id:
                continue
            if e.get("event_type") in ("ONUS_REGISTRO", "ONUS_BAIXA"):
                last[onus_id] = e

        rows: List[List[Any]] = []
        for onus_id, e in sorted(last.items(), key=lambda kv: sort_key_date_iso(kv[1], "event_date")):
            meta = onus_meta.get(onus_id) or {}
            tipo_divida = meta.get("tipo_divida") or ""
            cat = categoria_onus(str(tipo_divida))
            relevante = "SIM" if cat != "RESTRICAO_JUDICIAL" else "NAO"

            rows.append([
                onus_id,
                status.get(onus_id, ""),
                e.get("event_date") or "",
                e.get("data_registro") or meta.get("data_registro") or "",
                e.get("data_efetiva") or meta.get("data_efetiva") or "",
                e.get("event_type") or "",
                e.get("registro_ref") or "",
                str(tipo_divida),
                cat,
                relevante,
                e.get("credor_id") or "",
                e.get("valor_divida_num") if e.get("valor_divida_num") is not None else "",
                e.get("source_doc_id") or "",
            ])

        ativos_relevantes = sum(1 for r in rows if len(r) >= 10 and r[1] == "registrado" and r[9] == "SIM")

        content.append(f"\n## {normalize_property_label(pid)} (`{pid}`)\n")
        content.append(f"- Ônus distintos: **{len(rows)}**\n")
        content.append(f"- Ativos (registrados) relevantes ao caso: **{ativos_relevantes}**\n")
        content.append(md_table(
            ["onus_id", "status_evento", "data_evento", "data_registro", "data_efetiva", "tipo_evento", "registro_ref", "tipo_divida", "categoria", "relevante_caso", "credor_id", "valor_divida_num", "source_doc_id"],
            rows
        ))

    (out_dir / "02_onus_por_matricula.md").write_text("".join(content), encoding="utf-8")


def write_03_novacoes(ds: Dataset, out_dir: Path, property_id: Optional[str]) -> None:
    pids = guess_property_ids(ds)
    if property_id:
        pids = [pid for pid in pids if pid == property_id]

    content = []
    content.append("# 03 — Novações detectadas (novacoes_detectadas)\n")
    content.append("Ranking prioriza `match_level` (A melhor, depois B, C...).\n")

    novs_all = filter_by_property(ds.novacoes, property_id)
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for n in novs_all:
        pid = n.get("property_id")
        if isinstance(pid, str) and pid:
            grouped[pid].append(n)

    for pid in pids:
        novs = grouped.get(pid, [])
        novs.sort(key=lambda n: (rank_match_level(n.get("match_level")), n.get("janela_dias") or 9999))

        content.append(f"\n## {normalize_property_label(pid)} (`{pid}`)\n")
        content.append(f"- Candidatos: **{len(novs)}**\n")

        rows = []
        for n in novs:
            rows.append([
                n.get("novacao_id") or "",
                n.get("match_level") or "",
                n.get("janela_dias") or "",
                n.get("data_baixa") or "",
                n.get("onus_id_baixado") or "",
                n.get("data_nova_divida") or "",
                n.get("onus_id_novo") or "",
                n.get("match_basis") or "",
            ])

        content.append(md_table(
            ["novacao_id", "match_level", "janela_dias", "data_baixa", "onus_baixado", "data_nova", "onus_novo", "match_basis"],
            rows
        ))

        # evidências (top 5)
        if novs:
            content.append("\n### Evidências (top 5)\n")
            for n in novs[:5]:
                content.append(f"- **{n.get('novacao_id','')}** (`{n.get('match_level','')}` / {n.get('janela_dias','')} dias)\n")
                evid = n.get("evidencias")
                if isinstance(evid, list):
                    for ev in evid[:8]:
                        if isinstance(ev, dict):
                            content.append(
                                f"  - {md_escape(ev.get('tipo',''))} | "
                                f"{md_escape(ev.get('registro_ref',''))} | "
                                f"{md_escape(ev.get('event_date',''))} | "
                                f"{md_escape(ev.get('source_doc_id',''))}\n"
                            )
                content.append("\n")

    (out_dir / "03_novacoes.md").write_text("".join(content), encoding="utf-8")


def write_04_pendencias(ds: Dataset, out_dir: Path, property_id: Optional[str]) -> None:
    pend = filter_by_property(ds.pendencias, property_id)

    content: List[str] = []
    content.append("# 04 — Pendências (pendencias)\n")
    content.append(f"- Total: **{len(pend)}**\n\n")

    if not pend:
        content.append("_(sem dados)_\n")
        (out_dir / "04_pendencias.md").write_text("".join(content), encoding="utf-8")
        return

    # tenta agrupar por um campo comum (tipo/code/kind)
    def pend_type(r: Dict[str, Any]) -> str:
        return pend_group_key(r)

    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in pend:
        grouped[pend_type(r)].append(r)

    for k in sorted(grouped.keys()):
        content.append(f"## {k} ({len(grouped[k])})\n\n")

        rows: List[List[str]] = []
        for r in grouped[k]:
            rows.append([
                pend_msg(r),
                pend_property_id(r),
                pend_doc_id(r),
                pend_registro_ref(r),
            ])

        content.append(md_table(["mensagem", "property_id", "doc", "registro_ref"], rows))
        content.append("\n\n")  # separação visual entre tabelas

    (out_dir / "04_pendencias.md").write_text("".join(content), encoding="utf-8")


def write_index(out_dir: Path, property_id: Optional[str]) -> None:
    content = []
    content.append("# Relatório CAD-OBR — Reconciler (Markdown)\n\n")
    if property_id:
        content.append(f"- Filtro: `{property_id}`\n\n")
    content.append("- [00 — Resumo de Execução](00_resumo_exec.md)\n")
    content.append("- [01 — Timeline por matrícula](01_timeline_por_matricula.md)\n")
    content.append("- [02 — Ônus por matrícula](02_onus_por_matricula.md)\n")
    content.append("- [03 — Novações detectadas](03_novacoes.md)\n")
    content.append("- [04 — Pendências](04_pendencias.md)\n")
    (out_dir / "index.md").write_text("".join(content), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="report_md_cli.py",
        description="Gera relatórios Markdown a partir dos JSONL do dataset do reconciler.",
    )
    p.add_argument(
        "--dataset",
        required=True,
        help="Diretório do dataset (ex.: outputs/cad-obr/04_reconciler/dataset_v1)",
    )
    p.add_argument(
        "--output",
        required=True,
        help="Diretório de saída dos .md (ex.: outputs/cad-obr/04_reconciler/reports/dataset_v1)",
    )
    p.add_argument(
        "--property-id",
        default=None,
        help="Filtra para um property_id específico (ex.: matricula:7546).",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    dataset_dir = Path(args.dataset).resolve()
    out_dir = Path(args.output).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    ds = load_dataset(dataset_dir)

    write_index(out_dir, args.property_id)
    write_00_resumo(ds, out_dir, args.property_id)
    write_01_timeline(ds, out_dir, args.property_id)
    write_02_onus(ds, out_dir, args.property_id)
    write_03_novacoes(ds, out_dir, args.property_id)
    write_04_pendencias(ds, out_dir, args.property_id)

    print(f"OK: Relatórios gerados em: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
