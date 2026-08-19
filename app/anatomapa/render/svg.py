from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from anatomapa.domain.colormap import ColorMap
from anatomapa.domain.heatmap import Heatmap
from anatomapa.domain.model import AnatomicalModel
from anatomapa.render.base import Figure

_BILATERAL_SIDES = ("left", "right")

_SVG_NS = "http://www.w3.org/2000/svg"

# Fundos suportados e a fração de largura reservada à legenda (viewBox expandido)
_VALID_BACKGROUNDS = ("dark", "light", "transparent")
_LEGEND_WIDTH_RATIO = 0.24

# Preenchimentos para região sem dado ("missing"): "neutral" sinaliza ausência
# de dado com um cinza discreto; "cold" reproduz o visual antigo (cor fria do
# colormap em t=0.0), útil quando o autor quer tratar "sem dado" como "frio".
_VALID_MISSING = ("neutral", "cold")
_MISSING_NEUTRAL_HEX = "#9aa0a6"


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    """Convert (R, G, B) into a hexadecimal CSS colour string."""
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def _tag(elem: ET.Element) -> str:
    """Tag name without the XML namespace prefix."""
    return elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag


def _validate_background(background: str) -> None:
    """Validate the background parameter, raising a clear error if unknown."""
    if background not in _VALID_BACKGROUNDS:
        raise ValueError(
            f"Fundo inválido: {background!r}. Use um de {list(_VALID_BACKGROUNDS)}."
        )


def _validate_missing(missing: str) -> None:
    """Validate the missing parameter, raising a clear error if unknown."""
    if missing not in _VALID_MISSING:
        raise ValueError(
            f"Missing inválido: {missing!r}. Use um de {list(_VALID_MISSING)}."
        )


def _missing_fill(missing: str, colormap: ColorMap | None) -> str:
    """Fill colour for a region (path) with no data, according to `missing`.

    "neutral" (default) uses a discreet grey, distinct from the colormap's
    cold end, so "no data" never reads as "low value". "cold" uses
    colormap.color_at(0.0), the older behaviour, when available.
    """
    if missing == "cold" and colormap is not None:
        return _rgb_to_hex(colormap.color_at(0.0))
    return _MISSING_NEUTRAL_HEX


def _background_fill(background: str) -> str | None:
    """Background fill colour, or None when transparent (no rectangle)."""
    return {"dark": "#0a0a0a", "light": "#ffffff", "transparent": None}[background]


def _legend_width(vw: float, legend: bool) -> float:
    """Width reserved for the legend (0 when legend=False)."""
    return vw * _LEGEND_WIDTH_RATIO if legend else 0.0


def _legend_ui_colors(background: str) -> tuple[str, str, str, str]:
    """Legend UI colours adapted to the background brightness.

    Returns (primary text, secondary text, bar border, tick stroke). A light
    background uses dark text; a dark or transparent one uses light text.
    """
    if background == "light":
        return "#1a1a1a", "#4a4a4a", "rgba(0,0,0,0.25)", "rgba(0,0,0,0.45)"
    return "#f2f2f2", "#d8d8d8", "rgba(255,255,255,0.25)", "rgba(255,255,255,0.45)"


def _append_background_rect(
    root: ET.Element, vx: float, vy: float, total_w: float, vh: float, background: str
) -> None:
    """Insert a background <rect> covering the whole viewBox (body + legend).

    Nothing is inserted when background="transparent". The rectangle is always
    the first visual element, the bottom-most layer.
    """
    fill = _background_fill(background)
    if fill is None:
        return
    insert_at = 1 if (len(root) > 0 and _tag(root[0]) == "title") else 0
    rect = ET.Element("rect")
    rect.set("id", "figure-background")
    rect.set("x", str(vx))
    rect.set("y", str(vy))
    rect.set("width", str(total_w))
    rect.set("height", str(vh))
    rect.set("fill", fill)
    root.insert(insert_at, rect)


def _canonical_and_side(elem_id: str) -> tuple[str, str | None]:
    """Split a path id into (canonical id, side), where side is 'left', 'right' or None."""
    for suffix, side in (("-left", "left"), ("-right", "right")):
        if elem_id.endswith(suffix):
            return elem_id[: -len(suffix)], side
    return elem_id, None


def _color_for(
    canonical: str,
    side: str | None,
    colors: dict[str, tuple[int, int, int]],
) -> tuple[int, int, int] | None:
    """Colour for a path: prefers the lateralised key (e.g. 'hand_left') when
    present, otherwise falls back to the canonical one ('hand'). Returns None
    when neither has a value."""
    if side is not None:
        key = f"{canonical}_{side}"
        if key in colors:
            return colors[key]
    return colors.get(canonical)


def _parse_viewbox(svg_string: str) -> tuple[float, float, float, float]:
    """Extract min-x, min-y, width and height from the SVG viewBox attribute."""
    try:
        root = ET.fromstring(svg_string)
    except ET.ParseError:
        return 0.0, 0.0, 400.0, 900.0
    vb = root.get("viewBox", "")
    if not vb:
        return 0.0, 0.0, 400.0, 900.0
    parts = vb.split()
    if len(parts) != 4:
        return 0.0, 0.0, 400.0, 900.0
    try:
        return float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
    except ValueError:
        return 0.0, 0.0, 400.0, 900.0


def _viewbox_of(root: ET.Element) -> tuple[float, float, float, float]:
    """Read the viewBox already set on an element, as (min-x, min-y, width, height)."""
    parts = (root.get("viewBox") or "").split()
    if len(parts) != 4:
        return 0.0, 0.0, 400.0, 900.0
    try:
        return float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
    except ValueError:
        return 0.0, 0.0, 400.0, 900.0


def _body_width(root: ET.Element, vw: float) -> float:
    """Width of the drawing itself, with the legend band discounted.

    The legend runs before the title and widens the viewBox to the right by a
    fixed fraction of the body width. Centring the title on the widened box
    would push it towards the legend, so the band is taken back out here.
    """
    has_legend = any(elem.get("id") == "legend-bar" for elem in root.iter())
    if not has_legend:
        return vw
    return vw / (1.0 + _LEGEND_WIDTH_RATIO)


