"""Lightweight rule-based auto-triage for Linear issues.

Classifies untriaged issues into priority + labels + area, logs the decision to
agent_memory (Postgres SSOT), and optionally applies the result back to Linear.

Rules are deliberately transparent and dependency-free (dev phase). Swap in an
LLM classifier later by replacing `classify()`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from cursor_dreaming_memory.integrations.linear import LinearClient, LinearMemoryBridge
from cursor_dreaming_memory.session import SessionContext
from cursor_dreaming_memory.store.postgres import AgentMemoryStore
from cursor_dreaming_memory.types import MemoryRecord, MemorySource, MemoryType, SessionType

# Linear priority: 0=none 1=urgent 2=high 3=medium 4=low
_PRIORITY_NAME = {0: "none", 1: "urgent", 2: "high", 3: "medium", 4: "low"}

# Ordered rules: (compiled regex, priority_or_None, labels, area)
_RULES: list[tuple[re.Pattern[str], int | None, tuple[str, ...], str | None]] = [
    (re.compile(r"\b(p0|urgent|blocker|down|outage|security|breach|data ?loss)\b", re.I),
     1, ("urgent",), "incident"),
    (re.compile(r"\b(bug|error|fail(ed|ure)?|crash|regression|broken|fix)\b", re.I),
     2, ("bug",), "bug"),
    (re.compile(r"\b(observability|metrics?|dashboard|monitor|logging|trace|telemetry)\b", re.I),
     None, ("observability",), "observability"),
    (re.compile(r"\b(agent|memory|llm|rag|prompt|eval)\b", re.I),
     None, ("agent",), "agent"),
    (re.compile(r"\b(onderzoek|research|spike|investigate|explore|poc)\b", re.I),
     3, ("research",), "research"),
    (re.compile(r"\b(infra|deploy|docker|postgres|oci|cloudflare|terraform|ci/?cd)\b", re.I),
     None, ("infra",), "infra"),
    (re.compile(r"\b(docs?|documentation|runbook|readme)\b", re.I),
     4, ("docs",), "docs"),
]


@dataclass
class TriageResult:
    issue_id: str
    identifier: str
    title: str
    priority: int
    labels: list[str] = field(default_factory=list)
    area: str | None = None
    rationale: str = ""

    def to_content(self) -> dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "identifier": self.identifier,
            "title": self.title,
            "priority": self.priority,
            "priority_name": _PRIORITY_NAME.get(self.priority, str(self.priority)),
            "labels": self.labels,
            "area": self.area,
            "rationale": self.rationale,
        }


def classify(title: str, description: str | None) -> TriageResult:
    """Rule-based classification. Returns a TriageResult without issue ids set."""
    text = f"{title}\n{description or ''}"
    labels: list[str] = []
    areas: list[str] = []
    priority: int | None = None
    hits: list[str] = []
    for pattern, prio, rule_labels, area in _RULES:
        if pattern.search(text):
            hits.append(pattern.pattern.split("\\b")[1] if "\\b" in pattern.pattern else "match")
            if prio is not None and (priority is None or prio < priority):
                priority = prio
            for lb in rule_labels:
                if lb not in labels:
                    labels.append(lb)
            if area and area not in areas:
                areas.append(area)
    if priority is None:
        priority = 3  # default medium
    rationale = (
        f"Auto-triage: priority={_PRIORITY_NAME[priority]}, "
        f"labels={labels or ['-']}, area={areas[0] if areas else '-'}"
    )
    return TriageResult(
        issue_id="",
        identifier="",
        title=title,
        priority=priority,
        labels=labels,
        area=areas[0] if areas else None,
        rationale=rationale,
    )


def _needs_triage(issue: dict[str, Any]) -> bool:
    state_type = (issue.get("state") or {}).get("type", "")
    has_labels = bool(issue.get("labels", {}).get("nodes"))
    no_priority = issue.get("priority", 0) in (0, None)
    return state_type in {"triage", "backlog", "unstarted"} and (no_priority or not has_labels)


class AutoTriage:
    """Triage untriaged Linear issues into the memory SSOT (+ optional apply)."""

    def __init__(
        self,
        store: AgentMemoryStore | None = None,
        client: LinearClient | None = None,
    ) -> None:
        self.store = store or AgentMemoryStore()
        self.client = client or LinearClient()
        self.bridge = LinearMemoryBridge(self.store, self.client)

    def run(
        self,
        *,
        state: str | None = None,
        limit: int = 50,
        apply: bool = False,
        comment: bool = False,
    ) -> list[TriageResult]:
        issues = self.client.list_issues(state=state, limit=limit)
        label_map = self.client.team_labels() if apply else {}
        results: list[TriageResult] = []
        ctx = SessionContext(
            session_id="auto-triage",
            session_type=SessionType.CURSOR,
            agent_id="auto-triage",
        )
        for issue in issues:
            if state is None and not _needs_triage(issue):
                continue
            res = classify(issue["title"], issue.get("description"))
            res.issue_id = issue["id"]
            res.identifier = issue["identifier"]

            self.store.write(
                MemoryRecord(
                    agent_id=ctx.agent_id,
                    session_id=ctx.session_id,
                    session_type=ctx.session_type,
                    memory_type=MemoryType.DECISION,
                    source=MemorySource.LINEAR,
                    content=res.to_content(),
                    metadata={"triage": True, "linear_issue_id": issue["id"]},
                )
            )

            if apply:
                existing = [n["id"] for n in issue.get("labels", {}).get("nodes", [])]
                new_ids = [label_map[lb] for lb in res.labels if lb in label_map]
                merged = list(dict.fromkeys(existing + new_ids))
                self.client.update_issue(
                    issue["identifier"], priority=res.priority, label_ids=merged
                )
                if comment:
                    self.client.add_comment(
                        issue["identifier"], f"[auto-triage] {res.rationale}"
                    )
            results.append(res)
        return results
