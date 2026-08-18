from __future__ import annotations

import difflib

from anatomapa.domain.model import AnatomicalModel
from anatomapa.resolver.normalize import slugify

# Palavras que indicam lado, em PT e EN (comparadas por slug, sem acento)
_RIGHT_WORDS = {"direita", "direito", "dir", "right"}
_LEFT_WORDS = {"esquerda", "esquerdo", "esq", "left"}

# Plurais irregulares que a remoção simples de "s" não cobre
_IRREGULAR_PLURALS = {
    "feet": "foot",
    "calves": "calf",
    "teeth": "tooth",
}


class ResolutionError(ValueError):
    """Raised when one or more labels cannot be resolved to region ids."""


def _plural_variants(slug: str) -> list[str]:
    """Generate singular variants of a slug so plurals are tolerated."""
    variants = [slug]
    if slug in _IRREGULAR_PLURALS:
        variants.append(_IRREGULAR_PLURALS[slug])
    if slug.endswith("es") and len(slug) > 4:
        variants.append(slug[:-2])
    if slug.endswith("s") and len(slug) > 2:
        variants.append(slug[:-1])
    return variants


def _extract_side(slug: str) -> tuple[str, str | None]:
    """Split the side (left/right) out of a slug, returning (base_slug, side).

    Recognises side words in Portuguese and English in any position (e.g.
    "mao_direita", "right_hand", "hand_right"). With no side word, returns
    (slug, None).
    """
    tokens = [t for t in slug.split("_") if t]
    side: str | None = None
    rest: list[str] = []
    for token in tokens:
        if side is None and token in _RIGHT_WORDS:
            side = "right"
        elif side is None and token in _LEFT_WORDS:
            side = "left"
        else:
            rest.append(token)
    if side is None:
        return slug, None
    return "_".join(rest), side


class _Lookup:
    """Model indices precomputed for fast resolution."""

    def __init__(self, model: AnatomicalModel) -> None:
        # ids canônicos já estão em forma de slug (minúsculo, sem acento)
        self.canonical = set(model.ids())
        self.alias_to_id: dict[str, str] = {}
        self.bilateral: dict[str, bool] = {}
        for region in model.regions():
            self.bilateral[region.id] = region.bilateral
            for alias in region.aliases:
                self.alias_to_id[slugify(alias)] = region.id
            self.alias_to_id[slugify(region.label_pt)] = region.id
            self.alias_to_id[slugify(region.label_en)] = region.id
        self.candidates = sorted(set(self.canonical) | set(self.alias_to_id))

    def match_base(self, slug: str) -> str | None:
        """Resolve a base slug (no side) to its canonical id, tolerating plurals."""
        for cand in _plural_variants(slug):
            if cand in self.canonical:
                return cand
            if cand in self.alias_to_id:
                return self.alias_to_id[cand]
        return None


def _resolve_one(
    label: str,
    lookup: _Lookup,
    region_map: dict[str, str],
    region_map_slug: dict[str, str],
) -> tuple[str | None, str | None]:
    """Resolve a single label. Returns (region_key, failure_reason).

    region_key may be the canonical id ("hand") or a lateralised one
    ("hand_left"). When it does not resolve, region_key is None and the reason
    may carry the explanation.
    """
    # 1. region_map do usuário tem precedência (exato e por slug)
    if label in region_map:
        return region_map[label], None
    label_slug = slugify(label)
    if label_slug in region_map_slug:
        return region_map_slug[label_slug], None

    # 2. Match direto (exato/slug/alias/plural), sem lado
    base_id = lookup.match_base(label_slug)
    if base_id is not None:
        return base_id, None

    # 3. Match com lado (esquerda/direita)
    base_slug, side = _extract_side(label_slug)
    if side is not None and base_slug:
        base_id = lookup.match_base(base_slug)
        if base_id is not None:
            if not lookup.bilateral.get(base_id, False):
                return None, (
                    f"a região {base_id!r} é central e não tem lado "
                    f"esquerdo/direito"
                )
            return f"{base_id}_{side}", None

    return None, None


def _format_errors(unresolved: dict[str, dict]) -> str:
    """Build the batched error message listing every unresolved label."""
    lines = [f"Não foi possível resolver {len(unresolved)} rótulo(s):"]
    for label, info in unresolved.items():
        detail = info["reason"]
        if info["suggestions"]:
            detail += f" (você quis dizer: {', '.join(info['suggestions'])}?)"
        lines.append(f"  - {label!r}: {detail}")
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
    region_map_slug = {slugify(k): v for k, v in region_map.items()}
    lookup = _Lookup(model)

    resolved: dict[str, str] = {}
    unresolved: dict[str, dict] = {}

    for label in labels:
        region_key, reason = _resolve_one(label, lookup, region_map, region_map_slug)
        if region_key is not None:
            resolved[label] = region_key
            continue
        base_slug, _ = _extract_side(slugify(label))
        suggestions = difflib.get_close_matches(
            base_slug or slugify(label), lookup.candidates, n=3, cutoff=0.5
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

    Cascade per label:
    1. User's region_map (takes precedence), by exact match or by slug.
    2. Direct match: canonical id, slug (no accents/case), alias, or plural.
    3. Match with side: "mão direita"/"right hand" -> "hand_right"; a side on
       a central region (head, torso) is an error.
    4. Unresolved: accumulated into a batch error with suggestions (difflib).

    Parameters
    ----------
    labels:
        Input labels (PT or EN, with accents, plural, with side, etc.).
    model:
        AnatomicalModel that provides ids, aliases, and the bilateral flag.
    region_map:
        User-provided mapping: custom label -> region id
        (e.g., {"right_hand": "hand_right"}).
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
