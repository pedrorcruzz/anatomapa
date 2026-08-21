"""Tests that the four version declarations in the repository agree.

`pyproject.toml`, `anatomapa.__version__`, `CITATION.cff` and `.zenodo.json`
must all state the same release. Zenodo archives the tarball of the tag and
reads `.zenodo.json` from it, so drift here silently mislabels the archived
record. Also covers the PEP 440 conversion used by `tools/bump_version.py`.
"""

import json
import os
import re
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_TOOLS = os.path.join(_ROOT, "app", "tools")

_PYPROJECT = os.path.join(_ROOT, "pyproject.toml")
_CITATION = os.path.join(_ROOT, "CITATION.cff")
_ZENODO = os.path.join(_ROOT, ".zenodo.json")


def _read(path: str) -> str:
    """Return the whole text content of a file."""
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _match(path: str, pattern: str) -> str:
    """Return the first capture group of `pattern` in the file at `path`."""
    found = re.search(pattern, _read(path), re.MULTILINE)
    if found is None:
        raise AssertionError(f"{path}: no line matching {pattern!r}")
    return found.group(1)


def _load_bump_version():
    """Import `tools/bump_version.py`, which lives outside the package."""
    if _TOOLS not in sys.path:
        sys.path.insert(0, _TOOLS)
    import bump_version

    return bump_version


class TestVersionSync(unittest.TestCase):
    """The four declared versions must describe the same release."""

    def setUp(self):
        self.pyproject = _match(_PYPROJECT, r'^version = "(.+)"')

    def test_package_version_matches_pyproject(self):
        import anatomapa

        self.assertEqual(anatomapa.__version__, self.pyproject)

    def test_citation_version_matches_pyproject(self):
        self.assertEqual(_match(_CITATION, r"^version: (.+)$"), self.pyproject)

    def test_zenodo_version_matches_pyproject(self):
        data = json.loads(_read(_ZENODO))
        self.assertEqual(data["version"], f"v{self.pyproject}")

    def test_zenodo_and_citation_share_the_release_date(self):
        data = json.loads(_read(_ZENODO))
        citation_date = _match(_CITATION, r'^date-released: "(.+)"$')
        self.assertEqual(data["publication_date"], citation_date)

    def test_release_date_is_iso_formatted(self):
        data = json.loads(_read(_ZENODO))
        self.assertRegex(data["publication_date"], r"^\d{4}-\d{2}-\d{2}$")


class TestPep440Conversion(unittest.TestCase):
    """Tag to PEP 440 conversion used when bumping the version."""

    def test_stable_tag_only_drops_the_prefix(self):
        self.assertEqual(_load_bump_version().pep440("v0.4.6"), "0.4.6")

    def test_prerelease_suffixes_are_normalized(self):
        pep440 = _load_bump_version().pep440
        self.assertEqual(pep440("v0.4.6-beta.1"), "0.4.6b1")
        self.assertEqual(pep440("v0.4.6-rc.2"), "0.4.6rc2")
        self.assertEqual(pep440("v1.0.0-alpha.3"), "1.0.0a3")


if __name__ == "__main__":
    unittest.main()
