import json
from pathlib import Path

# Ajuste estes diretórios para o seu caso:
# ex.: outputs/old/ e outputs/new/ ou outro layout que você escolher
OLD_DIR = Path("outputs/old")  # versões anteriores
NEW_DIR = Path("outputs/new")  # versões novas

# Campos que queremos monitorar
FIELDS_TO_CHECK = [
    "quitada",
    "cancelada",
    "detalhes_baixa",
    "averbacao_baixa",
    "data_baixa",
]


def load_json(path: Path):
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERRO] Falha ao ler {path}: {e}")
        return None


def index_hipotecas_by_registro(data: dict):
    """
    Cria um índice {registro_ou_averbacao: item} para a lista hipotecas_onus.
    Ignora entradas sem 'registro_ou_averbacao'.
    """
    idx = {}
    hipos = data.get("hipotecas_onus") or []
    if not isinstance(hipos, list):
        return idx

    for item in hipos:
        reg = item.get("registro_ou_averbacao")
        if not reg:
            continue
        idx[str(reg)] = item
    return idx


def value_str(v):
    """Normaliza valor para string de comparação/debug."""
    if v is None:
        return "null"
    return repr(v)


def compare_fields(old_item: dict, new_item: dict, registro: str, file_name: str):
    """
    Compara FIELDS_TO_CHECK entre old_item e new_item.
    Imprime apenas quando há 'regressão' ou inconsistência relevante:
      - antes: true, agora: false/null
      - antes: texto preenchido, agora: vazio/null
      - mudanças suspeitas em data/averbação de baixa
    """
    inconsistencias = []

    for field in FIELDS_TO_CHECK:
        old_val = old_item.get(field)
        new_val = new_item.get(field)

        # Igual -> nada a sinalizar
        if old_val == new_val:
            continue

        # Regressões booleanas
        if field in ("quitada", "cancelada"):
            if old_val is True and (new_val is False or new_val is None):
                inconsistencias.append(
                    f"{field}: antes=True, agora={value_str(new_val)}"
                )

        # Regressões textuais: antes tinha texto, agora virou null/vazio
        if field in ("detalhes_baixa", "averbacao_baixa", "data_baixa"):
            if (
                isinstance(old_val, str)
                and old_val.strip()
                and not (isinstance(new_val, str) and new_val.strip())
            ):
                inconsistencias.append(
                    f"{field}: antes={value_str(old_val)}, agora={value_str(new_val)}"
                )

        # Mudanças suspeitas (ex.: data/averbação trocadas)
        if (
            field in ("averbacao_baixa", "data_baixa")
            and old_val
            and new_val
            and old_val != new_val
        ):
            inconsistencias.append(
                f"{field}: mudou de {value_str(old_val)} para {value_str(new_val)}"
            )

    if inconsistencias:
        print(f"\n[INCONSISTENCIA] arquivo={file_name}, registro={registro}")
        for msg in inconsistencias:
            print("  -", msg)


def process_file_pair(old_path: Path, new_path: Path):
    old_data = load_json(old_path)
    new_data = load_json(new_path)
    if old_data is None or new_data is None:
        return

    old_idx = index_hipotecas_by_registro(old_data)
    new_idx = index_hipotecas_by_registro(new_data)

    # Só compara registros que existem em ambos
    for registro, old_item in old_idx.items():
        new_item = new_idx.get(registro)
        if not new_item:
            continue
        compare_fields(old_item, new_item, registro, new_path.name)


def main():
    print("=== Diff de hipotecas_onus (versões antigas vs novas) ===\n")

    if not OLD_DIR.exists() or not NEW_DIR.exists():
        print(
            f"[ERRO] Ajuste OLD_DIR ({OLD_DIR}) e NEW_DIR ({NEW_DIR}) para diretórios existentes."
        )
        return

    # Estratégia simples: parear arquivos pelo nome base
    old_files = {p.name: p for p in OLD_DIR.rglob("*.json")}
    new_files = {p.name: p for p in NEW_DIR.rglob("*.json")}

    common_names = sorted(set(old_files.keys()) & set(new_files.keys()))

    if not common_names:
        print(
            "[AVISO] Nenhum par de arquivos em comum encontrado entre OLD_DIR e NEW_DIR."
        )
        return

    for name in common_names:
        old_path = old_files[name]
        new_path = new_files[name]
        process_file_pair(old_path, new_path)

    print("\n=== Fim do diff ===")


if __name__ == "__main__":
    main()
