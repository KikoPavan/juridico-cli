"""
Structural rule analyzer for legal documents.

Core: GeradorDeRegras class.
Ported from pdf_legal_br/analisador_de_regras.py.
Standalone __main__ block removed — use GeradorDeRegras directly.
"""

import re
from collections import Counter
from pathlib import Path
from typing import List, Optional, Tuple


class GeradorDeRegras:
    """
    Analyzes a directory of .txt files to find repeated phrases
    and generate suggested cleaning rules.
    """

    def __init__(self, min_ocorrencias: int = 2, min_comprimento: int = 20) -> None:
        self.min_ocorrencias = min_ocorrencias
        self.min_comprimento = min_comprimento
        self._normalizado_para_original: dict[str, str] = {}

    def _normalizar_frase(self, frase: str) -> str:
        frase_norm = frase.lower()
        frase_norm = re.sub(r"[^\w\sáàâãéèêíïóôõöúçñ]", "", frase_norm)
        frase_norm = re.sub(r"\s+", " ", frase_norm).strip()
        return frase_norm

    def analisar_diretorio(
        self, diretorio_entrada: str, *, patterns: tuple[str, ...] = ("**/*.txt", "**/*.md")
    ) -> Optional[List[Tuple[str, int]]]:
        """
        Analyze all .txt and .md files in a directory to find repeated phrases.
        Returns a list of (normalized_phrase, count) sorted by frequency descending,
        or None if no files were found.
        """
        dir_path = Path(diretorio_entrada)
        seen: set[Path] = set()
        arquivos_txt: list[Path] = []
        for pat in patterns:
            for p in dir_path.glob(pat):
                if p not in seen:
                    seen.add(p)
                    arquivos_txt.append(p)

        if not arquivos_txt:
            return None

        todas_frases: list[str] = []
        for arquivo in arquivos_txt:
            try:
                text = arquivo.read_text(encoding="utf-8")
                for frase in text.split("\n"):
                    frase_strip = frase.strip()
                    if len(frase_strip) >= self.min_comprimento:
                        frase_norm = self._normalizar_frase(frase_strip)
                        if frase_norm:
                            todas_frases.append(frase_norm)
                            self._normalizado_para_original[frase_norm] = frase_strip
            except Exception as e:
                print(f"Warning: could not read {arquivo.name}: {e}")

        contador = Counter(todas_frases)
        frases_repetidas = {
            frase: count
            for frase, count in contador.items()
            if count >= self.min_ocorrencias
        }
        return sorted(frases_repetidas.items(), key=lambda item: item[1], reverse=True)

    def gerar_arquivo_regras(
        self, frases_ordenadas: List[Tuple[str, int]], caminho_saida: str
    ) -> None:
        """Write a proposed cleaning rules file for manual review."""
        if not frases_ordenadas:
            return

        with open(caminho_saida, "w", encoding="utf-8") as f:
            f.write("# PROPOSED CLEANING RULES\n")
            f.write("# Review and remove lines that should NOT be cleaned.\n")
            f.write("# Each line represents text that will be removed from documents.\n\n")

            for frase_norm, count in frases_ordenadas:
                texto_original = self._normalizado_para_original.get(frase_norm)
                if texto_original:
                    f.write(f"# [Found {count} times]\n")
                    f.write(f"{texto_original}\n\n")
