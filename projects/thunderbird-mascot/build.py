"""Reproducible build for the Black Bob Thunderbird mascot figurine.

    python projects/thunderbird-mascot/build.py        (~1-2 min)

source/costume-photo-2026-11-14-instagram.png is the reference (the costume mascot at school). There is no scan:
the figure is a chibi interpretation built from smooth signed-distance shapes, meshed with marching cubes.

  -> four shape groups, each one smooth field (parts of one group blend into each other):
       red body (torso, head, wings, tail, tongue) | red cap (dome, brim, button) |
       white parts (legs, feet, beak) | black parts (eyes, claws)
  -> colour "decals" painted onto the red with exact boolean regions: white chest starburst, white zigzag hem,
     white zigzag wing tips, white face mask, white "BB" on the cap
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
BASE = dict(c=(0.0, -2.0), r=(23.0, 20.0), h=5.0, round=1.6)
# v2: slimmer (owner: v1 "too pudgy and bloated"). Torso and head narrower and deeper-set, thinner wings and legs.
BODY = dict(c=(0.0, 2.0, 36.0), r=(12.0, 10.5, 17.5))
HEAD = dict(c=(0.0, 0.0, 60.0), r=(12.0, 11.5, 12.8))
NECK_BLEND = 4.0
# v3: real wings (owner: "more wing like"). A flat blade hanging from the shoulder, tilted out at the bottom and swept
# back, ending in three flat primary feathers. Shapes are in the wing's own frame: u = thickness (out from the body),
# v = front-back, a = distance down the wing.
WING = dict(shoulder=(11.2, 1.5, 46.0), tilt_deg=19.0, sweep_deg=12.0,
            bulb=((0.0, 0.0, 1.5), (3.4, 5.0, 4.5)), blade=((0.0, 0.8, 8.5), (2.3, 6.6, 9.0)),
            feathers=[(-1, 18.5), (0, 20.3), (1, 21.6)],   # (front/mid/back, tip distance down the wing)
            feather_root=12.0, feather_spread=3.6, feather_r=(2.4, 0.9), feather_flat=1.45)
TAIL = dict(c=(0.0, 11.5, 27.0), r=(5.5, 5.0, 2.4))
CAP = dict(grow=1.2, cut_z=65.3, brim_c=(0.0, -12.0, 66.3), brim_r=(9.8, 8.8, 1.5), brim_tilt_deg=8.0, button_r=1.4)
EYE = dict(x=4.5, z=62.0, r=(2.1, 1.3, 2.2), highlight_r=0.6, highlight_at=(0.5, 0.7))
# Beak: a broad, hooked eagle beak, slightly open. Ellipsoids blended along the beak: (centre, radii)
# v3: angular beak (owner: "more angular"). Each half is a side profile (y, z) cut by a top-view taper (x, y) and,
# for the upper beak, a roof that slopes off a ridge line: flat faces and crisp edges, a sharp downward hook.
UPPER_BEAK = dict(side=[(-5.0, 60.6), (-12.0, 59.9), (-19.0, 58.0), (-23.0, 51.0), (-20.4, 52.9), (-13.0, 54.4),
                        (-5.0, 54.2)],
                  top=[(-7.4, -4.0), (7.4, -4.0), (1.5, -23.5), (-1.5, -23.5)], roof=0.4)
LOWER_BEAK = dict(side=[(-5.0, 55.0), (-12.0, 53.4), (-17.8, 52.5), (-14.8, 49.8), (-5.0, 48.2)],
                  top=[(-6.0, -4.0), (6.0, -4.0), (1.2, -19.0), (-1.2, -19.0)])
BEAK_EDGE = 0.5   # edge rounding (mm): just enough to print cleanly
LEG = dict(x=5.8, foot_x=6.4, y=2.0, z0=7.5, z1=25.0, r0=2.9, r1=3.5)
# v2: feet much smaller than the costume's (owner's pick)
FOOT = dict(splay_deg=12.0, heel=(0.0, 2.5, 6.2), heel_r=(3.4, 3.8, 2.3), toe_root=(0.0, 0.5, 6.0),
            toe_len=7.5, toe_r=(2.0, 1.7), toe_spread_deg=30.0)
FOOT_FLOOR = BASE["h"] - 0.8   # soles and claws are cut flat here, inside the base
CLAW = dict(len=1.9, drop=2.6, r=(1.0, 0.45))
HEM = dict(c=(0.0, 2.0), radius=19.0, z=25.5, amp=2.2, teeth=11)
WING_TIP = dict(start=14.3, amp=1.4, teeth=6, radius=(3.4, 9.5))   # white zigzag on the feather ends (wing frame)
CHEST = dict(c=(0.0, 39.5), y_ref=-8.4, spikes=7, r_out=7.6, r_in=4.0, twist_deg=-8.0)  # XZ plane
FACE_MASK = dict(eye_r=4.0, eye_z=62.4, chin=(0.0, 58.6, 5.6, 3.7))   # white goggles round the eyes + a band down
                                                                       # to the beak (chin: x, z, half-width, half-height)
BB = dict(text="BB", height=3.6, z=70.0, x=0.0, y_ref=-9.2)


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


def red_body(X, Y, Z):
    d = ellipsoid(X, Y, Z, BODY["c"], BODY["r"])
    d = smin(d, ellipsoid(X, Y, Z, HEAD["c"], HEAD["r"]), NECK_BLEND)
    d = smin(d, mirror_x(wing)(X, Y, Z), 3.0)
    d = smin(d, ellipsoid(X, Y, Z, TAIL["c"], TAIL["r"]), 3.0)
    return d   # v2: no tongue (it grazed the beak and left slivers); the head shows red in the open mouth


def cap(X, Y, Z):
    g = CAP["grow"]
    dome = ellipsoid(X, Y, Z, HEAD["c"], np.add(HEAD["r"], g))
    dome = smax(dome, CAP["cut_z"] - Z, 0.6)
    # brim: a thin ellipsoid tilted down at the front (rotate about X through the brim centre)
    c = CAP["brim_c"]
    a = np.radians(CAP["brim_tilt_deg"])
    yy, zz = Y - c[1], Z - c[2]
    yr = yy * np.cos(a) - zz * np.sin(a)
    zr = yy * np.sin(a) + zz * np.cos(a)
    brim = ellipsoid(X, yr, zr, (c[0], 0.0, 0.0), CAP["brim_r"])
    top = HEAD["c"][2] + HEAD["r"][2] + g
    button = ellipsoid(X, Y, Z, (0.0, 0.0, top), (CAP["button_r"],) * 2 + (CAP["button_r"] * 0.8,))
    return smin(smin(dome, brim, 1.5), button, 0.8)


def foot_parts(side):
    """Toe tip points and directions for one foot (side = +1 right, -1 left)."""
    tips = []
    root = np.add(FOOT["toe_root"], (side * LEG["foot_x"], 0, 0))
    for k in (-1, 0, 1):
        ang = side * FOOT["splay_deg"] + k * FOOT["toe_spread_deg"]
        d = np.array(rot_z((0.0, -1.0, 0.0), ang))
        tips.append((root, root + d * FOOT["toe_len"], d))
    return tips


def sd_polygon(px, py, verts):
    """Signed distance to a simple 2D polygon (any winding), vectorised (from projects/wagon-cup-holder/sdf.py)."""
    v = np.asarray(verts, dtype=np.float32)
    shape = np.broadcast(px, py).shape
    d = np.full(shape, np.inf, dtype=np.float32)
    s = np.ones(shape, dtype=np.float32)
    j = len(v) - 1
    for i in range(len(v)):
        ex, ey = v[j, 0] - v[i, 0], v[j, 1] - v[i, 1]
        wx, wy = px - v[i, 0], py - v[i, 1]
        t = np.clip((wx * ex + wy * ey) / (ex * ex + ey * ey + 1e-12), 0.0, 1.0)
        bx, by = wx - ex * t, wy - ey * t
        d = np.minimum(d, bx * bx + by * by)
        c1, c2, c3 = py >= v[i, 1], py < v[j, 1], ex * wy > ey * wx
        s = np.where((c1 & c2 & c3) | (~c1 & ~c2 & ~c3), -s, s)
        j = i
    return s * np.sqrt(d)


def angular_beak(X, Y, Z, spec):
    d = smax(sd_polygon(Y, Z, spec["side"]), sd_polygon(X, Y, spec["top"]), BEAK_EDGE)
    if "roof" in spec:   # faces sloping off the ridge (the profile's top edge, up to the hook)
        top = spec["side"][:3]
        ridge = np.interp(-Y, [-p[0] for p in top], [p[1] for p in top])
        roof = (Z + spec["roof"] * np.abs(X) - ridge) / np.hypot(1.0, spec["roof"])
        d = smax(d, roof, BEAK_EDGE)
    return d


def white_parts(X, Y, Z):
    d = np.minimum(angular_beak(X, Y, Z, UPPER_BEAK), angular_beak(X, Y, Z, LOWER_BEAK))
    for side in (1, -1):
        leg = round_cone(X, Y, Z, (side * LEG["foot_x"], LEG["y"], LEG["z0"]), (side * LEG["x"], LEG["y"], LEG["z1"]),
                         LEG["r0"], LEG["r1"])
        foot = ellipsoid(X, Y, Z, np.add(FOOT["heel"], (side * LEG["foot_x"], 0, 0)), FOOT["heel_r"])
        for root, tip, _ in foot_parts(side):
            foot = smin(foot, round_cone(X, Y, Z, root, tip, *FOOT["toe_r"]), 2.0)
        d = np.minimum(d, smin(leg, foot, 3.0))
    return np.maximum(d, FOOT_FLOOR - Z)     # flat soles, sunk into the base


def eye_centre(side):
    x, z = side * EYE["x"], EYE["z"]
    c, r = HEAD["c"], HEAD["r"]
    y_surf = c[1] - r[1] * np.sqrt(1 - (x / r[0]) ** 2 - ((z - c[2]) / r[2]) ** 2)
    return np.array([x, y_surf + 0.9, z])          # sits 0.6 mm proud of the head


def claws(X, Y, Z):
    d = None
    for side in (1, -1):
        for _, tip, dirn in foot_parts(side):
            end = tip + dirn * CLAW["len"] + np.array([0, 0, -CLAW["drop"]])
            e = round_cone(X, Y, Z, tip - dirn * 0.6, end, *CLAW["r"])
            d = e if d is None else np.minimum(d, e)
    return np.maximum(d, FOOT_FLOOR + 0.35 - Z)    # not coplanar with the soles (coplanar faces break booleans)


def eyes_and_highlights():
    """Eyes (black ellipsoids) and their highlights (white spheres) as clean analytic meshes: marching-cubes facets
    this small make sliver triangles where one is cut from the other."""
    eyes = hl = None
    for side in (1, -1):
        c = eye_centre(side)
        e = m3d.Manifold.sphere(1.0, 96).scale(tuple(EYE["r"])).translate(tuple(c))
        # upper inner, on the eye's front: a point on the eye's surface, the sphere centre 0.35 below it (so it
        # stands 0.35 proud and stays clear of where the eye meets the head)
        rx, ry, rz = EYE["r"]
        dx, dz = -side * EYE["highlight_at"][0], EYE["highlight_at"][1]
        dy = -ry * np.sqrt(1 - (dx / rx) ** 2 - (dz / rz) ** 2)
        n = np.array([dx / rx ** 2, dy / ry ** 2, dz / rz ** 2])
        p = c + np.array([dx, dy, dz])
        h = m3d.Manifold.sphere(EYE["highlight_r"], 48).translate(tuple(p - 0.35 * n / np.linalg.norm(n)))
        eyes, hl = (e, h) if eyes is None else (eyes + e, hl + h)
    return eyes, hl


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


def wing_tip_region(side):
    """White zigzag on the feather ends: a zigzag region built round the wing's own axis, mapped into its frame."""
    S, U, D, sw = wing_frame()
    ru, rv = WING_TIP["radius"]
    z = zigzag_region(0.0, 0.0, 1.0, -WING_TIP["start"], WING_TIP["amp"], WING_TIP["teeth"], -40.0).scale((ru, rv, 1.0))
    # local (u, v, h) with h = -a (up the wing) -> world; the sweep shears v with a
    m = np.array([[U[0], 0.0, -D[0], S[0]],
                  [U[1], 1.0, -D[1] - sw, S[1]],
                  [U[2], 0.0, -D[2], S[2]]])
    z = z.transform(m)
    return z.mirror((1.0, 0.0, 0.0)) if side < 0 else z


