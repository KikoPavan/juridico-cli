import os
import subprocess

import yaml


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def get_project_root():
    # Caminho: agents/case-law-cli/main.py -> agents/ -> root/
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def main():
    try:
        config = load_config()
        project_root = get_project_root()

        runtime = config.get("runtime", {})
        paths = config.get("paths", {})

        provider = runtime.get("provider")
        agent_name = runtime.get("agent_name", "Agente Desconhecido")
        extension_name = runtime.get("cli_tool_name")

        print(f"--- Iniciando Agente: {agent_name} (Provedor: {provider}) ---")

        # 1. Resolver caminhos
        prompt_file = os.path.join(project_root, paths.get("prompt_file"))
        firac_input = os.path.join(project_root, config["paths"]["input_file"])
        juris_output = os.path.join(project_root, config["paths"]["output_file"])

        # 2. Ler prompt
        with open(prompt_file, "r", encoding="utf-8") as p:
            prompt_content = p.read()

        # 3. Construir comando (Gemini)
        # --- INÍCIO DA CORREÇÃO ---
        # A flag '-x' foi substituída pelo comando 'extension'
        command = [
            "gemini",
            "extension",  # <-- CORRIGIDO (era "-x")
            extension_name,
            "--",  # Separador de argumentos
            "--firac_file",
            firac_input,
            "--output_file",
            juris_output,
        ]
        # --- FIM DA CORREÇÃO ---

        print(f"Executando: {' '.join(command)}")

        # 4. Chamar sub-processo
        process = subprocess.run(
            command,
            input=prompt_content,
            text=True,
            encoding="utf-8",
            capture_output=True,
        )

        # 5. Imprimir resultados
        if process.returncode == 0:
            print(f"--- {agent_name} concluído com sucesso ---")
            print("Saída (stdout):")
            print(process.stdout)
        else:
            print(
                f"--- Erro ao executar {agent_name} (Código: {process.returncode}) ---"
            )
            print("Erro (stderr):")
            print(process.stderr)

    except FileNotFoundError as e:
        print("Erro: Arquivo não encontrado. Verifique seu config.yaml e os caminhos.")
        print(f"Detalhe: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")


if __name__ == "__main__":
    main()
