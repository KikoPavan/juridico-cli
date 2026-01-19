# pipelines/cad_obr/reconciler/reconciler_core.py
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# -----------------------------
# Utilitários determinísticos
# -----------------------------

_PT_MONTHS = {
    "janeiro": 1,
    "fevereiro": 2,
    "marco": 3,
    "março": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}


def sha1_12(s: str) -> str:
    h = hashlib.sha1(s.encode("utf-8")).hexdigest()
    return h[:12]


def digits_only(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    d = re.sub(r"\D+", "", s)
    return d or None


def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def normalize_name(s: str) -> str:
    s = normalize_ws(s)
    # mantém acentuação (para auditoria), mas remove excesso
    return s


def party_id_from_any(party: Any) -> Optional[str]:
    """
    Gera PartyId determinístico:
      - cpf:<11d>
      - cnpj:<14d>
      - nome:<sha12>
    Aceita dict (com cpf/cnpj/nome) ou string (nome).
    """
    if party is None:
        return None

    if isinstance(party, dict):
        cpf = digits_only(str(party.get("cpf") or ""))
        if cpf and len(cpf) == 11:
            return f"cpf:{cpf}"
        cnpj = digits_only(str(party.get("cnpj") or ""))
        if cnpj and len(cnpj) == 14:
            return f"cnpj:{cnpj}"
        nome = (
            party.get("nome")
            or party.get("razao_social")
            or party.get("denominacao")
            or ""
        )
        nome = str(nome).strip()
        if nome:
            return f"nome:{sha1_12(normalize_name(nome).lower())}"
        return None

    if isinstance(party, str):
        nome = party.strip()
        if nome:
            return f"nome:{sha1_12(normalize_name(nome).lower())}"
        return None

    return None


def property_id_from_matricula(matricula: Optional[str]) -> Optional[str]:
    d = digits_only(matricula)
    if not d:
        return None
    return f"matricula:{d}"


def registro_ref_norm(reg: Optional[str]) -> Optional[str]:
    if not reg:
        return None
    reg = normalize_ws(str(reg)).upper()
    # Normaliza "AV." vs "Av."
    reg = reg.replace("AV.", "AV.").replace("R.", "R.")
    # aceita "R.5", "AV.24", etc
    return reg


def onus_id(property_id: str, registro_ref: str) -> str:
    return f"{property_id}#{registro_ref}"


def is_iso_date(s: str) -> bool:
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", s))


def parse_date_to_iso(raw: Optional[str]) -> Optional[str]:
    """
    Converte:
      - YYYY-MM-DD
      - dd/mm/yyyy
      - "24 de Abril de 1.991"
      - "10 de fevereiro de 2.001"
    em YYYY-MM-DD.
    """
    if not raw:
        return None
    s = normalize_ws(str(raw))
    if not s:
        return None

    if is_iso_date(s):
        return s

    # dd/mm/yyyy
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})$", s)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), m.group(3)
        y = int(re.sub(r"\D", "", y))
        if y < 100:
            y += 1900
        try:
            return date(y, mo, d).isoformat()
        except ValueError:
            return None

    # "24 de Abril de 1.991" / "10 de fevereiro de 2.001"
    m = re.search(
        r"(\d{1,2})\s+de\s+([A-Za-zçÇáéíóúÁÉÍÓÚãõÃÕ]+)\s+de\s+([\d\.]{2,6})",
        s,
        re.IGNORECASE,
    )
    if m:
        d = int(m.group(1))
        mes_txt = m.group(2).lower()
        mes_txt = mes_txt.replace("ç", "c")
        y_txt = re.sub(r"\D", "", m.group(3))
        if not y_txt:
            return None
        y = int(y_txt)
        # "1991" pode vir como "1.991" => 1991 já ok
        if y < 100:
            y += 1900
        mo = _PT_MONTHS.get(mes_txt)
        if not mo:
            return None
        try:
            return date(y, mo, d).isoformat()
        except ValueError:
            return None

    return None


def extract_first_date_from_text(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    s = str(raw)
    # tenta ISO
    m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", s)
    if m:
        return m.group(1)
    # tenta dd/mm/yyyy
    m = re.search(r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b", s)
    if m:
        return parse_date_to_iso(m.group(1))
    # tenta "dd de mês de yyyy"
    return parse_date_to_iso(s)


def parse_brl_to_centavos(raw: Optional[str]) -> Optional[int]:
    """
    Extrai o primeiro valor monetário da string.
    Aceita:
      - "R$60.000,00-(...)" -> 6000000
      - "CR$15.276.818,18" -> 1527681818
      - "93354.27"         -> 9335427
      - "600000"           -> 60000000
    Retorna None se não achar número.
    """
    if not raw:
        return None
    s = str(raw)

    # 1) padrão BR: 1.234,56 ou 123,45
    m = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2})", s)
    if m:
        num = m.group(1)
        num = num.replace(".", "").replace(",", ".")
        try:
            val = float(num)
            return int(round(val * 100))
        except ValueError:
            return None

    # 2) padrão US: 1234.56 (sem milhares)
    m = re.search(r"(\d+\.\d{2})", s)
    if m:
        try:
            val = float(m.group(1))
            return int(round(val * 100))
        except ValueError:
            return None

    # 3) inteiro puro
    m = re.search(r"\b(\d+)\b", s)
    if m:
        try:
            val = int(m.group(1))
            return val * 100
        except ValueError:
            return None

    return None


