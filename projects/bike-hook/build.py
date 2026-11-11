"""Reproducible build for the vertical bike hook.

    python projects/bike-hook/build.py        (under a minute)

model.py (build123d) -> one constant-width extrusion of a side profile
  -> output/bike-hook.step / .stl      print pose: lying on its side, no supports
  -> output/report.json                checks, parameters, strength + screw estimates, wheel/spoke fit
  -> renders/model.png                 print pose: views + sections
  -> renders/in-use.png                on the 2x4 with a 700c wheel hung on it
  -> renders/asm-*.stl, ref-*.stl      world Z-up meshes for the viewer (X along the 2x4, Y out from it, Z up)

World frame: the 2x4's front face is Y = 0 and its top face is Z = 0; the wall is at Y = -board_depth.
"""

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / "tools"), str(HERE)]

import meshkit as mk  # noqa: E402
import numpy as np  # noqa: E402
import trimesh  # noqa: E402
from build123d import export_step  # noqa: E402
from model import HookParams, build_hook, print_pose, to_world  # noqa: E402
from render import render_sheet  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

OUT = HERE / "output"
RENDERS = HERE / "renders"

# --- Owner's numbers (none measured yet: these are typical values, see README "Open questions") -----------------
MEASURED = {}
BIKE_MASS_KG = 16.0          # assumed: a typical hybrid/gravel bike (road ~9, MTB ~14-16). Do NOT hang an e-bike on it
DYNAMIC_FACTOR = 3.0         # lifting the bike onto the hook, knocks, letting it drop the last few cm

# Printed PETG, stressed along the layers (this hook's print orientation). Conservative values for a 0.4 mm nozzle part:
PETG_SHORT_TERM_MPA = 30.0   # short-term failure stress along the layers (datasheets ~45-50 for XY bars)
PETG_SUSTAINED_MPA = 8.0     # keep the always-on (static) stress below this so it doesn't creep/sag over years

# --- Illustration wheel (700c road/gravel; change for the owner's wheel) -----------------------------------------
WHEEL = {
    "bed_r": 300.0,          # rim's inner (spoke-bed) radius: 700c ERD ~600 mm
    "rim_h": 22.0,           # rim radial depth
    "rim_w": 21.0,           # rim width
    "tire_w": 32.0,          # tire width (a 2.4 in MTB tire is ~60)
    "spokes": 32,
    "spoke_d": 2.0,
    "flange_r": 22.0,        # hub flange radius
    "flange_half": 35.0,     # hub flange offset from the wheel's centre plane
    "turn_deg": 80.0,        # how far the front wheel is turned (0 = straight, in line with the frame, perpendicular to the wall)
}


def world_mesh(mesh):
    m = mesh.copy()
    m.vertices = to_world(m.vertices)
    return m


# ---------------------------------------------------------------------------------------------------------------------
# Strength (beam estimate along the arm) and screw loads
# ---------------------------------------------------------------------------------------------------------------------

def section_polygon(mesh_profile, x):
    """Cross-section of the hook (profile frame) at x, as a shapely polygon in (z, y)."""
    path = mesh_profile.section(plane_origin=[x, 0, 0], plane_normal=[1, 0, 0])
    to_2d = np.array([[0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, x], [0, 0, 0, 1]], dtype=float)
    planar, _ = path.to_2D(to_2D=to_2d, check=False)
    return unary_union(planar.polygons_full)


def second_moment_y(poly):
    """Area and I about the horizontal centroidal axis (bending under a vertical load), plus extreme fibre distance."""
    area = poly.area
    cy = poly.centroid.y
    ixx = 0.0
    for g in getattr(poly, "geoms", [poly]):
        for ring, sign in [(g.exterior, 1)] + [(i, -1) for i in g.interiors]:
            c = np.asarray(ring.coords)
            x0, y0, x1, y1 = c[:-1, 0], c[:-1, 1], c[1:, 0], c[1:, 1]
            cross = x0 * y1 - x1 * y0
            ixx += sign * abs(np.sum(cross * (y0 ** 2 + y0 * y1 + y1 ** 2)) / 12.0)
    ixx -= area * cy ** 2
    miny, maxy = poly.bounds[1], poly.bounds[3]
    return area, ixx, max(maxy - cy, cy - miny)


