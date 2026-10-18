"""Draw the bite schematic for the README.

Geometry as named constants, taken from the model's own first pass, so the drawing can be checked
against the notebook inputs:

    work roll        diameter 1000 mm, flattened to 1021 mm by the roll force
    pass 1           entry 90 mm, exit 78 mm, draft 12 mm
    arc of contact   78 mm, bite angle 8.8 degrees
    friction         mu 0.3, neutral point at 44 per cent of the arc from the exit plane

The rolled radius is in the drawing because it is the radius the strip meets: Hitchcock flattening
adds 10.5 mm to the 500 mm radius on this pass. Run this file to rewrite figures/schematic_bite.png.
"""
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Polygon  # noqa: E402

ROLL_DIA_MM = 1000.0          # work roll diameter, the mill input
ROLL_DIA_FLAT_MM = 1021.1     # the same roll under the pass 1 load, Hitchcock flattening
ENTRY_MM = 90.0               # plate thickness entering the pass
EXIT_MM = 78.0                # plate thickness leaving it
ARC_MM = 78.0                 # arc of contact, from the flattened radius and the draft
BITE_DEG = 8.8                # bite angle, the half angle the roll spans
NEUTRAL_PCT = 44.0            # neutral point, per cent of the arc back from the exit plane
MU = 0.3
FIRST_CONTACT_C = 990.0

INK = "#222222"
STEEL = "#c8cdd2"
HOT = "#e69f00"
ACCENT = "#d55e00"
MUTED = "#9aa0a6"

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIGURES = ROOT / "figures"


def roll_surface(x, radius, gap):
    """Height of the roll surface above the pass line at position x, roll centre for a gap of hf."""
    yc = radius + gap / 2.0
    return yc - np.sqrt(np.maximum(radius**2 - x**2, 0.0))


def main():
    r_flat = ROLL_DIA_FLAT_MM / 2.0
    half_in, half_out = ENTRY_MM / 2.0, EXIT_MM / 2.0
    x_edge = 120.0
    y_frame = 112.0

    fig, ax = plt.subplots(figsize=(10.4, 5.4), constrained_layout=True)
    x = np.linspace(-x_edge, x_edge, 1200)

    for sign in (1, -1):
        ys = sign * roll_surface(x, r_flat, EXIT_MM)
        ax.fill_between(x, ys, ys - sign * 24, color=STEEL, alpha=0.55, lw=0, zorder=1)
        ax.plot(x, ys, color=INK, lw=1.4, zorder=3)

    plate = Polygon([(-x_edge, -half_in), (-ARC_MM, -half_in), (0.0, -half_out), (x_edge, -half_out),
                     (x_edge, half_out), (0.0, half_out), (-ARC_MM, half_in), (-x_edge, half_in)],
                    closed=True, facecolor=HOT, edgecolor=ACCENT, lw=1.2, alpha=0.85, zorder=4)
    ax.add_patch(plate)

    # the entry is on the left, the exit plane at x = 0, and the plate leaves at the exit gauge
    ax.annotate("", xy=(-x_edge - 8, -half_in), xytext=(-x_edge - 8, half_in),
                arrowprops=dict(arrowstyle="<->", color=INK, lw=1.1))
    ax.text(-x_edge - 14, 0, f"h0 {ENTRY_MM:.0f} mm", ha="right", va="center", fontsize=10)
    ax.annotate("", xy=(x_edge + 8, -half_out), xytext=(x_edge + 8, half_out),
                arrowprops=dict(arrowstyle="<->", color=INK, lw=1.1))
    ax.text(x_edge + 14, 0, f"hf {EXIT_MM:.0f} mm", ha="left", va="center", fontsize=10)

    y_arc = -half_out - 52
    ax.annotate("", xy=(0.0, y_arc), xytext=(-ARC_MM, y_arc),
                arrowprops=dict(arrowstyle="<->", color=INK, lw=1.1))
    ax.text(-ARC_MM / 2, y_arc - 6,
            f"arc of contact {ARC_MM:.0f} mm\ndraft {ENTRY_MM - EXIT_MM:.0f} mm, h0 {ENTRY_MM:.0f} "
            f"to hf {EXIT_MM:.0f} mm", ha="center", va="top", fontsize=10)

    x_n = -NEUTRAL_PCT / 100.0 * ARC_MM
    ax.plot([x_n, x_n], [-half_out - 2, half_in + 16], color=INK, lw=1.1, ls=":", zorder=5)
    ax.text(x_n, half_in + 19, f"neutral point\n{NEUTRAL_PCT:.0f}% of the arc", ha="center",
            va="bottom", fontsize=10)
    ax.plot([0.0, 0.0], [-half_out - 2, -half_out - 34], color=MUTED, lw=1.0, ls=":", zorder=5)
    ax.text(4, -half_out - 36, "exit plane", ha="left", va="top", fontsize=9, color=MUTED)

    ax.annotate(f"bite angle {BITE_DEG:.1f} deg", xy=(-ARC_MM + 2, half_in - 1), xytext=(-168, 88),
                fontsize=10, arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.0))
    ax.annotate(f"work rolls, dia {ROLL_DIA_MM:.0f} mm\nflattened to {ROLL_DIA_FLAT_MM:.0f} mm "
                f"under load\nboth rolls the same",
                xy=(88, roll_surface(np.array([88.0]), r_flat, EXIT_MM)[0]), xytext=(38, 84),
                fontsize=10, arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.0))
    ax.text(80, 0, f"plate at {FIRST_CONTACT_C:.0f} C", ha="center", va="center", fontsize=10)
    ax.text(80, -9, f"friction mu {MU}", ha="center", va="center", fontsize=9, color=INK)
    ax.annotate("bottom roll", xy=(110, -roll_surface(np.array([110.0]), r_flat, EXIT_MM)[0]),
                xytext=(140, -78), fontsize=10, ha="center",
                arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.0))

    ax.axhline(0, color=MUTED, lw=0.8, ls="-", zorder=2)
    ax.set_xlim(-190, 190)
    ax.set_ylim(-y_frame - 8, y_frame)
    ax.set_aspect("equal")
    ax.set_xlabel("rolling direction (mm), x = 0 at the exit plane")
    ax.set_yticks([])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.text(0.0, 1.015, "The bite of the first pass", transform=ax.transAxes, fontsize=13,
            fontweight="bold", color=INK, va="bottom")
    ax.text(0.0, -0.16, "drawn to scale in both directions; each roll extends far beyond the frame, "
                        "so only the crown is shown", transform=ax.transAxes, fontsize=8.5,
            color=MUTED, va="top")
    fig.savefig(FIGURES / "schematic_bite.png", dpi=130)
    plt.close(fig)
    print("wrote figures/schematic_bite.png")


if __name__ == "__main__":
    main()
