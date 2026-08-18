from __future__ import annotations

from anatomapa.domain.colormap import ColorMap
from anatomapa.domain.scale import LinearScale, LogScale, Scale

# Colormaps registrados por nome
_COLORMAPS: dict[str, ColorMap] = {
    "reds": ColorMap(
        stops=(
            (0.0, (255, 245, 240)),
            (0.25, (252, 174, 145)),
            (0.5, (251, 106, 74)),
            (0.75, (222, 45, 38)),
            (1.0, (165, 15, 21)),
        )
    ),
    "heat": ColorMap(
        stops=(
            (0.0, (255, 255, 204)),
            (0.33, (254, 178, 76)),
            (0.66, (240, 59, 32)),
            (1.0, (128, 0, 38)),
        )
    ),
    "viridis": ColorMap(
        stops=(
            (0.0, (68, 1, 84)),
            (0.25, (59, 82, 139)),
            (0.5, (33, 145, 140)),
            (0.75, (94, 201, 98)),
            (1.0, (253, 231, 37)),
        )
    ),
    "blues": ColorMap(
        stops=(
            (0.0, (247, 251, 255)),
            (0.25, (198, 219, 239)),
            (0.5, (107, 174, 214)),
            (0.75, (49, 130, 189)),
            (1.0, (8, 48, 107)),
        )
    ),
    "greens": ColorMap(
        stops=(
            (0.0, (247, 252, 245)),
            (0.25, (199, 233, 192)),
            (0.5, (116, 196, 118)),
            (0.75, (49, 163, 84)),
            (1.0, (0, 68, 27)),
        )
    ),
    "thermal": ColorMap(
        stops=(
            (0.00, (10, 12, 80)),
            (0.16, (0, 55, 220)),
            (0.33, (0, 170, 235)),
            (0.50, (0, 215, 120)),
            (0.64, (150, 225, 0)),
            (0.78, (250, 220, 0)),
            (0.90, (255, 175, 0)),
            (1.00, (255, 130, 0)),
        )
    ),
}

# Escalas registradas por nome
_SCALES: dict[str, Scale] = {
    "linear": LinearScale(),
    "log": LogScale(),
}


def get_colormap(name: str) -> ColorMap:
    """Return a ColorMap registered under the given name.

    Raises ValueError for unknown names.
    """
    try:
        return _COLORMAPS[name]
    except KeyError:
        available = sorted(_COLORMAPS)
        raise ValueError(
            f"Unknown colormap {name!r}. Available: {available}"
        )


def get_scale(name: str) -> Scale:
    """Return a Scale registered under the given name.

    Raises ValueError for unknown names.
    """
    try:
        return _SCALES[name]
    except KeyError:
        available = sorted(_SCALES)
        raise ValueError(f"Unknown scale {name!r}. Available: {available}")


def list_colormaps() -> list[str]:
    """Return a sorted list with the names of the available colormaps."""
    return sorted(_COLORMAPS)


def list_scales() -> list[str]:
    """Return a sorted list with the names of the available scales."""
    return sorted(_SCALES)
