# %% [markdown]
# # 04 Interactive figures for the website
# Reads only from `data/clean/`. Writes standalone HTML files to `site/interactive/`.
# Run from the `notebooks/` folder (same as the other notebooks). In VS Code each `# %%` block is a cell.
# Needs: pip install plotly folium (geopandas, pandas, pyarrow are already in requirements.txt)

# %%
import json
from pathlib import Path

import folium
import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.graph_objects as go

import style

CLEAN = Path("../data/clean")
OUT = Path("../site/interactive")
OUT.mkdir(parents=True, exist_ok=True)
for old_file in OUT.glob("*.html"):      # remove stale output so an old file can't be mistaken for a new one
    old_file.unlink()
print("04_interactive v2: Fig 7 drawn as shapes, Fig 8 without Carto tiles")

LAYOUT = dict(
    font=dict(family="Public Sans, system-ui, sans-serif", size=13, color=style.SECONDARY),
    paper_bgcolor="white",
    plot_bgcolor="white",
    margin=dict(l=60, r=20, t=50, b=50),
    hoverlabel=dict(font_size=13),
)


def export(fig, name):
    # include_plotlyjs="cdn" keeps each file small; the page needs internet to load Plotly
    fig.write_html(OUT / f"{name}.html", include_plotlyjs="cdn", full_html=True,
                   config={"displaylogo": False})
    print("wrote", OUT / f"{name}.html")


# %% [markdown]
# ## Fig 1: annual area burned (hover + year-range slider)

# %%
tot = pd.read_csv(CLEAN / "annual_totals.csv")
tot["mha"] = tot["large_area_ha"] / 1e6          # large fires only, as in the static Fig 1
tot["avg10"] = tot["mha"].rolling(10).mean()
peak = tot.loc[tot["mha"].idxmax()]
prev = tot[tot["year"] < peak["year"]]["mha"].max()      # previous record before the peak year

fig1 = go.Figure()
fig1.add_trace(go.Scatter(
    x=tot["year"], y=tot["mha"], mode="lines", name="Each year",
    line=dict(color=style.NEUTRAL, width=1.6),
    hovertemplate="%{y:.2f} million ha<extra>Each year</extra>"))
fig1.add_trace(go.Scatter(
    x=tot["year"], y=tot["avg10"], mode="lines", name="10-year average",
    line=dict(color=style.INK, width=3.5),
    hovertemplate="%{y:.2f} million ha<extra>10-year average</extra>"))
fig1.add_trace(go.Scatter(
    x=[int(peak["year"])], y=[float(peak["mha"])], mode="markers",
    marker=dict(color=style.ACCENT, size=11), showlegend=False, hoverinfo="skip"))
fig1.add_annotation(
    x=int(peak["year"]), y=float(peak["mha"]), xanchor="right", ax=-60, ay=0,
    text=f"{int(peak['year'])}: {peak['mha']:.1f} Mha, {peak['mha'] / prev:.1f}× the previous record",
    showarrow=True, arrowcolor=style.SECONDARY, arrowwidth=1,
    font=dict(size=13, color=style.INK))
fig1.update_layout(
    **{**LAYOUT, "margin": dict(l=60, r=20, t=50, b=50)},      # no in-chart title: the page caption carries it
    yaxis=dict(title="Area burned (million ha)", gridcolor=style.GRID, zeroline=False,
               rangemode="tozero"),
    xaxis=dict(rangeslider=dict(visible=True, thickness=0.07), showgrid=False),
    legend=dict(orientation="h", x=0, y=1.02, yanchor="bottom"),
    hovermode="x unified",
    height=520,
)
export(fig1, "fig1_annual_area")

# %% [markdown]
# ## Fig 2: year-by-month heat map (hover shows exact hectares)

# %%
fires = pd.read_parquet(CLEAN / "fires.parquet",
                        columns=["year", "month", "size_ha", "is_large", "province"])
big = fires[fires["is_large"] & fires["month"].notna()].copy()
big["month"] = big["month"].astype(int)

pt = (big.groupby(["month", "year"])["size_ha"].sum().unstack("year")
         .reindex(index=range(4, 11), columns=range(1959, 2026)))
