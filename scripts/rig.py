"""
Fully printed three-point bend rig for the lattice beams and the solid flex bars.

Coordinates (assembly): x = along the specimen, y = across it, z = up. Origin at mid-span.
Run from the repo root:  python3 scripts/rig.py   -> rig/*.step, rig/*.3mf, rig/assembly.step

Load path
  Weights on a peg at the end of a 5:1 lever. The lever pivots on a tower at y = -40,
  presses down on the loading nose at y = 0 through a large-radius tooth, and the peg sits
  at y = +160. Nose load = 5 x weight. Design load 2 kN at the nose (PAHT-CF beams).

Deflection is read relative to the specimen over its supports (a yoke that rests on the
specimen), not relative to the base, so flex in the printed rig does not enter the data.
"""
import math
import os

import cadquery as cq

OUT = "rig"

# ---------------- layout parameters (mm) ----------------
HB = 30.0              # base top
TONGUE_H = 8.0         # dovetail tongue on the rail
TONGUE_W0, TONGUE_W1 = 24.0, 32.0   # tongue width at bottom / top (undercut)
CLR = 0.3              # sliding clearance per side
SPANS = (180.0, 50.0)  # beam span, flex-bar span
BEAM_W, BEAM_D = 25.0, 25.0
BAR_W, BAR_T = 12.7, 3.2
PIVOT_Y = -40.0        # lever pivot
PEG_Y = 160.0          # weights: ratio (PEG_Y - PIVOT_Y) / (0 - PIVOT_Y) = 5
LEVER_W, LEVER_H = 34.0, 40.0
PIN_D = 14.0           # pivot pin
LOCK_D = 5.0           # saddle locking pins
STEM_Y = -21.0         # dial indicator stem axis (x, y)
STEM_X = -52.0

# derived heights
SADDLE_TOP = HB + 13.0          # flat top of saddle body
ROCKER_R = 10.0
ROCKER_CZ = HB + 10.0           # rocker axis height (axis along y)
ROCKER_TOP = ROCKER_CZ + ROCKER_R
PAD_T = 6.0
BB = ROCKER_TOP + PAD_T         # specimen bottom (support pad top) = 56
BT = BB + BEAM_D                # beam top = 81
NT = BT + 12.0                  # loading-nose top, same for both noses = 93
TOOTH_R = 60.0
LB = NT + 9.0                   # lever bottom = 102
LEVER_CZ = LB + LEVER_H / 2     # lever mid-height = pivot height = 122
TAB_Z0 = NT - 11.0              # indicator tab on the nose: 82..93
YOKE_BAR_Z = (BB + 3.0, BB + 12.0)   # side bar of both yokes: 59..68


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl_x(r, x0, x1, y, z):
    return cq.Workplane("YZ").circle(r).extrude(x1 - x0).translate((x0, y, z))


def cyl_y(r, y0, y1, x, z):
    return cq.Workplane("XZ").circle(r).extrude(-(y1 - y0)).translate((x, y0, z))


def cyl_z(r, z0, z1, x, y):
    return cq.Workplane("XY").circle(r).extrude(z1 - z0).translate((x, y, z0))


def prism_x(pts_yz, x0, x1):
    """Polygon in the y-z plane, extruded along x."""
    return cq.Workplane("YZ").polyline(pts_yz).close().extrude(x1 - x0).translate((x0, 0, 0))


