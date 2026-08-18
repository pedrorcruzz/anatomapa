from __future__ import annotations

import difflib

from anatomapa.domain.model import AnatomicalModel

_SIDES = ("left", "right")


class ResolutionError(ValueError):
    """Raised when one or more labels cannot be resolved to region ids."""


class _Lookup:
    """Model indices precomputed for fast resolution."""

    def __init__(self, model: AnatomicalModel) -> None:
        self.canonical = set(model.ids())
        self.bilateral = {r.id: r.bilateral for r in model.regions()}
        lateralised = {
            f"{rid}_{side}"
            for rid, is_bilateral in self.bilateral.items()
            if is_bilateral
            for side in _SIDES
        }
        self.candidates = sorted(self.canonical | lateralised)

    def match(self, key: str) -> tuple[str | None, str | None]:
        """Match a key against the region ids, exactly as written.

        Parameters
        ----------
        key:
            Canonical id ("hand") or lateralised id ("hand_left").

        Returns
        -------
        tuple[str | None, str | None]
            (region_key, failure_reason). Both are None when the key is simply
            unknown, with no extra explanation to give.
        """
        if key in self.canonical:
            return key, None

        base, separator, side = key.rpartition("_")
        if separator and side in _SIDES and base in self.canonical:
            if not self.bilateral.get(base, False):
                return None, (
                    f"a região {base!r} é central e não tem lado "
                    f"esquerdo/direito"
                )
            return key, None

        return None, None


def _resolve_one(
    label: str,
    lookup: _Lookup,
    region_map: dict[str, str],
) -> tuple[str | None, str | None]:
    """Resolve a single label. Returns (region_key, failure_reason).

    Resolution is strict: the label must be a region id written exactly as
    defined, or a key of the user's region_map. Nothing is guessed.
    """
    if label in region_map:
        target = region_map[label]
        region_key, reason = lookup.match(target)
        if region_key is None:
            return None, reason or (
                f"o region_map aponta para {target!r}, que não é uma região válida"
            )
        return region_key, None

    return lookup.match(label)


def _format_errors(unresolved: dict[str, dict]) -> str:
    """Build the batched error message listing every unresolved label."""
    lines = [f"Não foi possível resolver {len(unresolved)} rótulo(s):"]
    for label, info in unresolved.items():
        detail = info["reason"]
        if info["suggestions"]:
            detail += f" (você quis dizer: {', '.join(info['suggestions'])}?)"
        lines.append(f"  - {label!r}: {detail}")
    lines.append(
        "Use um id de região exato (veja anatomapa.list_regions() ou o enum "
        "Region) ou informe region_map para os seus rótulos."
    )
    return "\n".join(lines)


def analyze(
    labels: list[str],
    model: AnatomicalModel,
    region_map: dict[str, str] | None = None,
) -> dict[str, dict]:
    """Analyse labels WITHOUT raising (dry run). Backs resolve() and validate().

    Returns
    -------
    dict
        {"resolved": {label: region_key}, "unresolved": {label: {"reason", "suggestions"}}}.
    """
    region_map = region_map or {}
    lookup = _Lookup(model)

    resolved: dict[str, str] = {}
    unresolved: dict[str, dict] = {}

    for label in labels:
        region_key, reason = _resolve_one(label, lookup, region_map)
        if region_key is not None:
            resolved[label] = region_key
            continue
        suggestions = difflib.get_close_matches(
            str(label).strip().lower(), lookup.candidates, n=3, cutoff=0.5
        )
        unresolved[label] = {
            "reason": reason or "região desconhecida",
            "suggestions": suggestions,
        }

    return {"resolved": resolved, "unresolved": unresolved}


def resolve(
    labels: list[str],
    model: AnatomicalModel,
    region_map: dict[str, str] | None = None,
    strict: bool = True,
) -> dict[str, str]:
    """Resolves labels to region ids (canonical or lateralized).

    Resolution is exact by design: a label is accepted only when it is a region
    id written exactly as defined ("hand", "hand_left"), or a key of the user's
    region_map. Names in Portuguese, plurals, accents and sides spelled out are
    NOT interpreted, so a spreadsheet label such as "MÃO" must be mapped
    explicitly through region_map.

    Parameters
    ----------
    labels:
        Input labels: region ids, Region enum members, or region_map keys.
    model:
        AnatomicalModel that provides the ids and the bilateral flag.
    region_map:
        User-provided mapping: custom label -> region id
        (e.g., {"MÃO": "hand", "Membro Sup Dir": "arm_right"}).
    strict:
        If True (default), raises ResolutionError listing all unresolved
        labels. If False, unresolved labels are simply omitted from the result.

    Returns
    -------
    dict[str, str]
        Mapping from the original label to the resolved region id.

    Raises
    ------
    ResolutionError
        In strict mode, when any label could not be resolved.
    """
    report = analyze(labels, model, region_map)
    if report["unresolved"] and strict:
        raise ResolutionError(_format_errors(report["unresolved"]))
    return report["resolved"]
