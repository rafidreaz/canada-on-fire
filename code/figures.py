"""Every report figure, one function each. Each returns (fig, facts) where
`facts` holds the numbers quoted in the caption so text and figure agree."""
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

from scipy import stats

import fire_data as fd
import style as st


def trend_test(series):
    """Kendall's tau (monotonic trend) and Theil-Sen slope with 95% CI, per year."""
    s = series.dropna()
    tau, p = stats.kendalltau(s.index, s.values)
    slope, _, lo, hi = stats.theilslopes(s.values, s.index)
    return dict(tau=tau, p=p, slope=slope, lo=lo, hi=hi, years=f"{s.index.min()}–{s.index.max()}")


def _p(p):
    return "p < 0.001" if p < 0.001 else f"p = {p:.2f}"


# --------------------------------------------------------------------------
# Fig 1 (Q1) - line chart: area up, fire count down, 2023 off the scale
# --------------------------------------------------------------------------
def fig1_trend(df):
    y = fd.yearly(df)
    roll = y.rolling(10, min_periods=10).mean()   # trailing: mean of this + previous 9 years
    rec_year = int(y.area_ha.idxmax())
    rec = y.area_ha.max()
    runner_year = int(y.area_ha.drop(rec_year).idxmax())
    runner = y.area_ha.loc[runner_year]
    ta = trend_test(y.area_ha.loc[fd.FULL_REPORTING_FROM:])
    tf = trend_test(y.fires.loc[fd.FULL_REPORTING_FROM:])

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(st.TEXT_WIDTH, 4.6), sharex=True,
                                 gridspec_kw={"height_ratios": [1.7, 1], "hspace": 0.28})
    for ax in (a1, a2):
        ax.axvspan(fd.FIRST_YEAR - 1, fd.FULL_REPORTING_FROM - 0.5, color="#F3F1EC", zorder=0, lw=0)
        ax.yaxis.grid(True)
        ax.set_axisbelow(True)

    # top: hectares
    a1.plot(y.index, y.area_ha, color=st.CONTEXT, lw=1.0, zorder=2)
    a1.plot(roll.index, roll.area_ha, color=st.LIGHTNING, lw=2.0, zorder=3,
            solid_capstyle="round")
    a1.scatter([rec_year], [rec], s=34, color=st.EMBER, zorder=4, edgecolor="white", lw=0.8)
    a1.text(rec_year - 1.8, rec, f"{rec_year}: {rec / 1e6:.1f} million ha", ha="right",
            va="center", fontsize=8.5, color=st.INK, fontweight="bold")
    a1.text(rec_year - 2.2, rec * 0.9, f"{rec / runner:.1f}x the next-worst year",
            ha="right", va="center", fontsize=7.5, color=st.INK)
    a1.scatter([runner_year], [runner], s=22, color=st.INK, zorder=4, edgecolor="white", lw=0.8)
    a1.annotate(f"{runner_year}: {runner / 1e6:.1f} million ha, 2nd largest", xy=(runner_year, runner),
                xytext=(runner_year - 3, runner + 2.4e6), fontsize=7.2, color=st.INK, ha="right",
                va="center", arrowprops=dict(arrowstyle="-", color=st.INK, lw=0.6, shrinkB=3))
    a1.text(fd.FULL_REPORTING_FROM + 1, rec * 0.74,
            f"Trend {ta['years']}: not significant\n"
            f"(Kendall τ = {ta['tau']:.2f}, {_p(ta['p'])})",
            fontsize=7, color=st.MUTED, va="top")
    last = roll.area_ha.dropna()
    a1.text(last.index[-1] + 1.2, last.iloc[-1], "10-year\naverage", color=st.INK,
            fontsize=7.5, fontweight="bold", va="center", ha="left")
    a1.text(1951, rec * 0.97, "Incomplete reporting\nbefore 1980", fontsize=7, color=st.MUTED,
            va="top", style="italic")
    a1.set_ylim(0, rec * 1.08)
    a1.yaxis.set_major_locator(mticker.MultipleLocator(4e6))
    a1.yaxis.set_major_formatter(mticker.FuncFormatter(st.mha))
    a1.set_ylabel("Area burned (million ha)")

    # bottom: number of fires
    a2.plot(y.index, y.fires, color=st.CONTEXT, lw=1.0)
    a2.plot(roll.index, roll.fires, color=st.HUMAN, lw=2.0, solid_capstyle="round")
    lastf = roll.fires.dropna()
    a2.text(lastf.index[-1] + 1.2, lastf.iloc[-1], "10-year\naverage", color=st.INK,
            fontsize=7.5, fontweight="bold", va="center", ha="left")
    peak_dec = roll.fires.idxmax()
    a2.text(fd.FULL_REPORTING_FROM + 1, y.fires.max() * 1.1,
            f"Trend {tf['years']}: {tf['slope']:.0f} fires a year "
            f"(95% CI {tf['lo']:.0f} to {tf['hi']:.0f}), {_p(tf['p'])}", fontsize=7, color=st.MUTED, va="top")
    a2.set_ylim(0, y.fires.max() * 1.16)
    a2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v / 1000:.0f}k" if v else "0"))
    a2.set_ylabel("Fires reported")
    a2.set_xlim(fd.FIRST_YEAR - 1, fd.LAST_YEAR + 1)
    a2.xaxis.set_major_locator(mticker.MultipleLocator(10))

    a1.set_title("Area burned", fontsize=8.5, fontweight="bold", color=st.INK, pad=4)
    a2.set_title("Number of fires", fontsize=8.5, fontweight="bold", color=st.INK, pad=4)

    fig.subplots_adjust(top=0.84, bottom=0.1, left=0.09, right=0.9)
    st.headline(fig, "Fewer fires each year, but the worst seasons are extreme: 2023 and 2025 lead the record",
                "Canada, 1950–2025. Grey: yearly totals. Bold: trailing 10-year average (first full window 1959).",
                y=0.995)
    st.source_note(fig)

    early = y.loc[1980:1999]
    late = y.loc[2006:2025]
    facts = dict(record_year=rec_year, record_mha=rec / 1e6, ratio=rec / runner,
                 area_80s90s_mha=early.area_ha.mean() / 1e6, area_last20_mha=late.area_ha.mean() / 1e6,
                 fires_80s90s=early.fires.mean(), fires_last20=late.fires.mean(),
                 peak_fire_year_smoothed=int(peak_dec), runner_year=runner_year,
                 runner_mha=runner / 1e6, area_trend=ta, fire_trend=tf)
    return fig, facts


# --------------------------------------------------------------------------
# Fig 2 (Q1) - heatmap year x month: when the land burns, 2023 came early
# --------------------------------------------------------------------------
def fig2_season_heatmap(df):
    from matplotlib.colors import PowerNorm
    months = list(range(3, 11))  # Mar-Oct hold 99.8% of dated area burned
    mnames = ["Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"]
    dated = df[df.MONTH > 0]
    grid = (dated.pivot_table(index="MONTH", columns="YEAR", values="SIZE_HA", aggfunc="sum")
            .reindex(index=months, columns=range(fd.FIRST_YEAR, fd.LAST_YEAR + 1)).fillna(0))
    share_shown = dated[dated.MONTH.isin(months)].SIZE_HA.sum() / dated.SIZE_HA.sum()

    fig, ax = plt.subplots(figsize=(st.TEXT_WIDTH, 3.05))
    vals = grid.to_numpy().copy()
    vals[vals < 100] = np.nan                       # <100 ha in a month = "little or none"
    cmap = sns.color_palette(st.FIRE_CMAP, as_cmap=True).copy()
    cmap.set_bad("white")                           # blank = little or no burning
    x = np.arange(fd.FIRST_YEAR, fd.LAST_YEAR + 2) - 0.5
    yy = np.arange(len(months) + 1) - 0.5
    vmax = np.nanmax(vals)
    mesh = ax.pcolormesh(x, yy, vals, cmap=cmap, norm=PowerNorm(0.5, vmin=0, vmax=vmax),
                         edgecolors="white", linewidth=0.35)
    ax.set_yticks(range(len(months)), mnames)
    ax.invert_yaxis()
    ax.set_xticks(range(1950, 2030, 10))
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)

    # focus: outline 2023 and call out its record May
    ax.add_patch(plt.Rectangle((2022.5, -0.5), 1, len(months), fill=False, ec=st.INK, lw=1.1))
    may23 = grid.loc[5, 2023]
    may_rank = int(grid.loc[5].rank(ascending=False)[2023])
    ax.annotate(f"May 2023: {may23 / 1e6:.1f} million ha,\nthe largest May on record",
                xy=(2023, 2), xytext=(2014, -1.25), fontsize=7.5, color=st.INK,
                ha="right", va="center", fontweight="semibold", annotation_clip=False,
                arrowprops=dict(arrowstyle="-", color=st.INK, lw=0.7, shrinkB=0,
                                connectionstyle="angle,angleA=0,angleB=90,rad=0"))

    fig.subplots_adjust(top=0.68, left=0.06, right=0.995, bottom=0.11)
    cax = fig.add_axes([0.075, 0.755, 0.33, 0.03])
    cb = fig.colorbar(mesh, cax=cax, orientation="horizontal")
    cb.outline.set_visible(False)
    ticks = [0, 0.1e6, 0.5e6, 1e6, 2e6, 4e6, 6e6]
    cb.set_ticks(ticks, labels=["0", "0.1", "0.5", "1", "2", "4", "6M ha"])
    cb.ax.tick_params(labelsize=6.8, length=0, pad=2)
    cb.ax.set_title("Area burned in the month (square-root scale)", fontsize=6.8,
                    color=st.MUTED, loc="left", pad=3)
    st.headline(fig, "Canada burns in a narrow early-summer window; 2023 ignited it early",
                "Hectares burned per month, 1950–2025. Blank cells: under 100 ha. Reporting is incomplete before 1980.", y=0.995)
    st.source_note(fig)
    peak = grid.sum(axis=1)
    facts = dict(share_mar_oct=share_shown, may23_mha=may23 / 1e6, may23_rank=may_rank,
                 share_may_aug=peak.loc[5:8].sum() / peak.sum(),
                 jun_jul_share=peak.loc[6:7].sum() / peak.sum())
    return fig, facts


