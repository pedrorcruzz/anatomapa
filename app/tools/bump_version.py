"""Synchronize every version declaration in the repository with a release tag.

Local development and CI tool, not shipped. Four files declare the version and
they must agree with the tag *in the tagged commit itself*, because Zenodo
archives the release by downloading the tarball at that tag and reading
`.zenodo.json` from it. A fix applied after the tag exists arrives too late.

Files touched:
    pyproject.toml            version         (PEP 440)
    app/anatomapa/__init__.py __version__     (PEP 440)
    CITATION.cff              version, date-released
    .zenodo.json              version, publication_date

Usage:
    python3 tools/bump_version.py v0.4.6            # write
    python3 tools/bump_version.py v0.4.6 --check    # verify only, exit 1 on drift
    python3 tools/bump_version.py v0.4.6 --date 2026-08-21
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PYPROJECT = os.path.join(ROOT, "pyproject.toml")
INIT = os.path.join(ROOT, "app", "anatomapa", "__init__.py")
CITATION = os.path.join(ROOT, "CITATION.cff")
ZENODO = os.path.join(ROOT, ".zenodo.json")

TAG_PATTERN = re.compile(r"^v\d+\.\d+\.\d+(-(?:alpha|beta|rc)\.\d+)?$")


def pep440(tag: str) -> str:
    """Convert a release tag to its PEP 440 form.

    Parameters
    ----------
    tag : str
        Release tag, e.g. ``"v0.4.6"`` or ``"v0.4.6-beta.1"``.

    Returns
    -------
    str
        Version string, e.g. ``"0.4.6"`` or ``"0.4.6b1"``.
    """
    version = tag.removeprefix("v")
    version = re.sub(r"-alpha\.?", "a", version)
    version = re.sub(r"-beta\.?", "b", version)
    version = re.sub(r"-rc\.?", "rc", version)
    return version


def _replace_line(text: str, pattern: str, replacement: str, path: str) -> str:
    """Replace the single line matching ``pattern`` or raise if absent."""
    new_text, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count == 0:
        raise SystemExit(f"{path}: no line matching {pattern!r}; add the field first")
    return new_text


def render_pyproject(text: str, version: str) -> str:
    """Return `pyproject.toml` content with the project version set."""
    return _replace_line(text, r'^version = ".*"', f'version = "{version}"', PYPROJECT)


def render_init(text: str, version: str) -> str:
    """Return `__init__.py` content with `__version__` set."""
    return _replace_line(text, r'^__version__ = ".*"', f'__version__ = "{version}"', INIT)


def render_citation(text: str, version: str, date: str) -> str:
    """Return `CITATION.cff` content with the version and release date set."""
    text = _replace_line(text, r"^version: .*", f"version: {version}", CITATION)
    return _replace_line(
        text, r"^date-released: .*", f'date-released: "{date}"', CITATION
    )


def render_zenodo(text: str, tag: str, date: str) -> str:
    """Return `.zenodo.json` content with the version and publication date set.

    Zenodo keeps the tag form (``v0.4.6``) so the version label stays consistent
    with the records already archived, while `CITATION.cff` uses the bare number
    that the CFF specification expects.
    """
    data = json.loads(text)
    for key in ("version", "publication_date"):
        if key not in data:
            raise SystemExit(f"{ZENODO}: missing key {key!r}; add the field first")
    data["version"] = tag
    data["publication_date"] = date
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def _targets(tag: str, date: str) -> list[tuple[str, str]]:
    """Return the (path, expected content) pair for every versioned file."""
    version = pep440(tag)
    plans = [
        (PYPROJECT, render_pyproject, (version,)),
        (INIT, render_init, (version,)),
        (CITATION, render_citation, (version, date)),
        (ZENODO, render_zenodo, (tag, date)),
    ]
    out = []
    for path, render, extra in plans:
        with open(path, encoding="utf-8") as handle:
            out.append((path, render(handle.read(), *extra)))
    return out


def main(argv: list[str] | None = None) -> int:
    """Entry point: write or verify the version declarations."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag", help="release tag, e.g. v0.4.6 or v0.4.6-beta.1")
    parser.add_argument(
        "--check", action="store_true", help="verify only, do not write"
    )
    parser.add_argument("--date", help="release date as YYYY-MM-DD (default: today UTC)")
    args = parser.parse_args(argv)

    if not TAG_PATTERN.match(args.tag):
        print(f"tag inválida: {args.tag!r} (esperado vX.Y.Z ou vX.Y.Z-beta.N)")
        return 2

    date = args.date or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    # No --check a data vem do arquivo: só a versão precisa bater com a tag
    if args.check and not args.date:
        with open(CITATION, encoding="utf-8") as handle:
            found = re.search(r'^date-released: "?(.+?)"?$', handle.read(), re.MULTILINE)
        if found:
            date = found.group(1)

    drifted = []
    for path, expected in _targets(args.tag, date):
        with open(path, encoding="utf-8") as handle:
            current = handle.read()
        if current == expected:
            continue
        drifted.append(path)
        if not args.check:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(expected)

    rel = [os.path.relpath(p, ROOT) for p in drifted]
    if args.check:
        if drifted:
            print(f"versão fora de sincronia com {args.tag}: {', '.join(rel)}")
            print(f"corrija com: python3 app/tools/bump_version.py {args.tag}")
            return 1
        print(f"versão sincronizada com {args.tag} nos 4 arquivos")
        return 0

    print(f"atualizados para {args.tag}: {', '.join(rel) if rel else 'nada a fazer'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
