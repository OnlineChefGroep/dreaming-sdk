#!/usr/bin/env python3
"""CLI for dream-eval — run evaluations, check gates, score faithfulness."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from dream_eval.types import EvalMode, EvalReport, EvalResult, Labels


def main() -> None:
    parser = argparse.ArgumentParser(
        description="dream-eval — agent memory faithfulness evaluation"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Run a full eval pipeline")
    p_run.add_argument("--corpus", default=None, help="Path to golden corpus directory")
    p_run.add_argument("--mode", choices=["golden", "live"], default="golden")
    p_run.add_argument("--output-dir", default=None, help="Output directory for results")
    p_run.add_argument("--eval-report", default=None, help="Path to eval-report.json")
    p_run.add_argument("--labels", default=None, help="Path to labels.json")
    p_run.add_argument("--threshold", type=float, default=0.75, help="Faithfulness threshold")
    p_run.add_argument("--fuzzy", action="store_true", help="Use fuzzy content matching")
    p_run.add_argument("--nli", action="store_true", help="Use NLI content matching")

    p_gates = sub.add_parser("gates", help="Run only deterministic gates")
    p_gates.add_argument("--text", default=None, help="Text to check for secret leaks")
    p_gates.add_argument("--file", default=None, help="File to check hash determinism")
    p_gates.add_argument("--hash", default=None, help="Expected hash (sha256:hex)")
    p_gates.add_argument("--labels", default=None, help="labels.json with secret_leak.forbidden")
    p_gates.add_argument(
        "--forbidden-pattern",
        action="append",
        default=[],
        help="Forbidden regex/literal pattern for secret leak checks",
    )

    p_score = sub.add_parser("score", help="Score an eval report against labels")
    p_score.add_argument("--report", required=True, help="Path to eval-report.json")
    p_score.add_argument("--labels", default=None, help="Path to labels.json")
    p_score.add_argument("--fuzzy", action="store_true", help="Use fuzzy content matching")
    p_score.add_argument("--nli", action="store_true", help="Use NLI content matching")

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


def _load_labels(labels_path: str | None = None, corpus_path: str | None = None) -> Labels:
    if labels_path:
        path = Path(labels_path)
    elif corpus_path:
        path = Path(corpus_path) / "labels.json"
    else:
        path = Path("eval/golden-corpus/labels.json")
    if not path.exists():
        return Labels()
    return Labels.model_validate(json.loads(path.read_text(encoding="utf-8")))


def _load_eval_report(
    report_path: str | None = None,
    corpus_path: str | None = None,
) -> EvalReport:
    candidates: list[Path] = []
    if report_path:
        candidates.append(Path(report_path))
    if corpus_path:
        base = Path(corpus_path)
        candidates.extend([base / "eval-report.json", base / "report.json"])

    for path in candidates:
        if path.exists():
            return EvalReport.model_validate(json.loads(path.read_text(encoding="utf-8")))

    return EvalReport()


def _run_gates(args: argparse.Namespace) -> None:
    from dream_eval.gates import check_hash_determinism, check_secret_leak

    results = []
    labels = _load_labels(args.labels) if args.labels else Labels()
    forbidden = [*labels.secret_leak.forbidden, *args.forbidden_pattern]

    if args.text:
        result = check_secret_leak(args.text, forbidden or None)
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
    from dream_eval.backends import JsonFileBackend
    from dream_eval.gates import check_secret_leak
    from dream_eval.scoring import compute_faithfulness

    output_dir = args.output_dir or "eval/results"
    backend = JsonFileBackend(output_dir)
    labels = _load_labels(args.labels, args.corpus)
    report = _load_eval_report(args.eval_report, args.corpus)

    report_text = json.dumps(report.model_dump(mode="json"), default=str)
    gates = [check_secret_leak(report_text, labels.secret_leak.forbidden or None)]
    faithfulness = compute_faithfulness(
        report.items,
        labels.items,
        fuzzy=args.fuzzy,
        nli=args.nli,
    )

    if faithfulness.faithfulness_score < args.threshold:
        faithfulness.specificity_flags.append(
            "faithfulness below threshold: "
            f"{faithfulness.faithfulness_score:.3f} < {args.threshold:.3f}"
        )

    now = datetime.now(timezone.utc)
    result = EvalResult(
        run_id=now.strftime("%Y-%m-%dT%H-%M-%SZ"),
        date=now,
        mode=EvalMode(args.mode),
        gates=gates,
        faithfulness=faithfulness,
        sessions_evaluated=report.sessions_evaluated,
        token_cost=report.token_cost,
        latency=report.latency,
    )

    backend.save_eval_result(result)

    print(
        json.dumps(
            {
                "run_id": result.run_id,
                "output": str(Path(output_dir) / result.run_id),
                "hard_fail": result.hard_fail,
                "faithfulness_score": faithfulness.faithfulness_score,
                "items_proposed": faithfulness.items_proposed,
            },
            default=str,
        )
    )

    if result.hard_fail:
        sys.exit(1)


def _run_score(args: argparse.Namespace) -> None:
    from dream_eval.scoring import compute_faithfulness

    report_data = json.loads(Path(args.report).read_text(encoding="utf-8"))
    report = EvalReport.model_validate(report_data)

    labels_path = args.labels or str(
        Path(args.report).parent.parent / "golden-corpus" / "labels.json"
    )
    labels_data = json.loads(Path(labels_path).read_text(encoding="utf-8"))
    labels = Labels.model_validate(labels_data)

    faithfulness = compute_faithfulness(
        report.items,
        labels.items,
        fuzzy=args.fuzzy,
        nli=args.nli,
    )
    print(json.dumps(faithfulness.model_dump(mode="json"), default=str))


def _run_list(args: argparse.Namespace) -> None:
    from dream_eval.backends import JsonFileBackend, PostgresBackend

    if args.backend == "postgres":
        backend = PostgresBackend(dsn=args.dsn)
    else:
        backend = JsonFileBackend()

    runs = backend.list_runs(limit=args.limit)
    for run in runs:
        safe_run = dict(run)
        if "secret_leak" in safe_run:
            safe_run["secret_leak"] = "[REDACTED]"
        print(json.dumps(safe_run, default=str))


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