def drop_slivers(man, min_volume=0.01):
    """Remove zero-volume shells that booleans can leave where surfaces meet at a shallow angle."""
    return m3d.Manifold.compose([p for p in man.decompose() if abs(p.volume()) >= min_volume])


def zigzag_region(cx, cy, radius, z, amp, teeth, z_bottom):
    """Solid below a zigzag rim z(θ) = z ± amp around a vertical axis: the shape of a crown, points up."""
    n = 2 * teeth
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    zt = z + np.where(np.arange(n) % 2 == 0, amp, -amp)
    ring_top = np.c_[cx + radius * np.cos(th), cy + radius * np.sin(th), zt]
    ring_bot = np.c_[cx + radius * np.cos(th), cy + radius * np.sin(th), np.full(n, z_bottom)]
    v = np.vstack([ring_top, ring_bot, [[cx, cy, z]], [[cx, cy, z_bottom]]])
    ct, cb = 2 * n, 2 * n + 1
    f = []
    for i in range(n):
        j = (i + 1) % n
        f += [[ct, i, j], [cb, n + j, n + i], [i, n + i, n + j], [i, n + j, j]]
    m = trimesh.Trimesh(v, f, process=True)
    m.fix_normals()
    return to_manifold(m)


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


def face_mask():
    cs = m3d.CrossSection.circle(FACE_MASK["eye_r"], 96)
    eyes = cs.translate((EYE["x"], FACE_MASK["eye_z"])) + cs.translate((-EYE["x"], FACE_MASK["eye_z"]))
    x, z, hx, hz = FACE_MASK["chin"]
    chin = m3d.CrossSection.circle(1.0, 96).scale((hx, hz)).translate((x, z))
    # close the cusps where the circles meet (sharp notches there made sliver faces against the beak ridge)
    return (eyes + chin).offset(1.2, m3d.JoinType.Round, circular_segments=96).offset(
        -1.2, m3d.JoinType.Round, circular_segments=96)