month_names = {4: "Apr", 5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct"}
z = np.log10(pt.where(pt > 0))                    # colour on a log scale, like the static figure

fig2 = go.Figure(go.Heatmap(
    z=z.values, x=pt.columns, y=[month_names[m] for m in pt.index],
    customdata=pt.values,
    colorscale=[[i / (len(style.HEAT_STEPS) - 1), c] for i, c in enumerate(style.HEAT_STEPS)],
    zmin=3, zmax=7, xgap=1, ygap=1,
    colorbar=dict(title="Area burned (ha)", tickvals=[3, 4, 5, 6, 7],
                  ticktext=["1K", "10K", "100K", "1M", "10M"]),
    hovertemplate="%{y} %{x}: %{customdata:,.0f} ha<extra></extra>"))
fig2.update_layout(
    **LAYOUT,
    title=dict(text="Area burned by year and month of report", x=0, font=dict(size=17, color=style.INK)),
    yaxis=dict(autorange="reversed", showgrid=False),
    xaxis=dict(showgrid=False),
    height=430,
)
fig2.add_shape(type="rect", x0=2022.5, x1=2023.5, y0=-0.5, y1=2.5,
               line=dict(color="black", width=2))     # May–Jul 2023
export(fig2, "fig2_year_month_heatmap")

# %% [markdown]
# ## Fig 7: choropleth, hectares burned per 1,000 km² per year (hover for province values)
# Provinces are drawn as filled shapes in EPSG:3347 metres, so the map matches the static one.

# %%
prov = gpd.read_parquet(CLEAN / "provinces.parquet")
years = fires["year"].nunique()                    # 1959–2025
burned = fires.groupby("province")["size_ha"].sum().rename("burned_ha")
prov = prov.merge(burned, left_on="province", right_index=True, how="left")
prov["rate"] = prov["burned_ha"] / prov["land_km2"] * 1000 / years
prov["geometry"] = prov.geometry.simplify(3000)     # metres; keeps the file small

BINS = [0, 10, 50, 150, 300, 500, 800]               # same classes as the static map
LABELS = ["Under 10", "10–50", "50–150", "150–300", "300–500", "500–800"]
COLORS = [style.HEAT_STEPS[i] for i in (0, 1, 3, 4, 5, 6)]
prov["cls"] = pd.cut(prov["rate"], BINS, labels=False, include_lowest=True)


def outline(geom):
    """x and y lists for a (Multi)Polygon, with None between rings so one trace draws all parts."""
    parts = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
    xs, ys = [], []
    for part in parts:
        x, y = part.exterior.xy
        xs += list(x) + [None]
        ys += list(y) + [None]
    return xs, ys


fig7 = go.Figure()
seen = set()
for _, row in prov.sort_values("cls").iterrows():          # sorted so the legend runs low to high
    xs, ys = outline(row.geometry)
    c = int(row["cls"])
    fig7.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines", fill="toself", fillcolor=COLORS[c],
        line=dict(color="white", width=0.8), hoveron="fills", name=LABELS[c],
        legendgroup=LABELS[c], showlegend=c not in seen,
        text=f"<b>{row['name']}</b><br>{row['rate']:,.0f} ha per 1,000 km² per year",
        hoverinfo="text"))
    seen.add(c)
fig7.update_layout(
    **{**LAYOUT, "margin": dict(l=12, r=0, t=90, b=0)},
    title=dict(text="Hectares burned per 1,000 km² of land per year, 1959–2025",
               x=0, xanchor="left", y=0.97, yanchor="top", font=dict(size=17, color=style.INK)),
    legend=dict(title="ha per 1,000 km² per year", traceorder="normal"),
    xaxis=dict(visible=False),
    yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
    height=560,
)
export(fig7, "fig7_choropleth_rate")

# %% [markdown]
# ## Fig 8: burn perimeters on a web map, one decade at a time (Folium)
# 16,000+ polygons are too heavy for a web page, so we simplify them and keep only the biggest fires.

# %%
MIN_HA = 5000          # raise this if the HTML file is bigger than ~15 MB
perims = gpd.read_parquet(CLEAN / "perimeters.parquet")
perims = perims[perims["size_ha"] >= MIN_HA].copy()
perims["geometry"] = perims.geometry.simplify(1000)          # metres (EPSG:3347)
perims = perims.to_crs(4326)
perims["size_ha"] = perims["size_ha"].round(0)

m = folium.Map(location=[58, -96], zoom_start=4, tiles=None, zoom_control=True,
               min_zoom=3, max_zoom=9)
m.fit_bounds([[42, -140], [72, -55]])                         # frame Canada on load
m.get_root().html.add_child(folium.Element(
    "<style>.leaflet-container{background:#fff;font-family:system-ui,sans-serif}</style>"))

