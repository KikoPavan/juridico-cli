#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional


@dataclass(frozen=True)
class EngineIO:
    """
    IO estritamente do conversor PDF→Markdown.
    - dir_pdf: entrada (PDFs)
    - dir_md : saída (Markdown)
    """

    dir_pdf: Path
    dir_md: Path


@dataclass
class EngineMove:
    """
    Registro de uma conversão PDF→MD.
    """

    in_pdf: Path
    out_md: Path
    stem: str
    ok: bool = True
    error: Optional[str] = None


class Engine:
    """
    Engine simples e deliberadamente restrita:
    - Lista PDFs
    - Calcula destino .md
    - Executa conversão via callback
    - Retorna relatório de execução
    """

    def __init__(self, io: EngineIO, *, limit: Optional[int] = None) -> None:
        self.io = io
        self.limit = limit if (limit and limit > 0) else None

    def list_pdfs(self) -> List[Path]:
        if not self.io.dir_pdf.exists():
            raise FileNotFoundError(
                f"Diretório de PDFs não encontrado: {self.io.dir_pdf}"
            )
        pdfs = sorted(self.io.dir_pdf.glob("*.pdf"))
        if self.limit is not None:
            pdfs = pdfs[: self.limit]
        return pdfs

    def out_md_path(self, pdf_path: Path) -> Path:
        stem = pdf_path.stem
        return (self.io.dir_md / f"{stem}.md").resolve()

    def run_batch(
        self,
        convert_one: Callable[[Path, Path], None],
        *,
        pdf_files: Optional[List[Path]] = None,
    ) -> List[EngineMove]:
        """
        convert_one(in_pdf: Path, out_md: Path) -> None
        """
        self.io.dir_md.mkdir(parents=True, exist_ok=True)

        files = pdf_files if pdf_files is not None else self.list_pdfs()
        moves: List[EngineMove] = []

        for pdf_path in files:
            out_md = self.out_md_path(pdf_path)
            mv = EngineMove(in_pdf=pdf_path, out_md=out_md, stem=pdf_path.stem)

            try:
                convert_one(pdf_path, out_md)
            except Exception as e:
                mv.ok = False
                mv.error = str(e)

            moves.append(mv)

        return moves
