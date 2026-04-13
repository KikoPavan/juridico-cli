import abc
from typing import List, Dict, Any

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
    def generate_structured(self, messages: List[Dict[str, str]], schema: Dict[str, Any], **kwargs) -> Any:
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

    def generate_structured(self, messages: List[Dict[str, str]], schema: Dict[str, Any], **kwargs) -> Any:
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
    def create_client(provider_override: str = None) -> 'LLMClient':
        import os
        from dotenv import load_dotenv
        
        # Garante variáveis locais (ex: .env) carregadas
        load_dotenv(override=False) 
        
        # Default blindado: Gemini como Provedor Principal do Baseline
        provider = provider_override or os.environ.get("LLM_PROVIDER", "gemini").lower()
        
        if provider == "dummy":
            return DummyLLMClient()
            
        elif provider == "gemini":
            try:
                from .gemini_client import GeminiLLMClient
            except ImportError:
                import os, sys, importlib.util
                client_dir = os.path.dirname(__file__)
                spec = importlib.util.spec_from_file_location('gemini_client', os.path.join(client_dir, 'gemini_client.py'))
                gemini_mod = importlib.util.module_from_spec(spec)
                sys.modules['gemini_client'] = gemini_mod
                spec.loader.exec_module(gemini_mod)
                GeminiLLMClient = gemini_mod.GeminiLLMClient
                
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY falhou. Sem API key provisionada no .env para o baseline.")
            return GeminiLLMClient(api_key=api_key)
            
        else:
            raise ValueError(f"Provedor LLM '{provider}' desconhecido. O baseline oficial define 'gemini'.")

