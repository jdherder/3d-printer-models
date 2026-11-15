"""Reproducible build for the Black Bob Thunderbird mascot figurine.

    python projects/thunderbird-mascot/build.py        (~1-2 min)

References: source/costume-*.png (photos of the costume mascot at school). There is no scan: the figure is a
chibi interpretation built from smooth signed-distance shapes, meshed with marching cubes.

  -> shape groups, each one smooth field (parts of one group blend into each other):
       red body (torso, head, red "shorts", wings) | red cap (dome, button) |
       white parts (beak muzzle with an open mouth, legs, feet) | black (pupils, cap bill, claws)
  -> colour "decals" painted onto the red with exact boolean regions: the white chest blaze (jagged sides,
     zigzag bottom edge) and the white staggered "B B" on the cap
  -> a black display base
  -> colour bodies by priority (black > white > red), all disjoint, made with manifold3d booleans
  -> scaled so the whole figure (base to cap) is HEIGHT_MM tall
  -> output/thunderbird-mascot-multicolor.3mf  one object, three parts (red, white, black) for the AMS
  -> output/thunderbird-mascot.stl             single-colour print (everything merged)
  -> output/thunderbird-mascot-{red,white,black}.stl
  -> output/report.json, renders/*.png, renders/view-*.stl (light copies for the review page)

Design coordinates are millimetres at about 76 mm tall, Z-up, the bird faces -Y (the front view looks along +Y).
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / "tools")]

import manifold3d as m3d  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pymeshlab  # noqa: E402
import trimesh  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.textpath import TextPath  # noqa: E402
from skimage import measure  # noqa: E402

import meshkit as mk  # noqa: E402

NAME = "thunderbird-mascot"
OUT = HERE / "output"
RENDERS = HERE / "renders"

HEIGHT_MM = 80.0        # base bottom to cap top, after scaling
GRID = 0.3              # marching-cubes voxel (design mm)
GROUP_FACES = 80_000    # decimation target per shape group (keeps booleans and STLs light)
VIEW_FACES = 40_000     # per colour, for the review page (< 65k vertices)

COLOURS = {"red": "#c8202c", "white": "#f2f2f2", "black": "#2b2b2e"}

# ------------------------------------------------------------------------------------------------
# Design parameters (design mm, before scaling)
# ------------------------------------------------------------------------------------------------
# v7: rebuilt from the owner's costume photos (source/costume-2026-11-14-facebook-*.png). The costume is a tall red
# column with no waist, the head flowing straight into it; a big rounded white beak with a short hook and a wide-open
# red mouth, the white running up between the eyes; black eyes high at the sides under the bill; a white jagged blaze
# down the chest that widens into a white belly with a zigzag bottom edge; red "shorts"; white legs; red wings with red
# feathered tips; small white feet (owner's pick) with black talons.
BASE = dict(c=(0.0, -2.0), r=(22.0, 19.0), h=5.0, round=1.6)
CHEST_E = dict(c=(0.0, 1.5, 42.0), r=(10.5, 9.2, 12.0))     # torso = chest + belly blended: a column
BELLY_E = dict(c=(0.0, 0.5, 30.0), r=(11.0, 9.6, 10.0))
TORSO_BLEND = 6.0
SHORTS = dict(x=4.8, c=(0.0, 1.5, 21.5), r=(5.0, 5.5, 4.2))   # red thighs (mirrored in x)
HEAD = dict(c=(0.0, 0.5, 60.5), r=(10.5, 10.5, 11.5))         # an egg, taller than wide
NECK_BLEND = 6.0
# Wings: a flat blade hanging from the shoulder, tilted out at the bottom and swept back, ending in three flat
# feathers (all red, as on the costume). Built in the wing's own frame: u = thickness, v = front-back, a = down the wing.
WING = dict(shoulder=(10.6, 1.5, 47.0), tilt_deg=15.0, sweep_deg=10.0,
            bulb=((0.0, 0.0, 1.5), (3.4, 5.0, 4.5)), blade=((0.0, 0.8, 8.5), (2.3, 6.4, 9.0)),
            feathers=[(-1, 17.5), (0, 19.3), (1, 20.4)],   # (front/mid/back, tip distance down the wing)
            feather_root=12.0, feather_spread=3.4, feather_r=(2.4, 0.9), feather_flat=1.45)
CAP = dict(grow=1.2, cut_z=65.4, brim_c=(0.0, -11.5, 67.2), brim_r=(8.6, 7.6, 1.2), brim_tilt_deg=0.0, button_r=1.3)
# v9: friendly eyes, like the keychain's: a white eyeball, a big black pupil set a little low and toward the beak,
# and a white highlight at the pupil's upper left (as seen from the front). Pupil and highlight are painted onto the
# eyeball (cone decals from its centre), so they're flush: nothing thin to print. Offsets are on the eye's front, in mm.
# v10: on the sides of the head like a real bird (owner): each eye sits `azimuth` degrees round from straight ahead,
# turned to face out from the head; pupil_at x is toward the front of the head (so he still glances forward).
EYE = dict(azimuth=58.0, z=62.2, r=(2.5, 1.6, 2.6), pupil_r=1.75, pupil_at=(0.55, -0.35), highlight_r=0.55,
           highlight_at=(-0.6, 0.65))
# v8: the mouth is a smile, not an "O" (owner: v7 looked surprised). The opening's top edge (under the upper beak)
# is nearly straight, its bottom edge (the lower lip) dips in the middle and both rise to pinched, upturned corners.
# Heights are z at the centre and at the corners (|x| = half_w); the cavity runs back into the head (red back wall).
SMILE = dict(half_w=6.2, top=(54.0, 54.7), bottom=(50.2, 53.3), back_y=-6.5, edge_round=1.4)
# Beak: one rounded white muzzle: a bulk, a short downward hook, a narrow blaze up between the eyes and a lower jaw,
# blended; the mouth is a cavity cut into it, deep enough that its back wall is the red head (the red inside).
MUZZLE = dict(bulk=((0.0, -11.5, 56.5), (7.0, 8.0, 5.0)),
              hook=((0.0, -16.0, 56.8), (0.0, -20.4, 54.3), 4.0, 1.9),
              blaze=((0.0, -8.5, 61.0), (3.0, 3.5, 3.8)),
              jaw=((0.0, -10.5, 49.6), (6.6, 7.5, 3.2)),
              mouth_round=1.0,
              corner=((5.6, -9.4, 52.3), (2.4, 4.2, 2.8)))   # mouth corners: upper and lower beak join here (mirrored)
LEG = dict(x=5.0, foot_x=5.8, y=1.5, z0=7.5, z1=20.0, r0=2.6, r1=3.1)
FOOT = dict(splay_deg=12.0, heel=(0.0, 2.5, 6.2), heel_r=(3.4, 3.8, 2.3), toe_root=(0.0, 0.5, 6.0),
            toe_len=7.5, toe_r=(2.0, 1.7), toe_spread_deg=30.0)
FOOT_FLOOR = BASE["h"] - 0.8   # soles and claws are cut flat here, inside the base
CLAW = dict(len=1.9, drop=2.6, r=(1.0, 0.45))
CHEST = dict(apex=(0.0, 1.5, 38.0), y_ref=-8.0)   # the blaze outline is made by chest_blaze()
BB = dict(letters=[(-1.9, 71.3), (1.9, 70.3)], height=2.7, y_ref=-6.3)   # staggered like the costume's cap


# ------------------------------------------------------------------------------------------------
# Signed-distance helpers (negative inside; broadcastable arrays X[:,None,None], Y[None,:,None], Z[None,None,:])
# ------------------------------------------------------------------------------------------------

def smin(a, b, k):
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k * 0.25


def smax(a, b, k):
    return -smin(-a, -b, k)


def ellipsoid(X, Y, Z, c, r):
    x, y, z = (X - c[0]) / r[0], (Y - c[1]) / r[1], (Z - c[2]) / r[2]
    k0 = np.sqrt(x * x + y * y + z * z)
    k1 = np.sqrt((x / r[0]) ** 2 + (y / r[1]) ** 2 + (z / r[2]) ** 2)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-6)


def round_cone(X, Y, Z, a, b, ra, rb):
    """Tapered capsule from a (radius ra) to b (radius rb). Approximate distance, exact surface for small tapers."""
    a, b = np.asarray(a, np.float32), np.asarray(b, np.float32)
    ba = b - a
    px, py, pz = X - a[0], Y - a[1], Z - a[2]
    t = np.clip((px * ba[0] + py * ba[1] + pz * ba[2]) / float(ba @ ba), 0.0, 1.0)
    dx, dy, dz = px - ba[0] * t, py - ba[1] * t, pz - ba[2] * t
    return np.sqrt(dx * dx + dy * dy + dz * dz) - (ra + (rb - ra) * t)


def chain(X, Y, Z, pts, k):
    """Smooth union of round cones through (x, y, z, r) points."""
    d = None
    for p, q in zip(pts[:-1], pts[1:]):
        e = round_cone(X, Y, Z, p[:3], q[:3], p[3], q[3])
        d = e if d is None else smin(d, e, k)
    return d


def blob(X, Y, Z, ells, k):
    """Smooth union of ellipsoids [(centre, radii), ...]."""
    d = None
    for c, r in ells:
        e = ellipsoid(X, Y, Z, c, r)
        d = e if d is None else smin(d, e, k)
    return d


def rot_z(v, deg):
    a = np.radians(deg)
    x, y = v[0], v[1]
    return (x * np.cos(a) - y * np.sin(a), x * np.sin(a) + y * np.cos(a), v[2])


def mirror_x(f):
    """Field of f(X) plus its mirror image across x = 0."""
    return lambda X, Y, Z: np.minimum(f(X, Y, Z), f(-X, Y, Z))


# ------------------------------------------------------------------------------------------------
# Shape groups
# ------------------------------------------------------------------------------------------------

def wing_frame():
    """(origin S, outward U, down-the-wing D, sweep tangent) of the right wing."""
    a, sw = np.radians(WING["tilt_deg"]), np.tan(np.radians(WING["sweep_deg"]))
    return np.array(WING["shoulder"]), np.array([np.cos(a), 0, np.sin(a)]), np.array([np.sin(a), 0, -np.cos(a)]), sw


def wing(X, Y, Z):
    S, U, D, sw = wing_frame()
    dx, dy, dz = X - S[0], Y - S[1], Z - S[2]
    a = dx * D[0] + dz * D[2]
    u = dx * U[0] + dz * U[2]
    v = dy - a * sw
    d = smin(ellipsoid(u, v, a, *WING["bulb"]), ellipsoid(u, v, a, *WING["blade"]), 3.0)
    for k, tip in WING["feathers"]:
        f = round_cone(u * WING["feather_flat"], v, a, (0, k * WING["feather_spread"], WING["feather_root"]),
                       (0, k * WING["feather_spread"] * 1.1, tip), *WING["feather_r"])
        d = smin(d, f / WING["feather_flat"], 1.2)
    return d


def head_field(X, Y, Z):
    return ellipsoid(X, Y, Z, HEAD["c"], HEAD["r"])


def red_body(X, Y, Z):
    d = smin(ellipsoid(X, Y, Z, CHEST_E["c"], CHEST_E["r"]), ellipsoid(X, Y, Z, BELLY_E["c"], BELLY_E["r"]),
             TORSO_BLEND)
    for side in (1, -1):
        d = smin(d, ellipsoid(X, Y, Z, np.add(SHORTS["c"], (side * SHORTS["x"], 0, 0)), SHORTS["r"]), 3.0)
    d = smin(d, head_field(X, Y, Z), NECK_BLEND)
    return smin(d, mirror_x(wing)(X, Y, Z), 3.0)


def cap(X, Y, Z):
    g = CAP["grow"]
    dome = head_field(X, Y, Z) - g      # follows the real head (cheeks included), so nothing pokes through
    dome = smax(dome, CAP["cut_z"] - Z, 0.6)
    top = HEAD["c"][2] + HEAD["r"][2] + g
    button = ellipsoid(X, Y, Z, (0.0, 0.0, top), (CAP["button_r"],) * 2 + (CAP["button_r"] * 0.8,))
    return smin(dome, button, 0.8)


def brim_mesh():
    """The bill as an analytic ellipsoid mesh (a marching-cubes one this thin cut the dome with sliver faces)."""
    c = CAP["brim_c"]
    return (m3d.Manifold.sphere(1.0, 128).scale(tuple(CAP["brim_r"])).rotate((CAP["brim_tilt_deg"], 0.0, 0.0))   # + = front down
            .translate(tuple(c)))


def foot_parts(side):
    """Toe tip points and directions for one foot (side = +1 right, -1 left)."""
    tips = []
    root = np.add(FOOT["toe_root"], (side * LEG["foot_x"], 0, 0))
    for k in (-1, 0, 1):
        ang = side * FOOT["splay_deg"] + k * FOOT["toe_spread_deg"]
        d = np.array(rot_z((0.0, -1.0, 0.0), ang))
        tips.append((root, root + d * FOOT["toe_len"], d))
    return tips


def muzzle(X, Y, Z):
    m = MUZZLE
    d = ellipsoid(X, Y, Z, *m["bulk"])
    d = smin(d, round_cone(X, Y, Z, *m["hook"]), 3.0)
    d = smin(d, ellipsoid(X, Y, Z, *m["blaze"]), 3.0)
    d = smin(d, ellipsoid(X, Y, Z, *m["jaw"]), 2.5)
    cx = m["corner"][0]
    for side in (1, -1):
        d = smin(d, ellipsoid(X, Y, Z, (side * cx[0], cx[1], cx[2]), m["corner"][1]), 2.0)
    return smax(d, -smile(X, Y, Z), m["mouth_round"])


def smile(X, Y, Z):
    """The mouth opening (see SMILE): between a bottom curve and a top curve, both parabolas in x, open at the front."""
    sm = SMILE
    u = (X / sm["half_w"]) ** 2
    top = sm["top"][0] + (sm["top"][1] - sm["top"][0]) * u
    bottom = sm["bottom"][0] + (sm["bottom"][1] - sm["bottom"][0]) * u
    k = sm["edge_round"]
    d = smax(bottom - Z, Z - top, k)
    d = smax(d, np.abs(X) - sm["half_w"], k)
    return smax(d, Y - sm["back_y"], k)


def white_parts(X, Y, Z):
    d = muzzle(X, Y, Z)
    for side in (1, -1):
        leg = round_cone(X, Y, Z, (side * LEG["foot_x"], LEG["y"], LEG["z0"]), (side * LEG["x"], LEG["y"], LEG["z1"]),
                         LEG["r0"], LEG["r1"])
        foot = ellipsoid(X, Y, Z, np.add(FOOT["heel"], (side * LEG["foot_x"], 0, 0)), FOOT["heel_r"])
        for root, tip, _ in foot_parts(side):
            foot = smin(foot, round_cone(X, Y, Z, root, tip, *FOOT["toe_r"]), 2.0)
        d = np.minimum(d, smin(leg, foot, 3.0))
    return np.maximum(d, FOOT_FLOOR - Z)     # flat soles, sunk into the base


def eye_frame(side):
    """(centre, heading in degrees about Z) of one eye. The centre is found on the real head surface along the ray
    from the head's axis at that heading, 0.9 inside it (the eye stands ~0.7 proud; at 0.6 and 0.4 its rim grazed the
    head at the side and left slivers)."""
    phi = side * EYE["azimuth"]
    a = np.radians(phi)
    d = np.array([np.sin(a), -np.cos(a), 0.0])
    axis = np.array([0.0, HEAD["c"][1], EYE["z"]])
    ts = np.linspace(20.0, 0.0, 4001, dtype=np.float32)
    pts = axis[None, :] + ts[:, None] * d[None, :]
    f = red_body(pts[:, 0].astype(np.float32), pts[:, 1].astype(np.float32), pts[:, 2].astype(np.float32))
    t_surf = float(ts[np.argmax(f < 0)])
    return axis + (t_surf - 0.9) * d, phi


def claws(X, Y, Z):
    d = None
    for side in (1, -1):
        for _, tip, dirn in foot_parts(side):
            end = tip + dirn * CLAW["len"] + np.array([0, 0, -CLAW["drop"]])
            e = round_cone(X, Y, Z, tip - dirn * 0.6, end, *CLAW["r"])
            d = e if d is None else np.minimum(d, e)
    return np.maximum(d, FOOT_FLOOR + 0.35 - Z)    # not coplanar with the soles (coplanar faces break booleans)


def eyes():
    """(eyeballs, pupil paint): white analytic eyeballs, and the regions that paint them black (pupil cone minus
    highlight cone). Each eye is built facing -Y at the origin, then turned to its heading and moved into place.
    In that local frame the highlight's x is as seen by someone looking straight at the eye."""
    balls = paint = None
    for side in (1, -1):
        c, phi = eye_frame(side)
        ball = m3d.Manifold.sphere(1.0, 96).scale(tuple(EYE["r"]))
        px, pz = -side * EYE["pupil_at"][0], EYE["pupil_at"][1]     # local -x of the right eye points forward
        pupil = m3d.CrossSection.circle(EYE["pupil_r"], 64).translate((px, pz))
        hl = m3d.CrossSection.circle(EYE["highlight_r"], 48).translate(
            (px + EYE["highlight_at"][0], pz + EYE["highlight_at"][1]))
        y_front = -EYE["r"][1]
        p = cone_decal(pupil, (0.0, 0.0, 0.0), y_front) - cone_decal(hl, (0.0, 0.0, 0.0), y_front)
        ball, p = (m.rotate((0.0, 0.0, phi)).translate(tuple(c)) for m in (ball, p))
        balls, paint = (ball, p) if balls is None else (balls + ball, paint + p)
    return balls, paint


