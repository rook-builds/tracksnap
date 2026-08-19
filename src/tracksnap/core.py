"""tracksnap core — stateful RSS/Atom feed tracker."""
from __future__ import annotations

import csv
import io
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional

import httpx

from .state import get_conn, get_seen_ids, mark_seen, reset_feed


@dataclass
class Item:
    """One entry from an RSS/Atom feed."""

    title: str
    url: str
    author: str = ""
    score: int = 0
    comments: int = 0
    created_at: Optional[datetime] = None
    body: str = ""
    guid: str = ""  # internal dedup key; excluded from public output

    def _created_iso(self) -> str:
        return self.created_at.isoformat() if self.created_at else ""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _item_guid(item: Item) -> str:
    """Best available unique ID for deduplication."""
    return item.guid or item.url or item.title


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _parse_rss_date(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(s.strip())
    except Exception:
        return None


def _parse_iso_date(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.strip())
    except Exception:
        return None


def _parse_rss(root: ET.Element) -> list[Item]:
    items = []
    for entry in root.findall("./channel/item"):
        guid = (
            entry.findtext("guid") or entry.findtext("link") or ""
        ).strip()
        title = entry.findtext("title", "").strip()
        url = entry.findtext("link", "").strip()
        author = (
            entry.findtext("author")
            or entry.findtext("{http://purl.org/dc/elements/1.1/}creator")
            or ""
        ).strip()
        body = _strip_html(entry.findtext("description", ""))
        created_at = _parse_rss_date(entry.findtext("pubDate", ""))
        items.append(
            Item(
                title=title,
                url=url,
                author=author,
                body=body,
                created_at=created_at,
                guid=guid,
            )
        )
    return items


def _parse_atom(root: ET.Element) -> list[Item]:
    ns = "{http://www.w3.org/2005/Atom}"
    items = []
    for entry in root.findall(f"{ns}entry"):
        guid = entry.findtext(f"{ns}id", "").strip()
        title = entry.findtext(f"{ns}title", "").strip()

        url = ""
        for link in entry.findall(f"{ns}link"):
            rel = link.get("rel", "alternate")
            if rel == "alternate" or not url:
                url = link.get("href", "")

        author_el = entry.find(f"{ns}author")
        author = ""
        if author_el is not None:
            author = (author_el.findtext(f"{ns}name") or "").strip()

        body = _strip_html(
            entry.findtext(f"{ns}summary", "")
            or entry.findtext(f"{ns}content", "")
        )
        created_at = _parse_iso_date(
            entry.findtext(f"{ns}updated")
            or entry.findtext(f"{ns}published")
            or ""
        )
        items.append(
            Item(
                title=title,
                url=url,
                author=author,
                body=body,
                created_at=created_at,
                guid=guid,
            )
        )
    return items


def parse_feed(xml_text: str) -> list[Item]:
    """Parse an RSS 2.0 or Atom feed and return a list of Items."""
    root = ET.fromstring(xml_text)
    if root.tag == "rss":
        return _parse_rss(root)
    if root.tag == "{http://www.w3.org/2005/Atom}feed":
        return _parse_atom(root)
    raise ValueError(f"Unknown feed format: root tag '{root.tag}'")


# ---------------------------------------------------------------------------
# fetch — the public interface
# ---------------------------------------------------------------------------

def fetch(
    url: Optional[str] = None,
    limit: int = 10,
    all_items: bool = False,
    reset: bool = False,
    db_path=None,
) -> list[Item]:
    """Fetch RSS/Atom feed at url, returning only items not previously seen.

    Args:
        url:       Feed URL (required).
        limit:     Max items to return.
        all_items: If True, return all items regardless of seen history.
        reset:     If True, clear seen history for this URL before fetching.
        db_path:   Override DB path (for testing).
    """
    if not url:
        raise ValueError("URL is required")

    with httpx.Client(
        timeout=15,
        follow_redirects=True,
        headers={"User-Agent": "tracksnap/0.1.0"},
    ) as c:
        resp = c.get(url)
        resp.raise_for_status()

    parsed = parse_feed(resp.text)

    conn = get_conn(db_path)
    try:
        if reset:
            reset_feed(conn, url)

        if all_items or reset:
            mark_seen(conn, url, [_item_guid(it) for it in parsed])
            return parsed[:limit]

        seen = get_seen_ids(conn, url)
        new_items = [it for it in parsed if _item_guid(it) not in seen]
        mark_seen(conn, url, [_item_guid(it) for it in parsed])
        return new_items[:limit]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

def to_text(items: list[Item], source: str = "tracksnap") -> str:
    if not items:
        return f"# {source}\n\nNo items found."
    lines = [f"# {source}", ""]
    for i, it in enumerate(items, 1):
        meta = []
        if it.score:
            meta.append(f"{it.score} points")
        if it.comments:
            meta.append(f"{it.comments} comments")
        if it.author:
            meta.append(f"by {it.author}")
        suffix = f"  ({' · '.join(meta)})" if meta else ""
        lines.append(f"{i}. **{it.title}**{suffix}")
        if it.url:
            lines.append(f"   {it.url}")
        if it.body:
            lines.append(f"   {it.body}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def to_json(items: list[Item], source: str = "tracksnap") -> str:
    def _item_dict(it: Item) -> dict:
        d = asdict(it)
        d.pop("guid", None)  # internal tracking field
        d["created_at"] = it._created_iso()
        return d

    payload = {
        "source": source,
        "count": len(items),
        "items": [_item_dict(it) for it in items],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def to_table(items: list[Item], source: str = "tracksnap") -> str:
    if not items:
        return "No items found."
    header = "| # | Title | Score | Comments | Author |"
    sep = "|---|-------|-------|----------|--------|"
    rows = [header, sep]
    for i, it in enumerate(items, 1):
        title = it.title.replace("|", "\\|")
        rows.append(
            f"| {i} | {title} | {it.score} | {it.comments} | {it.author} |"
        )
    return "\n".join(rows)


def to_csv(items: list[Item], source: str = "tracksnap") -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["title", "url", "author", "score", "comments", "created_at"])
    for it in items:
        w.writerow(
            [it.title, it.url, it.author, it.score, it.comments, it._created_iso()]
        )
    return buf.getvalue()
