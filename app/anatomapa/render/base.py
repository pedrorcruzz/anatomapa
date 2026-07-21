from __future__ import annotations

import os
from typing import Protocol

from anatomapa.domain.heatmap import Heatmap
from anatomapa.domain.model import AnatomicalModel


class Figure:
    """Contêiner para uma figura SVG renderizada.

    Attributes
    ----------
    _svg:
        O conteúdo SVG como string.
    """

    def __init__(self, svg: str) -> None:
        self._svg = svg

    def to_svg(self) -> str:
        """Retorna o conteúdo SVG como string."""
        return self._svg

    def __str__(self) -> str:
        """Retorna o conteúdo SVG para uso simples como string."""
        return self._svg

    def _repr_svg_(self) -> str:
        """Renderizacao inline de SVG em notebooks Jupyter."""
        return self._svg

    def save(self, path: str | os.PathLike) -> None:
        """Grava o conteúdo SVG em um arquivo.

        Parameters
        ----------
        path:
            Caminho de destino do arquivo.
        """
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self._svg)


class Renderer(Protocol):
    """Protocolo para renderizadores de figura."""

    def render(
        self,
        heatmap: Heatmap,
        model: AnatomicalModel,
        lang: str,
    ) -> Figure:
        """Renderiza um Heatmap em uma Figure."""
        ...
