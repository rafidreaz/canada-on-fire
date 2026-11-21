"""Generate canada_on_fire.ipynb: the narrative notebook with every figure's full code.

Each figure's plotting code is copied into its own cell from code/figures.py (one
source of truth), so the notebook is self-contained to read and still matches the
script exactly.

Run:  python code/build_notebook.py
Then: jupyter nbconvert --to notebook --execute --inplace canada_on_fire.ipynb
"""
import inspect
import sys
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
import figures as F  # noqa: E402

md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
src = lambda obj: inspect.getsource(obj).rstrip()
C = []

C.append(md("""# Canada on Fire: Seven Decades of Wildfire Patterns, Causes and Extremes
**COMP 6934: Introduction to Data Visualization · Fall 2026 · Group 15**

This notebook reproduces every figure in the report, in report order, with the full plotting code of each figure in its own cell. Data loading and cleaning live in `code/fire_data.py` and the visual system (palette, font, sizes) in `code/style.py`; the figure code below is generated from `code/figures.py`, so the script and the notebook always match. Running top to bottom writes `figures/*.pdf` (for LaTeX) and `figures/*.png`.

**Data:** Canadian National Fire Database (CNFDB), Canadian Forest Service, Natural Resources Canada, https://cwfis.cfs.nrcan.gc.ca/en/fire-history, Open Government Licence – Canada. Point data `NFDB_point_20260811.txt`; burned-area polygons 1972–2024.

**Questions**
1. Is the area burned each year increasing, and how unusual was 2023?
2. How do lightning- and human-caused fires differ in where they happen, when they happen, and how big they get?
3. Do a small number of very large fires account for most of the burned area, and has the typical fire size changed by decade?
4. Where are Canada's main wildfire hotspots, and have they shifted over time?"""))

C.append(code("""import sys
from pathlib import Path
sys.path.insert(0, str(Path("code").resolve()))

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

import fire_data as fd
import style as st

st.apply()
%matplotlib inline"""))

C.append(md("""## 1. Data, cleaning and checks
- Years kept: 1950–2025 (drops `YEAR = -999` and 171 sparse pre-1950 records). Most agencies report from 1959; New Brunswick from 1980 and PEI from 2018, so trend tests use **1980–2025** and figures shade the earlier years.
- Cause: H = Human, N = Lightning, U = Unknown (kept and shown, never silently dropped).
- **Province = where the fire burned**, found by a spatial join of each fire point to the province outlines (nearest province within 25 km for coastal points). Parks Canada fires therefore count in their province, and the NWT and Nunavut are separate.
- 40,028 fires have size 0 ha (spot fires). Size figures use fires with a recorded size and say so.
- Seasonal figures drop records with unknown month (`MONTH = 0`).
- The burned-area polygons are simplified to 1 km by `code/prepare_geo.py`, keeping 99.06% of the mapped area. Run it once before the maps."""))
C.append(code("""df = fd.load_fires()
print(f"{len(df):,} fires, {df.YEAR.min()}–{df.YEAR.max()}; "
      f"{df.province.isna().sum()} points outside every province (0.08%)")
df.head()"""))
C.append(md("**Check against the official statistics.** Yearly fire counts and hectares are compared with NRCan's published NFDB summary (`NFDB_point_stats.xlsx`). Only the years listed below differ; all are within 0.6% except 1979, where one record was revised after the summary was produced."))
C.append(code("""diff = fd.check_official(df)
diff[["fires", "FIRES", "fires_diff", "area_ha", "TOTAL_HA", "ha_diff"]] if len(diff) else diff"""))
C.append(code("""summary = df.groupby("cause", observed=True).agg(
    fires=("SIZE_HA", "size"),
    area_Mha=("SIZE_HA", lambda s: s.sum() / 1e6),
    median_ha=("SIZE_HA", "median"))
summary.round(2)"""))
C.append(md("""## 2. Shared helpers
Trend test (Kendall's tau with a Theil–Sen slope and 95% CI), p-value formatting, waffle drawing, and map helpers used by several figures."""))
C.append(code("\n\n\n".join([
    src(F.trend_test), src(F._p), src(F._largest_remainder), src(F._waffle),
    'NEUTRAL = "#A09A92"   # warm grey: neutral context, not a cause colour',
    'GEO_DIR = st.FIG_DIR.parent / "data_derived"\nLAND = "#EFEBE4"',
    src(F._load_geo), src(F._base_map), src(F.scar_centres),
    src(F.stripe_colors), src(F.fire_rings_grid)])))

