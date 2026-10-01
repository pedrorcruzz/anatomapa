from __future__ import annotations

import os
from typing import Callable, Protocol

from anatomapa.domain.heatmap import Heatmap
from anatomapa.domain.model import AnatomicalModel


_RASTER_FORMATS = {"png", "jpg", "jpeg"}


class Figure:
    """A rendered anatomical figure.

    The underlying representation is always SVG. Raster formats (png, jpg, jpeg)
    are produced on demand and require the optional ``raster`` extra
    (``pip install anatomapa[raster]``).
    """

    def __init__(
        self,
        svg: str,
        format: str = "svg",
        raster_svg: Callable[[], str] | None = None,
    ) -> None:
        self._svg = svg
        self._format = format.lower()
        self._raster_svg = raster_svg
        self._raster_cache: str | None = None

    def _svg_for_raster(self) -> str:
        """SVG actually handed to the rasteriser.

        Raster converters do not implement SVG filters, so the filtered thermal
        blend would come out as a blank body. When the figure carries a
        filter-free variant, it is built once, on first use, and reused.
        """
        if self._raster_svg is None:
            return self._svg
        if self._raster_cache is None:
            self._raster_cache = self._raster_svg()
        return self._raster_cache

    def to_svg(self) -> str:
        """Return the SVG content as a string."""
        return self._svg

    def __str__(self) -> str:
        """Return the SVG content for simple string usage."""
        return self._svg

    def _repr_svg_(self) -> str:
        """Inline SVG rendering for Jupyter notebooks."""
        return self._svg

    def to_png(self, scale: float = 2.0) -> bytes:
        """Render the figure to PNG bytes. Requires the ``raster`` extra."""
        from anatomapa.render.raster import svg_to_png

        return svg_to_png(self._svg_for_raster(), scale=scale)

    def to_jpeg(self, quality: int = 90, scale: float = 2.0) -> bytes:
        """Render the figure to JPEG bytes. Requires the ``raster`` extra."""
        from anatomapa.render.raster import png_to_jpeg, svg_to_png

        return png_to_jpeg(
            svg_to_png(self._svg_for_raster(), scale=scale), quality=quality
        )

    def save(self, path: str | os.PathLike, format: str | None = None) -> None:
        """Write the figure to a file.

        The output format is taken from ``format`` when given, otherwise from the
        path extension, otherwise from the figure's own format. PNG and JPEG
        require the optional ``raster`` extra.

        Parameters
        ----------
        path:
            Destination file path.
        format:
            Optional explicit output format: "svg", "png", "jpg" or "jpeg".
        """
        fmt = (format or self._extension(path) or self._format).lower()
        if fmt in _RASTER_FORMATS:
            data = self.to_jpeg() if fmt in ("jpg", "jpeg") else self.to_png()
            with open(path, "wb") as fh:
                fh.write(data)
            return
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self._svg)

    @staticmethod
    def _extension(path: str | os.PathLike) -> str | None:
        """Extract the known extension from the path, if any."""
        ext = os.path.splitext(os.fspath(path))[1].lower().lstrip(".")
        return ext if ext in ({"svg"} | _RASTER_FORMATS) else None


class Renderer(Protocol):
    """Protocol for figure renderers."""

    def render(
        self,
        heatmap: Heatmap,
        model: AnatomicalModel,
        lang: str,
    ) -> Figure:
        """Render a Heatmap into a Figure."""
        ...
