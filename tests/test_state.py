"""Tests for tracksnap.state SQLite persistence."""
import pytest
from tracksnap.state import get_conn, get_seen_ids, mark_seen, reset_feed


@pytest.fixture
def conn(tmp_path):
    c = get_conn(tmp_path / "state.db")
    yield c
    c.close()


class TestState:
    def test_empty_seen(self, conn):
        assert get_seen_ids(conn, "https://example.com/feed") == set()

    def test_mark_and_get(self, conn):
        mark_seen(conn, "https://example.com/feed", ["id1", "id2"])
        assert get_seen_ids(conn, "https://example.com/feed") == {"id1", "id2"}

    def test_mark_idempotent(self, conn):
        mark_seen(conn, "https://example.com/feed", ["id1"])
        mark_seen(conn, "https://example.com/feed", ["id1"])
        assert len(get_seen_ids(conn, "https://example.com/feed")) == 1

    def test_reset(self, conn):
        mark_seen(conn, "https://example.com/feed", ["id1", "id2"])
        reset_feed(conn, "https://example.com/feed")
        assert get_seen_ids(conn, "https://example.com/feed") == set()

    def test_separate_feeds(self, conn):
        mark_seen(conn, "https://feed1.com", ["id1"])
        mark_seen(conn, "https://feed2.com", ["id2"])
        assert get_seen_ids(conn, "https://feed1.com") == {"id1"}
        assert "id2" not in get_seen_ids(conn, "https://feed1.com")
