# Canada on Fire – COMP 6934 Project (Group 15)

## Setup (once)

Requires Python 3.12.

```bash
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

In VS Code / Jupyter, select the `.venv` kernel.

Install the project dependencies, including the packages for the interactive figures, with:

```bash
pip install -r requirements.txt
```

## Data

**The clean data is already in this repo (`data/clean/`), so you can start making figures straight away.**

You only need the raw downloads if you want to re-run the cleaning. They are not in the repo (2.3 GB, over GitHub's file
size limit); put them in `data/raw/`:

| Folder | Source |
|---|---|
| `data/raw/NFDB_point_txt/` | https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_pnt/current_version/NFDB_point_txt.zip |
| `data/raw/NFDB_poly_large_fires/` | https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_poly/current_version/NFDB_poly_large_fires.zip |
| `data/raw/lpr_000b21a_e/` | https://www12.statcan.gc.ca/census-recensement/2021/geo/sip-pis/boundary-limites/files-fichiers/lpr_000b21a_e.zip |

Then run `notebooks/01_clean.ipynb` top to bottom (about 2 minutes). It writes everything in `data/clean/`.
**Figure notebooks should only read from `data/clean/`.**

## Clean files

### `fires.parquet` – 432,595 fires, 1959–2025

```python
fires = pd.read_parquet("../data/clean/fires.parquet")
```

| Column | Meaning |
|---|---|
| `fire_id`, `agency` | NRCan fire ID and reporting agency (`PC` = Parks Canada) |
| `province` | Province/territory the fire is **located in** (two-letter code) |
| `year`, `month`, `date`, `doy` | `month`/`date`/`doy` (day of year) are empty for ~1% of fires with no recorded date |
| `decade` | `1960s` … `2020s`. `1950s` holds only 1959 and `2020s` only 2020–2025 |
| `cause` | `Human`, `Lightning`, `Unknown` |
| `size_ha` | Final fire size in hectares (0 for ~40k tiny spot fires) |
| `size_class` | Canadian classes A < 0.1 ha, B 0.1–4, C 4–40, D 40–200, E ≥ 200 |
| `is_large` | `size_ha >= 200` |
| `has_size` | `size_ha > 0` – filter on this before any log scale |
| `lat`, `lon` | Degrees; empty for 207 fires with impossible coordinates |
| `x`, `y` | Same location in EPSG:3347 metres – use these on maps |

### `perimeters.parquet` – 16,262 burn perimeters ≥ 200 ha, 1972–2024

```python
perims = gpd.read_parquet("../data/clean/perimeters.parquet")
```

Columns: `fire_id`, `agency`, `year`, `month`, `day`, `size_ha`, `calc_ha`, `cause`, `decade`, `geometry`.

### `provinces.parquet` – 13 provinces and territories

Columns: `province` (code), `name`, `land_km2` (for per-area normalising), `geometry`.

### Other

- `annual_totals.csv` – yearly fires and area burned, overall and ≥ 200 ha. Quick reference only.
- `cleaning_log.csv` – rows removed by each cleaning step.

All three map layers use **EPSG:3347** (StatCan Lambert), so they line up with no reprojection.

## Rules to keep the analysis consistent

1. **Trends over time use `is_large` fires only.** Small fires were badly under-reported before the 1970s, so counts and
   typical sizes from all fires aren't comparable across decades. Large fires are 4.8% of fires but 98.9% of area burned.
2. **Start national time series in 1959.** Before 1959 only BC, Yukon, Newfoundland and Parks Canada reported (already
   removed from the clean data).
3. **Normalise maps by area** (`land_km2`), otherwise the biggest provinces always look worst.
4. **Removed during cleaning:** duplicates, unknown years, prescribed burns, re-burns, and AB/SK mutual-aid responses
   (see `cleaning_log.csv`). Mention this in the report's data section.

## Notebooks (run in order)

| Notebook | What it does |
|---|---|
| `01_clean.ipynb` | Raw downloads → `data/clean/` (only needed if you change the cleaning) |
| `02_explore.ipynb` | Tests each proposal claim; the first cell summarises what holds up |
| `03_figures.ipynb` | Builds all 8 report figures into `figures/` (PDF for LaTeX, PNG previews) |
| `04_interactive.py` | Builds the interactive website figures (requires Plotly and Folium) |

To generate the interactive figures, first install dependencies from the repository root with `pip install -r requirements.txt`.
Then run the script from the `notebooks/` directory so its relative data and output paths resolve correctly:

```bash
cd notebooks
python 04_interactive.py
```

The generated standalone HTML files are saved in `site/interactive/`.

## Figure style

Every figure uses `notebooks/style.py` (`import style; style.apply()`). Use its constants rather than picking colours:

- `style.CAUSE_COLORS` – Lightning orange, Human blue, Unknown grey, the same in every figure
- `style.HEAT` – sequential ramp for amounts (heat map, maps)
- `style.ACCENT` / `style.NEUTRAL` – highlight vs context in single-series charts
- `style.FULL_WIDTH` (6.5 in) / `style.HALF_WIDTH` – figure widths that fit the 12pt LaTeX page
- `style.save(fig, "name")` – writes `figures/name.pdf` and `.png`

## Layout

```
data/raw/        downloads (not shared)
data/clean/      outputs of 01_clean.ipynb
notebooks/       01_clean, 02_explore, 03_figures, style.py
figures/         exported figures for the report
report/          LaTeX source
```
