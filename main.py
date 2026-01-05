import os  # <--- Adicione
from pathlib import Path

import typer
from dotenv import load_dotenv  # <--- Adicione esta importação
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from scripts.doc_collector import DocCollector

# Importações dos scripts
from scripts.setup_schemas import generate_schemas
from scripts.transcriber_util import PDFTranscriber

# --- CORREÇÃO AQUI ---
# Carrega as variáveis de ambiente antes de qualquer comando
load_dotenv()
# ---------------------

# Configuração da Aplicação
app = typer.Typer(
    name="juridico-cli",
    help="CLI para Orquestração de Agentes Jurídicos (Collector & Transcriber)",
    add_completion=False,
)
console = Console()


@app.command()
def setup():
    """
    [Passo 1] Gera/Atualiza os arquivos JSON Schemas na pasta schemas/.
    """
    console.print(Panel("[bold blue]Inicializando Setup de Schemas...[/bold blue]"))
    try:
        generate_schemas()
        console.print("[green]✔ Schemas gerados com sucesso![/green]")
    except Exception as e:
        console.print(f"[red]Erro ao gerar schemas: {e}[/red]")


@app.command()
def transcrever(
    pasta_entrada: str = typer.Option(
        "data/anexos", help="Pasta contendo os PDFs para conversão."
    ),
    forcar: bool = typer.Option(
        False, help="Se True, reprocessa arquivos que já existem em Markdown."
    ),
):
    """
    [Passo 2] Converte PDFs da pasta de anexos para Markdown com numeração de folhas.
    """
    console.print(
        Panel(
            f"[bold yellow]Iniciando Transcrição de PDFs em: {pasta_entrada}[/bold yellow]"
        )
    )

    path_entrada = Path(pasta_entrada)
    if not path_entrada.exists():
        console.print(f"[red]Erro: A pasta '{pasta_entrada}' não existe.[/red]")
        raise typer.Exit(code=1)

    transcriber = PDFTranscriber(
        output_dir=str(path_entrada)
    )  # Salva o .md ao lado do .pdf ou em pasta específica

    pdfs = list(path_entrada.glob("*.pdf"))
    if not pdfs:
        console.print("[yellow]Nenhum arquivo PDF encontrado para processar.[/yellow]")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(description="Processando...", total=len(pdfs))

        for pdf in pdfs:
            nome_md = pdf.with_suffix(".md").name
            caminho_md = path_entrada / nome_md

            progress.update(task, description=f"Convertendo: {pdf.name}")

            if caminho_md.exists() and not forcar:
                console.print(f"[dim]Ignorado (já existe): {nome_md}[/dim]")
                continue

            try:
                transcriber.convert(str(pdf))
                console.print(f"[green]✔ Convertido: {nome_md}[/green]")
            except Exception as e:
                console.print(f"[red]✖ Falha em {pdf.name}: {e}[/red]")


@app.command()
def coletar():
    """
    [Passo 3] Executa o Agente Collector (Gemini) para extrair dados dos Markdowns.
    """
    console.print(
        Panel(
            "[bold magenta]Iniciando Agente Collector (Extração de Dados)...[/bold magenta]"
        )
    )

    # Verifica se a API KEY está configurada

    if not os.getenv("GOOGLE_API_KEY"):
        console.print(
            "[bold red]ERRO CRÍTICO:[/bold red] Variável GOOGLE_API_KEY não encontrada no .env"
        )
        raise typer.Exit(code=1)

    try:
        collector = DocCollector(root_dir=".")
        # O método run() do collector já tem seus próprios logs,
        # mas aqui capturamos o fluxo geral.
        collector.run()
        console.print(
            "\n[bold green]✔ Ciclo de coleta finalizado! Verifique a pasta 'outputs/'.[/bold green]"
        )
    except Exception as e:
        console.print(f"[bold red]Erro fatal durante a coleta: {e}[/bold red]")


@app.command()
def tudo():
    """
    Executa o pipeline completo: Setup -> Transcrever -> Coletar.
    """
    setup()
    console.print()
    transcrever()
    console.print()
    coletar()


if __name__ == "__main__":
    app()
