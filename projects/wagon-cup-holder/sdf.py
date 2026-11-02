"""Tiny signed-distance-field toolkit: build an organic solid from smooth blends, mesh it with marching cubes.

Why: stacking prisms and filleting where they meet looks assembled. Here the whole form is defined as one field,
so a smooth union gives true blended joins (no plate-on-block steps), and rounded edges are just smooth intersections.
The fit-critical surfaces (dovetail, bore, holes) are NOT done here: they are cut exactly on the mesh afterwards.

Convention: a field is negative inside, positive outside, in mm, as float32 arrays that broadcast against each other.
Axes are the grid's own (X, Y, Z); a Grid hands out broadcastable X[:, None, None], Y[None, :, None], Z[None, None, :].
"""

from dataclasses import dataclass

import numpy as np
import trimesh
from skimage import measure


@dataclass(frozen=True)
class Grid:
    lo: tuple
    hi: tuple
    h: float = 0.5

    def axes(self):
        return tuple(np.arange(l, u + self.h / 2, self.h, dtype=np.float32) for l, u in zip(self.lo, self.hi))

    def xyz(self):
        x, y, z = self.axes()
        return x[:, None, None], y[None, :, None], z[None, None, :]

    @property
    def shape(self):
        return tuple(len(a) for a in self.axes())


# ---------------------------------------------------------------------------------------------------------
# Booleans and blends
# ---------------------------------------------------------------------------------------------------------

def smin(a, b, k):
    """Smooth union (polynomial). k is the blend width in mm: concave joins get a fillet of about k/2."""
    if k <= 0:
        return np.minimum(a, b)
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k * 0.25


def smax(a, b, k):
    """Smooth intersection: rounds the convex edge where two surfaces meet."""
    return -smin(-a, -b, k)


def subtract(a, b, k=0.0):
    return smax(a, -b, k)


# ---------------------------------------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------------------------------------

def sd_polygon(px, py, verts):
    """Exact signed distance to a simple 2D polygon (any winding), vectorised over broadcastable px, py."""
    v = np.asarray(verts, dtype=np.float32)
    n = len(v)
    shape = np.broadcast(px, py).shape
    d = np.full(shape, np.inf, dtype=np.float32)
    s = np.ones(shape, dtype=np.float32)
    j = n - 1
    for i in range(n):
        ex, ey = v[j, 0] - v[i, 0], v[j, 1] - v[i, 1]
        wx, wy = px - v[i, 0], py - v[i, 1]
        t = np.clip((wx * ex + wy * ey) / (ex * ex + ey * ey + 1e-12), 0.0, 1.0)
        bx, by = wx - ex * t, wy - ey * t
        d = np.minimum(d, bx * bx + by * by)
        c1 = py >= v[i, 1]
        c2 = py < v[j, 1]
        c3 = ex * wy > ey * wx
        flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
        s = np.where(flip, -s, s)
        j = i
    return s * np.sqrt(d)


def sd_slab(t, lo, hi):
    """Signed distance to the slab lo <= t <= hi (t is a coordinate array)."""
    return np.maximum(lo - t, t - hi)


def sd_rect(px, py, cx, cy, hx, hy):
    """Signed distance to an axis-aligned rectangle (2D)."""
    qx, qy = np.abs(px - cx) - hx, np.abs(py - cy) - hy
    return np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0)


def sd_round_box(px, py, pz, c, half, r):
    """Signed distance to a box (centre c, half sizes `half`) with all edges rounded by r."""
    qx = np.abs(px - c[0]) - (half[0] - r)
    qy = np.abs(py - c[1]) - (half[1] - r)
    qz = np.abs(pz - c[2]) - (half[2] - r)
    out = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2 + np.maximum(qz, 0) ** 2)
    return out + np.minimum(np.maximum(np.maximum(qx, qy), qz), 0) - r


def revolve_profile(rho, z, half_profile):
    """SDF of a solid of revolution. `half_profile` is the (rho >= 0, z) outline from the axis out; it is mirrored so
    the polygon has no edge on the axis (which would make the field wrong deep inside)."""
    hp = [(r, zz) for r, zz in half_profile]
    mirrored = [(-r, zz) for r, zz in reversed(hp)]
    return sd_polygon(rho, z, hp + mirrored)


# ---------------------------------------------------------------------------------------------------------
# Meshing
# ---------------------------------------------------------------------------------------------------------

def to_mesh(field, grid: Grid, target_faces: int | None = None) -> trimesh.Trimesh:
    """Marching cubes at the zero level (guaranteed closed and manifold), then optional quadric decimation."""
    field = np.broadcast_to(field, grid.shape).astype(np.float32)
    # Close the volume: force the outermost voxel layer outside, so every surface is a closed shell.
    field = field.copy()
    field[0], field[-1] = 1.0, 1.0
    field[:, 0], field[:, -1] = 1.0, 1.0
    field[:, :, 0], field[:, :, -1] = 1.0, 1.0
    verts, faces, _, _ = measure.marching_cubes(field, level=0.0, spacing=(grid.h, grid.h, grid.h))
    verts = verts + np.asarray(grid.lo, dtype=np.float64)
    mesh = trimesh.Trimesh(verts, faces, process=True)
    mesh.fix_normals()
    if target_faces and len(mesh.faces) > target_faces:
        mesh = decimate(mesh, target_faces)
    return mesh


def decimate(mesh: trimesh.Trimesh, target_faces: int) -> trimesh.Trimesh:
    import pymeshlab
    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(mesh.vertices, mesh.faces))
    ms.meshing_decimation_quadric_edge_collapse(targetfacenum=int(target_faces), preservenormal=True,
                                                preservetopology=True, qualitythr=0.6, planarquadric=True)
    m = ms.current_mesh()
    out = trimesh.Trimesh(m.vertex_matrix(), m.face_matrix(), process=True)
    out.fix_normals()
    return out