def base(X, Y, Z):
    c, r, h, rr = BASE["c"], BASE["r"], BASE["h"], BASE["round"]
    # ellipse distance (approximate, fine for a near-circle)
    ex, ey = (X - c[0]) / r[0], (Y - c[1]) / r[1]
    d2 = (np.sqrt(ex * ex + ey * ey) - 1.0) * min(r)
    qx = d2 + rr
    qz = np.abs(Z - h / 2) - h / 2 + rr
    return np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qz, 0) ** 2) + np.minimum(np.maximum(qx, qz), 0) - rr


# ------------------------------------------------------------------------------------------------
# Meshing and manifold glue
# ------------------------------------------------------------------------------------------------

def mesh_field(f, lo, hi, h=GRID, faces=GROUP_FACES):
    axes = [np.arange(l - 2 * h, u + 2 * h, h, dtype=np.float32) for l, u in zip(lo, hi)]
    X, Y, Z = axes[0][:, None, None], axes[1][None, :, None], axes[2][None, None, :]
    field = np.broadcast_to(f(X, Y, Z), tuple(len(a) for a in axes)).astype(np.float32).copy()
    field[[0, -1]] = 1.0
    field[:, [0, -1]] = 1.0
    field[:, :, [0, -1]] = 1.0
    v, fc, _, _ = measure.marching_cubes(field, 0.0, spacing=(h, h, h))
    m = trimesh.Trimesh(v + [a[0] for a in axes], fc, process=True)
    m.fix_normals()
    if faces and len(m.faces) > faces:
        m = decimate(m, faces)
    return to_manifold(m)


