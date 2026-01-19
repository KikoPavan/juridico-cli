from __future__ import annotations

import argparse
from pathlib import Path

from evidence_pack_core import generate_pack_global


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Generate evidence pack (pack_global) from dataset_v1"
    )
    ap.add_argument("--dataset-dir", default="outputs/cad_obr/04_reconciler/dataset_v1")
    ap.add_argument(
        "--reports-dir", default="outputs/cad_obr/04_reconciler/reports/dataset_v1"
    )
    ap.add_argument("--dataset-id", default="dataset_v1")

    ap.add_argument("--duckdb", default="artifacts/db/cad_obr_dataset_v1.duckdb")
    ap.add_argument(
        "--out", default="artifacts/evidence_packs/dataset_v1/pack_global.json"
    )

    ap.add_argument("--max-findings", type=int, default=12)
    ap.add_argument("--max-support-rows", type=int, default=20)

    args = ap.parse_args()

    dataset_dir = Path(args.dataset_dir)
    reports_dir = Path(args.reports_dir)
    out_path = Path(args.out)
    duckdb_path = Path(args.duckdb) if args.duckdb else None

    pack = generate_pack_global(
        dataset_dir=dataset_dir,
        reports_dir=reports_dir,
        dataset_id=str(args.dataset_id),
        out_path=out_path,
        max_findings=int(args.max_findings),
        max_support_rows=int(args.max_support_rows),
        duckdb_path=duckdb_path,
    )

    print(f"OK: pack gerado em: {out_path}")
    if pack.get("inputs", {}).get("duckdb_path"):
        print(f"DuckDB: {pack['inputs']['duckdb_path']}")
    print(f"Pack ID: {pack.get('pack_id')}")


if __name__ == "__main__":
    main()
