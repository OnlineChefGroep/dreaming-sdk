#!/usr/bin/env python3
"""CLI for dream-eval — run evaluations, check gates, score faithfulness."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from dream_eval.types import EvalMode, EvalResult


def main() -> None:
    parser = argparse.ArgumentParser(
        description="dream-eval — agent memory faithfulness evaluation"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Run a full eval pipeline")
    p_run.add_argument("--corpus", default=None, help="Path to golden corpus directory")
    p_run.add_argument("--mode", choices=["golden", "live"], default="golden")
    p_run.add_argument("--output-dir", default=None, help="Output directory for results")

    p_gates = sub.add_parser("gates", help="Run only deterministic gates")
    p_gates.add_argument("--text", default=None, help="Text to check for secret leaks")
    p_gates.add_argument("--file", default=None, help="File to check hash determinism")
    p_gates.add_argument("--hash", default=None, help="Expected hash (sha256:hex)")

    p_score = sub.add_parser("score", help="Score an eval report against labels")
    p_score.add_argument("--report", required=True, help="Path to eval-report.json")
    p_score.add_argument("--labels", default=None, help="Path to labels.json")

    p_list = sub.add_parser("list", help="List recent eval runs")
    p_list.add_argument("--limit", type=int, default=10)
    p_list.add_argument("--backend", choices=["json", "postgres"], default="json")
    p_list.add_argument("--dsn", default=None, help="Postgres DSN (for postgres backend)")

    p_show = sub.add_parser("show", help="Show a specific eval run result")
    p_show.add_argument("run_id")
    p_show.add_argument("--backend", choices=["json", "postgres"], default="json")

    args = parser.parse_args()

    if args.command == "gates":
        _run_gates(args)
    elif args.command == "run":
        _run_eval(args)
    elif args.command == "score":
        _run_score(args)
    elif args.command == "list":
        _run_list(args)
    elif args.command == "show":
        _run_show(args)


def _run_gates(args: argparse.Namespace) -> None:
    from dream_eval.gates import check_hash_determinism, check_secret_leak

    results = []

    if args.text:
        result = check_secret_leak(args.text)
        results.append(result)

    if args.file:
        result = check_hash_determinism(
            open(args.file, encoding="utf-8").read(), args.hash
        )
        results.append(result)

    if not results:
        print("No checks specified. Use --text or --file.", file=sys.stderr)
        sys.exit(1)

    for r in results:
        print(json.dumps(r.model_dump(mode="json"), default=str))

    if any(r.status.value == "fail" for r in results):
        sys.exit(1)


def _run_eval(args: argparse.Namespace) -> None:
    from pathlib import Path

    result = EvalResult(
        run_id=datetime.now().strftime("%Y-%m-%dT%H-%M-%SZ"),
        date=datetime.now(),
        mode=EvalMode(args.mode),
    )

    output_dir = args.output_dir or "eval/results"
    out_path = Path(output_dir) / result.run_id
    out_path.mkdir(parents=True, exist_ok=True)

    metrics_path = out_path / "metrics.json"
    metrics_path.write_text(
        json.dumps(result.to_metrics_dict(), indent=2, default=str),
        encoding="utf-8",
    )

    print(json.dumps({
        "run_id": result.run_id,
        "output": str(out_path),
        "hard_fail": result.hard_fail,
    }, default=str))


def _run_score(args: argparse.Namespace) -> None:
    from pathlib import Path

    from dream_eval.scoring import compute_faithfulness
    from dream_eval.types import EvalReport, Labels

    report_data = json.loads(Path(args.report).read_text(encoding="utf-8"))
    report = EvalReport.model_validate(report_data)

    labels_path = args.labels or str(
        Path(args.report).parent.parent / "golden-corpus" / "labels.json"
    )
    labels_data = json.loads(Path(labels_path).read_text(encoding="utf-8"))
    labels = Labels.model_validate(labels_data)

    faithfulness = compute_faithfulness(report.items, labels.items)
    print(json.dumps(faithfulness.model_dump(mode="json"), default=str))


def _run_list(args: argparse.Namespace) -> None:
    from dream_eval.backends import JsonFileBackend, PostgresBackend

    if args.backend == "postgres":
        backend = PostgresBackend(dsn=args.dsn)
    else:
        backend = JsonFileBackend()

    runs = backend.list_runs(limit=args.limit)
    for run in runs:
        print(json.dumps(run, default=str))


def _run_show(args: argparse.Namespace) -> None:
    from dream_eval.backends import JsonFileBackend, PostgresBackend

    if args.backend == "postgres":
        backend = PostgresBackend()
    else:
        backend = JsonFileBackend()

    report = backend.load_eval_report(args.run_id)
    if report:
        print(json.dumps(report.model_dump(mode="json"), default=str))
    else:
        print(f"Run {args.run_id} not found", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
