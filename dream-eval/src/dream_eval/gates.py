"""Deterministic gates — hard stops that must pass before scoring."""

from __future__ import annotations

import hashlib
import re

from dream_eval.types import GateResult, GateStatus

DEFAULT_FORBIDDEN_PATTERNS: list[str] = [
    r"sk-[a-zA-Z0-9]{20,}",
    r"ghp_[a-zA-Z0-9]{36}",
    r"gho_[a-zA-Z0-9]{36}",
    r"ghu_[a-zA-Z0-9]{36}",
    r"xox[bps]-[a-zA-Z0-9]{10,}",
    r"AKIA[0-9A-Z]{16}",
    r"password\s*=\s*\S+",
    r"secret\s*=\s*\S+",
    r"api[_-]?key\s*=\s*\S+",
    r"Bearer\s+[A-Za-z0-9\-._~+/]{20,}",
    r"-----BEGIN\s+(RSA|EC|DSA|OPENSSH)\s+PRIVATE\s+KEY-----",
    r"https?://[^@\s]+@[^/\s]",
    r"token\s*=\s*\S+",
]


def check_secret_leak(
    output_text: str,
    forbidden_patterns: list[str] | None = None,
) -> GateResult:
    """Check evaluator output for leaked secrets.

    When *forbidden_patterns* is ``None`` the built-in defaults are used.
    Pass an explicit empty list ``[]`` to skip scanning entirely.
    Hard stop: if any forbidden pattern matches, the eval must fail.
    """
    if forbidden_patterns is None:
        forbidden_patterns = list(DEFAULT_FORBIDDEN_PATTERNS)
    if not forbidden_patterns:
        return GateResult(
            name="secret_leak",
            status=GateStatus.SKIP,
            message="No forbidden patterns configured",
        )

    matches: list[str] = []
    for pattern in forbidden_patterns:
        try:
            if re.search(pattern, output_text, re.IGNORECASE):
                matches.append(pattern)
        except re.error:
            if pattern.lower() in output_text.lower():
                matches.append(pattern)

    if matches:
        return GateResult(
            name="secret_leak",
            status=GateStatus.FAIL,
            message=f"Secret leak detected: {len(matches)} forbidden pattern(s) matched",
            details={"matched_patterns": matches},
        )

    return GateResult(
        name="secret_leak",
        status=GateStatus.PASS,
        message="No forbidden patterns found in output",
    )


def _canonical_hash(content: str) -> str:
    """Canonical SHA-256: strip BOM, normalize CRLF→LF, hex digest with prefix."""
    text = content
    if text.startswith("\ufeff"):
        text = text[1:]
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def check_hash_determinism(
    content: str,
    expected_hash: str | None = None,
) -> GateResult:
    """Verify hash is deterministic after BOM/CRLF normalization.

    The canonical hash algorithm:
    1. Strip UTF-8 BOM if present
    2. Normalize line endings: CRLF → LF
    3. Compute SHA-256 hex digest
    """
    actual_hash = _canonical_hash(content)

    if expected_hash is None:
        return GateResult(
            name="hash_determinism",
            status=GateStatus.PASS,
            message=f"Hash computed: {actual_hash}",
            details={"hash": actual_hash},
        )

    if actual_hash == expected_hash:
        return GateResult(
            name="hash_determinism",
            status=GateStatus.PASS,
            message="Hash matches expected value",
            details={"hash": actual_hash},
        )

    return GateResult(
        name="hash_determinism",
        status=GateStatus.FAIL,
        message=f"Hash mismatch: expected {expected_hash}, got {actual_hash}",
        details={"expected": expected_hash, "actual": actual_hash},
    )
