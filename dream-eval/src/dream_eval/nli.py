"""NLI claim verification using Vectara HHEM-2.1-Open.

Optional module — requires `dream-eval[nli]` extra:
    pip install dream-eval[nli]

Uses the HHEM (Hierarchical Hypothesis Evaluation Model) for
natural language inference-based claim verification. This provides
semantic similarity beyond exact/fuzzy matching, achieving higher
faithfulness scores for agent memory evaluation.

Reference: https://huggingface.co/vectara/hhem-2.1-Open
"""

from __future__ import annotations

from typing import Any

from dream_eval.types import LabeledItem, ProposedItem

# Lazy-loaded model singleton
_model: Any = None


def _get_model() -> Any:
    """Load HHEM-2.1-Open model on first use."""
    global _model
    if _model is not None:
        return _model

    try:
        from transformers import AutoModelForSequenceClassification
    except ImportError as exc:
        raise ImportError(
            "NLI verification requires the `nli` extra. "
            "Install with: pip install dream-eval[nli]"
        ) from exc

    _model = AutoModelForSequenceClassification.from_pretrained(
        "vectara/hhem-2.1-Open",
        trust_remote_code=True,
    )
    return _model


def verify_claim(claim: str, context: str, threshold: float = 0.5) -> tuple[bool, float]:
    """Verify if a claim is supported by context using NLI.

    Args:
        claim: The claim to verify (proposed item content).
        context: The reference context (label content).
        threshold: Score threshold for support (0-1). Default 0.5.

    Returns:
        Tuple of (supported: bool, score: float).
    """
    model = _get_model()

    # HHEM expects premise, hypothesis format
    # premise = context (known facts), hypothesis = claim (to verify)
    result = model.predict([(context, claim)])
    score = float(result)
    return score >= threshold, score


def verify_content_nli(
    item: ProposedItem,
    label: LabeledItem,
    threshold: float = 0.5,
) -> tuple[bool, float]:
    """Verify if all label content is supported by item content using NLI.

    Checks each key-value pair in label.content against the corresponding
    value in item.content using natural language inference.

    Returns:
        Tuple of (all_supported: bool, min_score: float).
    """
    scores: list[float] = []

    for key, value in label.content.items():
        if key not in item.content:
            return False, 0.0

        label_text = str(value).strip()
        item_text = str(item.content[key]).strip()

        if not label_text or not item_text:
            return False, 0.0

        supported, score = verify_claim(item_text, label_text, threshold)
        scores.append(score)

        if not supported:
            return False, score

    return True, min(scores) if scores else 1.0