FIGS = [
    ("Q1: Is the area burned increasing, and how unusual was 2023?", [
        ("fig1_trend", "Figure 1: Fewer fires, extreme worst seasons",
         "Fires per year have fallen since 1980 (−77 a year, p < 0.001). Area burned has no "
         "significant trend over 1980–2025 (Kendall p = 0.10): it swings wildly, and the two largest "
         "years on record are 2023 (17.6 Mha, 2.0x any other) and 2025 (8.7 Mha)."),
        ("fig12_ranked_years", "Figure 2: How unusual was 2023?",
         "Ranked against every year since 1980, 2023 is 2.0x the next-worst year (2025) and 9x the "
         "median year (1.9 Mha)."),
        ("fig2_season_heatmap", "Figure 3: When the land burns",
         "Burning is concentrated in May–August (97% of dated area). 2023 started early, with the "
         "largest May in 76 years (6.5 Mha)."),
        ("fig3_treemap_2023", "Figure 4: 2023 by province and territory",
         "Five jurisdictions each burned over 1.5 Mha in 2023 (93% of the year); Quebec and the NWT "
         "alone made up half."),
    ]),
    ("Q2: How do lightning and human fires differ?", [
        ("fig4_waffle_cause", "Figure 5: Share of fires vs share of area",
         "People start 54% of fires but cause only 12% of the area burned; lightning starts 44% but "
         "burns 84%."),
        ("fig13_cause_share_province", "Figure 6: The same split, region by region",
         "Outside New Brunswick and Nova Scotia, lightning's share of area exceeds its share of fires "
         "by 17–68 points; the gap is widest in Newfoundland and Labrador."),
        ("fig5_radar_season", "Figure 7: Two fire seasons",
         "Human fires peak in May (42% in March–May); 90% of lightning fires start in June–August."),
        ("fig6_region_cause", "Figure 8: Where each cause burns",
         "Lightning burns 73–96% of the area in every province or territory with over 10 Mha burned; "
         "the Maritimes together burned under 0.2 Mha."),
        ("fig10_ignition_maps", "Figure 9: Where fires start, by cause",
         "Lightning ignitions spread across the remote boreal interior; human ignitions trace roads, "
         "rivers and the populated south."),
    ]),
    ("Q3: Do a few huge fires dominate, and has typical size changed?", [
        ("fig7_size_histogram", "Figure 10: A few huge fires do almost all the burning",
         "Fires of 200 ha or more are 5.3% of fires with a recorded size but 98.9% of the area; the "
         "largest 1% burned 83%."),
        ("fig14_concentration_curve", "Figure 11: How concentrated is the burning?",
         "Just 766 fires (0.19%) burned half of all the land burned since 1950."),
        ("fig8_boxen_decade", "Figure 12: Escaped lightning fires have grown since 1980",
         "The yearly median size of lightning fires over 1 ha rose over 1980–2025 (Spearman ρ = 0.68, "
         "p < 0.001; 0.66 without 2023); human fires show no significant change (ρ = 0.28, p = 0.06)."),
    ]),
    ("Q4: Where are the hotspots, and have they shifted?", [
        ("fig9_burn_scars", "Figure 13: Half a century of burn scars",
         "The boreal belt has not moved north (centre of burning 57.7–59.7°N in every decade), but "
         "mapped burning per year doubled in the 2020s and its centre moved about 370 km west."),
        ("fig15_decade_small_multiples", "Figure 14: One map per decade",
         "Every decade burns the same belt; the 2020s (2020–24) averaged 5.5 Mha of mapped burning a "
         "year, double any earlier decade."),
        ("fig11_burn_rate_map", "Figure 15: Burning per unit of land",
         "Per 1,000 km² of land, Saskatchewan burns hardest (935 ha a year), ahead of Manitoba and "
         "Alberta; the NWT, first in total area, is fourth."),
    ]),
    ("Method check: reporting coverage", [
        ("fig16_coverage", "Figure 16: Who reported, and from when",
         "Most agencies report from 1959, New Brunswick from 1980 and PEI from 2018, which is why the "
         "trend tests start in 1980."),
    ]),
    ("Gallery: the same data, drawn to be seen", [
        ("fig17_fire_stripes", "Plate A: Fire stripes",
         "One stripe per year, coloured by area burned; the exact values are in Figures 1 and 2."),
        ("fig18_fire_rings", "Plate B: Fire rings",
         "One ring per year, one sector per week: May–August burns in every ring, and 2023 lit up from "
         "early May. The exact version is Figure 3."),
        ("fig19_ember_field", "Plate C: Ember field",
         "All 448,447 fire starts, sized and lit by final size: large embers fill the remote north, "
         "small ones crowd the populated south."),
    ]),
]
for i, (section, figs) in enumerate(FIGS, start=3):
    C.append(md(f"## {i}. {section}"))
    for fn, title, point in figs:
        C.append(md(f"### {title}\n**Point this figure supports:** {point}"))
        C.append(code(src(getattr(F, fn))))
        C.append(code(f'fig, facts = {fn}(df)\nst.save(fig, "{fn}")\nplt.show()\nfacts'))

C.append(md("""## 9. Conclusions
1. **Q1 (trend and 2023).** Canada reports fewer fires each year (a significant decline since 1980), but area burned has no significant linear trend: it is dominated by extreme seasons. 2023 burned 17.6 Mha, twice any other year, started early (record May) and burned in five jurisdictions at once; 2025 (8.7 Mha) is the second-largest year, so 2023 was not an isolated spike.
2. **Q2 (lightning vs people).** The two causes are different problems. People start more than half of all fires, mostly in spring and near settlements, and those fires stay small. Lightning starts fewer fires, in mid-summer across the remote boreal interior, and burns 84% of the land.
3. **Q3 (concentration and size).** Area burned is extremely concentrated: 5% of fires burn 99% of the area. Among fires that escape past 1 ha, the typical lightning fire has grown steadily since 1980; human fires have not.
4. **Q4 (hotspots).** The fire belt is stable in latitude, but burning per year doubled in the 2020s and its centre moved roughly 370 km west. Scaled by land area, the Prairie provinces (Saskatchewan, Manitoba, Alberta) burn hardest.

**Limitations.** Reporting is incomplete before 1980 and starts late in New Brunswick (1980) and PEI (2018); the 2020s hold six seasons (five for polygons); trends are associations, not causes, and are confounded with changing suppression policy and better satellite mapping; cause is Unknown for 4% of the area."""))

nb = nbf.v4.new_notebook()
nb["cells"] = C
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbf.write(nb, ROOT / "canada_on_fire.ipynb")
print("notebook written:", len(C), "cells")
