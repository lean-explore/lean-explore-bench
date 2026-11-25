"""Apply external reporting aliases without changing numeric measurements."""

import json


def relabel(value, aliases):
    """Replace exact string labels and reject aliases that merge object keys."""
    if isinstance(value, dict):
        renamed = [aliases.get(key, key) for key in value]
        if len(set(renamed)) != len(renamed):
            raise ValueError("Reporting aliases merge distinct keys")
        return {
            aliases.get(key, key): relabel(item, aliases) for key, item in value.items()
        }
    if isinstance(value, list):
        return [relabel(item, aliases) for item in value]
    return aliases.get(value, value) if isinstance(value, str) else value


def load(path, aliases_path=None):
    """Read an aggregate artifact and apply an optional external label mapping."""
    aliases = json.loads(aliases_path.read_text()) if aliases_path else {}
    if not isinstance(aliases, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in aliases.items()
    ):
        raise ValueError("Reporting aliases must map strings to strings")
    return relabel(json.loads(path.read_text()), aliases)
