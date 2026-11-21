"""Load and clean the Canadian National Fire Database (CNFDB) point data.

Every figure in the project gets its data through `load_fires()`, so all
cleaning decisions live in one place (see docs/design-and-plan.md).
"""
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
_POINT = Path("NFDB_point_txt") / "NFDB_point_20260811.txt"
# Raw data lives in data/raw/ inside a repo checkout, or in ../ProjectData/ locally.
_RAW_DIR = next((d for d in (PROJECT_DIR / "data" / "raw", PROJECT_DIR.parent / "ProjectData")
                 if (d / _POINT).exists()), PROJECT_DIR / "data" / "raw")
DATA_FILE = _RAW_DIR / _POINT

FIRST_YEAR, LAST_YEAR = 1950, 2025
FULL_REPORTING_FROM = 1980  # most agencies report completely from here on

CAUSE_LABELS = {"H": "Human", "N": "Lightning", "U": "Unknown"}
CAUSE_ORDER = ["Lightning", "Human", "Unknown"]

AGENCY_NAMES = {
    "BC": "British Columbia", "AB": "Alberta", "SK": "Saskatchewan",
    "MB": "Manitoba", "ON": "Ontario", "QC": "Quebec",
    "NB": "New Brunswick", "NS": "Nova Scotia", "PE": "Prince Edward Island",
    "NL": "Newfoundland and Labrador", "YT": "Yukon",
    "NT": "Northwest Territories", "PC": "Parks Canada",
}
AGENCY_SHORT = {
    "BC": "BC", "AB": "Alberta", "SK": "Saskatchewan", "MB": "Manitoba",
    "ON": "Ontario", "QC": "Quebec", "NB": "New Brunswick",
    "NS": "Nova Scotia", "PE": "PEI", "NL": "Newfoundland & Lab.",
    "YT": "Yukon", "NT": "NW Territories", "PC": "Parks Canada",
}

# Province/territory the fire burned in (by location, not by reporting agency):
# Parks Canada fires join their province, NWT and Nunavut separate.
PROV_SHORT = {
    "BC": "BC", "AB": "Alberta", "SK": "Saskatchewan", "MB": "Manitoba",
    "ON": "Ontario", "QC": "Quebec", "NB": "New Brunswick", "NS": "Nova Scotia",
    "PE": "PEI", "NL": "Newfoundland & Lab.", "YT": "Yukon",
    "NT": "NW Territories", "NU": "Nunavut",
}
PROVINCES_FILE = PROJECT_DIR / "data_derived" / "canada_provinces.gpkg"
OFFICIAL_STATS = _RAW_DIR / "NFDB_point_stats.xlsx"

SIZE_BINS = [0, 0.1, 1, 10, 100, 1_000, 10_000, np.inf]
SIZE_LABELS = ["<0.1 ha", "0.1-1", "1-10", "10-100", "100-1k", "1k-10k", ">10k ha"]


def load_fires(path: Path = DATA_FILE) -> pd.DataFrame:
    """Return one row per fire, 1950-2025, with tidy derived columns."""
    df = pd.read_csv(
        path,
        encoding="utf-8-sig",
        usecols=["NFDBFIREID", "SRC_AGENCY", "LATITUDE", "LONGITUDE",
                 "YEAR", "MONTH", "DAY", "SIZE_HA", "CAUSE"],
        dtype={"SRC_AGENCY": "string", "CAUSE": "string"},
    )
    df = df[df["YEAR"].between(FIRST_YEAR, LAST_YEAR)].copy()
    df["YEAR"] = df["YEAR"].astype(int)
    df["MONTH"] = df["MONTH"].astype(int)          # 0 = month unknown
    df["cause"] = pd.Categorical(df["CAUSE"].map(CAUSE_LABELS), CAUSE_ORDER)
    df["agency"] = df["SRC_AGENCY"].str.strip()
    df["region"] = df["agency"].map(AGENCY_SHORT)
    df["decade"] = (df["YEAR"] // 10) * 10
    df["size_class"] = pd.cut(df["SIZE_HA"], SIZE_BINS, labels=SIZE_LABELS,
                              include_lowest=True, right=False)
    df = df.reset_index(drop=True)
    df["province"] = pd.Categorical(add_province(df).map(PROV_SHORT),
                                    list(PROV_SHORT.values()))
    return df


def add_province(df: pd.DataFrame) -> pd.Series:
    """Two-letter code of the province/territory each fire point falls in.

    Points just offshore or on a simplified coastline (1.3%) take the nearest
    province within 25 km; the remaining 346 (0.08%) stay unassigned.
    """
    import geopandas as gpd
    prov = gpd.read_file(PROVINCES_FILE, columns=["postal"])
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(df.LONGITUDE, df.LATITUDE),
                           index=df.index, crs=4326).to_crs(prov.crs)
    j = gpd.sjoin(pts, prov, how="left", predicate="within")
    j = j[~j.index.duplicated()]
    miss = j.postal.isna()
    nn = gpd.sjoin_nearest(pts[miss], prov, how="left", max_distance=25_000)
    j.loc[miss, "postal"] = nn[~nn.index.duplicated()].postal
    return j.postal


def check_official(df: pd.DataFrame, path: Path = OFFICIAL_STATS) -> pd.DataFrame:
    """Compare yearly fires and hectares with NRCan's published NFDB summary.

    Returns only the years that differ (fires, or area by more than 1 ha).
    """
    if not Path(path).exists():
        print(f"Official summary not found ({Path(path).name}); check skipped.")
        return pd.DataFrame()
    o = pd.read_excel(path, sheet_name="CNFDB_SumStats_Src_Data", header=1)
    o = o[pd.to_numeric(o.YEAR, errors="coerce").between(FIRST_YEAR, LAST_YEAR)]
    off = o.astype({"YEAR": int}).groupby("YEAR")[["FIRES", "TOTAL_HA"]].sum()
    j = yearly(df).join(off)
    j["fires_diff"] = j.fires - j.FIRES
    j["ha_diff"] = (j.area_ha - j.TOTAL_HA).round(0)
    return j[(j.fires_diff != 0) | (j.ha_diff.abs() > 1)]


def yearly(df: pd.DataFrame) -> pd.DataFrame:
    """Fires and hectares burned per year (every year present, gaps = 0)."""
    out = df.groupby("YEAR").agg(fires=("SIZE_HA", "size"), area_ha=("SIZE_HA", "sum"))
    return out.reindex(range(FIRST_YEAR, LAST_YEAR + 1), fill_value=0)


if __name__ == "__main__":
    d = load_fires()
    y = yearly(d)
    print(f"{len(d):,} fires {d.YEAR.min()}-{d.YEAR.max()}")
    print(f"2023 area: {y.loc[2023, 'area_ha'] / 1e6:.2f} Mha")
    print(d["cause"].value_counts().to_dict())