# ------------------------------------------------------------------ parts
def base():
    rail = box(-120, 120, -30, 30, 0, HB)
    cross = box(-30, 30, -62, 185, 0, HB)
    tongue = prism_x([(-TONGUE_W0 / 2, HB), (TONGUE_W0 / 2, HB),
                      (TONGUE_W1 / 2, HB + TONGUE_H), (-TONGUE_W1 / 2, HB + TONGUE_H)], -120, 120)
    gap = LEVER_W / 2 + 0.5
    top = LEVER_CZ + PIN_D / 2 + 13
    # Cheeks are full width only up near the pin; below z = 100 they stay clear (y < -32) of the
    # saddles, the yoke rail and the nose tab, which all sit between y = -30 and y = 0.
    knee = 100.0
    cheeks = None
    for x0 in (gap, -gap - 10):
        c = box(x0, x0 + 10, PIVOT_Y - 14, -32, HB, top).union(box(x0, x0 + 10, PIVOT_Y - 14, PIVOT_Y + 14, knee, top))
        cheeks = c if cheeks is None else cheeks.union(c)
    stop_top = LB - 52.0      # lever lands here after ~14 mm of nose travel (a break)
    stop = box(-15, 15, 94, 106, HB, stop_top)
    b = rail.union(cross).union(tongue).union(cheeks).union(stop)
    b = b.cut(cyl_x(PIN_D / 2 + 0.3, -40, 40, PIVOT_Y, LEVER_CZ))
    for span in SPANS:
        for sx in (-span / 2, span / 2):
            for sy in (-24, 24):
                b = b.cut(cyl_z(LOCK_D / 2 + 0.3, HB - 12, HB + 1, sx, sy))
            # span marks on the rail's -y face
            b = b.cut(box(sx - 0.5, sx + 0.5, -31, -29.2, HB - 10, HB + 1))
    return b


def saddle():
    body = box(-15, 15, -30, 30, HB, SADDLE_TOP)
    slot = prism_x([(-TONGUE_W0 / 2 - CLR, HB - 1), (TONGUE_W0 / 2 + CLR, HB - 1),
                    (TONGUE_W0 / 2 + CLR, HB), (TONGUE_W1 / 2 + CLR, HB + TONGUE_H + CLR),
                    (-TONGUE_W1 / 2 - CLR, HB + TONGUE_H + CLR), (-TONGUE_W0 / 2 - CLR, HB)], -16, 16)
    rocker = cyl_y(ROCKER_R, -16, 16, 0, ROCKER_CZ).intersect(box(-8, 8, -16, 16, SADDLE_TOP - 1, ROCKER_TOP + 1))
    s = body.cut(slot).union(rocker)
    for sy in (-24, 24):
        s = s.cut(cyl_z(LOCK_D / 2 + 0.3, HB - 1, SADDLE_TOP + 1, 0, sy))
    s = s.cut(box(-0.5, 0.5, -31, -29.2, HB + 2, SADDLE_TOP + 1))     # center mark
    return s


def support_pad(bar=False):
    top = BB if not bar else BB - ROCKER_R / 2 + 0.0
    p = box(-10, 10, -16, 16, ROCKER_TOP - 3, BB if not bar else BB - 5)
    if not bar:
        p = p.edges("|Y and >Z").fillet(3)
    else:
        p = p.union(cyl_y(5, -16, 16, 0, BB - 5))      # R5 support, ASTM D790 size
    return p.cut(cyl_y(ROCKER_R + 0.3, -20, 20, 0, ROCKER_CZ))


def beam_nose():
    half = BEAM_W / 2
    pad = box(-10, 10, -half, half, BT, BT + 5).edges("|Y and <Z").fillet(3)
    upper = box(-15, 15, -half - 3.4, half + 3.4, BT + 5, NT)
    lips = box(-10, 10, half + 0.4, half + 3.4, BT - 8, BT + 5).union(
        box(-10, 10, -half - 3.4, -half - 0.4, BT - 8, BT + 5))
    tab = box(STEM_X - 6, -10, -28, -half - 0.4, TAB_Z0, NT)
    return pad.union(upper).union(lips).union(tab)


def bar_nose():
    half = BAR_W / 2
    tip_cz = BB + BAR_T + 5
    tip = cyl_y(5, -half - 0.25, half + 0.25, 0, tip_cz).union(box(-5, 5, -half - 3.4, half + 3.4, tip_cz, tip_cz + 4))
    lips = box(-5, 5, half + 0.4, half + 3.4, BB + 1, tip_cz).union(box(-5, 5, -half - 3.4, -half - 0.4, BB + 1, tip_cz))
    column = box(-8, 8, -half - 3.4, half + 3.4, tip_cz + 4, NT - 11)
    upper = box(-15, 15, -12, 12, NT - 11, NT)
    tab = box(STEM_X - 6, -10, -28, -11, TAB_Z0, NT)
    return tip.union(lips).union(column).union(upper).union(tab)