def decimate(mesh, target):
    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(mesh.vertices, mesh.faces))
    ms.meshing_decimation_quadric_edge_collapse(targetfacenum=int(target), preservenormal=True, preservetopology=True,
                                                qualitythr=0.6, planarquadric=True)
    m = ms.current_mesh()
    out = trimesh.Trimesh(m.vertex_matrix(), m.face_matrix(), process=True)
    out.fix_normals()
    return out


def to_manifold(mesh):
    man = m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(mesh.vertices, np.float32),
                                tri_verts=np.asarray(mesh.faces, np.uint32)))
    assert man.status() == m3d.Error.NoError, man.status()
    return man


def from_manifold(man):
    m = man.to_mesh()
    return trimesh.Trimesh(m.vert_properties[:, :3], m.tri_verts, process=False)


def drop_slivers(man, min_volume=0.01):
    """Remove zero-volume shells that booleans can leave where surfaces meet at a shallow angle."""
    return m3d.Manifold.compose([p for p in man.decompose() if abs(p.volume()) >= min_volume])


def prism_xz(poly_xz, y0, y1):
    """Extrude an XZ-plane outline (or a CrossSection) along Y from y0 to y1. Readable from the front (-Y)."""
    cs = poly_xz if isinstance(poly_xz, m3d.CrossSection) else m3d.CrossSection([np.asarray(poly_xz, np.float64)], m3d.FillRule.EvenOdd)
    # extrude along +Z, then rotate +90° about X: (x, y, z) -> (x, -z, y), so drawing y becomes Z and depth goes to -Y
    return cs.extrude(y1 - y0).rotate((90.0, 0.0, 0.0)).translate((0.0, y1, 0.0))


