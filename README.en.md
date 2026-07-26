<p align="center">
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/icon.svg?v=2" width="120" alt="anatomapa" />
</p>

<h1 align="center">anatomapa</h1>

<p align="center">
  <strong>Paint the human body with your data.</strong><br/>
  From a dict or a spreadsheet to a publish-ready anatomical heatmap in SVG,
  in a few lines of Python and with zero dependencies.
</p>

<p align="center">
  <a href="https://github.com/pedrorcruzz/anatomapa/blob/main/README.md"><img src="https://flagcdn.com/24x18/br.png" alt="PT-BR" /> Português</a>
  &nbsp;·&nbsp;
  <a href="https://github.com/pedrorcruzz/anatomapa/blob/main/README.en.md"><img src="https://flagcdn.com/24x18/us.png" alt="EN" /> <strong>English</strong></a>
</p>

<p align="center">
  <a href="https://pypi.org/project/anatomapa/"><img alt="PyPI" src="https://img.shields.io/pypi/v/anatomapa?color=blue&logo=pypi&logoColor=white" /></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=ffdd54" />
  <img alt="License MIT" src="https://img.shields.io/badge/License-MIT-green" />
  <img alt="zero dependencies" src="https://img.shields.io/badge/dependencies-zero%20(stdlib%20only)-orange" />
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/hero.png?v=2" alt="Male and female anatomical heatmap with legend" width="720" />
</p>

<br>

## About

**anatomapa** is a Python library that generates **anatomical heatmaps** of the external
human body surface. You feed it quantitative data per region (frequency, intensity or event
density) and it returns the body colored, always in the front (anterior) view, male or
female, with color proportional to each region's value.

It fits any field that records the body region as a variable: venomous animal accidents
(scorpions, snakes, spiders), occupational trauma, sports injuries, forensics, burns and
dermatology.

- **Zero dependencies:** Python stdlib only at the core; PNG/JPG is an optional extra.
- **Deterministic:** the same input always produces the exact same SVG.
- **Bilingual:** understands region names in Portuguese and English and writes labels in either.

## Installation

```bash
pip install anatomapa
```

Requires **Python 3.10+** and no external dependencies.

To generate PNG/JPG/JPEG (raster output), install the optional extra, which brings cairosvg
and Pillow. Pure SVG needs nothing.

```bash
pip install "anatomapa[raster]"
```

The quotes matter: shells like zsh and fish treat the brackets as a file pattern (glob), so
quote the command to make it work everywhere.

> For development, clone the repository: `git clone https://github.com/pedrorcruzz/anatomapa.git`

## Quick start

```python
import anatomapa as am

fig = am.heatmap({"HAND": 5153, "FOOT": 13666, "head": 845})
fig.save("map.svg")
```

Done: an SVG with hands, feet and head colored by value. The rest of this manual is optional.

## `heatmap()` parameters

```python
am.heatmap(values, body="male", lang="pt", format="svg", title=None,
           background="transparent", on_unknown="error", region_map=None)
```

| Parameter    | Values                                                         | Default         | What it does |
|--------------|----------------------------------------------------------------|-----------------|--------------|
| `values`     | `dict {region: value}` or `(region, value)` pairs              | required        | Data; accepts reader output directly |
| `body`       | `"male"`, `"female"`                                           | `"male"`        | Male or female body |
| `lang`       | `"pt"`, `"en"`                                                 | `"pt"`          | Language of labels written in the SVG |
| `format`     | `"svg"`, `"png"`, `"jpg"`, `"jpeg"`                            | `"svg"`         | Output format; png/jpg/jpeg require `pip install anatomapa[raster]` |
| `title`      | `str` or `None`                                                | `None`          | Title drawn on the figure |
| `background` | `"dark"`, `"light"`, `"transparent"`                           | `"transparent"` | Figure background |
| `on_unknown` | `"error"`, `"skip"`, `"warn"`                                  | `"error"`       | What to do with an unrecognized name |
| `region_map` | `dict {your label: region id}`                                 | `None`          | Your own name mapping; takes precedence |