def lever():
    body = box(-LEVER_W / 2, LEVER_W / 2, PIVOT_Y - 13, PEG_Y + 12, LB, LB + LEVER_H)
    tooth = cyl_x(TOOTH_R, -LEVER_W / 2, LEVER_W / 2, 0, NT + TOOTH_R).intersect(
        box(-LEVER_W / 2, LEVER_W / 2, -10, 10, NT - 1, LB + 1))
    lv = body.union(tooth)
    lv = lv.cut(cyl_x(PIN_D / 2 + 0.4, -30, 30, PIVOT_Y, LEVER_CZ))
    lv = lv.cut(cyl_z(8.2, LB - 1, LB + LEVER_H + 1, 0, PEG_Y))
    lv = lv.edges("|X").edges(cq.selectors.BoxSelector((-50, PIVOT_Y - 20, 0), (50, PIVOT_Y - 5, 300))).fillet(8)
    return lv


def pivot_pin():
    length = 2 * (LEVER_W / 2 + 0.5 + 10) + 7
    p = cyl_x(PIN_D / 2, 0, length, 0, 0).union(cyl_x(PIN_D / 2 + 4, -4, 0, 0, 0))
    return p.cut(box(-10, length + 1, -20, 20, -20, -PIN_D / 2 + 0.8))   # flat, prints lying on it


def pin_keeper():
    k = cyl_z(PIN_D / 2 + 4, 0, 5, 0, 0).cut(cyl_z(PIN_D / 2 - 0.1, -1, 6, 0, 0))
    return k.cut(box(-0.6, 0.6, 0, PIN_D, -1, 6))


def lock_pin():
    return cyl_z(LOCK_D / 2, 0, 24, 0, 0).union(cyl_z(4.5, 24, 26, 0, 0))


def plate_peg(sleeve_d, flange_d):
    """Stem goes through the lever, flange bears on the lever top, plates slide on the sleeve."""
    z0 = LB
    stem = cyl_z(8.0, z0, z0 + LEVER_H, 0, PEG_Y)
    flange = cyl_z(flange_d / 2, z0 + LEVER_H, z0 + LEVER_H + 4, 0, PEG_Y)
    rise = (flange_d - sleeve_d) / 2
    cone = cq.Workplane("XY").circle(flange_d / 2).workplane(offset=rise).circle(sleeve_d / 2).loft() \
        .translate((0, PEG_Y, z0 + LEVER_H + 4))
    sleeve = cyl_z(sleeve_d / 2, z0 + LEVER_H + 4, z0 + LEVER_H + 4 + 80, 0, PEG_Y)
    return stem.union(flange).union(cone).union(sleeve)


def weight_tray():
    """Sits on the standard peg's sleeve; holds water, sand or washers for the light flex-bar loads."""
    z0 = LB + LEVER_H + 4 + 80 - 40
    dish = cyl_z(90, z0, z0 + 30, 0, PEG_Y).cut(cyl_z(87, z0 + 3, z0 + 31, 0, PEG_Y))
    socket = cyl_z(16, z0, z0 + 40, 0, PEG_Y).cut(cyl_z(12.8, z0 - 1, z0 + 41, 0, PEG_Y))
    return dish.union(socket).cut(cyl_z(12.8, z0 - 1, z0 + 41, 0, PEG_Y))


def yoke(span, top, half_w, lips):
    """Rests on the specimen right over the supports and carries the dial indicator."""
    xs = span / 2
    y_out = -half_w - 3.4
    parts = []
    for sx in (-xs, xs):
        plate = box(sx - 6, sx + 6, y_out, -y_out, top + 1.5, top + 7)
        ridge = cyl_y(1.5, -half_w + 0.2, half_w - 0.2, sx, top + 1.5)
        conn = box(sx - 6, sx + 6, -30, y_out, YOKE_BAR_Z[0], top + 7)
        parts += [plate, ridge, conn]
        if lips:
            parts += [box(sx - 6, sx + 6, half_w + 0.4, half_w + 3.4, top - 7, top + 7)]
    x_lo = min(-xs - 6, STEM_X - 10)
    parts.append(box(x_lo, xs + 6, -30, -18, *YOKE_BAR_Z))
    parts.append(box(STEM_X - 5, STEM_X + 5, -40, -30, YOKE_BAR_Z[0], 150))     # indicator post
    y = parts[0]
    for p in parts[1:]:
        y = y.union(p)
    return y


