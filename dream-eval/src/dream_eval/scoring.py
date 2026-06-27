"""Scoring algorithms for dream-eval — precision, recall, faithfulness.

Supports three modes:
- Exact: key-by-key comparison (fast, deterministic)
- Fuzzy: semantic similarity via difflib (no LLM dependency, handles inflection)
- NLI: natural language inference via HHEM-2.1-Open (requires dream-eval[nli])
"""

from __future__ import annotations

import asyncio
import difflib
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from dream_eval.types import FaithfulnessReport, LabeledItem, ProposedItem

# Threshold for fuzzy content matching (0-1, higher = stricter)
FUZZY_THRESHOLD = 0.85


def compute_precision(proposed: list[ProposedItem], labels: list[LabeledItem]) -> float:
    """Fraction of proposed items that are supported by labels."""
    if not proposed:
        return 0.0

    label_map = {(lab.id, lab.category): lab for lab in labels}
    supported = 0
    for item in proposed:
        key = (item.id, item.category)
        if key in label_map:
            if _content_supported(item, label_map[key]):
                supported += 1
    return supported / len(proposed)


def compute_recall(proposed: list[ProposedItem], labels: list[LabeledItem]) -> float:
    """Fraction of labeled items that appear in proposed items."""
    if not labels:
        return 0.0

    proposed_keys = {(p.id, p.category) for p in proposed}
    found = sum(1 for lab in labels if (lab.id, lab.category) in proposed_keys)
    return found / len(labels)


def compute_recurrence_calibration(
    proposed: list[ProposedItem], labels: list[LabeledItem]
) -> float:
    """How well recurrence counts match ground truth.

    Returns a score in [0, 1] where 1 = perfect calibration.
    Items without max_recurrence in labels are excluded.
    """
    label_map = {(lab.id, lab.category): lab for lab in labels}
    scored = 0
    total_deviation = 0.0

    for item in proposed:
        key = (item.id, item.category)
        label = label_map.get(key)
        if label is None or label.max_recurrence is None:
            continue
        scored += 1
        deviation = abs(item.recurrence - label.max_recurrence)
        max_possible = max(label.max_recurrence, 1)
        total_deviation += min(deviation / max_possible, 1.0)

    if scored == 0:
        return 1.0

    return 1.0 - (total_deviation / scored)


def compute_faithfulness(
    proposed: list[ProposedItem],
    labels: list[LabeledItem],
    *,
    fuzzy: bool = False,
    nli: bool = False,
    threshold: float = FUZZY_THRESHOLD,
) -> FaithfulnessReport:
    """Full faithfulness report — the primary quality signal.

    Faithfulness = items with fully supported claims / total proposed items.

    Args:
        proposed: Items proposed by the evaluator.
        labels: Ground truth labels from golden corpus.
        fuzzy: Use semantic similarity for content matching (slower, more accurate).
        nli: Use NLI claim verification via HHEM-2.1-Open (requires dream-eval[nli]).
        threshold: Similarity threshold for fuzzy matching (0-1).
    """
    precision = compute_precision(proposed, labels)
    recall = compute_recall(proposed, labels)
    recurrence_cal = compute_recurrence_calibration(proposed, labels)

    label_map = {(lab.id, lab.category): lab for lab in labels}
    fully_supported = 0
    partially_supported = 0
    unsupported = 0
    recurrence_violations: list[str] = []
    specificity_flags: list[str] = []

    for item in proposed:
        key = (item.id, item.category)
        label = label_map.get(key)
        if label is None:
            unsupported += 1
            continue

        if nli:
            supported, _ = _content_supported_nli(item, label)
        elif fuzzy:
            supported = _content_supported_fuzzy(item, label, threshold)
        else:
            supported = _content_supported(item, label)

        if not supported:
            unsupported += 1
            continue

        if label.max_recurrence is not None and item.recurrence > label.max_recurrence:
            recurrence_violations.append(
                f"{item.id}: claimed {item.recurrence}, max {label.max_recurrence}"
            )
            partially_supported += 1
        else:
            fully_supported += 1

    total = len(proposed) if proposed else 1
    faithfulness = fully_supported / total

    return FaithfulnessReport(
        faithfulness_score=faithfulness,
        precision=precision,
        recall=recall,
        recurrence_calibration=recurrence_cal,
        items_proposed=len(proposed),
        items_fully_supported=fully_supported,
        items_partially_supported=partially_supported,
        items_unsupported=unsupported,
        recurrence_violations=recurrence_violations,
        specificity_flags=specificity_flags,
    )


# --- Async parallel scoring ---

async def score_transcripts_parallel(
    transcripts: list[dict],
    scorer: Callable[[dict], FaithfulnessReport],
    *,
    max_workers: int | None = None,
) -> list[FaithfulnessReport]:
    """Score multiple transcripts in parallel using ThreadPoolExecutor.

    Preserves input order. Uses asyncio.to_thread for CPU-bound scoring.
    """
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        tasks = [
            loop.run_in_executor(pool, scorer, transcript)
            for transcript in transcripts
        ]
    return list(await asyncio.gather(*tasks))


# --- Content matching ---

def _content_supported(item: ProposedItem, label: LabeledItem) -> bool:
    """Exact content matching: all label keys must be present with equal values."""
    for key, value in label.content.items():
        if key not in item.content:
            return False
        if item.content[key] != value:
            return False
    return True


def _content_supported_fuzzy(
    item: ProposedItem, label: LabeledItem, threshold: float = FUZZY_THRESHOLD
) -> bool:
    """Fuzzy content matching: semantic similarity via difflib.

    Handles inflection, minor rewording, and case differences.
    No LLM dependency — uses SequenceMatcher for portability.
    """
    for key, value in label.content.items():
        if key not in item.content:
            return False

        label_val = str(value).lower().strip()
        item_val = str(item.content[key]).lower().strip()

        if label_val == item_val:
            continue

        ratio = difflib.SequenceMatcher(None, label_val, item_val).ratio()
        if ratio < threshold:
            return False

    return True


def _compute_pairwise_similarity(text_a: str, text_b: str) -> float:
    """Compute similarity ratio between two strings (0-1)."""
    return difflib.SequenceMatcher(
        None, text_a.lower().strip(), text_b.lower().strip()
    ).ratio()


def _content_supported_nli(
    item: ProposedItem, label: LabeledItem
) -> tuple[bool, float]:
    """NLI content matching using HHEM-2.1-Open.

    Requires dream-eval[nli] extra. Falls back to fuzzy matching if NLI unavailable.
    """
    try:
        from dream_eval.nli import verify_content_nli
        return verify_content_nli(item, label)
    except ImportError:
        # Fall back to fuzzy matching if nli extra not installed
        return _content_supported_fuzzy(item, label, FUZZY_THRESHOLD), 0.0