Returns a [`Figure`](#output-the-figure-object) object. An unknown region name raises
`ResolutionError` (the library's public exception). The color palette is always the
**thermal** one (cold blue to hot orange, thermal-camera look); there is no palette choice.
The intensity scale is always **linear**: color grows proportionally to the value.

## Background

- **`background`**: `"dark"` (#0a0a0a), `"light"` (#ffffff) or `"transparent"` (default, no
  background). Legend colors adapt to the chosen background.

The **legend** with the value bar (min..max, label in the `lang` language: "Valor" or
"Value") and the **continuous thermal gradient** over the body (model preserved, crisp
outline) are native behavior of the figure: always present, no parameter. The legend is what
reports the map's values.

```python
am.heatmap(data, background="dark")
```

## Region names

The resolver is forgiving on purpose. It accepts:

| You write                                   | Becomes |
|---------------------------------------------|---------|
| `"HAND"`, `"hand"`, `"hands"`, `"mão"`, `"wrist"` | `hand` |
| `"Dedo da mão"`, `"finger"`, `"fingers"`    | `finger` |
| `"trunk"`, `"tronco"`, `"torso"`            | `trunk` |

That is: **PT or EN**, any case, with or without accents, plurals and synonyms. What it does
**not** do is guess: an unknown name raises `ResolutionError` listing every bad name with
suggestions for the closest match. Control it with `on_unknown`: `"error"` (default),
`"skip"` (ignore silently) or `"warn"` (ignore with a warning).

**Laterality.** Bilateral regions (arm, forearm, hand, finger, thigh, leg, foot, toe) accept
a side: `"right hand"`, `"mão direita"` or the id `"hand_right"` paint only the right hand.
Without a side, the value paints both sides.

```python
am.heatmap({"right hand": 500, "left hand": 20, "right leg": 80})
```

**Your own names.** If your spreadsheet uses internal codes, map them with `region_map`
(side ids allowed; it takes precedence over the resolver):

```python
am.heatmap(data, region_map={"Upper Right Limb": "arm", "right_hand": "hand_right"})
```

## Regions and hierarchy

There are **14 regions**. `trunk` is a **hierarchical aggregator**: it has no geometry of its
own, it only distributes its value to its children. Bilateral regions take one value for both
sides (or an explicit side).

| id        | Label   | View            | Bilateral | Parent  |
|-----------|---------|-----------------|-----------|---------|
| `head`    | Head    | both            | no        |         |
| `trunk`   | Trunk   | aggregator      | no        |         |
| `chest`   | Chest   | front only      | no        | `trunk` |
| `abdomen` | Abdomen | front only      | no        | `trunk` |
| `pelvis`  | Pelvis  | front and back  | no        | `trunk` |
| `back`    | Back    | back only       | no        | `trunk` |
| `arm`     | Arm     | both            | yes       |         |
| `forearm` | Forearm | both            | yes       |         |
| `hand`    | Hand    | both            | yes       |         |
| `finger`  | Finger  | both            | yes       | `hand`  |
| `thigh`   | Thigh   | both            | yes       |         |
| `leg`     | Leg     | both            | yes       |         |
| `foot`    | Foot    | both            | yes       |         |
| `toe`     | Toe     | both            | yes       | `foot`  |

**Rollup (parent-to-children inheritance).** Send data at whatever level you have:

```python
am.heatmap({"trunk": 2602})                             # chest+abdomen+pelvis+back inherit
am.heatmap({"chest": 900, "abdomen": 1200, "pelvis": 500})  # or per part
```

A value on the parent flows down to its children automatically; if you provide a specific
part, it uses its own value. Same logic for `hand` to `finger` and `foot` to `toe`.

**Regions with no data.** A region without a value natively shows in **neutral grey**
(#9aa0a6), distinct from cold: "no data" never reads as "few cases". No parameter.

## Data input

`heatmap()` accepts a `dict` or any iterable of `(region, value)` pairs, so every reader's
output goes in directly, no conversion:

```python
# plain dict (or normalized via from_dict)
fig = am.heatmap(am.from_dict({"hand": 10, "foot": 25}))

# CSV: you declare the columns, nothing is guessed
data = am.from_csv("injuries.csv", region_col="region", value_col="total", delimiter=",")

# JSON: object {"hand": 10} or list [{"region": "...", "value": ...}]
data = am.from_json("injuries.json", region_key="region", value_key="value")

# Records: dicts, namedtuples, dataclasses and pandas DataFrames (duck typing)
data = am.from_records(records, region_col="region", value_col="total")

# Excel .xlsx, no external dependency; column by index, letter "D" or header name
data = am.from_xlsx("injuries.xlsx", sheet="2024", region_col="Region",
                    value_col="Total", header=True)
```

In `from_xlsx`, `aggregate` handles spreadsheets with one row per case: `"count"` counts each
region's occurrences and `"sum"` sums the values. `None` (default) expects one row per region.

## Output: the `Figure` object

| Usage            | Result |
|------------------|--------|
| `fig.save("map.svg")` | writes the file; infers the format from the extension (`.svg`, `.png`, `.jpg`), uses the heatmap's `format`, or accepts `fig.save(path, format="png")` |
| `fig.to_svg()`   | returns the SVG as a `str` |
| `fig.to_png()`   | returns the PNG as `bytes` (requires `anatomapa[raster]`) |
| `fig.to_jpeg()`  | returns the JPEG as `bytes` (requires `anatomapa[raster]`) |
| `str(fig)`       | same as `to_svg()`, raw SVG (handy in templates) |
| Jupyter cell     | renders inline automatically |

For **raster** output (PNG/JPG/JPEG), install the optional extra `pip install anatomapa[raster]`
(brings cairosvg and Pillow, imported only on demand; the core stays zero-dep and pure SVG
never needs an extra). Without the extra installed, requesting png/jpg/jpeg raises an
`ImportError` with the install hint:

```python
fig = am.heatmap(data, format="png")
fig.save("map.png")
```

## Full example

Scorpion sting topography (frequency per region), from raw data to the final map:

```python
import anatomapa as am

data = {"cabeça": 845, "braço": 1831, "antebraço": 974, "mão": 5153,
        "dedo da mão": 8684, "tronco": 2602, "coxa": 1733, "perna": 1984,
        "pé": 13666, "dedo do pé": 6547}

# 1. Check the names before rendering (dry-run, renders nothing)
result = am.validate(data)
assert not result["unresolved"]

# 2. Render the map: thermal look on a dark background
fig = am.heatmap(data, body="male", background="dark")
fig.save("map.svg")
```

## Utilities

**`validate(values, body="male", region_map=None)`**
does the dry-run: it does not render, it only shows what resolves and what does not.

```python
am.validate({"hand": 1, "pedro": 2, "right hand": 3})
# {'resolved': {'hand': 'hand', 'right hand': 'hand_right'},
#  'unresolved': {'pedro': {'reason': '...', 'suggestions': ['finger', ...]}}}
```

**`list_regions(lang="pt", body="male")`** lists the regions,
each as `{"id", "label", "bilateral", "parent"}`:

```python
am.list_regions(lang="en")
# [{'id': 'head', 'label': 'Head', 'bilateral': False, 'parent': None}, ...]
```

## Gallery

<p align="center">
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/exemplo-maos.png?v=2" alt="Hands with high values" width="300" />
  &nbsp;
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/exemplo-perna-peito.png?v=2" alt="Legs and chest with high values" width="300" />
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/fundos.png?v=2" alt="Same map over dark, light and transparent backgrounds, male and female" width="640" />
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/dark-vs-light.png?v=2" alt="Dark versus light background comparison" width="640" />
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/corpo-modelo.png?v=2" alt="Male and female anatomical model" width="420" />
</p>

## License and attribution

Released under the **MIT** license. See [LICENSE](https://github.com/pedrorcruzz/anatomapa/blob/main/LICENSE).

The SVG model silhouettes derive from a **public-domain (CC0)** source; details in
[`app/anatomapa/assets/ATTRIBUTION.txt`](https://github.com/pedrorcruzz/anatomapa/blob/main/app/anatomapa/assets/ATTRIBUTION.txt).

## Credits

- **Pedro Rosa**: developer/creator
- **Marcelo Reis**: Professor of the Graduate Program in Environmental Systems Analysis, CESMAC
- **Mozart Melo**: coordinator/advisor, CESMAC
- **Centro Universitário CESMAC**: institution

<br>

<p align="center">
  ⭐ <strong>If anatomapa helped you, leave a star on the repo!</strong> ⭐
</p>