def _append_title(root: ET.Element, title: str | None, background: str) -> None:
    """Draw the figure title in a band above the drawing, growing the viewBox upwards.

    Does nothing without a title, so a figure with none keeps exactly the same
    layout. Must run after the legend, which widens the viewBox sideways: the
    title is centred on the body, not on the body plus legend.
    """
    if not title:
        return

    vx, vy, vw, vh = _viewbox_of(root)
    body_w = _body_width(root, vw)
    base_size = vh * 0.030
    # Título longo encolhe para caber na largura (~0.58 de avanço por caractere
    # em Helvetica negrito), mas a faixa mantém a altura do tamanho cheio
    fitted = body_w * 0.92 / max(len(title) * 0.58, 1.0)
    font_size = min(base_size, fitted)
    band_h = base_size * 2.4
    new_vy = round(vy - band_h, 2)
    new_vh = round(vh + band_h, 2)
    root.set("viewBox", f"{vx} {new_vy} {vw} {new_vh}")

    # O fundo já foi criado com a altura antiga: cresce junto, senão fica uma
    # tira sem fundo em cima
    for elem in root.iter():
        if elem.get("id") == "figure-background":
            elem.set("y", str(new_vy))
            elem.set("height", str(new_vh))
            break

    ui_main = _legend_ui_colors(background)[0]
    text = ET.SubElement(root, "text")
    text.set("id", "figure-title")
    text.set("x", str(round(vx + body_w / 2.0, 2)))
    text.set("y", str(round(new_vy + band_h * 0.62, 2)))
    text.set("text-anchor", "middle")
    text.set("font-size", str(round(font_size, 2)))
    text.set("font-family", "Helvetica, Arial, sans-serif")
    text.set("font-weight", "600")
    text.set("fill", ui_main)
    text.text = title


def _extract_body_outline_d(svg_string: str) -> str | None:
    """Extract the d attribute of the path with id='body-outline', or None if absent."""
    try:
        root = ET.fromstring(svg_string)
    except ET.ParseError:
        return None
    for elem in root.iter():
        if elem.get("id") == "body-outline":
            return elem.get("d")
    return None


def _split_outline_d(outline_d: str) -> tuple[str, str]:
    """Split an outline path into (silhouette, details) by subpath area.

    The subpath with the largest bounding box is the external silhouette;
    every other subpath is interior detail (face, hands, back grooves).
    Assets only use absolute commands, so subpaths start at ``M``.
    """
    subpaths = [s.strip() for s in re.split(r"(?=M[ ,])", outline_d) if s.strip()]
    if len(subpaths) < 2:
        return outline_d, ""

    def bbox_area(subpath: str) -> float:
        nums = [float(v) for v in re.findall(r"-?\d+\.?\d*", subpath)]
        xs, ys = nums[0::2], nums[1::2]
        return (max(xs) - min(xs)) * (max(ys) - min(ys))

    silhouette = max(subpaths, key=bbox_area)
    details = [s for s in subpaths if s is not silhouette]
    return silhouette, " ".join(details)


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    """Parse a #rrggbb string into an RGB tuple."""
    return int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16)


def _lerp_hex(a: str, b: str, t: float) -> str:
    """Interpolate two #rrggbb colours channel by channel."""
    ra, ga, ba = _hex_to_rgb(a)
    rb, gb, bb = _hex_to_rgb(b)
    return _rgb_to_hex((
        round(ra + (rb - ra) * t),
        round(ga + (gb - ga) * t),
        round(ba + (bb - ba) * t),
    ))


def _mix_hex(a: str, b: str) -> str:
    """Average two #rrggbb colours channel by channel."""
    return _lerp_hex(a, b, 0.5)


def _eased_ramp(
    start: float, end: float, color_from: str, color_to: str
) -> list[tuple[float, str]]:
    """Gradient stops of a ramp with smoothstep easing.

    A linear ramp meeting a plateau creates a visible Mach band, an illusory
    line where the colour slope breaks. Easing the ramp in and out removes
    the break, so the transition reads as continuous shading.
    """
    stops = []
    for fraction in (0.0, 1.0 / 3.0, 2.0 / 3.0, 1.0):
        eased = fraction * fraction * (3.0 - 2.0 * fraction)
        offset = start + (end - start) * fraction
        stops.append((offset, _lerp_hex(color_from, color_to, eased)))
    return stops


def _vertical_neighbors(
    present: set[str],
) -> dict[str, tuple[object, object]]:
    """Map each region to its (above, below) neighbours along the body axis.

    Neighbours drive the colour blending between adjacent regions. A tuple
    value blends the edge with the average of several regions (the genital
    region meets both thighs). Regions absent from `present` are dropped.

    Every region is bilateral, so the chains are built per side: the left half
    of the chest blends with the left half of the abdomen, never with the right
    one. The midline seam is handled by the thermal blur, not here.
    """
    posterior = any(key.startswith("upper_back") for key in present)
    if posterior:
        trunk = ["upper_back", "lower_back"]
        crown, trunk_bottom = "skull", "buttocks"
    else:
        trunk = ["upper_chest", "lower_chest", "upper_abdomen", "lower_abdomen"]
        crown, trunk_bottom = "face", "hip"

    # Cadeia da coroa ao dedo do pé; o braço pendura no ombro, que por sua vez
    # nasce no topo do tronco
    spine = [crown, "neck", *trunk, trunk_bottom]
    spine += ["thigh", "knee", "lower_leg", "ankle", "foot", "toe"]
    limb = ["shoulder", "upper_arm", "elbow", "forearm", "wrist", "hand", "finger"]

    neighbors: dict[str, tuple[object, object]] = {}
    for side in ("left", "right"):
        chain = [f"{region}-{side}" for region in spine]
        for index, key in enumerate(chain):
            above = chain[index - 1] if index else None
            below = chain[index + 1] if index + 1 < len(chain) else None
            neighbors[key] = (above, below)

        arm = [f"{region}-{side}" for region in limb]
        neighbors[arm[0]] = (f"{trunk[0]}-{side}", arm[1])
        for index in range(1, len(arm)):
            below = arm[index + 1] if index + 1 < len(arm) else None
            neighbors[arm[index]] = (arm[index - 1], below)

    if not posterior:
        neighbors["genital"] = (
            ("hip-left", "hip-right"),
            ("thigh-left", "thigh-right"),
        )
    return {k: v for k, v in neighbors.items() if k in present}


