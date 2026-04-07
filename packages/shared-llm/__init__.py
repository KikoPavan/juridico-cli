"""
Pacote Central Shared LLM
Garante a adoção e injeção do padrão de cliente da interface agnóstica.
"""
from .client import LLMClient, DummyLLMClient

__all__ = ['LLMClient', 'DummyLLMClient']