def _largest_remainder(shares, total=100):
    """Round shares to integers that sum exactly to `total` (waffle must = 100%)."""
    raw = np.asarray(shares, float) / np.sum(shares) * total
    out = np.floor(raw).astype(int)
    for i in np.argsort(raw - out)[::-1][: total - out.sum()]:
        out[i] += 1
    return out


# --------------------------------------------------------------------------
# Fig 3 (Q1) - treemap: 2023 burned everywhere at once
# --------------------------------------------------------------------------
def fig3_treemap_2023(df):
    import squarify
    d = df[df.YEAR == 2023]
    by = d.groupby("province", observed=True).SIZE_HA.sum().sort_values(ascending=False)
    by = by[by > 0]
    keep = by[by >= 1e6]
    rest = by[by < 1e6]
    tiles = pd.concat([keep, pd.Series({"Other 7": rest.sum()})])
    total = by.sum()
    top4 = by[by >= 1.5e6]                       # focus: every jurisdiction over 1.5 Mha
    top2 = by.head(2)

    W, H = 100, 36
    fig, ax = plt.subplots(figsize=(st.TEXT_WIDTH, 2.45))
    rects = squarify.squarify(squarify.normalize_sizes(tiles.values, W, H), 0, 0, W, H)
    for r, (name, val) in zip(rects, tiles.items()):
        focal = name in top4.index
        fc = st.EMBER if focal else ("#E7E2DA" if name == "Other 7" else "#CFC7BC")
        tc = "white" if focal else st.INK
        ax.add_patch(plt.Rectangle((r["x"], r["y"]), r["dx"], r["dy"], fc=fc, ec="white", lw=2.2))
        label = name if name != "Other 7" else "Others*"
        narrow = r["dx"] < 15
        if narrow:
            label = label.replace(" ", "\n")
        ax.text(r["x"] + 1.2, r["y"] + r["dy"] - 1.8, label, ha="left", va="top",
                fontsize=8.5 if focal else 7.5, fontweight="bold", color=tc, linespacing=1.15)
        ax.text(r["x"] + 1.2, r["y"] + r["dy"] - (9.6 if narrow else 6.0),
                f"{val / 1e6:.1f} Mha · {val / total:.0%}",
                ha="left", va="top", fontsize=7.5 if focal else 7, color=tc)
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")
    fig.subplots_adjust(top=0.79, bottom=0.08, left=0, right=1)
    st.headline(fig, f"2023 burned in five jurisdictions at once; {top2.index[0]} and the NWT "
                f"made up half",
                f"Area burned in 2023 ({total / 1e6:.1f} million ha) by where the fires burned. "
                "Tile area = hectares. Red: over 1.5 million ha.", y=0.995)
    st.source_note(fig, st.SOURCE + ".  *" + ", ".join(rest.index) + ".")
    facts = dict(total_mha=total / 1e6, focal=list(top4.index), focal_share=top4.sum() / total,
                 top2_share=top2.sum() / total, by_province_mha=(by / 1e6).round(2).to_dict(),
                 regions_over_1mha=int((by >= 1e6).sum()))
    return fig, facts


# --------------------------------------------------------------------------
# Fig 4 (Q2) - waffles: humans light most fires, lightning burns most land
# (unit squares drawn directly so every square sits on an exact grid)
# --------------------------------------------------------------------------
def _waffle(ax, squares, colors, n=10, gap=0.16):
    from matplotlib.patches import FancyBboxPatch
    cells = [c for c, k in zip(colors, squares) for _ in range(k)]
    for i, c in enumerate(cells):                  # fill column-wise from bottom-left
        col, row = divmod(i, n)
        ax.add_patch(FancyBboxPatch((col + gap / 2, row + gap / 2), 1 - gap, 1 - gap,
                                    boxstyle="round,pad=0,rounding_size=0.14", fc=c, ec="none"))
    ax.set_xlim(0, n)
    ax.set_ylim(0, n)
    ax.set_aspect("equal")
    ax.axis("off")


def fig4_waffle_cause(df):
    counts = df.cause.value_counts().reindex(fd.CAUSE_ORDER)
    area = df.groupby("cause", observed=True).SIZE_HA.sum().reindex(fd.CAUSE_ORDER)
    c_sq, a_sq = _largest_remainder(counts), _largest_remainder(area)
    colors = [st.CAUSE_COLORS[c] for c in fd.CAUSE_ORDER]

    fig = plt.figure(figsize=(st.TEXT_WIDTH, 2.7))
    axes = [fig.add_axes([0.0, 0.1, 0.27, 0.62]), fig.add_axes([0.5, 0.1, 0.27, 0.62])]
    for ax, title, sq in ((axes[0], "Share of fires started", c_sq),
                          (axes[1], "Share of area burned", a_sq)):
        _waffle(ax, sq, colors)
        ax.text(0, 10.35, title, fontsize=8.5, fontweight="bold", color=st.INK, va="bottom")
        y = 9.6
        for cause, k in zip(fd.CAUSE_ORDER, sq):
            ax.add_patch(plt.Rectangle((10.6, y - 2.55), 0.62, 0.62, fc=st.CAUSE_COLORS[cause],
                                       ec="none", clip_on=False))
            ax.text(10.6, y, f"{k}%", fontsize=14, fontweight="bold", color=st.INK,
                    va="top", ha="left")
            ax.text(11.45, y - 2.0, cause, fontsize=7.5, color=st.MUTED, va="top", ha="left")
            y -= 3.4
    st.headline(fig, "People start most fires, but lightning burns most of the land",
                "Each square is 1% of all fires (left) or of all hectares burned (right), 1950–2025.",
                y=0.995)
    st.source_note(fig, st.SOURCE + ". Squares rounded to sum to exactly 100.")
    facts = dict(fire_share=dict(zip(fd.CAUSE_ORDER, (counts / counts.sum()).round(3))),
                 area_share=dict(zip(fd.CAUSE_ORDER, (area / area.sum()).round(3))),
                 mean_size=dict(zip(fd.CAUSE_ORDER, (area / counts).round(1))))
    return fig, facts


