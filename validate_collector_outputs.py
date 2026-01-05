import json
import os
from pathlib import Path

from jsonschema import Draft7Validator, RefResolver

# Ajuste este caminho para o root do projeto, se necessário
PROJECT_ROOT = Path(__file__).resolve().parent

SCHEMAS_DIR = PROJECT_ROOT / "schemas"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Mapeia prefixos/nome de pasta para o schema correspondente
SCHEMA_MAP = {
    "cad-obr": "escritura_imovel.schema.json",
    "juntada": "juntada.schema.json",  # se existir
    "processo": "processo.schema.json",
    "contrato_social": "contrato_social.schema.json",
    "hipotecaria": "escritura_hipotecaria.schema.json",
    "procuracao": "procuracao.schema.json",
}


def load_schema(schema_name: str):
    schema_path = SCHEMAS_DIR / schema_name
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    base_uri = f"file://{SCHEMAS_DIR.as_posix()}/"
    resolver = RefResolver(base_uri=base_uri, referrer=schema)
    validator = Draft7Validator(schema, resolver=resolver)
    return validator


def choose_schema_for_file(fname: str, parent_dir: Path):
    name_lower = fname.lower()

    # 1) Heurística por nome do diretório pai
    if parent_dir.name in ("cad-obr", "cad_obr", "matriculas", "escrituras"):
        return "escritura_imovel.schema.json"
    if parent_dir.name in ("juntada", "anexos"):
        return "juntada.schema.json"
    if parent_dir.name in ("processo", "processos"):
        return "processo.schema.json"

    # 2) Heurística por nome do arquivo
    if "contrato_social" in name_lower:
        return "contrato_social.schema.json"
    if "hipotec" in name_lower:
        return "escritura_hipotecaria.schema.json"
    if "procuracao" in name_lower or "procuração" in name_lower:
        return "procuracao.schema.json"

    # 3) Nada encontrado
    return None


def iter_output_json_files():
    for root, dirs, files in os.walk(OUTPUTS_DIR):
        root_path = Path(root)
        for f in files:
            if f.endswith(".json") and not f.endswith(".error.json"):
                yield root_path, f


def main():
    print("=== Validação dos JSONs do collector-cli ===\n")

    # Cache de validators por schema
    validators = {}
    total_files = 0
    total_ok = 0
    total_errors = 0

    # Estatísticas de erros por campo
    field_error_stats = {}

    for parent_dir, fname in iter_output_json_files():
        total_files += 1
        fpath = parent_dir / fname

        schema_name = choose_schema_for_file(fname, parent_dir)
        if not schema_name:
            print(f"[AVISO] {fpath} -> Nenhum schema associado (pular)")
            continue

        if schema_name not in validators:
            try:
                validators[schema_name] = load_schema(schema_name)
                print(f"[INFO] Carregado schema: {schema_name}")
            except Exception as e:
                print(f"[ERRO] Falha ao carregar schema {schema_name}: {e}")
                continue

        validator = validators[schema_name]

        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[ERRO] Falha ao ler {fpath}: {e}")
            total_errors += 1
            continue

        errors = sorted(validator.iter_errors(data), key=lambda e: e.path)

        if not errors:
            total_ok += 1
            continue

        total_errors += 1
        print(f"\n[INVALIDO] {fpath} (schema: {schema_name})")

        for err in errors:
            # Caminho do campo (ex.: hipotecas_onus[0].tipo_divida)
            path_str = ".".join(str(p) for p in err.path) or "<root>"

            # Incrementa estatísticas por campo
            field_error_stats.setdefault(path_str, 0)
            field_error_stats[path_str] += 1

            print(f"  - Campo: {path_str}")
            print(f"    Tipo erro: {err.validator}")
            print(f"    Mensagem: {err.message}")

    print("\n=== RESUMO GERAL ===")
    print(f"Arquivos analisados: {total_files}")
    print(f"Válidos: {total_ok}")
    print(f"Inválidos: {total_errors}")

    print("\n=== TOP CAMPOS COM MAIS ERROS ===")
    for field, count in sorted(
        field_error_stats.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"  {field}: {count} ocorrência(s) de erro")


if __name__ == "__main__":
    main()
