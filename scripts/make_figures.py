"""Draw the README figures from the notebook's own engine.

The script runs rolling_mill_pass_simulation.ipynb headlessly, so every number it draws comes out of
the model the notebook ships, and writes four PNGs into figures/:

    fig_schedule.png       exit gauge, reduction, temperature, roll force, power, torque
    fig_bite.png           the friction hill of the heaviest pass, and the pressure against the
                           classical bounds for every pass
    fig_penetration.png    how far the strain reaches through the thickness, pass by pass
    fig_microstructure.png grain size and the softening verdict at three depths

Run it from the repository root or anywhere else: paths are taken from this file.
"""
import json
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import plotly.graph_objects as go  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "rolling_mill_pass_simulation.ipynb"
FIGURES = ROOT / "figures"


def run_notebook():
    """Execute every code cell in one namespace, with the display calls turned off.

    This is the notebook's own engine, so the figures cannot drift from the model. The cells that
    draw the notebook's animations still run; their embedded output is what the script discards.
    """
    cells = [c for c in json.loads(NOTEBOOK.read_text(encoding="utf-8"))["cells"]
             if c["cell_type"] == "code"]
    ns = {"__name__": "__main__"}
    plt.show = lambda *a, **k: None
    go.Figure.show = lambda *a, **k: None
    for i, c in enumerate(cells):
        ns["display"] = lambda *a, **k: None
        exec(compile("".join(c["source"]), f"cell_{i:03d}", "exec"), ns)
    return ns


def fig_schedule(ns):
    """What the schedule asks of the mill: gauge, reduction, temperature, force, power, torque."""
    PS, PR, G, CM, N = ns["PS"], ns["PR"], ns["G"], ns["CM"], ns["N"]
    ACCENT, MUTED, INK, PAL = ns["ACCENT"], ns["MUTED"], ns["INK"], ns["PALETTE"]
    k = np.arange(1, N + 1)
    h_out = np.array([p["hf"] for p in PS])
    red = np.array([100 * p["dh"] / p["h0"] for p in PS])
    T_in = np.array([G.mean(pr["TLin"])[CM] for pr in PR])
    T_out = np.array([G.mean(pr["oL"]["T"])[CM] for pr in PR])
    F = np.array([pr["FL"][CM] for pr in PR])
    band = np.array([[pr["FL"].min(), pr["FL"].max()] for pr in PR])
    pw = np.array([pr["power"] for pr in PR]) / 1e3
    tq = np.array([pr["torque"] for pr in PR]) / 1e3

    fig, axs = plt.subplots(2, 2, figsize=(12.0, 7.4), constrained_layout=True)

    a = axs[0, 0]
    a.bar(k, red, color=MUTED, width=0.6, zorder=2)
    a.set_ylim(0, red.max() * 1.3)
    a.set_ylabel("reduction this pass (%)")
    for x, y in zip(k, red):
        a.text(x, y + 0.4, f"{y:.0f}", ha="center", fontsize=9, color=INK)
    twin = a.twinx()
    twin.plot(k, h_out, "o-", color=INK, lw=2, zorder=3)
    twin.set_ylim(24, 84)
    twin.set_yticks(np.arange(30, 81, 10))
    twin.set_ylabel("exit thickness (mm)")
    twin.grid(False)
    a.set_xticks(k)
    a.set_title("Gauge and reduction")

    a = axs[0, 1]
    a.plot(k, T_in, "o-", color=PAL[0], lw=2, label="entry, section mean")
    a.plot(k, T_out, "s--", color=ACCENT, lw=2, label="exit, section mean")
    a.axhline(ns["TNR"], color=INK, lw=1.2, ls=":")
    a.text(k[-1], ns["TNR"] + 4, f"Tnr {ns['TNR']:.0f} C", ha="right", fontsize=9, color=INK)
    a.set_ylabel("temperature (C)")
    a.set_xticks(k)
    a.legend(frameon=False, fontsize=9)
    a.set_title("Interpass temperature")

    a = axs[1, 0]
    a.fill_between(k, band[:, 0], band[:, 1], color=MUTED, alpha=0.28, lw=0,
                   label="head to tail spread")
    a.plot(k, F, "o-", color=PAL[0], lw=2, label="mid-length force")
    a.set_ylabel("roll force (MT)")
    a.set_xticks(k)
    a.legend(frameon=False, fontsize=9)
    a.set_title("Roll separating force")

    a = axs[1, 1]
    a.bar(k, pw, color=PAL[2], width=0.6, zorder=2)
    a.set_ylabel("drive power (MW)")
    a.set_xticks(k)
    twin = a.twinx()
    twin.plot(k, tq, "o-", color=ACCENT, lw=2)
    twin.set_ylabel("torque (kNm)")
    twin.grid(False)
    a.set_title("Drive power and torque")

    for a in axs.ravel():
        a.set_xlabel("pass")
    fig.savefig(FIGURES / "fig_schedule.png", dpi=130)
    plt.close(fig)