def _edge_color(
    fills: dict[str, str],
    ref: object,
    self_hex: str,
    reciprocal: bool = True,
) -> str:
    """Colour of a region edge facing its neighbour.

    When the neighbour also fades towards this region the two meet halfway;
    when it does not (the trunk never fades towards the arms), the edge takes
    the neighbour's full colour so the seam disappears on this side alone.
    """
    if ref is None:
        return self_hex
    if isinstance(ref, tuple):
        found = [fills[r] for r in ref if r in fills]
        if not found:
            return self_hex
        base = found[0] if len(found) == 1 else _mix_hex(found[0], found[1])
    elif ref in fills:
        base = fills[ref]
    else:
        return self_hex
    return _mix_hex(self_hex, base) if reciprocal else base


def _path_points(d: str) -> list[tuple[float, float]]:
    """Coordinate pairs of a path's data attribute."""
    nums = [float(v) for v in re.findall(r"-?\d+\.?\d*", d)]
    return list(zip(nums[0::2], nums[1::2]))


def _points_bbox(points: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    """Bounding box (x0, y0, x1, y1) of a list of points."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _center_of(ref: object, boxes: dict) -> tuple[float, float] | None:
    """Centre of a neighbour reference; averages a tuple of regions."""
    if isinstance(ref, tuple):
        found = [boxes[r] for r in ref if r in boxes]
        if not found:
            return None
        centers = [((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0) for b in found]
        return (
            sum(c[0] for c in centers) / len(centers),
            sum(c[1] for c in centers) / len(centers),
        )
    if ref in boxes:
        b = boxes[ref]
        return (b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0
    return None


def _gradient_line(
    points: list[tuple[float, float]],
    above_center: tuple[float, float] | None,
    below_center: tuple[float, float] | None,
) -> tuple[float, float, float, float]:
    """Endpoints of the blending axis across a region, in user space.

    The axis follows the limb: it points from the neighbour above towards the
    neighbour below, so angled arms blend along their own direction instead
    of the vertical. It spans the projection of the region's own points; the
    bounding box would overshoot on diagonal limbs and push the ramps outside
    the shape.
    """
    box = _points_bbox(points)
    cx, cy = (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0
    if above_center and below_center:
        vx, vy = below_center[0] - above_center[0], below_center[1] - above_center[1]
    elif below_center:
        vx, vy = below_center[0] - cx, below_center[1] - cy
    elif above_center:
        vx, vy = cx - above_center[0], cy - above_center[1]
    else:
        vx, vy = 0.0, 1.0
    length = (vx * vx + vy * vy) ** 0.5
    # Eixo degenerado cai no vertical
    if length < 1e-6:
        vx, vy, length = 0.0, 1.0, 1.0
    ux, uy = vx / length, vy / length
    spans = [(px - cx) * ux + (py - cy) * uy for px, py in points]
    t0, t1 = min(spans), max(spans)
    return cx + t0 * ux, cy + t0 * uy, cx + t1 * ux, cy + t1 * uy


def _points_back(ref: object, region_id: str, neighbors: dict, position: int) -> bool:
    """Whether the neighbour's opposite edge fades towards this region."""
    if not isinstance(ref, str):
        # Par de coxas: ambas apontam de volta para a pelve
        return True
    counterpart = neighbors.get(ref, (None, None))[position]
    if isinstance(counterpart, tuple):
        return region_id in counterpart
    return counterpart == region_id


def _axis_color(info: dict, point: tuple[float, float]) -> str:
    """Displayed colour of a region at a point, replaying its gradient."""
    x1, y1, x2, y2 = info["line"]
    dx, dy = x2 - x1, y2 - y1
    denom = dx * dx + dy * dy
    if denom < 1e-9:
        return info["self"]
    t = ((point[0] - x1) * dx + (point[1] - y1) * dy) / denom
    if t <= 0.0:
        return info["top"]
    if t < 0.3:
        f = t / 0.3
        return _lerp_hex(info["top"], info["self"], f * f * (3.0 - 2.0 * f))
    if t <= 0.7:
        return info["self"]
    if t >= 1.0:
        return info["bottom"]
    f = (t - 0.7) / 0.3
    return _lerp_hex(info["self"], info["bottom"], f * f * (3.0 - 2.0 * f))


def _region_fill_map(
    defs: ET.Element,
    fills: dict[str, str],
    points: dict[str, list[tuple[float, float]]],
    draw: set[str] | None = None,
) -> tuple[dict[str, str], dict[str, str]]:
    """Create blending gradients; return each region's fill and its veils.

    A region whose edges match its own colour keeps the plain fill; the
    others get a linearGradient along the limb axis fading into the
    neighbouring colours, so adjacent regions transition smoothly instead of
    hard-cutting. Junction regions such as the deltoid also get a "veil": a
    vertical overlay in the trunk colour fading to transparent, painted over
    the fill, because their two borders are nearly perpendicular and a single
    gradient direction cannot align with both.
    """
    neighbors = _vertical_neighbors(set(fills))
    result: dict[str, str] = {}
    veils: dict[str, str] = {}
    boxes = {rid: _points_bbox(pts) for rid, pts in points.items()}

    # Primeira passada: cores de borda e eixo de cada região, porque o véu de
    # uma junção precisa amostrar a cor EXIBIDA pelo vizinho, não a cor base
    info: dict[str, dict] = {}
    for region_id, self_hex in fills.items():
        above, below = neighbors.get(region_id, (None, None))
        above_reciprocal = _points_back(above, region_id, neighbors, 1)
        top = _edge_color(fills, above, self_hex, reciprocal=above_reciprocal)
        bottom = _edge_color(
            fills, below, self_hex,
            reciprocal=_points_back(below, region_id, neighbors, 0),
        )
        line = _gradient_line(
            points[region_id],
            _center_of(above, boxes) if above_reciprocal else None,
            _center_of(below, boxes),
        )
        info[region_id] = {
            "self": self_hex, "top": top, "bottom": bottom, "line": line,
            "above": above, "above_reciprocal": above_reciprocal,
        }

    for region_id in sorted(fills):
        if draw is not None and region_id not in draw:
            continue
        data = info[region_id]
        self_hex, top, bottom = data["self"], data["top"], data["bottom"]
        if top == self_hex and bottom == self_hex:
            result[region_id] = self_hex
            continue
        box = boxes[region_id]
        x1, y1, x2, y2 = data["line"]
        gradient = ET.SubElement(defs, "linearGradient")
        gradient.set("id", f"grad-{region_id}")
        gradient.set("gradientUnits", "userSpaceOnUse")
        for name, value in (("x1", x1), ("y1", y1), ("x2", x2), ("y2", y2)):
            gradient.set(name, str(round(value, 2)))
        stops = (
            _eased_ramp(0.0, 0.3, top, self_hex)
            + _eased_ramp(0.7, 1.0, self_hex, bottom)
        )
        for offset, color in stops:
            stop = ET.SubElement(gradient, "stop")
            stop.set("offset", str(round(offset, 4)))
            stop.set("stop-color", color)
        result[region_id] = f"url(#grad-{region_id})"

        if not data["above_reciprocal"] and top != self_hex:
            # O véu acompanha a cor que o tronco exibe em cada altura: com
            # peito e abdômen distintos, o peito já chega mesclado na altura
            # do ombro, e um véu de cor única abriria um corte seco
            above = data["above"]
            above_info = info.get(above) if isinstance(above, str) else None
            center_x = (box[0] + box[2]) / 2.0
            veil = ET.SubElement(defs, "linearGradient")
            veil.set("id", f"veil-{region_id}")
            veil.set("gradientUnits", "userSpaceOnUse")
            veil.set("x1", str(round(box[0], 2)))
            veil.set("y1", str(round(box[1], 2)))
            veil.set("x2", str(round(box[0], 2)))
            veil.set("y2", str(round(box[1] + (box[3] - box[1]) * 0.55, 2)))
            for fraction in (0.0, 1.0 / 3.0, 2.0 / 3.0, 1.0):
                eased = fraction * fraction * (3.0 - 2.0 * fraction)
                sample_y = box[1] + (box[3] - box[1]) * 0.55 * fraction
                color = (
                    _axis_color(above_info, (center_x, sample_y))
                    if above_info is not None else top
                )
                stop = ET.SubElement(veil, "stop")
                stop.set("offset", str(round(fraction, 4)))
                stop.set("stop-color", color)
                stop.set("stop-opacity", str(round(1.0 - eased, 4)))
            veils[region_id] = f"url(#veil-{region_id})"
    return result, veils


def _compute_ticks(value_min: float, value_max: float, n: int = 5) -> list[float]:
    """Compute ~n evenly spaced values between value_min and value_max for the legend ticks."""
    if value_min == value_max:
        return [value_min]
    step = (value_max - value_min) / (n - 1)
    return [value_min + i * step for i in range(n)]


def _append_legend(
    root: ET.Element,
    heatmap: Heatmap,
    colormap: ColorMap,
    vx: float,
    vy: float,
    vw: float,
    vh: float,
    lang: str = "pt",
    background: str = "transparent",
) -> None:
    """Insert a VERTICAL gradient bar on the right-hand side of the figure.

    The root element's viewBox is widened sideways so the legend fits without
    overlapping the body. Design: vertical gradient bar (top=maximum,
    bottom=minimum), label above and numeric ticks to the right. Text colours
    adapt to the background brightness.
    """
    # Faixa reservada à direita para a legenda (viewBox expandido)
    legend_w = _legend_width(vw, True)
    new_total_w = vw + legend_w
    root.set("viewBox", f"{vx} {vy} {new_total_w} {vh}")
    ui_main, ui_sub, ui_border, ui_tick = _legend_ui_colors(background)

    # Barra vertical em pílula, alta e centralizada
    bar_h = vh * 0.52
    bar_w = legend_w * 0.15
    bar_x = vx + vw + legend_w * 0.28
    bar_y = vy + (vh - bar_h) / 2.0

    label_size = vh * 0.026
    tick_font_size = vh * 0.019
    tick_len = bar_w * 0.45

    grad_id = "legend-gradient"

    # Localiza ou cria o bloco <defs> existente
    defs: ET.Element | None = None
    for child in root:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == "defs":
            defs = child
            break
    if defs is None:
        defs = ET.SubElement(root, "defs")

    # Gradiente VERTICAL: topo = cor quente (max), base = cor fria (min)
    grad = ET.SubElement(defs, "linearGradient")
    grad.set("id", grad_id)
    grad.set("x1", "0%")
    grad.set("y1", "0%")
    grad.set("x2", "0%")
    grad.set("y2", "100%")
    n_stops = 24
    for i in range(n_stops + 1):
        # t=0 -> topo (quente/max), t=1 -> base (frio/min)
        t_color = 1.0 - i / n_stops
        color = _rgb_to_hex(colormap.color_at(t_color))
        stop = ET.SubElement(grad, "stop")
        stop.set("offset", f"{round(i * 100 / n_stops, 1)}%")
        stop.set("stop-color", color)

    # Barra em pílula (cantos totalmente arredondados)
    bar_rx = round(bar_w / 2.0, 2)
    bar = ET.SubElement(root, "rect")
    bar.set("id", "legend-bar")
    bar.set("x", str(round(bar_x, 2)))
    bar.set("y", str(round(bar_y, 2)))
    bar.set("width", str(round(bar_w, 2)))
    bar.set("height", str(round(bar_h, 2)))
    bar.set("fill", f"url(#{grad_id})")
    bar.set("rx", str(bar_rx))

    # Borda fina e discreta acompanhando a pílula
    bar_border = ET.SubElement(root, "rect")
    bar_border.set("id", "legend-bar-border")
    bar_border.set("x", str(round(bar_x, 2)))
    bar_border.set("y", str(round(bar_y, 2)))
    bar_border.set("width", str(round(bar_w, 2)))
    bar_border.set("height", str(round(bar_h, 2)))
    bar_border.set("fill", "none")
    bar_border.set("stroke", ui_border)
    bar_border.set("stroke-width", str(round(vw * 0.0011, 2)))
    bar_border.set("rx", str(bar_rx))

    # Rótulo acima da barra, em negrito e alinhado à esquerda dela
    axis_label = "Valor" if lang == "pt" else "Value"
    label_elem = ET.SubElement(root, "text")
    label_elem.set("id", "legend-label")
    label_elem.set("x", str(round(bar_x, 2)))
    label_elem.set("y", str(round(bar_y - label_size * 0.9, 2)))
    label_elem.set("text-anchor", "start")
    label_elem.set("font-size", str(round(label_size, 2)))
    label_elem.set("font-family", "Helvetica, Arial, sans-serif")
    label_elem.set("font-weight", "600")
    label_elem.set("letter-spacing", str(round(label_size * 0.08, 2)))
    label_elem.set("fill", ui_main)
    label_elem.text = axis_label

    # Ticks: linha curta + valor, à direita da barra
    ticks = _compute_ticks(heatmap.value_min, heatmap.value_max)
    span = heatmap.value_max - heatmap.value_min
    tick_x_start = bar_x + bar_w + bar_w * 0.4
    tick_x_end = tick_x_start + tick_len
    text_x = tick_x_end + legend_w * 0.06

    tick_labels = _format_ticks(ticks)
    for tick_val, tick_label in zip(ticks, tick_labels):
        # Proporção vertical: max no topo (y=bar_y), min na base (y=bar_y+bar_h)
        t = (tick_val - heatmap.value_min) / span if span else 0.0
        tick_y = bar_y + bar_h * (1.0 - t)

        tick_line = ET.SubElement(root, "line")
        tick_line.set("x1", str(round(tick_x_start, 2)))
        tick_line.set("y1", str(round(tick_y, 2)))
        tick_line.set("x2", str(round(tick_x_end, 2)))
        tick_line.set("y2", str(round(tick_y, 2)))
        tick_line.set("stroke", ui_tick)
        tick_line.set("stroke-width", str(round(vw * 0.0011, 2)))

        tick_text = ET.SubElement(root, "text")
        tick_text.set("x", str(round(text_x, 2)))
        tick_text.set("y", str(round(tick_y + tick_font_size * 0.34, 2)))
        tick_text.set("text-anchor", "start")
        tick_text.set("font-size", str(round(tick_font_size, 2)))
        tick_text.set("font-family", "Helvetica, Arial, sans-serif")
        tick_text.set("fill", ui_sub)
        tick_text.text = tick_label


def _build_smooth_svg(
    base_svg: str,
    heatmap: Heatmap,
    colormap: ColorMap,
    legend: bool,
    lang: str = "pt",
    background: str = "transparent",
    missing: str = "neutral",
) -> str:
    """Build the "preserved model" SVG: a thermal gradient with cold edges and
    the body outline always crisp on top.

    Layer strategy (bottom to top):
    1. Background (optional): rectangle covering the whole viewBox (body +
       legend).
    2. Group with mask="url(#body-mask)" (solid mask = union of every region
       path): nothing inside ever bleeds outside the silhouette.
       a. Group with filter="url(#thermal-blur)": cold base (the colormap's
          t=0 colour) plus one copy per region carrying the data colour, with
          a light blur for continuity between neighbouring regions.
       b. Cold inner-glow layer (feFlood + feComposite operator="out" +
          feGaussianBlur + feComposite operator="in"): a blue/cold glow that
          clings only to the inner edges of each part, never the core.
    3. CRISP layer, outside both the mask and the blur: thin semi-transparent
       detail lines plus a strong outer contour (fill-rule="evenodd"), so the
       model never distorts along with the gradient.
    4. Legend (optional).

    Regions with no value get no path of their own: the base underneath (the
    `missing` colour, neutral grey by default or cold when missing="cold")
    already covers the area, leaving no holes in the gradient.

    Deterministic output (stable id ordering and fixed attributes).
    """
    _validate_background(background)
    _validate_missing(missing)
    ET.register_namespace("", _SVG_NS)
    base_root = ET.fromstring(base_svg)

    vx, vy, vw, vh = _parse_viewbox(base_svg)
    legend_w = _legend_width(vw, legend)
    total_w = vw + legend_w

    root = ET.Element("svg")
    root.set("xmlns", _SVG_NS)
    root.set("viewBox", f"{vx} {vy} {total_w} {vh}")

    if heatmap.title:
        title_elem = ET.SubElement(root, "title")
        title_elem.text = heatmap.title

    defs = ET.SubElement(root, "defs")

    # Coleta paths de região do SVG base, preservando a geometria real
    base_paths: dict[str, str] = {}
    for elem in base_root.iter():
        if _tag(elem) == "g" and elem.get("id") == "regions":
            for child in elem:
                if _tag(child) == "path":
                    pid = child.get("id", "")
                    if pid:
                        base_paths[pid] = child.get("d", "")

    outline_d = _extract_body_outline_d(base_svg)
    cold_hex = _rgb_to_hex(colormap.color_at(0.0))
    missing_hex = _missing_fill(missing, colormap)

    # Stroke que fecha os vãos entre os sub-paths na silhueta unida (~2% do vw)
    seam_w = str(round(vw * 0.020, 2))
    blur_std = round(vw * 0.010, 2)
    glow_std = round(vw * 0.040, 2)

    # Filtro 1: desfoque leve para continuidade do degradê entre regiões
    blur_filter = ET.SubElement(defs, "filter")
    blur_filter.set("id", "thermal-blur")
    blur_filter.set("x", "-15%")
    blur_filter.set("y", "-15%")
    blur_filter.set("width", "130%")
    blur_filter.set("height", "130%")
    blur_filter.set("color-interpolation-filters", "sRGB")
    blur_fe = ET.SubElement(blur_filter, "feGaussianBlur")
    blur_fe.set("stdDeviation", str(blur_std))

    # Filtro 2: inner-glow frio -- brilho da cor fria que gruda só por dentro
    # das bordas (operator="out" isola a franja externa da forma) e desaparece
    # em direção ao núcleo (operator="in" recorta de volta na forma original).
    glow_filter = ET.SubElement(defs, "filter")
    glow_filter.set("id", "inner-glow-cold")
    glow_filter.set("x", "-20%")
    glow_filter.set("y", "-20%")
    glow_filter.set("width", "140%")
    glow_filter.set("height", "140%")
    glow_filter.set("color-interpolation-filters", "sRGB")
    flood = ET.SubElement(glow_filter, "feFlood")
    flood.set("flood-color", cold_hex)
    flood.set("result", "cold-flood")
    composite_out = ET.SubElement(glow_filter, "feComposite")
    composite_out.set("in", "cold-flood")
    composite_out.set("in2", "SourceAlpha")
    composite_out.set("operator", "out")
    composite_out.set("result", "outside")
    glow_blur = ET.SubElement(glow_filter, "feGaussianBlur")
    glow_blur.set("in", "outside")
    glow_blur.set("stdDeviation", str(glow_std))
    glow_blur.set("result", "blurred")
    composite_in = ET.SubElement(glow_filter, "feComposite")
    composite_in.set("in", "blurred")
    composite_in.set("in2", "SourceAlpha")
    composite_in.set("operator", "in")

    # Máscara sólida do corpo: união de todos os paths de região (ordem estável)
    # com stroke que fecha os vãos entre sub-paths -- silhueta única, sem buracos.
    body_union_d = " ".join(base_paths[pid] for pid in sorted(base_paths))
    mask = ET.SubElement(defs, "mask")
    mask.set("id", "body-mask")
    mask_path = ET.SubElement(mask, "path")
    mask_path.set("d", body_union_d)
    mask_path.set("fill", "white")
    mask_path.set("stroke", "white")
    mask_path.set("stroke-width", seam_w)
    mask_path.set("stroke-linejoin", "round")

    # Recorte pela silhueta externa: a máscara é a união das regiões e pode
    # transbordar o contorno; o clip garante cor só dentro do corpo
    if outline_d:
        clip = ET.SubElement(defs, "clipPath")
        clip.set("id", "body-clip")
        clip_path = ET.SubElement(clip, "path")
        clip_path.set("d", _split_outline_d(outline_d)[0])

    _append_background_rect(root, vx, vy, total_w, vh, background)

    # Grupo recortado na máscara sólida: nada aqui dentro vaza da silhueta.
    masked_group = ET.SubElement(root, "g")
    masked_group.set("mask", "url(#body-mask)")
    if outline_d:
        masked_group.set("clip-path", "url(#body-clip)")

    # Camada 1: base (cor de missing) + regiões coloridas por dado, com blur leve.
    blurred_group = ET.SubElement(masked_group, "g")
    blurred_group.set("filter", "url(#thermal-blur)")

    body_base = ET.SubElement(blurred_group, "path")
    body_base.set("d", body_union_d)
    body_base.set("fill", missing_hex)
    body_base.set("stroke", missing_hex)
    body_base.set("stroke-width", seam_w)
    body_base.set("stroke-linejoin", "round")

    # Regiões sem dado entram no mapa de cores só como vizinhas: a borda das
    # regiões coloridas se funde com a cor de missing em vez de cortar seco
    region_fills: dict[str, str] = {}
    drawn: set[str] = set()
    for elem_id in sorted(base_paths):
        canonical_id, side = _canonical_and_side(elem_id)
        rgb = _color_for(canonical_id, side, heatmap.colors)
        if rgb is None:
            region_fills[elem_id] = missing_hex
        else:
            region_fills[elem_id] = _rgb_to_hex(rgb)
            drawn.add(elem_id)

    region_points = {rid: _path_points(d) for rid, d in base_paths.items()}
    fill_by_region, veils = _region_fill_map(
        defs, region_fills, region_points, draw=drawn
    )
    for elem_id in sorted(drawn):
        fill = fill_by_region[elem_id]
        path_elem = ET.SubElement(blurred_group, "path")
        path_elem.set("id", elem_id)
        path_elem.set("d", base_paths[elem_id])
        path_elem.set("fill", fill)
        path_elem.set("stroke", fill)
        path_elem.set("stroke-width", seam_w)
        path_elem.set("stroke-linejoin", "round")
        # Véu da junção do ombro por cima do preenchimento da região
        if elem_id in veils:
            overlay = ET.SubElement(blurred_group, "path")
            overlay.set("d", base_paths[elem_id])
            overlay.set("fill", veils[elem_id])
            overlay.set("stroke", veils[elem_id])
            overlay.set("stroke-width", seam_w)
            overlay.set("stroke-linejoin", "round")

    # Camada 2: inner-glow frio por cima -- bordas frias em cada região.
    # Leva a mesma costura da máscara: sem ela, uma fresta entre dois paths do
    # desenho vira buraco só nesta camada e deixa passar uma linha clara, sem o
    # escurecimento das bordas.
    glow_elem = ET.SubElement(masked_group, "path")
    glow_elem.set("d", body_union_d)
    glow_elem.set("fill", "white")
    glow_elem.set("stroke", "white")
    glow_elem.set("stroke-width", seam_w)
    glow_elem.set("stroke-linejoin", "round")
    glow_elem.set("filter", "url(#inner-glow-cold)")

    # Camada 3 (NÍTIDA, fora da máscara/blur): linhas de detalhe + contorno
    # forte do modelo, para o corpo nunca distorcer com o degradê.
    if outline_d:
        detail = ET.SubElement(root, "path")
        detail.set("id", "body-outline-detail")
        detail.set("d", outline_d)
        detail.set("fill", "none")
        detail.set("stroke", "rgba(0,0,0,0.9)")
        detail.set("stroke-width", str(round(vw * 0.004, 2)))
        detail.set("stroke-linejoin", "round")

        outline = ET.SubElement(root, "path")
        outline.set("id", "body-outline")
        outline.set("d", outline_d)
        outline.set("fill", "none")
        outline.set("stroke", "#000000")
        outline.set("stroke-width", str(round(vw * 0.010, 2)))
        outline.set("stroke-linejoin", "round")
        outline.set("fill-rule", "evenodd")

    if legend:
        _append_legend(root, heatmap, colormap, vx, vy, vw, vh, lang=lang, background=background)

    _append_title(root, heatmap.title, background)

    return ET.tostring(root, encoding="unicode")


def _namespace_ids(svg: str, prefix: str) -> str:
    """Prefix every id and internal reference so two panels can share one SVG.

    Masks, filters and gradients are referenced by id, and ids are global to the
    document. Without the prefix the second panel would silently reuse the first
    panel's body mask.
    """
    svg = re.sub(r'id="([^"]+)"', lambda m: f'id="{prefix}{m.group(1)}"', svg)
    svg = re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{prefix}{m.group(1)})", svg)
    svg = re.sub(r'href="#([^"]+)"', lambda m: f'href="#{prefix}{m.group(1)}"', svg)
    return svg


