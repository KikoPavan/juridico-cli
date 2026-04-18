"""
LocalLLMClient — Provider para LLM local via LM Studio.

Compatível com a interface agnóstica LLMClient.
Usa a API OpenAI-compatible exposta pelo servidor do LM Studio.
"""

import json
import logging
import os
from typing import Any, Dict, List

import requests

try:
    from .client import LLMClient
except ImportError:
    import sys

    client_mod = sys.modules.get("client_mod")
    LLMClient = client_mod.LLMClient if client_mod else object

logger = logging.getLogger(__name__)


class LocalLLMClient(LLMClient):
    """
    Cliente para LLM local via LM Studio (API OpenAI-compatible).

    Endpoint padrão: http://host.docker.internal:1234
    Configurável via variáveis de ambiente:
      - LLAMA_CPP_ENDPOINT (default: http://host.docker.internal:1234)
      - LLAMA_MODEL (default: modelo carregado no server)
    """

    def __init__(
        self,
        endpoint: str = None,
        model_name: str = None,
        timeout: int = 900,
    ):
        self.endpoint = endpoint or os.environ.get(
            "LLAMA_CPP_ENDPOINT", "http://host.docker.internal:1234"
        ).rstrip("/")
        self.model_name = model_name or os.environ.get("LLAMA_MODEL", "local-model")
        self.timeout = timeout

        # Validar conectividade
        self._health_check()

    def _health_check(self) -> None:
        """Verifica se o endpoint llama.cpp está acessível."""
        try:
            resp = requests.get(f"{self.endpoint}/health", timeout=5)
            if resp.status_code != 200:
                raise RuntimeError(
                    f"llama.cpp health check falhou: HTTP {resp.status_code}"
                )
            logger.info(f"llama.cpp endpoint OK: {self.endpoint}")
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Não foi possível conectar ao llama.cpp em {self.endpoint}: {exc}"
            )

    def generate_text(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Gera texto usando a API de chat do llama.cpp.

        Messages: lista de dicts com 'role' e 'content'.
        Retorna o texto gerado.
        """
        url = f"{self.endpoint}/v1/chat/completions"

        # Montar payload compatível com OpenAI
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.0),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "stream": False,
        }

        # Adicionar parâmetros extras se presentes
        if "top_p" in kwargs:
            payload["top_p"] = kwargs["top_p"]
        if "repeat_penalty" in kwargs:
            payload["repeat_penalty"] = kwargs["repeat_penalty"]

        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            if resp.status_code != 200:
                logger.error(f"llama.cpp HTTP {resp.status_code}: {resp.text[:500]}")
            resp.raise_for_status()
            data = resp.json()

            # Extrair resposta
            choices = data.get("choices", [])
            if not choices:
                raise ValueError("llama.cpp retornou resposta sem choices")

            return choices[0]["message"]["content"]

        except requests.RequestException as exc:
            logger.error(f"Erro na comunicação com llama.cpp: {exc}")
            raise RuntimeError(f"Erro na chamada ao llama.cpp: {exc}")
        except (KeyError, ValueError) as exc:
            logger.error(f"Resposta malformada do llama.cpp: {exc}")
            raise RuntimeError(f"Resposta malformada do llama.cpp: {exc}")

    def generate_structured(
        self,
        messages: List[Dict[str, str]],
        schema: Dict[str, Any],
        **kwargs,
    ) -> Any:
        """
        Gera JSON estruturado usando o llama.cpp.

        Estratégia:
        1. Incluir instruções JSON no system prompt
        2. Usar temperature=0.0 para deterministicidade
        3. Tentar parse do JSON retornado
        4. Se falhar, aplicar reparo heurístico
        """
        # Inserir instrução JSON no system prompt
        system_instruction = (
            "Você deve retornar APENAS um objeto JSON válido, sem markdown, "
            "sem explicação, sem fences de código. O JSON deve seguir "
            "exatamente o schema fornecido."
        )

        # Verificar se já existe mensagem system
        has_system = messages and messages[0].get("role") == "system"
        if has_system:
            messages = [
                {
                    "role": "system",
                    "content": messages[0]["content"] + "\n\n" + system_instruction,
                },
                *messages[1:],
            ]
        else:
            messages = [
                {"role": "system", "content": system_instruction},
                *messages,
            ]

        # Incluir schema no prompt do usuário
        schema_str = json.dumps(schema, ensure_ascii=False, indent=2)
        messages = [
            *messages[:-1],
            {
                "role": "user",
                "content": messages[-1]["content"]
                + f"\n\nSchema esperado:\n```json\n{schema_str}\n```",
            },
        ]

        # Gerar texto com temperature=0
        raw_text = self.generate_text(
            messages,
            temperature=0.0,
            max_tokens=kwargs.get("max_tokens", 8192),
        )

        # Tentar parse do JSON
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            pass

        # Tentar extrair JSON de texto com markdown fences
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Tentar extrair entre chaves
        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            candidate = cleaned[first_brace : last_brace + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"LLM local retornou JSON inválido: {exc}\n"
                    f"Texto (primeiros 500 chars): {raw_text[:500]}"
                )

        raise ValueError(
            f"Não foi possível extrair JSON da resposta do LLM local.\n"
            f"Texto (primeiros 500 chars): {raw_text[:500]}"
        )