def cone_decal(poly_xz, apex, y_ref):
    """Decal region: the XZ outline as drawn at depth y_ref, swept as a cone from `apex` (a point inside the part) out
    through the front. Its walls meet a rounded surface nearly square on, unlike a straight prism, so the colour
    boundary is clean (no grazing slivers)."""
    ax, ay, az = apex
    y_back, y_front = ay - 1.0, y_ref - 12.0
    pr = prism_xz(poly_xz, y_front, y_back)

    def warp(v):
        s = (v[:, 1] - ay) / (y_ref - ay)
        out = v.copy()
        out[:, 0] = ax + (v[:, 0] - ax) * s
        out[:, 2] = az + (v[:, 2] - az) * s
        return out
    return pr.warp_batch(warp)


def bb_text():
    """The cap's two B's, staggered (the costume's: left one higher)."""
    out = None
    for x, z in BB["letters"]:
        tp = TextPath((0, 0), "B", size=1.0, prop=FontProperties(family="DejaVu Sans", weight="bold"))
        cs = m3d.CrossSection([np.asarray(p, np.float64) for p in tp.to_polygons() if len(p) >= 3], m3d.FillRule.EvenOdd)
        lo, hi = np.array(cs.bounds()[:2]), np.array(cs.bounds()[2:])
        sc = BB["height"] / (hi[1] - lo[1])
        cs = cs.translate(tuple(-(lo + hi) / 2)).scale((sc, sc)).translate((x, z))
        out = cs if out is None else out + cs
    return out


