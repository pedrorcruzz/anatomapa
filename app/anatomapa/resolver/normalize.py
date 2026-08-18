from __future__ import annotations

import unicodedata


def slugify(text: str) -> str:
    """Normalise a label into a canonical slug.

    Steps: lowercase, strip accents, replace hyphens and spaces with
    underscores, trim surrounding whitespace.

    Parameters
    ----------
    text:
        Input label in any language or capitalisation.

    Returns
    -------
    str
        Normalised slug suitable for alias matching.
    """
    text = text.strip().lower()
    # Remove acentos via decomposição unicode
    normalized = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    # Substitui espaços e hifens por underscore
    result = []
    for ch in text:
        if ch in (" ", "-"):
            result.append("_")
        else:
            result.append(ch)
    return "".join(result)
