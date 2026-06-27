"""Tests for dream-eval scoring algorithms."""

import asyncio

from hypothesis import example, given
from hypothesis import strategies as st

from dream_eval.scoring import (
    compute_faithfulness,
    compute_precision,
    compute_recall,
    compute_recurrence_calibration,
    score_transcripts_parallel,
)
from dream_eval.types import FaithfulnessReport, LabeledItem, ProposedItem

# --- Exact matching tests ---


def test_precision_perfect():
    proposed = [ProposedItem(id="a", category="pref"), ProposedItem(id="b", category="rule")]
    labels = [LabeledItem(id="a", category="pref"), LabeledItem(id="b", category="rule")]
    assert compute_precision(proposed, labels) == 1.0


def test_precision_partial():
    proposed = [
        ProposedItem(id="a", category="pref"),
        ProposedItem(id="x", category="unknown"),
    ]
    labels = [LabeledItem(id="a", category="pref")]
    assert compute_precision(proposed, labels) == 0.5


def test_precision_empty():
    assert compute_precision([], []) == 0.0


def test_recall_perfect():
    proposed = [ProposedItem(id="a", category="pref"), ProposedItem(id="b", category="rule")]
    labels = [LabeledItem(id="a", category="pref"), LabeledItem(id="b", category="rule")]
    assert compute_recall(proposed, labels) == 1.0


def test_recall_partial():
    proposed = [ProposedItem(id="a", category="pref")]
    labels = [LabeledItem(id="a", category="pref"), LabeledItem(id="b", category="rule")]
    assert compute_recall(proposed, labels) == 0.5


def test_recall_empty_labels():
    proposed = [ProposedItem(id="a", category="pref")]
    assert compute_recall(proposed, []) == 0.0


def test_recurrence_calibration_perfect():
    proposed = [ProposedItem(id="a", category="pref", recurrence=3)]
    labels = [LabeledItem(id="a", category="pref", max_recurrence=3)]
    assert compute_recurrence_calibration(proposed, labels) == 1.0


def test_recurrence_calibration_off():
    proposed = [ProposedItem(id="a", category="pref", recurrence=5)]
    labels = [LabeledItem(id="a", category="pref", max_recurrence=3)]
    score = compute_recurrence_calibration(proposed, labels)
    assert 0.0 < score < 1.0


def test_faithfulness_full_support():
    proposed = [ProposedItem(id="a", category="pref")]
    labels = [LabeledItem(id="a", category="pref")]
    report = compute_faithfulness(proposed, labels)
    assert report.faithfulness_score == 1.0
    assert report.items_fully_supported == 1
    assert report.items_unsupported == 0


def test_faithfulness_no_support():
    proposed = [ProposedItem(id="x", category="unknown")]
    labels = [LabeledItem(id="a", category="pref")]
    report = compute_faithfulness(proposed, labels)
    assert report.faithfulness_score == 0.0
    assert report.items_unsupported == 1


def test_faithfulness_mixed():
    proposed = [
        ProposedItem(id="a", category="pref"),
        ProposedItem(id="b", category="pref"),
        ProposedItem(id="x", category="unknown"),
    ]
    labels = [LabeledItem(id="a", category="pref")]
    report = compute_faithfulness(proposed, labels)
    assert report.items_fully_supported == 1
    assert report.items_partially_supported == 0
    assert report.items_unsupported == 2


# --- Fuzzy matching tests ---


def test_fuzzy_matching_inflection():
    proposed = [ProposedItem(id="a", category="pref", content={"key": "running tests"})]
    labels = [LabeledItem(id="a", category="pref", content={"key": "run tests"})]
    report = compute_faithfulness(proposed, labels, fuzzy=True, threshold=0.7)
    assert report.items_fully_supported == 1


def test_fuzzy_matching_exact_still_works():
    proposed = [ProposedItem(id="a", category="pref", content={"key": "exact match"})]
    labels = [LabeledItem(id="a", category="pref", content={"key": "exact match"})]
    report = compute_faithfulness(proposed, labels, fuzzy=True)
    assert report.faithfulness_score == 1.0


def test_fuzzy_matching_below_threshold():
    proposed = [ProposedItem(id="a", category="pref", content={"key": "completely different"})]
    labels = [LabeledItem(id="a", category="pref", content={"key": "exact match"})]
    report = compute_faithfulness(proposed, labels, fuzzy=True, threshold=0.9)
    assert report.items_unsupported == 1


# --- Async parallel scoring tests ---


def test_parallel_scoring_preserves_order():
    def slow_scorer(transcript: dict) -> FaithfulnessReport:
        return compute_faithfulness(
            [ProposedItem(id=transcript["id"], category="pref")],
            [LabeledItem(id=transcript["id"], category="pref")],
        )

    transcripts = [{"id": f"item-{i}"} for i in range(5)]
    results = asyncio.run(score_transcripts_parallel(transcripts, slow_scorer))

    for result in results:
        assert result.items_proposed == 1
        assert result.items_fully_supported == 1


def test_parallel_scoring_empty():
    results = asyncio.run(score_transcripts_parallel([], lambda t: compute_faithfulness([], [])))
    assert results == []


# --- Property-based tests with Hypothesis ---


@given(st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=20))
@example([])
@example(["single"])
@example(["a", "a", "a"])
def test_faithfulness_score_bounds(claim_ids: list[str]):
    """Faithfulness score must always be in [0, 1]."""
    proposed = [ProposedItem(id=c, category="pref") for c in claim_ids]
    labels = [LabeledItem(id=c, category="pref") for c in claim_ids[:len(claim_ids) // 2 or 1]]
    report = compute_faithfulness(proposed, labels)
    assert 0.0 <= report.faithfulness_score <= 1.0
    assert report.items_proposed == len(proposed)


@given(st.integers(min_value=0, max_value=100))
@example(0)
@example(1)
@example(100)
def test_recall_bounds(n_labels: int):
    """Recall must always be in [0, 1]."""
    proposed = [ProposedItem(id="a", category="pref")]
    labels = [LabeledItem(id=f"item-{i}", category="pref") for i in range(n_labels)]
    recall = compute_recall(proposed, labels)
    assert 0.0 <= recall <= 1.0


@given(st.integers(min_value=0, max_value=50))
@example(0)
@example(50)
def test_precision_bounds(n_unrelated: int):
    """Precision must always be in [0, 1]."""
    proposed = [ProposedItem(id="a", category="pref")]
    labels = [LabeledItem(id="a", category="pref")]
    precision = compute_precision(proposed, labels)
    assert 0.0 <= precision <= 1.0


@given(st.integers(min_value=0, max_value=20), st.integers(min_value=0, max_value=20))
@example(0, 0)
@example(5, 5)
@example(0, 10)
@example(10, 0)
def test_recurrence_calibration_bounds(claimed: int, max_rec: int):
    """Recurrence calibration must always be in [0, 1]."""
    proposed = [ProposedItem(id="a", category="pref", recurrence=claimed)]
    labels = [LabeledItem(id="a", category="pref", max_recurrence=max_rec)]
    cal = compute_recurrence_calibration(proposed, labels)
    assert 0.0 <= cal <= 1.0
