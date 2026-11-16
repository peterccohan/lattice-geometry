"""
Infill-geometry bend specimens: five 2.5D cell geometries in the same beam envelope,
all at the same solid volume (same mass), so cell geometry is the only variable.

Sketch plane XY:  X = length, Y = depth (load direction in the bend test)
Extrude along Z:  width. Z is also the print direction: cells are vertical prisms,
                  so there are no overhangs and no supports.

How the mass is matched without biasing the test:
  1. Cell size and pattern placement are picked so that no cell wall lies along a
     face sheet (that would thicken the skin, and skins dominate bending stiffness).
  2. Wall thickness is then trimmed a few percent around WALL to land on the exact
     target volume.

Run:  python3 infill_beams.py      -> STEP + 3MF + preview.png in ./OUT
"""
import math
import os

import cadquery as cq
from shapely import affinity
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

# ---------------- parameters (edit these) ----------------
LENGTH = 200.0        # X, mm
DEPTH = 25.0          # Y, mm  (load direction)
WIDTH = 25.0          # Z, mm  (extrusion / print height)
SKIN = 1.6            # perimeter frame: top and bottom face sheets + end walls, mm
WALL = 0.8            # nominal cell wall, mm (2 lines @ 0.4 nozzle)
CORE_DENSITY = 0.25   # solid fraction of the region inside the frame
MIN_VOID = 0.6        # voids narrower than this (mm) get filled
MIN_VOID_AREA = 2.0   # voids smaller than this (mm^2) get filled
OUT = "cad"
# ---------------------------------------------------------

CX, CY = LENGTH / 2, DEPTH / 2
RX, RY = LENGTH / 2 + 40, DEPTH / 2 + 40   # half-extent the tiling has to cover
MITRE = dict(join_style="mitre", mitre_limit=20)


# ---- cell tilings centred on the origin; each returns closed cell polygons ----
def square_cells(p):
    """Walls at 0/90 deg to the beam axis."""
    n, m = int(RX / p) + 2, int(RY / p) + 2
    return [box(i * p, j * p, (i + 1) * p, (j + 1) * p)
            for i in range(-n, n + 1) for j in range(-m, m + 1)]


def diamond_cells(p):
    """Square grid rotated 45 deg (walls at +/-45 deg to the beam axis)."""
    n = int(math.hypot(RX, RY) / p) + 2
    cells = [box(i * p - p / 2, j * p - p / 2, i * p + p / 2, j * p + p / 2)
             for i in range(-n, n + 1) for j in range(-n, n + 1)]
    return [affinity.rotate(c, 45, origin=(0, 0)) for c in cells]


def triangle_cells(L):
    """Equilateral triangles, one wall family parallel to the beam axis."""
    H = L * math.sqrt(3) / 2
    n, m = int(RX / L) + 3, int(RY / H) + 2
    cells = []
    for j in range(-m, m + 1):
        for i in range(-n, n + 1):
            x0, y0 = i * L + j * L / 2, j * H
            if abs(x0) > RX + 2 * L:
                continue
            cells.append(Polygon([(x0, y0), (x0 + L, y0), (x0 + L / 2, y0 + H)]))
            cells.append(Polygon([(x0 + L, y0), (x0 + 1.5 * L, y0 + H), (x0 + L / 2, y0 + H)]))
    return cells


def hexagon_cells(s):
    """Regular hexagons, side s, two walls parallel to the load direction."""
    dx, dy = math.sqrt(3) * s, 1.5 * s
    n, m = int(RX / dx) + 3, int(RY / dy) + 2
    hexagon = [(s * math.cos(math.radians(30 + 60 * k)), s * math.sin(math.radians(30 + 60 * k)))
               for k in range(6)]
    return [Polygon([(x + i * dx + (j % 2) * dx / 2, y + j * dy) for x, y in hexagon])
            for j in range(-m, m + 1) for i in range(-n, n + 1)]


def reentrant_cells(l, theta_deg=30.0, h_over_l=2.0):
    """Re-entrant (bow-tie) auxetic honeycomb: inclined rib length l, re-entrant angle theta,
    ribs of length h = h_over_l * l parallel to the load direction."""
    a = l * math.cos(math.radians(theta_deg))
    d = l * math.sin(math.radians(theta_deg))
    h = h_over_l * l
    bow = [(-a, -h / 2), (0, -h / 2 + d), (a, -h / 2), (a, h / 2), (0, h / 2 - d), (-a, h / 2)]
    dx, dy = 2 * a, h - d
    n, m = int(RX / dx) + 3, int(RY / dy) + 2
    return [Polygon([(x + i * dx + (j % 2) * a, y + j * dy) for x, y in bow])
            for j in range(-m, m + 1) for i in range(-n, n + 1)]


# name, generator, size-parameter label, first-guess size as a multiple of WALL / CORE_DENSITY,
# vertical period of the tiling as a multiple of the size parameter
GEOMETRIES = [
    ("01_square_grid", square_cells, "pitch", 2.0, 1.0),
    ("02_diamond_grid", diamond_cells, "pitch", 2.0, math.sqrt(2)),
    ("03_triangle_isogrid", triangle_cells, "side", 2 * math.sqrt(3), math.sqrt(3) / 2),
    ("04_hexagon_honeycomb", hexagon_cells, "side", 2 / math.sqrt(3), 1.5),
    ("05_reentrant_auxetic", reentrant_cells, "rib length", 1.5, 1.5),
]


