# tracksnap

**Stateful RSS/Atom feed tracker. Remembers what you've seen — shows only what's new.**

```bash
pip install tracksnap
```

## The idea

Most feed readers show you everything, every time. tracksnap is different: it tracks which items you've already seen in a local SQLite database and only returns the delta. Run it in a cron job, pipe it into another tool, or use it as part of an agent workflow — you only ever process genuinely new content.

## Usage

```bash
# First run: shows all items, marks them as seen
tracksnap https://hnrss.org/frontpage

# Second run: shows ONLY items you haven't seen yet
tracksnap https://hnrss.org/frontpage

# Show everything regardless of history
tracksnap https://hnrss.org/frontpage --all

# Forget history for this feed, then show all items fresh
tracksnap https://hnrss.org/frontpage --reset

# Limit number of items
tracksnap https://hnrss.org/frontpage --limit 5

# Output formats
tracksnap https://hnrss.org/frontpage --output json
tracksnap https://hnrss.org/frontpage --output table
tracksnap https://hnrss.org/frontpage --output csv
```

## State storage

History is stored in `~/.local/share/tracksnap/state.db` (SQLite). Each feed URL gets its own set of seen item IDs. You can override the path with the `TRACKSNAP_DB` environment variable.

## Automation / agent use

```bash
# In a cron job — only process genuinely new items
tracksnap https://example.com/feed.xml --output json | jq '.items[].title'

# Feed into briefsnap or another pipeline tool
tracksnap https://example.com/feed.xml --output csv >> new_items.csv

# Inspect tool capabilities (ACLI-compliant)
tracksnap introspect
tracksnap skill
```

## Feed support

- **RSS 2.0** — standard `<item>` elements with guid, link, title, author, pubDate, description
- **Atom** — `<entry>` elements with id, title, link, updated/published, author, summary/content

## Part of the snap family

tracksnap is the stateful companion to [feedsnap](https://pypi.org/project/feedsnap/) (stateless RSS reader) and fits naturally into workflows with [briefsnap](https://pypi.org/project/briefsnap/) (morning digest aggregator).

| Tool | What it does |
|------|--------------|
| feedsnap | Stateless RSS/Atom reader |
| tracksnap | Stateful RSS/Atom tracker (only new items) |
| briefsnap | Morning digest aggregator |
| hackersnap | Hacker News top stories |
| bskysnap | Bluesky profile reader |
| reposnap | GitHub repo explorer |
| arxivsnap | arXiv paper search |

## License

MIT