# --------------------------------------------------------------------------
# Fig 5 (Q2) - radar: two different fire seasons
# --------------------------------------------------------------------------
def fig5_radar_season(df):
    dated = df[df.MONTH > 0]
    share = (pd.crosstab(dated.MONTH, dated.cause, normalize="columns")
             .reindex(range(1, 13)).fillna(0))
    labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    theta = np.linspace(0, 2 * np.pi, 12, endpoint=False)

    fig = plt.figure(figsize=(st.TEXT_WIDTH, 3.6))
    ax = fig.add_axes([0.05, 0.11, 0.46, 0.66], projection="polar")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    rmax = 0.40
    for r in (0.1, 0.2, 0.3, 0.4):
        ax.plot(np.linspace(0, 2 * np.pi, 200), [r] * 200, color=st.GRID, lw=0.7, zorder=0)
    ax.text(np.deg2rad(-5), 0.1, "10%", fontsize=6.5, color=st.MUTED, ha="right")
    ax.text(np.deg2rad(-5), 0.2, "20%", fontsize=6.5, color=st.MUTED, ha="right")
    ax.text(np.deg2rad(-5), 0.3, "30%", fontsize=6.5, color=st.MUTED, ha="right")
    ax.grid(False)
    ax.spines["polar"].set_visible(False)
    ax.set_yticks([])
    ax.set_xticks(theta, labels, fontsize=7.5, color=st.MUTED)
    ax.set_ylim(0, rmax)
    for cause, lw, z in (("Human", 2.2, 3), ("Lightning", 2.2, 3)):
        v = share[cause].to_numpy()
        t = np.append(theta, theta[0])
        vv = np.append(v, v[0])             # close the loop (L11 p.6)
        ax.plot(t, vv, color=st.CAUSE_COLORS[cause], lw=lw, zorder=z)   # lines only: a filled
        ax.scatter(theta, v, s=22, color=st.CAUSE_COLORS[cause], edgecolor="white", linewidth=1.0,
                   zorder=z + 1)                                     # area would grow with r²
    # direct labels at each peak
    hp, lp = share["Human"].idxmax(), share["Lightning"].idxmax()
    ax.annotate(f"Human\npeaks in May\n({share.loc[hp, 'Human']:.0%})", xy=(theta[hp - 1], share.loc[hp, "Human"]),
                xytext=(np.deg2rad(22), 0.25), fontsize=7.5, color=st.INK, fontweight="bold",
                ha="left", arrowprops=dict(arrowstyle="-", color=st.HUMAN, lw=0.7))
    ax.annotate(f"Lightning\npeaks in July\n({share.loc[lp, 'Lightning']:.0%})",
                xy=(theta[lp - 1], share.loc[lp, "Lightning"]), xytext=(np.deg2rad(238), 0.27),
                fontsize=7.5, color=st.INK, fontweight="bold", ha="right",
                arrowprops=dict(arrowstyle="-", color=st.LIGHTNING, lw=0.7))

    # side panel: the reading guide + the 3 numbers that matter
    spring_h = share.loc[3:5, "Human"].sum()
    summer_l = share.loc[6:8, "Lightning"].sum()
    tx = 0.6
    fig.text(tx, 0.70, "How to read", fontsize=8, fontweight="bold", color=st.INK)
    fig.text(tx, 0.67, "Each spoke is a month. Distance from the centre is\nthat month's share "
             "of the year's fires for each cause,\nso the two shapes compare timing, not volume.",
             fontsize=7.2, color=st.MUTED, va="top", linespacing=1.4)
    kx = tx                                                  # legend key (two series)
    for c, lab in ((st.LIGHTNING, "Lightning"), (st.HUMAN, "Human")):
        fig.add_artist(plt.Line2D([kx, kx + 0.03], [0.78, 0.78], color=c, lw=2.2,
                                  transform=fig.transFigure))
        fig.text(kx + 0.037, 0.78, lab, fontsize=7.8, color=st.INK, va="center")
        kx += 0.14
    fig.add_artist(plt.Rectangle((tx - 0.025, 0.478), 0.014, 0.028, fc=st.HUMAN, ec="none",
                                 transform=fig.transFigure))
    fig.add_artist(plt.Rectangle((tx - 0.025, 0.308), 0.014, 0.028, fc=st.LIGHTNING, ec="none",
                                 transform=fig.transFigure))
    fig.text(tx, 0.47, f"{spring_h:.0%}", fontsize=20, fontweight="bold", color=st.INK)
    fig.text(tx + 0.13, 0.475, "of human-caused fires start\nin spring (March–May)",
             fontsize=7.5, color=st.INK, linespacing=1.3)
    fig.text(tx, 0.30, f"{summer_l:.0%}", fontsize=20, fontweight="bold", color=st.INK)
    fig.text(tx + 0.13, 0.305, "of lightning fires start in\nsummer (June–August)",
             fontsize=7.5, color=st.INK, linespacing=1.3)
    st.headline(fig, "Two fire seasons: people burn in spring, lightning in summer",
                "Share of each cause's fires by month of discovery, 1950–2025 (dated records; Unknown cause omitted).",
                y=0.995)
    st.source_note(fig)
    facts = dict(human_peak_month=int(hp), lightning_peak_month=int(lp),
                 human_mar_may=spring_h, lightning_jun_aug=summer_l)
    return fig, facts


# --------------------------------------------------------------------------
# Fig 6 (Q2) - sorted stacked bars: where each cause burns
# --------------------------------------------------------------------------
def fig6_region_cause(df):
    pv = (df.pivot_table(index="province", columns="cause", values="SIZE_HA", aggfunc="sum",
                         observed=True).reindex(columns=fd.CAUSE_ORDER).fillna(0))
    pv = pv[pv.sum(axis=1) > 0]
    pv = pv.loc[pv.sum(axis=1).sort_values().index]          # ranked, largest on top
    total = pv.sum(axis=1)

    fig, ax = plt.subplots(figsize=(st.TEXT_WIDTH, 3.9))
    left = np.zeros(len(pv))
    for cause in fd.CAUSE_ORDER:
        ax.barh(pv.index, pv[cause], left=left, color=st.CAUSE_COLORS[cause], height=0.68,
                edgecolor="white", linewidth=0.8, label=cause)
        left += pv[cause].to_numpy()
    for i, (name, tot) in enumerate(total.items()):
        lshare = pv.loc[name, "Lightning"] / tot if tot else 0
        lab = f"{tot / 1e6:.1f} Mha" if tot >= 0.1e6 else "<0.1 Mha"
        t = ax.text(tot + 0.35e6, i, lab, va="center", fontsize=7.5, color=st.INK,
                    fontweight="semibold")
        if tot > 1e6:
            ax.annotate(f"  {lshare:.0%} lightning", xycoords=t, xy=(1, 0.5), va="center",
                        fontsize=6.8, color=st.MUTED)
    ax.set_xlim(0, total.max() * 1.18)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(st.mha))
    ax.xaxis.grid(True)
    ax.set_axisbelow(True)
    ax.set_xlabel("Area burned, 1950–2025 (million ha)")
    ax.tick_params(axis="y", length=0, labelsize=8, labelcolor=st.INK)
    ax.spines["left"].set_visible(False)
    # legend as direct colour key above the plot
    x0 = 0.0
    for cause in fd.CAUSE_ORDER:
        ax.text(x0, 1.015, "■ ", transform=ax.transAxes, color=st.CAUSE_COLORS[cause], fontsize=10,
                va="bottom")
        ax.text(x0 + 0.03, 1.02, cause, transform=ax.transAxes, color=st.INK, fontsize=8, va="bottom")
        x0 += 0.13
    fig.subplots_adjust(top=0.82, bottom=0.12, left=0.2, right=0.98)
    big = total[total > 10e6].index
    lshare = pv.loc[big, "Lightning"] / total[big]
    st.headline(fig, "Lightning burns most of the land in every major fire region; the Maritimes barely burn",
                "Total area burned 1950–2025 by the province or territory where the fire burned, and by cause. "
                "Ranked; bars start at zero.", y=0.995)
    st.source_note(fig, st.SOURCE + ". Records start 1950–60 for most agencies, New Brunswick 1980, PEI 2018.")
    nt = pv.loc["NW Territories"]
    facts = dict(top=total.idxmax(), top_mha=total.max() / 1e6,
                 nt_lightning_share=nt["Lightning"] / nt.sum(),
                 east_mha=total.reindex(["Nova Scotia", "New Brunswick", "PEI"]).sum() / 1e6,
                 lightning_share_big=lshare.round(3).to_dict())
    return fig, facts


# --------------------------------------------------------------------------
# Fig 7 (Q3) - mirrored log histogram: count of fires vs share of area
# --------------------------------------------------------------------------
NEUTRAL = "#A09A92"   # warm grey: neutral context, not a cause colour


