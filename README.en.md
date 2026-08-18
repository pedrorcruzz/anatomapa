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
density) and it returns the body colored, front and back views, male or female, with
color proportional to each region's value.

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

The quotes matter: shells like zsh and fish treat the brackets as a glob, so quote the command.

> For development, clone the repository: `git clone https://github.com/pedrorcruzz/anatomapa.git`

## Quick start

```python
import anatomapa as am

fig = am.heatmap({"hand": 5153, "foot": 13666, "head": 845})
fig.save("map.svg")
```

Done: an SVG with hands, feet and head colored by value. The rest of this manual is optional.

## `heatmap()` parameters

```python
am.heatmap(values, view="anterior", body="male", lang="pt", format="svg",
           title=None, background="transparent", on_unknown="error",
           region_map=None, split=False)
```

| Parameter    | Values                                                         | Default         | What it does |
|--------------|----------------------------------------------------------------|-----------------|--------------|
| `values`     | `dict {region: value}` or `(region, value)` pairs              | required        | Data; keys may be `Region`; accepts reader output directly |
| `view`       | `"anterior"`, `"posterior"`, `"both"`                          | `"anterior"`    | Front, back, or the two side by side sharing one legend |
| `body`       | `"male"`, `"female"`                                           | `"male"`        | Male or female body |
| `lang`       | `"pt"`, `"en"`                                                 | `"pt"`          | Language of labels written in the SVG |
| `format`     | `"svg"`, `"png"`, `"jpg"`, `"jpeg"`                            | `"svg"`         | Default when the saved path has no extension; png/jpg/jpeg need the `raster` extra |
| `title`      | `str` or `None`                                                | `None`          | Optional: the title is only drawn when given |
| `background` | `"dark"`, `"light"`, `"transparent"`                           | `"transparent"` | Figure background |
| `on_unknown` | `"error"`, `"skip"`, `"warn"`                                  | `"error"`       | What to do with an unrecognized name |
| `region_map` | `dict {your label: region id}`                                 | `None`          | Your own name mapping; takes precedence |
| `split`      | `True`, `False`                                                | `False`         | Only with `view="both"`: `True` returns the (front, back) pair |

**`split`** only applies to `view="both"`: `False` draws the two views side by side in a single
figure with one legend; `True` makes the call return the **pair** `(anterior, posterior)` of
independent figures, each with its own legend, sharing the same color scale. Any other `view`
raises `ValueError`.

```python
front, back = am.heatmap(data, view="both", split=True)
front.save("front.png")
back.save("back.png")
```