def indicator_clamp(stem_d):
    """Slides on the yoke post (friction flexure) and grips the indicator stem (split ring)."""
    z0, z1 = 115, 129
    sock = box(STEM_X - 8.2, STEM_X + 8.2, -43.2, -26.8, z0, z1).cut(box(STEM_X - 5, STEM_X + 5, -40, -30, z0 - 1, z1 + 1))
    sock = sock.cut(box(STEM_X - 9, STEM_X - 4, -35.5, -34.5, z0 - 1, z1 + 1))
    ring = cyl_z(stem_d / 2 + 3.7, z0, z1, STEM_X, STEM_Y)
    c = sock.union(ring).cut(cyl_z(stem_d / 2 - 0.05, z0 - 1, z1 + 1, STEM_X, STEM_Y))
    c = c.cut(box(STEM_X - 0.6, STEM_X + 0.6, STEM_Y, STEM_Y + 20, z0 - 1, z1 + 1))
    return c


# ---------------------------------------------------------------- print orientation
def flip(shape):
    """Upside down onto the bed."""
    return shape.rotate((0, 0, 0), (1, 0, 0), 180)


def on_side_x(shape):
    """Lay a part with its x-extrusion axis vertical (profile on the bed)."""
    return shape.rotate((0, 0, 0), (0, 1, 0), 90)


def to_bed(shape):
    bb = shape.val().BoundingBox()
    return shape.translate((-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2, -bb.zmin))


# name, builder, copies, how to orient it for printing, notes
PARTS = [
    ("01_base", base, 1, lambda s: s, "rail + crosspiece + pivot tower + lever stop, one piece"),
    ("02_support_saddle", saddle, 2, lambda s: s, "slides on the rail, locked by two pins"),
    ("03_beam_support_pad", lambda: support_pad(False), 2, flip, "rocks on the saddle, flat top"),
    ("04_bar_support_pad", lambda: support_pad(True), 2, flip, "rocks on the saddle, R5 top"),
    ("05_beam_loading_nose", beam_nose, 1, flip, "25 x 20 mm load pad"),
    ("06_bar_loading_nose", bar_nose, 1, flip, "R5 nose"),
    ("07_lever", lever, 1, on_side_x, "5:1, print on its side"),
    ("08_pivot_pin", pivot_pin, 1, lambda s: s, "prints on its flat"),
    ("09_pin_keeper", pin_keeper, 1, lambda s: s, "friction fit on the pivot pin"),
    ("10_saddle_lock_pin", lock_pin, 4, flip, "head down"),
    ("11_plate_peg_standard", lambda: plate_peg(25.0, 40.0), 1, flip, "for 1-inch-hole plates"),
    ("12_plate_peg_olympic", lambda: plate_peg(48.0, 70.0), 1, flip, "for 2-inch-hole plates"),
    ("13_weight_tray", weight_tray, 1, lambda s: s, "on the standard peg, for flex bars"),
    ("14_beam_deflection_yoke", lambda: yoke(SPANS[0], BT, BEAM_W / 2, True), 1, lambda s: s, "needs supports"),
    ("15_bar_deflection_yoke", lambda: yoke(SPANS[1], BB + BAR_T, BAR_W / 2, False), 1, lambda s: s, "needs supports"),
    ("16_indicator_clamp_8mm", lambda: indicator_clamp(8.0), 1, lambda s: s, "metric dial indicators"),
    ("17_indicator_clamp_3-8in", lambda: indicator_clamp(9.525), 1, lambda s: s, "US dial indicators"),
]


