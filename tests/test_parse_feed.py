"""Tests for RSS 2.0 and Atom feed parsing."""
import pytest
from tracksnap.core import parse_feed

RSS_XML = """\
<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>First Post</title>
      <link>https://example.com/1</link>
      <guid>https://example.com/1</guid>
      <author>alice</author>
      <pubDate>Tue, 10 Jul 2026 17:43:30 +0000</pubDate>
      <description>Some &lt;b&gt;bold&lt;/b&gt; text.</description>
    </item>
    <item>
      <title>Second Post</title>
      <link>https://example.com/2</link>
      <guid>guid-2</guid>
    </item>
  </channel>
</rss>"""

ATOM_XML = """\
<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Atom Feed</title>
  <entry>
    <id>tag:example.com,2026:1</id>
    <title>Atom Entry</title>
    <link href="https://example.com/atom/1" rel="alternate"/>
    <updated>2026-07-10T17:43:30+00:00</updated>
    <author><name>bob</name></author>
    <summary>Summary text</summary>
  </entry>
</feed>"""


class TestParseRss:
    def test_count(self):
        assert len(parse_feed(RSS_XML)) == 2

    def test_title(self):
        assert parse_feed(RSS_XML)[0].title == "First Post"

    def test_url(self):
        assert parse_feed(RSS_XML)[0].url == "https://example.com/1"

    def test_guid(self):
        assert parse_feed(RSS_XML)[0].guid == "https://example.com/1"

    def test_author(self):
        assert parse_feed(RSS_XML)[0].author == "alice"

    def test_created_at_not_none(self):
        assert parse_feed(RSS_XML)[0].created_at is not None

    def test_body_no_html(self):
        body = parse_feed(RSS_XML)[0].body
        assert "<b>" not in body
        assert "bold" in body


class TestParseAtom:
    def test_count(self):
        assert len(parse_feed(ATOM_XML)) == 1

    def test_title(self):
        assert parse_feed(ATOM_XML)[0].title == "Atom Entry"

    def test_url(self):
        assert parse_feed(ATOM_XML)[0].url == "https://example.com/atom/1"

    def test_guid(self):
        assert parse_feed(ATOM_XML)[0].guid == "tag:example.com,2026:1"

    def test_author(self):
        assert parse_feed(ATOM_XML)[0].author == "bob"

    def test_created_at_not_none(self):
        assert parse_feed(ATOM_XML)[0].created_at is not None
