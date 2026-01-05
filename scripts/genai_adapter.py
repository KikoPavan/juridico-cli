import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

import yaml  # <--- Nova importação
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Configuração básica de logs
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()


class GenAIAdapter:
    def __init__(self, config_path: str = "config.yaml"):
        """
        Inicializa o adaptador lendo as configurações do config.yaml.
        """
        self.config = self._load_config(config_path)

        # Configurações extraídas do YAML
        runtime_conf = self.config.get("runtime", {})
        self.model_name = runtime_conf.get(
            "model", "gemini-2.5-flash"
        )  # Default se falhar
        self.temperature = runtime_conf.get("temperature", 0.0)

        # API Key continua vindo do .env por segurança
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "A variável de ambiente GOOGLE_API_KEY não está definida no .env"
            )

        logger.info(
            f"Inicializando Agente com Modelo: {self.model_name} (Temp: {self.temperature})"
        )
        self.client = genai.Client(api_key=api_key)
        self.schemas_dir = Path("schemas")

    def _load_config(self, path: str) -> Dict[str, Any]:
        """Lê o arquivo YAML de configuração."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Configuração '{path}' não encontrada. Usando defaults.")
            return {}
        except Exception as e:
            logger.error(f"Erro ao ler config.yaml: {e}")
            return {}

    def _load_schema(self, schema_filename: str) -> Dict[str, Any]:
        # ... (MANTENHA ESTE MÉTODO IGUAL AO ANTERIOR) ...
        schema_path = self.schemas_dir / schema_filename
        if not schema_path.exists():
            logger.warning(
                f"Schema '{schema_filename}' não encontrado. Tentando 'default.schema.json'."
            )
            schema_path = self.schemas_dir / "default.schema.json"

        if not schema_path.exists():
            raise FileNotFoundError(f"Nenhum schema encontrado em {self.schemas_dir}")

        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def extract_structured_data(
        self, markdown_content: str, schema_filename: str, system_instruction: str
    ) -> Dict[str, Any]:
        try:
            json_schema = self._load_schema(schema_filename)

            # Configuração
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=json_schema,
                temperature=self.temperature,
            )

            full_prompt = (
                f"{system_instruction}\n\n"
                f"--- DOCUMENTO PARA ANÁLISE ---\n"
                f"{markdown_content}"
            )

            logger.info(f"Enviando requisição para o modelo {self.model_name}...")

            response = self.client.models.generate_content(
                model=self.model_name, contents=full_prompt, config=config
            )

            # --- ÁREA DE CORREÇÃO E BLINDAGEM ---
            if not response.text:
                logger.error(
                    "A resposta do modelo veio vazia ou bloqueada por segurança."
                )
                return {"erro": "Resposta vazia", "revisar": True}

            raw_text = response.text.strip()

            # Remove blocos de código Markdown se o modelo insistir em mandá-los
            if raw_text.startswith("```"):
                # Remove ```json no início e ``` no final
                lines = raw_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_text = "\n".join(lines).strip()

            try:
                parsed_data = json.loads(raw_text)
                return parsed_data
            except json.JSONDecodeError as json_err:
                logger.error(
                    f"Erro ao fazer parse do JSON. Texto recebido iniciava com: {raw_text[:100]}..."
                )
                # Salva o texto problemático num arquivo de debug se precisar
                with open("debug_last_error.txt", "w") as f:
                    f.write(raw_text)
                raise json_err
            # ------------------------------------

        except Exception as e:
            logger.error(f"Erro GenAI: {e}")
            return {"erro": str(e), "status": "falha"}
