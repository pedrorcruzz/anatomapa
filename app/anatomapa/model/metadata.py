from __future__ import annotations

import json
import os

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")


def load_metadata(assets_dir: str | None = None) -> list[dict]:
    """Load the region metadata from regions.json.

    Parameters
    ----------
    assets_dir:
        Directory holding regions.json. Defaults to the package assets folder.

    Returns
    -------
    list[dict]
        Metadata dictionaries exactly as stored in regions.json.
    """
    base = assets_dir or _ASSETS_DIR
    path = os.path.join(base, "regions.json")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return data["regions"]
