from __future__ import annotations

import xml.etree.ElementTree as ET

from anatomapa.domain.colormap import ColorMap
from anatomapa.domain.heatmap import Heatmap
from anatomapa.domain.model import AnatomicalModel
from anatomapa.render.base import Figure

_PLACEHOLDER_FILL = "#e0e0e0"
_BILATERAL_SIDES = ("left", "right")

_SVG_NS = "http://www.w3.org/2000/svg"


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    """Converte (R, G, B) para string de cor CSS em hexadecimal."""
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def _canonical_and_side(elem_id: str) -> tuple[str, str | None]:
    """Separa o id do path em (id canônico, lado), onde lado é 'left', 'right' ou None."""
    for suffix, side in (("-left", "left"), ("-right", "right")):
        if elem_id.endswith(suffix):
            return elem_id[: -len(suffix)], side
    return elem_id, None


def _color_for(
    canonical: str,
    side: str | None,
    colors: dict[str, tuple[int, int, int]],
) -> tuple[int, int, int] | None:
    """Cor de um path: usa a chave lateralizada (ex.: 'hand_left') se existir,
    senão cai na chave canônica ('hand'). Retorna None se nenhuma tiver valor."""
    if side is not None:
        key = f"{canonical}_{side}"
        if key in colors:
            return colors[key]
    return colors.get(canonical)


def _parse_viewbox(svg_string: str) -> tuple[float, float, float, float]:
    """Extrai min-x, min-y, largura e altura do atributo viewBox do SVG."""
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


def _extract_body_outline_d(svg_string: str) -> str | None:
    """Extrai o atributo d do path com id='body-outline', ou None se ausente."""
    try:
        root = ET.fromstring(svg_string)
    except ET.ParseError:
        return None
    for elem in root.iter():
        if elem.get("id") == "body-outline":
            return elem.get("d")
    return None


def _compute_ticks(value_min: float, value_max: float, n: int = 5) -> list[float]:
    """Calcula ~n valores uniformes entre value_min e value_max para os ticks da legenda."""
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
) -> None:
    """Insere barra de gradiente VERTICAL no lado direito da figura (estilo gganatogram).

    O viewBox do elemento raiz é expandido lateralmente para acomodar a legenda
    sem sobrepor o corpo. Design: barra vertical com gradiente (topo=máximo,
    base=mínimo), rótulo acima e ticks numéricos à direita.
    """
    # Largura da faixa da legenda: ~22% do vw original
    legend_w = vw * 0.22
    new_total_w = vw + legend_w

    # Atualiza o viewBox do elemento raiz para a largura expandida
    root.set("viewBox", f"{vx} {vy} {new_total_w} {vh}")

    # Posição e dimensões da barra
    bar_h = vh * 0.55
    bar_w = legend_w * 0.20
    # Âncora horizontal: início da faixa extra + margem
    bar_x = vx + vw + legend_w * 0.18
    # Centralizado verticalmente
    bar_y = vy + (vh - bar_h) / 2.0

    label_size = vh * 0.020
    tick_font_size = vh * 0.018
    tick_len = bar_w * 0.55

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
    n_stops = 15
    for i in range(n_stops + 1):
        # t=0 -> topo (quente/max), t=1 -> base (frio/min)
        t_color = 1.0 - i / n_stops
        color = _rgb_to_hex(colormap.color_at(t_color))
        stop = ET.SubElement(grad, "stop")
        stop.set("offset", f"{i * 100 // n_stops}%")
        stop.set("stop-color", color)

    # Barra de gradiente com cantos levemente arredondados
    bar_rx = round(bar_w * 0.20, 2)
    bar = ET.SubElement(root, "rect")
    bar.set("id", "legend-bar")
    bar.set("x", str(round(bar_x, 2)))
    bar.set("y", str(round(bar_y, 2)))
    bar.set("width", str(round(bar_w, 2)))
    bar.set("height", str(round(bar_h, 2)))
    bar.set("fill", f"url(#{grad_id})")
    bar.set("rx", str(bar_rx))

    # Borda fina clara sobre a barra
    bar_border = ET.SubElement(root, "rect")
    bar_border.set("id", "legend-bar-border")
    bar_border.set("x", str(round(bar_x, 2)))
    bar_border.set("y", str(round(bar_y, 2)))
    bar_border.set("width", str(round(bar_w, 2)))
    bar_border.set("height", str(round(bar_h, 2)))
    bar_border.set("fill", "none")
    bar_border.set("stroke", "rgba(255,255,255,0.40)")
    bar_border.set("stroke-width", str(round(vw * 0.0015, 2)))
    bar_border.set("rx", str(bar_rx))

    # Rótulo acima da barra
    axis_label = "Valor" if lang == "pt" else "Value"
    label_elem = ET.SubElement(root, "text")
    label_elem.set("id", "legend-label")
    label_elem.set("x", str(round(bar_x + bar_w / 2.0, 2)))
    label_elem.set("y", str(round(bar_y - label_size * 0.6, 2)))
    label_elem.set("text-anchor", "middle")
    label_elem.set("font-size", str(round(label_size, 2)))
    label_elem.set("font-family", "sans-serif")
    label_elem.set("fill", "#e0e0e0")
    label_elem.text = axis_label

    # Ticks: ~5 valores uniformes entre min e max
    ticks = _compute_ticks(heatmap.value_min, heatmap.value_max)
    tick_x_start = bar_x + bar_w
    tick_x_end = tick_x_start + tick_len
    text_x = tick_x_end + legend_w * 0.04

    for tick_val in ticks:
        # Proporção vertical: max no topo (y=bar_y), min na base (y=bar_y+bar_h)
        t = (tick_val - heatmap.value_min) / (heatmap.value_max - heatmap.value_min) if heatmap.value_max != heatmap.value_min else 0.0
        tick_y = bar_y + bar_h * (1.0 - t)

        # Linha do tick
        tick_line = ET.SubElement(root, "line")
        tick_line.set("x1", str(round(tick_x_start, 2)))
        tick_line.set("y1", str(round(tick_y, 2)))
        tick_line.set("x2", str(round(tick_x_end, 2)))
        tick_line.set("y2", str(round(tick_y, 2)))
        tick_line.set("stroke", "rgba(255,255,255,0.55)")
        tick_line.set("stroke-width", str(round(vw * 0.0015, 2)))

        # Texto do tick
        tick_text = ET.SubElement(root, "text")
        tick_text.set("x", str(round(text_x, 2)))
        tick_text.set("y", str(round(tick_y + tick_font_size * 0.35, 2)))
        tick_text.set("text-anchor", "start")
        tick_text.set("font-size", str(round(tick_font_size, 2)))
        tick_text.set("font-family", "sans-serif")
        tick_text.set("fill", "#cccccc")
        tick_text.text = _format_tick(tick_val)


