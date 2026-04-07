"""Unit tests for rule_analysis/analisador_de_regras.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_processing.rule_analysis.analisador_de_regras import GeradorDeRegras


def test_analisar_diretorio_empty_folder(tmp_path):
    g = GeradorDeRegras()
    result = g.analisar_diretorio(str(tmp_path))
    assert result is None


def test_analisar_diretorio_finds_repeated_phrases(tmp_path):
    repeated = "Esta frase é repetida várias vezes nos documentos do processo"
    for i in range(3):
        f = tmp_path / f"doc{i}.txt"
        f.write_text(f"Intro.\n{repeated}\nFim.\n", encoding="utf-8")

    g = GeradorDeRegras(min_ocorrencias=2, min_comprimento=20)
    result = g.analisar_diretorio(str(tmp_path))
    assert result is not None
    assert len(result) > 0
    texts = [g._normalizado_para_original.get(phrase, "") for phrase, _ in result]
    assert any(repeated.lower()[:30] in t.lower() for t in texts)


def test_gerar_arquivo_regras_creates_file(tmp_path):
    g = GeradorDeRegras()
    fake_phrases = [("frase normalizada um dois tres", 3)]
    g._normalizado_para_original["frase normalizada um dois tres"] = "Frase Normalizada Um Dois Tres"
    out = tmp_path / "regras.txt"
    g.gerar_arquivo_regras(fake_phrases, str(out))
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "Frase Normalizada" in content


def test_gerar_arquivo_regras_empty_does_not_create(tmp_path):
    g = GeradorDeRegras()
    out = tmp_path / "regras.txt"
    g.gerar_arquivo_regras([], str(out))
    assert not out.exists()
