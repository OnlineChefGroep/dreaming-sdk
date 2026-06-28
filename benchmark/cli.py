#!/usr/bin/env python3
"""dreaming-benchmark CLI — run agent workflow benchmarks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from evaluator import (
    EvalReport,
    load_corpus,
    run_eval,
)


class DryRunRunner:
    """Placeholder runner that returns generic responses for testing the framework."""

    def run_scenario(self, scenario: dict) -> dict:
        return {
            "action": scenario.get("expected", {}).get("action", "unknown"),
            "output": "Dry run — no agent connected.",
            "memory_write": None,
            "evidence_refs": [],
        }


def print_report(report: EvalReport) -> None:
    print(f"\n{'='*60}")
    print(f"Benchmark Results: {report.passed}/{report.total} passed")
    print(f"Aggregate score: {report.aggregate_score:.2%}")
    print(f"{'='*60}\n")

    for r in report.results:
        status = "PASS" if r.passed else "FAIL"
        print(f"  [{status}] {r.scenario_id}")
        if r.error:
            print(f"         ERROR: {r.error}")
        for c in r.checks:
            if not c.passed:
                print(f"         FAIL: {c.name} — {c.detail}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="dreaming-benchmark",
        description="Run agent workflow benchmarks",
    )
    sub = parser.add_subparsers(dest="command")

    # list
    list_cmd = sub.add_parser("list", help="List available scenarios")
    list_cmd.add_argument("--scenarios-dir", type=Path, default=Path("benchmark/scenarios"))
    list_cmd.add_argument("--format", choices=["table", "json"], default="table")

    # run
    run_cmd = sub.add_parser("run", help="Run benchmark corpus")
    run_cmd.add_argument("--scenarios-dir", type=Path, default=Path("benchmark/scenarios"))
    run_cmd.add_argument("--format", choices=["table", "json"], default="table")
    run_cmd.add_argument("--filter-domain", type=str, default=None)
    run_cmd.add_argument("--filter-tag", type=str, default=None)

    # show
    show_cmd = sub.add_parser("show", help="Show a single scenario")
    show_cmd.add_argument("scenario_id", type=str)
    show_cmd.add_argument("--scenarios-dir", type=Path, default=Path("benchmark/scenarios"))

    args = parser.parse_args()

    if args.command == "list":
        corpus = load_corpus(args.scenarios_dir)
        if args.format == "json":
            print(json.dumps(corpus, indent=2))
        else:
            print(f"\n{'ID':<35} {'Domain':<20} {'Difficulty':<12} {'Tags'}")
            print("-" * 90)
            for s in corpus:
                tags = ", ".join(s.get("tags", []))
                print(f"{s['id']:<35} {s['domain']:<20} {s.get('difficulty',''):<12} {tags}")
            print(f"\nTotal: {len(corpus)} scenarios\n")
        return 0

    if args.command == "show":
        corpus = load_corpus(args.scenarios_dir)
        match = [s for s in corpus if s["id"] == args.scenario_id]
        if not match:
            print(f"Scenario not found: {args.scenario_id}", file=sys.stderr)
            return 1
        print(json.dumps(match[0], indent=2))
        return 0

    if args.command == "run":
        corpus = load_corpus(args.scenarios_dir)
        if args.filter_domain:
            corpus = [s for s in corpus if s["domain"] == args.filter_domain]
        if args.filter_tag:
            corpus = [s for s in corpus if args.filter_tag in s.get("tags", [])]

        if not corpus:
            print("No scenarios matched filters.", file=sys.stderr)
            return 1

        runner = DryRunRunner()
        report = run_eval(corpus, runner)

        if args.format == "json":
            print(json.dumps({
                "total": report.total,
                "passed": report.passed,
                "failed": report.failed,
                "errors": report.errors,
                "aggregate_score": report.aggregate_score,
                "results": [
                    {
                        "scenario_id": r.scenario_id,
                        "passed": r.passed,
                        "error": r.error,
                        "failed_checks": [
                            {"name": c.name, "detail": c.detail}
                            for c in r.checks
                            if not c.passed
                        ],
                    }
                    for r in report.results
                ],
            }, indent=2))
        else:
            print_report(report)

        return 0 if report.failed == 0 else 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