def _build_smooth_svg(
    base_svg: str,
    heatmap: Heatmap,
    colormap: ColorMap,
    legend: bool,
    lang: str = "pt",
) -> str:
    """Constrói SVG com degradê térmico contínuo via feGaussianBlur.

    Estratégia de camadas (de baixo para cima):
    1. <defs>: filtro de blur + máscara sólida do corpo.
    2. Grupo externo com mask="url(#body-mask)": recorta tudo na silhueta do corpo.
       - Grupo interno blurred (sem clipPath nem mask): base fria + regiões coloridas.
         O blur age livremente antes do recorte -- sem bordas duras internas.
    3. Linhas musculares por cima (dentro da mask): stroke escuro semitransparente
       traça as divisões de músculo sem apagar as cores.

    Máscara body-mask: body-outline branco + todos os paths de região com stroke
    branco grosso (~5% do vw) que fecha os vãos entre os sub-paths musculares.
    O resultado é uma silhueta sólida e sem buracos -- borda nítida, blur apenas interno.

    Saída determinística (ordem estável de ids e atributos fixos).
    """
    ET.register_namespace("", _SVG_NS)
    base_root = ET.fromstring(base_svg)

    vx, vy, vw, vh = _parse_viewbox(base_svg)

    root = ET.Element("svg")
    root.set("xmlns", _SVG_NS)
    root.set("viewBox", f"{vx} {vy} {vw} {vh}")

    if heatmap.title:
        title_elem = ET.SubElement(root, "title")
        title_elem.text = heatmap.title

    defs = ET.SubElement(root, "defs")

    # Desfoque: ~1.5% da largura do viewBox -- suaviza juntas entre regiões sem
    # dissolver a forma. O recorte pela mask garante borda nítida.
    blur_std = round(vw * 0.015, 2)
    filter_id = "thermal-blur"
    filt = ET.SubElement(defs, "filter")
    filt.set("id", filter_id)
    # Área estendida para o blur não ser cortado antes da mask
    filt.set("x", "-10%")
    filt.set("y", "-10%")
    filt.set("width", "120%")
    filt.set("height", "120%")
    filt.set("color-interpolation-filters", "sRGB")
    blur_elem = ET.SubElement(filt, "feGaussianBlur")
    blur_elem.set("in", "SourceGraphic")
    blur_elem.set("stdDeviation", str(blur_std))

    cold_color = _rgb_to_hex(colormap.color_at(0.0))

    # Stroke que "engorda" cada path para cobrir os vãos entre regiões (~5.0% do vw)
    region_stroke_w = str(round(vw * 0.050, 2))

    # Coleta paths do SVG base preservando geometria real
    base_paths: dict[str, str] = {}
    for elem in base_root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "g" and elem.get("id") == "regions":
            for child in elem:
                ctag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if ctag == "path":
                    pid = child.get("id", "")
                    pd = child.get("d", "")
                    if pid:
                        base_paths[pid] = pd

    # Máscara sólida do corpo: body-outline branco + todos os paths de região com
    # stroke branco grosso que fecha os vãos entre sub-paths musculares.
    mask_id = "body-mask"
    outline_d = _extract_body_outline_d(base_svg)
    mask = ET.SubElement(defs, "mask")
    mask.set("id", mask_id)
    if outline_d:
        mask_outline = ET.SubElement(mask, "path")
        mask_outline.set("d", outline_d)
        mask_outline.set("fill", "white")
        mask_outline.set("stroke", "white")
        mask_outline.set("stroke-width", region_stroke_w)
        mask_outline.set("stroke-linejoin", "round")
    for pid in sorted(base_paths):
        mask_path = ET.SubElement(mask, "path")
        mask_path.set("d", base_paths[pid])
        mask_path.set("fill", "white")
        mask_path.set("stroke", "white")
        mask_path.set("stroke-width", region_stroke_w)
        mask_path.set("stroke-linejoin", "round")

    # Grupo externo com a máscara: recorta na silhueta do corpo (borda nítida).
    # O blur é computado ANTES do recorte (filtro no grupo interno).
    masked_group = ET.SubElement(root, "g")
    masked_group.set("mask", f"url(#{mask_id})")

    # Grupo interno blurred SEM clipPath nem mask: o blur age livremente dentro
    # da área expandida do filtro antes de ser cortado pelo masked_group.
    blurred_group = ET.SubElement(masked_group, "g")
    blurred_group.set("filter", f"url(#{filter_id})")

    # Base fria com a FORMA do corpo (body-outline). O stroke da mesma cor fecha
    # os vãos do path composto. Se não houver body-outline, usa rect de fallback.
    if outline_d:
        inner_base = ET.SubElement(blurred_group, "path")
        inner_base.set("d", outline_d)
        inner_base.set("fill", cold_color)
        inner_base.set("stroke", cold_color)
        inner_base.set("stroke-width", region_stroke_w)
        inner_base.set("stroke-linejoin", "round")
    else:
        inner_base = ET.SubElement(blurred_group, "rect")
        inner_base.set("x", str(round(vx - vw * 0.15, 2)))
        inner_base.set("y", str(round(vy - vh * 0.15, 2)))
        inner_base.set("width", str(round(vw * 1.30, 2)))
        inner_base.set("height", str(round(vh * 1.30, 2)))
        inner_base.set("fill", cold_color)

    # Pinta todas as regiões com fill+stroke da cor correspondente.
    # Regiões sem valor recebem a cor fria para não deixar buracos no degradê.
    for elem_id in sorted(base_paths):
        canonical_id, side = _canonical_and_side(elem_id)
        rgb = _color_for(canonical_id, side, heatmap.colors)
        fill = _rgb_to_hex(rgb) if rgb is not None else cold_color

        path_elem = ET.SubElement(blurred_group, "path")
        path_elem.set("id", elem_id)
        path_elem.set("d", base_paths[elem_id])
        path_elem.set("fill", fill)
        path_elem.set("stroke", fill)
        path_elem.set("stroke-width", region_stroke_w)
        path_elem.set("stroke-linejoin", "round")
        path_elem.set("stroke-linecap", "round")

    # Linhas musculares: stroke escuro semitransparente traça as divisões dos
    # músculos por cima do degradê, dentro da máscara do corpo.
    muscle_stroke_w = str(round(vw * 0.004, 2))
    muscle_group = ET.SubElement(masked_group, "g")
    muscle_group.set("id", "muscle-lines")
    for pid in sorted(base_paths):
        mp = ET.SubElement(muscle_group, "path")
        mp.set("d", base_paths[pid])
        mp.set("fill", "none")
        mp.set("stroke", "rgba(0,0,0,0.35)")
        mp.set("stroke-width", muscle_stroke_w)
        mp.set("stroke-linejoin", "round")

    if legend:
        _append_legend(root, heatmap, colormap, vx, vy, vw, vh, lang=lang)

    return ET.tostring(root, encoding="unicode")


