"""Public region identifiers for building heatmaps directly in code."""

from __future__ import annotations

from enum import Enum


class Region(str, Enum):
    """Canonical anatomical region ids, usable directly as heatmap keys.

    Each member is a plain string (``Region.TRUNK == "trunk"``), so it can be
    used anywhere a region label is accepted, including as ``heatmap`` keys and
    as ``region_map`` values. Using these members instead of free strings gives
    editor autocomplete and turns a typo into an immediate error instead of a
    runtime resolution failure.

    Bilateral regions expose both the canonical member, which colors both sides
    at once (``Region.HAND``), and the lateralised members for a single side
    (``Region.HAND_LEFT``, ``Region.HAND_RIGHT``).

    Iterate ``list(Region)`` to discover every valid id.
    """

    # Regiões centrais (sem lado)
    HEAD = "head"
    TRUNK = "trunk"
    CHEST = "chest"
    ABDOMEN = "abdomen"
    PELVIS = "pelvis"
    BACK = "back"

    # Regiões bilaterais: a forma canônica colore os dois lados
    ARM = "arm"
    FOREARM = "forearm"
    HAND = "hand"
    FINGER = "finger"
    THIGH = "thigh"
    LEG = "leg"
    FOOT = "foot"
    TOE = "toe"

    # Membros lateralizados (um lado só)
    ARM_LEFT = "arm_left"
    ARM_RIGHT = "arm_right"
    FOREARM_LEFT = "forearm_left"
    FOREARM_RIGHT = "forearm_right"
    HAND_LEFT = "hand_left"
    HAND_RIGHT = "hand_right"
    FINGER_LEFT = "finger_left"
    FINGER_RIGHT = "finger_right"
    THIGH_LEFT = "thigh_left"
    THIGH_RIGHT = "thigh_right"
    LEG_LEFT = "leg_left"
    LEG_RIGHT = "leg_right"
    FOOT_LEFT = "foot_left"
    FOOT_RIGHT = "foot_right"
    TOE_LEFT = "toe_left"
    TOE_RIGHT = "toe_right"
