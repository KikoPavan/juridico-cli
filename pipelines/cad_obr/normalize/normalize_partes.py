#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
pipelines/cad_obr/normalize/normalize_partes.py

Normalização determinística de PARTES para conciliação (Reconciler).

Objetivo:
- Construir chaves de match consistentes entre:
  - escritura_imovel
  - escritura_hipotecaria / contrato bancário / aditivos
  - contrato_social

O script:
1) Normaliza documentos (CPF/CNPJ/“documento”) para digits-only quando aplicável
2) Normaliza nomes (nome_norm) e cria IDs determinísticos:
   - cpf:<11d> | cnpj:<14d> | nome:<sha1_12>
3) Injeta IDs úteis no próprio JSON (sem apagar o texto original):
   - credor.id_parte / emitente_devedor.id_parte / interveniente_garante.id_parte
   - socios[*].id_parte / administradores[*].id_parte (com documento_norm)
   - hipotecas_onus[*].credor_id (quando credor é string)
   - transacoes_venda[*].compradores_ids / vendedores_ids
   - historico_titularidade[*].proprietarios_ids
   - transacoes_venda_posse[*].beneficiario_id
4) Escreve um resumo canônico em doc["_partes_meta"] com:
   - version
   - chaves_match
   - partes (lista detalhada)
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import unicodedata
from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


META_KEY = "_partes_meta"
META_VERSION = "cad-obr.normalize_partes.v1"


# ---------------------------------------------------------------------
# Normalização básica
# ---------------------------------------------------------------------

HONORIFICS_PREFIX = {
    "SR", "SRA", "SENHOR", "SENHORA", "DONA", "DON", "DR", "DRA", "DOUTOR", "DOUTORA",
}

SPLIT_PATTERNS_PRIMARY = [
    " E SUA MULHER",
    " E SEU MARIDO",
    " E SUA ESPOSA",
    " E SEU ESPOSO",
]



def digits_only(s: Any) -> str:
    if s is None:
        return ""
    return re.sub(r"\D+", "", str(s))


