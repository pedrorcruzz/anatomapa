<p align="center">
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/icon.svg?v=4" width="120" alt="anatomapa" />
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
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/hero.png?v=4" alt="Male and female anatomical heatmap with legend" width="720" />
</p>

<br>

## About

**anatomapa** is a Python library that generates **anatomical heatmaps** of the external
human body surface: you feed it values per region (frequency, intensity or event density)
and it returns the body colored, front and back views, male or female, with color
proportional to each region's value. It fits any field that records the body region:
venomous animal accidents, occupational trauma, sports injuries, forensics, burns and dermatology.

- **Zero dependencies:** Python stdlib only at the core; PNG/JPG is an optional extra.
- **Deterministic:** the same input always produces the exact same SVG.
- **Bilingual:** understands region names in Portuguese and English and writes labels in either.

## Installation

```bash
pip install anatomapa
```

Requires **Python 3.10+**. For PNG/JPG/JPEG (raster output), install the optional extra,
which brings cairosvg and Pillow. The quotes matter, zsh and fish treat brackets as a glob:

```bash
pip install "anatomapa[raster]"
```

## Quick start

```python
import anatomapa as am

fig = am.heatmap({"hand": 5153, "foot": 13666, "face": 845})
fig.save("map.svg")
```

Done: an SVG with hands, feet and face colored by value. The rest of this manual is optional.

## Quick examples

```python
import anatomapa as am
from anatomapa import Region

am.heatmap({
    Region.UPPER_CHEST: 90,
    Region.HAND: 40,
    Region.KNEE: 12,
}).save("map.svg")
```

A dict with three regions is enough. A region with no value comes out in neutral grey,
meaning "no data", not "low value"; and a hand with no side suffix paints both hands.
<p align="center"><img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/exemplo-minimo.png?v=4" alt="Map with upper chest, hands and knees colored and everything else in grey" width="340" /></p>

```python
am.heatmap(
    {Region.LEG: 80, Region.UPPER_BACK: 30},
    view="posterior",
).save("map.svg")
```

`leg` is the whole lower limb: a single value flows down to buttocks, thigh, knee, lower
leg, ankle, foot and toes. Inheritance in action: send data at whatever level you have.
<p align="center"><img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/exemplo-heranca.png?v=4" alt="Posterior view with the whole lower limb hot and the upper back cooler" width="340" /></p>

```python
am.heatmap({
    Region.LEG_RIGHT: 80,        # whole right lower limb
    Region.THIGH_LEFT: 20,       # the left one, segment by segment
    Region.LOWER_LEG_LEFT: 95,
    Region.FOOT_LEFT: 40,
    Region.UPPER_CHEST_RIGHT: 60,
}).save("map.svg")
```

One side as a whole, the other in detail, in the same call. On the right everything comes out
at 80; on the left only what was declared paints, and the toes inherit 40 from the foot, their
closest ancestor. The left hip gets no value and stays unpainted: whoever details a side owns covering it all.
<p align="center"><img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/exemplo-lados.png?v=4" alt="Uniform right side and left side detailed segment by segment" width="340" /></p>

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
| `split`      | `True`, `False`                                                | `False`         | Only with `view="both"`, otherwise `ValueError`: `True` returns the (front, back) pair of independent figures sharing the same color scale |

