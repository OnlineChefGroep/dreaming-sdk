"""Core types for dream-eval — agent-agnostic evaluation pipeline."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class EvalMode(StrEnum):
    GOLDEN = "golden"
    LIVE = "live"


class GateStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"


class ItemOutcome(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EDITED = "edited"
    DEFERRED = "deferred"
    ROLLED_BACK = "rolled_back"


class ProposedItem(BaseModel):
    """A single item proposed by the evaluator."""

    id: str
    category: str
    content: dict[str, Any] = Field(default_factory=dict)
    recurrence: int = 1
    confidence: float = 1.0
    source_refs: list[str] = Field(default_factory=list)


class EvalReport(BaseModel):
    """Evaluator output — proposed items from transcript analysis."""

    items: list[ProposedItem] = Field(default_factory=list)
    sessions_evaluated: int = 0
    token_cost: int = 0
    latency: float = 0.0
    evaluator_version: str = "0.2.0"


class LabeledItem(BaseModel):
    """Ground truth item from labels.json (golden corpus)."""

    id: str
    category: str
    content: dict[str, Any] = Field(default_factory=dict)
    max_recurrence: int | None = None
    forbidden_patterns: list[str] = Field(default_factory=list)


class SecretLeakConfig(BaseModel):
    """Configuration for secret leak detection gate."""

    forbidden: list[str] = Field(default_factory=list)


class Labels(BaseModel):
    """Golden corpus labels file."""

    items: list[LabeledItem] = Field(default_factory=list)
    secret_leak: SecretLeakConfig = Field(default_factory=SecretLeakConfig)


class GateResult(BaseModel):
    """Result of a single deterministic gate check."""

    name: str
    status: GateStatus
    message: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class FaithfulnessReport(BaseModel):
    """Judge output — scored faithfulness metrics."""

    faithfulness_score: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    recurrence_calibration: float = 0.0
    items_proposed: int = 0
    items_fully_supported: int = 0
    items_partially_supported: int = 0
    items_unsupported: int = 0
    recurrence_violations: list[str] = Field(default_factory=list)
    specificity_flags: list[str] = Field(default_factory=list)
    redundancy_flags: list[str] = Field(default_factory=list)


class EvalResult(BaseModel):
    """Complete eval run result — gates + scoring + metadata."""

    run_id: str
    date: datetime
    mode: EvalMode
    gates: list[GateResult] = Field(default_factory=list)
    faithfulness: FaithfulnessReport = Field(default_factory=FaithfulnessReport)
    acceptance_rate: dict[str, float | None] = Field(default_factory=dict)
    regret_rate: float | None = None
    soul_version: str | None = None
    agents_md_hash_before: str | None = None
    agents_md_hash_after: str | None = None
    sessions_evaluated: int = 0
    token_cost: int = 0
    latency: float = 0.0

    @property
    def hard_fail(self) -> bool:
        return any(g.status == GateStatus.FAIL for g in self.gates)

    def to_metrics_dict(self) -> dict[str, Any]:
        """Export as canonical metrics.json format."""
        rolled_back = {
            "pref": 0,
            "workflow": 0,
            "skill": 0,
            "subagent": 0,
            "rule": 0,
        }
        gates = {g.name: g.status.value == "pass" for g in self.gates}
        return {
            "run_id": self.run_id,
            "date": self.date.isoformat(),
            "timestamp": self.date.isoformat(),
            "mode": self.mode.value,
            "sessions_evaluated": self.sessions_evaluated,
            "items_proposed": self.faithfulness.items_proposed,
            "accepted": 0,
            "rejected": 0,
            "edited": 0,
            "deferred": 0,
            "rolled_back": rolled_back,
            "acceptance_rate": self.acceptance_rate,
            "precision": self.faithfulness.precision,
            "recall": self.faithfulness.recall,
            "recurrence_calibration": self.faithfulness.recurrence_calibration,
            "faithfulness_score": self.faithfulness.faithfulness_score,
            "faithfulness": self.faithfulness.faithfulness_score,
            "secret_leak_test": self._gate_status("secret_leak"),
            "gates": gates,
            "hard_fail": self.hard_fail,
            "regret_rate": self.regret_rate,
            "token_cost": self.token_cost,
            "latency": self.latency,
            "soul_version": self.soul_version,
            "agents_md_hash_before": self.agents_md_hash_before,
            "agents_md_hash_after": self.agents_md_hash_after,
        }

    def _gate_status(self, name: str) -> str:
        for g in self.gates:
            if g.name == name:
                return g.status.value
        return "skip"