def fig7_size_histogram(df):
    s = df.loc[df.SIZE_HA > 0, ["SIZE_HA"]].copy()
    edges = 200.0 * 10.0 ** (np.arange(-18, 18) / 4)     # 4 bins per decade, aligned so 200 ha is an edge
    s["bin"] = pd.cut(s.SIZE_HA, edges, right=False)
    g = s.groupby("bin", observed=False).SIZE_HA.agg(["size", "sum"])
    cnt_pct = g["size"] / g["size"].sum() * 100
    area_pct = g["sum"] / g["sum"].sum() * 100
    left, width = edges[:-1], np.diff(edges)

    big = 200.0                                          # threshold used in fire statistics
    sized = s.SIZE_HA                                    # denominator: fires with a recorded size > 0
    share_n = (sized >= big).mean()
    share_a = sized[sized >= big].sum() / sized.sum()
    under1 = (sized < 1).mean()
    sorted_sz = sized.sort_values(ascending=False)
    top1 = sorted_sz.head(len(sorted_sz) // 100).sum() / sorted_sz.sum()

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(st.TEXT_WIDTH, 3.9), sharex=True,
                                 gridspec_kw={"hspace": 0.08})
    is_big = left >= big * 0.999
    a1.bar(left, cnt_pct, width=width * 0.9, align="edge",
           color=np.where(is_big, st.EMBER, NEUTRAL))
    a2.bar(left, -area_pct, width=width * 0.9, align="edge",
           color=np.where(is_big, st.EMBER, NEUTRAL))
    for ax in (a1, a2):
        ax.set_xscale("log")
        ax.axvline(big, color=st.INK, lw=0.7, ls=(0, (1, 2)))
        ax.yaxis.grid(True)
        ax.set_axisbelow(True)
    a1.set_ylabel("% of fires")
    a2.set_ylabel("% of area burned")
    a2.yaxis.set_major_locator(mticker.MultipleLocator(4))
    a2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{abs(v):.0f}"))
    a1.yaxis.set_major_locator(mticker.MultipleLocator(10))
    a1.spines["bottom"].set_visible(False)
    a1.tick_params(axis="x", length=0)
    a2.spines["bottom"].set_visible(False)
    a2.spines["top"].set_visible(True)
    a2.spines["top"].set_color("#8A8A8A")
    a2.xaxis.tick_bottom()
    a2.set_xlim(0.006, 4e6)
    a2.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: {0.01: "0.01 ha", 1: "1 ha", 100: "100 ha", 1e4: "10,000 ha", 1e6: "1M ha"}.get(round(v, 2), "")))
    a2.set_xticks([0.01, 0.1, 1, 10, 100, 1e3, 1e4, 1e5, 1e6])
    a2.set_xlabel("Final fire size (log scale)")

    a1.text(big * 1.25, a1.get_ylim()[1] * 0.92,
            f"Fires of {big:.0f} ha or more:\n{share_n:.1%} of fires…", color=st.INK,
            fontsize=8, fontweight="bold", va="top")
    a2.text(big / 1.25, a2.get_ylim()[0] * 0.85, f"…but {share_a:.1%} of\nthe area burned",
            color=st.INK, fontsize=8, fontweight="bold", va="bottom", ha="right")
    a1.text(1.4, a1.get_ylim()[1] * 0.6,
            f"{under1:.0%} of fires are recorded\nunder 1 ha",
            color="#4A4A4A", fontsize=7.5, va="top")
    a1.text(0.13, a1.get_ylim()[1] * 0.98, "Spike: small fires are\noften logged as 0.1 ha",
            color=st.MUTED, fontsize=6.6, va="top", style="italic")
    a2.text(0.012, a2.get_ylim()[0] * 0.45, f"The largest 1% of fires\nburned {top1:.0%} of the area",
            color=st.INK, fontsize=7.5, va="center", ha="left", fontweight="semibold")
    fig.subplots_adjust(top=0.84, bottom=0.12, left=0.1, right=0.99)
    st.headline(fig, f"A few huge fires do almost all the burning",
                f"Fires with a recorded size, 1950–2025 (n = {len(sized):,}): share of fires (top) and "
                "share of area burned (bottom) in each size band.", y=0.995)
    st.source_note(fig)
    facts = dict(share_fires_ge200=share_n, share_area_ge200=share_a, top1pct_area=top1,
                 median_ha=sized.median(), share_under_1ha=under1, n_sized=len(sized),
                 n_zero=int((df.SIZE_HA == 0).sum()))
    return fig, facts


# --------------------------------------------------------------------------
# Fig 8 (Q3) - boxen by decade and cause: has the typical / extreme fire changed?
# --------------------------------------------------------------------------
def fig8_boxen_decade(df):
    d = df[(df.SIZE_HA >= 1) & df.cause.isin(["Lightning", "Human"])].copy()   # fires that escaped
    d["cause"] = d["cause"].cat.remove_unused_categories()
    d["dec"] = d.decade.astype(str) + "s"
    order = [f"{y}s" for y in range(1950, 2030, 10)]
    fig, ax = plt.subplots(figsize=(st.TEXT_WIDTH, 3.3))
    sns.boxenplot(data=d, x="dec", y="SIZE_HA", hue="cause", order=order,
                  hue_order=["Lightning", "Human"], palette=st.CAUSE_COLORS, log_scale=True,
                  k_depth=4, width=0.78, gap=0.12, linewidth=0.5, linecolor="white",
                  flier_kws=dict(s=1.2, alpha=0.35, linewidth=0), ax=ax, legend=False)
    ax.axvspan(-0.5, 2.5, color="#F3F1EC", zorder=0, lw=0)
    ax.text(-0.42, 2.4e6, "Incomplete\nreporting", fontsize=6.8, color=st.MUTED, va="top", style="italic")
    med = d.groupby(["dec", "cause"], observed=True).SIZE_HA.median().unstack()
    p99 = d.groupby(["dec", "cause"], observed=True).SIZE_HA.quantile(0.99).unstack()
    ax.set_ylim(0.8, 3e6)
    ax.set_xlabel("")
    ax.set_ylabel("Final fire size (ha, log scale)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: {1: "1", 10: "10", 100: "100", 1e3: "1k", 1e4: "10k", 1e5: "100k", 1e6: "1M"}.get(round(v, 2), "")))
    ax.yaxis.set_minor_locator(mticker.NullLocator())
    for i, dec in enumerate(order):                     # median labels, both causes
        for dx, cause in ((-0.2, "Lightning"), (0.2, "Human")):
            m = med.loc[dec, cause]
            ax.text(i + dx, m, f"{m:.0f}", ha="center", va="center", fontsize=6.3, color="white",
                    fontweight="bold", bbox=dict(boxstyle="round,pad=0.15",
                                                 fc=st.CAUSE_COLORS[cause], ec="none"))
    ax.set_xticks(range(len(order)), order[:-1] + ["2020s\n(2020–25)"])
    # trend test on yearly medians, 1980 on (complete reporting)
    rec = d[d.YEAR >= fd.FULL_REPORTING_FROM]
    ym = rec.groupby(["YEAR", "cause"], observed=True).SIZE_HA.median().unstack()
    rho = {c: stats.spearmanr(ym.index, ym[c]) for c in ("Lightning", "Human")}
    no23 = ym.drop(2023)
    rho_l_no23 = stats.spearmanr(no23.index, no23["Lightning"])[0]
    ax.text(0.995, 0.97, f"Yearly median vs year, 1980–2025 (Spearman):\n"
            f"lightning ρ = {rho['Lightning'][0]:.2f}, {_p(rho['Lightning'][1])} "
            f"({rho_l_no23:.2f} without 2023)\n"
            f"human ρ = {rho['Human'][0]:.2f}, {_p(rho['Human'][1])}",
            transform=ax.transAxes, ha="right", va="top", fontsize=6.8, color=st.INK,
            bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=st.GRID, lw=0.6))
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", length=0, labelcolor=st.INK)
    ax.text(0.0, 1.03, "■", transform=ax.transAxes, color=st.LIGHTNING, fontsize=10, va="bottom")
    ax.text(0.025, 1.035, "Lightning", transform=ax.transAxes, fontsize=8, va="bottom")
    ax.text(0.14, 1.03, "■", transform=ax.transAxes, color=st.HUMAN, fontsize=10, va="bottom")
    ax.text(0.165, 1.035, "Human", transform=ax.transAxes, fontsize=8, va="bottom")
    ax.text(0.26, 1.035, "Widest box = middle 50% of fires; each narrower box adds the next tail.",
            transform=ax.transAxes, fontsize=7, color=st.MUTED, va="bottom")
    fig.subplots_adjust(top=0.8, bottom=0.08, left=0.1, right=0.99)
    st.headline(fig, "Since 1980 the typical escaped lightning fire has grown; human fires have not",
                "Size of fires that grew past 1 ha, by decade and cause (boxen plot). "
                "Labels: median size (ha).",
                y=0.995)
    st.source_note(fig)
    n = d.groupby(["dec", "cause"], observed=True).size().unstack()
    facts = dict(median=med.round(2).to_dict(), p99=p99.round(0).to_dict(), n=n.to_dict(),
                 rho_lightning=rho["Lightning"][0], p_lightning=rho["Lightning"][1],
                 rho_lightning_no2023=rho_l_no23, rho_human=rho["Human"][0], p_human=rho["Human"][1])
    return fig, facts


# --------------------------------------------------------------------------
# Maps (Q4). Layers come from code/prepare_geo.py (run once).
# --------------------------------------------------------------------------
GEO_DIR = st.FIG_DIR.parent / "data_derived"
LAND = "#EFEBE4"


def _load_geo():
    import geopandas as gpd
    prov = gpd.read_file(GEO_DIR / "canada_provinces.gpkg")
    scars = gpd.read_file(GEO_DIR / "burn_scars_1972_2024.gpkg")
    return prov, scars


def _base_map(ax, prov, crop=True, top=0.75):
    prov.plot(ax=ax, color=LAND, edgecolor="white", linewidth=0.6, zorder=0)
    ax.set_axis_off()
    ax.set_aspect("equal")
    if crop:   # trim the fire-free high Arctic so the page is used for the fire belt
        x0, y0, x1, y1 = prov.total_bounds
        ax.set_xlim(x0 + 0.02 * (x1 - x0), x1 - 0.04 * (x1 - x0))
        ax.set_ylim(y0, y0 + top * (y1 - y0))