def strength(mesh_profile, p: HookParams):
    g = 9.81
    f_static = BIKE_MASS_KG * g
    x_load = p.reach - 5.0                   # the rim bears in the crook, just inside the tip
    stations = np.linspace(p.plate_t + 2, x_load - 8, 24)
    rows = []
    for x in stations:
        poly = section_polygon(mesh_profile, x)
        area, ixx, c = second_moment_y(poly)
        m = f_static * (x_load - x)          # N mm
        rows.append({"x": round(float(x), 1), "depth": round(poly.bounds[3] - poly.bounds[1], 1),
                     "stress_static_mpa": round(m * c / ixx, 2)})
    worst = max(rows, key=lambda r: r["stress_static_mpa"])
    s_static = worst["stress_static_mpa"]
    s_dyn = s_static * DYNAMIC_FACTOR
    # Screws: the hook tips about the plate's bottom edge; the lip screws (in shear) hold the top back.
    lever = p.plate_h + p.lip_t / 2
    h_screws = f_static * x_load / lever
    return {
        "bike_mass_kg_assumed": BIKE_MASS_KG,
        "static_load_n": round(f_static, 1),
        "dynamic_factor": DYNAMIC_FACTOR,
        "arm_worst_section": worst,
        "arm_stress_static_mpa": s_static,
        "arm_stress_dynamic_mpa": round(s_dyn, 2),
        "safety_factor_dynamic_vs_short_term": round(PETG_SHORT_TERM_MPA / s_dyn, 1),
        "safety_factor_static_vs_creep_limit": round(PETG_SUSTAINED_MPA / s_static, 1),
        "lip_screws_shear_each_static_n": round(h_screws / 2, 1),
        "lip_screws_shear_each_dynamic_n": round(h_screws / 2 * DYNAMIC_FACTOR, 1),
        "note": ("Beam estimate along the arm with the bike's weight in the crook. PETG along the layers assumed "
                 f"{PETG_SHORT_TERM_MPA:g} MPa short term, {PETG_SUSTAINED_MPA:g} MPa sustained (creep). "
                 "A #10 wood screw in a 2x4 is good for roughly 400 N sideways (design value), so the lip screws "
                 "have a big margin. The weight itself bears on the lip, not the screws."),
        "sections": rows,
    }


# ---------------------------------------------------------------------------------------------------------------------
# The 2x4, the wall, and a wheel hung on the hook (world frame)
# ---------------------------------------------------------------------------------------------------------------------

def board_and_wall(p: HookParams, half_len=300.0):
    board = trimesh.creation.box(extents=[2 * half_len, p.board_depth, p.board_face])
    board.apply_translation([0, -p.board_depth / 2, -p.board_face / 2])
    wall = trimesh.creation.box(extents=[2 * half_len + 200, 12.7, 900])
    wall.apply_translation([0, -p.board_depth - 6.35, -250])
    return board, wall


def wheel_frame(turn_deg):
    t = math.radians(turn_deg)
    u = np.array([math.sin(t), math.cos(t), 0.0])     # in the wheel plane, horizontal
    up = np.array([0.0, 0.0, 1.0])
    a = np.cross(u, up)                                # axle
    return np.column_stack([u, up, a])                 # local (x: in-plane horizontal, y: up, z: axle) -> world


def wheel_parts(w, centre, turn_deg, phase=0.0):
    """Rim + tire, and spokes, in world coordinates (wheel centre `centre`)."""
    R = wheel_frame(turn_deg)
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = centre
    # Local wheel: plane = local x/y, axle = local z. trimesh's annulus/torus are built around Z, so they already match.
    rim = trimesh.creation.annulus(r_min=w["bed_r"], r_max=w["bed_r"] + w["rim_h"], height=w["rim_w"], sections=160)
    tire_r = w["tire_w"] / 2
    tire = trimesh.creation.torus(major_radius=w["bed_r"] + w["rim_h"] + tire_r * 0.6, minor_radius=tire_r,
                                  major_sections=160, minor_sections=16)
    rimtire = trimesh.util.concatenate([rim, tire])
    rimtire.apply_transform(T)
    spokes, segs = [], []
    n = w["spokes"]
    for i in range(n):
        ang = phase + 2 * math.pi * i / n
        d = np.array([math.cos(ang), math.sin(ang), 0.0])
        side = 1 if i % 2 else -1
        p0 = d * w["flange_r"] + np.array([0, 0, side * w["flange_half"]])
        p1 = d * (w["bed_r"] + 2)
        q0, q1 = R @ p0 + centre, R @ p1 + centre
        segs.append((q0, q1))
        spokes.append(trimesh.creation.cylinder(radius=w["spoke_d"] / 2, segment=[q0, q1], sections=8))
    return rimtire, trimesh.util.concatenate(spokes), segs