base = gpd.read_parquet(CLEAN / "provinces.parquet")
base["geometry"] = base.geometry.simplify(3000)
base = base.to_crs(4326)[["name", "geometry"]]
folium.GeoJson(
    base.to_json(drop_id=True), name="Provinces", control=False,
    style_function=lambda f: {"fillColor": style.LAND, "color": style.BORDER, "weight": 1, "fillOpacity": 1},
).add_to(m)

decades = sorted(perims["decade"].unique())
for decade in decades:
    layer = folium.FeatureGroup(name=str(decade), overlay=False, show=(decade == decades[-1]))
    sub = perims[perims["decade"] == decade][["year", "size_ha", "cause", "geometry"]]
    folium.GeoJson(
        sub.to_json(drop_id=True),
        style_function=lambda f: {
            "fillColor": style.CAUSE_COLORS.get(f["properties"]["cause"], style.NEUTRAL),
            "color": style.CAUSE_COLORS.get(f["properties"]["cause"], style.NEUTRAL),
            "weight": 0.6, "fillOpacity": 0.65},
        highlight_function=lambda f: {"weight": 2, "fillOpacity": 0.9},
        tooltip=folium.GeoJsonTooltip(fields=["year", "size_ha", "cause"],
                                      aliases=["Year", "Size (ha)", "Cause"],
                                      localize=True),
    ).add_to(layer)
    layer.add_to(m)
folium.LayerControl(collapsed=False, position="topright").add_to(m)

legend = (
    '<div style="position:fixed;bottom:24px;left:24px;z-index:9999;background:#fff;padding:10px 14px;'
    'border:1px solid #dcdad2;font-size:13px;line-height:1.7;color:#1c1b19">'
    '<b>Burn perimeters (fires of ' + f"{MIN_HA:,}" + ' ha or more)</b><br>'
    + "".join(f'<span style="display:inline-block;width:12px;height:12px;background:{c};'
              f'margin-right:6px;opacity:.8"></span>{k}<br>'
              for k, c in style.CAUSE_COLORS.items())
    + 'Choose a decade at the top right.</div>'
)
m.get_root().html.add_child(folium.Element(legend))
m.save(OUT / "fig8_perimeters_map.html")
print("wrote", OUT / "fig8_perimeters_map.html")

# %% [markdown]
# ## Fig 9 and Fig 10: treemap and sunburst (same syntax as Lecture 19)
# Area burned by large fires, split by province and cause. The treemap goes province first, the
# sunburst goes cause first, so together they show both "where" and "why".

# %%
import plotly.express as px

tm = pd.read_parquet(CLEAN / "fires.parquet", columns=["province", "cause", "size_ha", "is_large"])
# province and cause are stored as pandas categoricals; Plotly's hierarchy charts need plain text
tm["province"] = tm["province"].astype(str)
tm["cause"] = tm["cause"].astype(str)
tm = tm[tm["is_large"]].groupby(["province", "cause"], as_index=False, observed=True)["size_ha"].sum()
names = pd.DataFrame(gpd.read_parquet(CLEAN / "provinces.parquet")[["province", "name"]])
names["province"] = names["province"].astype(str)
names["name"] = names["name"].astype(str)
tm = tm.merge(names, on="province")
tm = tm[tm["size_ha"] > 0].copy()
tm["Mha"] = (tm["size_ha"] / 1e6).round(3)           # million hectares

# Leaf nodes take the cause colour; parent nodes with mixed causes get the neutral land colour.
COLOR_MAP = {**style.CAUSE_COLORS, "(?)": style.LAND}
TEXT = dict(texttemplate="%{label}<br>%{value:.1f} Mha",
            hovertemplate="<b>%{label}</b><br>%{value:.2f} million ha burned<extra></extra>")

fig9 = px.treemap(data_frame=tm, path=["name", "cause"], values="Mha", color="cause",
                  color_discrete_map=COLOR_MAP, height=600)
fig9.update_traces(**TEXT, marker_line_color="white")
fig9.update_layout(font=LAYOUT["font"], margin=dict(t=10, l=10, r=10, b=10))
export(fig9, "fig9_treemap_province_cause")

fig10 = px.sunburst(data_frame=tm, path=["cause", "name"], values="Mha", color="cause",
                    color_discrete_map=COLOR_MAP, height=620)
fig10.update_traces(**TEXT, marker_line_color="white")
fig10.update_layout(font=LAYOUT["font"], margin=dict(t=10, l=10, r=10, b=10))
export(fig10, "fig10_sunburst_cause_province")
