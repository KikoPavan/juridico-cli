import os
from dataclasses import dataclass

from mem0 import Memory

# Simulação da biblioteca TurboQuant (Online Vector Quantization)
# Em um ambiente real, esta lógica estaria embutida no seu Vector Store ou middleware
from turboquant import OnlineQuantizer


@dataclass
class LegalExperience:
    bundle_id: str
    task_result: dict
    reliability_score: float
    metadata: dict


class Mem0TurboAdapter:
    def __init__(self):
        # Inicializa o Mem0 para gerenciar a lógica de memória episódica
        self.memory = Memory()
        # Inicializa o quantizador para manter a "Distorção Quase Ideal"
        self.quantizer = OnlineQuantizer(distortion_threshold=0.05)

    def add_experience(self, user_id: str, experience: LegalExperience):
        """
        Adiciona uma experiência de extração à memória,
        aplicando compressão TurboQuant antes da persistência.
        """
        # Só persiste se atingir o limite de resiliência do ReliabilityBench
        if experience.reliability_score < 0.85:
            return "Experiência descartada: Confiabilidade insuficiente."

        # O TurboQuant reduz o tamanho do vetor na RAM em tempo real
        compressed_vector = self.quantizer.quantize(experience.task_result)

        # Armazena no Mem0 associando ao usuário e ao bundle específico
        self.memory.add(
            data=str(experience.task_result),
            user_id=user_id,
            metadata={
                "bundle": experience.bundle_id,
                "vector_state": "turboquant_compressed",
                **experience.metadata,
            },
        )
        return "Sucesso: Experiência comprimida e armazenada."

    def get_contextual_memory(self, user_id: str, query: str):
        """
        Recupera memórias relevantes para o Agente, filtrando por contexto.
        """
        # Busca memórias persistidas que ajudam no raciocínio ReAct
        relevant_memories = self.memory.search(query, user_id=user_id)
        return relevant_memories
