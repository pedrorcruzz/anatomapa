"""Optional SVG rasterisation to PNG/JPEG.

Isolated in its own module behind lazy imports: the library stays zero-dep by
default and only touches `cairosvg`/`Pillow` when the user asks for a raster
format. Without the extra installed, it raises ImportError with install hints.
"""

from __future__ import annotations

import io

_INSTALL_HINT = (
    "Formatos raster (png/jpg/jpeg) exigem o extra opcional 'raster'. "
    "Instale com: pip install anatomapa[raster]"
)


def svg_to_png(svg: str, scale: float = 2.0) -> bytes:
    """Convert SVG into PNG bytes via cairosvg (optional extra)."""
    try:
        import cairosvg
    except ImportError as exc:
        raise ImportError(_INSTALL_HINT) from exc
    return cairosvg.svg2png(bytestring=svg.encode("utf-8"), scale=scale)


def png_to_jpeg(png: bytes, quality: int = 90) -> bytes:
    """Convert PNG bytes into JPEG bytes via Pillow (optional extra).

    JPEG has no alpha channel, so the image is flattened onto a white
    background.
    """
    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError(_INSTALL_HINT) from exc
    source = Image.open(io.BytesIO(png)).convert("RGBA")
    canvas = Image.new("RGB", source.size, (255, 255, 255))
    canvas.paste(source, mask=source.split()[-1])
    out = io.BytesIO()
    canvas.save(out, format="JPEG", quality=quality)
    return out.getvalue()