def scar_centres(scars):
    """Area-weighted centre of burning per decade (projected metres) and Mha per year."""
    c = scars.geometry.representative_point()
    w = scars.SIZE_HA
    g = scars.assign(cx=c.x * w, cy=c.y * w, w=w).groupby("dec")
    out = pd.DataFrame({"x": g.cx.sum() / g.w.sum(), "y": g.cy.sum() / g.w.sum(),
                        "mha_per_year": g.w.sum() / g.YEAR.nunique() / 1e6,
                        "years": g.YEAR.nunique()})
    return out


def fig9_burn_scars(df):
    from matplotlib.colors import BoundaryNorm, ListedColormap
    import geopandas as gpd
    prov, scars = _load_geo()
    scars["dec"] = (scars.YEAR // 10) * 10
    decades = [1970, 1980, 1990, 2000, 2010, 2020]
    ramp = sns.color_palette("rocket_r", 9)[1:7]          # pale -> deep, six decades
    cen = scars_c = scar_centres(scars)
    fig, ax = plt.subplots(figsize=(st.TEXT_WIDTH, 4.9))
    _base_map(ax, prov, top=0.78)
    for dec, col in zip(decades, ramp):                    # oldest first, newest on top
        scars[scars.dec == dec].plot(ax=ax, color=col, linewidth=0, zorder=1 + dec / 1e4)
    prov.boundary.plot(ax=ax, color="white", linewidth=0.5, zorder=3)

    from matplotlib import patheffects as pe
    halo = [pe.withStroke(linewidth=2.2, foreground="white")]
    # centre of burning, decade by decade (the "has it shifted?" answer, drawn in place)
    ax.plot(cen.x, cen.y, color=st.INK, lw=0.9, zorder=5)
    for (dec, r), col in zip(cen.iterrows(), ramp):
        ax.scatter(r.x, r.y, s=34, color=col, edgecolor=st.INK, lw=0.8, zorder=6)
    first, last = cen.iloc[1], cen.iloc[-1]                # 1980s (complete) -> 2020s
    shift_km = (first.x - last.x) / 1000
    from matplotlib import patheffects as pe
    halo = [pe.withStroke(linewidth=2.2, foreground="white")]
    ax.annotate(f"Centre of burning\n{shift_km:.0f} km west\nsince the 1980s",
                xy=(first.x, first.y), xytext=(first.x + 0.36e6, first.y + 0.24e6), fontsize=7.2,
                color=st.INK, fontweight="semibold", ha="left", va="center", zorder=7,
                path_effects=halo, linespacing=1.15,
                arrowprops=dict(arrowstyle="-", color=st.INK, lw=0.6, shrinkB=5))
    for r, lab, ha, dx in ((first, "1980s", "left", 0.9e5), (last, "2020s", "right", -0.9e5)):
        ax.text(r.x + dx, r.y - 1.1e5, lab, fontsize=6.4, color=st.INK, ha=ha, va="center",
                fontweight="bold", zorder=7, path_effects=halo)

    # place names used in the title
    for code, label in (("NT", "Northwest\nTerritories"), ("QC", "Quebec"), ("BC", "BC"),
                        ("SK", "Sask."), ("AB", "Alberta"), ("ON", "Ontario")):
        pt = prov.loc[prov.postal == code].geometry.representative_point().iloc[0]
        dy = {"NT": -2.2e5, "QC": 2.8e5, "ON": 2.5e5}.get(code, 0)
        ax.text(pt.x, pt.y + dy, label, fontsize=6.6, color="#4A4A4A", ha="center", va="center",
                zorder=7, fontweight="semibold", linespacing=1.1, path_effects=halo)

    # scale bar: 500 km
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    sx, sy = x1 - 0.2 * (x1 - x0), y0 + 0.06 * (y1 - y0)
    ax.plot([sx, sx + 5e5], [sy, sy], color=st.INK, lw=1.4, solid_capstyle="butt", zorder=7)
    ax.text(sx + 2.5e5, sy + 0.012 * (y1 - y0), "500 km", fontsize=6.6, ha="center", va="bottom",
            color=st.INK, zorder=7)

    # inset: mapped area burned per year, by decade (normalised: the 2020s hold 5 seasons)
    ins = fig.add_axes([0.70, 0.60, 0.27, 0.17])
    ins.bar(range(len(cen)), cen.mha_per_year, color=ramp, width=0.72)
    for i, v in enumerate(cen.mha_per_year):
        ins.text(i, v + 0.15, f"{v:.1f}", ha="center", va="bottom", fontsize=6.4, color=st.INK)
    ins.set_xticks(range(len(cen)), ["70s", "80s", "90s", "00s", "10s", "20s"], fontsize=6.4)
    ins.set_yticks([])
    ins.spines[["left", "top", "right"]].set_visible(False)
    ins.tick_params(axis="x", length=0, pad=1)
    ins.set_ylim(0, cen.mha_per_year.max() * 1.25)
    ins.set_title("Mapped area burned per year (Mha)", fontsize=6.8, color=st.INK, loc="left",
                  fontweight="semibold", pad=3)
    ins.patch.set_alpha(0)

    # decade colour key (stepped, labelled)
    cax = fig.add_axes([0.03, 0.08, 0.34, 0.022])
    cmap = ListedColormap(ramp)
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=BoundaryNorm(range(7), 6), cmap=cmap), cax=cax,
                      orientation="horizontal")
    cb.set_ticks([i + 0.5 for i in range(6)], labels=["1970s", "80s", "90s", "00s", "10s", "2020–24"])
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=0, labelsize=6.8, pad=2)
    cb.ax.set_title("Decade the area burned (dots: centre of burning)", fontsize=7, color=st.MUTED,
                    loc="left", pad=3)

    lat = gpd.GeoSeries(gpd.points_from_xy(cen.x, cen.y), crs=prov.crs).to_crs(4326)
    fig.subplots_adjust(top=0.87, bottom=0.0, left=0.0, right=1.0)
    st.headline(fig, "The fire belt has not moved north; burning per year doubled and drifted west",
                f"Mapped perimeters of {len(scars):,} fires, 1972–2024, coloured by decade; small scars "
                "under ~1 km² simplified away (1% of area).", y=0.995)
    st.source_note(fig, "Source: CNFDB burned-area polygons, NRCan; provinces: Natural Earth. "
                   "Lambert conformal conic projection. 1970s polygons are the least complete.")
    facts = dict(n_scars=len(scars), mha_per_year=cen.mha_per_year.round(2).to_dict(),
                 centre_lat=dict(zip(cen.index, lat.y.round(2))),
                 centre_lon=dict(zip(cen.index, lat.x.round(2))), shift_km_west_80s_20s=shift_km)
    return fig, facts


def fig11_burn_rate_map(df):
    """Hectares burned per 1,000 km² of land per year, 1980-2025 (normalised choropleth)."""
    from matplotlib.colors import BoundaryNorm, ListedColormap
    prov, _ = _load_geo()
    rec = df[df.YEAR >= fd.FULL_REPORTING_FROM]
    years = fd.LAST_YEAR - fd.FULL_REPORTING_FROM + 1
    code = {v: k for k, v in fd.PROV_SHORT.items()}
    ha = rec.groupby("province", observed=True).SIZE_HA.sum().rename(index=code)
    prov = prov.set_index("postal")
    prov["rate"] = (ha.reindex(prov.index).fillna(0) / years) / (prov.geometry.area / 1e9)
    bins = [0, 50, 200, 400, 600, 1000]
    ramp = sns.color_palette("rocket_r", 8)[0:6:1][:len(bins) - 1]
    ramp[0] = "#F6EDE3"                                    # lowest class still visibly tinted
    cmap, norm = ListedColormap(ramp), BoundaryNorm(bins, len(bins) - 1)

    fig, ax = plt.subplots(figsize=(st.TEXT_WIDTH, 4.3))
    prov.plot(ax=ax, column="rate", cmap=cmap, norm=norm, edgecolor="white", linewidth=0.7)
    ax.set_axis_off(); ax.set_aspect("equal")
    x0, y0, x1, y1 = prov.total_bounds
    ax.set_xlim(x0 + 0.02 * (x1 - x0), x1 - 0.04 * (x1 - x0))
    ax.set_ylim(y0, y0 + 0.78 * (y1 - y0))
    nudge = {"NU": (0, -6e5), "NT": (0, -2e5), "QC": (0, 2.5e5), "ON": (0, 2e5),
             "NS": (3.2e5, -1.4e5), "NB": (-1.5e5, 1.6e5), "PE": (2.4e5, 1.7e5)}
    for code_, r in prov.iterrows():
        pt = r.geometry.representative_point()
        dx, dy = nudge.get(code_, (0, 0))
        dark = r.rate >= 400
        ax.text(pt.x + dx, pt.y + dy, f"{code_}\n{r.rate:,.0f}", ha="center", va="center",
                fontsize=6.8 if code_ not in ("PE", "NS", "NB") else 6.0, linespacing=1.1,
                color="white" if dark else st.INK, fontweight="bold")
    cax = fig.add_axes([0.03, 0.09, 0.4, 0.022])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation="horizontal")
    cb.set_ticks(bins, labels=[f"{b:,}" for b in bins])
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=0, labelsize=6.8, pad=2)
    cb.ax.set_title("Hectares burned per 1,000 km² of land per year", fontsize=7, color=st.MUTED,
                    loc="left", pad=3)
    top = prov.rate.sort_values(ascending=False)
    fig.subplots_adjust(top=0.87, bottom=0.045, left=0.0, right=1.0)
    st.headline(fig, "Scaled by land area, Saskatchewan burns hardest and the NWT drops to fourth",
                f"Average yearly area burned per 1,000 km² of land, {fd.FULL_REPORTING_FROM}–{fd.LAST_YEAR}, "
                "by the province or territory where fires burned.", y=0.995)
    st.source_note(fig, "Source: CNFDB point data, NRCan; land area from Natural Earth provinces "
                   "(includes tundra and farmland with little fuel).")
    facts = dict(rate=top.round(0).to_dict())
    return fig, facts


