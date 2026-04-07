class ExperienceRewriter:
    def rewrite_for_memory(self, task_result):
        """
        Transforma o output bruto em uma 'lição aprendida' concisa.
        Reduz ruído para otimizar a quantização vetorial.
        """
        # Exemplo: Remove campos nulos e formata como string densa
        essential_data = {k: v for k, v in task_result.items() if v is not None}
        return f"Aprendizado de Extração: {essential_data}"
