from __future__ import annotations

import unicodedata


def slugify(text: str) -> str:
    """Normaliza um rótulo para um slug canônico.

    Passos: minúsculas, remove acentos, substitui hifens e espaços por
    underscores, remove espaços nas bordas.

    Parameters
    ----------
    text:
        Rótulo de entrada em qualquer idioma ou capitalização.

    Returns
    -------
    str
        Slug normalizado adequado para correspondência de aliases.
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
