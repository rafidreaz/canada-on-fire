"""One visual system for every figure in the report.

Figures are drawn at their final printed size (LaTeX text width = 6.5 in),
so fonts in the PDF match the report exactly and nothing is rescaled.
"""
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

FIG_DIR = Path(__file__).resolve().parents[1] / "figures"

# ---- page geometry (inches) -------------------------------------------------
TEXT_WIDTH = 6.5
HALF_WIDTH = 3.15

# ---- palette ----------------------------------------------------------------
LIGHTNING = "#C77700"   # amber (passes 3:1 contrast + CVD checks)
HUMAN = "#1F5A99"       # deep blue
UNKNOWN = "#2E9E6E"     # green: third categorical slot (validated all-pairs with amber/blue)
CONTEXT = "#C9C9C9"     # de-emphasised marks
INK = "#222222"         # text and focal lines
MUTED = "#6B6B6B"       # secondary text
GRID = "#E6E6E6"
EMBER = "#B3261E"       # single accent for record / highlight
CAUSE_COLORS = {"Lightning": LIGHTNING, "Human": HUMAN, "Unknown": UNKNOWN}
FIRE_CMAP = "rocket_r"  # seaborn sequential: pale yellow -> deep red/black

SOURCE = "Source: Canadian National Fire Database (CNFDB), Natural Resources Canada"


FONT_DIR = Path(__file__).resolve().parents[1] / "assets" / "fonts"


def apply():
    """Set global Matplotlib defaults for the project.

    Inter (SIL Open Font Licence) ships inside the project so every machine
    renders identical figures, with real bold/semibold weights.
    """
    from matplotlib import font_manager
    for ttf in FONT_DIR.glob("Inter-*.ttf"):
        font_manager.fontManager.addfont(str(ttf))
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Inter", "DejaVu Sans"],
        "font.size": 8.5,
        "axes.titlesize": 10.5,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.titlepad": 14,
        "axes.labelsize": 8.5,
        "axes.labelcolor": INK,
        "axes.edgecolor": "#8A8A8A",
        "axes.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 3,
        "ytick.major.size": 3,
        "legend.frameon": False,
        "legend.fontsize": 8,
        "text.color": INK,
        "figure.dpi": 110,
        "savefig.dpi": 300,
        "pdf.fonttype": 42,      # embed TrueType so text stays selectable/sharp
        "axes.unicode_minus": True,
    })


def headline(fig, title, subtitle=None, x=0.0, y=1.0):
    """Finding-style title (bold) with an optional grey subtitle, figure-aligned."""
    fig.text(x, y, title, ha="left", va="top", fontsize=10.5, fontweight="bold", color=INK,
             transform=fig.transFigure)
    if subtitle:
        fig.text(x, y - 0.055 * (3.0 / fig.get_figheight()), subtitle, ha="left", va="top",
                 fontsize=8.5, color=MUTED, transform=fig.transFigure)


def source_note(fig, text=SOURCE, y=0.0):
    fig.text(0.0, y, text, ha="left", va="bottom", fontsize=6.8, color=MUTED,
             transform=fig.transFigure)


def save(fig, name):
    """Write vector PDF (for LaTeX) and a PNG preview with identical layout."""
    FIG_DIR.mkdir(exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(FIG_DIR / f"{name}.{ext}", bbox_inches="tight", pad_inches=0.04,
                    facecolor="white")
    return FIG_DIR / f"{name}.pdf"


def mha(x, _pos=None):
    """Axis formatter: hectares -> millions, no false rounding."""
    v = x / 1e6
    return "0" if not x else (f"{v:.0f}" if float(v).is_integer() else f"{v:.1f}")