def format_centavos_to_brl(centavos: int) -> str:
    """
    555521 -> "5.555,21"
    """
    if centavos < 0:
        centavos = abs(centavos)
    inteiro = centavos // 100
    frac = centavos % 100
    s_int = f"{inteiro:,}".replace(",", ".")
    return f"{s_int},{frac:02d}"


def anchor_from_obj(obj: Any) -> Optional[Dict[str, Any]]:
    """
    Converte estruturas comuns de fonte (arquivo_md/ancora/fls etc) em AnchorRef.
    """
    if not isinstance(obj, dict):
        return None

    arquivo = obj.get("arquivo_md") or obj.get("arquivo") or obj.get("source_path")
    ancora = obj.get("ancora") or obj.get("anchor")
    trecho = obj.get("trecho")

    if not arquivo:
        return None

    out: Dict[str, Any] = {"source_path": str(arquivo)}
    if ancora:
        out["ancora"] = str(ancora)
    if trecho:
        out["trecho"] = str(trecho)[:500]
    return out


# -----------------------------
# Modelos
# -----------------------------


@dataclass
class LoadedDoc:
    stage: str  # "02_normalize" | "03_monetary"
    path: Path
    data: Dict[str, Any]


@dataclass
class ReconcilerInputs:
    normalize_root: Path
    monetary_root: Path
    pattern: str = "*.json"


@dataclass
class ReconcilerOutputs:
    output_root: Path  # outputs/cad_obr/04_reconciler
    dataset_dirname: str = "dataset_v1"


# -----------------------------
# Detecção de tipo de documento
# -----------------------------


def detect_doc_tipo(doc: Dict[str, Any], fallback_folder: Optional[str] = None) -> str:
    # 1) pelo campo explícito
    tipo_raw = str(doc.get("tipo_documento") or "").upper()

    if "ADITIV" in tipo_raw:
        return "ADITIVO"
    if (
        "CONTRAT" in tipo_raw
        or "CÉDULA" in tipo_raw
        or "CEDULA" in tipo_raw
        or "CRÉDITO" in tipo_raw
        or "CREDITO" in tipo_raw
    ):
        return "CONTRATO_BANCARIO"
    if "ESCRITURA" in tipo_raw and "HIPOT" in tipo_raw:
        return "ESCRITURA_HIPOTECARIA"

    # 2) por estrutura
    if "hipotecas_onus" in doc and "matricula" in doc:
        return "ESCRITURA_IMOVEL"
    if "divida_confessada" in doc and "garantias" in doc:
        # pode ser escritura_hipotecaria ou contrato bancário (sem tipo_documento preenchido)
        if fallback_folder and "hipotec" in fallback_folder.lower():
            # ainda assim pode conter contrato bancário; decide pelo conteúdo de operacao_original
            op = ((doc.get("divida_confessada") or {}).get("operacao_original")) or {}
            if isinstance(op, dict) and op.get("numero"):
                return "CONTRATO_BANCARIO"
        return "ESCRITURA_HIPOTECARIA"
    if "empresa" in doc or "razao_social" in doc or "quadro_socios" in doc:
        return "CONTRATO_SOCIAL"

    # 3) fallback por pasta
    if fallback_folder:
        ff = fallback_folder.lower()
        if "contrato_social" in ff:
            return "CONTRATO_SOCIAL"
        if "escritura_imovel" in ff:
            return "ESCRITURA_IMOVEL"
        if "escritura_hipotecaria" in ff:
            return "ESCRITURA_HIPOTECARIA"

    return "OUTRO"


def doc_id_for(stage: str, tipo: str, path: Path) -> str:
    key = f"{stage}|{tipo}|{str(path)}"
    return f"doc_{sha1_12(key)}"


# -----------------------------
# Scanner / Loader
# -----------------------------


def scan_json_files(root: Path, pattern: str) -> List[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob(pattern))


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_inputs(inputs: ReconcilerInputs) -> Tuple[List[LoadedDoc], List[LoadedDoc]]:
    norm_docs: List[LoadedDoc] = []
    mon_docs: List[LoadedDoc] = []

    for p in scan_json_files(inputs.normalize_root, inputs.pattern):
        try:
            norm_docs.append(LoadedDoc(stage="02_normalize", path=p, data=load_json(p)))
        except Exception:
            # deixa para pendências no reconciler
            continue

    for p in scan_json_files(inputs.monetary_root, inputs.pattern):
        try:
            mon_docs.append(LoadedDoc(stage="03_monetary", path=p, data=load_json(p)))
        except Exception:
            continue

    return norm_docs, mon_docs


# -----------------------------
# Construção do dataset (camadas)
# -----------------------------