Returns a [`Figure`](#output-the-figure-object) object. An unknown region name raises
`ResolutionError` (the library's public exception). The color palette is always the
**thermal** one (cold blue to hot orange, thermal-camera look); there is no palette choice.
The intensity scale is always **linear**: color grows proportionally to the value.

## Background and title

- **`background`**: `"dark"` (#0a0a0a), `"light"` (#ffffff) or `"transparent"` (default, no
  background). Legend colors adapt to the chosen background.
- **`title`**: when given, it is drawn bold and centered in a band above the drawing; the viewBox
  grows upwards only, the width stays the same, the text color follows the background and a long
  title shrinks its font to fit. It works with any `view` (with `split=True`, each figure gets the
  title) and is also kept as the SVG `<title>`. `None` (default) draws nothing, reserves no space.

The **legend** (min..max value bar, label following `lang`) and the **thermal gradient** over the
body are native: always present, no parameter. E.g. `am.heatmap(data, background="dark")`.

## Region names

Identification is **strict**: a label must be a region id written exactly as defined, or a key
of your `region_map`. Nothing is guessed, so there is never a second correct spelling for the
same region. An unknown name raises `ResolutionError`, listing what failed and suggesting the
closest match. Control it with `on_unknown`: `"error"` (default), `"skip"` or `"warn"`.

**In code: the `Region` enum.** `from anatomapa import Region` gives 30 constants: the 14
canonical ids plus `_LEFT`/`_RIGHT` versions of the 8 bilateral ones. Each member is the id
string itself (`Region.TRUNK == "trunk"`), so it works as a `heatmap()` key or `region_map`
value. The gain: autocomplete and typos becoming immediate errors. `list(Region)` lists them.

**Laterality.** The 8 bilateral regions take a side through the id suffix: `Region.HAND_RIGHT`
paints only the right hand; without it, both sides. A side on a central region is an error.

**Your spreadsheet names: `region_map`.** Source labels rarely match the ids, so you declare
the correspondence once, in code; keys compare exactly as written, accents and case included:

```python
am.heatmap({Region.TRUNK: 50, Region.HAND_LEFT: 100})  # enum (or "trunk"/"hand_left")
am.heatmap(data, region_map={"HAND": Region.HAND, "FOREARM": Region.FOREARM})
```

## Regions and hierarchy

| Id | Region | Front (`anterior`) | Back (`posterior`) | Sided? |
|---|---|:---:|:---:|:---:|
| `head` | head | ✓ | ✓ | no |
| `trunk` | trunk (aggregator) | ✓ | ✓ | no |
| `chest` | chest | ✓ |  | no |
| `abdomen` | abdomen | ✓ |  | no |
| `pelvis` | pelvis | ✓ |  | no |
| `back` | back (dorsum) |  | ✓ | no |
| `buttocks` | buttocks |  | ✓ | no |
| `arm` | arm and shoulder | ✓ | ✓ | yes |
| `forearm` | forearm | ✓ | ✓ | yes |
| `hand` | hand | ✓ | ✓ | yes |
| `finger` | hand fingers | ✓ | ✓ | yes |
| `thigh` | thigh | ✓ | ✓ | yes |
| `leg` | leg | ✓ | ✓ | yes |
| `foot` | foot | ✓ | ✓ | yes |
| `toe` | foot toes | ✓ | ✓ | yes |

Of the **15 regions**, `trunk` is the aggregator: no geometry of its own, it paints the drawn
view's children (front, `chest`+`abdomen`+`pelvis`; back, `back`+`buttocks`). Bilaterals take the
`_left`/`_right` suffix; without it, both sides paint. `list_regions(view=...)` filters per view.

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
| `fig.save("map.svg")` | writes the file; the path extension (`.svg`, `.png`, `.jpg`) decides the format, `fig.save(path, format="png")` overrides it and, with no extension, the heatmap's `format` applies |
| `fig.to_svg()`   | returns the SVG as a `str` |
| `fig.to_png()`   | returns the PNG as `bytes` (requires `anatomapa[raster]`) |
| `fig.to_jpeg()`  | returns the JPEG as `bytes` (requires `anatomapa[raster]`) |
| `str(fig)`       | same as `to_svg()`, raw SVG (handy in templates) |
| Jupyter cell     | renders inline automatically |

For **raster** output (PNG/JPG/JPEG), install the optional extra `pip install anatomapa[raster]`
(brings cairosvg and Pillow, imported only on demand; the core stays zero-dep and pure SVG
never needs an extra). Any figure rasterises correctly: when turned into PNG/JPG it uses a
variant without the SVG filters (which raster converters do not implement), built on demand,
so `am.heatmap(data).save("map.png")`, `to_png()`, `to_jpeg()` and `format="png"` all produce
the same image, with the same colors and the same thermal look. Without the extra installed,
requesting png/jpg/jpeg raises an `ImportError` with the install hint.

## Full example

Scorpion sting topography (frequency per region), from raw data to the final map:

```python
import anatomapa as am
from anatomapa import Region

data = {Region.HEAD: 845, Region.ARM: 1831, Region.FOREARM: 974, Region.HAND: 5153,
        Region.FINGER: 8684, Region.TRUNK: 2602, Region.THIGH: 1733,
        Region.LEG: 1984, Region.FOOT: 13666, Region.TOE: 6547}

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
am.validate({"hand": 1, "haand": 2, "hand_right": 3})
# {'resolved': {'hand': 'hand', 'hand_right': 'hand_right'},
#  'unresolved': {'haand': {'reason': 'região desconhecida',
#                           'suggestions': ['hand', 'head', 'hand_left']}}}
```

**`list_regions(lang="pt", body="male", view=None)`** lists the regions, each as
`{"id", "label", "bilateral", "parent", "views"}`. With `view`, it filters per view:

```python
am.list_regions(lang="en", view="posterior")
# [{'id': 'head', ..., 'views': ['anterior', 'posterior']}, {'id': 'back', ...}, ...]
```

## Gallery

<p align="center">
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/exemplo-maos.png?v=2" alt="Hands with high values" width="300" />
  &nbsp;
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/exemplo-perna-peito.png?v=2" alt="Legs and chest with high values" width="300" />
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/fundos.png?v=2" alt="Same map over dark, light and transparent backgrounds, male and female" width="640" />
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
