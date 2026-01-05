"""
Agente: reconciler-cli

Passos:
1) Motor heurístico em Python:
   - Lê JSONs monetários (monetary_out_cad-obr_*.json, ou padrão definido em config)
   - Constrói grafo consolidado de obrigações (outputs/cadeia_obrigacoes.json)

2) Narrativa analítica com LLM (Gemini):
   - Usa grafo + context.json + contexto_relacoes.json + prompts
   - Gera relatório em Markdown em outputs/reconciler_relatorio.md
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import typer
import yaml
from google import genai
from google.genai.types import GenerateContentConfig

# ---------------------------------------------------------------------------
# Configuração básica de logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

app = typer.Typer(help="Agente Reconciler-CLI (cadeia de obrigações).")


# ---------------------------------------------------------------------------
# Funções utilitárias
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Configuração YAML não encontrada: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    logging.info("Configuração carregada de: %s", path)
    return data


def _load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo JSON não encontrado: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de texto não encontrado: {path}")
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Classe principal do agente
# ---------------------------------------------------------------------------


class ReconcilerAgent:
    def __init__(self, config_path: str) -> None:
        self.config_path = Path(config_path)
        self.config = _load_yaml(self.config_path)

        # Raiz do projeto
        # 1) runtime.project_root (novo padrão)
        # 2) project_root na raiz do YAML (legado)
        # 3) dois níveis acima deste arquivo (fallback)
        default_root = Path(__file__).resolve().parents[2]
        runtime_cfg = self.config.get("runtime", {}) or {}
        project_root_cfg = runtime_cfg.get(
            "project_root",
            self.config.get("project_root", default_root),
        )
        self.project_root = Path(project_root_cfg).resolve()
        logging.info("project_root resolvido para: %s", self.project_root)

        # Configuração de caminhos
        paths_cfg = self.config.get("paths", {}) or {}

        # Diretório dos JSONs monetários (por padrão já aponta para 02_monetary)
        self.path_input_cad_obr = self._resolve_path(
            paths_cfg.get("input_cad_obr", "outputs/cad-obr/02_monetary")
        )

        # Padrão dos arquivos monetários (pode ser sobrescrito em config.paths)
        self.monetary_pattern = paths_cfg.get(
            "input_cad_obr_pattern",
            "monetary_out_cad-obr_*.json",
        )

        self.path_context = self._resolve_path(
            paths_cfg.get("context_file", "data/context.json")
        )
        self.path_relacoes = self._resolve_path(
            paths_cfg.get("relacoes_file", "data/contexto_relacoes.json")
        )
        self.path_prompt_system = self._resolve_path(
            paths_cfg.get("prompt_system", "prompts/reconciler.md")
        )
        self.path_prompt_user = self._resolve_path(
            paths_cfg.get("prompt_user", "prompts/reconciler_user.md")
        )
        self.path_output_graph = self._resolve_path(
            paths_cfg.get("output_graph", "outputs/cadeia_obrigacoes.json")
        )
        self.path_output_report = self._resolve_path(
            paths_cfg.get("output_report", "outputs/reconciler_relatorio.md")
        )

        logging.info("Diretório de entrada (cad-obr): %s", self.path_input_cad_obr)
        logging.info("Padrão de arquivos monetários: %s", self.monetary_pattern)
        logging.info("Arquivo de contexto: %s", self.path_context)
        logging.info("Arquivo de relações: %s", self.path_relacoes)
        logging.info("Prompt system: %s", self.path_prompt_system)
        logging.info("Prompt user: %s", self.path_prompt_user)
        logging.info("Saída grafo: %s", self.path_output_graph)
        logging.info("Saída relatório: %s", self.path_output_report)

        # LLM (Gemini via google.genai)
        llm_cfg = self.config.get("llm", {}) or {}
        self.model_name: str = llm_cfg.get("model", "gemini-2.5-flash")
        self.temperature: float = float(llm_cfg.get("temperature", 0.0))

        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Nenhuma API key encontrada. Defina GOOGLE_API_KEY ou GEMINI_API_KEY."
            )

        self.client = genai.Client(api_key=api_key)

        logging.info(
            "Inicializando Agente Reconciler com Modelo: %s (Temp: %.2f)",
            self.model_name,
            self.temperature,
        )

    # ------------------------ util interno ------------------------

    def _resolve_path(self, relative_or_absolute: str) -> Path:
        p = Path(relative_or_absolute)
        if p.is_absolute():
            return p
        return (self.project_root / p).resolve()

    # -----------------------------------------------------------------------
    # Passo 1: Construção do grafo de obrigações a partir dos JSON monetários
    # -----------------------------------------------------------------------

    def step_1_build_graph(self) -> Path:
        """
        Lê arquivos:
          outputs/cad-obr/02_monetary/*.json
        e produz um grafo consolidado de obrigações em:
          outputs/cadeia_obrigacoes.json
        """
        logging.info("Iniciando reconciliação de obrigações...")

        # Agora usamos TODOS os .json da pasta configurada (ex.: outputs/cad-obr/02_monetary)
        pattern = "*.json"
        files = sorted(self.path_input_cad_obr.glob(pattern))

        if not files:
            logging.warning(
                "Nenhum arquivo '%s' encontrado em %s.",
                pattern,
                self.path_input_cad_obr,
            )
        else:
            logging.info(
                "Encontrados %d arquivo(s) de cad-obr para reconciliação.",
                len(files),
            )

        obrigacoes: List[Dict[str, Any]] = []

        for fpath in files:
            try:
                blob = _load_json(fpath)
            except Exception as e:  # noqa: BLE001
                logging.error("Falha ao ler %s: %s", fpath, e)
                continue

            dados = blob.get("dados", {})
            hipotecas = dados.get("hipotecas_onus", [])

            matricula = dados.get("matricula", dados.get("numero_matricula"))

            for item in hipotecas:
                reg = item.get("registro_ou_averbacao")
                if not reg:
                    continue

                oid = f"{matricula}:{reg}" if matricula else reg

                obrigacao = {
                    "id": oid,
                    "arquivo_origem": fpath.name,
                    "matricula": matricula,
                    "registro_ou_averbacao": reg,
                    "data_registro": item.get("data_registro") or item.get("data"),
                    "data_efetiva": item.get("data_efetiva"),
                    "tipo_divida": item.get("tipo_divida"),
                    "numero_contrato": item.get("numero_contrato"),
                    "credor": item.get("credor"),
                    "devedor": item.get("devedor"),
                    "valor_divida_original": item.get("valor_divida_original"),
                    "valor_divida": item.get("valor_divida"),
                    "prazo": item.get("prazo"),
                    "vencimento": item.get("vencimento"),
                    "taxas": item.get("taxas"),
                    "quitada": item.get("quitada"),
                    "cancelada": item.get("cancelada"),
                    "detalhes_baixa": item.get("detalhes_baixa"),
                    "folha_localizacao": item.get("folha_localizacao"),
                    "valor_presente": item.get("valor_presente"),
                    "_monetary_meta": item.get("_monetary_meta"),
                }

                obrigacoes.append(obrigacao)

        graph: Dict[str, Any] = {
            "versao": "1.0",
            "gerado_em": __import__("datetime")
            .datetime.now()
            .isoformat(timespec="seconds"),
            "obrigacoes": obrigacoes,
            "metadados": {
                "total_obrigacoes": len(obrigacoes),
                "fontes": [str(f) for f in files],
            },
        }

        _write_json(self.path_output_graph, graph)
        logging.info("Grafo gerado em: %s", self.path_output_graph)
        return self.path_output_graph


    # -----------------------------------------------------------------------
    # Passo 2: Geração da narrativa analítica com Gemini (google.genai)
    # -----------------------------------------------------------------------

    def step_2_narrative_generation(self, graph_path: Path) -> None:
        """
        Usa:
          - grafo de obrigações (cadeia_obrigacoes.json)
          - contexto do caso (data/context.json)
          - contexto de relações (data/contexto_relacoes.json)
          - prompts system/user (prompts/reconciler_*.md)

        E gera relatório analítico em Markdown na pasta outputs.
        """
        # Carrega dados
        graph = _load_json(graph_path)
        context = _load_json(self.path_context)
        relacoes = _load_json(self.path_relacoes)

        system_prompt = _read_text(self.path_prompt_system)
        try:
            user_prompt = _read_text(self.path_prompt_user)
        except FileNotFoundError:
            user_prompt = ""

        # Monta um "super prompt" único (texto) para o modelo
        full_prompt_parts: List[str] = []

        # System-like
        full_prompt_parts.append(system_prompt.strip())
        full_prompt_parts.append("\n\n# Dados Estruturados\n")

        # Contexto do caso
        full_prompt_parts.append("## 1. Contexto do caso (context.json)\n")
        full_prompt_parts.append("```json\n")
        full_prompt_parts.append(json.dumps(context, ensure_ascii=False, indent=2))
        full_prompt_parts.append("\n```\n")

        # Relações
        full_prompt_parts.append(
            "## 2. Contexto de relações (contexto_relacoes.json)\n"
        )
        full_prompt_parts.append("```json\n")
        full_prompt_parts.append(json.dumps(relacoes, ensure_ascii=False, indent=2))
        full_prompt_parts.append("\n```\n")

        # Grafo de obrigações
        full_prompt_parts.append(
            "## 3. Grafo consolidado de obrigações (cadeia_obrigacoes.json)\n"
        )
        full_prompt_parts.append("```json\n")
        full_prompt_parts.append(json.dumps(graph, ensure_ascii=False, indent=2))
        full_prompt_parts.append("\n```\n")

        # Instrução de usuário: o que queremos como saída
        full_prompt_parts.append("\n\n# Tarefa\n")
        full_prompt_parts.append(user_prompt.strip())

        full_prompt = "\n".join(full_prompt_parts)

        # Configuração da geração
        cfg = GenerateContentConfig(
            temperature=self.temperature,
            # text/markdown não é suportado na SDK nova.
            # Usamos text/plain e ainda assim escrevemos Markdown no conteúdo.
            response_mime_type="text/plain",
        )

        logging.info("Gerando narrativa analítica com IA (Gemini)...")

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=full_prompt,
            config=cfg,
        )

        # A SDK expõe response.text como atalho
        texto = getattr(response, "text", None)
        candidates = getattr(response, "candidates", None)
        if not texto and candidates is not None and len(candidates) > 0:
            # Fallback manual (por segurança)
            try:
                cand = candidates[0]
                parts = getattr(cand, "content", cand).parts  # type: ignore[attr-defined]
                texto = "".join(p.text for p in parts if hasattr(p, "text"))
            except Exception as e:  # noqa: BLE001
                logging.error("Falha ao extrair texto da resposta: %s", e)
                texto = ""

        if not texto:
            raise RuntimeError("Resposta vazia do modelo Gemini ao gerar narrativa.")

        # Salvamos como Markdown (o conteúdo já vem em texto simples compatível)
        self.path_output_report.parent.mkdir(parents=True, exist_ok=True)
        self.path_output_report.write_text(texto, encoding="utf-8")
        logging.info("Relatório analítico salvo em: %s", self.path_output_report)

    # -----------------------------------------------------------------------
    # Orquestração
    # -----------------------------------------------------------------------

    def run(self) -> None:
        """
        1) Constrói grafo de obrigações (motor heurístico).
        2) Gera narrativa analítica com o LLM.
        """
        logging.info(">>> Passo 1: Executando motor heurístico (Python)...")
        graph_path = self.step_1_build_graph()

        logging.info(">>> Passo 2: Gerando narrativa analítica com IA (Gemini)...")
        self.step_2_narrative_generation(graph_path)


# ---------------------------------------------------------------------------
# CLI Typer
# ---------------------------------------------------------------------------


@app.command()
def main(
    config: str = typer.Option(
        "agents/reconciler-cli/config.yaml",
        "--config",
        "-c",
        help="Caminho para o arquivo de configuração YAML do reconciler-cli.",
    ),
) -> None:
    """
    Executa o agente Reconciler-CLI com base no config.yaml.
    """
    agent = ReconcilerAgent(config_path=config)
    agent.run()


if __name__ == "__main__":
    app()
