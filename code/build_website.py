"""Export everything the companion website needs into website/.

- charts/*.json : Plotly Express figures (L19) as {data, layout} specs. Colours
                  are applied in the page from theme tokens via trace.meta roles.
- data/summary.json : small numbers for the waffle, hero and callouts.
- img/*.png     : transparent, pixel-aligned map layers (land per theme, burn
                  scars per decade per theme, ignition dots per cause per theme).

Run:  python code/build_website.py            (everything)
      python code/build_website.py --charts-only  (skip the slow map layers)
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from scipy import stats

import fire_data as fd
import figures as F

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "website"
for sub in ("charts", "data", "img"):
    (WEB / sub).mkdir(parents=True, exist_ok=True)


def dump(fig, name):
    def clean(o):                            # NaN is not valid JSON: write gaps as null
        if isinstance(o, float) and o != o:
            return None
        if isinstance(o, list):
            return [clean(v) for v in o]
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        return o
    spec = clean(json.loads(fig.to_json()))
    spec["layout"].pop("template", None)
    (WEB / "charts" / f"{name}.json").write_text(json.dumps(spec, separators=(",", ":")))


def r(x, n=1):
    return float(round(float(x), n))


# --------------------------------------------------------------------------
df = fd.load_fires()
y = fd.yearly(df)
roll = y.rolling(10, min_periods=10).mean()

# ---- c1: trend (two stacked panels, shared x) ----------------------------
c1 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_heights=[0.62, 0.38])
c1.add_trace(go.Scatter(x=y.index, y=y.area_ha / 1e6, mode="lines", name="Area burned (Mha)",
                        meta="context", hovertemplate="%{x}: %{y:.2f} Mha<extra></extra>"), 1, 1)
c1.add_trace(go.Scatter(x=roll.index, y=roll.area_ha / 1e6, mode="lines", name="Area, 10-yr average",
                        meta="Lightning", hovertemplate="%{x} 10-yr avg: %{y:.2f} Mha<extra></extra>"), 1, 1)
c1.add_trace(go.Scatter(x=y.index, y=y.fires, mode="lines", name="Fires", meta="context",
                        hovertemplate="%{x}: %{y:,} fires<extra></extra>"), 2, 1)
c1.add_trace(go.Scatter(x=roll.index, y=roll.fires, mode="lines", name="Fires, 10-yr average", meta="Human",
                        hovertemplate="%{x} 10-yr avg: %{y:,.0f} fires<extra></extra>"), 2, 1)
c1.add_trace(go.Scatter(x=[2023], y=[y.loc[2023, "area_ha"] / 1e6], mode="markers+text", meta="ember",
                        text=["2023 · 17.6 Mha"], textposition="middle left", name="2023",
                        hovertemplate="2023: %{y:.1f} Mha, 2.0x the next-worst year<extra></extra>"), 1, 1)
c1.add_trace(go.Scatter(x=[2025], y=[y.loc[2025, "area_ha"] / 1e6], mode="markers+text", meta="ink",
                        text=["2025 · 8.7 Mha"], textposition="top left", name="2025",
                        hovertemplate="2025: %{y:.1f} Mha, 2nd-largest year<extra></extra>"), 1, 1)
c1.add_vrect(x0=1949.5, x1=1979.5, line_width=0, layer="below", fillcolor="rgba(128,120,110,0.10)")
c1.update_yaxes(title_text="Area burned (Mha)", row=1, col=1, rangemode="tozero")
c1.update_yaxes(title_text="Fires reported", row=2, col=1, rangemode="tozero")
c1.update_xaxes(showgrid=False)
c1.update_layout(showlegend=False, height=460, hovermode="x unified")
dump(c1, "c1_trend")

# ---- c2: heatmap year x month (sqrt colour, true values in hover) -----------
months = list(range(3, 11))
mnames = ["Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"]
grid = (df[df.MONTH > 0].pivot_table(index="MONTH", columns="YEAR", values="SIZE_HA", aggfunc="sum")
        .reindex(index=months, columns=range(1950, 2026)).fillna(0))
c2 = px.imshow(np.sqrt(grid.to_numpy()), x=list(grid.columns), y=mnames, aspect="auto",
               color_continuous_scale="Inferno_r" if False else "YlOrRd")
c2.data[0].update(customdata=grid.to_numpy() / 1e6, meta="heat",
                  hovertemplate="%{y} %{x}: %{customdata:.2f} Mha<extra></extra>", xgap=1, ygap=1)
ticks = [0, 0.1e6, 0.5e6, 1e6, 2e6, 4e6, 6e6]
c2.update_layout(height=330, coloraxis_colorbar=dict(
    title="Mha", tickvals=[np.sqrt(t) for t in ticks], ticktext=["0", "0.1", "0.5", "1", "2", "4", "6"],
    thickness=10, len=0.9))
dump(c2, "c2_heatmap")

# ---- c3: treemap 2023 -------------------------------------------------------
t23 = (df[df.YEAR == 2023].groupby("province", observed=True).SIZE_HA.sum()
       .sort_values(ascending=False).reset_index())
t23 = t23[t23.SIZE_HA > 1000]
t23["province"] = t23.province.astype(str)
t23["Mha"] = t23.SIZE_HA / 1e6
t23["role"] = np.where(t23.SIZE_HA >= 1.5e6, "ember", "muted")
c3 = px.treemap(t23, path=["province"], values="Mha")
c3.data[0].update(meta=list(t23.set_index("province").loc[c3.data[0].labels, "role"]),
                  texttemplate="<b>%{label}</b><br>%{value:.1f} Mha · %{percentRoot:.0%}",
                  hovertemplate="%{label}: %{value:.2f} Mha (%{percentRoot:.1%} of 2023)<extra></extra>",
                  tiling=dict(pad=2))
c3.update_layout(height=360, uniformtext=dict(minsize=10, mode="hide"))
dump(c3, "c3_treemap")

# ---- c5: radar --------------------------------------------------------------
dated = df[df.MONTH > 0]
share = pd.crosstab(dated.MONTH, dated.cause, normalize="columns").reindex(range(1, 13)).fillna(0)
mlong = (share[["Lightning", "Human"]] * 100).reset_index().melt(id_vars="MONTH", var_name="cause",
                                                                     value_name="pct")
mlong["month"] = mlong.MONTH.map(dict(zip(range(1, 13), ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                                          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])))
c5 = px.line_polar(mlong, r="pct", theta="month", color="cause", line_close=True)
for tr in c5.data:
    tr.update(meta=tr.name, mode="lines+markers", hovertemplate=tr.name + ", %{theta}: %{r:.1f}% of its fires<extra></extra>")
c5.update_layout(height=420, legend_title_text="", polar=dict(angularaxis=dict(direction="clockwise", rotation=90),
                                        radialaxis=dict(ticksuffix="%", angle=90, tickangle=90, dtick=10)))
dump(c5, "c5_radar")

# ---- c6: region x cause stacked bars ----------------------------------------
pv = (df.pivot_table(index="province", columns="cause", values="SIZE_HA", aggfunc="sum", observed=True)
      .reindex(columns=fd.CAUSE_ORDER).fillna(0) / 1e6)
pv = pv[pv.sum(axis=1) > 0.001]
pv = pv.loc[pv.sum(axis=1).sort_values().index]
pv.index = pv.index.astype(str)
blong = pv.reset_index().melt(id_vars="province", var_name="cause", value_name="Mha")
c6 = px.bar(blong, y="province", x="Mha", color="cause", orientation="h",
            category_orders={"cause": fd.CAUSE_ORDER, "province": list(pv.index[::-1])})
for tr in c6.data:
    tr.update(meta=tr.name, hovertemplate="%{y} · " + tr.name + ": %{x:.2f} Mha<extra></extra>")
c6.update_yaxes(automargin=True)
c6.update_layout(height=460, barmode="stack", legend_title_text="", xaxis_title="Area burned 1950–2025 (Mha)",
                 yaxis_title="", margin=dict(l=150, r=16, t=40, b=48))
dump(c6, "c6_bars")

# ---- c7: mirrored histogram -------------------------------------------------
edges = 200.0 * 10.0 ** (np.arange(-18, 18) / 4)
s = df.loc[df.SIZE_HA > 0, "SIZE_HA"]
cut = pd.cut(s, edges, right=False)
g = s.groupby(cut, observed=False).agg(["size", "sum"])
mid = np.log10(np.sqrt(edges[:-1] * edges[1:]))   # plot on log10 values: equal-width bars
big = edges[:-1] >= 199.9
c7 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04)
lab = [f"{a:,.2g}–{b:,.2g} ha" for a, b in zip(edges[:-1], edges[1:])]
c7.add_trace(go.Bar(x=mid, width=0.22, y=g["size"] / g["size"].sum() * 100, meta=["ember" if b else "neutral" for b in big],
                    customdata=lab, hovertemplate="%{customdata}: %{y:.2f}% of fires<extra></extra>"), 1, 1)
c7.add_trace(go.Bar(x=mid, width=0.22, y=-(g["sum"] / g["sum"].sum() * 100), meta=["ember" if b else "neutral" for b in big],
                    customdata=np.c_[lab, (g["sum"] / g["sum"].sum() * 100).round(2)],
                    hovertemplate="%{customdata[0]}: %{customdata[1]}% of area<extra></extra>"), 2, 1)
c7.update_xaxes(tickvals=[-2, 0, 2, 4, 6], ticktext=["0.01 ha", "1 ha", "100 ha", "10,000 ha", "1M ha"], showgrid=False)
c7.update_yaxes(title_text="% of fires", row=1, col=1)
c7.update_yaxes(title_text="% of area", row=2, col=1, tickvals=[0, -4, -8, -12], ticktext=["0", "4", "8", "12"])
c7.update_layout(height=440, showlegend=False, bargap=0.08)
dump(c7, "c7_hist")

# ---- c8: yearly median size of escaped fires (the series the trend test uses) --
d8 = df[(df.SIZE_HA >= 1) & df.cause.isin(["Lightning", "Human"]) & (df.YEAR >= 1980)]
ym = d8.groupby(["YEAR", "cause"], observed=True).SIZE_HA.median().unstack()
rho = {c: stats.spearmanr(ym.index, ym[c]) for c in ("Lightning", "Human")}
c8 = go.Figure()
for cause in ["Lightning", "Human"]:
    c8.add_trace(go.Scatter(x=ym.index, y=ym[cause], mode="lines+markers", name=cause, meta=cause,
                            hovertemplate=cause + " %{x}: median %{y:.1f} ha<extra></extra>"))
c8.update_layout(height=400, legend_title_text="", xaxis=dict(showgrid=False),
                 yaxis=dict(type="log", title="Median fire size, ha (log)",
                            tickvals=[1, 3, 10, 30, 100, 300], ticktext=["1", "3", "10", "30", "100", "300"]))
dump(c8, "c8_medians")

# ---- summary numbers ---------------------------------------------------------
counts = df.cause.value_counts().reindex(fd.CAUSE_ORDER)
area = df.groupby("cause", observed=True).SIZE_HA.sum().reindex(fd.CAUSE_ORDER)
summary = dict(
    n_fires=int(len(df)), years=[int(df.YEAR.min()), int(df.YEAR.max())],
    record_mha=r(y.area_ha.max() / 1e6), ratio=r(y.area_ha.max() / y.area_ha.drop(2023).max()),
    waffle_fires=dict(zip(fd.CAUSE_ORDER, map(int, F._largest_remainder(counts)))),
    waffle_area=dict(zip(fd.CAUSE_ORDER, map(int, F._largest_remainder(area)))),
    fires_raw=dict(zip(fd.CAUSE_ORDER, map(int, counts))),
    area_mha_raw=dict(zip(fd.CAUSE_ORDER, [r(v / 1e6) for v in area])),
    share_fires_ge200=r((df.loc[df.SIZE_HA > 0, "SIZE_HA"] >= 200).mean() * 100),
    share_area_ge200=r(df.loc[df.SIZE_HA >= 200, "SIZE_HA"].sum() / df.SIZE_HA.sum() * 100),
    top_years=[dict(year=int(k), mha=r(v / 1e6, 2), fires=int(y.loc[k, "fires"]))
               for k, v in y.area_ha.sort_values(ascending=False).head(10).items()],
    rho=dict(lightning=r(rho["Lightning"][0], 2), human=r(rho["Human"][0], 2),
             p_human=r(rho["Human"][1], 2)),
)
(WEB / "data" / "summary.json").write_text(json.dumps(summary, indent=1))

# ---- map layers ------------------------------------------------------------
import sys
if "--charts-only" in sys.argv:
    print("charts and summary written (map layers skipped)")
    raise SystemExit(0)
import seaborn as sns
from pyproj import Transformer
import style as st
st.apply()

prov, scars = F._load_geo()
x0, y0, x1, y1 = prov.total_bounds
XL = (x0 + 0.02 * (x1 - x0), x1 - 0.04 * (x1 - x0))
YL = (y0, y0 + 0.75 * (y1 - y0))
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
    fig.savefig(WEB / "img" / f"{name}.png", dpi=200, transparent=True)
    plt.close(fig)


THEMES = {"light": dict(land="#E6E1D9", edge="#FFFFFF"), "dark": dict(land="#2A2622", edge="#16130F")}
for t, c in THEMES.items():
    layer(f"land_{t}", lambda ax, c=c: prov.plot(ax=ax, color=c["land"], edgecolor=c["edge"], linewidth=0.5))

scars["dec"] = (scars.YEAR // 10) * 10
ramps = {"light": sns.color_palette("rocket_r", 9)[1:7],
         "dark": [plt.get_cmap("inferno")(v) for v in np.linspace(0.32, 0.95, 6)]}
for t, ramp in ramps.items():
    for dec, col in zip([1970, 1980, 1990, 2000, 2010, 2020], ramp):
        layer(f"scars_{dec}_{t}", lambda ax, dec=dec, col=col: scars[scars.dec == dec].plot(
            ax=ax, color=col, linewidth=0))

tr = Transformer.from_crs(4326, prov.crs, always_xy=True)
px_, py_ = tr.transform(df.LONGITUDE.to_numpy(), df.LATITUDE.to_numpy())
dots = {"light": {"Lightning": "#C77700", "Human": "#1F5A99"},
        "dark": {"Lightning": "#C98226", "Human": "#4F8FD4"}}   # validated dark tokens
for t, cols in dots.items():
    for cause, col in cols.items():
        m = (df.cause == cause).to_numpy()
        layer(f"dots_{cause.lower()}_{t}", lambda ax, m=m, col=col: ax.scatter(
            px_[m], py_[m], s=0.2, color=col, alpha=0.28, linewidths=0, rasterized=True))

cen = F.scar_centres(scars)
centres = [dict(dec=int(d), x=r((row.x - XL[0]) / (XL[1] - XL[0]), 4),
                y=r(1 - (row.y - YL[0]) / (YL[1] - YL[0]), 4), mha_yr=r(row.mha_per_year, 2))
           for d, row in cen.iterrows()]

# per-area choropleth (hectares per 1,000 km2 per year, 1980-2025)
code = {v: k for k, v in fd.PROV_SHORT.items()}
rec = df[df.YEAR >= fd.FULL_REPORTING_FROM]
ha = rec.groupby("province", observed=True).SIZE_HA.sum().rename(index=code)
pr = prov.set_index("postal")
pr["rate"] = (ha.reindex(pr.index).fillna(0) / (fd.LAST_YEAR - fd.FULL_REPORTING_FROM + 1)) / (pr.geometry.area / 1e9)
BINS = [0, 50, 200, 400, 600, 1000]
rate_ramps = {"light": ["#F6EDE3"] + [matplotlib.colors.to_hex(c) for c in sns.color_palette("rocket_r", 8)[1:5]],
              "dark": ["#2E2621"] + [matplotlib.colors.to_hex(plt.get_cmap("inferno")(v)) for v in (0.35, 0.5, 0.65, 0.85)]}
NUDGE = {"NU": (0, -6e5), "NT": (0, -2e5), "QC": (0, 2.5e5), "ON": (0, 2e5),
         "NS": (3.2e5, -1.4e5), "NB": (-1.5e5, 1.6e5), "PE": (2.4e5, 1.7e5)}
for t, cols in rate_ramps.items():
    def draw(ax, cols=cols, t=t):
        k = np.clip(np.digitize(pr.rate, BINS) - 1, 0, len(cols) - 1)
        pr.plot(ax=ax, color=[cols[i] for i in k], edgecolor=THEMES[t]["edge"], linewidth=0.8)
        for (c, row), i in zip(pr.iterrows(), k):
            pt = row.geometry.representative_point(); dx, dy = NUDGE.get(c, (0, 0))
            light_txt = (i >= 3) if t == "light" else (i <= 1)
            ax.text(pt.x + dx, pt.y + dy, f"{c}\n{row.rate:,.0f}", ha="center", va="center",
                    fontsize=9 if c not in ("PE", "NS", "NB") else 7.5, fontweight="bold",
                    color="#FFFFFF" if light_txt else "#1F1B17", linespacing=1.1, family="Inter")
    layer(f"rate_{t}", draw)

ramp_hex = {t: [matplotlib.colors.to_hex(c) for c in v] for t, v in ramps.items()}
(WEB / "data" / "map_meta.json").write_text(json.dumps(dict(
    aspect=H_IN / W_IN, decade_colors=ramp_hex, centres=centres, rate_bins=BINS,
    rate_colors=rate_ramps, rate=pr.rate.round(0).to_dict(),
    decade_mha=(scars.groupby("dec").SIZE_HA.sum() / 1e6).round(1).to_dict())))
print("website assets written to", WEB)