def overlap(a, b):
    inter = a.intersection(b, engine="manifold")
    return float(abs(inter.volume)) if len(inter.faces) else 0.0


def hang_wheel(hook_w, p: HookParams, w):
    """Where the wheel comes to rest: its rim on the arm, slid down the slope toward the tip until the rim or tire
    touches the tip. Returns the wheel centre."""
    def centre(y, z_top):
        return np.array([0.0, y, z_top - w["bed_r"]])

    def lowest_z(y):
        lo, hi = p.seat_y - 20, p.seat_y + 50
        for _ in range(9):
            mid = (lo + hi) / 2
            rimtire, _, _ = wheel_parts(w, centre(y, mid), w["turn_deg"])
            if overlap(rimtire, hook_w) > 0.5:
                lo = mid
            else:
                hi = mid
        return hi

    best = None
    for y in np.arange(p.reach - 60, p.reach + 1, 5.0):
        z = lowest_z(y)
        if best is None or z < best[1] - 0.05:
            best = (y, z)
    return centre(*best)


def spoke_clearance(hook_w, w, c, n_phase=24):
    """Rotate the wheel about its axle (which spokes end up near the hook) and find the best and worst gap to the hook."""
    pts = hook_w.sample(60000)
    tree = cKDTree(pts)
    results = []
    for k in range(n_phase):
        phase = (2 * 2 * math.pi / w["spokes"]) * k / n_phase       # the pattern repeats every 2 spokes
        _, _, segs = wheel_parts(w, c, w["turn_deg"], phase)
        dmin = np.inf
        for q0, q1 in segs:
            s = np.linspace(0, 1, 400)[:, None]
            line = q0 + (q1 - q0) * s
            near = np.linalg.norm(line - c, axis=1) > w["bed_r"] - 140    # only the outer part can reach the hook
            if near.any():
                d, _ = tree.query(line[near])
                dmin = min(dmin, d.min() - w["spoke_d"] / 2)
        results.append((phase, dmin))
    best = max(results, key=lambda r: r[1])
    worst = min(results, key=lambda r: r[1])
    return best, worst


def wall_clearance(board, wall, w, c):
    rimtire, _, _ = wheel_parts(w, c, w["turn_deg"])
    return overlap(rimtire, trimesh.util.concatenate([board, wall]).convex_hull) < 1.0


# ---------------------------------------------------------------------------------------------------------------------

