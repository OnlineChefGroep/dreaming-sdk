"""Benchmark evaluator — runs scenario corpus against agents and reports results."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import yaml


@dataclass
class ScenarioResult:
    scenario_id: str
    passed: bool
    checks: list[CheckResult] = field(default_factory=list)
    error: str | None = None


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class EvalReport:
    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    results: list[ScenarioResult] = field(default_factory=list)
    aggregate_score: float = 0.0

    def compute_score(self, weights: dict[str, float] | None = None) -> float:
        if not self.results:
            return 0.0
        total_weight = 0.0
        weighted_sum = 0.0
        for r in self.results:
            w = (weights or {}).get(r.scenario_id, 1.0)
            weighted_sum += w * (1.0 if r.passed else 0.0)
            total_weight += w
        self.aggregate_score = weighted_sum / total_weight if total_weight else 0.0
        return self.aggregate_score


class AgentRunner(Protocol):
    """Protocol for something that can run a benchmark scenario."""

    def run_scenario(
        self, scenario: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute scenario and return agent response dict.

        Returns:
            {
                "action": str | None,
                "output": str,
                "memory_write": dict | None,
                "evidence_refs": list[str],
            }
        """
        ...


def load_corpus(scenarios_dir: Path) -> list[dict[str, Any]]:
    """Load all YAML scenario files from a directory tree."""
    scenarios: list[dict[str, Any]] = []
    for yaml_file in sorted(scenarios_dir.rglob("*.yaml")):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict) and "id" in data:
            scenarios.append(data)
    return scenarios


def evaluate_scenario(
    scenario: dict[str, Any],
    agent_response: dict[str, Any],
) -> ScenarioResult:
    """Evaluate a single agent response against scenario expectations."""
    sid = scenario["id"]
    expected = scenario.get("expected", {})
    forbidden = scenario.get("forbidden", {})
    checks: list[CheckResult] = []

    # Check action
    exp_action = expected.get("action")
    if exp_action:
        actual_action = agent_response.get("action", "")
        checks.append(CheckResult(
            name="action_match",
            passed=actual_action == exp_action,
            detail=f"expected={exp_action!r}, got={actual_action!r}",
        ))

    # Check output contains
    output = agent_response.get("output", "")
    for phrase in expected.get("output_contains", []):
        checks.append(CheckResult(
            name=f"contains:{phrase[:40]}",
            passed=phrase.lower() in output.lower(),
            detail=f"looking for {phrase!r} in output",
        ))

    # Check output not contains
    for phrase in expected.get("output_not_contains", []):
        checks.append(CheckResult(
            name=f"not_contains:{phrase[:40]}",
            passed=phrase.lower() not in output.lower(),
            detail=f"must not contain {phrase!r}",
        ))

    # Check memory write
    exp_memory = expected.get("memory_write")
    if exp_memory:
        actual_memory = agent_response.get("memory_write")
        if actual_memory is None:
            checks.append(CheckResult(
                name="memory_write",
                passed=False,
                detail="expected memory write but got none",
            ))
        else:
            if exp_memory.get("memory_type"):
                checks.append(CheckResult(
                    name="memory_type",
                    passed=actual_memory.get("memory_type") == exp_memory["memory_type"],
                    detail=f"expected type={exp_memory['memory_type']}",
                ))
            for key in exp_memory.get("content_keys", []):
                checks.append(CheckResult(
                    name=f"content_key:{key}",
                    passed=key in actual_memory.get("content", {}),
                    detail=f"content must have key {key!r}",
                ))

    # Check evidence refs
    exp_refs = expected.get("evidence_refs", [])
    actual_refs = agent_response.get("evidence_refs", [])
    for ref in exp_refs:
        checks.append(CheckResult(
            name=f"evidence_ref:{ref[:40]}",
            passed=ref in actual_refs,
            detail=f"expected evidence ref {ref!r}",
        ))

    # Check forbidden actions
    for action in forbidden.get("actions", []):
        checks.append(CheckResult(
            name=f"forbidden_action:{action[:40]}",
            passed=action != agent_response.get("action"),
            detail=f"action {action!r} is forbidden",
        ))

    # Check forbidden phrases
    for phrase in forbidden.get("phrases", []):
        checks.append(CheckResult(
            name=f"forbidden_phrase:{phrase[:40]}",
            passed=phrase.lower() not in output.lower(),
            detail=f"phrase {phrase!r} is forbidden",
        ))

    # Check forbidden memory states
    for state in forbidden.get("memory_states", []):
        actual_state = (
            agent_response.get("memory_write", {}).get("trust_state")
            if agent_response.get("memory_write")
            else None
        )
        checks.append(CheckResult(
            name=f"forbidden_state:{state}",
            passed=actual_state != state,
            detail=f"memory state {state!r} is forbidden",
        ))

    all_passed = all(c.passed for c in checks) if checks else True
    has_error = agent_response.get("error") is not None

    return ScenarioResult(
        scenario_id=sid,
        passed=all_passed and not has_error,
        checks=checks,
        error=agent_response.get("error"),
    )


def run_eval(
    corpus: list[dict[str, Any]],
    runner: AgentRunner,
) -> EvalReport:
    """Run full eval corpus through an agent runner."""
    report = EvalReport(total=len(corpus))
    for scenario in corpus:
        try:
            response = runner.run_scenario(scenario)
            result = evaluate_scenario(scenario, response)
        except Exception as e:
            result = ScenarioResult(
                scenario_id=scenario["id"],
                passed=False,
                error=str(e),
            )
            report.errors += 1
        report.results.append(result)
        if result.passed:
            report.passed += 1
        else:
            report.failed += 1
    report.compute_score()
    return report
