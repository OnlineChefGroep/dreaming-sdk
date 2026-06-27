"""Tests for dream-eval deterministic gates."""

from dream_eval.gates import check_hash_determinism, check_secret_leak
from dream_eval.types import GateStatus


def test_secret_leak_no_patterns():
    result = check_secret_leak("some output text")
    assert result.status == GateStatus.SKIP


def test_secret_leak_clean():
    result = check_secret_leak("clean output", forbidden_patterns=[r"sk-.*", r"password=.*"])
    assert result.status == GateStatus.PASS


def test_secret_leak_detected():
    result = check_secret_leak("sk-abc123 secret key", forbidden_patterns=[r"sk-.*"])
    assert result.status == GateStatus.FAIL
    assert len(result.details["matched_patterns"]) == 1


def test_secret_leak_multiple_patterns():
    result = check_secret_leak(
        "password=secret123 and token=abc456",
        forbidden_patterns=[r"password\s*=\s*\S+", r"token\s*=\s*\S+"],
    )
    assert result.status == GateStatus.FAIL
    assert len(result.details["matched_patterns"]) == 2


def test_hash_determinism_bom():
    with_bom = "\ufeffhello world"
    without_bom = "hello world"
    r1 = check_hash_determinism(with_bom)
    r2 = check_hash_determinism(without_bom)
    assert r1.details["hash"] == r2.details["hash"]


def test_hash_determinism_crlf():
    crlf = "line1\r\nline2\r\n"
    lf = "line1\nline2\n"
    r1 = check_hash_determinism(crlf)
    r2 = check_hash_determinism(lf)
    assert r1.details["hash"] == r2.details["hash"]


def test_hash_determinism_expected_match():
    content = "test content"
    r1 = check_hash_determinism(content)
    expected = r1.details["hash"]
    r2 = check_hash_determinism(content, expected)
    assert r2.status == GateStatus.PASS


def test_hash_determinism_expected_mismatch():
    r = check_hash_determinism("content", "sha256:wrong")
    assert r.status == GateStatus.FAIL
