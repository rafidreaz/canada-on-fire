# Chart choices and justifications

The report's "why this chart" text comes from this file. For each figure it records what we chose, the alternatives we considered, why we rejected them (with lecture references) and the design decisions we made.

---

## Figure 1: Area burned vs number of fires (two-panel line chart)

**Chosen:** two stacked line charts sharing one time axis. Yearly totals are drawn in grey, with a bold trailing 10-year moving average.

**Why a line chart:** time has a meaningful order. Lecture 3 (p.3) says a line plot shows the trend of y over an ordered x, and the trend is the question (Q1).

**Alternatives considered:**
- **Bar chart of yearly area.** Bars suit comparing discrete categories (L3 p.14). With 76 bars the eye reads individual years, not the long-term trend, and a second series cannot share the axis cleanly.
- **One chart with two y-axes (area and count).** This was rejected because a dual axis lets the designer slide either line up or down and invent a "crossing" point, so the comparison it suggests is arbitrary. Two aligned panels with their own zero baselines keep both honest.
- **Scatter of area vs year with a fitted trend line (L3 p.13).** It is good for relationships but hides the year-to-year sequence that makes 2023 visible as a spike.

**Design decisions (L9 angle, frame and focus; L3 pp.4–6):**
- **Focus:** the context (yearly values) is grey, the signal (the moving average) is in colour, and the 2023 record is annotated in red with its multiple of the next-worst year. This follows the FT example in L3 p.4.
- **Evidence:** each panel carries a trend test over 1980–2025 (Kendall's τ, Theil–Sen slope with 95% CI). Fires fall significantly (−77 a year, p < 0.001); area burned does not (τ = 0.17, p = 0.10). The title was rewritten to claim only that: fewer fires, extreme worst seasons, with 2023 and 2025 (8.7 Mha, annotated) the two largest years.
- **Frame:** the years before 1980 are shaded as "incomplete reporting", because several agencies only report fully from the 1970s–80s. That keeps the early rise in fire counts from being misread as a real change.
- **Trailing rather than centred average:** a centred window needs future years, so its last five points would use a shrinking window. A trailing window is computed the same way for every year.
- **Labels and baselines:** labels sit directly on the lines instead of in a legend, both y-axes start at zero, and the wide aspect ratio avoids exaggerating the slope (L3 p.6).

---

## Figure 2: When the land burns (year x month heatmap)

**Chosen:** a heatmap with years as columns and months as rows. Colour shows the hectares burned in that month, on a sequential single-ramp scale (pale to dark).

**Why a heatmap:** we need to show two ordered dimensions at once (76 years x 8 months = 608 cells) on one page. A heatmap is the densest honest view of a grid of magnitudes. The instructor's own research figures in L1 use heatmaps with colour bars, and Plotly Express covers `density_heatmap`/`imshow` (L19).

**Alternatives considered:**
- **Small multiples of 76 monthly line charts:** each panel would be tiny, and the seasonal band would disappear.
- **Stacked bars per year, split by month:** every month after the first has a floating baseline, so its segments cannot be compared across years (L3 p.17 shows stacked bars working only for a few parts).
- **Radial (polar) season chart for every year:** these overlap into clutter, and rose charts make area grow with the square of the value (L11 p.9).

**Design decisions:**
- **Square-root colour scale, not linear or log.** A linear scale leaves all but a dozen cells pale. A log scale (first draft) turned almost every summer cell near-black and hid the extremes. Square root keeps zero at zero and stays monotonic, so the record months still stand out. The scale is stated on the colour bar.
- **One hue family from pale to dark** (sequential, never a rainbow). Cells under 100 ha are grey, so "almost nothing" reads differently from "small".
- **Frame:** only March–October are shown, since they hold 99.8% of the dated area. That is stated in the caption.
- **Focus:** the 2023 column is outlined, and its record May (6.5 Mha, ranked first of 76 Mays) is called out.

---

## Figure 3: 2023 by jurisdiction (treemap)

**Chosen:** a treemap of 2023's 17.6 Mha. Tile area is proportional to hectares. Fires are placed by the province or territory where they burned. The five jurisdictions over 1.5 Mha are filled in ember and the rest in neutral grey; the eight under 1 Mha are grouped as "Others" and named in a footnote. The title states the checked numbers (Quebec 4.29 and the NWT 4.25 Mha made up half the year).

**Why a treemap:** the question is part-to-whole ("how was 2023's total split?"). L8 recommends treemaps over sunbursts when there are many parts (p.14) and suggests highlighting particular tiles with colour (p.15). Area is proportional to value, with consistent scaling (p.17).

**Alternatives considered:**
- **Pie or donut:** 13 slices are unreadable, and angles are harder to judge than lengths or areas (L8 pp.4–5).
- **Ranked bar chart:** more precise for comparing values one against another. But the point here is the share of one year's total, and Figure 6 already uses ranked bars for the all-time comparison, so a different form avoids repeating it.
- **Choropleth of 2023:** larger provinces would look more important simply because of their size, not because of the hectares burned.

**Design decisions:** in an early draft the tiles were coloured by size, which repeated what area already showed (a value ramp on categories is an anti-pattern). Colour now carries only the focus (L9 p.24). Labels sit inside the tiles, and narrow tiles get wrapped labels.

---

## Figure 4: cause share of fires vs area (two waffle charts)

**Chosen:** two 10x10 waffle charts side by side. Each square is 1% of all fires (left) or of all hectares burned (right), coloured by cause, with large direct percentage labels.

**Why waffles:** the story is a contrast of two part-to-whole splits (54% of fires are human-caused but only 12% of the area). Waffles make percentages countable and always sum to 100 (L8 pp.18–19). We used largest-remainder rounding so that each grid holds exactly 100 squares (L8 p.3: parts must sum to 100%).

**Alternatives considered:**
- **Two pies:** comparing angles across two pies is weak (L8 p.4).
- **Grouped bars:** precise, but they lose the "share of a whole" reading.
- **Sankey from cause to size class:** considered and dropped at the design stage (L9 p.12, "learn to kill it"). It would need far more ink to say the same thing, and its many cause-to-size flows would cross (L10 p.6).

**Design decisions:** the squares are drawn directly in Matplotlib rather than through `pywaffle`, because pywaffle overrides the figure layout and the titles collided. Corners are slightly rounded and gaps are even. Unknown is grey on purpose, so it recedes.

---

## Figure 5: two fire seasons (radar chart)

**Chosen:** a radar (closed polar line) chart with one spoke per month. The radius is each cause's share of its own fires, with a reading guide and two headline numbers beside it.

**Why radar:** months are cyclic. December sits next to January, and a radar shows the shape of a season at a glance (L11 p.5). Normalising within each cause compares timing, not volume.

**Alternatives considered:**
- **Polar bar (rose) chart:** rejected because a rose chart's area grows with the square of the value, which exaggerates peaks (L11 pp.9, 12).
- **Grouped bar chart of 12 months:** accurate, but it breaks the cycle at December–January, and the two seasonal shapes are harder to see.
- **Line chart:** a valid alternative (L11 p.8 shows the same data as a line chart). We kept the radar because the cyclic shape is the message.

**Design decisions:** the loop is closed (L11 p.6). Lines and month markers carry the identity, with no filled area: a filled polygon's area grows with the square of the radius and depends on the neighbouring spokes, the same distortion we rejected the rose chart for. Unknown cause is omitted here and the subtitle says so. Direct peak annotations replace a legend, and the ring labels sit on the left of the spoke so they stay clear of the data.

---

## Figure 6: where each cause burns (ranked stacked horizontal bars)

**Chosen:** horizontal bars of total area by the province or territory where the fire burned (a spatial join, not the reporting agency, so Parks Canada fires count in their province), split by cause, ranked by total, starting at zero, with a direct total and a lightning-share label on each bar.

**Why:** we are comparing magnitudes across 13 categories, which is the bar chart's job (L3 p.14). Horizontal bars keep the long names readable, the ranking makes the order meaningful (L3 p.19), and the zero baseline keeps lengths honest (L3 p.18).

**Alternatives considered:**
- **Choropleth of totals:** big territories dominate visually just for being big. Figure 11 maps the normalised rate instead, and this chart keeps the exact totals.
- **Grouped bars by cause:** three bars x 13 agencies is cluttered.
- **100% stacked bars:** these would hide that the East barely burns at all.

---

## Figure 7: a few huge fires do almost all the burning (mirrored log histogram)

**Chosen:** a two-panel histogram on one log-scaled size axis, with the share of fires above and the share of area burned mirrored below. Bars at 200 ha or more are highlighted in ember.

**Why:** Q3 asks about the shape of the size distribution and where the area comes from. A histogram shows shape (L7 pp.3–5). Fire size spans eight orders of magnitude, so a log x-axis is needed. Mirroring two percentages on the same bins shows the counts and the area pulling apart. Both panels are percentages, so this is not a dual-axis chart.

**Alternatives considered:**
- **Linear histogram:** every fire falls in the first bin.
- **Cumulative-share (Lorenz-style) curve:** strong for the "1% to 85%" claim, but abstract for a general audience. We quote that figure in the text instead.
- **Box plot:** hides the bimodal count-vs-area shape.

**Denominator:** fires with a recorded size (408,419). The 40,028 fires recorded as 0 ha cannot sit on a log axis, so every percentage on this figure uses the same base, and the subtitle gives n.

**Design decisions:** the largest 1% of fires (83% of the area) is printed on the chart, so the concentration claim no longer needs a separate curve. Both panels use the same neutral grey, so only the 200 ha highlight carries meaning. The bins are aligned so that 200 ha (the CNFDB large-fire threshold) is a bin edge, and there are four bins per decade, which gives appropriate detail (L7 p.5). The spike at 0.1 ha is a reporting-precision artefact, and the caption says so.

---

## Figure 8: escaped lightning fires have grown since 1980 (boxen by decade)

**Chosen:** boxen (letter-value) plots of fire size per decade, split by cause, on a log axis, with the median of each lightning decade labelled. Only fires that grew to at least 1 ha are included.

**Why boxen:** the question is about both the typical fire and the tail. L12 p.10 says boxen plots convey more about the shape, "particularly in the TAILS". Box and violin plots are also good for comparing many categories (L7 pp.10, 14).

**Alternatives considered:**
- **Box plot:** it collapses the tail into whiskers and outliers, and with 100k+ points per group the outliers become a solid smear.
- **Violin:** the KDE is smoothed over a log scale with a heavy reporting spike at 0.1 ha, so the bandwidth choice would dominate the shape (L13 p.8).
- **Line of median by decade:** this drops the distribution entirely.

**Evidence, not eyeballing:** decade medians alone (39, 56, 12, 8, 6, 10, 23, 50 ha) are not monotonic, and quoting the 1990s low point against the 2020s would cherry-pick. The claim is therefore tested on yearly medians over 1980–2025, when reporting is complete: Spearman ρ = 0.68 (p < 0.001) for lightning, 0.66 with 2023 removed, and ρ = 0.28 (p = 0.06) for human fires. The result is printed on the figure, both causes' medians are labelled, and the 2020s are marked as a partial decade (2020–25). The website shows the same yearly medians as a line chart. Confounders (more remote fires left to burn, better satellite mapping) are named in the caption.

**Framing decision:** fires under 1 ha were removed. They are mostly recorded at a fixed 0.1 ha precision, and that pile-up distorted every box. Fires of 1 ha or more (28% of fires) are the ones that "escape", so the result answers a cleaner question. The years before 1980 are shaded as incomplete reporting.

---

## Figure 9: burn-scar map, 1972–2024 (GIS map of polygons)

**Chosen:** mapped perimeters of 15,578 fires drawn on Canada's provinces in a Lambert conformal conic projection, coloured by decade on a single sequential ramp. The newest decades are drawn on top.

**Why a map:** Q4 is about geography. A projected map is the only form that shows where the burn belt lies and how recent scars cluster. It extends the lectures' scatter plot of locations (L3) to real perimeters, and the colour follows sequential-palette practice (one hue, pale to dark).

**Alternatives considered:**
- **Choropleth by province:** throws away the within-province pattern, which is the whole point.
- **Hexbin density:** loses the actual fire shapes, which are the most striking and honest evidence.
- **Web Mercator projection:** inflates the North, so Lambert conformal conic (the national atlas standard) is used instead.

**Answering "have they shifted?":** newer scars drawn on top hide older ones, so the shift is measured, not left to the eye. Each decade's area-weighted centre of burning is drawn on the map as a dot in that decade's colour, joined in time order: it stays between 57.7 and 59.7°N (no northward move) but moves about 370 km west from the 1980s to the 2020s. An inset bar chart gives mapped area per year by decade, because the decades have different lengths (the 2020s hold five seasons); burning per year doubled in the 2020s. Province labels have a white halo, and there is a 500 km scale bar.

**Data handling:** the perimeters were simplified at 1 km tolerance for print. Scars smaller than about 1 km² disappear, but 99.06% of the mapped area is kept, and the subtitle says so. The fire-free high Arctic is cropped.

---

## Figure 10: where fires start, by cause (small-multiple dot maps)

**Chosen:** two dot maps side by side, one dot per fire start (195k lightning and 242k human), with a shared projection and extent.

**Why:** small multiples let the eye compare the two geographies directly. With tiny, translucent dots, the density itself draws the pattern: lightning across the boreal interior, human fires along roads, rivers and the populated south. This is a geographic scatter plot (L3 p.8), with transparency to manage overplotting (L12).

**Alternatives considered:**
- **One map with two colours:** the colours overplot and mix.
- **2D KDE contours (L13):** they smooth away the road and river corridors that explain human ignitions.
- **Choropleth of counts:** loses all the within-province detail.

---

## Figure 11: burning per unit of land (normalised choropleth)

**Chosen:** a choropleth of average hectares burned per 1,000 km² of land per year, 1980–2025, by the province or territory where the fires burned, in five binned classes of one sequential ramp, with every value printed on its region.

**Why:** Figure 6 ranks totals, which favour the largest territories. For a map, a rate is required: a choropleth of raw counts makes big regions look important only because they are big. Normalising by land area and by years changes the answer: Saskatchewan (935) burns hardest, then Manitoba and Alberta, and the NWT, first in total area, drops to fourth (531).

**Alternatives considered:**
- **Choropleth of totals:** misleading for the reason above.
- **Hexbin of burn rate:** finer detail, but provinces are the units agencies manage and readers know; Figure 10 already shows the detail inside provinces.
- **Normalising by forested area instead of land area:** fairer for Nunavut and the farmed south, but needs a forest-cover layer outside our data; the source line notes that land area includes tundra and farmland.

**Design decisions:** binned classes rather than a continuous ramp, so each region reads as one class; the lowest class has a visible tint so "low" is not confused with "no data"; values printed directly so no reader has to match shades to the legend.

