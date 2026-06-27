"""Tests for dreaming-memory Linear integration."""

from unittest.mock import MagicMock, patch

from dreaming_memory.integrations.linear import LinearClient, LinearMemoryBridge


def test_linear_client_init():
    with patch.dict("os.environ", {"LINEAR_API_KEY": "test-key"}):
        client = LinearClient()
        assert client.api_key == "test-key"


def test_linear_client_no_key():
    with patch.dict("os.environ", {}, clear=True):
        try:
            LinearClient()
        except ValueError as e:
            assert "LINEAR_API_KEY" in str(e)


def test_linear_client_normalize_issue_id():
    with patch.dict("os.environ", {"LINEAR_API_KEY": "test-key"}):
        client = LinearClient()
        assert client.normalize_issue_id("123") == "CHEF-123"
        assert client.normalize_issue_id("CHEF-123") == "CHEF-123"
        assert client.normalize_issue_id("chef-456") == "CHEF-456"


def test_linear_client_gql():
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": {"viewer": {"id": "1"}}}
    mock_response.raise_for_status = MagicMock()

    with patch.dict("os.environ", {"LINEAR_API_KEY": "test-key"}):
        with patch("dreaming_memory.integrations.linear.httpx.post", return_value=mock_response):
            client = LinearClient()
            result = client.gql("query { viewer { id } }")
            assert result == {"viewer": {"id": "1"}}


def test_linear_client_gql_error():
    mock_response = MagicMock()
    mock_response.json.return_value = {"errors": [{"message": "test error"}]}
    mock_response.raise_for_status = MagicMock()

    with patch.dict("os.environ", {"LINEAR_API_KEY": "test-key"}):
        with patch("dreaming_memory.integrations.linear.httpx.post", return_value=mock_response):
            client = LinearClient()
            try:
                client.gql("query { viewer { id } }")
            except RuntimeError as e:
                assert "Linear GraphQL errors" in str(e)


def test_linear_bridge_init():
    mock_store = MagicMock()
    with patch.dict("os.environ", {"LINEAR_API_KEY": "test-key"}):
        bridge = LinearMemoryBridge(store=mock_store)
        assert bridge.store is mock_store


def test_linear_client_get_issue():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "issue": {
                "id": "issue-1",
                "identifier": "CHEF-1",
                "title": "Test",
                "description": "Desc",
                "state": {"name": "Todo"},
                "priority": 0,
                "url": "https://linear.app/test/issue/1",
                "assignee": None,
                "labels": {"nodes": []},
                "comments": {"nodes": []},
                "createdAt": "2026-01-01",
                "updatedAt": "2026-01-01",
            }
        }
    }
    mock_response.raise_for_status = MagicMock()

    with patch.dict("os.environ", {"LINEAR_API_KEY": "test-key"}):
        with patch("dreaming_memory.integrations.linear.httpx.post", return_value=mock_response):
            client = LinearClient()
            issue = client.get_issue("1")
            assert issue["identifier"] == "CHEF-1"


def test_linear_client_list_issues():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "issues": {
                "nodes": [
                    {"id": "1", "identifier": "CHEF-1", "title": "Test"}
                ]
            }
        }
    }
    mock_response.raise_for_status = MagicMock()

    with patch.dict("os.environ", {"LINEAR_API_KEY": "test-key"}):
        with patch("dreaming_memory.integrations.linear.httpx.post", return_value=mock_response):
            client = LinearClient()
            issues = client.list_issues()
            assert len(issues) == 1
