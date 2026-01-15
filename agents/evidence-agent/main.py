import argparse
import json
import sys

from graph import create_reconciler_graph


def main():
    parser = argparse.ArgumentParser(description="Juridico Reconciler Agent CLI")
    parser.add_argument(
        "--property", required=True, help="Target Property ID (e.g. matricula:7013)"
    )
    parser.add_argument("--hypothesis", help="Hypothesis to investigate", default="")
    args = parser.parse_args()

    print(f"--- Reconciler Agent V2 ---")
    print(f"Target: {args.property}")

    # setup inputs
    inputs = {
        "case_id": "auto_run",
        "target_property": args.property,
        "hypothesis": args.hypothesis,
        "evidence": {},
    }

    # Run Graph
    try:
        app = create_reconciler_graph()
        result = app.invoke(inputs)

        # Output Summary
        evidence = result.get("evidence", {})
        print("\n--- Execution Complete ---")
        print(f"Facts Found: {len(evidence.get('facts', []))}")
        print(f"Snippets Found: {len(evidence.get('snippets', []))}")

        # Dump full result to stdout for inspection (or pipe to file)
        # print(json.dumps(result, default=str, indent=2))

    except Exception as e:
        print(f"Error executing graph: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
