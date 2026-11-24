# %% [markdown]
# # 05 Website data
# Builds everything `site/index.html` loads: Plotly chart specs (`site/charts/`), map layers for the light and
# dark themes (`site/img/`), small data files (`site/data/`), plus copies of the report figures and PDF.
# Reads only from `data/clean/`, like the other notebooks, so every number matches the report.
# Run from the `notebooks/` folder: `python 05_site.py` (about a minute). Needs plotly (see requirements.txt).
#
# Charts carry no colours of their own. Each trace names a colour *role* in `meta` (for example "Lightning",
# "ember" or "--heat-2"), and the page fills in the colour from its CSS tokens, so one spec works in both themes.

# %%
import json
import shutil
from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path("..")
CLEAN = ROOT / "data" / "clean"
SITE = ROOT / "site"
for sub in ("charts", "data", "img", "figures"):
    (SITE / sub).mkdir(parents=True, exist_ok=True)

fires = pd.read_parquet(CLEAN / "fires.parquet")
provinces = gpd.read_parquet(CLEAN / "provinces.parquet")
perimeters = gpd.read_parquet(CLEAN / "perimeters.parquet")
NAMES = provinces.set_index("province")["name"].astype(str).replace(
    {"Newfoundland and Labrador": "Newfoundland & Labrador"})
CAUSES = ["Lightning", "Human", "Unknown"]
YEARS = fires["year"].nunique()                      # 67 (1959–2025)


class _Encoder(json.JSONEncoder):
    """numpy values to plain JSON; NaN to null (NaN is not valid JSON)."""
    def default(self, o):
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, np.generic):
            return o.item()
        return super().default(o)


def _nan_to_null(o):
    if isinstance(o, float) and o != o:
        return None
    if isinstance(o, list):
        return [_nan_to_null(v) for v in o]
    if isinstance(o, dict):
        return {k: _nan_to_null(v) for k, v in o.items()}
    return o


def dump(fig, name, table):
    """Write one chart spec. `table` = (header, rows) of preformatted strings for the page's data-table view."""
    spec = json.loads(json.dumps(fig.to_plotly_json(), cls=_Encoder))
    spec["layout"].pop("template", None)
    spec["layout"]["meta"] = {"table": {"head": table[0], "rows": table[1]}}
    text = json.dumps(_nan_to_null(spec), separators=(",", ":"), ensure_ascii=False)
    (SITE / "charts" / f"{name}.json").write_text(text, encoding="utf-8")
    print(f"charts/{name}.json  {len(text) / 1024:,.0f} KB")


def pct(v, dp=0):
    return f"{v:.{dp}f}%"


# %% [markdown]
# ## Q1: area burned per year (line chart with a range slider)

# %%
annual = fires.groupby("year")["size_ha"].sum() / 1e6
counts = fires.groupby("year").size()
avg10 = annual.rolling(10).mean()
prev_record = annual[annual.index < 2023].max()
print(f"2023: {annual[2023]:.1f} Mha = {annual[2023] / prev_record:.1f}x previous record "
      f"({annual[annual.index < 2023].idxmax()})")

c1 = go.Figure()
c1.add_trace(go.Scatter(x=annual.index, y=annual.round(2), mode="lines", name="Each year", meta="context",
                        hovertemplate="%{y:.2f} Mha<extra>Each year</extra>"))
c1.add_trace(go.Scatter(x=avg10.index, y=avg10.round(2), mode="lines", name="10-year average", meta="ink",
                        hovertemplate="%{y:.2f} Mha<extra>10-year average</extra>"))
hi = [2023, 2024, 2025]
c1.add_trace(go.Scatter(x=hi, y=annual[hi].round(2), mode="markers", meta="ember", showlegend=False,
                        hoverinfo="skip"))
c1.add_annotation(x=2023, y=annual[2023], text="<b>2023: 17.6 Mha</b><br>2.3× the previous record (1989)",
                  showarrow=True, ax=-110, ay=6, xanchor="right", align="right")