def compose_views(
    panels: list[tuple[str, str]],
    heatmap: Heatmap,
    colormap: ColorMap | None,
    legend: bool = True,
    lang: str = "pt",
    background: str = "transparent",
) -> str:
    """Place already rendered panels side by side in a single SVG.

    Parameters
    ----------
    panels:
        Pairs of (prefix, svg) in drawing order, left to right. The prefix
        namespaces the panel ids (``anterior-hand-left``).
    heatmap:
        Heatmap used for the shared legend; every panel shares the same scale.
    colormap:
        ColorMap for the legend gradient.
    legend:
        If True, draws a single legend to the right of the last panel.
    lang:
        Label language.
    background:
        Figure background, applied once over the whole composition.

    Returns
    -------
    str
        The composed SVG.
    """
    _validate_background(background)
    ET.register_namespace("", _SVG_NS)

    namespaced = [_namespace_ids(svg, prefix) for prefix, svg in panels]
    roots = [ET.fromstring(svg) for svg in namespaced]
    vx, vy, vw, vh = _parse_viewbox(namespaced[0])

    gap = vw * 0.04
    total_w = vw * len(roots) + gap * (len(roots) - 1)

    root = ET.Element(f"{{{_SVG_NS}}}svg")
    root.set("viewBox", f"{vx} {vy} {round(total_w, 2)} {vh}")

    if heatmap.title:
        title_elem = ET.SubElement(root, "title")
        title_elem.text = heatmap.title

    # O fundo tem que cobrir também a faixa da legenda, que só é acrescentada
    # depois e alarga o viewBox; senão sobra uma tira sem fundo à direita
    draws_legend = legend and colormap is not None
    legend_w = _legend_width(total_w, True) if draws_legend else 0.0
    _append_background_rect(root, vx, vy, total_w + legend_w, vh, background)

    for index, panel_root in enumerate(roots):
        group = ET.SubElement(root, "g")
        offset = index * (vw + gap)
        group.set("id", f"{panels[index][0]}view")
        group.set("transform", f"translate({round(offset, 2)}, 0)")
        for child in list(panel_root):
            group.append(child)

    if draws_legend:
        _append_legend(
            root, heatmap, colormap, vx, vy, total_w, vh,
            lang=lang, background=background,
        )

    _append_title(root, heatmap.title, background)

    return ET.tostring(root, encoding="unicode")


