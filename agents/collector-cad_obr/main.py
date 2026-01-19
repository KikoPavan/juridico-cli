import glob
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple
from datetime import date
import unicodedata
import yaml
from dotenv import load_dotenv  # <--- ADICIONAR ESTA LINHA

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()  # <--- ADICIONAR ESTA LINHA

# --- IMPORTAÇÃO DA NOVA SDK DO GOOGLE ---
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("ERRO CRÍTICO: Biblioteca 'google-genai' não instalada.")
    print("Execute: pip install google-genai")
    exit(1)

# --- UTILS BÁSICAS ---


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config não encontrado em: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def read_file(path: str) -> str:
    if not os.path.exists(path):
        return f"[ERRO] Arquivo não encontrado: {path}"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def save_json(data: Any, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def extract_json_from_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("```json", "").replace("```", "").strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        return match.group(1)
    return text


# --- POST-PROCESSING (LÓGICA DE ADITIVOS E BAIXAS) ---


def parse_monetary_value(val_str: str):
    """
    Estilo parse_valor_brl (monetary_core):
    - Extrai o PRIMEIRO valor no padrão pt-BR (ex.: 93.354,27 ou 93354,27)
    - Ignora o restante do texto (ex.: "-(noventa e três mil, ...)")
    - Retorna None se não encontrar valor (não retorna 0.0)
    """
    if not val_str:
        return None

    s = str(val_str)

    # Primeiro valor pt-BR com vírgula decimal (com ou sem milhar)
    m = re.search(r"(\d{1,3}(?:\.\d{3})+,\d{2}|\d+,\d{2})", s)
    if not m:
        return None

    num_str = m.group(1)
    try:
        return float(num_str.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def format_currency(val_float: float) -> str:
    """
    Formata um float para string monetária com vírgula decimal e ponto de milhar.
    Ex.: 93354.27 -> "93.354,27"
    """
    s = f"{val_float:,.2f}"  # "93,354.27"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# =========================
# Histórico de titularidade (ESCRITURA_IMOVEL): rebuild determinístico por datas
# =========================

_PT_MONTHS = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "março": 3, "abril": 4, "maio": 5, "junho": 6,
    "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}

_DATE_RE = re.compile(
    r"(\d{1,2})\s+de\s+([A-Za-z\u00C0-\u017F]+)\s+de\s+(\d{1,4}(?:\.\d{3})?)",
    flags=re.IGNORECASE
)

def _norm_txt(s: str) -> str:
    s = (s or "").strip().lower()
    s = unicodedata.normalize("NFD", s)
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")

def parse_date_ptbr(value: Any) -> Optional[date]:
    """Converte '14 de Março de 2.001' -> date(2001, 3, 14). Retorna None se não parseável."""
    if not isinstance(value, str):
        return None
    m = _DATE_RE.search(value)
    if not m:
        return None
    dd = int(m.group(1))
    mm_name = _norm_txt(m.group(2))
    yyyy_raw = m.group(3).replace(".", "")
    if not yyyy_raw.isdigit():
        return None
    yyyy = int(yyyy_raw)
    mm = _PT_MONTHS.get(mm_name)
    if not mm:
        return None
    try:
        return date(yyyy, mm, dd)
    except ValueError:
        return None



def corrigir_historico_titularidade_por_transacoes_venda(data: Dict[str, Any]) -> Dict[str, Any]:
    """Corrige limites (inicio/fim/consolidacao) do historico_titularidade usando transacoes_venda como fonte de verdade.

    Caso-alvo (recorrente): o LLM inicia o período no registro de "consolidação" (ex.: R.48) e ignora o
    registro anterior que já transfere a posse/titularidade (ex.: R.46 com retrovenda e anuência do banco).
    Aqui, o início do período do comprador passa a ser o primeiro registro onde ele aparece como COMPRADOR,
    e o registro definitivo passa a ser tratado como consolidação.
    """
    periods = data.get("historico_titularidade")
    tv = data.get("transacoes_venda")

    if not isinstance(periods, list) or not periods:
        return data
    if not isinstance(tv, list) or not tv:
        return data

    def norm_name(s: str) -> str:
        return _norm_txt(s).upper()

    # Normaliza transações por data efetiva (fallback: data_registro)
    txs: List[Dict[str, Any]] = []
    for t in tv:
        if not isinstance(t, dict):
            continue

        reg = t.get("registro") or t.get("registro_ou_averbacao")
        if not reg:
            continue

        d_eff = parse_date_ptbr(t.get("data_efetiva") or t.get("data_registro"))
        if not d_eff:
            continue

        compradores = t.get("compradores") or []
        comp_names = []
        for c in compradores:
            if isinstance(c, str) and c.strip():
                comp_names.append(c.split(",")[0].strip())

        comp_key = tuple(sorted({norm_name(n) for n in comp_names if n}))

        txs.append(
            {
                "reg": reg,
                "date": d_eff,
                "raw": t,
                "comp_names": comp_names,
                "comp_key": comp_key,
            }
        )

    if not txs:
        return data

    txs.sort(key=lambda x: (x["date"], x["reg"]))

    # Agrupa por segmentos: mudança de comprador abre novo período; registros "definitivos" entram como consolidação.
    segments: List[Dict[str, Any]] = []
    cur = None

    for tx in txs:
        if cur is None:
            cur = {
                "start_tx": tx,
                "end_tx": None,  # primeiro registro do próximo comprador
                "comp_key": tx["comp_key"],
                "comp_names": tx["comp_names"],
                "consolidations": [],
            }
            continue

        if tx["comp_key"] == cur["comp_key"]:
            tipo = (tx["raw"].get("tipo_transacao") or "").upper()
            if tx["raw"].get("consolida_titularidade") is True or "DEFINITIVA" in tipo:
                cur["consolidations"].append(tx)
        else:
            cur["end_tx"] = tx
            segments.append(cur)
            cur = {
                "start_tx": tx,
                "end_tx": None,
                "comp_key": tx["comp_key"],
                "comp_names": tx["comp_names"],
                "consolidations": [],
            }

    if cur is not None:
        segments.append(cur)

    # Datas de início dos períodos (para achar o período anterior correto)
    period_starts: List[Tuple[int, date]] = []
    for i, p in enumerate(periods):
        d = parse_date_ptbr(p.get("data_inicio"))
        if d:
            period_starts.append((i, d))
    period_starts.sort(key=lambda x: x[1])

    def find_period_by_primary_name(primary: str) -> Optional[int]:
        if not primary:
            return None
        prim = norm_name(primary)
        for i, p in enumerate(periods):
            props = p.get("proprietarios") or []
            for prop in props:
                if isinstance(prop, str) and prim in norm_name(prop):
                    return i
        return None

    def find_prev_period_idx(start_d: date, exclude_idx: int) -> Optional[int]:
        prev = None
        for i, d in period_starts:
            if i == exclude_idx:
                continue
            if d < start_d:
                prev = i
        return prev

    for seg in segments:
        start_tx = seg["start_tx"]
        end_tx = seg.get("end_tx")

        primary = seg["comp_names"][0] if seg["comp_names"] else ""
        idx_p = find_period_by_primary_name(primary)
        if idx_p is None:
            continue

        p = periods[idx_p]
        start_raw = start_tx["raw"]

        # Início do período = primeiro registro onde aparece como COMPRADOR (data_efetiva)
        p["registro_inicio"] = start_tx["reg"]
        p["data_inicio"] = start_raw.get("data_efetiva") or start_raw.get("data_registro")

        # Consolidação = compra definitiva (se houver dentro do mesmo comprador)
        if seg["consolidations"]:
            cons = sorted(seg["consolidations"], key=lambda x: (x["date"], x["reg"]))[0]
            cons_raw = cons["raw"]
            p["registro_consolidacao"] = cons["reg"]
            p["data_consolidacao"] = cons_raw.get("data_efetiva") or cons_raw.get("data_registro")
        else:
            if p.get("registro_consolidacao") == p.get("registro_inicio"):
                p["registro_consolidacao"] = None
                p["data_consolidacao"] = None

        # Fim do período = início do próximo comprador (quando existir)
        if end_tx is not None:
            end_raw = end_tx["raw"]
            p["registro_fim"] = end_tx["reg"]
            p["data_fim"] = end_raw.get("data_efetiva") or end_raw.get("data_registro")

        # Ajusta o período anterior para terminar exatamente no início deste
        prev_idx = find_prev_period_idx(start_tx["date"], idx_p)
        if prev_idx is not None:
            prev_p = periods[prev_idx]
            prev_p["registro_fim"] = start_tx["reg"]
            prev_p["data_fim"] = start_raw.get("data_efetiva") or start_raw.get("data_registro")

    return data

def _normalize_period_chain(periods: List[Dict[str, Any]]) -> None:
    """
    Garante coerência do encadeamento registral:
    - registro_inicio do período i deve ser o registro_fim do período i-1.
    Isso evita começar o período no registro de compra 'definitiva' (ex.: R.48) quando o correto,
    para marco temporal do período, é o registro anterior com efeito (ex.: R.46).
    """
    for i in range(1, len(periods)):
        prev = periods[i - 1]
        cur = periods[i]

        prev_fim_reg = prev.get("registro_fim")
        prev_fim_dt = prev.get("data_fim")
        cur_ini_reg = cur.get("registro_inicio")
        cur_ini_dt = cur.get("data_inicio")

        if not prev_fim_reg or not prev_fim_dt:
            continue

        prev_end = parse_date_ptbr(prev_fim_dt)
        cur_start = parse_date_ptbr(cur_ini_dt)

        # Se o período atual não começa no registro_fim anterior e sua data de início é posterior,
        # forçamos o encadeamento e preservamos o início anterior como 'consolidação' (se aplicável).
        if cur_ini_reg != prev_fim_reg and prev_end and (cur_start is None or cur_start > prev_end):
            if not cur.get("registro_consolidacao") and cur_ini_reg:
                cur["registro_consolidacao"] = cur_ini_reg
                cur["data_consolidacao"] = cur_ini_dt
            cur["registro_inicio"] = prev_fim_reg
            cur["data_inicio"] = prev_fim_dt

def _build_period_ranges(periods: List[Dict[str, Any]]) -> Dict[int, Tuple[date, Optional[date]]]:
    """Ranges semi-abertos: [data_inicio, proxima_data_inicio)."""
    starts: List[Tuple[int, date]] = []
    for i, p in enumerate(periods):
        d = parse_date_ptbr(p.get("data_inicio"))
        if not d:
            return {}
        starts.append((i, d))

    starts.sort(key=lambda x: x[1])
    ranges: Dict[int, Tuple[date, Optional[date]]] = {}
    for pos, (idx, dstart) in enumerate(starts):
        dend = starts[pos + 1][1] if pos + 1 < len(starts) else None
        ranges[idx] = (dstart, dend)
    return ranges

def _find_period_for(d: date, ranges: Dict[int, Tuple[date, Optional[date]]]) -> Optional[int]:
    chosen: Optional[int] = None
    for idx, (st, en) in ranges.items():
        if d < st:
            continue
        if en is None or d < en:
            if chosen is None or st > ranges[chosen][0]:
                chosen = idx
    return chosen

def rebuild_registros_periodo_escritura_imovel(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reconstrói historico_titularidade[].registros_periodo por datas, de forma determinística.

    Regras:
    - marco temporal:
      - registro normal: data_efetiva (se existir), senão data_registro
      - BAIXA: usar averbacao_baixa com marco = data_baixa (data efetiva da baixa)
    - Inclui também registros de consolidação (ex.: R.48) quando existirem no período.
    """
    periods = data.get("historico_titularidade")
    if not isinstance(periods, list) or not periods:
        return data

    _normalize_period_chain(periods)
    ranges = _build_period_ranges(periods)
    if not ranges:
        return data

    events: Dict[str, date] = {}

    def add_event(eid: Optional[str], dt: Any) -> None:
        if not eid:
            return
        d = parse_date_ptbr(dt)
        if not d:
            return
        prev = events.get(eid)
        if prev is None or d < prev:
            events[eid] = d

    # Períodos (início/consolidação/fim)
    for p in periods:
        add_event(p.get("registro_inicio"), p.get("data_inicio"))
        add_event(p.get("registro_consolidacao"), p.get("data_consolidacao"))
        add_event(p.get("registro_fim"), p.get("data_fim"))

    # Transações/posse (se existirem)
    for t in (data.get("transacoes_venda_posse") or []):
        if isinstance(t, dict):
            add_event(t.get("registro_ou_averbacao"), t.get("data_efetiva") or t.get("data_registro"))

    # Ônus/hipotecas: inclui registro do ônus, aditivos e principalmente BAIXA (averbacao_baixa pela data_baixa)
    for h in (data.get("hipotecas_onus") or []):
        if not isinstance(h, dict):
            continue
        add_event(h.get("registro_ou_averbacao"), h.get("data_efetiva") or h.get("data_registro"))

        for ad in (h.get("historico_aditivos") or []):
            if isinstance(ad, dict):
                add_event(ad.get("averbacao"), ad.get("data"))

        av_baixa = h.get("averbacao_baixa")
        dt_baixa = h.get("data_baixa")
        if av_baixa and dt_baixa:
            add_event(av_baixa, dt_baixa)

    # Reconstrução do zero
    original_lists = [list(p.get("registros_periodo") or []) for p in periods]
    for p in periods:
        p["registros_periodo"] = []

    assigned: Dict[str, int] = {}
    for eid, d in events.items():
        pid = _find_period_for(d, ranges)
        if pid is not None:
            assigned[eid] = pid

    per_sets: List[Dict[str, None]] = [dict() for _ in periods]
    for eid, pid in assigned.items():
        per_sets[pid][eid] = None

    # Preservar itens sem data que já existiam (não-datáveis), sem duplicar
    for i, orig in enumerate(original_lists):
        for eid in orig:
            if not eid:
                continue
            if eid in events or eid in assigned:
                continue
            per_sets[i][eid] = None

    # Ordenar: datáveis por data; não-datáveis por ordem original
    for i, p in enumerate(periods):
        datados: List[Tuple[date, str]] = []
        sem_data: List[str] = []

        for eid in per_sets[i].keys():
            d = events.get(eid)
            if d:
                datados.append((d, eid))
            else:
                sem_data.append(eid)

        datados.sort(key=lambda x: (x[0], x[1]))
        orig_pos = {eid: pos for pos, eid in enumerate(original_lists[i])}
        sem_data.sort(key=lambda eid: orig_pos.get(eid, 10**9))

        p["registros_periodo"] = [eid for _, eid in datados] + sem_data

    return data


def post_process_data(data: Dict) -> Dict:
    """Aplica regras de negócio, correções matemáticas e fusão de aditivos/baixas."""

    # --- PARTE 1: Processar Hipotecas/Ônus ---
    if "hipotecas_onus" in data and isinstance(data["hipotecas_onus"], list):
        raw_list = data["hipotecas_onus"]
        processed_map = {}
        pendentes_processamento = []

        # 1. Primeira Passada: Identificar Registros Principais
        for item in raw_list:
            ident = item.get("registro_ou_averbacao", "")
            tipo = (item.get("tipo_divida") or "").upper()

            # REGRA LEASING
            credor = (item.get("credor") or "").upper()
            if "LEASING" in credor or "ARRENDAMENTO" in credor:
                item["tipo_divida"] = "ARRENDAMENTO MERCANTIL"

            # REGRA MOEDA (normalização e conversão CR$ -> R$)
            val_orig = item.get("valor_divida_original") or ""
            val_atual = item.get("valor_divida")

            # 1) Se houver valor_divida_original, ele é a fonte prioritária
            if val_orig:
                val_float = parse_monetary_value(val_orig)
                if isinstance(val_float, (int, float)):
                    up = val_orig.upper()

                    if "CR$" in up:
                        # Conversão cruzeiro real -> real (1 R$ = 2.750 CR$)
                        val_reais = val_float / 2750.0
                        item["valor_divida"] = format_currency(val_reais)

                    elif "R$" in up or "REAIS" in up:
                        # Já está em reais, apenas normaliza o formato
                        item["valor_divida"] = format_currency(val_float)

            # 2) Se ainda não há valor_divida normalizado,
            #    mas o campo veio preenchido (ex.: "93354.27"),
            #    normaliza assim mesmo.
            if not item.get("valor_divida") and val_atual:
                val_num = parse_monetary_value(val_atual)
                if isinstance(val_num, (int, float)):
                    item["valor_divida"] = format_currency(val_num)


            is_baixa = tipo.startswith("BAIXA") or tipo.startswith("CANCELAMENTO")
            is_aditivo = (
                "ADITIVO" in tipo or "PRORROGACAO" in tipo or "RERRATIFICACAO" in tipo
            )

            if is_baixa or is_aditivo:
                pendentes_processamento.append(item)
            else:
                if ident:
                    processed_map[ident] = item
                    if "historico_aditivos" not in item:
                        item["historico_aditivos"] = []
                else:
                    processed_map[f"unknown_{len(processed_map)}"] = item

        # 2. Segunda Passada: Processar Dependentes
        for pendente in pendentes_processamento:
            tipo_p = (pendente.get("tipo_divida") or "").upper()
            is_aditivo = "ADITIVO" in tipo_p or "PRORROGACAO" in tipo_p

            contrato_pendente = pendente.get("numero_contrato")
            texto_busca = (
                (pendente.get("detalhes_baixa") or "")
                + " "
                + (pendente.get("detalhes") or "")
                + " "
                + (pendente.get("observacao_juridica") or "")
            )

            pai_encontrado = None

            # Busca pelo contrato
            if contrato_pendente:
                for reg in processed_map.values():
                    if reg.get("numero_contrato") == contrato_pendente:
                        pai_encontrado = reg
                        break

            # Busca pelo R.XX
            if not pai_encontrado:
                match_ref = re.search(
                    r"(R\.|Registro n\.º?)\s*(\d+)", texto_busca, re.IGNORECASE
                )
                if match_ref:
                    chave_pai = f"R.{match_ref.group(2)}"
                    if chave_pai in processed_map:
                        pai_encontrado = processed_map[chave_pai]

            if pai_encontrado:
                if is_aditivo:
                    novo_vencimento = pendente.get("vencimento")
                    if novo_vencimento:
                        pai_encontrado["vencimento"] = novo_vencimento

                    novo_valor = pendente.get("valor_divida")
                    if novo_valor:
                        pai_encontrado["valor_divida"] = novo_valor

                    aditivo_info = {
                        "averbacao": pendente.get("registro_ou_averbacao"),
                        "data": pendente.get("data_registro"),
                        "resumo": f"{pendente.get('tipo_divida')}: Vencimento alterado para {novo_vencimento or 'N/A'}",
                    }
                    if "historico_aditivos" not in pai_encontrado:
                        pai_encontrado["historico_aditivos"] = []
                    pai_encontrado["historico_aditivos"].append(aditivo_info)

                else:
                    # BAIXA
                    pai_encontrado["cancelada"] = True
                    pai_encontrado["quitada"] = pendente.get("quitada")
                    pai_encontrado["averbacao_baixa"] = pendente.get(
                        "registro_ou_averbacao"
                    )
                    pai_encontrado["data_baixa"] = pendente.get("data_baixa")
                    pai_encontrado["folha_baixa"] = pendente.get("folha_localizacao")

                    # CORREÇÃO: Extração Inteligente de Autorização
                    # Se o campo veio vazio, tenta pescar no texto
                    auth = pendente.get("autorizacao_baixa")
                    if not auth:
                        # Procura padrões comuns de autorização no texto
                        match_auth = re.search(
                            r"(autorização emitida pelo .+?)(,|$|\.)",
                            texto_busca,
                            re.IGNORECASE,
                        )
                        if match_auth:
                            auth = match_auth.group(1)

                    pai_encontrado["autorizacao_baixa"] = auth
                    pai_encontrado["detalhes_baixa"] = pendente.get(
                        "detalhes_baixa"
                    ) or pendente.get("detalhes")

        final_list = list(processed_map.values())

        def sort_key(x):
            reg = x.get("registro_ou_averbacao", "")
            nums = re.findall(r"\d+", reg)
            return int(nums[0]) if nums else 9999

        final_list.sort(key=sort_key)
        data["hipotecas_onus"] = final_list

    # Corrige limites do histórico por transações de venda (fonte de verdade)
    data = corrigir_historico_titularidade_por_transacoes_venda(data)

    # Rebuild determinístico do histórico de titularidade (ESCRITURA_IMOVEL)
    # Evita que baixas (Av.*) sejam atribuídas ao período errado.
    data = rebuild_registros_periodo_escritura_imovel(data)

    return data


# --- INTEGRAÇÃO COM IA ---


def call_llm_provider(prompt_text: str, config: Dict) -> str:
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY não definida.")

    model_name = "gemini-2.5-flash"

    client = genai.Client(api_key=api_key)
    generate_config = types.GenerateContentConfig(
        temperature=0.0,
        max_output_tokens=65536,
        response_mime_type="application/json",
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
        ],
    )

    try:
        response = client.models.generate_content(
            model=model_name, contents=prompt_text, config=generate_config
        )
        return response.text or ""
    except Exception as e:
        print(f"   [ERRO API] {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)


# --- LÓGICA DO AGENTE ---


def assemble_prompt(
    base_prompt: str, skill_content: str, schema_content: str, doc_content: str
) -> str:
    parts = [
        base_prompt,
        "\n---\n# 1. SCHEMA DE SAÍDA",
        "```json",
        schema_content,
        "```",
        "\n---\n# 2. REGRAS",
        skill_content,
        "\n---\n# 3. DOCUMENTO",
        doc_content,
    ]
    return "\n".join(parts)


def process_job(job: Dict, global_config: Dict, project_root: str):
    print(f"\n--- Job: {job.get('name')} ---")
    input_dir = os.path.join(project_root, job["input_dir"])
    output_dir = os.path.join(project_root, job["output_dir"])

    prompt_file = os.path.join(project_root, global_config["paths"]["prompt_file"])

    skill_key = job["skill_key"]
    skill_rel_path = global_config["skills_map"].get(skill_key)

    if not skill_rel_path:
        print(f"   [ERRO] Skill '{skill_key}' não encontrada no mapa.")
        return

    skill_file = os.path.join(project_root, skill_rel_path)
    schema_file = os.path.join(project_root, job["schema_file"])

    base_prompt = read_file(prompt_file)
    skill_content = read_file(skill_file)
    schema_content = read_file(schema_file)

    md_files = glob.glob(os.path.join(input_dir, "*.md"))
    if not md_files:
        print(f"   [AVISO] Sem arquivos .md em {input_dir}")
        return

    mode = job.get("mode", "individual")
    prefix = job.get("output_prefix", "")

    def handle_response(json_str, file_base_name):
        clean_json = extract_json_from_text(json_str)
        if not clean_json:
            print("   [ERRO] Resposta vazia.")
            return

        try:
            data = json.loads(clean_json)

            if (job.get("skill_key") or "").strip() == "escritura_imovel":
                print(
                    "   [INFO] Aplicando correções pós-processamento (Aditivos/Baixas/Histórico)..."
                )
                data = post_process_data(data)

            out_name = f"{prefix}{file_base_name.replace('.md', '.json')}"
            save_json(data, os.path.join(output_dir, out_name))
            print(f"   -> Salvo: {out_name}")

        except json.JSONDecodeError:
            print("   [ERRO] JSON inválido.")
            save_json(
                {"raw": json_str},
                os.path.join(output_dir, f"{prefix}{file_base_name}.error.json"),
            )

    if mode == "individual":
        for fpath in md_files:
            fname = os.path.basename(fpath)
            print(f"   Processando: {fname}")
            full_prompt = assemble_prompt(
                base_prompt, skill_content, schema_content, read_file(fpath)
            )
            resp = call_llm_provider(full_prompt, global_config)
            handle_response(resp, fname)

    elif mode == "consolidated":
        print(f"   Modo Consolidado ({len(md_files)} arqs)...")
        all_content = ""
        for fpath in md_files:
            all_content += (
                f"\n\n--- DOC: {os.path.basename(fpath)} ---\n{read_file(fpath)}\n"
            )

        full_prompt = assemble_prompt(
            base_prompt, skill_content, schema_content, all_content
        )
        resp = call_llm_provider(full_prompt, global_config)
        out_name = job.get("output_filename", "consolidated.json").replace(
            ".json", ".md"
        )
        handle_response(resp, out_name)


def main():
    try:
        config = load_config()
        project_root = get_project_root()
        agent_name = config.get("runtime", {}).get("agent_name", "Collector")
        print(f"=== {agent_name} Iniciado ===")
        for job in config.get("jobs", []):
            process_job(job, config, project_root)
        print(f"=== {agent_name} Finalizado ===")
    except Exception as e:
        print(f"ERRO FATAL: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