c1.add_annotation(x=2025, y=annual[2025], text="2024–25: two more of<br>the 7 largest years",
                  showarrow=True, ax=-90, ay=-34, xanchor="right", align="right")
for yr in (1989, 1995):
    c1.add_annotation(x=yr, y=annual[yr], text=str(yr), showarrow=False, yshift=12, font=dict(size=12))
c1.update_layout(height=470, hovermode="x unified", margin=dict(l=56, r=16, t=36, b=24),
                 yaxis=dict(title="Area burned (million ha)", rangemode="tozero", range=[0, 19.5]),
                 xaxis=dict(rangeslider=dict(visible=True, thickness=0.08), range=[1958.5, 2025.5]))
top = annual.sort_values(ascending=False).head(10)
dump(c1, "c1_annual", (["Rank", "Year", "Area burned (Mha)", "Fires"],
                       [[str(i + 1), str(y), f"{v:.2f}", f"{counts[y]:,}"] for i, (y, v) in enumerate(top.items())]))

# %% [markdown]
# ## Q1: year × month heat map (log colour scale)

# %%
MONTHS = [4, 5, 6, 7, 8, 9, 10]
MNAME = {4: "Apr", 5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct"}
dated = fires.dropna(subset=["month"])
grid = (dated.groupby(["month", "year"])["size_ha"].sum().unstack(fill_value=0)
        .reindex(index=MONTHS, columns=range(1959, 2026), fill_value=0))
z = np.log10(grid.where(grid >= 1)).round(3)
c2 = go.Figure(go.Heatmap(
    z=z.to_numpy(), x=list(grid.columns), y=[MNAME[m] for m in MONTHS], customdata=grid.round(0).to_numpy(),
    zmin=3, zmax=7, xgap=1, ygap=1, meta="heat",
    colorbar=dict(title=dict(text="ha", side="top"), tickvals=[3, 4, 5, 6, 7],
                  ticktext=["1K", "10K", "100K", "1M", "10M"], thickness=10, len=0.9),
    hovertemplate="%{y} %{x}: %{customdata:,.0f} ha<extra></extra>"))
c2.add_shape(type="rect", x0=2022.5, x1=2023.5, y0=0.5, y1=3.5, line=dict(width=2))
c2.update_layout(height=330, margin=dict(l=44, r=8, t=8, b=32),
                 yaxis=dict(autorange="reversed", showgrid=False), xaxis=dict(showgrid=False))
months_top = dated.groupby(["year", "month"])["size_ha"].sum().sort_values(ascending=False).head(10)
dump(c2, "c2_heatmap", (["Rank", "Month", "Area burned (Mha)"],
                        [[str(i + 1), f"{MNAME.get(int(m), m)} {y}", f"{v / 1e6:.2f}"]
                         for i, ((y, m), v) in enumerate(months_top.items())]))

# %% [markdown]
# ## Q2: share of fires vs share of area, by cause and province

# %%
order = fires.groupby("province")["size_ha"].sum().drop("PE").sort_values(ascending=False).index.tolist()
n_by = fires.groupby(["province", "cause"], observed=True).size().unstack(fill_value=0)
a_by = fires.groupby(["province", "cause"], observed=True)["size_ha"].sum().unstack(fill_value=0)
n_by.loc["Canada"], a_by.loc["Canada"] = n_by.sum(), a_by.sum()
rows = ["Canada"] + order
labels = ["<b>Canada</b>"] + [NAMES[p] for p in rows[1:]]
shares = [n_by.loc[rows, CAUSES].pipe(lambda t: t.div(t.sum(axis=1), axis=0) * 100),
          a_by.loc[rows, CAUSES].pipe(lambda t: t.div(t.sum(axis=1), axis=0) * 100)]

c3 = make_subplots(rows=1, cols=2, shared_yaxes=True, horizontal_spacing=0.05,
                   subplot_titles=("<b>Share of fires</b>", "<b>Share of area burned</b>"))
for col, sh in enumerate(shares, start=1):
    for cause in CAUSES:
        c3.add_trace(go.Bar(
            y=labels, x=sh[cause].round(1), orientation="h", name=cause, meta=cause, legendgroup=cause,
            showlegend=col == 1,
            text=[f"{v:.0f}%" if cause == "Lightning" and v >= 12 else "" for v in sh[cause]],
            textposition="inside", insidetextanchor="end",
            hovertemplate="%{y}<br>" + cause + ": %{x:.0f}%<extra></extra>"), row=1, col=col)
c3.update_layout(barmode="stack", bargap=0.3, height=520, margin=dict(l=8, r=30, t=84, b=28),
                 yaxis=dict(autorange="reversed", automargin=True), legend=dict(y=1.12, yanchor="bottom"))
c3.update_xaxes(range=[0, 100], tickvals=[0, 25, 50, 75, 100], ticktext=["0%", "25%", "50%", "75%", "100%"])
dump(c3, "c3_share", (["Province / territory", "Lightning: % of fires", "Lightning: % of area",
                       "Human: % of fires", "Human: % of area"],
                      [[NAMES.get(p, p), pct(shares[0].loc[p, "Lightning"]), pct(shares[1].loc[p, "Lightning"]),
                        pct(shares[0].loc[p, "Human"]), pct(shares[1].loc[p, "Human"])] for p in rows]))
print(f"Lightning: {shares[0].loc['Canada', 'Lightning']:.0f}% of fires, "
      f"{shares[1].loc['Canada', 'Lightning']:.0f}% of area")

# %% [markdown]
# ## Q2: the fire season by cause (radial chart of weekly shares)

# %%
dd = fires.dropna(subset=["doy"])
dd = dd[dd["cause"] != "Unknown"]
week = ((dd["doy"] - 1) // 7).clip(upper=51)
weekly = (dd.groupby([week, "cause"], observed=True).size().unstack(fill_value=0)
          .reindex(range(52), fill_value=0)[["Human", "Lightning"]])
weekly = weekly / weekly.sum() * 100
theta = ((np.arange(52) + 0.5) / 52 * 360).round(2)
month_deg = [round((pd.Timestamp(f"2001-{m:02d}-01").dayofyear - 1) / 365 * 360, 2) for m in range(1, 13)]
MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

c4 = go.Figure()
for cause in ["Human", "Lightning"]:
    r_ = np.append(weekly[cause].to_numpy(), weekly[cause].iloc[0]).round(2)
    c4.add_trace(go.Scatterpolar(r=r_, theta=np.append(theta, theta[0]), mode="lines", name=cause, meta=cause,
                                 hovertemplate="Week %{customdata}: %{r:.1f}% of " + cause.lower()
                                 + " fires<extra></extra>",
                                 customdata=list(range(1, 53)) + [1]))
c4.update_layout(height=520, margin=dict(l=40, r=40, t=40, b=30), polar=dict(
    angularaxis=dict(rotation=90, direction="clockwise", tickvals=month_deg, ticktext=MONTH_ABBR),
    radialaxis=dict(range=[0, 11.5], tickvals=[2, 4, 6, 8, 10], ticktext=["2%", "4%", "6%", "8%", "10%"],
                    angle=100)))
mon = dd.groupby(["month", "cause"], observed=True).size().unstack(fill_value=0)[["Human", "Lightning"]]
mon = mon / mon.sum() * 100
human_spring = mon.loc[[4, 5], "Human"].sum()
light_summer = mon.loc[[6, 7, 8], "Lightning"].sum()
print(f"Human Apr–May {human_spring:.0f}%, lightning Jun–Aug {light_summer:.0f}%")
dump(c4, "c4_radial", (["Month", "Human: % of its fires", "Lightning: % of its fires"],
                       [[MONTH_ABBR[int(m) - 1], pct(r["Human"], 1), pct(r["Lightning"], 1)]
                        for m, r in mon.iterrows()]))

# %% [markdown]
# ## Q2: treemap and sunburst of area burned by large fires (province and cause)
# The same breakdown in two orders: the treemap groups by province first, the sunburst by cause first.

# %%
big = fires[fires["is_large"]]
pc = big.groupby(["province", "cause"], observed=True)["size_ha"].sum().div(1e6).round(3)
pc = pc[pc > 0]
prov_tot = pc.groupby(level=0).sum().sort_values(ascending=False)
cause_tot = pc.groupby(level=1).sum().reindex(CAUSES).dropna()


def hier(first_level):
    ids, lab, par, val, role = [], [], [], [], []
    if first_level == "province":
        for p, tot in prov_tot.items():
            ids.append(p); lab.append(NAMES[p]); par.append(""); val.append(round(tot, 3)); role.append("muted")
            for c in CAUSES:
                if (p, c) in pc.index:
                    ids.append(f"{p}/{c}"); lab.append(c); par.append(p); val.append(pc[(p, c)]); role.append(c)
    else:
        for c, tot in cause_tot.items():
            ids.append(c); lab.append(c); par.append(""); val.append(round(tot, 3)); role.append(c)
            for p in prov_tot.index:
                if (p, c) in pc.index:
                    ids.append(f"{c}/{p}"); lab.append(NAMES[p]); par.append(c); val.append(pc[(p, c)])
                    role.append(c)
    return dict(ids=ids, labels=lab, parents=par, values=val, meta=role, branchvalues="total",
                hovertemplate="<b>%{label}</b><br>%{value:.2f} million ha<br>%{percentRoot:.1%} of all"
                              "<extra></extra>")


tm_table = (["Province / territory", "Lightning (Mha)", "Human (Mha)", "Unknown (Mha)", "Total (Mha)"],
            [[NAMES[p]] + [f"{pc.get((p, c), 0):.2f}" for c in CAUSES] + [f"{prov_tot[p]:.2f}"]
             for p in prov_tot.index])
c5t = go.Figure(go.Treemap(**hier("province"), texttemplate="%{label}<br>%{value:.1f} Mha", tiling=dict(pad=2)))
c5t.update_layout(height=540, margin=dict(l=4, r=4, t=8, b=4))
dump(c5t, "c5_treemap", tm_table)
c5s = go.Figure(go.Sunburst(**hier("cause"), texttemplate="%{label}<br>%{value:.1f} Mha", insidetextorientation="radial"))
c5s.update_layout(height=560, margin=dict(l=4, r=4, t=8, b=4))
dump(c5s, "c5_sunburst", tm_table)

# %% [markdown]
# ## Q3: fire size distribution (count vs area) and the concentration curve

# %%
sized = fires.loc[fires["has_size"], "size_ha"]
edges = np.arange(-2, 6.5, 0.5)
fires_pct = np.histogram(np.log10(sized), bins=edges)[0] / len(sized) * 100
area_pct = np.histogram(np.log10(sized), bins=edges, weights=sized)[0] / sized.sum() * 100
centres = edges[:-1] + 0.25


def ha_label(v):
    return f"{v:,.0f}" if v >= 1 else f"{v:g}"


bands = [f"{ha_label(10 ** a)}–{ha_label(10 ** b)} ha" for a, b in zip(edges[:-1], edges[1:])]
c6 = go.Figure()
c6.add_trace(go.Bar(x=centres, y=fires_pct.round(2), name="Share of fires", meta="neutral", customdata=bands,
                    hovertemplate="%{customdata}<br>%{y:.1f}% of fires<extra></extra>"))
c6.add_trace(go.Bar(x=centres, y=area_pct.round(2), name="Share of area burned", meta="ember", customdata=bands,
                    hovertemplate="%{customdata}<br>%{y:.1f}% of area<extra></extra>"))
c6.add_annotation(x=0.1, y=24, text="Most fires are<br>under 1 ha", showarrow=False, xanchor="left")
c6.add_annotation(x=4.5, y=31, text="Most area comes from<br>fires over 10,000 ha", showarrow=False)
c6.update_layout(barmode="group", bargap=0.12, height=420, margin=dict(l=52, r=12, t=36, b=48),
                 xaxis=dict(title="Fire size (ha, log scale)", tickvals=list(range(-2, 7)),
                            ticktext=["0.01", "0.1", "1", "10", "100", "1K", "10K", "100K", "1M"]),
                 yaxis=dict(ticksuffix="%"))
dump(c6, "c6_sizes", (["Size band", "% of fires", "% of area burned"],
                      [[b, pct(f, 1), pct(a, 1)] for b, f, a in zip(bands, fires_pct, area_pct) if f or a]))

desc = np.sort(sized.to_numpy())[::-1]
cum = desc.cumsum() / desc.sum() * 100
top_pct = np.arange(1, len(desc) + 1) / len(desc) * 100
half = int(np.searchsorted(cum, 50))
one = int(0.01 * len(desc)) - 1
pick = np.unique(np.geomspace(1, len(desc), 500).astype(int) - 1)
print(f"Half of the area: {half + 1:,} of {len(desc):,} sized fires ({top_pct[half]:.2f}%); "
      f"top 1% = {cum[one]:.1f}%")
c7 = go.Figure()
c7.add_trace(go.Scatter(x=top_pct[pick].round(5), y=cum[pick].round(2), mode="lines", meta="ember",
                        name="Cumulative share", hovertemplate="Largest %{x:.3g}% of fires: "
                        "%{y:.1f}% of area<extra></extra>"))
c7.add_trace(go.Scatter(x=[top_pct[half], top_pct[one]], y=[cum[half], cum[one]], mode="markers", meta="ember",
                        showlegend=False, hoverinfo="skip"))
c7.add_annotation(x=np.log10(top_pct[half]), y=cum[half], text=f"<b>{half + 1:,} fires (0.2%)</b><br>= half of all area",
                  ax=70, ay=30, xanchor="left", align="left")
c7.add_annotation(x=np.log10(top_pct[one]), y=cum[one], text="<b>Largest 1%</b><br>= 83% of area",
                  ax=60, ay=34, xanchor="left", align="left")
c7.update_layout(height=420, showlegend=False, margin=dict(l=56, r=16, t=16, b=48),
                 xaxis=dict(type="log", range=[-3, 2.02], title="Largest fires, as % of all fires (log scale)",
                            tickvals=[0.001, 0.01, 0.1, 1, 10, 100],
                            ticktext=["0.001%", "0.01%", "0.1%", "1%", "10%", "100%"]),
                 yaxis=dict(range=[0, 102], ticksuffix="%", title="Cumulative share of area"))
marks = [0.01, 0.1, 0.2, 1, 5, 10]
dump(c7, "c7_concentration", (["Largest fires (% of all)", "Number of fires", "Share of area burned"],
                              [[f"{m:g}%", f"{int(m / 100 * len(desc)):,}",
                                pct(cum[max(int(m / 100 * len(desc)) - 1, 0)], 1)] for m in marks]))

# %% [markdown]
# ## Q3: size of large fires by decade (box plots, 10th–90th percentile whiskers)

# %%
DECS = ["1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
large = fires[fires["is_large"] & fires["decade"].isin(DECS)]
q = large.groupby("decade", observed=True)["size_ha"].quantile([0.1, 0.25, 0.5, 0.75, 0.9]).unstack().reindex(DECS)
n_dec = large.groupby("decade", observed=True).size().reindex(DECS)
over10k = large.assign(o=large["size_ha"] >= 10_000).groupby("decade", observed=True)["o"].mean().reindex(DECS) * 100
c8 = go.Figure(go.Box(x=DECS, q1=q[0.25].round(0), median=q[0.5].round(0), q3=q[0.75].round(0),
                      lowerfence=q[0.1].round(0), upperfence=q[0.9].round(0), meta="ember", name="Large fires",
                      hoverinfo="y"))
for d in DECS:
    c8.add_annotation(x=d, y=np.log10(q.loc[d, 0.5]), text=f"{q.loc[d, 0.5]:,.0f}", showarrow=False,
                      xshift=52, font=dict(size=12))
    c8.add_annotation(x=d, y=1.0, yref="paper", text=f"{over10k[d]:.0f}%", showarrow=False, yanchor="bottom",
                      font=dict(size=12))
c8.add_annotation(x=0, xref="paper", y=1.0, yref="paper", text="Over 10,000 ha:", showarrow=False, xanchor="right",
                  yanchor="bottom", xshift=-6, font=dict(size=12))
c8.update_layout(height=400, showlegend=False, margin=dict(l=110, r=16, t=30, b=32),
                 yaxis=dict(type="log", range=[np.log10(200), np.log10(60000)], title="Fire size (ha, log scale)",
                            tickvals=[300, 1000, 3000, 10000, 30000], ticktext=["300", "1,000", "3,000", "10,000",
                                                                              "30,000"]))
dump(c8, "c8_decades", (["Decade", "Large fires", "10th pct (ha)", "Median (ha)", "90th pct (ha)", "Over 10,000 ha"],
                        [[d, f"{n_dec[d]:,}", f"{q.loc[d, 0.1]:,.0f}", f"{q.loc[d, 0.5]:,.0f}",
                          f"{q.loc[d, 0.9]:,.0f}", pct(over10k[d])] for d in DECS]))

# %% [markdown]
# ## Q4: choropleth of hectares burned per 1,000 km² per year (hover for each province)

# %%
rate = (fires.groupby("province")["size_ha"].sum() / provinces.set_index("province")["land_km2"] * 1000 / YEARS)
share_nat = fires.groupby("province")["size_ha"].sum() / fires["size_ha"].sum() * 100
CLASSES = [0, 10, 50, 150, 300, 500, 800]
CLASS_LABELS = ["Under 10", "10–50", "50–150", "150–300", "300–500", "500–800"]
shapes = provinces.copy()
shapes["geometry"] = shapes.geometry.simplify(4000)
shapes["cls"] = pd.cut(shapes["province"].map(rate), CLASSES, labels=False, include_lowest=True).astype(int)


def rings(geom):
    xs, ys = [], []
    for part in (geom.geoms if geom.geom_type == "MultiPolygon" else [geom]):
        if part.area < 2e8:                           # drop specks under 200 km² to keep the file small
            continue
        x, y = part.exterior.xy
        xs += [round(v / 1000) for v in x] + [None]   # kilometres, integers
        ys += [round(v / 1000) for v in y] + [None]
    return xs, ys


c9 = go.Figure()
seen = set()
for _, row in shapes.sort_values("cls").iterrows():
    xs, ys = rings(row.geometry)
    k = int(row["cls"])
    p = row["province"]
    c9.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines", fill="toself", meta=f"--rate-{k}", hoveron="fills",
        name=CLASS_LABELS[k], legendgroup=CLASS_LABELS[k], showlegend=k not in seen,
        text=f"<b>{NAMES[p]}</b><br>{rate[p]:,.0f} ha per 1,000 km² per year<br>{share_nat[p]:.1f}% of Canada's area burned",
        hoverinfo="text"))
    seen.add(k)
NUDGE = {"NU": (0, -350), "NT": (0, -120), "QC": (0, -180), "ON": (0, -260), "BC": (0, -100),
         "NS": (260, -220), "NB": (-60, -330), "PE": (230, 150), "NL": (60, 120)}
for _, row in shapes.iterrows():
    p = row["province"]
    pt = row.geometry.representative_point()
    dx, dy = NUDGE.get(p, (0, 0))
    val = f"{rate[p]:,.0f}" if rate[p] >= 1 else "<1"
    c9.add_annotation(x=pt.x / 1000 + dx, y=pt.y / 1000 + dy, text=f"<b>{p}</b><br>{val}", showarrow=False,
                      font=dict(size=11), bgcolor="#ffffff", opacity=0.92, borderpad=2)   # page re-themes it
c9.update_layout(height=560, margin=dict(l=0, r=0, t=8, b=0), legend=dict(title=dict(text="ha per 1,000 km²/yr")),
                 xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
dump(c9, "c9_choropleth", (["Province / territory", "Area burned (Mha)", "Land (1,000 km²)",
                            "ha per 1,000 km² per year", "% of Canada's area burned"],
                           [[NAMES[p], f"{fires.loc[fires.province == p, 'size_ha'].sum() / 1e6:.2f}",
                             f"{provinces.set_index('province').loc[p, 'land_km2'] / 1000:,.0f}",
                             f"{rate[p]:,.1f}", pct(share_nat[p], 1)] for p in rate.sort_values(ascending=False).index]))

# %% [markdown]
# ## Q4: map layers for the decade scrubber, the hero map and the small multiples
# One transparent PNG per decade and theme, stacked in the page and switched with CSS, so the map changes
# instantly without loading a heavy vector file. Colours follow the page's decade ramp.

# %%
DECADES = ["1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
RAMP = {"light": ["#f69c73", "#f3714d", "#e83f3f", "#ca1a50", "#a11a5b", "#751f58"],
        "dark": ["#721a6e", "#a62d60", "#d44842", "#f3761b", "#fcb014", "#f1ef75"]}
LAND = {"light": dict(land="#E6E1D9", edge="#FFFFFF"), "dark": dict(land="#2A2622", edge="#16130F")}
x0, y0, x1, y1 = provinces.total_bounds
XL = (x0 + 0.02 * (x1 - x0), x1 - 0.03 * (x1 - x0))
YL = (y0, y0 + 0.78 * (y1 - y0))
W_IN = 8.0
H_IN = W_IN * (YL[1] - YL[0]) / (XL[1] - XL[0])


def layer(name, draw):
    fig = plt.figure(figsize=(W_IN, H_IN))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(*XL)
    ax.set_ylim(*YL)
    ax.set_aspect("equal")
    ax.set_axis_off()
    draw(ax)
    fig.savefig(SITE / "img" / f"{name}.png", dpi=200, transparent=True)
    plt.close(fig)


for theme, c in LAND.items():
    layer(f"land_{theme}", lambda ax, c=c: provinces.plot(ax=ax, color=c["land"], edgecolor=c["edge"], linewidth=0.6))
    for d, colour in zip(DECADES, RAMP[theme]):
        layer(f"scars_{d[:4]}_{theme}", lambda ax, d=d, colour=colour:
              perimeters[perimeters["decade"] == d].plot(ax=ax, color=colour, linewidth=0))
print("map layers written")

span_years = perimeters.groupby("decade")["year"].nunique()
dec_mha = perimeters.groupby("decade")["size_ha"].sum() / 1e6
bc = (perimeters.groupby(["decade", "agency"])["size_ha"].sum().unstack(fill_value=0)
      .pipe(lambda t: t["BC"] / t.sum(axis=1) * 100))
meta = dict(aspect=H_IN / W_IN, colors=RAMP, decades=[dict(
    key=d[:4], label={"1970s": "1972–79", "2020s": "2020–24"}.get(d, d), mha=round(dec_mha[d], 1),
    mha_yr=round(dec_mha[d] / span_years[d], 2), bc=round(bc[d], 0)) for d in DECADES])
(SITE / "data" / "map_meta.json").write_text(json.dumps(meta), encoding="utf-8")
(SITE / "data" / "summary.json").write_text(json.dumps(dict(
    years=annual.index.tolist(), mha=annual.round(3).tolist())), encoding="utf-8")
for d in meta["decades"]:
    print(d)

# %% [markdown]
# ## Copies of the printed report figures and the report itself

# %%
for png in (ROOT / "figures").glob("fig*.png"):
    shutil.copy2(png, SITE / "figures" / png.name)
if (ROOT / "report" / "main.pdf").exists():
    shutil.copy2(ROOT / "report" / "main.pdf", SITE / "report.pdf")
print("done")
