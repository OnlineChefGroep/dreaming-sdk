"""Tests for dream-eval types."""

from dream_eval.types import (
    EvalMode,
    EvalReport,
    EvalResult,
    FaithfulnessReport,
    GateResult,
    GateStatus,
    ItemOutcome,
    LabeledItem,
    Labels,
    ProposedItem,
)


def test_proposed_item_defaults():
    item = ProposedItem(id="a", category="pref")
    assert item.content == {}
    assert item.recurrence == 1
    assert item.confidence == 1.0
    assert item.source_refs == []


def test_labeled_item_defaults():
    item = LabeledItem(id="a", category="pref")
    assert item.content == {}
    assert item.max_recurrence is None
    assert item.forbidden_patterns == []


def test_labels_defaults():
    labels = Labels()
    assert labels.items == []
    assert labels.secret_leak.forbidden == []


def test_eval_report_defaults():
    report = EvalReport()
    assert report.items == []
    assert report.sessions_evaluated == 0


def test_gate_result_model():
    result = GateResult(name="test", status=GateStatus.PASS, message="ok")
    assert result.name == "test"
    assert result.details == {}


def test_faithfulness_report_defaults():
    report = FaithfulnessReport()
    assert report.faithfulness_score == 0.0
    assert report.items_proposed == 0
    assert report.recurrence_violations == []


def test_eval_result_hard_fail_true():
    result = EvalResult(
        run_id="r1",
        date="2026-01-01",
        mode=EvalMode.GOLDEN,
        gates=[GateResult(name="x", status=GateStatus.FAIL)],
    )
    assert result.hard_fail is True


def test_eval_result_hard_fail_false():
    result = EvalResult(
        run_id="r1",
        date="2026-01-01",
        mode=EvalMode.GOLDEN,
        gates=[GateResult(name="x", status=GateStatus.PASS)],
    )
    assert result.hard_fail is False


def test_eval_result_no_gates():
    result = EvalResult(
        run_id="r1", date="2026-01-01", mode=EvalMode.GOLDEN
    )
    assert result.hard_fail is False


def test_eval_result_to_metrics_dict():
    result = EvalResult(
        run_id="r1",
        date="2026-01-01",
        mode=EvalMode.GOLDEN,
        faithfulness=FaithfulnessReport(
            faithfulness_score=0.8,
            precision=0.9,
            recall=0.7,
            recurrence_calibration=1.0,
            items_proposed=5,
        ),
        gates=[GateResult(name="secret_leak", status=GateStatus.PASS)],
    )
    m = result.to_metrics_dict()
    assert m["run_id"] == "r1"
    assert m["faithfulness_score"] == 0.8
    assert m["precision"] == 0.9
    assert m["secret_leak_test"] == "pass"
    assert m["mode"] == "golden"


def test_eval_result_gate_status_missing():
    result = EvalResult(
        run_id="r1", date="2026-01-01", mode=EvalMode.GOLDEN
    )
    assert result._gate_status("secret_leak") == "skip"


def test_eval_mode_values():
    assert EvalMode.GOLDEN.value == "golden"
    assert EvalMode.LIVE.value == "live"


def test_gate_status_values():
    assert GateStatus.PASS.value == "pass"
    assert GateStatus.FAIL.value == "fail"
    assert GateStatus.WARN.value == "warn"
    assert GateStatus.SKIP.value == "skip"


def test_item_outcome_values():
    assert ItemOutcome.ACCEPTED.value == "accepted"
    assert ItemOutcome.ROLLED_BACK.value == "rolled_back"
