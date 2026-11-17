"""
README / write-up figures. Run from the repo root:  python3 scripts/make_figures.py
Writes PNGs into docs/img/.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

OUT = "docs/img"
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#a3a29c"
GRID = "#e6e5e0"
TRI = "#2a78d6"     # triangle isogrid, categorical slot 1
HEX = "#eb6834"     # hexagon honeycomb, categorical slot 2
SOLID = "#3d3c39"   # printed material in schematics

plt.rcParams.update({
    "font.family": ["Inter", "DejaVu Sans"],
    "font.size": 11,
    "text.color": INK,
    "axes.labelcolor": INK2,
    "axes.edgecolor": MUTED,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
})


def save(fig, name):
    fig.savefig(f"{OUT}/{name}", dpi=160, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    print("wrote", name)


def dim(ax, x0, y0, x1, y1, text, offset=(0, 0), color=INK2, **kw):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="<|-|>", mutation_scale=9,
                                 color=color, lw=0.9, shrinkA=0, shrinkB=0))
    ax.text((x0 + x1) / 2 + offset[0], (y0 + y1) / 2 + offset[1], text, color=color,
            ha="center", va="center", fontsize=10, **kw)


# ---------------------------------------------------------------- 1. beam renders
def beam_render():
    """Oblique (cabinet) projection of each extruded beam, built straight from the 2D section."""
    import sys
    sys.path.insert(0, "scripts")
    import infill_beams as ib

    inner = (ib.LENGTH - 2 * ib.SKIN) * (ib.DEPTH - 2 * ib.SKIN)
    target = ib.LENGTH * ib.DEPTH - inner + ib.CORE_DENSITY * inner
    picks = {"03_triangle_isogrid": ("Triangle isogrid", TRI), "04_hexagon_honeycomb": ("Hexagon honeycomb", HEX)}
    ang = np.radians(35)
    dvec = np.array([np.cos(ang), np.sin(ang)]) * ib.WIDTH * 0.55       # depth axis on paper

    fig, axes = plt.subplots(2, 1, figsize=(10, 4.9))
    for ax, (base, fn, label, k, period) in zip(axes, [g for g in ib.GEOMETRIES if g[0] in picks]):
        title, color = picks[base]
        size, phase, wall, sec = ib.layout(fn, k * ib.WALL / ib.CORE_DENSITY, period, target)
        rgb = np.array(matplotlib.colors.to_rgb(color))
        light = np.array([-0.5, 0.85]); light /= np.linalg.norm(light)
        quads = []
        for ring, is_hole in [(sec.exterior, False)] + [(r, True) for r in sec.interiors]:
            pts = np.array(ring.coords)
            ccw = ring.is_ccw
            for a, b in zip(pts[:-1], pts[1:]):
                e = b - a
                n = np.array([e[1], -e[0]]) if ccw else np.array([-e[1], e[0]])   # right-hand normal
                if is_hole:
                    n = -n
                n = n / (np.linalg.norm(n) + 1e-12)
                # n now points away from material (outward for exterior, into the hole for holes)
                if n @ dvec <= 0:
                    continue
                shade = 0.55 + 0.35 * max(0.0, n @ light)
                quads.append((np.array([a, b, b + dvec, a + dvec]), rgb * shade, 0 if is_hole else 1))
        quads.sort(key=lambda qc: qc[2])          # hole walls first, outer faces over them
        for q, c, _ in quads:
            ax.add_patch(Polygon(q, closed=True, facecolor=c, edgecolor=c, lw=0.3))
        verts, codes = [], []
        from matplotlib.path import Path
        from matplotlib.patches import PathPatch
        for ring in [sec.exterior, *sec.interiors]:
            xy = list(ring.coords)
            verts += xy
            codes += [Path.MOVETO] + [Path.LINETO] * (len(xy) - 2) + [Path.CLOSEPOLY]
        face = np.clip(rgb * 1.05 + 0.05, 0, 1)
        ax.add_patch(PathPatch(Path(verts, codes), facecolor=face, edgecolor=rgb * 0.7, lw=0.4))
        ax.set_xlim(-3, ib.LENGTH + dvec[0] + 3)
        ax.set_ylim(-3, ib.DEPTH + dvec[1] + 3)
        ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(title, loc="left", color=INK, fontsize=12)
    fig.text(0.01, 0.0, "200 x 25 x 25 mm, both 44.56 cm³ of plastic. Cells run straight through the 25 mm width.",
             color=INK2, fontsize=10)
    fig.tight_layout(h_pad=1.2)
    save(fig, "beam_render.png")


# ---------------------------------------------------------------- 2. test setup
def test_setup():
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.set_aspect("equal"); ax.axis("off")
    L, D, span, r = 200, 25, 180, 5
    x0 = 0
    # base / supports
    ax.add_patch(Rectangle((-15, -32), 230, 8, color=GRID, lw=0))
    for xs in (x0 + (L - span) / 2, x0 + (L + span) / 2):
        ax.add_patch(Polygon([(xs - 9, -24), (xs + 9, -24), (xs, -r)], closed=True, color=MUTED, lw=0))
        ax.add_patch(Circle((xs, -r), r, color=INK2, lw=0))
    # beam
    ax.add_patch(Rectangle((x0, 0), L, D, facecolor="#dfeafa", edgecolor=TRI, lw=1.6))
    ax.add_patch(Rectangle((x0, 0), L, 1.6, color=TRI, lw=0))
    ax.add_patch(Rectangle((x0, D - 1.6), L, 1.6, color=TRI, lw=0))
    ax.text(x0 + L / 2, D / 2, "lattice beam", ha="center", va="center", color=INK2, fontsize=10)
    # load rod + hanger
    xc = x0 + L / 2
    ax.add_patch(Circle((xc, D + r), r, color=INK2, lw=0))
    ax.plot([xc - 30, xc - 30, xc + 30, xc + 30], [D + 52, D + r, D + r, D + 52], color=INK2, lw=1.2)
    ax.plot([xc - 30, xc + 30], [D + 52, D + 52], color=INK2, lw=1.2)
    ax.plot([xc, xc], [D + 52, D + 64], color=INK2, lw=1.2)
    for i in range(3):
        ax.add_patch(Rectangle((xc - 14, D + 64 + 7 * i), 28, 6, facecolor=SOLID, lw=0))
    ax.text(xc + 22, D + 74, "masses added\nin equal steps", va="center", color=INK2, fontsize=10)
    ax.add_patch(FancyArrowPatch((xc - 48, D + 62), (xc - 48, D + 30), arrowstyle="-|>",
                                 mutation_scale=14, color=INK, lw=1.4))
    ax.text(xc - 52, D + 48, "P", ha="right", va="center", color=INK, fontsize=13, style="italic")
    # dial indicator under mid-span
    ax.add_patch(Rectangle((xc - 3, -22), 6, 10, color=INK2, lw=0))
    ax.plot([xc, xc], [-12, 0], color=INK2, lw=1.2)
    ax.text(xc + 8, -16, "dial indicator\n(mid-span deflection δ)", va="center", color=INK2, fontsize=10)
    # dimensions
    dim(ax, x0 + (L - span) / 2, -42, x0 + (L + span) / 2, -42, "span 180 mm", offset=(0, -6))
    dim(ax, x0 - 9, 0, x0 - 9, D, "25", offset=(-7, 0))
    ax.text(x0 + L - 2, D + 4, "length 200 mm", ha="right", va="bottom", color=INK2, fontsize=10)
    ax.text(x0 + (L - span) / 2 - 12, -14, "support\nrods", color=INK2, fontsize=9, ha="right", va="center")
    ax.set_xlim(-30, 230); ax.set_ylim(-56, 112)
    ax.set_title("Three-point bend setup (flex bars use the same rig at a 50 mm span)",
                 color=INK, fontsize=12, loc="left")
    save(fig, "test_setup.png")


# ---------------------------------------------------------------- 3. sandwich anatomy
def sandwich_anatomy():
    fig, ax = plt.subplots(figsize=(9, 4.4))
    ax.set_aspect("equal"); ax.axis("off")
    b, D, t = 25, 25, 1.6
    # scaled cross-section (end view)
    ax.add_patch(Rectangle((0, 0), b, D, facecolor="#f1f0ec", edgecolor=SOLID, lw=1.2))
    ax.add_patch(Rectangle((0, 0), b, t, color=SOLID, lw=0))
    ax.add_patch(Rectangle((0, D - t), b, t, color=SOLID, lw=0))
    for xx in np.arange(3, b, 4):
        ax.plot([xx, xx], [t, D - t], color=MUTED, lw=0.8)
    dim(ax, 0, -3, b, -3, "b = 25", offset=(0, -2.4))
    dim(ax, -3.5, t, -3.5, D - t, "c = 21.8", offset=(-1.8, 0), rotation=90)
    dim(ax, -10, t / 2, -10, D - t / 2, "d = 23.4", offset=(-1.8, 0), rotation=90)
    dim(ax, -16.5, 0, -16.5, D, "25", offset=(-1.8, 0), rotation=90)
    ax.annotate("face sheet, t = 1.6 mm\ncarries bending (tension / compression)", xy=(b * 0.8, D - t / 2),
                xytext=(b + 8, D + 1), color=INK, fontsize=10, va="center",
                arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
    ax.annotate("lattice core, 25% solid\ncarries shear: this is where\ntriangle and hexagon differ",
                xy=(b * 0.7, D / 2), xytext=(b + 8, D / 2), color=INK, fontsize=10, va="center",
                arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
    ax.annotate("face sheet", xy=(b * 0.8, t / 2), xytext=(b + 8, -1), color=INK, fontsize=10, va="center",
                arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
    ax.text(0, D + 6, "Beam cross-section (end view, to scale)", color=INK, fontsize=12)
    ax.text(b + 8, -12, "δ / P  =  L³ / 48D  +  L / 4AG*\n         bending          core shear",
            color=INK2, fontsize=10, family="DejaVu Sans Mono", va="center")
    ax.set_xlim(-24, 78); ax.set_ylim(-19, D + 10)
    save(fig, "sandwich_anatomy.png")


# ---------------------------------------------------------------- 4. test matrix
def test_matrix():
    mats = ["PLA", "PLA-CF", "PAHT-CF"]
    groups = [("Triangle beams", "TRI", TRI), ("Hexagon beams", "HEX", HEX), ("Solid flex bars", "BAR", SOLID)]
    fig, ax = plt.subplots(figsize=(10, 3.6))
    ax.axis("off")
    cw, ch, gap = 1.0, 0.62, 0.35
    for gi, (gname, tag, color) in enumerate(groups):
        gx = gi * (3 * cw + gap) + 1.4
        ax.text(gx + 1.5 * cw, len(mats) * ch + 0.18, gname, ha="center", va="bottom", fontsize=11, color=INK)
        for mi, m in enumerate(mats):
            y = (len(mats) - 1 - mi) * ch
            for c in range(3):
                ax.add_patch(Rectangle((gx + c * cw + 0.04, y + 0.05), cw - 0.08, ch - 0.1,
                                       facecolor=color, alpha=0.14, edgecolor=color, lw=1.1))
                ax.text(gx + c * cw + cw / 2, y + ch / 2, f"{tag}-{c + 1}", ha="center", va="center",
                        fontsize=10, color=INK)
    for mi, m in enumerate(mats):
        ax.text(1.25, (len(mats) - 1 - mi) * ch + ch / 2, m, ha="right", va="center", fontsize=11, color=INK)
    ax.text(0, -0.32, "27 specimens: 18 beams (2 shapes x 3 materials x 3 copies) + 9 flex bars. "
            "Full ID = material-shape-copy, e.g. PAHT-CF-HEX-2.",
            fontsize=10, color=INK2)
    ax.set_xlim(0, 1.4 + 3 * (3 * cw + gap)); ax.set_ylim(-0.5, len(mats) * ch + 0.55)
    save(fig, "test_matrix.png")


# ---------------------------------------------------------------- 5. predicted scaling
def predicted_scaling():
    rho = np.logspace(np.log10(0.05), np.log10(0.35), 200)
    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.plot(rho, rho / 3, color=TRI, lw=2, label="Triangle  E*/Es = ρ/3")
    ax.plot(rho, 1.5 * rho ** 3, color=HEX, lw=2, label="Hexagon  E*/Es = 1.5ρ³")
    for fn, c in ((lambda r: r / 3, TRI), (lambda r: 1.5 * r ** 3, HEX)):
        ax.plot([0.25], [fn(0.25)], "o", ms=8, color=c, mec=SURFACE, mew=2, zorder=5)
    ax.axvline(0.25, color=MUTED, lw=1, ls=(0, (3, 3)), zorder=0)
    ax.text(0.255, 2.2e-4, "this test, ρ = 0.25", color=INK2, fontsize=10)
    ax.annotate("", xy=(0.25, 0.25 / 3), xytext=(0.25, 1.5 * 0.25 ** 3),
                arrowprops=dict(arrowstyle="<|-|>", color=INK, lw=1, mutation_scale=10))
    ax.text(0.262, 0.042, "≈ 3.6x", color=INK, fontsize=11)
    ax.text(0.35, 0.35 / 3, " triangle", color=INK, va="center", fontsize=10)
    ax.text(0.35, 1.5 * 0.35 ** 3, " hexagon", color=INK, va="center", fontsize=10)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(0.05, 0.45); ax.set_ylim(1e-4, 0.3)
    from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator
    ax.xaxis.set_major_locator(FixedLocator([0.05, 0.1, 0.2, 0.3]))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_xlabel("Relative density ρ (solid fraction of core)")
    ax.set_ylabel("Core stiffness / solid modulus,  E*/Es")
    ax.grid(True, which="major", color=GRID, lw=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper left", labelcolor=INK)
    ax.set_title("Predicted in-plane core stiffness (thin-wall theory, Gibson-Ashby)", loc="left",
                 color=INK, fontsize=12)
    save(fig, "predicted_scaling.png")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    test_setup()
    sandwich_anatomy()
    test_matrix()
    predicted_scaling()
    beam_render()
