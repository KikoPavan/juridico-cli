import glob
import json
import os
import re
from typing import Any, Dict

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


def parse_monetary_value(val_str: str) -> float:
    if not val_str:
        return 0.0
    clean = re.sub(r"[^\d,.]", "", val_str)
    if "," in clean and "." in clean:
        clean = clean.replace(".", "").replace(",", ".")
    elif "," in clean:
        clean = clean.replace(",", ".")
    try:
        return float(clean)
    except ValueError:
        return 0.0


def format_currency(val_float: float) -> str:
    return f"R$ {val_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


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

            if job.get("id") == "cad-obr":
                print(
                    "   [INFO] Aplicando correções pós-processamento (Aditivos/Baixas)..."
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