def section(cell_fn, size, wall, yshift=0.0):
    """2D cross-section (shapely polygon with holes)."""
    outer = box(0, 0, LENGTH, DEPTH)
    inner = box(SKIN, SKIN, LENGTH - SKIN, DEPTH - SKIN)
    voids = []
    for c in cell_fn(size):
        c = affinity.translate(c, CX, CY + yshift)
        if not c.intersects(inner):
            continue
        v = c.buffer(-wall / 2, **MITRE).intersection(inner)                 # shrink by half a wall, clip to frame
        v = v.buffer(-MIN_VOID / 2, **MITRE).buffer(MIN_VOID / 2, **MITRE)   # drop slivers
        v = v.intersection(inner)
        parts = getattr(v, "geoms", [v])
        voids += [g for g in parts if g.geom_type == "Polygon" and g.area >= MIN_VOID_AREA]
    return outer.difference(unary_union(voids)).simplify(1e-6)


def skin_excess(sec):
    """Fraction of the band just inside each face sheet (2.5 walls deep) that is solid, worst of
    top/bottom. Low and similar across geometries = no geometry gets a hidden thicker skin."""
    band, worst = 2.5 * WALL, 0.0
    for y0 in (SKIN, DEPTH - SKIN - band):
        b = box(10, y0, LENGTH - 10, y0 + band)
        worst = max(worst, sec.intersection(b).area / b.area)
    return worst


def layout(cell_fn, guess, period, target):
    """Pick cell size + placement with clean skins, then trim wall thickness to the exact mass."""
    cands = []
    for k in range(41):
        size = guess * (0.75 + 0.5 * k / 40)
        for phase in (0.0, 0.5):               # the two placements that keep top and bottom equivalent
            sec = section(cell_fn, size, WALL, phase * period * size)
            err = (sec.area - target) / target
            if abs(err) <= 0.05:
                cands.append((skin_excess(sec), abs(err), size, phase))
    cleanest = min(c[0] for c in cands)
    _, _, size, phase = min((c for c in cands if c[0] <= cleanest + 0.02), key=lambda c: c[1])
    lo, hi = 0.8 * WALL, 1.2 * WALL
    for _ in range(40):                        # area rises smoothly with wall thickness
        wall = (lo + hi) / 2
        if section(cell_fn, size, wall, phase * period * size).area < target:
            lo = wall
        else:
            hi = wall
    return size, phase, wall, section(cell_fn, size, wall, phase * period * size)


def to_solid(sec):
    """Shapely polygon with holes -> extruded CadQuery solid (planar faces only)."""
    def wire(ring):
        pts = [cq.Vector(round(x, 5), round(y, 5), 0) for x, y in list(ring.coords)[:-1]]
        return cq.Wire.makePolygon(pts, close=True)
    face = cq.Face.makeFromWires(wire(sec.exterior), [wire(r) for r in sec.interiors])
    return cq.Solid.extrudeLinear(face, cq.Vector(0, 0, WIDTH))


def export(shape, stem):
    wp = cq.Workplane("XY").add(shape)
    cq.exporters.export(wp, f"{OUT}/{stem}.step")
    cq.exporters.export(wp, f"{OUT}/{stem}.3mf", tolerance=0.001, angularTolerance=0.05)


def build_all():
    os.makedirs(OUT, exist_ok=True)
    inner_area = (LENGTH - 2 * SKIN) * (DEPTH - 2 * SKIN)
    target = LENGTH * DEPTH - inner_area + CORE_DENSITY * inner_area
    results = []
    for base, fn, label, k, period in GEOMETRIES:
        name = f"{base}_{DEPTH:g}x{WIDTH:g}"
        size, phase, wall, sec = layout(fn, k * WALL / CORE_DENSITY, period, target)
        assert sec.geom_type == "Polygon" and sec.is_valid, name
        solid = to_solid(sec)
        export(solid, name)
        r = dict(name=name, label=label, size=size, wall=wall, sec=sec, excess=skin_excess(sec),
                 volume_cm3=solid.Volume() / 1000, cells=len(sec.interiors), valid=solid.isValid())
        results.append(r)
        print(f"{name:28s} {label} = {size:5.2f}  wall = {wall:.3f}  skin excess = {r['excess']:.2f}  "
              f"cells = {r['cells']:3d}  volume = {r['volume_cm3']:.2f} cm3  valid = {r['valid']}")
    print(f"target volume = {target * WIDTH / 1000:.2f} cm3")
    return results


def flex_bar():
    """Solid base-material bar for 3-point bending (ASTM D790 size: 127 x 12.7 x 3.2 mm)."""
    export(cq.Workplane("XY").box(127.0, 12.7, 3.2, centered=False).val(), "00_solid_flex_bar_127x12.7x3.2")


def preview(results, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path

    fig, axes = plt.subplots(len(results), 1, figsize=(9, (9 * DEPTH / LENGTH + 0.55) * len(results)))
    for ax, r in zip(axes, results):
        sec = r["sec"]
        verts, codes = [], []
        for ring in [sec.exterior, *sec.interiors]:
            xy = list(ring.coords)
            verts += xy
            codes += [Path.MOVETO] + [Path.LINETO] * (len(xy) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), facecolor="#2b2f36", edgecolor="none"))
        ax.set_xlim(-2, LENGTH + 2)
        ax.set_ylim(-1, DEPTH + 1)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(f"{r['name']}   ({r['label']} {r['size']:.1f} mm, wall {r['wall']:.2f} mm, "
                     f"{r['volume_cm3']:.1f} cm³)", fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(path, dpi=130, facecolor="white")


if __name__ == "__main__":
    res = build_all()
    flex_bar()
    preview(res, f"{OUT}/preview.png")
