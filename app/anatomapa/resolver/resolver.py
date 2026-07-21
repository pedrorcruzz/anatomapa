from __future__ import annotations

import difflib

from anatomapa.domain.model import AnatomicalModel
from anatomapa.resolver.normalize import slugify


class ResolutionError(ValueError):
    """Lançado quando um rótulo não pode ser resolvido para um id canônico de região."""


def resolve(
    labels: list[str],
    model: AnatomicalModel,
    region_map: dict[str, str] | None = None,
) -> dict[str, str]:
    """Resolve uma lista de rótulos para ids canônicos de regiões.

    Cascata de resolução por rótulo:
    1. Correspondência exata com ids canônicos.
    2. Correspondência por slug (minúsculas, sem acentos, hifens/espaços como underscores).
    3. Correspondência por aliases conhecidos (comparação por slug).
    4. Correspondência via region_map fornecido pelo usuário (exata).
    5. Lança ResolutionError com sugestão do difflib.

    Parameters
    ----------
    labels:
        Rótulos de entrada a resolver (podem ser PT ou EN, com acentos, etc.).
    model:
        AnatomicalModel que fornece ids canônicos e dados de alias.
    region_map:
        Mapeamento opcional do usuário de rótulo customizado para id canônico.

    Returns
    -------
    dict[str, str]
        Mapeamento do rótulo original para o id canônico resolvido.
    """
    region_map = region_map or {}
    result: dict[str, str] = {}

    canonical_ids = set(model.ids())
    # Pré-computa mapa de slug -> id canônico
    slug_to_id: dict[str, str] = {slugify(rid): rid for rid in model.ids()}

    # Mapa de slug de alias -> id canônico
    alias_to_id: dict[str, str] = {}
    for region in model.regions():
        for alias in region.aliases:
            alias_slug = slugify(alias)
            alias_to_id[alias_slug] = region.id
        # Adiciona labels PT e EN como aliases implícitos
        alias_to_id[slugify(region.label_pt)] = region.id
        alias_to_id[slugify(region.label_en)] = region.id

    # Candidatos para sugestão de erro
    all_candidates = list(canonical_ids) + list(alias_to_id.keys())

    for label in labels:
        label_slug = slugify(label)

        # 1. Match exato contra ids canônicos
        if label in canonical_ids:
            result[label] = label
            continue

        # 2. Match normalizado contra ids canônicos
        if label_slug in slug_to_id:
            result[label] = slug_to_id[label_slug]
            continue

        # 3. Match via aliases (PT + EN + declarados)
        if label_slug in alias_to_id:
            result[label] = alias_to_id[label_slug]
            continue

        # 4. Match via region_map do usuário
        if label in region_map:
            result[label] = region_map[label]
            continue

        # 5. Erro com sugestão
        suggestions = difflib.get_close_matches(
            label_slug, all_candidates, n=3, cutoff=0.5
        )
        suggestion_text = (
            f" Suggestions: {suggestions}" if suggestions else ""
        )
        raise ResolutionError(
            f"Cannot resolve label {label!r} to a known region id.{suggestion_text}"
        )

    return result
