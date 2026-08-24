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

    Regions form a tree. Painting a parent paints every child that has no value
    of its own: ``Region.LEG`` covers hip, thigh, knee, lower leg, ankle, foot
    and toes at once. Every region except the genital one is bilateral and
    exposes the canonical member, which paints both sides (``Region.HAND``), and
    the lateralised members for a single side (``Region.HAND_LEFT``,
    ``Region.HAND_RIGHT``). Sides follow the observer, not the anatomical
    convention: ``HAND_LEFT`` is the hand drawn on the left of the figure.

    Iterate ``list(Region)`` to discover every valid id.
    """

    # Cabeça e pescoço
    HEAD = "head"
    FACE = "face"
    SKULL = "skull"
    NECK = "neck"

    # Tronco
    TRUNK = "trunk"
    SHOULDER = "shoulder"
    CHEST = "chest"
    UPPER_CHEST = "upper_chest"
    LOWER_CHEST = "lower_chest"
    ABDOMEN = "abdomen"
    UPPER_ABDOMEN = "upper_abdomen"
    LOWER_ABDOMEN = "lower_abdomen"
    BACK = "back"
    UPPER_BACK = "upper_back"
    LOWER_BACK = "lower_back"
    GENITAL = "genital"

    # Membro superior
    ARM = "arm"
    UPPER_ARM = "upper_arm"
    ELBOW = "elbow"
    FOREARM = "forearm"
    WRIST = "wrist"
    HAND = "hand"
    FINGER = "finger"

    # Membro inferior
    LEG = "leg"
    HIP = "hip"
    BUTTOCKS = "buttocks"
    THIGH = "thigh"
    KNEE = "knee"
    LOWER_LEG = "lower_leg"
    ANKLE = "ankle"
    FOOT = "foot"
    TOE = "toe"

    # Variantes de lado: um lado só da mesma região
    HEAD_LEFT = "head_left"
    HEAD_RIGHT = "head_right"
    FACE_LEFT = "face_left"
    FACE_RIGHT = "face_right"
    SKULL_LEFT = "skull_left"
    SKULL_RIGHT = "skull_right"
    NECK_LEFT = "neck_left"
    NECK_RIGHT = "neck_right"
    TRUNK_LEFT = "trunk_left"
    TRUNK_RIGHT = "trunk_right"
    SHOULDER_LEFT = "shoulder_left"
    SHOULDER_RIGHT = "shoulder_right"
    CHEST_LEFT = "chest_left"
    CHEST_RIGHT = "chest_right"
    UPPER_CHEST_LEFT = "upper_chest_left"
    UPPER_CHEST_RIGHT = "upper_chest_right"
    LOWER_CHEST_LEFT = "lower_chest_left"
    LOWER_CHEST_RIGHT = "lower_chest_right"
    ABDOMEN_LEFT = "abdomen_left"
    ABDOMEN_RIGHT = "abdomen_right"
    UPPER_ABDOMEN_LEFT = "upper_abdomen_left"
    UPPER_ABDOMEN_RIGHT = "upper_abdomen_right"
    LOWER_ABDOMEN_LEFT = "lower_abdomen_left"
    LOWER_ABDOMEN_RIGHT = "lower_abdomen_right"
    BACK_LEFT = "back_left"
    BACK_RIGHT = "back_right"
    UPPER_BACK_LEFT = "upper_back_left"
    UPPER_BACK_RIGHT = "upper_back_right"
    LOWER_BACK_LEFT = "lower_back_left"
    LOWER_BACK_RIGHT = "lower_back_right"
    ARM_LEFT = "arm_left"
    ARM_RIGHT = "arm_right"
    UPPER_ARM_LEFT = "upper_arm_left"
    UPPER_ARM_RIGHT = "upper_arm_right"
    ELBOW_LEFT = "elbow_left"
    ELBOW_RIGHT = "elbow_right"
    FOREARM_LEFT = "forearm_left"
    FOREARM_RIGHT = "forearm_right"
    WRIST_LEFT = "wrist_left"
    WRIST_RIGHT = "wrist_right"
    HAND_LEFT = "hand_left"
    HAND_RIGHT = "hand_right"
    FINGER_LEFT = "finger_left"
    FINGER_RIGHT = "finger_right"
    LEG_LEFT = "leg_left"
    LEG_RIGHT = "leg_right"
    HIP_LEFT = "hip_left"
    HIP_RIGHT = "hip_right"
    BUTTOCKS_LEFT = "buttocks_left"
    BUTTOCKS_RIGHT = "buttocks_right"
    THIGH_LEFT = "thigh_left"
    THIGH_RIGHT = "thigh_right"
    KNEE_LEFT = "knee_left"
    KNEE_RIGHT = "knee_right"
    LOWER_LEG_LEFT = "lower_leg_left"
    LOWER_LEG_RIGHT = "lower_leg_right"
    ANKLE_LEFT = "ankle_left"
    ANKLE_RIGHT = "ankle_right"
    FOOT_LEFT = "foot_left"
    FOOT_RIGHT = "foot_right"
    TOE_LEFT = "toe_left"
    TOE_RIGHT = "toe_right"
