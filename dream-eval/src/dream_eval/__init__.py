"""dream-eval — Agent-agnostic faithfulness evaluation framework."""

from dream_eval.gates import check_hash_determinism, check_secret_leak
from dream_eval.scoring import compute_faithfulness, compute_precision, compute_recall
from dream_eval.types import EvalResult, FaithfulnessReport, GateResult

__all__ = [
    "EvalResult",
    "FaithfulnessReport",
    "GateResult",
    "check_hash_determinism",
    "check_secret_leak",
    "compute_faithfulness",
    "compute_precision",
    "compute_recall",
]

__version__ = "0.1.0"