def remove_accents(s: str) -> str:
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def normalize_name_raw(name: str) -> str:
    """
    Normaliza para comparação:
    - trim, uppercase
    - remove acentos
    - colapsa espaços
    """
    s = normalize_whitespace(name)
    s = s.upper()
    s = remove_accents(s)

    # remove pontuação “leve” (mantém espaços)
    s = re.sub(r"[\"'`´^~]", "", s)
    s = re.sub(r"[()\[\]{}]", " ", s)
    s = re.sub(r"[.;:|/\\]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_name_primary(name: str) -> str:
    """
    Extrai um “nome primário” determinístico, útil para match quando o texto traz qualificadores:
    - corta em marcadores típicos de estado civil ("solteir", "casad", etc.)
    - corta em "E SUA MULHER"/"E SEU MARIDO"/etc.
    - remove honoríficos no início
    """
    s = normalize_name_raw(name)

    # remove honorífico no começo (se presente)
    parts = s.split(" ", 1)
    if parts and parts[0] in HONORIFICS_PREFIX:
        s = parts[1] if len(parts) > 1 else ""

    # corta por palavras típicas de qualificadores (determinístico)
    for marker in [" SOLTEIR", " CASAD", " VIU", " DIVORCIAD", " SEPARAD"]:
        idx = s.find(marker)
        if idx > 0:
            s = s[:idx].strip()
            break

    # corta por padrões “e sua mulher” etc.
    for pat in SPLIT_PATTERNS_PRIMARY:
        idx = s.find(pat)
        if idx > 0:
            s = s[:idx].strip()
            break

    return s


def party_id_from(name_primary: Optional[str], cpf: Optional[str], cnpj: Optional[str]) -> Optional[str]:
    cpf_d = digits_only(cpf) if cpf else ""
    cnpj_d = digits_only(cnpj) if cnpj else ""

    if cpf_d and len(cpf_d) == 11:
        return f"cpf:{cpf_d}"
    if cnpj_d and len(cnpj_d) == 14:
        return f"cnpj:{cnpj_d}"

    if name_primary:
        h = sha1(name_primary.encode("utf-8")).hexdigest()[:12]
        return f"nome:{h}"

    return None


def append_unique(lst: List[Any], value: Any) -> None:
    if value is None:
        return
    if value not in lst:
        lst.append(value)


# ---------------------------------------------------------------------
# Estruturas de saída (meta)
# ---------------------------------------------------------------------

@dataclass
class Stats:
    files_in: int = 0
    files_out: int = 0
    parties_found: int = 0
    ids_written: int = 0
    docs_normalized: int = 0


def add_party(
    meta: Dict[str, Any],
    role: str,
    nome: Optional[str],
    cpf: Optional[str] = None,
    cnpj: Optional[str] = None,
    source_path: Optional[str] = None,
    ancora: Optional[str] = None,
) -> Optional[str]:
    nome = (nome or "").strip() if isinstance(nome, str) else ""
    nome_primary = normalize_name_primary(nome) if nome else ""
    pid = party_id_from(nome_primary or None, cpf, cnpj)

    record = {
        "id": pid,
        "role": role,
        "nome": nome or None,
        "nome_norm": nome_primary or None,
        "cpf": digits_only(cpf) if cpf else None,
        "cnpj": digits_only(cnpj) if cnpj else None,
        "source_path": source_path,
        "ancora": ancora,
    }

    meta["partes"].append(record)
    append_unique(meta["chaves_match"].setdefault(f"{role}_ids", []), pid)
    return pid


# ---------------------------------------------------------------------
# Normalização por estrutura conhecida
# ---------------------------------------------------------------------

def get_fonte_ancora(party_obj: Dict[str, Any]) -> Optional[str]:
    fonte = party_obj.get("fonte")
    if isinstance(fonte, dict):
        anc = fonte.get("ancora")
        if isinstance(anc, str) and anc.strip():
            return anc.strip()
    return None


def normalize_party_object(party_obj: Dict[str, Any], role: str, meta: Dict[str, Any], source_path: str) -> Optional[str]:
    """
    party_obj esperado: {"nome":..., "cpf"/"cnpj":..., "fonte": {"ancora":...}, ...}
    Injeta party_obj["id_parte"] e normaliza cpf/cnpj para digits-only quando existirem.
    """
    if not isinstance(party_obj, dict):
        return None

    nome = party_obj.get("nome")
    cpf = party_obj.get("cpf") if isinstance(party_obj.get("cpf"), str) else None
    cnpj = party_obj.get("cnpj") if isinstance(party_obj.get("cnpj"), str) else None

    # normaliza cpf/cnpj in-place
    if cpf:
        party_obj["cpf"] = digits_only(cpf)
        cpf = party_obj["cpf"]
    if cnpj:
        party_obj["cnpj"] = digits_only(cnpj)
        cnpj = party_obj["cnpj"]

    ancora = get_fonte_ancora(party_obj)

    pid = add_party(meta, role=role, nome=nome, cpf=cpf, cnpj=cnpj, source_path=source_path, ancora=ancora)
    if pid:
        party_obj["id_parte"] = pid
    return pid


def normalize_named_list_strings(names: Any, role: str, meta: Dict[str, Any], source_path: str) -> List[str]:
    """
    names: lista de strings
    retorna lista de ids (na mesma ordem, sem None)
    """
    ids: List[str] = []
    if isinstance(names, list):
        for i, n in enumerate(names):
            if isinstance(n, str) and n.strip():
                pid = add_party(meta, role=role, nome=n, source_path=f"{source_path}[{i}]")
                if pid:
                    ids.append(pid)
    return ids


def normalize_socios(doc: Dict[str, Any], meta: Dict[str, Any]) -> None:
    socios = doc.get("socios")
    if not isinstance(socios, list):
        return

    ids: List[str] = []
    for i, s in enumerate(socios):
        if not isinstance(s, dict):
            continue
        nome = s.get("nome") if isinstance(s.get("nome"), str) else None
        tipo_raw = s.get("tipo_documento")
        tipo = tipo_raw.strip() if isinstance(tipo_raw, str) else ""
        tipo_u = tipo.upper() if tipo else ""

        documento_raw = s.get("documento")
        doc_digits = digits_only(documento_raw)

        if doc_digits:
            s["documento_norm"] = doc_digits

        cpf = doc_digits if tipo_u == "CPF" else None
        cnpj = doc_digits if tipo_u == "CNPJ" else None

        anc = s.get("ancora_qualificacao")
        anc = anc.strip() if isinstance(anc, str) and anc.strip() else None

        pid = add_party(meta, role="socio", nome=nome, cpf=cpf, cnpj=cnpj, source_path=f"socios[{i}]", ancora=anc)
        if pid:
            s["id_parte"] = pid
            ids.append(pid)

    meta["chaves_match"]["socios_ids"] = ids


def normalize_administradores(doc: Dict[str, Any], meta: Dict[str, Any]) -> None:
    admins = doc.get("administradores")
    if not isinstance(admins, list):
        return

    ids: List[str] = []
    for i, a in enumerate(admins):
        if not isinstance(a, dict):
            continue
        nome = a.get("nome") if isinstance(a.get("nome"), str) else None
        documento_raw = a.get("documento")
        doc_digits = digits_only(documento_raw)


        if doc_digits:
            a["documento_norm"] = doc_digits

        # regra determinística: 11 dígitos -> cpf, 14 -> cnpj
        cpf = doc_digits if len(doc_digits) == 11 else None
        cnpj = doc_digits if len(doc_digits) == 14 else None

        anc = a.get("ancora_clausula")
        anc = anc.strip() if isinstance(anc, str) and anc.strip() else None

        pid = add_party(meta, role="administrador", nome=nome, cpf=cpf, cnpj=cnpj, source_path=f"administradores[{i}]", ancora=anc)
        if pid:
            a["id_parte"] = pid
            ids.append(pid)

    meta["chaves_match"]["administradores_ids"] = ids


def normalize_empresa_contrato_social(doc: Dict[str, Any], meta: Dict[str, Any]) -> None:
    razao = doc.get("razao_social") if isinstance(doc.get("razao_social"), str) else None
    cnpj = doc.get("cnpj") if isinstance(doc.get("cnpj"), str) else None

    if cnpj:
        doc["cnpj"] = digits_only(cnpj)
        cnpj = doc["cnpj"]

    if razao or cnpj:
        pid = add_party(meta, role="empresa", nome=razao, cnpj=cnpj, source_path="(root)")
        if pid:
            meta["chaves_match"]["empresa_id"] = pid


def normalize_escritura_hipotecaria(doc: Dict[str, Any], meta: Dict[str, Any]) -> None:
    if isinstance(doc.get("credor"), dict):
        pid = normalize_party_object(doc["credor"], "credor", meta, "credor")
        if pid:
            meta["chaves_match"]["credor_id"] = pid

    if isinstance(doc.get("emitente_devedor"), dict):
        pid = normalize_party_object(doc["emitente_devedor"], "emitente_devedor", meta, "emitente_devedor")
        if pid:
            meta["chaves_match"]["emitente_devedor_id"] = pid

        reps = doc["emitente_devedor"].get("representantes")
        if isinstance(reps, list):
            rep_ids: List[str] = []
            for i, r in enumerate(reps):
                if isinstance(r, dict) and isinstance(r.get("nome"), str) and r["nome"].strip():
                    pidr = add_party(meta, role="representante_emitente_devedor", nome=r["nome"], source_path=f"emitente_devedor.representantes[{i}]")
                    if pidr:
                        r["id_parte"] = pidr
                        rep_ids.append(pidr)
            meta["chaves_match"]["representantes_emitente_devedor_ids"] = rep_ids

    if isinstance(doc.get("interveniente_garante"), dict):
        pid = normalize_party_object(doc["interveniente_garante"], "interveniente_garante", meta, "interveniente_garante")
        if pid:
            meta["chaves_match"]["interveniente_garante_id"] = pid

        reps = doc["interveniente_garante"].get("representantes")
        if isinstance(reps, list):
            rep_ids: List[str] = []
            for i, r in enumerate(reps):
                if isinstance(r, dict) and isinstance(r.get("nome"), str) and r["nome"].strip():
                    pidr = add_party(meta, role="representante_interveniente_garante", nome=r["nome"], source_path=f"interveniente_garante.representantes[{i}]")
                    if pidr:
                        r["id_parte"] = pidr
                        rep_ids.append(pidr)

                    proc = r.get("procurador")
                    if isinstance(proc, dict) and isinstance(proc.get("nome"), str) and proc["nome"].strip():
                        pidp = add_party(meta, role="procurador_interveniente_garante", nome=proc["nome"], source_path=f"interveniente_garante.representantes[{i}].procurador")
                        if pidp:
                            proc["id_parte"] = pidp
            meta["chaves_match"]["representantes_interveniente_garante_ids"] = rep_ids


def normalize_escritura_imovel(doc: Dict[str, Any], meta: Dict[str, Any]) -> None:
    onus = doc.get("hipotecas_onus")
    credor_ids_all: List[str] = []
    if isinstance(onus, list):
        for i, it in enumerate(onus):
            if not isinstance(it, dict):
                continue
            c = it.get("credor")
            if isinstance(c, str) and c.strip():
                pid = add_party(meta, role="credor_onus", nome=c, source_path=f"hipotecas_onus[{i}].credor")
                if pid:
                    it["credor_id"] = pid
                    append_unique(credor_ids_all, pid)
            elif isinstance(c, dict):
                pid = normalize_party_object(c, "credor_onus", meta, f"hipotecas_onus[{i}].credor")
                if pid:
                    it["credor_id"] = pid
                    append_unique(credor_ids_all, pid)
    if credor_ids_all:
        meta["chaves_match"]["credores_onus_ids"] = credor_ids_all

    tv = doc.get("transacoes_venda")
    if isinstance(tv, list):
        compradores_all: List[str] = []
        vendedores_all: List[str] = []
        for i, it in enumerate(tv):
            if not isinstance(it, dict):
                continue
            comp_ids = normalize_named_list_strings(it.get("compradores"), "comprador", meta, f"transacoes_venda[{i}].compradores")
            vend_ids = normalize_named_list_strings(it.get("vendedores"), "vendedor", meta, f"transacoes_venda[{i}].vendedores")

            if comp_ids:
                it["compradores_ids"] = comp_ids
                for pid in comp_ids:
                    append_unique(compradores_all, pid)
            if vend_ids:
                it["vendedores_ids"] = vend_ids
                for pid in vend_ids:
                    append_unique(vendedores_all, pid)

        if compradores_all:
            meta["chaves_match"]["compradores_ids"] = compradores_all
        if vendedores_all:
            meta["chaves_match"]["vendedores_ids"] = vendedores_all

    hist = doc.get("historico_titularidade")
    if isinstance(hist, list):
        proprietarios_all: List[str] = []
        for i, it in enumerate(hist):
            if not isinstance(it, dict):
                continue
            prop_ids = normalize_named_list_strings(it.get("proprietarios"), "proprietario", meta, f"historico_titularidade[{i}].proprietarios")
            if prop_ids:
                it["proprietarios_ids"] = prop_ids
                for pid in prop_ids:
                    append_unique(proprietarios_all, pid)
        if proprietarios_all:
            meta["chaves_match"]["proprietarios_ids"] = proprietarios_all

    posse = doc.get("transacoes_venda_posse")
    if isinstance(posse, list):
        ben_all: List[str] = []
        for i, it in enumerate(posse):
            if not isinstance(it, dict):
                continue
            b = it.get("beneficiario")
            if isinstance(b, str) and b.strip():
                pid = add_party(meta, role="beneficiario_posse", nome=b, source_path=f"transacoes_venda_posse[{i}].beneficiario")
                if pid:
                    it["beneficiario_id"] = pid
                    append_unique(ben_all, pid)
        if ben_all:
            meta["chaves_match"]["beneficiarios_posse_ids"] = ben_all


def normalize_document(doc: Dict[str, Any]) -> Tuple[Dict[str, Any], Stats]:
    stats = Stats(docs_normalized=1)

    meta: Dict[str, Any] = {
        "version": META_VERSION,
        "chaves_match": {},
        "partes": [],
    }

    # contrato social
    if "socios" in doc or "administradores" in doc or ("razao_social" in doc and "cnpj" in doc):
        normalize_empresa_contrato_social(doc, meta)
        normalize_socios(doc, meta)
        normalize_administradores(doc, meta)

    # escritura hipotecária / contrato bancário
    if any(k in doc for k in ("credor", "emitente_devedor", "interveniente_garante")):
        normalize_escritura_hipotecaria(doc, meta)

    # escritura imóvel
    if any(k in doc for k in ("hipotecas_onus", "transacoes_venda", "historico_titularidade", "transacoes_venda_posse")):
        normalize_escritura_imovel(doc, meta)

    stats.parties_found = len(meta["partes"])
    stats.ids_written = sum(1 for p in meta["partes"] if p.get("id"))

    doc[META_KEY] = meta
    return doc, stats


# ---------------------------------------------------------------------
# IO e CLI
# ---------------------------------------------------------------------

def iter_input_files(input_path: Path, pattern: str) -> List[Path]:
    if input_path.is_file():
        return [input_path]
    return sorted(input_path.rglob(pattern))


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Normalize partes (IDs + chaves_match) para conciliação CAD-OBR.")
    ap.add_argument("--input", required=True, help="Arquivo .json ou diretório de entrada")
    ap.add_argument("--output", required=True, help="Arquivo .json ou diretório de saída")
    ap.add_argument("--pattern", default="*.json", help="Glob quando --input é diretório. Default: *.json")
    ap.add_argument("--inplace", action="store_true", help="Permite sobrescrever input==output (usa tmp + move).")
    args = ap.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)

    if not in_path.exists():
        raise SystemExit(f"ERRO: input não existe: {in_path}")

    in_files = iter_input_files(in_path, args.pattern)
    stats_total = Stats(files_in=len(in_files), files_out=0, parties_found=0, ids_written=0, docs_normalized=0)

    if not args.inplace:
        try:
            if in_path.resolve() == out_path.resolve():
                raise SystemExit("ERRO: input e output são o mesmo caminho. Use --inplace.")
        except Exception:
            pass

    for src in in_files:
        doc = load_json(src)
        doc_norm, st = normalize_document(doc)

        if in_path.is_file():
            dst = out_path
        else:
            rel = src.relative_to(in_path)
            dst = out_path / rel

        if args.inplace:
            tmp = dst.with_suffix(dst.suffix + ".tmp")
            save_json(tmp, doc_norm)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(tmp), str(dst))
        else:
            save_json(dst, doc_norm)

        stats_total.files_out += 1
        stats_total.parties_found += st.parties_found
        stats_total.ids_written += st.ids_written
        stats_total.docs_normalized += st.docs_normalized

    print("OK normalize_partes")
    print(f"- arquivos_in:      {stats_total.files_in}")
    print(f"- arquivos_out:     {stats_total.files_out}")
    print(f"- docs_processados: {stats_total.docs_normalized}")
    print(f"- partes_encontradas_total: {stats_total.parties_found}")
    print(f"- ids_gerados_total:        {stats_total.ids_written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
