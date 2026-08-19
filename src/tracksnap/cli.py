"""tracksnap CLI — stateful RSS/Atom feed tracker."""
from __future__ import annotations

import sys

import click

from .core import fetch, to_csv, to_json, to_table, to_text
from .introspect import get_introspect_json, get_skill_md

_ACLI_COMMANDS = {"introspect", "skill"}


def _handle_acli_command(cmd: str) -> None:
    if cmd == "introspect":
        print(get_introspect_json())
    elif cmd == "skill":
        print(get_skill_md())


@click.command()
@click.argument("url", required=False, default=None)
@click.option(
    "--limit", "-n",
    default=10, show_default=True,
    help="Max items to return.",
)
@click.option(
    "--output", "-o",
    default="text", show_default=True,
    type=click.Choice(["text", "json", "table", "csv"]),
    help="Output format.",
)
@click.option(
    "--all", "all_items",
    is_flag=True,
    help="Show all items, not just new ones.",
)
@click.option(
    "--reset",
    is_flag=True,
    help="Clear history for this URL, then show all items.",
)
def main(url, limit, output, all_items, reset):
    """Stateful RSS/Atom feed tracker — shows only items you haven't seen yet.

    Special commands: tracksnap introspect | tracksnap skill
    """
    if url in _ACLI_COMMANDS:
        _handle_acli_command(url)
        sys.exit(0)

    if not url:
        click.echo("Error: URL is required.", err=True)
        sys.exit(1)

    items = fetch(url, limit=limit, all_items=all_items, reset=reset)

    if output == "text":
        click.echo(to_text(items))
    elif output == "json":
        click.echo(to_json(items))
    elif output == "table":
        click.echo(to_table(items))
    else:
        click.echo(to_csv(items), nl=False)


if __name__ == "__main__":
    main()
