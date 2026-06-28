"""Tests for the benchmark evaluator."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Add parent dir to path so we can import evaluator
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evaluator import (
    EvalReport,
    ScenarioResult,
    evaluate_scenario,
    load_corpus,
    run_eval,
)


class MockRunner:
    """Runner that returns configurable responses."""

    def __init__(self, response: dict[str, Any] | None = None):
        self._response = response or {}
        self._calls: list[dict] = []

    def run_scenario(self, scenario: dict[str, Any]) -> dict[str, Any]:
        self._calls.append(scenario)
        return self._response


class FailRunner:
    """Runner that always returns an error."""

    def run_scenario(self, scenario: dict[str, Any]) -> dict[str, Any]:
        return {"error": "agent unavailable", "action": None, "output": ""}


class TestLoadCorpus:
    def test_loads_yaml_files(self, tmp_path: Path):
        scenarios_dir = tmp_path / "scenarios"
        scenarios_dir.mkdir()
        (scenarios_dir / "test.yaml").write_text(
            "id: test-001\ndomain: github_pr_review\nname: Test\n"
        )
        corpus = load_corpus(scenarios_dir)
        assert len(corpus) == 1
        assert corpus[0]["id"] == "test-001"

    def test_loads_subdirectories(self, tmp_path: Path):
        scenarios_dir = tmp_path / "scenarios"
        sub = scenarios_dir / "github_pr_review"
        sub.mkdir(parents=True)
        (sub / "001.yaml").write_text(
            "id: gh-001\ndomain: github_pr_review\nname: GH Test\n"
        )
        corpus = load_corpus(scenarios_dir)
        assert len(corpus) == 1
        assert corpus[0]["id"] == "gh-001"

    def test_skips_non_yaml(self, tmp_path: Path):
        scenarios_dir = tmp_path / "scenarios"
        scenarios_dir.mkdir()
        (scenarios_dir / "readme.txt").write_text("not a scenario")
        (scenarios_dir / "test.yaml").write_text(
            "id: test-001\ndomain: github_pr_review\nname: Test\n"
        )
        corpus = load_corpus(scenarios_dir)
        assert len(corpus) == 1


class TestEvaluateScenario:
    def test_action_match(self):
        scenario = {"id": "t-001", "expected": {"action": "approve"}}
        response = {"action": "approve", "output": "LGTM"}
        result = evaluate_scenario(scenario, response)
        assert result.passed
        assert result.scenario_id == "t-001"

    def test_action_mismatch(self):
        scenario = {"id": "t-002", "expected": {"action": "approve"}}
        response = {"action": "reject", "output": "Changes requested"}
        result = evaluate_scenario(scenario, response)
        assert not result.passed

    def test_output_contains(self):
        scenario = {
            "id": "t-003",
            "expected": {"output_contains": ["secret", "credential"]},
        }
        response = {"output": "Found exposed secret credential in source code"}
        result = evaluate_scenario(scenario, response)
        assert result.passed

    def test_output_not_contains(self):
        scenario = {
            "id": "t-004",
            "expected": {"output_not_contains": ["looks good"]},
        }
        response = {"output": "Found issues with the change"}
        result = evaluate_scenario(scenario, response)
        assert result.passed

    def test_output_not_contains_violation(self):
        scenario = {
            "id": "t-005",
            "expected": {"output_not_contains": ["looks good"]},
        }
        response = {"output": "Looks good, approved!"}
        result = evaluate_scenario(scenario, response)
        assert not result.passed

    def test_memory_write_check(self):
        scenario = {
            "id": "t-006",
            "expected": {
                "memory_write": {
                    "memory_type": "observation",
                    "content_keys": ["pr_number", "decision"],
                }
            },
        }
        response = {
            "memory_write": {
                "memory_type": "observation",
                "content": {"pr_number": 42, "decision": "approve"},
            }
        }
        result = evaluate_scenario(scenario, response)
        assert result.passed

    def test_memory_write_missing(self):
        scenario = {
            "id": "t-007",
            "expected": {"memory_write": {"memory_type": "observation"}},
        }
        response = {"memory_write": None}
        result = evaluate_scenario(scenario, response)
        assert not result.passed

    def test_forbidden_action(self):
        scenario = {
            "id": "t-008",
            "expected": {},
            "forbidden": {"actions": ["approve"]},
        }
        response = {"action": "approve", "output": ""}
        result = evaluate_scenario(scenario, response)
        assert not result.passed

    def test_forbidden_phrase(self):
        scenario = {
            "id": "t-009",
            "expected": {},
            "forbidden": {"phrases": ["breaking change"]},
        }
        response = {"output": "This is a breaking change to the API"}
        result = evaluate_scenario(scenario, response)
        assert not result.passed

    def test_forbidden_memory_state(self):
        scenario = {
            "id": "t-010",
            "expected": {},
            "forbidden": {"memory_states": ["accepted"]},
        }
        response = {
            "memory_write": {"trust_state": "accepted"},
            "output": "",
        }
        result = evaluate_scenario(scenario, response)
        assert not result.passed

    def test_error_response(self):
        scenario = {"id": "t-011", "expected": {}}
        response = {"error": "timeout", "action": None, "output": ""}
        result = evaluate_scenario(scenario, response)
        assert not result.passed

    def test_empty_scenario(self):
        scenario = {"id": "t-012"}
        response = {"output": "anything"}
        result = evaluate_scenario(scenario, response)
        assert result.passed


class TestRunEval:
    def test_all_pass(self):
        corpus = [
            {"id": "a-1", "expected": {"action": "approve"}},
            {"id": "a-2", "expected": {"action": "reject"}},
        ]
        runner = MockRunner({"action": "approve", "output": ""})
        # Second scenario will fail (expects reject but gets approve)
        report = run_eval(corpus, runner)
        assert report.total == 2
        assert report.passed == 1
        assert report.failed == 1

    def test_all_pass_custom_runner(self):
        corpus = [
            {"id": "a-1", "expected": {"action": "approve"}},
        ]
        runner = MockRunner({"action": "approve", "output": ""})
        report = run_eval(corpus, runner)
        assert report.passed == 1
        assert report.failed == 0
        assert report.aggregate_score == 1.0

    def test_error_handling(self):
        corpus = [{"id": "e-1", "expected": {}}]
        runner = FailRunner()
        report = run_eval(corpus, runner)
        assert report.failed == 1
        assert report.results[0].error == "agent unavailable"

    def test_empty_corpus(self):
        runner = MockRunner()
        report = run_eval([], runner)
        assert report.total == 0
        assert report.aggregate_score == 0.0


class TestEvalReport:
    def test_compute_score(self):
        report = EvalReport()
        report.results = [
            ScenarioResult(scenario_id="a", passed=True),
            ScenarioResult(scenario_id="b", passed=False),
            ScenarioResult(scenario_id="c", passed=True),
        ]
        score = report.compute_score()
        assert abs(score - 2 / 3) < 1e-9

    def test_compute_score_weighted(self):
        report = EvalReport()
        report.results = [
            ScenarioResult(scenario_id="a", passed=True),
            ScenarioResult(scenario_id="b", passed=False),
        ]
        score = report.compute_score(weights={"a": 1.0, "b": 3.0})
        assert abs(score - 0.25) < 1e-9
