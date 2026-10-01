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


def list_xlsx_sheets(payload: str) -> str:
    """Return the JSON list of sheet names in an uploaded .xlsx file.

    Parameters
    ----------
    payload:
        JSON string with the FS path of the uploaded file.
    """
    import anatomapa

    path = json.loads(payload)
    return json.dumps(anatomapa.list_sheets(path))


def preview_xlsx(payload: str) -> str:
    """Return the JSON preview (sheets, headers, sample rows) of an uploaded .xlsx file.

    Parameters
    ----------
    payload:
        JSON object with "path" and "options" (keyword arguments accepted by
        anatomapa.preview_xlsx: sheet, header, n_rows).
    """
    import anatomapa

    request = json.loads(payload)
    return json.dumps(anatomapa.preview_xlsx(request["path"], **request["options"]))


def read_xlsx(payload: str) -> str:
    """Return the JSON region-to-value mapping parsed from an uploaded .xlsx file.

    Parameters
    ----------
    payload:
        JSON object with "path" and "options" (keyword arguments accepted by
        anatomapa.from_xlsx: sheet, region_col, value_col, header, aggregate).
    """
    import anatomapa

    request = json.loads(payload)
    return json.dumps(anatomapa.from_xlsx(request["path"], **request["options"]))
