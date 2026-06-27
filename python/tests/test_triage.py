"""Tests for dreaming-memory triage module."""

from dreaming_memory.triage import _PRIORITY_NAME, _needs_triage, classify


def test_classify_urgent():
    result = classify("urgent: system down", None)
    assert result.priority == 1
    assert "urgent" in result.labels
    assert result.area == "incident"


def test_classify_bug():
    result = classify("bug: login fails", None)
    assert result.priority == 2
    assert "bug" in result.labels
    assert result.area == "bug"


def test_classify_docs():
    result = classify("update documentation", None)
    assert result.priority == 4
    assert "docs" in result.labels


def test_classify_default():
    result = classify("general task", None)
    assert result.priority == 3  # default medium


def test_classify_research():
    result = classify("onderzoek: new approach", None)
    assert result.priority == 3
    assert "research" in result.labels


def test_classify_infra():
    result = classify("deploy docker container", None)
    assert result.area == "infra"


def test_classify_agent():
    result = classify("memory agent improvement", None)
    assert result.area == "agent"


def test_classify_observability():
    result = classify("add metrics dashboard", None)
    assert result.area == "observability"


def test_needs_triage_unstarted():
    issue = {"state": {"type": "unstarted"}, "priority": 0, "labels": {"nodes": []}}
    assert _needs_triage(issue) is True


def test_needs_triage_with_priority():
    issue = {"state": {"type": "triage"}, "priority": 2, "labels": {"nodes": []}}
    assert _needs_triage(issue) is True


def test_needs_triage_complete():
    issue = {"state": {"type": "completed"}, "priority": 2, "labels": {"nodes": [{"id": "1"}]}}
    assert _needs_triage(issue) is False


def test_priority_name_mapping():
    assert _PRIORITY_NAME[0] == "none"
    assert _PRIORITY_NAME[1] == "urgent"
    assert _PRIORITY_NAME[4] == "low"
