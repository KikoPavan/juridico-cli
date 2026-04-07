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
