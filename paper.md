---
title: 'Anatomapa: An Open-Source Python Package for Visualizing Anatomical Patterns in Epidemiological and Injury Data'
tags:
  - python
  - anatomy
  - body map
  - heatmap
  - data visualization
  - epidemiology
  - forensic science
  - sports medicine
  - svg
authors:
  - name: Marcelo Reis
    orcid: 0000-0002-9195-7750
    affiliation: "1"
    corresponding: true
    equal-contrib: true
  - name: Pedro Henrique Rosa Cruz
    orcid: 0009-0003-6273-5803
    affiliation: "2"
    equal-contrib: true
  - name: Felipe de Carvalho Silva
    orcid: 0009-0001-8221-3039
    affiliation: "1"
  - name: João Paulo Lopes-Silva
    orcid: 0000-0002-2033-365X
    affiliation: "1, 3, 4"
  - name: Rafael Lima Kons
    orcid: 0000-0003-1615-5464
    affiliation: "5"
  - name: Mozart de Melo Alves Júnior
    orcid: 0000-0002-4865-6581
    affiliation: "2"
affiliations:
  - name: Postgraduate Program in Environmental Systems Analysis, CESMAC University Center, Maceió, Alagoas, Brazil
    index: 1
  - name: Department of Technology, CESMAC University Center, Maceió, Alagoas, Brazil
    index: 2
  - name: Applied Performance and Health Research Group, CESMAC University Center, Maceió, Alagoas, Brazil
    index: 3
  - name: National Institute of Research in Sport Science and Nutrition, Research Center III, Maceió, Alagoas, Brazil
    index: 4
  - name: Department of Physical Education, Faculty of Education, Federal University of Bahia, Salvador, Bahia, Brazil
    index: 5
date: 26 October 2026
bibliography: paper.bib
---

## Summary

Anatomical location is a variable routinely recorded in health, forensic, and sports-injury
datasets, yet it is typically reduced to a categorical label and summarized with frequencies or
conventional statistical plots, which obscures the spatial relationships between affected regions
[@cattaneo2024; @gotardelo2023]. `Anatomapa` is a Python package that turns this kind of
region-indexed tabular data into anatomical heatmaps of the external human body surface: given a
mapping from body region to a numeric value (frequency, intensity, or event density), it renders
the body, in anterior and posterior views, male or female, colored by a continuous thermal scale,
with an automatically generated legend and an optional title. The same input always produces the
exact same output, down to the byte, because the figure is regenerated directly from the data
rather than drawn by hand and reused.

The library's core depends only on the Python standard library: the SVG geometry, the XML
serialization, the color interpolation, and the optional PNG/JPEG encoding are all implemented
in-house, with no third-party package such as `matplotlib`, `pandas`, or `Pillow` required for the
core workflow. A companion static web application runs the same library client-side through
Pyodide [@pyodide], letting a non-programmer type values by hand or import a spreadsheet and get
the same heatmap in the browser, with no backend and no data leaving the user's machine.

We validated `Anatomapa` on three independent, contrasting datasets: a 10-year registry of 45,846
scorpion-sting notifications in Maceió, Brazil; 4,030 shark-bite records from the Global Shark
Attack File [@sharkdatalab]; and 185 training and competition injuries in elite Para Taekwondo
athletes [@felix2026]. Despite differing substantially in scale, injury mechanism, and spatial
resolution, all three datasets were represented through the same visualization pipeline with no
case-specific code, supporting the package's use as a general-purpose tool for anatomical pattern
visualization.

Data enters as a `dict`, a list of `(region, value)` records, or through dedicated readers for
CSV, JSON, and Excel `.xlsx` files, with the caller declaring which column holds the region and
which holds the value. Region identification is strict: a label must match one of the 32 canonical
region identifiers, organized in a shallow hierarchy (for example, `hand` under `arm`), or an
explicit user-declared mapping; an unrecognized label raises an error that suggests the closest
valid identifier instead of failing silently or guessing. A value given at an aggregate level, such
as the whole lower limb, automatically rolls down to its anatomical children that have no value of
their own, so partial or coarse-grained datasets still produce a complete figure.

## Statement of need

