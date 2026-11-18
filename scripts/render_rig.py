"""Shaded preview renders of the rig assemblies -> docs/img/rig_beam.png, docs/img/rig_bar.png"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection

sys.path.insert(0, "scripts")
import rig as r  # noqa: E402

SURFACE = "#fcfcfb"
INK, INK2 = "#0b0b0b", "#52514e"


def mesh(shape, tol=0.25):
    verts, tris = shape.val().tessellate(tol, 0.3)
    return np.array([(v.x, v.y, v.z) for v in verts]), np.array(tris)


def parts(config):
    beam = config == "beam"
    span = r.SPANS[0] if beam else r.SPANS[1]
    lt, mid, dk = "#cfcfcb", "#8d8c88", "#3d3c39"
    out = [(r.base(), lt)]
    for sx in (-span / 2, span / 2):
        out += [(r.saddle().translate((sx, 0, 0)), mid), (r.support_pad(not beam).translate((sx, 0, 0)), dk)]
    out += [(r.specimen(beam), "#2a78d6" if beam else "#eb6834"),
            (r.beam_nose() if beam else r.bar_nose(), dk),
            (r.lever(), mid),
            (r.cyl_x(r.BOLT_D / 2, -(r.LEVER_W / 2 + r.SPACER_T + 12), r.LEVER_W / 2 + r.SPACER_T + 20, r.PIVOT_Y, r.LEVER_CZ), "#9da0a6"),
            (r.plate_peg(48, 70) if beam else r.plate_peg(25, 40), dk),
            (r.yoke(span, r.BT if beam else r.BB + r.BAR_T, (r.BEAM_W if beam else r.BAR_W) / 2, beam), lt),
            (r.indicator_clamp(8.0), dk)]
    if not beam:
        out.append((r.weight_tray(), lt))
    return out


def render(config, path, title, az_deg=-140.0, el_deg=26.0, width=1500):
    """Flat-shaded z-buffer render (no OpenGL needed)."""
    az, el = np.radians(az_deg), np.radians(el_deg)
    view = np.array([np.cos(el) * np.sin(az), -np.cos(el) * np.cos(az), np.sin(el)])   # toward the viewer
    right = np.array([np.cos(az), np.sin(az), 0.0])
    up = np.cross(view, right)
    light = np.array([-0.4, 0.5, 0.77]); light /= np.linalg.norm(light)
    tris, cols = [], []
    for shape, color in parts(config):
        v, t = mesh(shape)
        p = v[t]
        n = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        keep = n @ view > 0
        p, n = p[keep], n[keep]
        shade = 0.5 + 0.5 * np.clip(n @ light, 0, 1)
        rgb = np.array(matplotlib.colors.to_rgb(color))
        tris.append(np.stack([p @ right, p @ up, p @ view], axis=-1))
        cols.append(np.clip(rgb[None, :] * shade[:, None], 0, 1))
    tris, cols = np.concatenate(tris), np.concatenate(cols)
    lo, hi = tris[..., :2].reshape(-1, 2).min(0) - 6, tris[..., :2].reshape(-1, 2).max(0) + 6
    scale = width / (hi[0] - lo[0])
    W, H = width, int((hi[1] - lo[1]) * scale)
    img = np.ones((H, W, 3)) * np.array(matplotlib.colors.to_rgb(SURFACE))
    zbuf = np.full((H, W), -np.inf)
    P = np.empty_like(tris)
    P[..., 0] = (tris[..., 0] - lo[0]) * scale
    P[..., 1] = (hi[1] - tris[..., 1]) * scale
    P[..., 2] = tris[..., 2]
    for tri, c in zip(P, cols):
        x0, y0 = np.floor(tri[:, :2].min(0)).astype(int)
        x1, y1 = np.ceil(tri[:, :2].max(0)).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, W - 1), min(y1, H - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        (ax_, ay), (bx, by), (cx, cy) = tri[0, :2], tri[1, :2], tri[2, :2]
        den = (by - cy) * (ax_ - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-9:
            continue
        w0 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den
        w1 = ((cy - ay) * (xs - cx) + (ax_ - cx) * (ys - cy)) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue
        z = w0 * tri[0, 2] + w1 * tri[1, 2] + w2 * tri[2, 2]
        sub = zbuf[y0:y1 + 1, x0:x1 + 1]
        upd = inside & (z > sub)
        sub[upd] = z[upd]
        img[y0:y1 + 1, x0:x1 + 1][upd] = c
    # light outline where depth jumps, so parts read separately
    dz = np.zeros_like(zbuf)
    finite = np.isfinite(zbuf)
    zf = np.where(finite, zbuf, zbuf[finite].min() - 50)
    dz[1:, :] = np.maximum(dz[1:, :], np.abs(np.diff(zf, axis=0)))
    dz[:, 1:] = np.maximum(dz[:, 1:], np.abs(np.diff(zf, axis=1)))
    img[dz > 4] = img[dz > 4] * 0.45
    fig = plt.figure(figsize=(W / 150, H / 150 + 0.45), dpi=150)
    ax = fig.add_axes([0, 0, 1, H / (H + 0.45 * 150)])
    ax.imshow(img, interpolation="antialiased"); ax.axis("off")
    fig.text(0.01, 0.985, title, va="top", color=INK, fontsize=12)
    fig.patch.set_facecolor(SURFACE)
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)
    print("wrote", path)


if __name__ == "__main__":
    render("beam", "docs/img/rig_beam.png", "Bend rig, beam setup (180 mm span, Olympic plate peg)")
    render("bar", "docs/img/rig_bar.png", "Bend rig, flex-bar setup (50 mm span, weight tray)")