def chest_blaze():
    """The white blaze: narrow at the neck, jagged spikes out to both sides, widening to the belly, with a zigzag
    bottom edge (white points hanging into the red). The left side is shifted up a little: the costume's isn't
    symmetric."""
    right = [(1.0, 51.0), (2.6, 47.0), (5.6, 48.6), (4.0, 44.2), (7.6, 44.6), (5.6, 40.2), (8.8, 39.4), (6.8, 35.4),
             (9.4, 33.0), (8.8, 27.0)]
    xs = np.linspace(8.8, -8.8, 9)[1:-1]
    bottom = [(x, 23.2 if i % 2 == 0 else 26.6) for i, x in enumerate(xs)]
    left = [(-x, z + 1.0) for x, z in reversed(right)]
    left[0] = (-8.8, 27.0)
    return right + bottom + left


# ------------------------------------------------------------------------------------------------
# Build
# ------------------------------------------------------------------------------------------------

def build_bodies():
    print("meshing shape groups ...")
    red = mesh_field(red_body, (-22, -16, 13), (22, 16, 74))
    capm = mesh_field(cap, (-18, -26, 63), (18, 18, 78))
    white = mesh_field(white_parts, (-14, -26, 3), (14, 8, 67))
    balls, pupils = eyes()
    black = mesh_field(claws, (-26, -32, 3), (26, 0, 12), h=0.2) + brim_mesh()
    basem = mesh_field(base, (-32, -32, 0), (32, 26, BASE["h"]), faces=20000)

    # Scale and place the inputs before the booleans: transforming the finished bodies re-rounds their float32
    # vertices and can flip the thinnest slivers at colour borders into self-intersections.
    allm = red + capm + white + black + basem
    lo, hi = np.array(allm.bounding_box()[:3]), np.array(allm.bounding_box()[3:])
    s = HEIGHT_MM / (hi[2] - lo[2])
    shift = (-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2])

    def place(m):
        return m.translate(shift).scale((s, s, s))
    red, capm, white, black, balls, pupils, basem = map(place, (red, capm, white, black, balls, pupils, basem))
    red_solid = red + capm
    head_c = np.add(HEAD["c"], (0.0, 0.0, 0.5))
    # Decals on the body (chest) and on the cap (BB) are kept apart.
    body_decals = place(cone_decal(chest_blaze(), CHEST["apex"], CHEST["y_ref"]))
    cap_decals = place(cone_decal(bb_text(), head_c, BB["y_ref"]))

    # Never subtract a body that shares surface with the one it's cut from (red ^ decals lies on red's skin):
    # coincident faces leave zero-volume slivers. So red loses the decal regions themselves, not their red-clipped copies.
    # The eyeballs are split by their pupil regions: (balls ^ pupils) is black, (balls - pupils) white; red loses the
    # whole balls in one go (subtracting the two halves one by one would cut along shared faces).
    black_other = black + basem
    black_b = black_other + (balls ^ pupils)
    white_b = (white + (balls - pupils) + ((red ^ body_decals) - capm) + (capm ^ cap_decals)) - black_other
    red_b = ((red - body_decals) + (capm - cap_decals)) - (white + balls + black_other)
    merged = red_solid + white + balls + black + basem   # raw shapes: the colour bodies share faces exactly
    bodies = {"red": red_b, "white": white_b, "black": black_b}
    return {k: drop_slivers(v) for k, v in bodies.items()}, drop_slivers(merged), s


