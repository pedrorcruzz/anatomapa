<p align="center">
  <img src="assets/icon.svg" width="120" alt="anatomapa" />
</p>

<h1 align="center">anatomapa</h1>

<p align="center">
  Turn injury and accident data into heatmaps over the human body.
  From spreadsheet to publish-ready SVG in a few lines of Python.
</p>

<p align="center">
  <a href="README.md"><img src="https://flagcdn.com/24x18/br.png" alt="PT-BR" /> Português</a>
  &nbsp;·&nbsp;
  <a href="README.en.md"><img src="https://flagcdn.com/24x18/us.png" alt="EN" /> <strong>English</strong></a>
</p>

<p align="center">
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=ffdd54" />
  <img alt="License MIT" src="https://img.shields.io/badge/License-MIT-green" />
  <img alt="zero dependencies" src="https://img.shields.io/badge/dependencies-zero%20(stdlib%20only)-orange" />
</p>

<p align="center">
  <img src="assets/screenshots/hero.png" alt="Male and female anatomical heatmap with legend" width="720" />
</p>

<br>

## About

**anatomapa** is a Python library to generate **anatomical heatmaps** of the external human
body surface. You map quantitative data (frequency, intensity or density of events) to
anatomical regions and the library renders a colored map in anterior and posterior views,
with color proportional to each region's value.

It fits any field that records the body region as an analysis variable: venomous animal
accidents (scorpions, snakes, spiders), occupational trauma, sports injuries, forensics,
burns and dermatology.

- **Zero dependencies:** Python standard library only. No matplotlib, pandas, numpy or pillow.
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

fig = am.heatmap(
    {"HAND": 5153, "FOOT": 13666, "head": 845},
    cmap="thermal",
    smooth=True,
    legend=True,
    background="dark",
    lang="en",
)

fig.save("map.svg")      # export the SVG
svg = fig.to_svg()       # or get the SVG string
```

Region names may be given in **Portuguese or English**, upper or lower case: the resolver
maps "HAND", "hand" or "mão" to the same canonical id, and suggests a fix when a name is not
recognized.

## `heatmap()` parameters

| Parameter     | Values                                              | Default      |
|---------------|-----------------------------------------------------|--------------|
| `values`      | `dict` `{region: value}`                            | required     |
| `view`        | `"anterior"`, `"posterior"`                         | `"anterior"` |
| `body`        | `"male"`, `"female"`                                | `"male"`     |
| `cmap`        | `"thermal"`, `"reds"`, `"heat"`, `"viridis"`, `"blues"`, `"greens"` | `"reds"` |
| `scale`       | `"linear"`, `"log"`                                 | `"linear"`   |
| `lang`        | `"pt"`, `"en"` (label language in the SVG)          | `"pt"`       |
| `title`       | `str` or `None`                                     | `None`       |
| `smooth`      | `bool` (continuous thermal gradient)                | `False`      |
| `legend`      | `bool` (value bar on the side)                      | `False`      |
| `background`  | `"dark"`, `"light"`, `"transparent"`                | `"transparent"` |
| `on_unknown`  | `"error"`, `"skip"`, `"warn"` (unrecognized name)   | `"error"`    |
| `region_map`  | `dict` mapping custom names to region ids           | `None`       |
| `assets_dir`  | alternative assets directory                        | `None`       |

Returns a `Figure` object with `.save(path)`, `.to_svg()` and `str(fig)`. In Jupyter, the
figure renders inline automatically.

## Data input

Besides a `dict`, there are readers for the common formats. `heatmap()` accepts either a
`dict` or the reader output directly (no conversion needed):

```python
# CSV (you declare the columns, nothing is guessed)
data = am.from_csv("injuries.csv", region_col="region", value_col="total")
fig = am.heatmap(data, cmap="thermal", lang="en")

# JSON  (object {"hand": 10} or list [{"region": "...", "value": ...}])
fig = am.heatmap(am.from_json("injuries.json"))

# Records (dicts, namedtuples, dataclasses, pandas DataFrame via duck typing)
fig = am.heatmap(am.from_records(records, region_col="region", value_col="total"))

# Excel .xlsx (no external dependency)
data = am.from_xlsx("injuries.xlsx", region_col="D", value_col="E", header=True)
```

## Region names

The resolver is forgiving: it accepts **PT or EN**, any case, **accents**, **plurals** and
**synonyms** ("HAND", "hand", "mão", "hands", "wrist" → `hand`). Unknown names are **never
guessed**: by default the lib **errors and suggests** the closest match (control with `on_unknown`).

**Laterality (left/right).** Bilateral regions accept a side: write "right hand" or "mão direita"
and only the right hand lights up; without a side, both are painted:

```python
am.heatmap({"right hand": 500, "left hand": 20, "right leg": 80})
```

**Your own names.** Use `region_map` (your label → region id, side ids allowed):

```python
am.heatmap(data, region_map={"Upper Right Limb": "arm", "right_hand": "hand_right"})
```

**Check before rendering (dry-run).** `validate()` shows what resolves and what does not:

```python
am.validate({"hand": 1, "pedro": 2, "right hand": 3})
# {'resolved': {'hand': 'hand', 'right hand': 'hand_right'},
#  'unresolved': {'pedro': {'reason': '...', 'suggestions': ['finger', ...]}}}
```

## Regions

10 macro regions. `head` and `trunk` are central; the rest are **bilateral** (a single value
paints both sides):

| id        | Label       | id        | Label        |
|-----------|-------------|-----------|--------------|
| `head`    | Head        | `thigh`   | Thigh        |
| `trunk`   | Trunk       | `leg`     | Leg          |
| `arm`     | Arm         | `foot`    | Foot         |
| `forearm` | Forearm     | `toe`     | Toe          |
| `hand`    | Hand        | `finger`  | Finger       |

```python
am.list_regions(lang="en")   # id, label, whether bilateral, and parent region
```

## Gallery

Male and female bodies, anterior and posterior views, thermal palette and a value legend.
Choose the background (dark, light or transparent).

<p align="center">
  <img src="assets/screenshots/exemplo-maos.png" alt="Hands with high values" width="300" />
  &nbsp;
  <img src="assets/screenshots/exemplo-perna-peito.png" alt="Legs and chest with high values" width="300" />
</p>

<p align="center">
  <img src="assets/screenshots/fundos.png" alt="Same map over dark, light and transparent backgrounds, male and female" width="640" />
</p>

<p align="center">
  <img src="assets/screenshots/corpo-modelo.png" alt="Male and female anatomical model" width="420" />
</p>

## License

Released under the **MIT** license. See [LICENSE](LICENSE).

The SVG model silhouettes derive from a **public-domain (CC0)** source; details in
[`app/anatomapa/assets/ATTRIBUTION.txt`](app/anatomapa/assets/ATTRIBUTION.txt).

## Credits

- **Pedro Rosa** — developer/creator
- **Marcelo Reis** — professor
- **Mozart Melo** — coordinator/advisor
- **Centro Universitário CESMAC** — institution

<br>

<p align="center">
  ⭐ <strong>If anatomapa helped you, leave a star on the repo!</strong> ⭐
</p>
