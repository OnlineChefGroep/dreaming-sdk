#!/usr/bin/env python3
"""Quick start example for dream-eval."""

from dream_eval.scoring import compute_faithfulness
from dream_eval.gates import check_secret_leak, check_hash_determinism
from dream_eval.types import ProposedItem, LabeledItem


def main() -> None:
    # --- 1. Faithfulness scoring ---
    proposed = [
        ProposedItem(
            id="pref-1",
            category="pref",
            content={"key": "ci-merge-gate", "value": "require-reviews"},
            recurrence=3,
        ),
        ProposedItem(
            id="rule-1",
            category="rule",
            content={"key": "no-secrets-in-code", "value": "true"},
        ),
        ProposedItem(
            id="unknown-1",
            category="pref",
            content={"key": "mystery-pref"},
        ),
    ]

    labels = [
        LabeledItem(
            id="pref-1",
            category="pref",
            content={"key": "ci-merge-gate", "value": "require-reviews"},
            max_recurrence=5,
        ),
        LabeledItem(
            id="rule-1",
            category="rule",
            content={"key": "no-secrets-in-code", "value": "true"},
        ),
    ]

    report = compute_faithfulness(proposed, labels)

    print("=== Faithfulness Report ===")
    print(f"  Score:        {report.faithfulness_score:.3f}")
    print(f"  Precision:    {report.precision:.3f}")
    print(f"  Recall:       {report.recall:.3f}")
    print(f"  Proposed:     {report.items_proposed}")
    print(f"  Supported:    {report.items_fully_supported}")
    print(f"  Unsupported:  {report.items_unsupported}")
    print()

    # --- 2. Secret leak detection ---
    clean = check_secret_leak(
        "The config uses environment variables for all secrets.",
        forbidden_patterns=[r"sk-.*", r"password\s*=\s*\S+"],
    )
    leaked = check_secret_leak(
        "Set password=secret123 in the config file.",
        forbidden_patterns=[r"sk-.*", r"password\s*=\s*\S+"],
    )

    print("=== Secret Leak Gates ===")
    print(f"  Clean text:  {clean.status.value}")
    print(f"  Leaked text: {leaked.status.value}")
    print()

    # --- 3. Hash determinism ---
    content_v1 = "Hello World\n"
    content_v2 = "Hello World\r\n"  # CRLF variant
    content_v3 = "\ufeffHello World\n"  # BOM variant

    h1 = check_hash_determinism(content_v1)
    h2 = check_hash_determinism(content_v2)
    h3 = check_hash_determinism(content_v3)

    print("=== Hash Determinism ===")
    print(f"  LF:      {h1.details['hash']}")
    print(f"  CRLF:    {h2.details['hash']}")
    print(f"  BOM+LF:  {h3.details['hash']}")
    print(f"  All match: {h1.details['hash'] == h2.details['hash'] == h3.details['hash']}")


if __name__ == "__main__":
    main()
