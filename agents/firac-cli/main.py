import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml


def load_config(argv_path: str | None = None) -> dict:
    """
    Carrega o YAML. Se o usuário passar um caminho via argv, usa esse caminho.
    Caso contrário, usa o config.yaml na mesma pasta do main.py.
    """
    if argv_path:
        p = Path(argv_path)
        if p.is_dir():
            p = p / "config.yaml"
        config_path = p
    else:
        config_path = Path(__file__).with_name("config.yaml")

    if not config_path.exists():
        raise FileNotFoundError(f"Config não encontrado: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    cfg["_config_path"] = str(config_path)
    return cfg


def get_nested(cfg: dict, dotted_key: str, default=None):
    cur = cfg
    for part in dotted_key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def require_str(cfg: dict, dotted_key: str) -> str:
    val = get_nested(cfg, dotted_key, None)
    if val is None:
        raise ValueError(f"Config obrigatório ausente: '{dotted_key}'")
    if not isinstance(val, str):
        raise ValueError(
            f"Config '{dotted_key}' deve ser string, mas veio: {type(val).__name__}"
        )
    val = val.strip()
    if not val:
        raise ValueError(f"Config '{dotted_key}' não pode ser vazio")
    return val


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def extract_markdown(stdout_text: str) -> str:
    """
    Extrai o relatório em Markdown do stdout.
    Heurística: começa em '# Relatório' se existir; caso contrário, usa tudo.
    """
    idx = stdout_text.find("\n# Relatório")
    if idx == -1:
        idx = stdout_text.find("# Relatório")
    if idx != -1:
        return stdout_text[idx:].strip() + "\n"
    return stdout_text.strip() + "\n"


def extract_json_block(stdout_text: str) -> dict | None:
    """
    Extrai o primeiro bloco ```json ... ``` do stdout e retorna como dict.
    """
    m = re.search(r"```json\s*(\{.*?\})\s*```", stdout_text, flags=re.DOTALL)
    if not m:
        return None
    raw = m.group(1).strip()
    return json.loads(raw)


def main():
    try:
        argv_config = sys.argv[1] if len(sys.argv) > 1 else None
        config = load_config(argv_config)

        runtime = (
            config.get("runtime", {})
            if isinstance(config.get("runtime", {}), dict)
            else {}
        )
        provider = runtime.get("provider", "desconhecido")
        agent_name = runtime.get("agent_name", "firac-cli")

        skill_name = require_str(config, "runtime.cli_tool_name")

        # Paths de saída
        output_md = get_nested(
            config, "paths.output_relatorio_firac", "outputs/relatorio_firac.md"
        )
        output_json = get_nested(config, "paths.output_relatorio_firac_json", None)

        output_md_path = Path(output_md)
        if output_json is None or (
            isinstance(output_json, str) and not output_json.strip()
        ):
            # Deriva JSON a partir do MD (relatorio_firac.md -> relatorio_firac.json)
            output_json_path = output_md_path.with_suffix(".json")
        else:
            output_json_path = Path(str(output_json))

        # Logs (sempre bom guardar stdout bruto)
        logs_dir = get_nested(config, "paths.logs_dir", "outputs/firac/99_logs")
        stdout_log_path = Path(logs_dir) / "firac_stdout.txt"
        json_raw_log_path = Path(logs_dir) / "firac_json_raw.txt"

        print(f"--- Iniciando Agente: {agent_name} (Provedor: {provider}) ---")
        print(f"Config carregado de: {config.get('_config_path')}")

        command = ["gemini", "skill", skill_name]
        print(f"Executando: {' '.join(command)}")

        process = subprocess.run(
            command, text=True, encoding="utf-8", capture_output=True
        )

        if process.returncode != 0:
            print(
                f"--- Erro ao executar {agent_name} (Código: {process.returncode}) ---"
            )
            if process.stderr:
                print("Erro (stderr):")
                print(process.stderr)
            if process.stdout:
                print("Saída (stdout):")
                print(process.stdout)
            return

        print(f"--- {agent_name} concluído com sucesso ---")
        if process.stdout:
            print("Saída (stdout):")
            print(process.stdout)

        # 1) Persistir stdout bruto (auditoria)
        ensure_parent_dir(stdout_log_path)
        stdout_log_path.write_text(process.stdout or "", encoding="utf-8")

        # 2) Extrair e salvar Markdown
        md = extract_markdown(process.stdout or "")
        ensure_parent_dir(output_md_path)
        output_md_path.write_text(md, encoding="utf-8")

        # 3) Extrair e salvar JSON (se existir)
        try:
            data = extract_json_block(process.stdout or "")
            if data is not None:
                ensure_parent_dir(output_json_path)
                output_json_path.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            else:
                # Não é erro; apenas não havia bloco json
                pass
        except Exception:
            # Se falhar parse do JSON, salva o trecho bruto para depurar
            ensure_parent_dir(json_raw_log_path)
            json_raw_log_path.write_text(process.stdout or "", encoding="utf-8")
            print(
                "Aviso: não foi possível extrair/parsear o bloco JSON; salvei stdout em logs para depuração."
            )

        print(f"\nArquivos gravados:")
        print(f"- MD:   {output_md_path}")
        print(f"- JSON: {output_json_path}")
        print(f"- LOG:  {stdout_log_path}")

    except FileNotFoundError as e:
        print(f"Erro: {e}")
    except ValueError as e:
        print(f"Erro de configuração: {e}")
        print(
            "Ação: defina 'runtime.cli_tool_name' no config.yaml (ex.: firac-relatorio)."
        )
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")


if __name__ == "__main__":
    main()