def fig_bite(ns):
    """The friction hill and the pressure level against the classical constant flow stress bounds."""
    PS, PR, G, CM, CHK, P = ns["PS"], ns["PR"], ns["G"], ns["CM"], ns["CHK"], ns["P"]
    ACCENT, MUTED, INK, PAL = ns["ACCENT"], ns["MUTED"], ns["INK"], ns["PALETTE"]
    k_heavy = int(np.argmax([pr["FL"][CM] for pr in PR]))
    ps, pr = PS[k_heavy], PR[k_heavy]
    x = ps["geo"]["x"]
    u = x[0] - x                                   # distance from first contact, mm
    p, kp = pr["oL"]["p"][CM], pr["oL"]["kp"][CM]
    un = x[0] - float(pr["oL"]["nn_x"][CM])        # neutral point, same axis

    fig, axs = plt.subplots(1, 2, figsize=(12.0, 4.6), constrained_layout=True)

    a = axs[0]
    a.plot(u, p, color=PAL[0], lw=2.4, label="roll pressure")
    a.plot(u, kp, color=ACCENT, lw=2, ls="--", label="plane strain yield")
    a.axvline(un, color=INK, lw=1.2, ls=":")
    a.text(un - 2, a.get_ylim()[1] * 0.92, "neutral point", ha="right", fontsize=9, color=INK)
    a.annotate("entry", xy=(u[0], p[0]), xytext=(6, 12), textcoords="offset points", fontsize=9)
    a.annotate("exit", xy=(u[-1], p[-1]), xytext=(-22, 14), textcoords="offset points", fontsize=9)
    a.set_xlabel("distance from first contact (mm)")
    a.set_ylabel("stress (MPa)")
    a.legend(frameon=False, fontsize=9)
    a.set_title(f"Friction hill, pass {k_heavy + 1}")

    a = axs[1]
    k = np.arange(1, len(CHK) + 1)
    a.bar(k, CHK["p_bar_over_2k"], color=MUTED, width=0.6, zorder=2,
          label="model mean pressure")
    a.plot(k, CHK["sliding_bound"], "o-", color=PAL[0], lw=2, label="sliding bound")
    a.plot(k, CHK["sticking_bound"], "s--", color=ACCENT, lw=2, label="sticking bound")
    a.set_ylim(0, CHK["sticking_bound"].max() * 1.15)
    a.set_xticks(k)
    a.set_xlabel("pass")
    a.set_ylabel("mean pressure / plane strain yield")
    a.legend(frameon=False, fontsize=9)
    a.set_title("Pressure against the classical bounds")

    fig.savefig(FIGURES / "fig_bite.png", dpi=130)
    plt.close(fig)


