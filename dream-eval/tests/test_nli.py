"""Tests for dream-eval NLI module (mocked transformers)."""

import sys
from unittest.mock import MagicMock, patch

from dream_eval.types import LabeledItem, ProposedItem


def test_verify_claim_import_error():
    """Without transformers, should raise ImportError."""
    # Remove transformers from modules if present
    to_delete = [k for k in sys.modules if "transformers" in k]
    for k in to_delete:
        del sys.modules[k]

    import dream_eval.nli as nli_mod
    nli_mod._model = None

    with patch.dict(sys.modules, {"transformers": None}):
        try:
            nli_mod._get_model()
            assert False, "Should have raised ImportError"
        except ImportError as e:
            assert "nli" in str(e)


@patch("dream_eval.nli._get_model")
def test_verify_claim_supported(mock_get_model):
    from dream_eval.nli import verify_claim

    mock_model = MagicMock()
    mock_model.predict.return_value = 0.9
    mock_get_model.return_value = mock_model

    supported, score = verify_claim("claim text", "context text")
    assert supported is True
    assert score == 0.9


@patch("dream_eval.nli._get_model")
def test_verify_claim_not_supported(mock_get_model):
    from dream_eval.nli import verify_claim

    mock_model = MagicMock()
    mock_model.predict.return_value = 0.2
    mock_get_model.return_value = mock_model

    supported, score = verify_claim("claim text", "context text")
    assert supported is False
    assert score == 0.2


@patch("dream_eval.nli._get_model")
def test_verify_content_nli_all_supported(mock_get_model):
    from dream_eval.nli import verify_content_nli

    mock_model = MagicMock()
    mock_model.predict.return_value = 0.8
    mock_get_model.return_value = mock_model

    item = ProposedItem(id="a", category="pref", content={"key": "value"})
    label = LabeledItem(id="a", category="pref", content={"key": "value"})

    supported, score = verify_content_nli(item, label)
    assert supported is True


@patch("dream_eval.nli._get_model")
def test_verify_content_nli_missing_key(mock_get_model):
    from dream_eval.nli import verify_content_nli

    item = ProposedItem(id="a", category="pref", content={})
    label = LabeledItem(id="a", category="pref", content={"key": "value"})

    supported, score = verify_content_nli(item, label)
    assert supported is False
    assert score == 0.0


@patch("dream_eval.nli._get_model")
def test_verify_content_nli_empty_values(mock_get_model):
    from dream_eval.nli import verify_content_nli

    item = ProposedItem(id="a", category="pref", content={"key": ""})
    label = LabeledItem(id="a", category="pref", content={"key": "value"})

    supported, score = verify_content_nli(item, label)
    assert supported is False
