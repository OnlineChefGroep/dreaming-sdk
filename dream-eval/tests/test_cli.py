"""Tests for dream-eval CLI."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from dream_eval.cli import main


def test_gates_secret_leak_default_patterns(capsys):
    with patch("sys.argv", ["dream-eval", "gates", "--text", "clean output"]):
        main()
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["status"] == "pass"


def test_gates_hash_via_text(capsys):
    with patch("sys.argv", ["dream-eval", "gates", "--text", "hello"]):
        main()
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["name"] == "secret_leak"


def test_gates_no_args(capsys):
    with patch("sys.argv", ["dream-eval", "gates"]):
        try:
            main()
        except SystemExit as e:
            assert e.code == 1


def test_run_eval(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("sys.argv", ["dream-eval", "run", "--output-dir", tmpdir]):
            try:
                main()
            except SystemExit as e:
                assert e.code == 1 if e.code != 0 else None
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "run_id" in data
        assert data["faithfulness_score"] > 0


def test_run_eval_default_dir(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("sys.argv", ["dream-eval", "run", "--output-dir", tmpdir]):
            try:
                main()
            except SystemExit:
                pass
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "run_id" in data


def test_run_eval_live_mode(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("sys.argv", ["dream-eval", "run", "--mode", "live", "--output-dir", tmpdir]):
            try:
                main()
            except SystemExit as e:
                assert e.code == 1
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["run_id"]


def test_list_empty(capsys):
    with tempfile.TemporaryDirectory():
        with patch("sys.argv", ["dream-eval", "list", "--limit", "5"]):
            # list uses default eval/results dir, just verify no crash
            main()


def test_list_with_data(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a run directory with metrics.json
        run_dir = Path(tmpdir) / "eval" / "results" / "r1"
        run_dir.mkdir(parents=True)
        (run_dir / "metrics.json").write_text(json.dumps({
            "run_id": "r1",
            "faithfulness_score": 0.8,
            "secret_leak_test": "pass",
        }), encoding="utf-8")

        # Patch the default path
        def _init_override(self, **kw):
            self.results_dir = Path(tmpdir) / "eval" / "results"

        with patch("dream_eval.backends.JsonFileBackend.__init__", _init_override):
            with patch("sys.argv", ["dream-eval", "list", "--limit", "5"]):
                main()
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["run_id"] == "r1"


def test_show_nonexistent(capsys):
    with patch("sys.argv", ["dream-eval", "show", "nonexistent-run"]):
        try:
            main()
        except SystemExit as e:
            assert e.code == 1


def test_show_existing(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir) / "eval" / "results" / "r1"
        run_dir.mkdir(parents=True)
        (run_dir / "eval-report.json").write_text(json.dumps({
            "items": [],
            "sessions_evaluated": 3,
        }), encoding="utf-8")

        def _init_override2(self, **kw):
            self.results_dir = Path(tmpdir) / "eval" / "results"

        with patch("dream_eval.backends.JsonFileBackend.__init__", _init_override2):
            with patch("sys.argv", ["dream-eval", "show", "r1"]):
                main()
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["sessions_evaluated"] == 3


def test_score_missing_report():
    with patch("sys.argv", ["dream-eval", "score", "--report", "/nonexistent.json"]):
        try:
            main()
        except (SystemExit, FileNotFoundError):
            pass
