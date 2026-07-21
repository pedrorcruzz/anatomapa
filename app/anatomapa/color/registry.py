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
            (0.00, (0, 0, 80)),
            (0.12, (0, 0, 255)),
            (0.26, (0, 190, 255)),
            (0.40, (0, 235, 120)),
            (0.52, (120, 255, 0)),
            (0.62, (255, 255, 0)),
            (0.75, (255, 145, 0)),
            (0.88, (255, 0, 0)),
            (1.00, (255, 255, 255)),
        )
    ),
}

# Escalas registradas por nome
_SCALES: dict[str, Scale] = {
    "linear": LinearScale(),
    "log": LogScale(),
}


def get_colormap(name: str) -> ColorMap:
    """Retorna um ColorMap registrado pelo nome.

    Lança ValueError para nomes desconhecidos.
    """
    try:
        return _COLORMAPS[name]
    except KeyError:
        available = sorted(_COLORMAPS)
        raise ValueError(
            f"Unknown colormap {name!r}. Available: {available}"
        )


def get_scale(name: str) -> Scale:
    """Retorna uma Scale registrada pelo nome.

    Lança ValueError para nomes desconhecidos.
    """
    try:
        return _SCALES[name]
    except KeyError:
        available = sorted(_SCALES)
        raise ValueError(f"Unknown scale {name!r}. Available: {available}")


def list_colormaps() -> list[str]:
    """Retorna lista ordenada com os nomes dos colormaps disponíveis."""
    return sorted(_COLORMAPS)


def list_scales() -> list[str]:
    """Retorna lista ordenada com os nomes das escalas disponíveis."""
    return sorted(_SCALES)
