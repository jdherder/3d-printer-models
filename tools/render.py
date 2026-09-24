"""Headless preview renders (no GPU / OpenGL needed).

A tiny numpy z-buffer rasteriser draws shaded orthographic views, and
matplotlib lays them out with cross-sections so a human (or an agent reading
the PNG) can check shape and dimensions at a glance.

    python tools/render.py part.stl renders/part.png
"""

from __future__ import annotations

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from matplotlib.collections import LineCollection

# View name -> (camera direction the viewer looks *along*, screen-up vector)
VIEWS = {
    "iso": (np.array([-1.0, 1.0, -0.8]), np.array([0.0, 0.0, 1.0])),
    "top": (np.array([0.0, 0.0, -1.0]), np.array([0.0, 1.0, 0.0])),
    "front": (np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, 1.0])),
    "right": (np.array([-1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0])),
}


def rasterize(mesh: trimesh.Trimesh, view_dir, up, px: int = 700,
              color=(0.72, 0.74, 0.80)):
    """Return (rgb image, extent) of an orthographic shaded render."""
    d = np.asarray(view_dir, float)
    d /= np.linalg.norm(d)
    right = np.cross(d, up)
    right /= np.linalg.norm(right)
    upv = np.cross(right, d)
    v = mesh.vertices
    sx, sy, depth = v @ right, v @ upv, v @ d
    lo = np.array([sx.min(), sy.min()])
    hi = np.array([sx.max(), sy.max()])
    pad = 0.04 * (hi - lo).max()
    lo -= pad
    hi += pad
    scale = px / (hi - lo).max()
    W, H = np.ceil((hi - lo) * scale).astype(int) + 1
    X = (sx - lo[0]) * scale
    Y = (hi[1] - sy) * scale  # image rows grow downward

    # Headlight-ish key light plus a little fill; two-sided so open shells read.
    light = -d + 0.6 * upv - 0.4 * right
    light /= np.linalg.norm(light)
    n = mesh.face_normals
    shade = 0.25 + 0.75 * np.abs(n @ light)

    zbuf = np.full((H, W), np.inf)
    img = np.ones((H, W, 3))
    for f, s in zip(mesh.faces, shade):
        x, y, z = X[f], Y[f], depth[f]
        x0, x1 = int(max(np.floor(x.min()), 0)), int(min(np.ceil(x.max()), W - 1))
        y0, y1 = int(max(np.floor(y.min()), 0)), int(min(np.ceil(y.max()), H - 1))
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(den) < 1e-12:
            continue
        a = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / den
        b = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / den
        c = 1 - a - b
        inside = (a >= -1e-6) & (b >= -1e-6) & (c >= -1e-6)
        zz = a * z[0] + b * z[1] + c * z[2]
        sub = zbuf[y0:y1 + 1, x0:x1 + 1]
        win = inside & (zz < sub)
        sub[win] = zz[win]
        img[y0:y1 + 1, x0:x1 + 1][win] = np.asarray(color) * s
    extent = (lo[0], lo[0] + W / scale, hi[1] - H / scale, hi[1])
    return img, extent


def section_segments(mesh, normal, origin, axes):
    segs = trimesh.intersections.mesh_plane(mesh, normal, origin)
    return segs[:, :, axes] if len(segs) else np.zeros((0, 2, 2))


def render_sheet(meshes, out_path: str, title: str = "", labels=None,
                 sections_y=(0.0,), sections_x=(0.0,)):
    """Four shaded views of the first mesh plus XZ / YZ sections of all meshes."""
    if not isinstance(meshes, (list, tuple)):
        meshes = [meshes]
    labels = labels or [f"mesh {i}" for i in range(len(meshes))]
    main = meshes[0]
    colors = ["black", "tab:red", "tab:blue", "tab:green"]
    n_sec = len(sections_y) + len(sections_x)
    fig = plt.figure(figsize=(20, 10 + 4 * ((n_sec + 3) // 4)))
    gs = fig.add_gridspec(2 + (n_sec + 3) // 4, 4)

    ax = fig.add_subplot(gs[0:2, 0:2])
    img, ext = rasterize(main, *VIEWS["iso"], px=900)
    ax.imshow(img, extent=ext)
    ax.set_title("iso")
    ax.axis("off")
    for (name, pos) in zip(["top", "front", "right"], [gs[0, 2], gs[0, 3], gs[1, 2]]):
        ax = fig.add_subplot(pos)
        img, ext = rasterize(main, *VIEWS[name], px=500)
        ax.imshow(img, extent=ext)
        ax.set_title(f"{name} (mm)")
        ax.grid(True, alpha=0.3)
    ax = fig.add_subplot(gs[1, 3])
    ax.axis("off")
    e = main.extents
    ax.text(0, 0.9, f"extents X {e[0]:.1f}  Y {e[1]:.1f}  Z {e[2]:.1f} mm", fontsize=13)
    for i, lab in enumerate(labels):
        ax.text(0, 0.75 - 0.1 * i, f"— {lab}", color=colors[i], fontsize=12)

    specs = [("y", v) for v in sections_y] + [("x", v) for v in sections_x]
    for k, (axis, val) in enumerate(specs):
        ax = fig.add_subplot(gs[2 + k // 4, k % 4])
        for m, c in zip(meshes, colors):
            if axis == "y":
                segs = section_segments(m, [0, 1, 0], [0, val, 0], [0, 2])
            else:
                segs = section_segments(m, [1, 0, 0], [val, 0, 0], [1, 2])
            ax.add_collection(LineCollection(segs, colors=c, lw=1.2))
        ax.autoscale()
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.4)
        ax.set_title(f"section {axis}={val:g} mm ({'XZ' if axis == 'y' else 'YZ'})")

    fig.suptitle(title, fontsize=16)
    fig.savefig(out_path, dpi=70, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python tools/render.py <mesh> <out.png>")
    m = trimesh.load(sys.argv[1], force="mesh")
    render_sheet(m, sys.argv[2], title=sys.argv[1])
