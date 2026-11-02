"""Printable clamp bolt (with a hand knob) and nut for the cup holder's clip: M8 x 1.5.

Why not M4: a printed M4 thread (0.7 mm pitch) is finer than FDM can hold, and it would strip long before the
clamp reaches the ~100-200 N it needs. M8 x 1.5 prints and holds. Printed in PETG it tolerates finger-tight only.

The threads are generated directly as a mesh: a cylinder whose radius follows the thread profile along a
right-hand helix. That is robust (no helical CAD sweeps or booleans) and watertight by construction. The nut's
bore is the bolt's own thread surface grown by `thread_clr`, so the two always mesh, at any rotation.

Frames (both pieces are built in their print pose, axis = Z, flat side on the bed):
    bolt: knob z in [-knob_h, 0] on the bed, threaded shank z in [0, length]. Shift to z >= 0 on export.
    nut:  z in [0, nut_h].
"""

from dataclasses import dataclass

import numpy as np
import trimesh
from shapely.geometry import Polygon as ShapelyPolygon


@dataclass(frozen=True)
class FastenerParams:
    major: float = 8.0           # bolt thread major diameter
    pitch: float = 1.5           # coarse-ish: prints better than M8 x 1.25
    thread_clr: float = 0.25     # radial gap between bolt and nut thread surfaces (printed pairs: 0.2-0.3)
    length: float = 40.0         # threaded shank under the knob
    knob_d: float = 24.0
    knob_h: float = 9.0
    knob_scallops: int = 8
    nut_af: float = 13.0         # hex across flats (the ear pocket is nut_af + clearance)
    nut_h: float = 6.5
    crest: float = 1 / 8         # ISO-ish profile as fractions of the pitch: crest flat, root flat,
    root: float = 1 / 4          # and two 30-degree flanks taking up the rest

    @property
    def depth(self) -> float:
        flank = (1 - self.crest - self.root) / 2 * self.pitch
        return flank / np.tan(np.radians(30))

    @property
    def r_core(self) -> float:
        return self.major / 2 - self.depth


def _profile(p: FastenerParams):
    flank = (1 - p.crest - p.root) / 2
    xs = [0, p.root / 2, p.root / 2 + flank, p.root / 2 + flank + p.crest, p.root / 2 + 2 * flank + p.crest, 1.0]
    ys = [0, 0, 1, 1, 0, 0]
    return lambda u: np.interp(np.mod(u, 1.0), xs, ys)


def threaded_cylinder(p: FastenerParams, z0: float, z1: float, grow: float = 0.0, chamfer_tip: bool = False,
                      ntheta: int = 72, rows_per_pitch: int = 24) -> trimesh.Trimesh:
    """Closed, watertight threaded rod from z0 to z1. `grow` offsets the whole surface outward (used for the nut bore)."""
    f = _profile(p)
    nz = max(2, int(round((z1 - z0) / p.pitch * rows_per_pitch)) + 1)
    th = np.linspace(0, 2 * np.pi, ntheta, endpoint=False)
    z = np.linspace(z0, z1, nz)
    T, Z = np.meshgrid(th, z)                                   # (nz, ntheta)
    R = p.r_core + p.depth * f(Z / p.pitch - T / (2 * np.pi)) + grow    # right-hand helix
    if chamfer_tip:
        R = np.minimum(R, p.r_core - 0.3 + (z1 - Z))            # 45-degree lead-in at the tip
    verts = np.c_[(R * np.cos(T)).ravel(), (R * np.sin(T)).ravel(), Z.ravel()]
    idx = np.arange(nz * ntheta).reshape(nz, ntheta)
    a, b = idx[:-1], idx[1:]
    a2, b2 = np.roll(a, -1, axis=1), np.roll(b, -1, axis=1)
    faces = np.r_[np.c_[a.ravel(), a2.ravel(), b2.ravel()], np.c_[a.ravel(), b2.ravel(), b.ravel()]]
    # end caps (fans around a centre vertex)
    c0, c1 = len(verts), len(verts) + 1
    verts = np.r_[verts, [[0, 0, z0]], [[0, 0, z1]]]
    bot, top = idx[0], idx[-1]
    faces = np.r_[faces,
                  np.c_[np.full(ntheta, c0), np.roll(bot, -1), bot],
                  np.c_[np.full(ntheta, c1), top, np.roll(top, -1)]]
    m = trimesh.Trimesh(verts, faces, process=True)
    m.fix_normals()
    return m