def starburst():
    c, n = CHEST["c"], CHEST["spikes"]
    pts = []
    rng = np.random.default_rng(7)            # fixed: slightly uneven spikes, like the costume's patch
    for i in range(2 * n):
        a = np.radians(CHEST["twist_deg"]) + np.pi / 2 + i * np.pi / n
        r = CHEST["r_out"] * (0.8 + 0.25 * rng.random()) if i % 2 == 0 else CHEST["r_in"]
        pts.append((c[0] + r * np.cos(a), c[1] + r * np.sin(a)))
    return pts


def bb_text():
    tp = TextPath((0, 0), BB["text"], size=1.0, prop=FontProperties(family="DejaVu Sans", weight="bold"))
    polys = [np.asarray(p, np.float64) for p in tp.to_polygons() if len(p) >= 3]
    cs = m3d.CrossSection(polys, m3d.FillRule.EvenOdd)
    lo, hi = np.array(cs.bounds()[:2]), np.array(cs.bounds()[2:])
    s = BB["height"] / (hi[1] - lo[1])
    centre = (lo + hi) / 2
    return cs.translate(tuple(-centre)).scale((s, s)).translate((BB["x"], BB["z"]))


# ------------------------------------------------------------------------------------------------
# Build
# ------------------------------------------------------------------------------------------------

