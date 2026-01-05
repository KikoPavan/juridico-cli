import os
import subprocess

import yaml


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main():
    try:
        config = load_config()

        runtime = config.get("runtime", {})

        provider = runtime.get("provider")
        agent_name = runtime.get("agent_name", "Agente Desconhecido")
        skill_name = runtime.get("cli_tool_name")

        print(f"--- Iniciando Agente: {agent_name} (Provedor: {provider}) ---")

        # 1. Construir comando (Claude)
        # A Skill (firac-relatorio) é responsável por ler seus próprios
        # arquivos de input/prompt/template e salvar o output.
        command = ["claude", "skill", skill_name]

        print(f"Executando: {' '.join(command)}")

        # 2. Chamar sub-processo
        process = subprocess.run(
            command, text=True, encoding="utf-8", capture_output=True
        )

        # 3. Imprimir resultados
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
        print("Erro: Arquivo 'config.yaml' não encontrado.")
        print(f"Detalhe: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")


if __name__ == "__main__":
    main()