def render_colour(meshes, path, views):
    """Shaded multi-colour views (numpy z-buffer, like tools/render.py, with per-face colours)."""
    import render as rd
    fig, axes = plt.subplots(1, len(views), figsize=(6 * len(views), 7))
    for ax, (title, (d, up)) in zip(np.atleast_1d(axes), views.items()):
        img = None
        cat = trimesh.util.concatenate([m for m, _ in meshes])
        cols = np.vstack([np.tile(matplotlib.colors.to_rgb(c), (len(m.faces), 1)) for m, c in meshes])
        img, ext = raster_multi(cat, cols, d, up, rd)
        ax.imshow(img, extent=ext)
        ax.set_title(title)
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=80)
    plt.close(fig)


def raster_multi(mesh, cols, view_dir, up, rd, px=700):
    d = np.asarray(view_dir, float)
    d /= np.linalg.norm(d)
    right = np.cross(d, up)
    right /= np.linalg.norm(right)
    upv = np.cross(right, d)
    v = mesh.vertices
    sx, sy, depth = v @ right, v @ upv, v @ d
    lo, hi = np.array([sx.min(), sy.min()]), np.array([sx.max(), sy.max()])
    pad = 0.04 * (hi - lo).max()
    lo, hi = lo - pad, hi + pad
    scale = px / (hi - lo).max()
    W, H = np.ceil((hi - lo) * scale).astype(int) + 1
    X, Y = (sx - lo[0]) * scale, (hi[1] - sy) * scale
    light = -d + 0.6 * upv - 0.4 * right
    light /= np.linalg.norm(light)
    shade = 0.3 + 0.7 * np.clip(-(mesh.face_normals @ d) * 0.4 + np.abs(mesh.face_normals @ light) * 0.6, 0, 1)
    zbuf = np.full((H, W), np.inf)
    img = np.ones((H, W, 3))
    for f, s, c in zip(mesh.faces, shade, cols):
        x, y, z = X[f], Y[f], depth[f]
        x0, x1 = int(max(np.floor(x.min()), 0)), int(min(np.ceil(x.max()), W - 1))
        y0, y1 = int(max(np.floor(y.min()), 0)), int(min(np.ceil(y.max()), H - 1))
        if x1 < x0 or y1 < y0:
            continue
        den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(den) < 1e-12:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / den
        b = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / den
        cc = 1 - a - b
        inside = (a >= -1e-6) & (b >= -1e-6) & (cc >= -1e-6)
        zz = a * z[0] + b * z[1] + cc * z[2]
        sub = zbuf[y0:y1 + 1, x0:x1 + 1]
        win = inside & (zz < sub)
        sub[win] = zz[win]
        img[y0:y1 + 1, x0:x1 + 1][win] = c * s
    return img, (lo[0], lo[0] + W / scale, hi[1] - H / scale, hi[1])


