import json
import logging
from typing import List, Dict, Any
try:
    from .client import LLMClient
except ImportError:
    import sys
    client_mod = sys.modules.get('client_mod')
    LLMClient = client_mod.LLMClient if client_mod else object
from google import genai
from google.genai import types
from google.genai.errors import APIError

logger = logging.getLogger(__name__)

class GeminiLLMClient(LLMClient):
    """
    Integração real via google-genai SDK.
    Baseline para inferência esquemática estruturada (fail-fast architecture).
    """
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key)

    def generate_text(self, messages: List[Dict[str, str]], **kwargs) -> str:
        contents = self._format_messages(messages)
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            return response.text
        except APIError as e:
            logger.error(f"Erro na API Gemini: {str(e)}")
            raise RuntimeError(f"Erro na API Gemini: {str(e)}")

    def generate_structured(self, messages: List[Dict[str, str]], schema: Dict[str, Any], **kwargs) -> Any:
        contents = self._format_messages(messages)
        
        normalized_schema = self._normalize_schema(schema)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    # Passagem local usando subset JSON Schema restrito para compilar o JSON
                    response_json_schema=normalized_schema,
                    temperature=0.0
                )
            )
            
            raw_text = response.text
            if not raw_text:
                raise ValueError("Gemini retornou um conteúdo vazio.")
                
            # Validando conformidade json local
            try:
                return json.loads(raw_text)
            except json.JSONDecodeError as decode_err:
                raise ValueError(f"Output corrompido, não aderente a payload JSON: {str(decode_err)}")
                
        except APIError as e:
            raise RuntimeError(f"API Gemini falhou (Verifique Rate Limits/Auth/Schema mismatch): {str(e)}")

    def _normalize_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza, faz inline em $refs externos ('defs/common.schema.json#/$defs/...')
        e sanitiza o schema para o subconjunto OpenAPI/JSONSchema suportado pelo Gemini:
        - Remove $schema, $id, unevaluatedProperties
        - Converte 'const' em 'enum' + 'type'
        """
        import copy
        import os
        import json
        
        normalized = copy.deepcopy(schema)
        
        # Resolve 'common.schema.json' fisicamente na árvore raiz
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        common_path = os.path.join(base_dir, 'packages', 'shared-schemas', 'defs', 'common.schema.json')
        
        common_defs = {}
        if os.path.exists(common_path):
            with open(common_path, 'r', encoding='utf-8') as f:
                common_schema = json.load(f)
                common_defs = common_schema.get("$defs", {})
        else:
            logger.warning(f"Shared schema não encontrado fisicamente: {common_path}")
            
        if "$defs" not in normalized:
            normalized["$defs"] = {}
            
        for k, v in common_defs.items():
            if k in normalized["$defs"]:
                local_def = normalized["$defs"][k]
                # Se for mero alias apontando pro common.schema, sobrescrevemos com o corpo real
                if isinstance(local_def, dict) and "$ref" in local_def and "common.schema.json" in str(local_def.get("$ref", "")):
                    normalized["$defs"][k] = v
            else:
                normalized["$defs"][k] = v
                
        def _sanitize_and_rewrite(node):
            if isinstance(node, dict):
                # Remove chaves incompatíveis com o subset Gemini
                for key in ["$schema", "$id", "unevaluatedProperties"]:
                    node.pop(key, None)
                    
                # Converte const para enum
                if "const" in node:
                    const_val = node.pop("const")
                    node["enum"] = [const_val]
                    if "type" not in node:
                        node["type"] = "string" if isinstance(const_val, str) else type(const_val).__name__
                        
                if "anyOf" in node:
                    # Gemini OpenAPI não lida bem com top-level anyOf exigindo subsets.
                    # Se for array de requirements, vamos remover
                    if isinstance(node["anyOf"], list) and all("required" in item for item in node["anyOf"]):
                        node.pop("anyOf")
                
                if "$ref" in node and isinstance(node["$ref"], str):
                    ref_str = node["$ref"]
                    if "defs/common.schema.json#/$defs/" in ref_str:
                        key = ref_str.split("#/$defs/")[-1]
                        node["$ref"] = f"#/$defs/{key}"
                        
                # Recursão
                for k, v in list(node.items()):
                    if isinstance(v, dict) or isinstance(v, list):
                        _sanitize_and_rewrite(v)
                        
            elif isinstance(node, list):
                for item in node:
                    _sanitize_and_rewrite(item)

        _sanitize_and_rewrite(normalized)
        return normalized


    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        # Prepara conteudo condensado para basic baseline fallback.
        combined = []
        for msg in messages:
            role = msg.get("role", "user").upper()
            content = msg.get("content", "")
            combined.append(f"[{role}]\n{content}\n")
            
        return "\n".join(combined)
