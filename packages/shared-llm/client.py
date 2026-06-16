import abc
from typing import Any, Dict, List


class LLMClient(abc.ABC):
    """
    Interface base agnóstica para todo provedor de inteligência artificial.
    Ao aplicar Inversão de Controle, o orquestrador poderá injetar instâncias sem se amarrar
    a vendor-lockins de biblioteca (ex: OpenAI, Anthropic, Gemini).
    """

    @abc.abstractmethod
    def generate_text(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Recebe a montagem fina de mensagens (role/content) e gera um output de texto genérico.
        """
        pass

    @abc.abstractmethod
    def generate_structured(
        self, messages: List[Dict[str, str]], schema: Dict[str, Any], **kwargs
    ) -> Any:
        """
        Obtém a extração forçando um output perfeitamente aderente ao JSON Schema injetado.
        A camada do cliente implementador cuidará se usará tools/functions, json_mode nativo, etc.
        """
        pass


class DummyLLMClient(LLMClient):
    """
    Dummy object testável provendo mocking sem depender de chaves de API.
    Aprovettável para testes de isolamento de Phase 0 a 3.
    """

    def generate_text(self, messages: List[Dict[str, str]], **kwargs) -> str:
        return "[DUMMY RESPONSE] - Emulated generic text generation."

    def generate_structured(
        self, messages: List[Dict[str, str]], schema: Dict[str, Any], **kwargs
    ) -> Any:
        # Emulating the keys required by the schema with dummy data
        result = {}
        for key in schema.get("properties", {}).keys():
            result[key] = f"mock_{key}"
        return result


class LLMClientFactory:
    """
    Fábrica mínima para o Baseline.
    Evita que instâncias rígidas como GeminiLLMClient ou DummyLLMClient
    sejam costuradas nos apps consumistas.
    """

    @staticmethod
    def create_client(provider_override: str = None, model_override: str = None) -> "LLMClient":
        import os

        from dotenv import load_dotenv

        # Garante variáveis locais (ex: .env) carregadas
        load_dotenv(override=False)

        # Default blindado: Gemini como Provedor Principal do Baseline
        provider = provider_override or os.environ.get("LLM_PROVIDER", "gemini").lower()

        if provider == "dummy":
            return DummyLLMClient()

        elif provider in ("local", "lm_studio"):
            try:
                from .local_client import LocalLLMClient
            except ImportError:
                import importlib.util
                import os
                import sys

                client_dir = os.path.dirname(__file__)
                spec = importlib.util.spec_from_file_location(
                    "local_client", os.path.join(client_dir, "local_client.py")
                )
                local_mod = importlib.util.module_from_spec(spec)
                sys.modules["local_client"] = local_mod
                spec.loader.exec_module(local_mod)
                LocalLLMClient = local_mod.LocalLLMClient

            endpoint = os.environ.get(
                "LLAMA_CPP_ENDPOINT", "http://host.docker.internal:1234"
            )
            model_name = os.environ.get("LLAMA_MODEL", "local-model")
            return LocalLLMClient(endpoint=endpoint, model_name=model_name)

        elif provider == "gemini":
            try:
                from .gemini_client import GeminiLLMClient
            except ImportError:
                import importlib.util
                import os
                import sys

                client_dir = os.path.dirname(__file__)
                spec = importlib.util.spec_from_file_location(
                    "gemini_client", os.path.join(client_dir, "gemini_client.py")
                )
                gemini_mod = importlib.util.module_from_spec(spec)
                sys.modules["gemini_client"] = gemini_mod
                spec.loader.exec_module(gemini_mod)
                GeminiLLMClient = gemini_mod.GeminiLLMClient

            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError(
                    "GEMINI_API_KEY falhou. Sem API key provisionada no .env para o baseline."
                )
            if model_override:
                return GeminiLLMClient(api_key=api_key, model_name=model_override)
            return GeminiLLMClient(api_key=api_key)

        else:
            raise ValueError(
                f"Provedor LLM '{provider}' desconhecido. O baseline oficial define 'gemini'."
            )
