"""Extra tests for dream-eval scoring to boost coverage."""

from dream_eval.scoring import (
    _compute_pairwise_similarity,
    _content_supported,
    _content_supported_fuzzy,
    _content_supported_nli,
    compute_faithfulness,
    compute_precision,
    compute_recall,
    compute_recurrence_calibration,
)
from dream_eval.types import LabeledItem, ProposedItem


def test_content_supported_exact_match():
    item = ProposedItem(id="a", category="pref", content={"k": "v"})
    label = LabeledItem(id="a", category="pref", content={"k": "v"})
    assert _content_supported(item, label) is True


def test_content_supported_missing_key():
    item = ProposedItem(id="a", category="pref", content={})
    label = LabeledItem(id="a", category="pref", content={"k": "v"})
    assert _content_supported(item, label) is False


def test_content_supported_value_mismatch():
    item = ProposedItem(id="a", category="pref", content={"k": "x"})
    label = LabeledItem(id="a", category="pref", content={"k": "v"})
    assert _content_supported(item, label) is False


def test_content_supported_empty_label():
    item = ProposedItem(id="a", category="pref", content={"k": "v"})
    label = LabeledItem(id="a", category="pref", content={})
    assert _content_supported(item, label) is True


def test_content_supported_fuzzy_match():
    item = ProposedItem(id="a", category="pref", content={"k": "running tests"})
    label = LabeledItem(id="a", category="pref", content={"k": "run tests"})
    assert _content_supported_fuzzy(item, label, threshold=0.7) is True


def test_content_supported_fuzzy_no_match():
    item = ProposedItem(id="a", category="pref", content={"k": "completely different"})
    label = LabeledItem(id="a", category="pref", content={"k": "exact match"})
    assert _content_supported_fuzzy(item, label, threshold=0.9) is False


def test_content_supported_fuzzy_missing_key():
    item = ProposedItem(id="a", category="pref", content={})
    label = LabeledItem(id="a", category="pref", content={"k": "v"})
    assert _content_supported_fuzzy(item, label) is False


def test_content_supported_nli_fallback():
    """NLI falls back to fuzzy when transformers unavailable."""
    item = ProposedItem(id="a", category="pref", content={"k": "exact match"})
    label = LabeledItem(id="a", category="pref", content={"k": "exact match"})
    supported, score = _content_supported_nli(item, label)
    assert supported is True


def test_compute_pairwise_similarity():
    ratio = _compute_pairwise_similarity("hello world", "hello world")
    assert ratio == 1.0


def test_compute_pairwise_similarity_different():
    ratio = _compute_pairwise_similarity("hello", "goodbye")
    assert 0.0 <= ratio < 0.5


def test_precision_all_unmatched():
    proposed = [ProposedItem(id="x", category="pref")]
    labels = [LabeledItem(id="a", category="pref")]
    assert compute_precision(proposed, labels) == 0.0


def test_recall_no_proposed():
    labels = [LabeledItem(id="a", category="pref")]
    assert compute_recall([], labels) == 0.0


def test_recurrence_calibration_no_labels():
    proposed = [ProposedItem(id="a", category="pref", recurrence=5)]
    labels = [LabeledItem(id="x", category="pref")]
    assert compute_recurrence_calibration(proposed, labels) == 1.0


def test_faithfulness_nli_mode():
    """NLI mode falls back to fuzzy when transformers unavailable."""
    proposed = [ProposedItem(id="a", category="pref", content={"k": "test"})]
    labels = [LabeledItem(id="a", category="pref", content={"k": "test"})]
    report = compute_faithfulness(proposed, labels, nli=True)
    assert report.faithfulness_score == 1.0