def _format_value(v: float) -> str:
    """Format a numeric value for display in the legend."""
    if v == int(v):
        return str(int(v))
    return f"{v:.2f}"


def _format_ticks(values: list[float]) -> list[str]:
    """Format every legend tick, using the fewest decimals that keeps them apart.

    Rounding to integers gives clean ggplot-style labels, but on a narrow range
    (2 to 5, say) it collapses two ticks into the same text. Decimals are added
    only when that happens.

    Parameters
    ----------
    values:
        Tick values, in the order they are drawn.

    Returns
    -------
    list[str]
        One label per value, all distinct whenever the values are.
    """
    unique = len({round(v, 6) for v in values})
    for decimals in (0, 1, 2):
        labels = [
            str(int(round(v))) if decimals == 0 else f"{v:.{decimals}f}"
            for v in values
        ]
        if len(set(labels)) == unique:
            return labels
    return [f"{v:.3f}" for v in values]


class SvgRenderer:
    """Apply a Heatmap onto a clone of the base SVG.

    Regions with no value in the heatmap are filled according to `missing`
    ("neutral", a discreet grey, by default; or "cold", the colormap's cold
    colour). Output is deterministic: stable ordering of attributes and
    regions.
    """

    def render(
        self,
        heatmap: Heatmap,
        model: AnatomicalModel,
        lang: str = "pt",
        base_svg: str | None = None,
        smooth: bool = False,
        legend: bool = False,
        colormap: ColorMap | None = None,
        background: str = "transparent",
        missing: str = "neutral",
    ) -> Figure:
        """Apply the heatmap colours onto the anatomical SVG.

        Parameters
        ----------
        heatmap:
            Heatmap mapping region_id -> RGB colours.
        model:
            AnatomicalModel with the region geometry and metadata.
        lang:
            Label language ("pt" or "en").
        base_svg:
            SVG content as a string. When None, rebuilds from the model
            geometry.
        smooth:
            If True, applies a continuous thermal gradient with feGaussianBlur.
        legend:
            If True, inserts a colour bar with intensity labels.
        colormap:
            ColorMap used to generate the legend and smooth-mode stops.
        background:
            Figure background: "dark", "light" or "transparent" (default).
        missing:
            Fill for regions with no data: "neutral" (default, a discreet grey
            that reads as "no data") or "cold" (the colormap's cold colour,
            the older behaviour).

        Returns
        -------
        Figure
            Rendered figure wrapping the final SVG string.

        Raises
        ------
        ValueError
            If background is not "dark", "light" or "transparent", or if
            missing is not "neutral" or "cold".
        """
        _validate_background(background)
        _validate_missing(missing)

        if smooth and base_svg is not None and colormap is not None:
            svg_str = _build_smooth_svg(
                base_svg, heatmap, colormap, legend,
                lang=lang, background=background, missing=missing,
            )
        elif base_svg is not None:
            svg_str = self._render_onto_svg(
                base_svg, heatmap, model, legend, colormap,
                lang=lang, background=background, missing=missing,
            )
        else:
            svg_str = self._render_from_model(
                heatmap, model, lang, legend, colormap,
                background=background, missing=missing,
            )

        return Figure(svg_str)

    def _render_onto_svg(
        self,
        base_svg: str,
        heatmap: Heatmap,
        model: AnatomicalModel,
        legend: bool = False,
        colormap: ColorMap | None = None,
        lang: str = "pt",
        background: str = "transparent",
        missing: str = "neutral",
    ) -> str:
        """Clone the SVG tree and apply the heatmap fill colours."""
        _validate_background(background)
        _validate_missing(missing)
        ET.register_namespace("", _SVG_NS)
        root = ET.fromstring(base_svg)

        # Injeta título no SVG clonado quando presente
        if heatmap.title:
            existing_titles = [e for e in root if _tag(e) == "title"]
            if not existing_titles:
                title_elem = ET.Element("title")
                title_elem.text = heatmap.title
                root.insert(0, title_elem)

        vx, vy, vw, vh = _parse_viewbox(base_svg)
        legend_effective = legend and colormap is not None
        total_w = vw + _legend_width(vw, legend_effective)
        _append_background_rect(root, vx, vy, total_w, vh, background)

        def find_regions_group(root: ET.Element) -> ET.Element | None:
            for elem in root.iter():
                if _tag(elem) == "g" and elem.get("id") == "regions":
                    return elem
            return None

        # O contorno vem do SVG base sem fill nem stroke, então herdaria
        # preenchimento preto e taparia o mapa. Aqui ele vira traço, igual ao
        # modo suave: grosso só na silhueta externa e fino nos subpaths de
        # detalhe, senão os detalhes miúdos empastelam num borrão preto
        body_silhouette_d = None
        for parent in root.iter():
            for position, elem in enumerate(list(parent)):
                if elem.get("id") != "body-outline":
                    continue
                silhouette_d, details_d = _split_outline_d(elem.get("d", ""))
                body_silhouette_d = silhouette_d
                elem.set("d", silhouette_d)
                elem.set("fill", "none")
                elem.set("stroke", "#000000")
                elem.set("stroke-width", str(round(vw * 0.010, 2)))
                elem.set("stroke-linejoin", "round")
                if details_d:
                    detail = ET.Element("path")
                    detail.set("id", "body-outline-detail")
                    detail.set("d", details_d)
                    detail.set("fill", "none")
                    detail.set("stroke", "rgba(0,0,0,0.9)")
                    detail.set("stroke-width", str(round(vw * 0.004, 2)))
                    detail.set("stroke-linejoin", "round")
                    parent.insert(position, detail)

        regions_group = find_regions_group(root)
        if regions_group is None:
            _append_title(root, heatmap.title, background)
            return ET.tostring(root, encoding="unicode")

        defs = ET.Element("defs")

        # Recorta as regiões na silhueta: cor nenhuma passa do contorno
        if body_silhouette_d is not None:
            clip = ET.SubElement(defs, "clipPath")
            clip.set("id", "body-clip")
            clip_path = ET.SubElement(clip, "path")
            clip_path.set("d", body_silhouette_d)
            regions_group.set("clip-path", "url(#body-clip)")

        # Cor por lado: chave lateralizada (ex.: 'hand_left') senão a canônica
        fills: dict[str, str] = {}
        region_points: dict[str, list[tuple[float, float]]] = {}
        for elem in regions_group:
            if _tag(elem) != "path" or not elem.get("id"):
                continue
            canonical_id, side = _canonical_and_side(elem.get("id"))
            rgb = _color_for(canonical_id, side, heatmap.colors)
            fills[elem.get("id")] = (
                _rgb_to_hex(rgb) if rgb is not None
                else _missing_fill(missing, colormap)
            )
            region_points[elem.get("id")] = _path_points(elem.get("d", "0 0"))

        fill_by_region, veils = _region_fill_map(defs, fills, region_points)
        overlays: list[tuple[int, ET.Element]] = []
        for position, elem in enumerate(list(regions_group)):
            elem_id = elem.get("id", "")
            if elem_id not in fill_by_region:
                continue
            elem.set("fill", fill_by_region[elem_id])
            # Traço da própria cor dilata a região para fechar as frestas do
            # desenho de origem, do mesmo tamanho da costura do modo suave. Sem
            # ele o rasterizador mostra cada fresta como faixa branca
            elem.set("stroke", fill_by_region[elem_id])
            elem.set("stroke-width", str(round(vw * 0.020, 2)))
            elem.set("stroke-linejoin", "round")
            # Remove atributo style para evitar conflito com o atributo fill
            if "style" in elem.attrib:
                del elem.attrib["style"]
            if elem_id in veils:
                overlay = ET.Element("path")
                overlay.set("d", elem.get("d", ""))
                overlay.set("fill", veils[elem_id])
                # O traço do véu cobre o anel de traço da região por baixo
                overlay.set("stroke", veils[elem_id])
                overlay.set("stroke-width", str(round(vw * 0.020, 2)))
                overlay.set("stroke-linejoin", "round")
                overlays.append((position + 1, overlay))
        for position, overlay in reversed(overlays):
            regions_group.insert(position, overlay)

        if len(defs):
            root.insert(0, defs)

        if legend and colormap is not None:
            _append_legend(root, heatmap, colormap, vx, vy, vw, vh, lang=lang, background=background)

        _append_title(root, heatmap.title, background)

        return ET.tostring(root, encoding="unicode")

    def _render_from_model(
        self,
        heatmap: Heatmap,
        model: AnatomicalModel,
        lang: str,
        legend: bool = False,
        colormap: ColorMap | None = None,
        background: str = "transparent",
        missing: str = "neutral",
    ) -> str:
        """Build the SVG from scratch out of the model geometry when there is no base SVG."""
        _validate_background(background)
        _validate_missing(missing)
        ET.register_namespace("", _SVG_NS)
        vx, vy, vw, vh = 0.0, 0.0, 400.0, 900.0
        legend_effective = legend and colormap is not None
        total_w = vw + _legend_width(vw, legend_effective)

        root = ET.Element("svg")
        root.set("xmlns", _SVG_NS)
        root.set("viewBox", f"{vx} {vy} {total_w} {vh}")

        if heatmap.title:
            title_elem = ET.SubElement(root, "title")
            title_elem.text = heatmap.title

        _append_background_rect(root, vx, vy, total_w, vh, background)

        regions_group = ET.SubElement(root, "g")
        regions_group.set("id", "regions")

        # Ordem estável: ids do modelo
        for region in model.regions():
            if not region.geometry:
                continue

            if region.bilateral:
                for side in _BILATERAL_SIDES:
                    if side not in region.geometry:
                        continue
                    rgb = _color_for(region.id, side, heatmap.colors)
                    fill = _rgb_to_hex(rgb) if rgb is not None else _missing_fill(missing, colormap)
                    path_elem = ET.SubElement(regions_group, "path")
                    path_elem.set("id", f"{region.id}-{side}")
                    path_elem.set("class", "region")
                    path_elem.set("d", region.geometry[side])
                    path_elem.set("fill", fill)
            else:
                rgb = _color_for(region.id, None, heatmap.colors)
                fill = _rgb_to_hex(rgb) if rgb is not None else _missing_fill(missing, colormap)
                path_elem = ET.SubElement(regions_group, "path")
                path_elem.set("id", region.id)
                path_elem.set("class", "region")
                d = region.geometry.get("center", "")
                path_elem.set("d", d)
                path_elem.set("fill", fill)

        if legend and colormap is not None:
            _append_legend(root, heatmap, colormap, vx, vy, vw, vh, lang=lang, background=background)

        _append_title(root, heatmap.title, background)

        return ET.tostring(root, encoding="unicode")
