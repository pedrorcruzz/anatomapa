"""Optional SVG rasterisation to PNG/JPEG.

Isolated in its own module behind lazy imports: the library stays zero-dep by
default and only touches `cairosvg`/`Pillow` when the user asks for a raster
format. Without the extra installed, it raises ImportError with install hints.

The thermal blend is an SVG filter, and raster converters ignore filters, so a
plain conversion loses the blur and shows every hairline gap of the source
drawing as a white band. The blend is therefore rebuilt here on the bitmap:
the colour layer is blurred, clipped to the silhouette and given the same cold
inner glow, then the crisp outline and the legend go back on top. The result
matches the SVG instead of being a flat, banded version of it.
"""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET

_INSTALL_HINT = (
    "Formatos raster (png/jpg/jpeg) exigem o extra opcional 'raster'. "
    "Instale com: pip install anatomapa[raster]"
)

# Mesmas proporções do filtro SVG, para o raster não divergir do vetor
_BLUR_RATIO = 0.010
_GLOW_RATIO = 0.040
_GLOW_COLOR = (10, 12, 80)
_LEGEND_WIDTH_RATIO = 0.24


def _tag(elem: ET.Element) -> str:
    """Tag name without the XML namespace prefix."""
    return elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag


def _viewbox(root: ET.Element) -> tuple[float, float, float, float]:
    """viewBox as (min-x, min-y, width, height), with a safe default."""
    parts = (root.get("viewBox") or "").split()
    if len(parts) != 4:
        return 0.0, 0.0, 400.0, 900.0
    try:
        return tuple(float(p) for p in parts)  # type: ignore[return-value]
    except ValueError:
        return 0.0, 0.0, 400.0, 900.0


def _variant(root: ET.Element, keep) -> str:
    """Serialise a copy of the SVG holding only the children `keep` accepts."""
    import copy

    clone = copy.deepcopy(root)
    for child in list(clone):
        if not keep(child):
            clone.remove(child)
    return ET.tostring(clone, encoding="unicode")


def _mask_svg(root: ET.Element) -> str | None:
    """SVG of the silhouette alone, white on black, to use as an alpha mask.

    In the flat build `body-outline` already carries only the external
    silhouette: the face details live in a separate path.
    """
    outline = next(
        (e for e in root.iter() if e.get("id") == "body-outline"), None
    )
    if outline is None:
        return None
    vx, vy, vw, vh = _viewbox(root)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{vx} {vy} {vw} {vh}">'
        f'<rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" fill="black"/>'
        f'<path d="{outline.get("d", "")}" fill="white"/>'
        f"</svg>"
    )


def _raw_png(svg: str, scale: float) -> bytes:
    """Plain conversion, with no blend rebuilt on top."""
    try:
        import cairosvg
    except ImportError as exc:
        raise ImportError(_INSTALL_HINT) from exc
    return cairosvg.svg2png(bytestring=svg.encode("utf-8"), scale=scale)


def _render(svg: str, scale: float):
    """Rasterise one SVG string into an RGBA image."""
    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError(_INSTALL_HINT) from exc

    return Image.open(io.BytesIO(_raw_png(svg, scale))).convert("RGBA")


def _body_width(root: ET.Element, vw: float) -> float:
    """Width of the drawing itself, with the legend band discounted."""
    has_legend = any(e.get("id") == "legend-bar" for e in root.iter())
    return vw / (1.0 + _LEGEND_WIDTH_RATIO) if has_legend else vw


def svg_to_png(svg: str, scale: float = 2.0) -> bytes:
    """Convert SVG into PNG bytes, rebuilding the thermal blend on the bitmap.

    Parameters
    ----------
    svg:
        SVG document. The filter-free variant is expected: filters are ignored
        by the converter anyway.
    scale:
        Resolution multiplier applied to the viewBox.

    Returns
    -------
    bytes
        PNG data.
    """
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return _raw_png(svg, scale)

    mask_svg = _mask_svg(root)
    regions = next((e for e in root if e.get("id") == "regions"), None)
    if mask_svg is None or regions is None:
        # Sem corpo para mesclar: conversão direta, sem custo de Pillow
        return _raw_png(svg, scale)

    try:
        from PIL import Image, ImageChops, ImageFilter
    except ImportError as exc:
        raise ImportError(_INSTALL_HINT) from exc

    def is_defs(child: ET.Element) -> bool:
        return _tag(child) == "defs"

    def is_background(child: ET.Element) -> bool:
        return child.get("id") == "figure-background"

    colours = _render(
        _variant(root, lambda c: is_defs(c) or c.get("id") == "regions"), scale
    )
    crisp = _render(
        _variant(root, lambda c: not is_background(c) and c.get("id") != "regions"),
        scale,
    )
    base = _render(_variant(root, is_background), scale)
    silhouette = _render(mask_svg, scale).convert("L")

    _, _, vw, _ = _viewbox(root)
    body_w = _body_width(root, vw)
    blur = body_w * _BLUR_RATIO * scale
    glow = body_w * _GLOW_RATIO * scale

    # A cor borra e é recortada na silhueta, como o filtro faz com a máscara
    colours = colours.filter(ImageFilter.GaussianBlur(blur))
    colours.putalpha(ImageChops.multiply(colours.getchannel("A"), silhouette))

    # Brilho frio: floods a cor por dentro das bordas, com a opacidade caindo
    # para o centro. É o feFlood + composite out + blur + composite in do SVG.
    outside = ImageChops.invert(silhouette).filter(ImageFilter.GaussianBlur(glow))
    glow_layer = Image.new("RGBA", colours.size, _GLOW_COLOR + (0,))
    glow_layer.putalpha(ImageChops.multiply(outside, silhouette))

    canvas = base
    canvas.alpha_composite(colours)
    canvas.alpha_composite(glow_layer)
    canvas.alpha_composite(crisp)
    return _to_bytes(canvas)


def _to_bytes(image) -> bytes:
    """Serialise a Pillow image as PNG bytes."""
    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


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