def fig10_ignition_maps(df):
    from pyproj import Transformer
    prov, _ = _load_geo()
    tr = Transformer.from_crs(4326, prov.crs, always_xy=True)
    x, y = tr.transform(df.LONGITUDE.to_numpy(), df.LATITUDE.to_numpy())
    pts = df.assign(x=x, y=y)
    fig, axes = plt.subplots(1, 2, figsize=(st.TEXT_WIDTH, 3.15))
    for ax, cause in zip(axes, ["Lightning", "Human"]):
        _base_map(ax, prov)
        p = pts[pts.cause == cause]
        ax.scatter(p.x, p.y, s=0.25, color=st.CAUSE_COLORS[cause], alpha=0.25, linewidths=0,
                   rasterized=True, zorder=2)
        prov.boundary.plot(ax=ax, color="white", linewidth=0.4, zorder=3)
        ax.set_title(f"      {cause}  ·  {len(p):,} fires", fontsize=8.5, fontweight="bold",
                     color=st.INK, loc="left", pad=2)
        ax.add_patch(plt.Rectangle((0.0, 1.052), 0.022, 0.034, fc=st.CAUSE_COLORS[cause], ec="none",
                                   transform=ax.transAxes, clip_on=False))
    lat = df.groupby("cause", observed=True).LATITUDE.median()
    fig.subplots_adjust(top=0.8, bottom=0.04, left=0.0, right=1.0, wspace=0.02)
    st.headline(fig, "Lightning strikes the remote north; people start fires where they live",
                "Every fire start, 1950–2025, by cause. Blank southern Prairies: farmland outside agency fire reporting.", y=0.995)
    st.source_note(fig, "Source: CNFDB point data, NRCan; provinces: Natural Earth.")
    facts = dict(median_lat=lat.round(2).to_dict())
    return fig, facts


# --------------------------------------------------------------------------
# v2 additions
# --------------------------------------------------------------------------
def fig12_ranked_years(df):
    """Q1 - how unusual was 2023? Every year since complete reporting, ranked."""
    y = fd.yearly(df).loc[fd.FULL_REPORTING_FROM:].area_ha.sort_values(ascending=False)
    med = y.median()
    fig, ax = plt.subplots(figsize=(st.TEXT_WIDTH, 2.9))
    cols = [st.EMBER if yr == 2023 else (st.INK if yr == 2025 else NEUTRAL) for yr in y.index]
    ax.bar(range(len(y)), y.values, color=cols, width=0.78)
    ax.axhline(med, color=st.INK, lw=0.7, ls=(0, (1, 2)))
    ax.text(len(y) - 0.5, med * 1.25, f"Median year: {med / 1e6:.1f} million ha", ha="right",
            va="bottom", fontsize=7.2, color=st.INK)
    for i, (yr, v) in enumerate(y.head(2).items()):
        ax.text(i, v + 0.25e6, str(yr), ha="center", va="bottom", fontsize=7, color=st.INK,
                fontweight="bold")
    ax.annotate("then 1989, 1995, 1981", xy=(3, y.iloc[3] + 0.2e6), xytext=(5.5, y.iloc[2] + 1.6e6),
                fontsize=6.8, color=st.MUTED, ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color=st.MUTED, lw=0.5, shrinkB=2))
    ax.text(1.4, y.iloc[0] * 0.92, f"2023 = {y.iloc[0] / y.iloc[1]:.1f}x the next-worst year\n"
            f"and {y.iloc[0] / med:.0f}x the median year", fontsize=7.5, color=st.INK, va="top",
            fontweight="semibold")
    ax.set_xticks([])
    ax.set_xlim(-0.7, len(y) - 0.3)
    ax.spines["bottom"].set_visible(False)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(st.mha))
    ax.yaxis.set_major_locator(mticker.MultipleLocator(4e6))
    ax.yaxis.grid(True); ax.set_axisbelow(True)
    ax.set_ylabel("Area burned (million ha)")
    ax.set_xlabel(f"{len(y)} years, {fd.FULL_REPORTING_FROM}–{fd.LAST_YEAR}, ranked from largest to smallest",
                  fontsize=7.5, color=st.MUTED)
    fig.subplots_adjust(top=0.8, bottom=0.12, left=0.09, right=0.99)
    st.headline(fig, f"2023 stands alone: {y.iloc[0] / y.iloc[1]:.1f}x the next-worst year, "
                f"{y.iloc[0] / med:.0f}x a typical one",
                "Area burned each year since complete reporting began, ranked. Red: 2023. Black: 2025.", y=0.995)
    st.source_note(fig)
    return fig, dict(median_mha=med / 1e6, ratio_next=y.iloc[0] / y.iloc[1], ratio_median=y.iloc[0] / med,
                     rank_2025=int(list(y.index).index(2025)) + 1, top6=list(y.head(6).index))


def fig13_cause_share_province(df):
    """Q2 - share of fires vs share of area by cause, Canada and each province."""
    d = df[df.province.notna()]
    big = d.province.value_counts()
    keep = big[big >= 1000].index
    d = d[d.province.isin(keep)]
    fires = pd.crosstab(d.province, d.cause, normalize="index").reindex(columns=fd.CAUSE_ORDER)
    area = (d.pivot_table(index="province", columns="cause", values="SIZE_HA", aggfunc="sum",
                          observed=True).reindex(columns=fd.CAUSE_ORDER).fillna(0))
    area = area.div(area.sum(axis=1), axis=0)
    can_f = df.cause.value_counts(normalize=True).reindex(fd.CAUSE_ORDER)
    can_a = df.groupby("cause", observed=True).SIZE_HA.sum().reindex(fd.CAUSE_ORDER)
    can_a = can_a / can_a.sum()
    order = area["Lightning"].sort_values().index                  # bottom -> top
    fires = pd.concat([fires.loc[order], can_f.to_frame("Canada").T])
    area = pd.concat([area.loc[order], can_a.to_frame("Canada").T])
    fig, axes = plt.subplots(1, 2, figsize=(st.TEXT_WIDTH, 3.6), sharey=True,
                             gridspec_kw={"wspace": 0.12})
    for ax, data, title in ((axes[0], fires, "Share of fires"), (axes[1], area, "Share of area burned")):
        left = np.zeros(len(data))
        for cause in fd.CAUSE_ORDER:
            v = data[cause].fillna(0).to_numpy()
            ax.barh(range(len(data)), v, left=left, color=st.CAUSE_COLORS[cause], height=0.7,
                    edgecolor="white", linewidth=0.8)
            for i, (l, w) in enumerate(zip(left, v)):
                if cause == "Lightning" and w >= 0.12:
                    ax.text(l + 0.015, i, f"{w:.0%}", va="center", fontsize=6.6, color="white",
                            fontweight="bold")
            left += v
        ax.set_xlim(0, 1)
        ax.xaxis.set_major_formatter(mticker.PercentFormatter(1, decimals=0))
        ax.set_xticks([0, 0.5, 1])
        ax.set_title(title, fontsize=8.5, fontweight="bold", loc="left", pad=4)
        ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False)
        ax.axhline(len(data) - 1.5, color=st.INK, lw=0.6)
    axes[0].set_yticks(range(len(fires)), [str(i) for i in fires.index])
    axes[0].get_yticklabels()[-1].set_fontweight("bold")
    kx = 0.0
    for cause in fd.CAUSE_ORDER:
        fig.add_artist(plt.Rectangle((0.2 + kx, 0.835), 0.012, 0.024, fc=st.CAUSE_COLORS[cause], ec="none",
                                     transform=fig.transFigure))
        fig.text(0.2 + kx + 0.018, 0.847, cause, fontsize=7.8, va="center")
        kx += 0.13
    fig.subplots_adjust(top=0.76, bottom=0.08, left=0.2, right=0.98)
    st.headline(fig, "Outside the Maritimes, lightning's share of area beats its share of fires by 17–68 points",
                "Cause shares by province or territory (over 1,000 fires), sorted by lightning's share "
                "of area. Labels: lightning share.", y=0.995)
    st.source_note(fig)
    gap = (area["Lightning"] - fires["Lightning"]).drop("Canada")
    return fig, dict(gap_min=gap.min(), gap_max=gap.max(), widest=gap.idxmax(),
                     canada=dict(fires=can_f.round(3).to_dict(), area=can_a.round(3).to_dict()))


