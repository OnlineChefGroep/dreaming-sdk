"""Tests for dreaming-memory Notion integration."""

from unittest.mock import MagicMock, patch

from dreaming_memory.integrations.notion import NotionClient, NotionMemoryBridge


def test_notion_client_init():
    with patch.dict("os.environ", {"NOTION_API_KEY": "test-key"}):
        client = NotionClient()
        assert client.token == "test-key"


def test_notion_client_init_token():
    with patch.dict("os.environ", {"NOTION_TOKEN": "test-token"}, clear=True):
        client = NotionClient()
        assert client.token == "test-token"


def test_notion_client_no_key():
    with patch.dict("os.environ", {}, clear=True):
        try:
            NotionClient()
        except ValueError as e:
            assert "NOTION_API_KEY" in str(e)


def test_notion_client_headers():
    with patch.dict("os.environ", {"NOTION_API_KEY": "test-key"}):
        client = NotionClient()
        headers = client._headers()
        assert "Bearer test-key" in headers["Authorization"]
        assert headers["Notion-Version"] == "2022-06-28"


def test_notion_client_get_page():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": "page-1",
        "properties": {"Name": {"title": [{"text": {"content": "Test"}}]}},
        "url": "https://notion.so/test",
    }
    mock_response.raise_for_status = MagicMock()

    with patch.dict("os.environ", {"NOTION_API_KEY": "test-key"}):
        with patch("dreaming_memory.integrations.notion.httpx.get", return_value=mock_response):
            client = NotionClient()
            page = client.get_page("page-1")
            assert page["id"] == "page-1"


def test_notion_client_get_page_blocks():
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": []}
    mock_response.raise_for_status = MagicMock()

    with patch.dict("os.environ", {"NOTION_API_KEY": "test-key"}):
        with patch("dreaming_memory.integrations.notion.httpx.get", return_value=mock_response):
            client = NotionClient()
            blocks = client.get_page_blocks("page-1")
            assert blocks == []


def test_notion_bridge_init():
    mock_store = MagicMock()
    with patch.dict("os.environ", {"NOTION_API_KEY": "test-key"}):
        bridge = NotionMemoryBridge(store=mock_store)
        assert bridge.store is mock_store


def test_notion_client_extract_title():
    page = {
        "id": "page-1",
        "properties": {
            "Name": {"type": "title", "title": [{"plain_text": "Test Title"}]}
        },
    }
    with patch.dict("os.environ", {"NOTION_API_KEY": "test-key"}):
        client = NotionClient()
        title = client.extract_title(page)
        assert title == "Test Title"


def test_notion_client_extract_title_empty():
    page = {"id": "page-1", "properties": {}}
    with patch.dict("os.environ", {"NOTION_API_KEY": "test-key"}):
        client = NotionClient()
        title = client.extract_title(page)
        assert title == "page-1"


def test_notion_client_blocks_to_text():
    blocks = [
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Hello"}]}},
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "World"}]}},
    ]
    with patch.dict("os.environ", {"NOTION_API_KEY": "test-key"}):
        client = NotionClient()
        text = client.blocks_to_text(blocks)
        assert "Hello" in text
        assert "World" in text


def test_notion_client_blocks_to_text_empty():
    with patch.dict("os.environ", {"NOTION_API_KEY": "test-key"}):
        client = NotionClient()
        text = client.blocks_to_text([])
        assert text == ""
