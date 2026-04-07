"""
Legal document cleaner.

Core: LegalDocCleaner class.
Ported from app_streamlit/src/limpeza/clean_legal_docs.py (v2.1).
Interactive main() removed — use clean_document() or clean_batch() directly.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

import chardet


class LegalDocCleaner:
    """Intelligent cleaner for converted legal documents."""

    def __init__(self):
        # Patterns to remove
        self.patterns_to_remove = [
            # Court metadata
            r"Para conferir o original.*?código \w+\.",
            r"Este documento é cópia do original.*?número \w+\s*\.",
            r"Este documento é cópia do original.*?às \d{2}:\d{2}\s*\.",
            r"DOCUMENTO ASSINADO DIGITALMENTE.*?MARGEM DIREITA",
            r"liberado nos autos em.*?\.",
            # Repetitive headers
            r"TRIBUNAL DE JUSTIÇA DO ESTADO DE SÃO PAULO\s*",
            r"COMARCA DE CERQUEIRA CÉSAR\s*",
            r"FORO DE CERQUEIRA CÉSAR\s*",
            r"1ª VARA\s*",
            r"Rua Olimpio Pavan.*?355\.centro\.CEP\.18760-000\.Fone:\.14 - 37141014\s*",
            r"Rua Olimpio Pavan.*?17h00min\s*",
            r"Rua Olimpio Pavan.*?cerqcesar@tjsp\.jus\.br\s*",  # noqa: E501
            r"Horário de Atendimento.*?\d{2}h\d{2}min\s*",
            r"Cerqueira Cesar-SP - E-mail: cerqcesar@tjsp\.jus\.br\s*",
            # Repeated case references
            r"Processo (?:Digital )?nº:?\s*\d+-\d+\.\d+\.\d+\.\d+\.\d+\s*",
            r"Classe - Assunto.*?Imóvel\s*",
            r"Requerente:\s*Mare Agropecuaria Ltda\.\s*",
            r"Requerido:\s*(?:Juraci Pires Pavan e outro|"
            r"Francisco Carlos Pavan e outro)\s*",
            r"Juiz\(a\) de Direito:\s*Dr\(a\)\.\s*BRUNA MENDES FERREIRA\s*",
            # Page numbers and empty references
            r"fls\.\s*\d+\s*",
            r"Processo nº \d+-\d+\.\d+\.\d+\.\d+\.\d+ - p\. \d+",
            r"\(fls\.\s*\d+(?:/\d+)?\)",
            r"às fls\.\s*\d+(?:/\d+)?",
            r"\s+-\s+p\.\s+\d+\s*",
            r"\(fls?\.\s*\)",
            r"\(\s*/\d+\s*\)",
            r"\(\s*\d+/\s*\)",
            r"\(\s*\)",
            r"fls?\.\s*\d+/\d+",
            # Law firm headers (Kurtz Bruno Amarilha Zequi — repeats on every page)
            r"AV\. PINHEIRO MACHADO,?\s*\d+\s*\|\s*CENTRO\s*",
            r"CEP\s*18705[.\-]?\d*\s*\|.*?(?:wWW\.|www\.)\S+\s*",
            # Law firm footers
            r"BAGAGLI & MORENO\s*A D V O C A C I A\s*",
            r"Rua Rubens Arruda.*?advocaciabm\.com\s*",
            r"\(14\) \d+-\d+.*?advocaciabm\.com\s*",
            r"www\.advocaciabm\.com\s*",
            # Signatures
            r"GUILHERME E\. BAGAGLI\s*OAB\.SP \d+\s*",
            r"GISELE POMPILIO MORENO\s*OAB\.SP \d+\s*",
            # Whitespace normalization
            r"\n{3,}",
            r" {2,}",
        ]

        self.legal_structure_patterns = [
            r"Art(?:igo|\.)?\s*\d+",
            r"§\s*\d+",
            r"(?:Inciso\s+)?[IVX]+\s*[-–]",
            r"(?:Alínea\s+)?[a-z]\)",
            r"CLÁUSULA\s+\d+",
        ]

    def detect_encoding(self, file_path: str) -> str:
        with open(file_path, "rb") as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            return result["encoding"] or "utf-8"

    def fix_encoding(self, text: str) -> str:
        replacements = {
            "Ã£o": "ão", "Ã§Ã£o": "ção", "Ã§Ãµes": "ções", "Ã§Ã£": "çã",
            "Ã§Ãµ": "çõ", "Ã©": "é", "Ã¡": "á", "Ãº": "ú", "Ã­": "í",
            "Ã³": "ó", "Ãª": "ê", "Ã¢": "â", "Ã´": "ô", "Ã£": "ã",
            "Ãµ": "õ", "Ã§": "ç", "Ã¹": "ù",
            "Ã‰": "É", "Ãƒ": "Ã", 'Ã"': "Ó", "Ã": "Á", "Ãš": "Ú",
            "ÃŠ": "Ê", "Ã‡": "Ç",
            "DECISãO": "DECISÃO", "CONCLUSãO": "CONCLUSÃO",
            "PETIÃ‡ÃƒO": "PETIÇÃO", "OBRIGAÃ‡Ã•ES": "OBRIGAÇÕES",
            "LOCAÃ‡ÃƒO": "LOCAÇÃO",
            'â€"': "–", "â€œ": '"', "â€": '"', "â€™": "'", "â€˜": "'",
            "Â§": "§", "Âª": "ª", "Âº": "º", "Â°": "°",
            "\xa0": " ", "\u200b": "",
        }
        for wrong, correct in replacements.items():
            text = text.replace(wrong, correct)
        return text

    def remove_headers_footers(self, text: str) -> str:
        for pattern in self.patterns_to_remove:
            text = re.sub(pattern, "", text, flags=re.MULTILINE | re.IGNORECASE)
        return text

    def normalize_whitespace(self, text: str) -> str:
        text = "\n".join(line.strip() for line in text.split("\n"))
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        return text

    def preserve_legal_structure(self, text: str) -> str:
        text = re.sub(r"([^\n])(Art(?:igo|\.)?\s*\d+)", r"\1\n\n\2", text)
        text = re.sub(r"([^\n])(§\s*\d+)", r"\1\n\2", text)
        text = re.sub(r"([^\n])([IVX]+\s*[-–])", r"\1\n\2", text)
        return text

    def clean_document(self, input_path: str, output_path: str) -> Tuple[bool, str]:
        """Clean a single legal document. Returns (success, message)."""
        try:
            encoding = self.detect_encoding(input_path)
            with open(input_path, "r", encoding=encoding, errors="ignore") as f:
                text = f.read()

            text = self.fix_encoding(text)
            text = self.remove_headers_footers(text)
            text = self.preserve_legal_structure(text)
            text = self.normalize_whitespace(text)
            text = text.strip()

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)

            original_size = os.path.getsize(input_path)
            cleaned_size = os.path.getsize(output_path)
            reduction = ((original_size - cleaned_size) / original_size) * 100
            return True, f"Reduction: {reduction:.1f}%"

        except Exception as e:
            return False, f"Error: {e}"

    def clean_batch(
        self, input_folder: str, output_folder: str, *, patterns: tuple[str, ...] = ("*.txt", "*.md")
    ) -> List[Tuple[str, bool, str]]:
        """
        Clean all text/markdown files in a folder.
        Preserves the original extension in the output filename.
        Returns list of (filename, success, message).
        """
        input_path = Path(input_folder)
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)

        results = []
        seen: set[str] = set()
        for pattern in patterns:
            for src in sorted(input_path.glob(pattern)):
                if src.name in seen:
                    continue
                seen.add(src.name)
                dst = output_path / f"{src.stem}_clean{src.suffix}"
                success, message = self.clean_document(str(src), str(dst))
                results.append((src.name, success, message))
        return results