def _union(parts):
    return trimesh.boolean.union(parts, engine="manifold")


def _difference(a, b):
    return trimesh.boolean.difference([a, b], engine="manifold")


def make_bolt(p: FastenerParams = FastenerParams(), ntheta: int = 72, rows_per_pitch: int = 24) -> trimesh.Trimesh:
    """Knob-headed bolt, head down on the bed (z from -knob_h), shank up.
    Lower ntheta / rows_per_pitch for a light preview mesh (the viewer limits meshes to 65k vertices)."""
    shank = threaded_cylinder(p, -1.0, p.length, chamfer_tip=True, ntheta=ntheta,
                              rows_per_pitch=rows_per_pitch)                   # starts 1 mm inside the knob
    knob = trimesh.creation.cylinder(radius=p.knob_d / 2, height=p.knob_h, sections=96)
    knob.apply_translation([0, 0, -p.knob_h / 2])
    # scalloped grip: cut round notches around the rim
    r_s = 3.4
    for k in range(p.knob_scallops):
        a = 2 * np.pi * k / p.knob_scallops
        notch = trimesh.creation.cylinder(radius=r_s, height=p.knob_h + 2, sections=32)
        notch.apply_translation([(p.knob_d / 2 + r_s * 0.55) * np.cos(a), (p.knob_d / 2 + r_s * 0.55) * np.sin(a), -p.knob_h / 2])
        knob = _difference(knob, notch)
    bolt = _union([knob, shank])
    bolt.fix_normals()
    return bolt


def hex_prism(af: float, h: float, vertex_up: bool = True) -> trimesh.Trimesh:
    """Hex prism, z from 0 to h. Corners on the local +-Y axis when vertex_up."""
    ac_r = af / 2 / np.cos(np.radians(30))
    ang = np.radians(90 + 60 * np.arange(6)) if vertex_up else np.radians(60 * np.arange(6))
    poly = ShapelyPolygon(np.c_[ac_r * np.cos(ang), ac_r * np.sin(ang)])
    return trimesh.creation.extrude_polygon(poly, h)


def make_nut(p: FastenerParams = FastenerParams()) -> trimesh.Trimesh:
    """Hex nut, z from 0 to nut_h, corners on +-Y. Its bore is the bolt's thread surface grown by thread_clr."""
    body = hex_prism(p.nut_af, p.nut_h)
    bore = threaded_cylinder(p, -1.0, p.nut_h + 1.0, grow=p.thread_clr)
    nut = _difference(body, bore)
    nut.fix_normals()
    return nut


if __name__ == "__main__":
    p = FastenerParams()
    bolt, nut = make_bolt(p), make_nut(p)
    for name, m in (("bolt", bolt), ("nut", nut)):
        print(name, "watertight", m.is_watertight, "volume cm3", round(m.volume / 1000, 2), "faces", len(m.faces),
              "extents", m.extents.round(1))
    # Screw the nut on properly: rotating by 360 deg * (s / pitch) keeps its thread phase matched to the bolt at
    # axial position s, so there must be no collision anywhere along the shank.
    for pos in (8.0, 20.37, 33.9):
        n2 = nut.copy()
        n2.apply_transform(trimesh.transformations.rotation_matrix(2 * np.pi * (pos / p.pitch), [0, 0, 1]))
        n2.apply_translation([0, 0, pos])
        inter = bolt.intersection(n2, engine="manifold")
        print("nut at", pos, "interference mm3", round(abs(inter.volume), 4) if len(inter.faces) else 0.0)
