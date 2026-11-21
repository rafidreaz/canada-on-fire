# Canada on Fire: Seven Decades of Wildfire Patterns, Causes and Extremes

COMP 6934 Introduction to Data Visualization, Fall 2026, Group 15.
Branch `moskhan` (Md. Omar Shohid Khan).

Four questions, answered from the Canadian National Fire Database (CNFDB):

1. Is the area burned each year increasing, and how unusual was 2023?
2. How do lightning- and human-caused fires differ in where, when and how big they burn?
3. Do a few very large fires account for most of the area, and has the typical fire grown?
4. Where are Canada's wildfire hotspots, and have they shifted?

## What is here

| Path | Contents |
|---|---|
| `canada_on_fire.ipynb` | Narrative notebook with the full code of every figure in its own cell. Runs top to bottom and regenerates all 11 figures. |
| `code/fire_data.py` | Loading and cleaning (one place for every data decision), province-by-location join, check against NRCan's official totals. |
| `code/style.py` | Visual system: palette, Inter font, figure sizes for a 6.5 in LaTeX text width. |
| `code/figures.py` | One function per figure (`fig1_trend` ... `fig11_burn_rate_map`) plus the trend tests. |
| `code/prepare_geo.py` | One-off: simplifies the burn-perimeter shapefiles into `data_derived/`. |
| `code/build_website.py` | Exports the interactive Plotly charts and map layers for `website/`. |
| `code/build_notebook.py` | Writes `canada_on_fire.ipynb`, copying each figure's code from `figures.py`. |
| `figures/` | Report figures, PDF (for LaTeX) and PNG (preview). |
| `website/` | Interactive companion site (static HTML, Plotly 2.34, light/dark toggle). Live: https://omarshohidkhan.github.io/canada-on-fire/ |
| `docs/design-and-plan.md` | Design rules, figure lineup and plan. |
| `docs/chart-justifications.md` | Why each chart type, which alternatives were considered, with lecture references. |
| `data_derived/` | Simplified burn scars 1972-2024 and province outlines (GeoPackage). |
| `assets/fonts/` | Inter (SIL Open Font Licence). |

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Data

Raw data is not in the repo (2.3 GB). Put it in `data/raw/`:

| Folder | Source |
|---|---|
| `data/raw/NFDB_point_txt/NFDB_point_20260811.txt` | https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_pnt/current_version/NFDB_point_txt.zip |
| `data/raw/NFDB_point_stats.xlsx` | Official summary statistics, listed with the point data at https://cwfis.cfs.nrcan.gc.ca/en/fire-history (optional; used only for the totals check) |
| `data/raw/NFDB_poly/` | https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_poly/current_version/NFDB_poly.zip |
| `assets/geo/ne_admin1/` | Natural Earth admin-1, 10m (public domain): https://www.naturalearthdata.com/downloads/10m-cultural-vectors/ |

The point file is the 2026-08-11 release (`NFDB_point_20260811.txt`); a newer "current version" download will have a different file name and slightly different numbers.

The map layers in `data_derived/` are already built, so `prepare_geo.py` (and the two
polygon/Natural Earth downloads) are only needed to rebuild them.

## Reproduce

```bash
jupyter nbconvert --to notebook --execute --inplace canada_on_fire.ipynb   # all report figures
python code/figures.py fig1_trend fig7_size_histogram                       # or selected figures
python code/build_website.py                                                # website data and map layers
cd website && python -m http.server 8000                                    # open http://localhost:8000
```

Data: Canadian National Fire Database, Canadian Forest Service, Natural Resources Canada,
Open Government Licence - Canada.