def fig_penetration(ns):
    """How far the deformation front reaches, for the heaviest and the lightest pass alike."""
    PS, PR, G, CM, N, PEN = ns["PS"], ns["PR"], ns["G"], ns["CM"], ns["N"], ns["PEN"]
    ACCENT, MUTED, INK, PAL = ns["ACCENT"], ns["MUTED"], ns["INK"], ns["PALETTE"]
    k = np.arange(1, N + 1)
    cr = np.array(ns["cr"])

    fig, axs = plt.subplots(1, 2, figsize=(12.0, 4.6), constrained_layout=True)

    a = axs[0]
    for i in range(N):
        pen = PEN[i]
        frac = np.arange(len(pen)) / (len(pen) - 1)      # position along the arc dealt with
        a.plot(frac, pen, color=PAL[i % len(PAL)], lw=1.8, label=f"P{i + 1}")
    a.set_xlim(0, 1.0)
    a.set_ylim(0, 1.05)
    a.set_xlabel("fraction of the pass arc travelled")
    a.set_ylabel("penetration through the thickness")
    a.legend(frameon=False, fontsize=8, ncol=4, loc="lower right", columnspacing=0.9,
             handlelength=1.4)
    a.set_title("Deformation front through the bite")

    a = axs[1]
    a.bar(k, cr, color=MUTED, width=0.6, zorder=2)
    a.axhline(cr.mean(), color=ACCENT, lw=1.6, ls="--")
    a.text(k[0], cr.mean() + 0.01, f"schedule mean {cr.mean():.2f}", fontsize=9, color=ACCENT)
    a.set_ylim(0, 1.08)
    a.set_xticks(k)
    a.set_xlabel("pass")
    a.set_ylabel("core strain / surface strain")
    a.set_title("Strain that reaches the core")

    fig.savefig(FIGURES / "fig_penetration.png", dpi=130)
    plt.close(fig)


def fig_microstructure(ns):
    """What the austenite does between the passes: grain size and the softening verdict."""
    N, RXT, d_all, TNR = ns["N"], ns["RXT"], ns["d_all"], ns["TNR"]
    ACCENT, MUTED, INK, PAL = ns["ACCENT"], ns["MUTED"], ns["INK"], ns["PALETTE"]
    k = np.arange(1, N + 1)
    dep = ["surface", "quarter", "core"]

    fig, axs = plt.subplots(1, 2, figsize=(12.0, 4.6), constrained_layout=True)

    a = axs[0]
    for j, nm in enumerate(dep):
        a.plot(k, d_all[:, j], "o-", color=PAL[j], lw=2, label=nm)
    a.annotate(f"initial grain {d_all[0, 0]:.0f} um", xy=(1, d_all[0, 0]),
               xytext=(14, -18), textcoords="offset points", fontsize=9, color=INK)
    a.set_ylabel("austenite grain size (um)")
    a.set_xticks(k)
    a.set_xlabel("pass")
    a.legend(frameon=False, fontsize=9)
    a.set_title("Grain size at three depths")

    a = axs[1]
    regs = ["SRX", "PRX", "NRX"]                       # fully, partly, not softened
    cols = [PAL[2], PAL[1], PAL[0]]
    counts = np.array([[int(((RXT.loc[k_]["regime"].str.endswith(r)).sum())
                            if k_ in RXT.index else 0) for r in regs] for k_ in k])
    bottom = np.zeros(N)
    for j, (r, c) in enumerate(zip(regs, cols)):
        a.bar(k, counts[:, j], bottom=bottom, color=c, width=0.6, label=r, zorder=2)
        bottom += counts[:, j]
    a.set_ylim(0, 3.9)
    a.set_xticks(k)
    a.set_xlabel("pass")
    a.set_ylabel("depths with that verdict (of 3)")
    a.legend(frameon=False, fontsize=9, ncol=3, loc="upper center", columnspacing=1.4)
    a.set_title(f"Softening state after each pass, Tnr {TNR:.0f} C")

    fig.savefig(FIGURES / "fig_microstructure.png", dpi=130)
    plt.close(fig)


def main():
    FIGURES.mkdir(exist_ok=True)
    ns = run_notebook()
    fig_schedule(ns)
    fig_bite(ns)
    fig_penetration(ns)
    fig_microstructure(ns)
    for name in ("fig_schedule", "fig_bite", "fig_penetration", "fig_microstructure"):
        print(f"wrote figures/{name}.png")


if __name__ == "__main__":
    main()