Returns a [`Figure`](#output-the-figure-object) object. An unknown region name raises
`ResolutionError` (the library's public exception). The palette is always the **thermal**
one (cold blue to hot orange, thermal-camera look) and the scale always **linear**, no choice.

## Background and title

- **`background`**: `"dark"` (#0a0a0a), `"light"` (#ffffff) or `"transparent"` (default);
  legend colors adapt to the chosen background.
- **`title`**: drawn bold, centered relative to the body, above the drawing; a long title
  shrinks its font to fit and the text is also kept as the SVG `<title>`. With `split=True`,
  each figure gets the title.

The **legend** (min..max value bar, label following `lang`) and the **thermal gradient** are
native, no parameter. The scale only counts values that actually paint (an aggregator fully
covered by its children is left out), and tick labels gain decimal places whenever rounding
to integers would repeat two of them.

## Region names

Identification is **strict**: a label must be the exact region id or a key of your
`region_map`; nothing is guessed. An unknown name raises `ResolutionError`, listing what failed
and suggesting the closest match. Control it with `on_unknown`: `"error"` (default), `"skip"` or `"warn"`.

**In code: the `Region` enum.** `from anatomapa import Region` gives 94 constants: the 32
canonical ids plus `_LEFT`/`_RIGHT` versions of the 31 bilateral ones. Each member is the id
string itself (`Region.HAND == "hand"`), with autocomplete and typos becoming immediate errors.

**Laterality.** Every region is bilateral except `genital`, central. The id suffix picks the
side: `Region.HAND_RIGHT` paints only the right hand; without it, both sides. Sides follow the
**observer's** convention (left of the image), not the anatomical one; a side on a central region is an error.

**Your spreadsheet names: `region_map`.** You declare the correspondence once, in code;
keys compare exactly as written in the source, accents and case included:

```python
am.heatmap(data, region_map={"HAND": Region.HAND, "FOREARM": Region.FOREARM})
```

## Regions and hierarchy

There are **32 regions** in a tree up to 3 levels deep. An **aggregator** region has no drawing
of its own: a value on it flows down to its children. In parentheses, where each region draws:

```text
head           Head (aggregator)
├─ face            Face (front)
├─ skull           Skull (back)
└─ neck            Neck (front and back)
trunk          Trunk (aggregator)
├─ shoulder        Shoulder (front and back)
├─ chest           Chest (aggregator)
│  ├─ upper_chest      Upper chest (front)
│  └─ lower_chest      Lower chest (front)
├─ abdomen         Abdomen (aggregator)
│  ├─ upper_abdomen    Upper abdomen (front)
│  └─ lower_abdomen    Lower abdomen (front)
├─ back            Back (aggregator)
│  ├─ upper_back       Upper back (back)
│  └─ lower_back       Lower back (back)
└─ genital         Genital area (front; the only central one)
arm            Upper limb (aggregator)
├─ upper_arm       Upper arm (front and back)
├─ elbow           Elbow (front and back)
├─ forearm         Forearm (front and back)
├─ wrist           Wrist (front and back)
└─ hand            Hand (front and back)
   └─ finger           Fingers (front and back)
leg            Lower limb (aggregator)
├─ hip             Hip (front)
├─ buttocks        Buttocks (back)
├─ thigh           Thigh (front and back)
├─ knee            Knee (front and back)
├─ lower_leg       Lower leg (front and back)
├─ ankle           Ankle (front and back)
└─ foot            Foot (front and back)
   └─ toe              Toes (front and back)
```

**Inheritance (rollup), side-aware.** Send data at whatever level you have. To paint each
region, the library walks up the tree and uses the first ancestor holding a value. Three rules:

1. Walk up until a value is found, and stop at the first one.
2. At each step, the explicit side beats the general key (`foot_left` before `foot`).
3. A deeper region always beats a shallower ancestor: in `{"leg_left": 10, "foot": 2}`,
   the left foot is 2, not 10.

The real forensic case, one side as a whole and the other in detail, is the third of the [Quick examples](#quick-examples).

**Migrating from 0.3 (breaking changes).** `leg` was the calf (now `lower_leg`) and `arm` was
the segment above the elbow (now `upper_arm`); today they are the whole limbs. Since 0.4.0 there
is no runtime warning anymore: old code runs silently while painting something else, so review
your `leg` and `arm` usages before upgrading. `pelvis` became `hip` and `buttocks` moved under `leg`,
so a value on `trunk` no longer paints the buttocks; `chest`, `abdomen` and `back` remain valid, but became aggregators.

**Regions with no data** natively show in **neutral grey** (#9aa0a6), distinct from cold:
"no data" never reads as "few cases". No parameter.

## Data input

`heatmap()` accepts a `dict` or any iterable of `(region, value)` pairs, so every reader's output goes in directly:

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

In `from_xlsx`, `aggregate` handles spreadsheets with one row per case: `"count"` counts
occurrences and `"sum"` sums; `None` (default) expects one row per region.

## Output: the `Figure` object

| Usage            | Result |
|------------------|--------|
| `fig.save("map.svg")` | writes the file; the path extension (`.svg`, `.png`, `.jpg`) decides the format, `fig.save(path, format="png")` overrides it and, with no extension, the heatmap's `format` applies |
| `fig.to_svg()`   | returns the SVG as a `str` |
| `fig.to_png()`   | returns the PNG as `bytes` (requires `anatomapa[raster]`) |
| `fig.to_jpeg()`  | returns the JPEG as `bytes` (requires `anatomapa[raster]`) |
| `str(fig)`       | same as `to_svg()`, raw SVG (handy in templates) |
| Jupyter cell     | renders inline automatically |

For **raster** output, install the extra `pip install "anatomapa[raster]"` (cairosvg and
Pillow, imported only on demand; the core stays zero-dep). Figures rasterise with the same
thermal look as the SVG; without the extra, png/jpg/jpeg raises `ImportError` with the hint.

## Utilities

**`validate(values, body="male", region_map=None)`** does the dry-run: shows what resolves and what does not, without rendering.

```python
am.validate({"hand": 1, "haand": 2, "hand_right": 3})
# {'resolved': {'hand': 'hand', 'hand_right': 'hand_right'},
#  'unresolved': {'haand': {'reason': 'região desconhecida',
#                           'suggestions': ['hand', 'head', 'hand_left']}}}
```

**`list_regions(lang="pt", body="male", view=None)`** lists the regions, each as
`{"id", "label", "bilateral", "parent", "views"}`; `view` filters per view (aggregators, whose `views` is empty, always appear).

## Gallery

<p align="center">
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/fundos.png?v=4" alt="Same map over dark, light and transparent backgrounds, male and female" width="640" />
  <img src="https://raw.githubusercontent.com/pedrorcruzz/anatomapa/main/assets/screenshots/corpo-modelo.png?v=4" alt="Male and female anatomical model" width="420" />
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

<p align="center">⭐ <strong>If anatomapa helped you, leave a star on the repo!</strong> ⭐</p>
