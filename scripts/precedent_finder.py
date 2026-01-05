import argparse
import os
import sys


def log_message(message):
    """Imprime uma mensagem de log para o stdout (que o Gemini irá capturar)"""
    print(f"[precedent_finder.py] {message}", file=sys.stdout)


def simulate_thesis_extraction(firac_file):
    """
    Função mock para simular a leitura do FIRAC e extração de teses.
    """
    log_message(f"Lendo teses do arquivo: {firac_file}")
    if not os.path.exists(firac_file):
        log_message(f"Arquivo FIRAC não encontrado em {firac_file}. Usando teses mock.")
        return [
            "Tese 1: Nulidade de hipoteca por falta de poderes específicos em procuração."
        ]

    # Simulação de leitura
    with open(firac_file, "r", encoding="utf-8") as f:
        content = f.read()
        log_message(f"Arquivo lido: {len(content)} caracteres (simulado).")
        # Aqui entraria uma lógica real de NLP para extrair teses

    log_message("Teses extraídas (simulado).")
    return [
        "Tese 1: Nulidade de hipoteca por falta de poderes específicos em procuração.",
        "Tese 2: Aplicação do Art. 661 §1º do Código Civil em mandatos.",
    ]


def simulate_jurisprudence_search(theses):
    """
    Função mock para simular a busca de jurisprudência (API/Web Search).
    Os dados mockados seguem o formato do 'prompts/case-law.md'.
    """
    log_message(f"Simulando busca de jurisprudência para {len(theses)} teses...")

    mock_juris = [
        {
            "tese": "Tese 1: Nulidade de hipoteca por falta de poderes específicos em procuração.",
            "precedentes": [
                {
                    "citation": "STJ – REsp 1.845.662/SP – Rel. Min. Nancy Andrighi – Julg. 02/03/2021 – DJe 05/03/2021",
                    "adherence": "Alta",
                    "distinction": "Nenhuma distinção relevante. O caso trata exatamente de mandato sem poderes especiais para alienar ou gravar.",
                },
                {
                    "citation": "TJSP – Apelação Cível 1004567-89.2020.8.26.0100 – Rel. Des. José Carlos Ferreira Alves – Julg. 15/09/2022 – DJe 20/09/2022",
                    "adherence": "Média",
                    "distinction": "O caso paulista envolvia vício de consentimento (dolo) concomitante à falta de poderes.",
                },
            ],
        },
        {
            "tese": "Tese 2: Aplicação do Art. 661 §1º do Código Civil em mandatos.",
            "precedentes": [
                {
                    "citation": "STJ – AgInt no REsp 1.600.777/RJ – Rel. Min. Raul Araújo – Julg. 19/10/2020 – DJe 16/11/2020",
                    "adherence": "Alta",
                    "distinction": "O precedente discute a interpretação do Art. 661, § 1º, e a necessidade de poderes expressos.",
                }
            ],
        },
    ]
    log_message("Busca de jurisprudência simulada concluída.")
    return mock_juris


def write_jurisprudence_output(output_file_md, juris_data):
    """
    Escreve o arquivo de saída .md conforme o formato esperado
    pelo 'prompts/case-law.md'.
    """
    with open(output_file_md, "w", encoding="utf-8") as f:
        f.write("# Saída do Agente: case-law-cli\n\n")
        f.write("## 1. Teses e Precedentes Relevantes\n\n")

        for tese_data in juris_data:
            f.write(f"### Tese: {tese_data['tese']}\n\n")

            if not tese_data["precedentes"]:
                f.write("*Nenhum precedente encontrado para esta tese.*\n\n")
                continue

            for prec in tese_data["precedentes"]:
                f.write(f"**Precedente:** {prec['citation']}\n")
                f.write(f"  - **[Adesão]:** {prec['adherence']}\n")
                f.write(f"  - **[Distinção]:** {prec['distinction']}\n\n")

            f.write("---\n\n")

    log_message(f"Arquivo 'jurisprudencia.md' gerado em: {output_file_md}")


def main():
    parser = argparse.ArgumentParser(
        description="Script de Busca de Jurisprudência (Mock)"
    )
    parser.add_argument(
        "--firac_file",
        required=True,
        help="Caminho para o arquivo 'relatorio_firac.md'",
    )
    parser.add_argument(
        "--output_file",
        required=True,
        help="Caminho para o arquivo de saída 'jurisprudencia.md'",
    )
    parser.add_argument(
        "--prompt_stdin",
        action="store_true",
        help="Flag para indicar que o prompt virá do STDIN",
    )

    try:
        args = parser.parse_args()

        if args.prompt_stdin:
            prompt_content = sys.stdin.read()
            log_message(
                f"Prompt recebido via STDIN com sucesso ({len(prompt_content)} caracteres lidos)."
            )
            # Na implementação real, o prompt (e o 'google_web_search' tool)
            # seria usado para guiar a busca.

        # 1. Simular extração de teses
        theses = simulate_thesis_extraction(args.firac_file)

        # 2. Simular busca de jurisprudência
        juris_data = simulate_jurisprudence_search(theses)

        # 3. Escrever arquivo de saída
        write_jurisprudence_output(args.output_file, juris_data)

        log_message("Script 'precedent_finder.py' finalizado.")

    except Exception as e:
        print(f"Erro fatal em precedent_finder.py: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
