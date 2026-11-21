# Canada on Fire: design and build plan

COMP 6934 course project, Group 15. First written 2026-11-21, updated after the expert review of all three team drafts. The final report is due Fri Dec 18, 11:59 p.m. NT.

## Intent

Tell one clear, evidence-based story about seven decades of Canadian wildfires using the Canadian National Fire Database (CNFDB). It answers the four questions from the approved proposal. The report is an 8-page LaTeX document (12pt), and runnable Python reproduces every figure exactly. A companion website carries the interactive versions.

## Rules we hold ourselves to

These come from the course (L1 p.30, L3, L7, L8, L9, L11, L12, L13).

- Every figure makes one point. Its title is the finding, and the finding is only as strong as a test supports (trend claims carry a test result on the figure).
- Angle, frame, focus. Highlight the focal element in colour, keep the context grey, and annotate the key numbers.
- Bars start at zero and are sorted by value. Part-to-whole charts sum to 100%.
- Choose bin widths for appropriate detail. Radial charts use lines only, never filled areas, since filled area grows with the square of the value.
- Maps of totals are paired with a normalised map (rate per unit of land), so large regions do not look important just for being large.
- One palette that colour-blind readers can tell apart, the same type sizes everywhere, a source line on every figure.
- Tools: pandas, Matplotlib, Seaborn, squarify (course libraries), SciPy for the trend tests, and GeoPandas/pyproj for the maps (an extension of the course's location scatter plots to real projected boundaries and burn perimeters). Plotly Express (L19) for the website.
- Kill any figure that does not earn its place.

## Data decisions (assumption log)

- **Source:** `NFDB_point_20260811.txt` (CNFDB point data, NRCan, Open Government Licence – Canada): 448,447 fires after cleaning. Burned-area polygons 1972–2024.
- **Check:** yearly fires and hectares are compared with NRCan's published summary (`NFDB_point_stats.xlsx`, `fire_data.check_official`). Every year matches within 0.6% except 1979 (0.85 Mha lower in the point file).
- **Years:** keep 1950–2025. Drop `YEAR = -999` and the pre-1950 rows (171 records).
- **Reporting coverage (from the data):** first year per agency is 1950 (BC, YT, PC), 1955 (NL), 1959 (AB, MB, NT, ON, QC, SK), 1960 (NS), 1980 (NB), 2018 (PE). Trend tests use 1980–2025; figures shade earlier years.
- **Province:** assigned by where the fire burned (spatial join of each point to the province outlines; nearest province within 25 km for coastal points; 346 points, 0.08%, stay unassigned). Parks Canada fires therefore count in their province, and the NWT and Nunavut are separate.
- **Cause:** H = Human, N = Lightning (natural), U = Unknown. Unknown is shown in grey, never dropped silently (it is omitted only from the seasonal radar, and the subtitle says so).
- **Month:** seasonal figures drop `MONTH = 0` (records with an unknown month).
- **Size:** 40,028 records have `SIZE_HA = 0`. Size distributions use fires with a recorded size (408,419) and say so; area totals keep them, since they add 0 ha. 23.5% of records are exactly 0.1 ha, a recording habit, so size trends use fires of 1 ha or more.

## Figure lineup (report order)

| # | File | Question | Plot type (lecture) | Point it supports |
|---|---|---|---|---|
| 1 | fig1_trend | Q1 | Two-panel line + 10-yr average, trend tests (L3) | Fires fall (−77/yr, p < 0.001); area has no significant trend but 2023 and 2025 are the two largest years |
| 2 | fig2_season_heatmap | Q1 | Year × month heatmap, square-root scale | Burning is concentrated in May–Aug; 2023 had the largest May on record |
| 3 | fig3_treemap_2023 | Q1 | Treemap (L8) | Five jurisdictions burned over 1.5 Mha in 2023; Quebec and the NWT made up half |
| 4 | fig4_waffle_cause | Q2 | Two waffles (L8) | People start 54% of fires; lightning burns 84% of the area |
| 5 | fig5_radar_season | Q2 | Radar lines, no fill (L11) | Human fires peak in May, lightning in July |
| 6 | fig6_region_cause | Q2 | Ranked stacked bars (L3) | Lightning causes 74–96% of the area in every region over 10 Mha |
| 7 | fig10_ignition_maps | Q2 | Dot maps, small multiples (L3, L12) | Lightning starts in the remote interior; human starts near people |
| 8 | fig7_size_histogram | Q3 | Mirrored log histogram (L7) | 5.3% of fires burn 98.9% of the area; the top 1% burn 83% |
| 9 | fig8_boxen_decade | Q3 | Boxen by decade, Spearman test (L12) | Escaped lightning fires have grown since 1980 (ρ = 0.68); human fires have not |
| 10 | fig9_burn_scars | Q4 | Burn-perimeter map + centre of burning + per-year inset | The belt has not moved north; burning per year doubled in the 2020s and its centre moved ~370 km west |
| 11 | fig11_burn_rate_map | Q4 | Normalised choropleth | Per unit of land, Saskatchewan burns hardest; the NWT is fourth |

Eleven figures of ten distinct types, against a minimum of five. The 8-page report will use a subset (see the LaTeX step); the website shows all of them.

## Visual system

- **Page fit:** figures are drawn at the LaTeX text width of 6.5 in (letter, 1 in margins) and included at 100% scale, so 7–8.5pt figure text prints at 7–8.5pt.
- **Type:** Inter (bundled, SIL Open Font Licence) so every machine renders the same figures. Titles 10.5pt bold, labels and ticks 8–8.5pt, notes and source lines 6.8–7pt grey.
- **Colours:** Lightning `#C77700` (amber), Human `#1F5A99` (blue), Unknown `#8C8C8C` (grey, always direct-labelled), context `#C9C9C9`, neutral `#A09A92`, ink `#222222`, accent `#B3261E` (record / focus). Sequential ramps use seaborn "rocket_r". The amber/blue pair passes the colour-blind checks.
- **Furniture:** no top or right spines, light horizontal grid only where values are read, direct labels instead of legends wherever possible.

## Build structure

```
Project/
  code/fire_data.py       load + clean + province join + official check (single source of truth)
  code/style.py           rcParams, palette, helpers (titles, source line, save)
  code/figures.py         one function per figure, each returns (fig, facts)
  code/prepare_geo.py     one-off simplification of the burn perimeters
  code/build_notebook.py  writes the notebook with each figure's full code
  code/build_website.py   exports the website's chart specs and map layers
  canada_on_fire.ipynb    narrative notebook: one section per question, full figure code
  figures/                figN_name.pdf + .png (generated, never hand-edited)
  website/                companion site
  docs/                   this plan, chart justifications
```

## Plan

1. Done: data module, style, figures, notebook, reproducibility check, website.
2. Done: expert review of our work and the teammates' drafts; adopted their strongest ideas (location-based provinces, official-totals check, per-year normalisation, normalised choropleth, concentration callout, conclusions section) and fixed every must-fix item.
3. Write the LaTeX report (12pt, title page, 8 body pages), choosing the figure subset that fits.
4. Final consistency pass across report, notebook and website.