Anatomical location is a pivotal variable in injury-pattern analysis and the biological profiling
of injuries and diseases [@cattaneo2024], recorded across trauma, occupational, animal-related,
and sports-medicine datasets alike [@gotardelo2023]. Despite this inherently spatial character,
researchers commonly analyze anatomical location as a categorical variable and summarize it with
frequencies, tables, or conventional statistical plots [@edouard2026], which can obscure broader
spatial relationships: two datasets may report similar frequencies for individual regions while
differing markedly in how those regions cluster across the body. Generating a spatial
representation instead currently depends on manual figure editing, a mapping tool scoped to one
specific purpose, or an AI assistant, none of which is fully reproducible from the raw data.

Existing approaches for transforming region-coded observations into anatomical figures are tied to
a specific instrument or anatomical scope. `CHOIRBM` [@cramer2022] renders body-pain-location data
collected with one particular pain-registry instrument onto a fixed 74-segment silhouette built on
R's `ggplot2`, and `gganatogram` [@maag2018] targets internal organs, tissues, and anatomical
systems rather than the external body surface. Neither is suited to the general problem of turning
an arbitrary region-value table, from any domain that records where on the body something
happened, into a reproducible figure.

`Anatomapa` was developed to close this gap while analyzing a 10-year scorpionism dataset in a
tropical city in the Global South, where converting over 45,000 region-coded sting notifications
into a spatial figure had no existing, readily reusable solution. The package has since been
validated on two additional, independently sourced datasets, shark-bite records from the Global
Shark Attack File [@sharkdatalab] and Para Taekwondo training and competition injuries
[@felix2026], confirming that the same zero-dependency, Python stdlib-only pipeline generalizes
across domains, injury mechanisms, and data volumes without case-specific code. `Anatomapa` is
aimed at researchers in epidemiology and toxinology who need standardized, citable figures;
forensic and sports-medicine practitioners mapping the spatial distribution of lesions; and
students and reviewers who need to reproduce a published figure exactly from the dataset behind
it.

## Software design

The library follows a pragmatic Clean Architecture: an immutable domain (`Region`,
`AnatomicalModel`, `ColorMap`, `Heatmap`, implemented as frozen dataclasses) at the center, use
cases and pure transformations around it, and I/O, such as the SVG parser, the file readers, and
the raster encoder, pushed to the outer layer, with dependencies only ever pointing inward. The
anatomical model's single source of truth is a hand-authored SVG per view (anterior/posterior,
male/female), parsed once at runtime and cached; region metadata, labels in Portuguese and
English, laterality, and parent region, live in a separate JSON file, kept in sync with the SVG by
a dedicated test suite. Renderer and scale are implemented as interchangeable strategies behind a
registry, so the public API stays a single `heatmap()` call while the underlying machinery (linear
and logarithmic scales, alternative color maps) remains extensible without touching the facade.
Side (left/right) follows the observer's convention, the hand drawn on the right side of the image,
not the subject's anatomical right, which the library documents explicitly to prevent silently
mirrored data. The package enforces 90%-plus statement coverage in continuous integration,
including a determinism test that re-renders every example and diffs the output byte-for-byte.

## Figures

![Anatomical heatmap in anterior view for male and female body models, colored by the library's
thermal scale with an automatically generated legend.\label{fig:hero}](assets/screenshots/hero-en.png)

Figure \autoref{fig:hero} shows the default anterior-view output for both supported body models;
`view="both"` renders the anterior and posterior views side by side under one shared color scale.

## AI usage disclosure

The authors used Claude Code (Anthropic), a generative AI coding assistant, throughout the
development of the `Anatomapa` library and its companion web application. The tool assisted in
implementing the SVG rendering pipeline, the file readers, and the test suite, and in drafting the
project's documentation. The authors directed every architectural decision, defined the anatomical
domain rules, including the region hierarchy, the observer-based laterality convention, and the
resolution of the color scale, and designed and configured the specialized AI subagents used in the
development workflow. All AI-generated code, tests, and documentation were reviewed, validated, and,
where necessary, corrected by the authors, who retain full responsibility for the final design and
implementation of the software.

## Acknowledgements

We thank the teams responsible for the Notifiable Diseases Information System (SINAN), the Global
Shark Attack File, and the Brazilian Confederation of Taekwondo (CBTKD) for making the case-study
datasets available, and Centro Universitário CESMAC for institutional support. The authors declare
no conflicts of interest. This research received no specific grant from any funding agency in the
public, commercial, or not-for-profit sectors beyond the institutional support from CESMAC
acknowledged above.

## References