def fig14_concentration_curve(df):
    """Q3 - fires ranked largest first vs cumulative share of area burned."""
    s = df.loc[df.SIZE_HA > 0, "SIZE_HA"].sort_values(ascending=False).to_numpy()
    cum = np.cumsum(s) / s.sum()
    x = np.arange(1, len(s) + 1) / len(s)
    n_half = int(np.searchsorted(cum, 0.5)) + 1
    top1 = cum[int(len(s) * 0.01) - 1]
    n200 = int((s >= 200).sum())
    fig, ax = plt.subplots(figsize=(st.TEXT_WIDTH, 3.0))
    ax.plot(x * 100, cum * 100, color=st.EMBER, lw=2.0)
    ax.set_xscale("log")
    ax.set_xlim(1e-4 * 100 / 1, 100)
    ax.set_ylim(0, 101)
    for xv, yv, lab, dx in ((n_half / len(s), 0.5, f"{n_half:,} fires ({n_half / len(s):.2%})\nburned half of all area", 2.0),
                            (0.01, top1, f"Largest 1%: {top1:.0%} of area", 0.5),
                            (n200 / len(s), cum[n200 - 1], f"Fires of 200 ha+ ({n200 / len(s):.1%}):\n{cum[n200 - 1]:.1%} of area", 1.0)):
        ax.scatter([xv * 100], [yv * 100], s=26, color=st.EMBER, edgecolor="white", lw=1, zorder=4)
        ax.annotate(lab, xy=(xv * 100, yv * 100), xytext=(xv * 100 * (0.18 if dx < 1 else (2.2 if dx == 1.0 else 6)), yv * 100 - (14 if dx < 1 else (22 if dx == 1.0 else 18))),
                    fontsize=7.3, color=st.INK, ha="right" if dx < 1 else "left", va="center",
                    arrowprops=dict(arrowstyle="-", color=st.INK, lw=0.6, shrinkB=3))
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:g}%"))
    ax.set_xticks([0.01, 0.1, 1, 10, 100])
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(100, decimals=0))
    ax.yaxis.grid(True); ax.set_axisbelow(True)
    ax.set_xlabel("Share of fires, ranked from largest (log scale)")
    ax.set_ylabel("Cumulative share of area")
    fig.subplots_adjust(top=0.8, bottom=0.16, left=0.1, right=0.98)
    st.headline(fig, f"Just {n_half:,} fires burned half of all the land burned since 1950",
                f"Fires with a recorded size (n = {len(s):,}), largest first, against the share of all "
                "hectares they burned.", y=0.995)
    st.source_note(fig)
    return fig, dict(n_half=n_half, share_half=n_half / len(s), top1=top1, n200=n200,
                     share200=cum[n200 - 1])


