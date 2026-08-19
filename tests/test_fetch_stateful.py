"""Tests for stateful fetch() — deduplication and state management."""
import pytest
from unittest.mock import MagicMock, patch
from tracksnap.core import fetch

FEED_XML = """\
<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>First Post</title>
      <link>https://example.com/1</link>
      <guid>https://example.com/1</guid>
    </item>
    <item>
      <title>Second Post</title>
      <link>https://example.com/2</link>
      <guid>https://example.com/2</guid>
    </item>
  </channel>
</rss>"""


def _make_mock_client(feed_xml=FEED_XML):
    """Return a context-manager mock that yields an httpx-like client."""
    mock_resp = MagicMock()
    mock_resp.text = feed_xml
    mock_resp.raise_for_status = MagicMock(return_value=None)

    mock_instance = MagicMock()
    mock_instance.get.return_value = mock_resp

    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_instance)
    mock_cm.__exit__ = MagicMock(return_value=False)
    return mock_cm


class TestFetchStateful:
    def test_first_run_returns_all(self, tmp_path):
        db = tmp_path / "state.db"
        with patch("tracksnap.core.httpx.Client", return_value=_make_mock_client()):
            items = fetch("https://example.com/feed", db_path=db)
        assert len(items) == 2

    def test_second_run_returns_empty(self, tmp_path):
        db = tmp_path / "state.db"
        with patch("tracksnap.core.httpx.Client", return_value=_make_mock_client()):
            fetch("https://example.com/feed", db_path=db)  # first run
            items = fetch("https://example.com/feed", db_path=db)  # second run
        assert items == []

    def test_reset_shows_all_again(self, tmp_path):
        db = tmp_path / "state.db"
        with patch("tracksnap.core.httpx.Client", return_value=_make_mock_client()):
            fetch("https://example.com/feed", db_path=db)
            items = fetch("https://example.com/feed", db_path=db, reset=True)
        assert len(items) == 2

    def test_all_items_shows_all(self, tmp_path):
        db = tmp_path / "state.db"
        with patch("tracksnap.core.httpx.Client", return_value=_make_mock_client()):
            fetch("https://example.com/feed", db_path=db)
            items = fetch("https://example.com/feed", db_path=db, all_items=True)
        assert len(items) == 2

    def test_no_url_raises(self, tmp_path):
        db = tmp_path / "state.db"
        with pytest.raises(ValueError, match="URL is required"):
            fetch(None, db_path=db)
