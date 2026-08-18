"""Rasterização opcional de SVG para PNG/JPEG.

Isolado num módulo próprio e com imports preguiçosos: a lib continua zero-dep
por padrão e só toca em `cairosvg`/`Pillow` quando o usuário pede um formato
raster. Sem o extra instalado, levanta ImportError com instrução de instalação.
"""

from __future__ import annotations

import io

_INSTALL_HINT = (
    "Formatos raster (png/jpg/jpeg) exigem o extra opcional 'raster'. "
    "Instale com: pip install anatomapa[raster]"
)


def svg_to_png(svg: str, scale: float = 2.0) -> bytes:
    """Converte SVG em bytes PNG via cairosvg (extra opcional)."""
    try:
        import cairosvg
    except ImportError as exc:
        raise ImportError(_INSTALL_HINT) from exc
    return cairosvg.svg2png(bytestring=svg.encode("utf-8"), scale=scale)


def png_to_jpeg(png: bytes, quality: int = 90) -> bytes:
    """Converte bytes PNG em bytes JPEG via Pillow (extra opcional).

    JPEG não tem canal alfa, então a imagem é achatada sobre um fundo branco.
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