def main():
    OUT.mkdir(exist_ok=True)
    RENDERS.mkdir(exist_ok=True)
    bodies, merged_man, s = build_bodies()

    meshes = {}
    for col, b in bodies.items():
        m = from_manifold(b)
        info = mk.report(m)
        print(col, info)
        assert info["watertight"] and info["self_intersecting_faces"] == 0, (col, info)
        m.export(OUT / f"{NAME}-{col}.stl")
        meshes[col] = m

    merged = from_manifold(merged_man)
    info = mk.report(merged)
    print("merged", info)
    assert info["watertight"] and info["self_intersecting_faces"] == 0, info
    merged.export(OUT / f"{NAME}.stl")

    scene = trimesh.Scene()
    for col in ("red", "white", "black"):
        scene.add_geometry(meshes[col], node_name=col, geom_name=col)
    scene.export(OUT / f"{NAME}-multicolor.3mf")

    view = {}
    for col, m in meshes.items():
        v = decimate(m, VIEW_FACES) if len(m.faces) > VIEW_FACES else m
        v.export(RENDERS / f"view-{col}.stl")
        view[col] = v

    e = merged.extents
    params = {
        "height": round(float(e[2]), 1), "width": round(float(e[0]), 1), "depth": round(float(e[1]), 1),
        "base_w": round(2 * BASE["r"][0] * s, 1), "base_d": round(2 * BASE["r"][1] * s, 1),
        "base_h": round(BASE["h"] * s, 1),
        "eye_h": round(2 * EYE["r"][2] * s, 1), "bb_h": round(BB["height"] * s, 1),
        "claw_tip_d": round(2 * CLAW["r"][1] * s, 2), "highlight_d": round(2 * EYE["highlight_r"] * s, 2),
        "pupil_d": round(2 * EYE["pupil_r"] * s, 1),
    }
    report = {"merged": info, "params_mm": params, "design_scale": round(s, 4),
              "scale_status": "owner's choice (no real object): HEIGHT_MM = %g" % HEIGHT_MM,
              "bodies": {c: mk.report(m, check_self_intersections=False) for c, m in meshes.items()}}
    (OUT / "report.json").write_text(json.dumps(report, indent=2))

    parts = [(view[c], COLOURS[c]) for c in ("red", "white", "black")]
    render_colour(parts, RENDERS / "figure.png", {
        "front": (np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, 1.0])),
        "three-quarter": (np.array([0.7, 1.0, -0.35]), np.array([0.0, 0.0, 1.0])),
        "side": (np.array([-1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0])),
        "back": (np.array([0.0, -1.0, -0.2]), np.array([0.0, 0.0, 1.0])),
    })
    z_cut = 0.57 * float(e[2])   # head close-up: everything above the neck
    head = [(m.slice_plane([0, 0, z_cut], [0, 0, 1]), c) for m, c in parts]
    render_colour(head, RENDERS / "head.png", {
        "front": (np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, 1.0])),
        "three-quarter": (np.array([0.8, 1.0, -0.2]), np.array([0.0, 0.0, 1.0])),
        "side": (np.array([-1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0])),
    })
    print("done:", params)


if __name__ == "__main__":
    main()