class CadObrReconciler:
    def __init__(self, inputs: ReconcilerInputs, outputs: ReconcilerOutputs):
        self.inputs = inputs
        self.outputs = outputs

        self.norm_docs: List[LoadedDoc] = []
        self.mon_docs: List[LoadedDoc] = []

        # índices
        self.docs_catalog: List[Dict[str, Any]] = []
        self.partes_map: Dict[str, Dict[str, Any]] = {}
        self.imoveis_map: Dict[str, Dict[str, Any]] = {}
        self.operacoes_map: Dict[str, Dict[str, Any]] = {}
        self.onus_list: List[Dict[str, Any]] = []
        self.events_list: List[Dict[str, Any]] = []
        self.links_list: List[Dict[str, Any]] = []
        self.pendencias_list: List[Dict[str, Any]] = []
        self.novacoes_list: List[Dict[str, Any]] = []

        # mapeamentos para merge com monetary
        self.mon_by_matricula: Dict[str, LoadedDoc] = {}
        self.mon_by_operation: Dict[str, LoadedDoc] = {}

    # ---------
    # Layer A: catálogo + índices base
    # ---------

    def layer_a_load_and_index(self) -> None:
        self.norm_docs, self.mon_docs = load_inputs(self.inputs)
        self._index_monetary_docs()

        for ld in self.norm_docs:
            folder = ld.path.parent.name
            tipo = detect_doc_tipo(ld.data, fallback_folder=folder)
            did = doc_id_for(ld.stage, tipo, ld.path)

            # Indexa documento
            doc_item: Dict[str, Any] = {
                "doc_id": did,
                "tipo_documento": tipo,
                "source_path": str(ld.path),
                "origin_stage": ld.stage,
            }

            # tenta extrair operation_id
            op_id = self._extract_operation_id(ld.data)
            if op_id:
                doc_item["operation_id"] = op_id

            # property_ids
            prop_ids = self._extract_property_ids(ld.data)
            if prop_ids:
                doc_item["property_ids"] = prop_ids

            # party_ids
            party_ids = self._extract_party_ids(ld.data)
            if party_ids:
                doc_item["party_ids"] = party_ids

            # datas (quando existirem)
            datas: Dict[str, Any] = {}
            for k in ["data_assinatura", "data_registro", "data_efetiva"]:
                v = ld.data.get(k)
                iso = parse_date_to_iso(v) if isinstance(v, str) else None
                if iso:
                    datas[k] = iso
            if datas:
                doc_item["datas"] = datas

            anchors: List[Dict[str, Any]] = []
            fonte = ld.data.get("fonte_documento_geral")
            a = anchor_from_obj(fonte) if fonte else None
            if a:
                anchors.append(a)
            if anchors:
                doc_item["anchors"] = anchors

            self.docs_catalog.append(doc_item)

            # alimenta índices de partes/imóveis/operacoes
            self._index_partes_from_doc(ld.data, did)
            self._index_imoveis_from_doc(ld.data, did)
            self._index_operacoes_from_doc(ld.data, did)

    def _index_monetary_docs(self) -> None:
        """
        Indexa docs do stage 03 para permitir merge determinístico por:
          - matrícula
          - operation_id
        """
        for ld in self.mon_docs:
            data = ld.data
            folder = ld.path.parent.name
            tipo = detect_doc_tipo(data, fallback_folder=folder)

            # matrícula
            if tipo == "ESCRITURA_IMOVEL":
                mat = digits_only(str(data.get("matricula") or ""))
                if mat:
                    self.mon_by_matricula[mat] = ld

            # operation_id
            op_id = self._extract_operation_id(data)
            if op_id:
                self.mon_by_operation[op_id] = ld

    def _extract_property_ids(self, doc: Dict[str, Any]) -> List[str]:
        out: List[str] = []

        # escritura_imovel
        mat = doc.get("matricula")
        pid = property_id_from_matricula(str(mat)) if mat else None
        if pid:
            out.append(pid)

        # garantias (contratos)
        g = doc.get("garantias")
        if isinstance(g, list):
            for it in g:
                if isinstance(it, dict):
                    m = it.get("matricula")
                    pid2 = property_id_from_matricula(str(m)) if m else None
                    if pid2:
                        out.append(pid2)

        # dedup
        return sorted(list({x for x in out if x}))

    def _extract_party_ids(self, doc: Dict[str, Any]) -> List[str]:
        out: List[str] = []

        # campos comuns
        for key in ["credor", "emitente_devedor", "interveniente_garante"]:
            v = doc.get(key)
            pid = party_id_from_any(v)
            if pid:
                out.append(pid)

        # transações (escritura_imovel)
        tv = doc.get("transacoes_venda")
        if isinstance(tv, list):
            for t in tv:
                if isinstance(t, dict):
                    for role_key in ["vendedores", "compradores"]:
                        ppl = t.get(role_key)
                        if isinstance(ppl, list):
                            for name in ppl:
                                pid = party_id_from_any(name)
                                if pid:
                                    out.append(pid)

        return sorted(list({x for x in out if x}))

    def _extract_operation_id(self, doc: Dict[str, Any]) -> Optional[str]:
        # 1) já digits-only
        cand = (
            doc.get("numero_documento")
            or doc.get("numero_contrato")
            or doc.get("operation_id")
        )
        if isinstance(cand, str):
            d = digits_only(cand)
            if d:
                return d

        # 2) contrato: divida_confessada.operacao_original.numero
        dc = doc.get("divida_confessada")
        if isinstance(dc, dict):
            op = dc.get("operacao_original")
            if isinstance(op, dict):
                num = op.get("numero")
                d = digits_only(str(num)) if num else None
                if d:
                    return d

        return None

    def _index_partes_from_doc(self, doc: Dict[str, Any], doc_id: str) -> None:
        def upsert_party(p: Any, role: str) -> None:
            pid = party_id_from_any(p)
            if not pid:
                return
            cur = self.partes_map.get(pid)
            if not cur:
                cur = {"party_id": pid, "roles": [], "docs_origem": [], "anchors": []}
                self.partes_map[pid] = cur

            if role not in cur["roles"]:
                cur["roles"].append(role)
            if doc_id not in cur["docs_origem"]:
                cur["docs_origem"].append(doc_id)

            # nome/cpf/cnpj se disponíveis
            if isinstance(p, dict):
                if "nome" in p and p.get("nome"):
                    cur["nome"] = str(p.get("nome"))
                    cur["nome_norm"] = normalize_name(str(p.get("nome")))
                cpf = digits_only(str(p.get("cpf") or ""))
                if cpf and len(cpf) == 11:
                    cur["cpf"] = cpf
                cnpj = digits_only(str(p.get("cnpj") or ""))
                if cnpj and len(cnpj) == 14:
                    cur["cnpj"] = cnpj

                fonte = p.get("fonte")
                a = anchor_from_obj(fonte) if fonte else None
                if a:
                    cur["anchors"].append(a)

        # partes principais
        if "credor" in doc:
            upsert_party(doc.get("credor"), "credor")
        if "emitente_devedor" in doc:
            upsert_party(doc.get("emitente_devedor"), "emitente_devedor")
        if "interveniente_garante" in doc:
            upsert_party(doc.get("interveniente_garante"), "garante")

        # escritura_imovel: transações
        tv = doc.get("transacoes_venda")
        if isinstance(tv, list):
            for t in tv:
                if not isinstance(t, dict):
                    continue
                for n in t.get("vendedores") or []:
                    upsert_party(n, "vendedor")
                for n in t.get("compradores") or []:
                    upsert_party(n, "comprador")

        # escritura_imovel: hipotecas_onus credor string
        onus = doc.get("hipotecas_onus")
        if isinstance(onus, list):
            for o in onus:
                if isinstance(o, dict):
                    if o.get("credor"):
                        upsert_party(o.get("credor"), "credor")

    def _index_imoveis_from_doc(self, doc: Dict[str, Any], doc_id: str) -> None:
        mat = doc.get("matricula")
        pid = property_id_from_matricula(str(mat)) if mat else None
        if pid:
            cur = self.imoveis_map.get(pid)
            if not cur:
                cur = {
                    "property_id": pid,
                    "matricula": digits_only(str(mat)) or str(mat),
                    "docs_origem": [],
                    "anchors": [],
                }
                self.imoveis_map[pid] = cur
            if doc_id not in cur["docs_origem"]:
                cur["docs_origem"].append(doc_id)

        # garantias (contratos)
        g = doc.get("garantias")
        if isinstance(g, list):
            for it in g:
                if not isinstance(it, dict):
                    continue
                m = it.get("matricula")
                pid2 = property_id_from_matricula(str(m)) if m else None
                if not pid2:
                    continue
                cur2 = self.imoveis_map.get(pid2)
                if not cur2:
                    cur2 = {
                        "property_id": pid2,
                        "matricula": digits_only(str(m)) or str(m),
                        "docs_origem": [],
                        "anchors": [],
                    }
                    self.imoveis_map[pid2] = cur2
                if doc_id not in cur2["docs_origem"]:
                    cur2["docs_origem"].append(doc_id)

                fonte = it.get("fonte")
                a = anchor_from_obj(fonte) if fonte else None
                if a:
                    cur2["anchors"].append(a)

    def _index_operacoes_from_doc(self, doc: Dict[str, Any], doc_id: str) -> None:
        op_id = self._extract_operation_id(doc)
        if not op_id:
            # ainda assim pode haver uma lista de numero_documento em contrato hipotecário
            nums = doc.get("numero_documento")
            if isinstance(nums, list):
                for n in nums:
                    d = digits_only(str(n))
                    if d:
                        self._upsert_operacao(d, doc, doc_id)
            return
        self._upsert_operacao(op_id, doc, doc_id)

    def _upsert_operacao(self, op_id: str, doc: Dict[str, Any], doc_id: str) -> None:
        cur = self.operacoes_map.get(op_id)
        if not cur:
            cur = {
                "operation_id": op_id,
                "tipo_operacao": "",
                "docs_origem": [],
                "anchors": [],
                "property_ids": [],
            }
            self.operacoes_map[op_id] = cur

        if doc_id not in cur["docs_origem"]:
            cur["docs_origem"].append(doc_id)

        tipo_oper = ""
        # tenta pelo operacao_original.tipo
        dc = doc.get("divida_confessada")
        if isinstance(dc, dict):
            op = dc.get("operacao_original")
            if isinstance(op, dict) and op.get("tipo"):
                tipo_oper = str(op.get("tipo"))
            # taxa/TR
            enc = dc.get("encargos_financeiros")
            if isinstance(enc, str) and "TR" in enc.upper():
                cur["menciona_TR"] = True

            # datas
            for k_src, k_dst in [
                ("data_celebracao", "data_celebracao"),
                ("vencimento", "vencimento"),
            ]:
                if isinstance(op, dict) and op.get(k_src):
                    iso = parse_date_to_iso(str(op.get(k_src)))
                    if iso:
                        cur[k_dst] = iso

            if dc.get("data_posicao"):
                iso = parse_date_to_iso(str(dc.get("data_posicao")))
                if iso:
                    cur["data_posicao"] = iso

        if not tipo_oper and doc.get("tipo_documento"):
            tipo_oper = str(doc.get("tipo_documento"))
        if not tipo_oper:
            tipo_oper = "OPERACAO"
        cur["tipo_operacao"] = tipo_oper

        # parties
        cred = party_id_from_any(doc.get("credor"))
        dev = party_id_from_any(doc.get("emitente_devedor"))
        gar = party_id_from_any(doc.get("interveniente_garante"))
        if cred:
            cur["credor_id"] = cred
        if dev:
            cur["emitente_devedor_id"] = dev
        if gar:
            cur["garante_id"] = gar

        # valores (base/presente)
        dc = doc.get("divida_confessada")
        if isinstance(dc, dict):
            v = dc.get("valor") or (
                dc.get("valor_principal_original")
                if isinstance(dc.get("valor_principal_original"), str)
                else None
            )
            if isinstance(v, str):
                cent = parse_brl_to_centavos(v)
                if cent is not None:
                    cur["valor_base_num"] = cent
                    cur["valor_base"] = format_centavos_to_brl(cent)

        # property_ids (garantias)
        props = self._extract_property_ids(doc)
        for p in props:
            if p not in cur["property_ids"]:
                cur["property_ids"].append(p)

        # anchors
        fonte = doc.get("fonte_documento_geral")
        a = anchor_from_obj(fonte) if fonte else None
        if a:
            cur["anchors"].append(a)

    # ---------
    # Layer B: onus_obrigacoes (consolidado)
    # ---------

    def layer_b_build_onus_obrigacoes(self) -> None:
        # base: escritura_imovel no normalize
        for ld in self.norm_docs:
            tipo = detect_doc_tipo(ld.data, fallback_folder=ld.path.parent.name)
            if tipo != "ESCRITURA_IMOVEL":
                continue

            mat = digits_only(str(ld.data.get("matricula") or ""))
            pid = property_id_from_matricula(str(ld.data.get("matricula") or ""))
            if not pid or not mat:
                continue

            did = doc_id_for(ld.stage, tipo, ld.path)

            # tenta merge com monetary (mesma matrícula)
            mon = self.mon_by_matricula.get(mat)
            mon_onus_by_reg: Dict[str, Dict[str, Any]] = {}
            if mon and isinstance(mon.data.get("hipotecas_onus"), list):
                for o in mon.data["hipotecas_onus"]:
                    if isinstance(o, dict) and o.get("registro_ou_averbacao"):
                        rr = registro_ref_norm(str(o.get("registro_ou_averbacao")))
                        if rr:
                            mon_onus_by_reg[rr] = o

            for o in ld.data.get("hipotecas_onus") or []:
                if not isinstance(o, dict):
                    continue

                rr = registro_ref_norm(str(o.get("registro_ou_averbacao") or ""))
                if not rr:
                    continue

                oid = onus_id(pid, rr)

                # dates
                d_ef = parse_date_to_iso(o.get("data_efetiva")) or None
                d_rg = parse_date_to_iso(o.get("data_registro")) or None
                d_bx = parse_date_to_iso(o.get("data_baixa")) or None
                venc = parse_date_to_iso(o.get("vencimento")) or None

                # status determinístico (regra registral):
                # - BAIXADA: há baixa explícita (data_baixa / averbação de baixa / cancelada=True)
                # - ATIVA: não há baixa explícita (independe de vencimento; ônus pode permanecer vigente mesmo vencido)
                cancelada = o.get("cancelada")
                averb_baixa = o.get("averbacao_baixa")
                if d_bx or averb_baixa or cancelada is True:
                    status = "BAIXADA"
                else:
                    # Por padrão, considera ATIVA quando existe registro e não há baixa/cancelamento.
                    # Isso evita classificar como "INDETERMINADA" ônus que, pela ausência de baixa, permanecem vigentes.
                    status = "ATIVA"

                inicio = d_ef or d_rg
                fim = d_bx or venc or None

                if not inicio:
                    # pendência: sem data para timeline
                    self._pendencia(
                        entity_type="ONUS",
                        entity_id=oid,
                        motivo="dados_insuficientes: janela_vigencia_inicio ausente (sem data_efetiva e sem data_registro)",
                        evidencias=[{"source_path": str(ld.path)}],
                        campos_faltantes=["data_efetiva", "data_registro"],
                    )
                    continue

                # valores (base)
                val_orig = o.get("valor_divida_original")
                val_str = o.get("valor_divida")

                val_num = o.get("valor_divida_num")
                if not isinstance(val_num, int):
                    val_num = parse_brl_to_centavos(val_str) or parse_brl_to_centavos(
                        val_orig
                    )

                # merge monetary por registro (valor_presente, meta)
                valor_presente_num: Optional[int] = None
                valor_presente_str: Optional[str] = None
                monetary_meta: Optional[Dict[str, Any]] = None
                if rr in mon_onus_by_reg:
                    mo = mon_onus_by_reg[rr]
                    vp_num = mo.get("valor_presente_num")
                    if isinstance(vp_num, int):
                        valor_presente_num = vp_num
                        valor_presente_str = format_centavos_to_brl(vp_num)
                    vp = mo.get("valor_presente")
                    if isinstance(vp, str):
                        valor_presente_num = (
                            parse_brl_to_centavos(vp)
                            if valor_presente_num is None
                            else valor_presente_num
                        )
                        valor_presente_str = (
                            vp if valor_presente_str is None else valor_presente_str
                        )
                    mm = mo.get("_monetary_meta")
                    if isinstance(mm, dict):
                        monetary_meta = mm

                cred_id = party_id_from_any(o.get("credor"))
                dev_id = party_id_from_any(
                    o.get("emitente_devedor")
                ) or party_id_from_any(ld.data.get("emitente_devedor"))

                item: Dict[str, Any] = {
                    "onus_id": oid,
                    "property_id": pid,
                    "registro_ref": rr,
                    "tipo_divida": str(o.get("tipo_divida") or "").strip() or "DIVIDA",
                    "operation_id": digits_only(str(o.get("numero_contrato") or ""))
                    if o.get("numero_contrato")
                    else None,
                    "credor_id": cred_id,
                    "emitente_devedor_id": dev_id,
                    "data_efetiva": d_ef,
                    "data_registro": d_rg,
                    "vencimento": venc,
                    "data_baixa": d_bx,
                    "status": status,
                    "janela_vigencia_inicio": inicio,
                    "janela_vigencia_fim": fim,
                    "valor_divida_original": str(val_orig)
                    if val_orig is not None
                    else None,
                    "valor_divida": format_centavos_to_brl(val_num)
                    if isinstance(val_num, int)
                    else (str(val_str) if isinstance(val_str, str) else None),
                    "valor_divida_num": val_num if isinstance(val_num, int) else None,
                    "valor_presente": valor_presente_str,
                    "valor_presente_num": valor_presente_num,
                    "monetary_meta": monetary_meta,
                    "docs_origem": [did],
                    "anchors": [{"source_path": str(ld.path)}],
                }

                self.onus_list.append(item)

    # ---------
    # Layer C: property_events (timeline)
    # ---------

    def layer_c_build_property_events(self) -> None:
        # 1) eventos de ônus (registro e baixa)
        for o in self.onus_list:
            pid = o["property_id"]
            did = (o.get("docs_origem") or [""])[0]

            # ONUS_REGISTRO
            # Para ordenação jurídica e detecção de eventos, prioriza data_registro; mantém data_efetiva no payload para auditoria.
            ev_reg_date = (
                o.get("data_registro")
                or o.get("data_efetiva")
                or o.get("janela_vigencia_inicio")
            )
            if ev_reg_date:
                ev: Dict[str, Any] = {
                    "event_id": f"evt_{sha1_12(o['onus_id'] + '|REG')}",
                    "property_id": pid,
                    "event_type": "ONUS_REGISTRO",
                    "event_date": ev_reg_date,
                    "data_registro": o.get("data_registro"),
                    "data_efetiva": o.get("data_efetiva"),
                    "onus_id": o["onus_id"],
                    "operation_id": o.get("operation_id"),
                    "registro_ref": o.get("registro_ref"),
                    "credor_id": o.get("credor_id"),
                    "emitente_devedor_id": o.get("emitente_devedor_id"),
                    "valor_divida_num": o.get("valor_divida_num"),
                    "valor_presente_num": o.get("valor_presente_num"),
                    "source_doc_id": did,
                    "anchors": o.get("anchors") or [],
                }

                # flag registro_posterior
                d_rg = o.get("data_registro")
                d_ef = o.get("data_efetiva")
                if (
                    isinstance(d_rg, str)
                    and isinstance(d_ef, str)
                    and is_iso_date(d_rg)
                    and is_iso_date(d_ef)
                ):
                    try:
                        dr = datetime.strptime(d_rg, "%Y-%m-%d").date()
                        de = datetime.strptime(d_ef, "%Y-%m-%d").date()
                        if dr > de:
                            ev["flag_registro_posterior"] = True
                            ev["delta_registro_efetiva_dias"] = (dr - de).days
                    except Exception:
                        pass

                self.events_list.append(ev)

            # ONUS_BAIXA
            if o.get("status") == "BAIXADA":
                db = o.get("data_baixa")
                if db:
                    evb: Dict[str, Any] = {
                        "event_id": f"evt_{sha1_12(o['onus_id'] + '|BAIXA')}",
                        "property_id": pid,
                        "event_type": "ONUS_BAIXA",
                        "event_date": db,
                        "data_baixa": db,
                        "data_registro": o.get("data_registro"),
                        "data_efetiva": o.get("data_efetiva"),
                        "onus_id": o["onus_id"],
                        "operation_id": o.get("operation_id"),
                        "registro_ref": o.get("registro_ref"),
                        "credor_id": o.get("credor_id"),
                        "emitente_devedor_id": o.get("emitente_devedor_id"),
                        "source_doc_id": did,
                        "anchors": o.get("anchors") or [],
                    }
                    self.events_list.append(evb)

        # 2) eventos de venda / anuência (da escritura_imovel)
        for ld in self.norm_docs:
            tipo = detect_doc_tipo(ld.data, fallback_folder=ld.path.parent.name)
            if tipo != "ESCRITURA_IMOVEL":
                continue
            did = doc_id_for(ld.stage, tipo, ld.path)
            pid = property_id_from_matricula(str(ld.data.get("matricula") or ""))
            if not pid:
                continue

            tv = ld.data.get("transacoes_venda")
            if not isinstance(tv, list):
                continue

            for t in tv:
                if not isinstance(t, dict):
                    continue

                # VENDA
                d_ev = parse_date_to_iso(t.get("data_efetiva")) or parse_date_to_iso(
                    t.get("data_registro")
                )
                if d_ev:
                    evv: Dict[str, Any] = {
                        "event_id": f"evt_{sha1_12(pid + '|VENDA|' + (t.get('registro') or t.get('tipo_transacao') or ''))}",
                        "property_id": pid,
                        "event_type": "VENDA",
                        "event_date": d_ev,
                        "data_registro": parse_date_to_iso(t.get("data_registro")),
                        "data_efetiva": parse_date_to_iso(t.get("data_efetiva")),
                        "registro_ref": registro_ref_norm(t.get("registro"))
                        if t.get("registro")
                        else None,
                        "source_doc_id": did,
                        "anchors": [{"source_path": str(ld.path)}],
                        "notes": normalize_ws(str(t.get("tipo_transacao") or ""))[:2000]
                        if t.get("tipo_transacao")
                        else None,
                    }
                    self.events_list.append(evv)

                # ANUÊNCIA (se existir string)
                anu = t.get("anuencia_credor")
                if isinstance(anu, str) and anu.strip():
                    d_an = extract_first_date_from_text(anu)
                    if d_an:
                        eva: Dict[str, Any] = {
                            "event_id": f"evt_{sha1_12(pid + '|ANUENCIA|' + d_an)}",
                            "property_id": pid,
                            "event_type": "ANUENCIA_BANCO",
                            "event_date": d_an,
                            "source_doc_id": did,
                            "anchors": [{"source_path": str(ld.path)}],
                            "notes": normalize_ws(anu)[:2000],
                        }
                        self.events_list.append(eva)
                    else:
                        self._pendencia(
                            entity_type="EVENT",
                            entity_id=f"{pid}|ANUENCIA",
                            motivo="anuencia_detectada_sem_data_parseavel",
                            evidencias=[
                                {"source_path": str(ld.path), "trecho": anu[:200]}
                            ],
                        )

    # ---------
    # Layer D: links + pendencias (mínimo determinístico)
    # ---------

    def layer_d_build_links_and_pendencias(self) -> None:
        # links simples: operação -> matrículas (garantias), operação -> partes
        for op_id, op in self.operacoes_map.items():
            # operação -> property
            for pid in op.get("property_ids") or []:
                self.links_list.append(
                    {
                        "link_id": f"lnk_{sha1_12(op_id + '|' + pid)}",
                        "from_type": "OPERATION",
                        "from_id": op_id,
                        "to_type": "PROPERTY",
                        "to_id": pid,
                        "match_level": "A",
                        "match_reason": "operacao_original.numero vincula garantia (matricula) no documento",
                        "evidencias": op.get("anchors") or [{"source_path": "unknown"}],
                    }
                )

            # operação -> partes
            for role_key in ["credor_id", "emitente_devedor_id", "garante_id"]:
                if op.get(role_key):
                    pid = op[role_key]
                    self.links_list.append(
                        {
                            "link_id": f"lnk_{sha1_12(op_id + '|' + pid + '|' + role_key)}",
                            "from_type": "OPERATION",
                            "from_id": op_id,
                            "to_type": "PARTY",
                            "to_id": pid,
                            "match_level": "B",
                            "match_reason": f"parte vinculada à operação via campo {role_key}",
                            "evidencias": op.get("anchors")
                            or [{"source_path": "unknown"}],
                        }
                    )
        # pendências: status_indeterminado removida (status passa a ser determinístico ATIVA/BAIXADA)

    # ---------
    # Layer E: novações (baixa -> nova dívida na mesma matrícula)
    # ---------

    def layer_e_build_novacoes(self, janela_dias_max: int = 180) -> None:
        # monta eventos por property
        by_prop: Dict[str, List[Dict[str, Any]]] = {}
        for ev in self.events_list:
            if ev.get("property_id") and ev.get("event_date"):
                by_prop.setdefault(ev["property_id"], []).append(ev)

        def to_dt(s: Any) -> Optional[date]:
            if not isinstance(s, str):
                return None

            s = s.strip()
            if not s or not is_iso_date(s):
                return None
            try:
                return datetime.strptime(s, "%Y-%m-%d").date()
            except Exception:
                return None

        # index de onus por id (para bases de match)
        onus_by_id: Dict[str, Dict[str, Any]] = {
            o["onus_id"]: o for o in self.onus_list
        }

        def _tipo_upper(on: Dict[str, Any]) -> str:
            return str(on.get("tipo_divida") or "").strip().upper()

        def _novacao_elegivel(on: Dict[str, Any]) -> bool:
            """Evita falsos positivos de novação para obrigações que não representam 'troca de dívida'.

            Regras:
            - ARRENDAMENTO MERCANTIL: pagamento parcelado mensal; baixa não deve ser tratada como novação.
            - PENHORA / BLOQUEIO: são restrições judiciais, não nova dívida.
            """
            t = _tipo_upper(on)
            if not t:
                return True
            if "ARRENDAMENTO" in t:
                return False
            if "PENHORA" in t:
                return False
            if "BLOQUEIO" in t:
                return False
            return True

        for pid, evs in by_prop.items():
            evs_sorted = sorted(evs, key=lambda x: x.get("event_date") or "")
            for i, ev in enumerate(evs_sorted):
                if ev.get("event_type") != "ONUS_BAIXA":
                    continue
                db = to_dt(ev.get("event_date"))
                if not db or not ev.get("onus_id"):
                    continue

                # procura próximo ONUS_REGISTRO na janela
                for j in range(i + 1, len(evs_sorted)):
                    ev2 = evs_sorted[j]
                    if ev2.get("event_type") != "ONUS_REGISTRO":
                        continue
                    dn = to_dt(ev2.get("event_date"))
                    if not dn:
                        continue
                    delta = (dn - db).days
                    if delta < 0:
                        continue
                    if delta > janela_dias_max:
                        break

                    o1 = onus_by_id.get(ev["onus_id"])
                    o2 = onus_by_id.get(ev2.get("onus_id") or "")
                    if not o1 or not o2:
                        continue

                    # ARR. MERCANTIL e restrições judiciais não são elegíveis para novação automática.
                    if not _novacao_elegivel(o1) or not _novacao_elegivel(o2):
                        continue

                    basis: List[str] = ["JANELA_TEMPO"]
                    level = "C"

                    if o1.get("credor_id") and o1.get("credor_id") == o2.get(
                        "credor_id"
                    ):
                        basis.append("CREDOR")
                        level = "B"
                    if o1.get("emitente_devedor_id") and o1.get(
                        "emitente_devedor_id"
                    ) == o2.get("emitente_devedor_id"):
                        basis.append("DEVEDOR")
                        level = "B"
                    if o1.get("operation_id") and o1.get("operation_id") == o2.get(
                        "operation_id"
                    ):
                        basis.append("OPERACAO")
                        level = "A"

                    nov = {
                        "novacao_id": f"nov_{sha1_12(ev['onus_id'] + '|' + (ev2.get('onus_id') or '') + '|' + str(delta))}",
                        "property_id": pid,
                        "onus_id_baixado": ev["onus_id"],
                        "data_baixa": ev.get("event_date"),
                        "onus_id_novo": ev2.get("onus_id"),
                        "data_nova_divida": ev2.get("event_date"),
                        "match_basis": basis,
                        "match_level": level,
                        "janela_dias": delta,
                        "evidencias": (o1.get("anchors") or [])
                        + (o2.get("anchors") or []),
                    }
                    self.novacoes_list.append(nov)

                    # uma baixa pode ter múltiplas candidatas; mantém todas
                    # (se quiser, pode limitar a melhor por A>B>C depois)

    # -----------------------------
    # Escrita do dataset
    # -----------------------------

    def write_dataset(self) -> Path:
        out_dir = self.outputs.output_root / self.outputs.dataset_dirname
        out_dir.mkdir(parents=True, exist_ok=True)

        self._write_jsonl(out_dir / "documentos.jsonl", self.docs_catalog)
        self._write_jsonl(out_dir / "partes.jsonl", list(self.partes_map.values()))
        self._write_jsonl(out_dir / "imoveis.jsonl", list(self.imoveis_map.values()))
        self._write_jsonl(
            out_dir / "contratos_operacoes.jsonl", list(self.operacoes_map.values())
        )
        self._write_jsonl(out_dir / "onus_obrigacoes.jsonl", self.onus_list)
        self._write_jsonl(out_dir / "property_events.jsonl", self.events_list)
        self._write_jsonl(out_dir / "links.jsonl", self.links_list)
        self._write_jsonl(out_dir / "pendencias.jsonl", self.pendencias_list)
        self._write_jsonl(out_dir / "novacoes_detectadas.jsonl", self.novacoes_list)

        return out_dir

    def _write_jsonl(self, path: Path, rows: List[Dict[str, Any]]) -> None:
        with path.open("w", encoding="utf-8") as f:
            for r in rows:
                # remove chaves None para reduzir ruído
                clean = {k: v for k, v in r.items() if v is not None}
                f.write(json.dumps(clean, ensure_ascii=False) + "\n")

    # -----------------------------
    # Pendências helper
    # -----------------------------

    def _pendencia(
        self,
        entity_type: str,
        entity_id: str,
        motivo: str,
        evidencias: List[Dict[str, Any]],
        campos_faltantes: Optional[List[str]] = None,
        candidatos: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        item: Dict[str, Any] = {
            "pendencia_id": f"pend_{sha1_12(entity_type + '|' + entity_id + '|' + motivo)}",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "motivo": motivo,
            "evidencias": evidencias,
        }
        if campos_faltantes:
            item["campos_faltantes"] = campos_faltantes
        if candidatos:
            item["candidatos"] = candidatos
        self.pendencias_list.append(item)

    # -----------------------------
    # Runner (todas as camadas)
    # -----------------------------

    def run_all_layers(self) -> Path:
        self.layer_a_load_and_index()
        self.layer_b_build_onus_obrigacoes()
        self.layer_c_build_property_events()
        self.layer_d_build_links_and_pendencias()
        self.layer_e_build_novacoes()
        return self.write_dataset()


def run_reconciler(
    normalize_root: str,
    monetary_root: str,
    output_root: str,
    dataset_dirname: str = "dataset_v1",
    pattern: str = "*.json",
) -> Path:
    """
    Função utilitária para ser chamada pelo CLI.
    """
    inputs = ReconcilerInputs(
        normalize_root=Path(normalize_root),
        monetary_root=Path(monetary_root),
        pattern=pattern,
    )
    outputs = ReconcilerOutputs(
        output_root=Path(output_root),
        dataset_dirname=dataset_dirname,
    )
    recon = CadObrReconciler(inputs, outputs)
    return recon.run_all_layers()
