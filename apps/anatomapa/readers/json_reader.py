from __future__ import annotations

import io
import json


def from_json(
    source: str | io.TextIOBase,
    region_key: str = "region",
    value_key: str = "value",
    encoding: str = "utf-8",
) -> list[tuple[str, float]]:
    """Parses a JSON file or string into (label, value) pairs.

    Accepts two formats:
    - Object: {"region_id": value, ...}
    - Array: [{"region": "...", "value": ...}, ...]

    Parameters
    ----------
    source:
        File path, JSON string, or a text file-like object.
    region_key:
        Key for the region label in the array-of-objects format.
    value_key:
        Key for the numeric value in the array-of-objects format.
    encoding:
        Encoding used when source is a file path.

    Returns
    -------
    list[tuple[str, float]]
        List of (label, value) pairs.
    """
    if isinstance(source, str):
        stripped = source.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            data = json.loads(stripped)
        else:
            with open(source, encoding=encoding) as fh:
                data = json.load(fh)
    else:
        data = json.load(source)

    if isinstance(data, dict):
        return [(str(k), float(v)) for k, v in data.items()]

    if isinstance(data, list):
        return [(str(item[region_key]), float(item[value_key])) for item in data]

    raise ValueError(f"Unsupported JSON structure: {type(data)}")
