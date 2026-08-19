"""Agent-CLI introspection: `tracksnap introspect` and `tracksnap skill`.

Lets any AI agent discover how to drive this tool without a human in the loop.
"""
import json

from . import __version__


def get_introspect_json() -> str:
    return json.dumps(
        {
            "name": "tracksnap",
            "version": __version__,
            "description": "Stateful URL and feed change tracker — remembers what it's seen, shows only what's new.",
            "commands": [
                {
                    "usage": "tracksnap [TARGET] --limit N --output text|json|table|csv",
                    "description": "Stateful URL and feed change tracker — remembers what it's seen, shows only what's new.",
                }
            ],
        },
        indent=2,
    )


def get_skill_md() -> str:
    return (
        "# tracksnap\n\n"
        "Stateful URL and feed change tracker — remembers what it's seen, shows only what's new.\n\n"
        "## Usage\n\n"
        "```\n"
        "tracksnap [TARGET] --limit 10 --output json\n"
        "```\n\n"
        "Outputs: text (default), json, table, csv.\n"
    )