def main():
    OUT.mkdir(exist_ok=True)
    RENDERS.mkdir(exist_ok=True)
    p = HookParams(**MEASURED)

    hook = build_hook(p)
    assert hook.is_valid and len(hook.solids()) == 1
    printed = print_pose(hook)
    export_step(printed, str(OUT / "bike-hook.step"))
    mesh = mk.cad_to_mesh(printed)
    info = mk.report(mesh)
    assert info["watertight"], "print mesh is not watertight"
    mesh.export(OUT / "bike-hook.stl")

    hook_profile = mk.cad_to_mesh(hook)
    hook_w = world_mesh(hook_profile)
    board, wall = board_and_wall(p)

    st = strength(hook_profile, p)
    assert st["safety_factor_dynamic_vs_short_term"] >= 3, st
    assert st["safety_factor_static_vs_creep_limit"] >= 3, st

    # Screw access: the driver goes straight in along each hole; nothing of the hook may be in its way.
    face_path = trimesh.creation.cylinder(radius=p.head_d / 2 + 1, height=300)
    face_path.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
    face_path.apply_translation([0, p.plate_t + 0.5 + 150, p.face_screw_y])
    lip_paths = []
    for dz in (-p.lip_screw_dz, p.lip_screw_dz):
        cyl = trimesh.creation.cylinder(radius=p.head_d / 2 + 1, height=300)
        cyl.apply_translation([dz, p.lip_screw_x, p.lip_t + 0.5 + 150])
        lip_paths.append(cyl)
    access = {"face_screw_blocked_mm3": round(overlap(face_path, hook_w), 1),
              "lip_screws_blocked_mm3": round(sum(overlap(c, hook_w) for c in lip_paths), 1)}
    assert access["face_screw_blocked_mm3"] < 1 and access["lip_screws_blocked_mm3"] < 1, access

    # Wheel hung on the hook
    c = hang_wheel(hook_w, p, WHEEL)
    best, worst = spoke_clearance(hook_w, WHEEL, c)
    rimtire, spokes, _ = wheel_parts(WHEEL, c, WHEEL["turn_deg"], best[0])
    min_turn = None                       # step down from 90 deg until the wheel would hit the 2x4 or wall
    for turn in range(90, 29, -5):
        wt = {**WHEEL, "turn_deg": turn}
        if not wall_clearance(board, wall, wt, hang_wheel(hook_w, p, wt)):
            break
        min_turn = turn
    wheel = {
        **WHEEL,
        "wheel_centre_mm": [round(float(v), 1) for v in c],
        "rim_rests_at_y": round(float(c[1]), 1),
        "spoke_gap_best_phase_mm": round(float(best[1]), 1),
        "spoke_gap_worst_phase_mm": round(float(worst[1]), 1),
        "wheel_clears_2x4_and_wall": wall_clearance(board, wall, WHEEL, c),
        "min_turn_deg_to_clear_wall_hanging_from_hook": min_turn,
    }

    report = {
        "scale_status": "designed (no scan). 2x4 at nominal 1.5 x 3.5 in; wheel, tire and bike weight are assumed (see README)",
        "print": info,
        "print_orientation": "lying on its side (profile flat on the bed), no supports; layers run along the arm",
        "strength": st,
        "screw_access": access,
        "wheel_fit": wheel,
        "params_mm": {**p.report_params(), "bike_mass_kg": BIKE_MASS_KG,
                      "arm_stress_static_mpa": st["arm_stress_static_mpa"],
                      "safety_factor_dynamic": st["safety_factor_dynamic_vs_short_term"]},
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "params_mm"} | {"strength": {k: v for k, v in st.items() if k != "sections"}}, indent=2))

    # Viewer meshes (world, Z-up)
    hook_w.export(RENDERS / "asm-hook.stl")
    board.export(RENDERS / "ref-2x4.stl")
    rimtire.export(RENDERS / "ref-wheel.stl")
    spokes.export(RENDERS / "ref-spokes.stl")

    render_sheet(mesh, str(RENDERS / "model.png"), title="bike-hook: print pose (on its side, no supports), mm",
                 labels=["printed hook"], sections_y=(0.0,), sections_x=(0.0,))
    side = trimesh.util.concatenate([hook_w, board, rimtire, spokes]).slice_plane([0, 0, p.seat_y - 220], [0, 0, 1])
    render_sheet(side, str(RENDERS / "in-use.png"),
                 title=f"bike-hook on the 2x4, 700c wheel turned {WHEEL['turn_deg']:g} deg (X along the 2x4, Y out, Z up)",
                 labels=["hook + 2x4 + wheel (top of)"], sections_y=(), sections_x=())
    side_section(hook_w, board, wall, rimtire, p, RENDERS / "side-section.png")


def side_section(hook_w, board, wall, rimtire, p, path):
    """Section through the hook's centre plane (X = 0) with the 2x4, wall and wheel, zoomed in on the hook."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    from render import section_segments
    fig, ax = plt.subplots(figsize=(10, 7))
    for m, col, lab in [(hook_w, "black", "hook"), (board, "tab:brown", "2x4"), (wall, "tab:gray", "wall (drywall)"),
                        (rimtire, "tab:blue", "rim + tire")]:
        segs = section_segments(m, [1, 0, 0], [0, 0, 0], [1, 2])
        ax.add_collection(LineCollection(segs, colors=col, lw=1.4, label=lab))
    ax.set_xlim(-70, 170)
    ax.set_ylim(-110, 70)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.4)
    ax.legend(loc="lower right")
    ax.set_xlabel("Y: out from the 2x4's face (mm)")
    ax.set_ylabel("Z: up from the 2x4's top (mm)")
    ax.set_title("side section through the hook's centre (X = 0)")
    fig.savefig(path, dpi=80, bbox_inches="tight")
    plt.close(fig)

if __name__ == "__main__":
    main()
