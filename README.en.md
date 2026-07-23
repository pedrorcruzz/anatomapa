<p align="center">
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/icon.svg" width="120" alt="anatomapa" />
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
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=ffdd54" />
  <img alt="License MIT" src="https://img.shields.io/badge/License-MIT-green" />
  <img alt="zero dependencies" src="https://img.shields.io/badge/dependencies-zero%20(stdlib%20only)-orange" />
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/hero.png" alt="Male and female anatomical heatmap with legend" width="720" />
</p>

<br>

## About

**anatomapa** is a Python library that generates **anatomical heatmaps** of the external
human body surface. You feed it quantitative data per region (frequency, intensity or event
density) and it returns an SVG with the body colored, in anterior or posterior view, male or
female, with color proportional to each region's value.

It fits any field that records the body region as a variable: venomous animal accidents
(scorpions, snakes, spiders), occupational trauma, sports injuries, forensics, burns and
dermatology.

- **Zero dependencies:** Python stdlib only. No matplotlib, pandas, numpy or pillow.
- **Deterministic:** the same input always produces the exact same SVG.
- **Bilingual:** understands region names in Portuguese and English and writes labels in either.

## Installation

Not on PyPI yet. For now, clone the repository:

```bash
git clone https://github.com/pedrorcruzz/anatomapa.git
cd anatomapa
```

Requires **Python 3.10+**. No external dependencies.

## Quick start

```python
import anatomapa as am

fig = am.heatmap({"HAND": 5153, "FOOT": 13666, "head": 845})
fig.save("map.svg")
```

Done: an SVG with hands, feet and head colored by value. Everything else is optional, and
that is what the rest of this manual covers.

## `heatmap()` parameters

```python
am.heatmap(values, view="anterior", body="male", cmap="reds", scale="linear", lang="pt",
           title=None, smooth=False, legend=False, background="transparent",
           on_unknown="error", missing="neutral", region_map=None, assets_dir=None)
```

| Parameter    | Values                                                         | Default         | What it does |
|--------------|----------------------------------------------------------------|-----------------|--------------|
| `values`     | `dict {region: value}` or `(region, value)` pairs              | required        | Data; accepts reader output directly |
| `view`       | `"anterior"`, `"posterior"`                                    | `"anterior"`    | Body view (front or back) |
| `body`       | `"male"`, `"female"`                                           | `"male"`        | Male or female body |
| `cmap`       | `"reds"`, `"heat"`, `"viridis"`, `"blues"`, `"greens"`, `"thermal"` | `"reds"`   | Color palette |
| `scale`      | `"linear"`, `"log"`                                            | `"linear"`      | How values become intensity |
| `lang`       | `"pt"`, `"en"`                                                 | `"pt"`          | Language of labels written in the SVG |
| `title`      | `str` or `None`                                                | `None`          | Title drawn on the figure |
| `smooth`     | `bool`                                                         | `False`         | Continuous thermal gradient instead of flat colors |
| `legend`     | `bool`                                                         | `False`         | Value bar (min..max) on the side |
| `background` | `"dark"`, `"light"`, `"transparent"`                           | `"transparent"` | Figure background |
| `on_unknown` | `"error"`, `"skip"`, `"warn"`                                  | `"error"`       | What to do with an unrecognized name |
| `missing`    | `"neutral"`, `"cold"`                                          | `"neutral"`     | Color for regions with no data |
| `region_map` | `dict {your label: region id}`                                 | `None`          | Your own name mapping; takes precedence |
| `assets_dir` | `str` or `None`                                                | `None`          | Alternative assets directory |

Returns a [`Figure`](#output-the-figure-object) object. An unknown region name raises
`ResolutionError` (the library's public exception).

## Palettes (`cmap`)

| Palette   | Look | When to use |
|-----------|------|-------------|
| `reds`    | light to red (default) | sober reports, print |
| `heat`    | yellow to red | classic "hot zone" highlighting |
| `viridis` | purple to yellow | perceptually uniform, colorblind friendly |
| `blues`   | light to blue | "cold" data (humidity, exposure) |
| `greens`  | light to green | positive indicators |
| `thermal` | cold blue to hot orange, orange top | thermal-camera look; pairs well with `background="dark"` |

## Scales (`scale`)

- **`"linear"`** (default): color grows proportionally to the value. Good for balanced data.
- **`"log"`**: compresses extreme values. Use it when data is heavily skewed (the typical
  case for accident frequency, where one region concentrates almost everything):

```python
am.heatmap({"foot": 13666, "head": 845}, scale="log")  # the head still shows up
```

## Views and bodies

`view` accepts `"anterior"` (front) and `"posterior"` (back). There is no `"both"`: to get
both views, call `heatmap()` twice.

```python
front = am.heatmap(data, view="anterior", body="female")
back = am.heatmap(data, view="posterior", body="female")
front.save("front.svg"); back.save("back.svg")
```

## Background, legend and smoothing

- **`background`**: `"dark"` (#0a0a0a), `"light"` (#ffffff) or `"transparent"` (default, no
  background). Legend colors adapt to the chosen background.
- **`legend=True`**: draws a pill with the value bar next to the body, from min to max, with
  the label in the `lang` language ("Valor" or "Value").
- **`smooth`**: with `False` (default), each region gets a **flat color**, good for
  categorical reading. With `True`, the library renders a **continuous thermal gradient**
  over the body (model preserved, cold rim, crisp outline), looking like a real thermal image:

```python
am.heatmap(data, cmap="thermal", smooth=True, legend=True, background="dark")
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

**Regions with no data (`missing`).** With `"neutral"` (default), a region without a value
shows in **neutral grey** (#9aa0a6), distinct from cold: "no data" is never mistaken for
"few cases". With `"cold"`, no data becomes the cold color and the whole body gets colored
(thermal-camera look).

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
| `fig.save("map.svg")` | writes the SVG file |
| `fig.to_svg()`   | returns the SVG as a `str` |
| `str(fig)`       | same, raw SVG (handy in templates) |
| Jupyter cell     | renders inline automatically |

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

# 2. Render the map: log scale (skewed data), thermal look on a dark background
fig = am.heatmap(data, view="anterior", body="male", cmap="thermal",
                 scale="log", smooth=True, legend=True, background="dark")
fig.save("map.svg")
```

## Utilities

**`validate(values, view="anterior", body="male", region_map=None, assets_dir=None)`**
does the dry-run: it does not render, it only shows what resolves and what does not.

```python
am.validate({"hand": 1, "pedro": 2, "right hand": 3})
# {'resolved': {'hand': 'hand', 'right hand': 'hand_right'},
#  'unresolved': {'pedro': {'reason': '...', 'suggestions': ['finger', ...]}}}
```

**`list_regions(view="anterior", lang="pt", body="male", assets_dir=None)`** lists the view's
regions, each as `{"id", "label", "bilateral", "parent"}`:

```python
am.list_regions(view="posterior", lang="en")
# [{'id': 'head', 'label': 'Head', 'bilateral': False, 'parent': None}, ...]
```

## Gallery

<p align="center">
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/exemplo-maos.png" alt="Hands with high values" width="300" />
  &nbsp;
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/exemplo-perna-peito.png" alt="Legs and chest with high values" width="300" />
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/fundos.png" alt="Same map over dark, light and transparent backgrounds, male and female" width="640" />
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/dark-vs-light.png" alt="Dark versus light background comparison" width="640" />
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/corpo-modelo.png" alt="Male and female anatomical model" width="420" />
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