def _format_value(v: float) -> str:
    """Formata valor numérico para exibição na legenda."""
    if v == int(v):
        return str(int(v))
    return f"{v:.2f}"


def _format_tick(v: float) -> str:
    """Formata um valor de tick da legenda.

    Arredonda sempre ao inteiro mais próximo para produzir rótulos limpos
    no estilo ggplot. Valores de tick são posições aproximadas de escala,
    não medições precisas, então a perda de fração é intencional.
    """
    return str(round(v))


class SvgRenderer:
    """Aplica um Heatmap sobre um clone do SVG base.

    Regiões sem valor no heatmap recebem preenchimento neutro placeholder.
    Saída é determinística: ordem estável de atributos e regiões.
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
    ) -> Figure:
        """Aplica as cores do heatmap sobre o SVG anatômico.

        Parameters
        ----------
        heatmap:
            Heatmap com mapeamento region_id -> cores RGB.
        model:
            AnatomicalModel com geometria e metadados das regiões.
        lang:
            Idioma dos rótulos ("pt" ou "en").
        base_svg:
            Conteúdo SVG como string. Quando None, reconstrói a partir da geometria do modelo.
        smooth:
            Se True, aplica degradê térmico contínuo com feGaussianBlur.
        legend:
            Se True, insere barra de cores com rótulos de intensidade.
        colormap:
            ColorMap usado para gerar stops da legenda e do modo smooth.

        Returns
        -------
        Figure
            Figura renderizada encapsulando a string SVG final.
        """
        if smooth and base_svg is not None and colormap is not None:
            svg_str = _build_smooth_svg(base_svg, heatmap, colormap, legend, lang=lang)
        elif base_svg is not None:
            svg_str = self._render_onto_svg(base_svg, heatmap, model, legend, colormap, lang=lang)
        else:
            svg_str = self._render_from_model(heatmap, model, lang, legend, colormap)

        return Figure(svg_str)

    def _render_onto_svg(
        self,
        base_svg: str,
        heatmap: Heatmap,
        model: AnatomicalModel,
        legend: bool = False,
        colormap: ColorMap | None = None,
        lang: str = "pt",
    ) -> str:
        """Clona a árvore SVG e aplica as cores de preenchimento do heatmap."""
        ET.register_namespace("", _SVG_NS)
        root = ET.fromstring(base_svg)

        def tag_name(elem: ET.Element) -> str:
            return elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

        # Injeta título no SVG clonado quando presente
        if heatmap.title:
            existing_titles = [e for e in root if tag_name(e) == "title"]
            if not existing_titles:
                title_elem = ET.Element("title")
                title_elem.text = heatmap.title
                root.insert(0, title_elem)

        def find_regions_group(root: ET.Element) -> ET.Element | None:
            for elem in root.iter():
                if tag_name(elem) == "g" and elem.get("id") == "regions":
                    return elem
            return None

        regions_group = find_regions_group(root)
        if regions_group is None:
            return ET.tostring(root, encoding="unicode")

        for elem in regions_group:
            if tag_name(elem) != "path":
                continue
            elem_id = elem.get("id", "")
            if not elem_id:
                continue

            # Cor por lado: chave lateralizada (ex.: 'hand_left') senão a canônica
            canonical_id, side = _canonical_and_side(elem_id)
            rgb = _color_for(canonical_id, side, heatmap.colors)
            fill = _rgb_to_hex(rgb) if rgb is not None else _PLACEHOLDER_FILL

            elem.set("fill", fill)
            # Remove atributo style para evitar conflito com o atributo fill
            if "style" in elem.attrib:
                del elem.attrib["style"]

        if legend and colormap is not None:
            vx, vy, vw, vh = _parse_viewbox(base_svg)
            _append_legend(root, heatmap, colormap, vx, vy, vw, vh, lang=lang)

        return ET.tostring(root, encoding="unicode")

    def _render_from_model(
        self,
        heatmap: Heatmap,
        model: AnatomicalModel,
        lang: str,
        legend: bool = False,
        colormap: ColorMap | None = None,
    ) -> str:
        """Constrói o SVG do zero a partir da geometria do modelo quando não há SVG base."""
        ET.register_namespace("", _SVG_NS)
        root = ET.Element("svg")
        root.set("xmlns", _SVG_NS)
        root.set("viewBox", "0 0 400 900")

        if heatmap.title:
            title_elem = ET.SubElement(root, "title")
            title_elem.text = heatmap.title

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
                    fill = _rgb_to_hex(rgb) if rgb is not None else _PLACEHOLDER_FILL
                    path_elem = ET.SubElement(regions_group, "path")
                    path_elem.set("id", f"{region.id}-{side}")
                    path_elem.set("class", "region")
                    path_elem.set("d", region.geometry[side])
                    path_elem.set("fill", fill)
            else:
                rgb = _color_for(region.id, None, heatmap.colors)
                fill = _rgb_to_hex(rgb) if rgb is not None else _PLACEHOLDER_FILL
                path_elem = ET.SubElement(regions_group, "path")
                path_elem.set("id", region.id)
                path_elem.set("class", "region")
                d = region.geometry.get("center", "")
                path_elem.set("d", d)
                path_elem.set("fill", fill)

        if legend and colormap is not None:
            _append_legend(root, heatmap, colormap, 0.0, 0.0, 400.0, 900.0, lang=lang)

        return ET.tostring(root, encoding="unicode")