def specimen(beam=True):
    if beam:
        return box(-100, 100, -BEAM_W / 2, BEAM_W / 2, BB, BT)
    return box(-63.5, 63.5, -BAR_W / 2, BAR_W / 2, BB, BB + BAR_T)


def assembly(config="beam"):
    beam = config == "beam"
    span = SPANS[0] if beam else SPANS[1]
    a = cq.Assembly()
    a.add(base(), name="base", color=cq.Color(0.80, 0.80, 0.78))
    for i, sx in enumerate((-span / 2, span / 2)):
        a.add(saddle().translate((sx, 0, 0)), name=f"saddle{i}", color=cq.Color(0.55, 0.55, 0.53))
        a.add(support_pad(not beam).translate((sx, 0, 0)), name=f"pad{i}", color=cq.Color(0.24, 0.24, 0.22))
        for sy in (-24, 24):
            a.add(lock_pin().translate((sx, sy, HB - 11)), name=f"lock{i}{sy}", color=cq.Color(0.24, 0.24, 0.22))
    a.add(specimen(beam), name="specimen", color=cq.Color(0.16, 0.47, 0.84) if beam else cq.Color(0.92, 0.41, 0.20))
    a.add(beam_nose() if beam else bar_nose(), name="nose", color=cq.Color(0.24, 0.24, 0.22))
    a.add(lever(), name="lever", color=cq.Color(0.55, 0.55, 0.53))
    a.add(pivot_pin().rotate((0, 0, 0), (1, 0, 0), 180).translate((-(LEVER_W / 2 + 10.5), PIVOT_Y, LEVER_CZ)),
          name="pin", color=cq.Color(0.24, 0.24, 0.22))
    a.add(plate_peg(48.0, 70.0) if beam else plate_peg(25.0, 40.0), name="peg", color=cq.Color(0.24, 0.24, 0.22))
    if not beam:
        a.add(weight_tray(), name="tray", color=cq.Color(0.80, 0.80, 0.78))
    a.add(yoke(span, BT if beam else BB + BAR_T, (BEAM_W if beam else BAR_W) / 2, beam), name="yoke",
          color=cq.Color(0.80, 0.80, 0.78))
    a.add(indicator_clamp(8.0), name="clamp", color=cq.Color(0.24, 0.24, 0.22))
    return a


def interference_check(config="beam"):
    """Every pair of rig parts that should not touch must not overlap (volume > 1 mm^3)."""
    beam = config == "beam"
    span = SPANS[0] if beam else SPANS[1]
    solids = {"base": base(), "specimen": specimen(beam), "nose": beam_nose() if beam else bar_nose(),
              "lever": lever(), "yoke": yoke(span, BT if beam else BB + BAR_T, (BEAM_W if beam else BAR_W) / 2, beam),
              "clamp": indicator_clamp(8.0), "peg": plate_peg(48.0, 70.0) if beam else plate_peg(25.0, 40.0)}
    for i, sx in enumerate((-span / 2, span / 2)):
        solids[f"saddle{i}"] = saddle().translate((sx, 0, 0))
        solids[f"pad{i}"] = support_pad(not beam).translate((sx, 0, 0))
    names = list(solids)
    hits = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            v = solids[names[i]].intersect(solids[names[j]]).val().Volume() if True else 0
            if v > 1.0:
                hits.append((names[i], names[j], round(v, 1)))
    return hits


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn, n, orient, note in PARTS:
        shape = fn()
        assert shape.val().isValid(), name
        printed = to_bed(orient(shape))
        cq.exporters.export(printed, f"{OUT}/{name}.step")
        cq.exporters.export(printed, f"{OUT}/{name}.3mf", tolerance=0.02, angularTolerance=0.1)
        bb = printed.val().BoundingBox()
        print(f"{name:30s} x{n}  {bb.xlen:6.1f} x {bb.ylen:6.1f} x {bb.zlen:6.1f} mm  "
              f"{shape.val().Volume() / 1000:6.1f} cm3  {note}")
    for cfg in ("beam", "bar"):
        assembly(cfg).save(f"{OUT}/assembly_{cfg}.step")
        print(cfg, "interference:", interference_check(cfg) or "none")