def fig15_decade_small_multiples(df):
    """Q4 - one burn-scar map per decade, same extent, with area per year."""
    prov, scars = _load_geo()
    scars["dec"] = (scars.YEAR // 10) * 10
    cen = scar_centres(scars)
    decades = [1970, 1980, 1990, 2000, 2010, 2020]
    ramp = sns.color_palette("rocket_r", 9)[1:7]
    span = {1970: "1972–79", 2020: "2020–24"}
    fig, axes = plt.subplots(2, 3, figsize=(st.TEXT_WIDTH, 3.9))
    for ax, dec, col in zip(axes.flat, decades, ramp):
        _base_map(ax, prov, top=0.78)
        scars[scars.dec == dec].plot(ax=ax, color=st.EMBER, linewidth=0, zorder=1)
        r = cen.loc[dec]
        ax.scatter([r.x], [r.y], s=18, color=st.INK, edgecolor="white", lw=0.8, zorder=4)
        ax.set_title(f"{dec}s" if dec not in span else span[dec], fontsize=8, fontweight="bold",
                     loc="left", pad=1)
        ax.text(0.99, 1.02, f"{r.mha_per_year:.1f} Mha/yr", transform=ax.transAxes, ha="right",
                va="bottom", fontsize=7, color=st.MUTED)
    fig.subplots_adjust(top=0.8, bottom=0.06, left=0.0, right=1.0, wspace=0.03, hspace=0.16)
    st.headline(fig, "Every decade burns the same belt; the 2020s burned it twice as hard",
                "Mapped burn perimeters by decade, same extent. Dot: area-weighted centre of burning. "
                "Right: mapped area per year.", y=0.995)
    st.source_note(fig, "Source: CNFDB burned-area polygons, NRCan; provinces: Natural Earth.")
    return fig, dict(mha_per_year=cen.mha_per_year.round(2).to_dict())


def fig16_coverage(df):
    """Method - which agency reported fires in which year (reporting coverage)."""
    from matplotlib.colors import LogNorm
    names = {k: fd.AGENCY_SHORT[k] for k in fd.AGENCY_SHORT}
    g = df.groupby(["agency", "YEAR"]).size().unstack(fill_value=0)
    g = g.reindex(columns=range(fd.FIRST_YEAR, fd.LAST_YEAR + 1), fill_value=0)
    first = g.gt(0).idxmax(axis=1).sort_values(kind="stable")
    g = g.loc[first.index]
    vals = g.to_numpy().astype(float); vals[vals == 0] = np.nan
    cmap = sns.color_palette(st.FIRE_CMAP, as_cmap=True).copy(); cmap.set_bad("white")
    fig, ax = plt.subplots(figsize=(st.TEXT_WIDTH, 3.0))
    m = ax.pcolormesh(np.arange(fd.FIRST_YEAR, fd.LAST_YEAR + 2) - 0.5, np.arange(len(g) + 1) - 0.5, vals,
                      cmap=cmap, norm=LogNorm(1, np.nanmax(vals)), edgecolors="white", linewidth=0.3)
    ax.set_yticks(range(len(g)), [names[a] for a in g.index], fontsize=7.2)
    ax.invert_yaxis()
    ax.axvline(fd.FULL_REPORTING_FROM - 0.5, color=st.INK, lw=0.8)
    ax.text(fd.FULL_REPORTING_FROM - 1.5, 10.5, "Trend tests start\nhere (1980) →", fontsize=7, va="center",
            ha="right", color=st.INK)
    ax.tick_params(length=0)
    for s_ in ax.spines.values(): s_.set_visible(False)
    cax = fig.add_axes([0.62, 0.86, 0.3, 0.025])
    cb = fig.colorbar(m, cax=cax, orientation="horizontal")
    cb.outline.set_visible(False); cb.ax.tick_params(labelsize=6.5, length=0, pad=1)
    cb.ax.set_title("Fires reported (log scale)", fontsize=6.8, color=st.MUTED, loc="left", pad=2)
    fig.subplots_adjust(top=0.78, bottom=0.08, left=0.2, right=0.99)
    st.headline(fig, "Most agencies report from 1959; New Brunswick from 1980, PEI from 2018",
                "Fires reported per agency per year. Blank: no records.", y=0.995)
    st.source_note(fig)
    return fig, dict(first_year={names[a]: int(y) for a, y in first.items()})


# --------------------------------------------------------------------------
# Gallery: the same data, drawn to be seen (artistic but exact)
# --------------------------------------------------------------------------
def stripe_colors(df, theme="light"):
    """One colour per year for area burned (sequential, square-root scale)."""
    from matplotlib.colors import PowerNorm, to_hex
    y = fd.yearly(df).area_ha
    cmap = sns.color_palette("rocket_r" if theme == "light" else "inferno", as_cmap=True)
    norm = PowerNorm(0.5, vmin=0, vmax=y.max())
    lo = 0.0 if theme == "light" else 0.08                  # dark theme: keep the low end visible
    return y, [to_hex(cmap(lo + (1 - lo) * norm(v))) for v in y]


def fig17_fire_stripes(df):
    """Gallery A - one stripe per year, coloured by area burned (warming-stripes style)."""
    y, cols = stripe_colors(df)
    fig = plt.figure(figsize=(st.TEXT_WIDTH, 2.3))
    ax = fig.add_axes([0, 0.16, 1, 0.6])
    for i, c in enumerate(cols):
        ax.add_patch(plt.Rectangle((i, 0), 1.0, 1, fc=c, ec=c, lw=0.2))
    ax.set_xlim(0, len(cols)); ax.set_ylim(0, 1); ax.axis("off")
    for yr in (1950, 1980, 2000, 2023):
        i = yr - fd.FIRST_YEAR
        ax.text(i + 0.5, -0.06, str(yr), ha="center", va="top", fontsize=7,
                color=st.INK, fontweight="bold" if yr == 2023 else "normal")
    st.headline(fig, "Seventy-six years of Canadian wildfire, one stripe per year",
                "Each stripe is one year, 1950–2025, coloured by hectares burned (square-root scale; "
                "darkest = 2023, 17.6 million ha).", y=0.995)
    st.source_note(fig)
    return fig, dict(max_year=int(y.idxmax()))


def fire_rings_grid(df, bins=52):
    """Area burned per (year, week-of-year) from fires with a full start date."""
    d = df[(df.MONTH > 0) & (df.DAY > 0)]
    doy = pd.to_datetime(dict(year=d.YEAR, month=d.MONTH, day=d.DAY), errors="coerce").dt.dayofyear
    d = d.assign(w=np.minimum(((doy - 1) // 7).fillna(-1).astype(int), bins - 1))
    d = d[d.w >= 0]
    g = d.pivot_table(index="YEAR", columns="w", values="SIZE_HA", aggfunc="sum")
    return g.reindex(index=range(fd.FIRST_YEAR, fd.LAST_YEAR + 1), columns=range(bins)).fillna(0)


def fig18_fire_rings(df, theme="light", bare=False):
    """Gallery B - each year a tree ring (1950 at the centre), each week a sector."""
    from matplotlib.colors import PowerNorm
    g = fire_rings_grid(df)
    vals = g.to_numpy().copy(); vals[vals < 50] = np.nan
    bg = "white" if theme == "light" else "#0E0B09"
    ink = st.INK if theme == "light" else "#EEE8E1"
    if theme == "light":
        cmap = sns.color_palette("rocket_r", as_cmap=True).copy()
    else:                                                       # skip inferno's near-black low end
        from matplotlib.colors import ListedColormap
        cmap = ListedColormap(plt.get_cmap("inferno")(np.linspace(0.18, 1, 256)))
    cmap.set_bad((0, 0, 0, 0) if bare else bg)
    theta = np.linspace(0, 2 * np.pi, g.shape[1] + 1)
    r = np.arange(g.shape[0] + 1) + 18                        # hollow centre
    fig = plt.figure(figsize=(st.TEXT_WIDTH, st.TEXT_WIDTH if bare else 6.0), facecolor="none" if bare else bg)
    ax = fig.add_axes([0.07, 0.07, 0.86, 0.86] if bare else [0.09, 0.075, 0.82, 0.76], projection="polar",
                      facecolor="none" if bare else bg)
    ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
    ax.pcolormesh(theta, r, vals, cmap=cmap, norm=PowerNorm(0.4, vmin=0, vmax=np.nanmax(vals)),
                  shading="flat")
    i23 = 2023 - fd.FIRST_YEAR
    ax.plot(np.linspace(0, 2 * np.pi, 300), [r[i23] - 0.15] * 300, color=ink, lw=0.5)
    ax.plot(np.linspace(0, 2 * np.pi, 300), [r[i23 + 1] + 0.15] * 300, color=ink, lw=0.5)
    ax.set_ylim(0, r[-1] + 1)
    ax.set_yticks([]); ax.grid(False); ax.spines["polar"].set_visible(False)
    month_starts = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    ax.set_xticks([2 * np.pi * m / 365 for m in month_starts],
                  ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                  fontsize=7.5, color=ink)
    ax.tick_params(axis="x", pad=2)
    for yr in (1950, 1980, 2000):
        ax.text(np.deg2rad(-14), r[yr - fd.FIRST_YEAR] + 0.5, str(yr), fontsize=6.3, color=ink,
                ha="center", va="center", alpha=0.8)
    ax.annotate("2023", xy=(np.deg2rad(140), r[i23] + 0.5), xytext=(np.deg2rad(128), r[-1] + 9),
                fontsize=7.5, color=ink, fontweight="bold", ha="center",
                arrowprops=dict(arrowstyle="-", color=ink, lw=0.6))
    if bare:
        return fig, dict(peak_week=int(g.sum().idxmax()))
    fig.text(0.0, 0.995, "Fire rings: every week of every season since 1950", ha="left", va="top",
             fontsize=10.5, fontweight="bold", color=ink)
    fig.text(0.0, 0.965, "One ring per year (1950 at the centre, 2025 outside), one sector per week; "
             "colour = hectares burned by fires\nthat started that week (compressed scale, darker = more). "
             "Blank: under 50 ha.", ha="left", va="top", fontsize=8, color=ink, alpha=0.75)
    fig.text(0.0, 0.0, st.SOURCE + ". Fires with a full start date.", fontsize=6.8, color=ink, alpha=0.7)
    return fig, dict(peak_week=int(g.sum().idxmax()))


def fig19_ember_field(df, bare=False):
    """Gallery C - all 448k fire starts as embers on a night map; size and glow by fire size."""
    from pyproj import Transformer
    prov, _ = _load_geo()
    tr = Transformer.from_crs(4326, prov.crs, always_xy=True)
    d = df[df.LATITUDE.notna()].sort_values("SIZE_HA")       # biggest drawn last, on top
    x, y = tr.transform(d.LONGITUDE.to_numpy(), d.LATITUDE.to_numpy())
    lg = np.log10(d.SIZE_HA.clip(0.01, 1e6).to_numpy())       # -2 .. 6
    k = (lg + 2) / 8
    cmap = plt.get_cmap("inferno")
    fig = plt.figure(figsize=(st.TEXT_WIDTH, 4.6), facecolor="#0E0B09")
    if bare:
        fig.set_size_inches(st.TEXT_WIDTH, 4.0)
    ax = fig.add_axes([0, 0, 1, 1] if bare else [0, 0.03, 1, 0.84], facecolor="#0E0B09")
    prov.plot(ax=ax, color="#1A1512", edgecolor="#2A231E", linewidth=0.4, zorder=0)
    big = k > 0.55
    ax.scatter(x[big], y[big], s=(k[big] * 9) ** 2, color=cmap(0.85), alpha=0.06, linewidths=0,
               zorder=1, rasterized=True)                     # glow halo around large fires
    ax.scatter(x, y, s=0.4 + 5 * k ** 3, c=cmap(0.25 + 0.75 * k), alpha=0.55, linewidths=0,
               zorder=2, rasterized=True)
    ax.set_axis_off(); ax.set_aspect("equal")
    x0, y0, x1, y1 = prov.total_bounds
    ax.set_xlim(x0 + 0.02 * (x1 - x0), x1 - 0.04 * (x1 - x0)); ax.set_ylim(y0, y0 + 0.75 * (y1 - y0))
    if bare:
        return fig, dict(n=len(d))
    fig.text(0.0, 0.995, f"Ember field: all {len(d):,} fire starts, 1950–2025", ha="left", va="top",
             fontsize=10.5, fontweight="bold", color="#EEE8E1")
    fig.text(0.0, 0.955, "Each point is one fire. Bigger and brighter = larger final size "
             "(log scale); the largest fires glow.", ha="left", va="top", fontsize=8,
             color="#A69D93")
    fig.text(0.0, 0.0, st.SOURCE + ". Provinces: Natural Earth.", fontsize=6.8, color="#A69D93")
    return fig, dict(n=len(d))


ALL = {"fig1_trend": fig1_trend, "fig2_season_heatmap": fig2_season_heatmap,
       "fig9_burn_scars": fig9_burn_scars, "fig10_ignition_maps": fig10_ignition_maps,
       "fig7_size_histogram": fig7_size_histogram, "fig8_boxen_decade": fig8_boxen_decade,
       "fig3_treemap_2023": fig3_treemap_2023, "fig4_waffle_cause": fig4_waffle_cause,
       "fig5_radar_season": fig5_radar_season, "fig6_region_cause": fig6_region_cause,
       "fig11_burn_rate_map": fig11_burn_rate_map, "fig12_ranked_years": fig12_ranked_years,
       "fig13_cause_share_province": fig13_cause_share_province,
       "fig14_concentration_curve": fig14_concentration_curve,
       "fig15_decade_small_multiples": fig15_decade_small_multiples, "fig16_coverage": fig16_coverage,
       "fig17_fire_stripes": fig17_fire_stripes, "fig18_fire_rings": fig18_fire_rings,
       "fig19_ember_field": fig19_ember_field}


if __name__ == "__main__":
    import sys
    st.apply()
    df = fd.load_fires()
    names = sys.argv[1:] or list(ALL)
    for n in names:
        fig, facts = ALL[n](df)
        st.save(fig, n)
        plt.close(fig)
        print(n, {k: (round(v, 2) if isinstance(v, float) else v) for k, v in facts.items()})