def build_bodies():
    print("meshing shape groups ...")
    red = mesh_field(red_body, (-24, -20, 15), (24, 22, 76))
    capm = mesh_field(cap, (-18, -26, 63), (18, 18, 78))
    white = mesh_field(white_parts, (-26, -32, 3), (26, 12, 64))
    eyes, hilite = eyes_and_highlights()
    black = mesh_field(claws, (-26, -32, 3), (26, 0, 12), h=0.2) + eyes
    basem = mesh_field(base, (-32, -32, 0), (32, 26, BASE["h"]), faces=20000)

    # Scale and place the inputs before the booleans: transforming the finished bodies re-rounds their float32
    # vertices and can flip the thinnest slivers at colour borders into self-intersections.
    allm = red + capm + white + black + basem
    lo, hi = np.array(allm.bounding_box()[:3]), np.array(allm.bounding_box()[3:])
    s = HEIGHT_MM / (hi[2] - lo[2])
    shift = (-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2])

    def place(m):
        return m.translate(shift).scale((s, s, s))
    red, capm, white, black, hilite, basem = map(place, (red, capm, white, black, hilite, basem))
    red_solid = red + capm
    head_c = np.add(HEAD["c"], (0.0, 0.0, 0.5))
    # Decals on the body (chest, hem, wing tips, face) and on the cap (BB) are kept apart, so the face colour can't
    # spill onto the brim above it.
    body_decals = place(cone_decal(starburst(), (0.0, BODY["c"][1], CHEST["c"][1]), CHEST["y_ref"])
                        + zigzag_region(HEM["c"][0], HEM["c"][1], HEM["radius"], HEM["z"], HEM["amp"], HEM["teeth"], 0.0)
                        + cone_decal(face_mask(), head_c, -13.0))
    for side in (1, -1):
        body_decals += place(wing_tip_region(side))
    cap_decals = place(cone_decal(bb_text(), head_c, BB["y_ref"]))

    # Never subtract a body that shares surface with the one it's cut from (red ^ decals lies on red's skin):
    # coincident faces leave zero-volume slivers. So red loses the decal regions themselves, not their red-clipped copies.
    black_b = (black - hilite) + basem
    white_add = white + hilite
    white_b = (white_add + ((red ^ body_decals) - capm) + (capm ^ cap_decals)) - black_b
    red_b = ((red - body_decals) + (capm - cap_decals)) - white_add - black_b
    merged = red_solid + white + hilite + black + basem   # raw shapes: the colour bodies share faces exactly
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
    print("done:", params)


if __name__ == "__main__":
    main()
