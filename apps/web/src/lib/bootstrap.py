"""Glue layer between the browser runtime and the anatomapa library.

Every function takes and returns JSON strings so the JavaScript side never has
to handle Python proxies. No anatomical logic lives here: this module only
forwards calls to the library and serialises the answer.
"""

import json
import sys
import zipfile


def install_wheel(wheel_path: str, target_dir: str) -> None:
    """Extract a pure-Python wheel into target_dir and put it on sys.path."""
    with zipfile.ZipFile(wheel_path) as archive:
        archive.extractall(target_dir)
    if target_dir not in sys.path:
        sys.path.insert(0, target_dir)


def library_version() -> str:
    """Return the version of the installed anatomapa library."""
    import anatomapa

    return anatomapa.__version__


def render_heatmap(payload: str) -> str:
    """Render a heatmap and return it as an SVG string.

    Parameters
    ----------
    payload:
        JSON object with "values" (region to value mapping) and "options"
        (keyword arguments accepted by anatomapa.heatmap).
    """
    import anatomapa

    request = json.loads(payload)
    figure = anatomapa.heatmap(request["values"], **request["options"])
    return figure.to_svg()


def list_regions(payload: str) -> str:
    """Return the JSON list of regions accepted as input."""
    import anatomapa

    return json.dumps(anatomapa.list_regions(**json.loads(payload)))


def validate_values(payload: str) -> str:
    """Return the JSON report of which labels the library recognises."""
    import anatomapa

    request = json.loads(payload)
    return json.dumps(anatomapa.validate(request["values"], **request["options"]))
