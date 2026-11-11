"""Reproducible build for the vertical bike hook (v2: bike perpendicular to the wall, tires on the pegboard).

    python projects/bike-hook/build.py        (about a minute)

model.py (build123d) -> plate on the pegboard + arm beside the wheel + bar through the spokes
  -> output/bike-hook.step / .stl      print pose: on the arm's outer side, no supports
  -> output/report.json                checks, parameters, wheel fit, rim force, strength + screw estimates
  -> renders/model.png                 print pose: views + sections
  -> renders/in-use.png                on the pegboard with a 700c wheel hung on it
  -> renders/sections.png              side and plan sections through the wheel and hook
  -> renders/asm-*.stl, ref-*.stl      world Z-up meshes for the viewer

World frame (model.py): X along the wall, Y out from the pegboard's front face, Z up; origin on a pegboard hole.
"""

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / "tools"), str(HERE)]

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import meshkit as mk  # noqa: E402
import numpy as np  # noqa: E402
import pegboard as pb  # noqa: E402
import trimesh  # noqa: E402
from build123d import export_step  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from model import PITCH, HookParams, build_hook, print_pose  # noqa: E402
from render import render_sheet, section_segments  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402

OUT = HERE / "output"
RENDERS = HERE / "renders"

# --- Owner's setup -------------------------------------------------------------------------------------------------
BOARD = pb.DEFAULT_BOARD         # the owner's pegboard (3/16 in hardboard, 1/4 in holes on 1 in centres)
STUD_2X4 = {"depth": 38.1, "face": 88.9}   # assumed: 2x4 flat behind the pegboard (wide face toward it), centred on the screw rows

# --- Not measured yet (see README "Open questions") ------------------------------------------------------------------
MEASURED = {}
BIKE_MASS_KG = 16.0              # assumed; do NOT hang an e-bike on it without redoing the numbers
DYNAMIC_FACTOR = 3.0             # lifting the bike on, knocks

# Printed PETG. Along the layers (arm) vs across them (the bar runs up the print, so its bending pulls layers apart).
PETG_ALONG_MPA, PETG_ALONG_SUSTAINED_MPA = 30.0, 8.0
PETG_ACROSS_MPA, PETG_ACROSS_SUSTAINED_MPA = 15.0, 4.0
SCREW_WITHDRAWAL_N = 580.0       # #10 wood screw, ~33 mm into SPF: design (allowable) value, ~1/5 of ultimate

# Wheel (700c / 29er rims share a 622 mm bead seat). Tire outer radius ~ 311 + 0.95 * width.
WHEEL = {"bed_r": 300.0, "rim_h": 17.0, "rim_w": 21.0, "tire_w": 38.0, "spokes": 32, "spoke_d": 2.0,
         "flange_r": 22.0, "flange_half": 35.0}


# ---------------------------------------------------------------------------------------------------------------------
# Wheel
# ---------------------------------------------------------------------------------------------------------------------

def tire_outer_r(w):
    return 311.0 + 0.95 * w["tire_w"]


def wheel_parts(w, hub, phase=0.0):
    """Rim + tire and spokes in world coordinates. The wheel is straight: its plane is x = hub[0], axle along X."""
    R = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], dtype=float)   # local (x, y in the wheel plane; z axle) -> world (Y, Z, X)
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = hub
    rim = trimesh.creation.annulus(r_min=w["bed_r"], r_max=w["bed_r"] + w["rim_h"], height=w["rim_w"], sections=180)
    tr = w["tire_w"] / 2
    tire = trimesh.creation.torus(major_radius=tire_outer_r(w) - tr, minor_radius=tr, major_sections=180, minor_sections=16)
    rim.apply_transform(T)
    tire.apply_transform(T)
    spokes, segs = [], []
    for i in range(w["spokes"]):
        a = phase + 2 * math.pi * i / w["spokes"]
        d = np.array([math.cos(a), math.sin(a), 0.0])
        side = 1 if i % 2 else -1
        q0 = R @ (d * w["flange_r"] + np.array([0, 0, side * w["flange_half"]])) + hub
        q1 = R @ (d * (w["bed_r"] + 2)) + hub
        segs.append((q0, q1))
        spokes.append(trimesh.creation.cylinder(radius=w["spoke_d"] / 2, segment=[q0, q1], sections=8))
    return rim, tire, trimesh.util.concatenate(spokes), segs


def overlap(a, b):
    inter = a.intersection(b, engine="manifold")
    return float(abs(inter.volume)) if len(inter.faces) else 0.0


def hang(hook_w, w, x_wheel, seat, with_tire=True):
    """Tire against the pegboard (hub at y = tire radius), lowered until the rim (and tire) rests on the hook.
    `seat` = (y, z, r) of the rounded edge the rim should sit on; it brackets the search (lower = rim cuts the bar)."""
    y = tire_outer_r(w)
    cy, cz, cr = seat
    est = cz - math.sqrt((w["bed_r"] - cr) ** 2 - (y - cy) ** 2)   # seat edge just inside the rim's inner surface
    lo, hi = est - 10.0, est + 10.0

    def hits(z):
        rim, tire, _, _ = wheel_parts(w, np.array([x_wheel, y, z]))
        return overlap(trimesh.util.concatenate([rim, tire]) if with_tire else rim, hook_w) > 0.2

    assert hits(lo) and not hits(hi), "wheel search bracket is wrong"
    for _ in range(14):
        mid = (lo + hi) / 2
        if hits(mid):
            lo = mid           # too low: overlapping, so go up
        else:
            hi = mid
    return np.array([x_wheel, y, hi])


def spoke_gaps(hook_w, w, hub, n_phase=24):
    tree = cKDTree(hook_w.sample(60000))
    res = []
    for k in range(n_phase):
        phase = (4 * math.pi / w["spokes"]) * k / n_phase        # the pattern repeats every 2 spokes
        _, _, _, segs = wheel_parts(w, hub, phase)
        dmin = np.inf
        for q0, q1 in segs:
            line = q0 + (q1 - q0) * np.linspace(0, 1, 500)[:, None]
            near = np.linalg.norm(line - hub, axis=1) > w["bed_r"] - 160
            if near.any():
                dmin = min(dmin, tree.query(line[near])[0].min() - w["spoke_d"] / 2)
        res.append((phase, dmin))
    return max(res, key=lambda r: r[1]), min(res, key=lambda r: r[1])


# ---------------------------------------------------------------------------------------------------------------------
# Loads
# ---------------------------------------------------------------------------------------------------------------------

def loads(p: HookParams, hub, x_load):
    """The rim pushes on the seat along the line to the hub (radial), so its vertical part is the bike's weight."""
    W = BIKE_MASS_KG * 9.81
    cy, cz = p.contact_centre
    phi = math.atan2(hub[1] - cy, cz - hub[2])           # angle of the contact from the top of the wheel, toward the wall
    P = W * math.tan(phi)                                # pull on the hook, away from the wall
    N = W / math.cos(phi)
    seat = np.array([x_load, cy - p.contact_r * math.sin(phi), cz + p.contact_r * math.cos(phi)])
    F = np.array([0.0, P, -W])                           # force of the rim on the hook

    # Arm root (at the plate): rectangle arm_w (X) x depth (Z). Bending and axial stress run along the print layers.
    depth = p.z_top - p.arm_root_z
    arm_root = np.array([p.x_min + p.arm_w / 2, p.plate_t, (p.z_top + p.arm_root_z) / 2])
    m = np.cross(seat - arm_root, F)
    s_arm = abs(F[1]) / (p.arm_w * depth) + abs(m[0]) * 6 / (p.arm_w * depth ** 2) + abs(m[2]) * 6 / (depth * p.arm_w ** 2)

    # Bar root (where it leaves the arm's inner face). Slot section: 2r across x (L + 2r) along u, taken as 0.9 x the
    # rectangle's section modulus. The bar runs up the print, so this bending pulls layers apart.
    (c1y, c1z), (c2y, c2z) = p.contact_centre, p.bar_low_centre
    bar_root = np.array([p.x_arm_in, (c1y + c2y) / 2, (c1z + c2z) / 2])
    m = np.cross(seat - bar_root, F)
    u = np.array([0.0, *p.bar_u])
    t = np.array([0.0, -u[2], u[1]])
    b_t, h_u = 2 * p.seat_r, p.bar_len + 2 * p.seat_r
    m_t, m_u = abs(m @ t), abs(m @ u)            # moment about t bends along u (deep way), about u bends across
    s_bar = (m_t * 6 / (b_t * h_u ** 2) + m_u * 6 / (h_u * b_t ** 2)) / 0.9

    # Screws: elastic bolt group about its centroid (ignores the plate bearing on the board, so it overestimates tension).
    def bolt_group(screws):
        sc = np.array(screws)
        xb, zb = sc.mean(axis=0)
        mx = W * seat[1] + P * (seat[2] - zb)            # tips the top of the plate off the board
        mz = P * (seat[0] - xb)                          # twists it about a vertical line
        dx, dz = sc[:, 0] - xb, sc[:, 1] - zb
        return P / len(sc) + mx * dz / np.sum(dz ** 2) + mz * dx / np.sum(dx ** 2)

    patterns = {name: float(bolt_group(s).max()) for name, s in p.install_patterns.items()}
    worst = max(patterns, key=patterns.get)
    tens = np.array([patterns[worst]])
    sc = np.array(p.install_patterns[worst])
    shear = W / len(sc)
    return {
        "bike_mass_kg_assumed": BIKE_MASS_KG,
        "contact_angle_from_top_deg": round(math.degrees(phi), 1),
        "rim_force_n": round(N, 1),
        "hook_pull_from_wall_n": round(P, 1),
        "hook_down_n": round(W, 1),
        "arm_root_stress_mpa": {"static": round(s_arm, 2), "dynamic": round(s_arm * DYNAMIC_FACTOR, 2),
                                "safety_dynamic": round(PETG_ALONG_MPA / (s_arm * DYNAMIC_FACTOR), 1),
                                "safety_creep": round(PETG_ALONG_SUSTAINED_MPA / s_arm, 1), "layers": "along"},
        "bar_root_stress_mpa": {"static": round(s_bar, 2), "dynamic": round(s_bar * DYNAMIC_FACTOR, 2),
                                "safety_dynamic": round(PETG_ACROSS_MPA / (s_bar * DYNAMIC_FACTOR), 1),
                                "safety_creep": round(PETG_ACROSS_SUSTAINED_MPA / s_bar, 1), "layers": "across"},
        "screw_max_tension_n": {"static": round(float(tens.max()), 1), "dynamic": round(float(tens.max()) * DYNAMIC_FACTOR, 1),
                                "design_value": SCREW_WITHDRAWAL_N,
                                "safety_static_vs_design_value": round(SCREW_WITHDRAWAL_N / tens.max(), 1),
                                "safety_dynamic_vs_design_value": round(SCREW_WITHDRAWAL_N / (tens.max() * DYNAMIC_FACTOR), 1)},
        "screw_shear_each_n": round(shear, 1),
        "screw_max_tension_by_pattern_static_n": {k: round(v, 1) for k, v in patterns.items()},
        "screw_worst_pattern": worst,
        "seat_point_mm": [round(float(v), 1) for v in seat],
        "note": ("Beam estimates at the arm's root (bending along the print layers) and the bar's root (the bar runs up "
                 "the print, so its bending pulls layers apart: lower allowables). Dynamic = x3. Screw tension from an "
                 "elastic bolt group, which ignores the plate pressing on the board (conservative)."),
    }


# ---------------------------------------------------------------------------------------------------------------------
# Scene: pegboard, 2x4, wall (world)
# ---------------------------------------------------------------------------------------------------------------------

def pegboard_patch():
    m = pb.board_mesh(BOARD, rows=range(-9, 4), cols=range(-5, 8))
    m.vertices = m.vertices[:, [2, 0, 1]]                # board frame (x out, y up, z across) -> world (X, Y, Z)
    return m


def stud_and_wall():
    t = BOARD.thickness
    stud = trimesh.creation.box(extents=[400, STUD_2X4["depth"], STUD_2X4["face"]])
    stud.apply_translation([30, -t - STUD_2X4["depth"] / 2, 0])
    wall = trimesh.creation.box(extents=[500, 12.7, 700])
    wall.apply_translation([30, -t - STUD_2X4["depth"] - 6.35, -150])
    return stud, wall


def screw_access(p: HookParams, hook_w):
    """Each screw goes straight in along Y: the head, then a driver bit (with an extension) must not touch the hook."""
    blocked = 0.0
    for x, z in p.screws:
        head = trimesh.creation.cylinder(radius=p.head_d / 2, segment=[[x, p.plate_t + 0.3, z], [x, p.plate_t + 8, z]])
        bit = trimesh.creation.cylinder(radius=4.0, segment=[[x, p.plate_t + 8, z], [x, 300, z]])
        blocked += overlap(head, hook_w) + overlap(bit, hook_w)
    return round(blocked, 1)


def sections_png(p, hook_w, rim, tire, spokes, board, stud, wall, hub, path):
    fig, axes = plt.subplots(1, 2, figsize=(17, 8))
    ax = axes[0]
    for m, col, lab in [(hook_w, "black", "hook"), (board, "tab:olive", "pegboard"), (stud, "tab:brown", "2x4"),
                        (wall, "tab:gray", "wall"), (rim, "tab:blue", "rim"), (tire, "tab:cyan", "tire")]:
        segs = section_segments(m, [1, 0, 0], [hub[0], 0, 0], [1, 2])
        ax.add_collection(LineCollection(segs, colors=col, lw=1.3, label=lab))
    ax.plot([hub[1]], [hub[2]], "k+", ms=12)
    cy, cz = p.contact_centre
    ax.plot([hub[1], cy], [hub[2], cz], "r--", lw=1, label="rim force (through the hub)")
    ax.set_xlim(-70, 420)
    ax.set_ylim(hub[2] - 60, 120)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.4)
    ax.legend(loc="lower right")
    ax.set_xlabel("Y: out from the pegboard (mm)")
    ax.set_ylabel("Z (mm, 0 = middle screw row)")
    ax.set_title(f"side section through the wheel's centre plane (X = {hub[0]:.1f})")

    ax = axes[1]
    z0 = p.seat_z
    for m, col, lab in [(hook_w, "black", "hook"), (board, "tab:olive", "pegboard"), (rim, "tab:blue", "rim"),
                        (tire, "tab:cyan", "tire"), (spokes, "tab:gray", "spokes")]:
        segs = section_segments(m, [0, 0, 1], [0, 0, z0], [0, 1])
        ax.add_collection(LineCollection(segs, colors=col, lw=1.3, label=lab))
    ax.set_xlim(-60, 110)
    ax.set_ylim(-10, 170)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.4)
    ax.legend(loc="upper left")
    ax.set_xlabel("X: along the wall (mm)")
    ax.set_ylabel("Y: out from the pegboard (mm)")
    ax.set_title(f"plan section through the seat (Z = {z0:g})")
    fig.suptitle("bike-hook v2: wheel straight, tire on the pegboard, rim on the bar", fontsize=14)
    fig.savefig(path, dpi=75, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------------------------------------------------

def main():
    OUT.mkdir(exist_ok=True)
    RENDERS.mkdir(exist_ok=True)
    p = HookParams(**MEASURED)

    hook = build_hook(p)
    assert hook.is_valid and len(hook.solids()) == 1
    printed = print_pose(hook, p)
    export_step(printed, str(OUT / "bike-hook.step"))
    mesh = mk.cad_to_mesh(printed)
    info = mk.report(mesh)
    assert info["watertight"], "print mesh is not watertight"
    mesh.export(OUT / "bike-hook.stl")

    hook_w = mk.cad_to_mesh(hook)
    board = pegboard_patch()
    stud, wall = stud_and_wall()
    access = screw_access(p, hook_w)
    assert access < 1.0, f"a screw can't be driven straight in: {access} mm3 blocked"

    seat = (*p.contact_centre, p.contact_r)
    # Wheel: hang it, then check the rim (not the tire) is what rests on the hook, for this tire and the widest one.
    hub = hang(hook_w, WHEEL, p.x_wheel, seat)
    hub_rim_only = hang(hook_w, WHEEL, p.x_wheel, seat, with_tire=False)
    wide = {**WHEEL, "tire_w": p.tire_max_w, "rim_w": p.rim_max_w}
    tire_ok = {}
    for name, w in [("this_tire", WHEEL), ("widest_tire", wide)]:
        # wheel slid against the arm (its tire touches it), centred, and against the tip (its rim touches it)
        for xw in (p.x_arm_in + w["tire_w"] / 2 + 1, p.x_wheel, p.x_tip - w["rim_w"] / 2 - 1):
            h_all, h_rim = hang(hook_w, w, xw, seat), hang(hook_w, w, xw, seat, with_tire=False)
            tire_ok[f"{name}_x{xw:+.1f}"] = bool(abs(h_all[2] - h_rim[2]) < 0.5)
    assert all(tire_ok.values()), f"the tire, not the rim, rests on the hook: {tire_ok}"
    best, worst = spoke_gaps(hook_w, WHEEL, hub)
    rim, tire, spokes, _ = wheel_parts(WHEEL, hub, best[0])
    ld = loads(p, hub, p.x_wheel)
    assert ld["contact_angle_from_top_deg"] < 62, f"rim sits too far round the wheel: {ld}"
    assert ld["arm_root_stress_mpa"]["safety_creep"] >= 2 and ld["bar_root_stress_mpa"]["safety_creep"] >= 2, ld

    wheel = {**WHEEL, "tire_outer_r": round(tire_outer_r(WHEEL), 1), "hub_mm": [round(float(v), 1) for v in hub],
             "hub_below_middle_screw_row": round(float(-hub[2]), 1),
             "rim_rests_on_seat_not_tire": tire_ok,
             "spoke_gap_best_phase_mm": round(float(best[1]), 1),
             "spoke_gap_worst_phase_mm": round(float(worst[1]), 1),
             "tire_touches_pegboard": True}
    t = BOARD.thickness
    report = {
        "scale_status": "designed (no scan). Pegboard = owner's (3.94 mm); 2x4, bike weight and wheel are assumed (see README)",
        "print": info,
        "print_orientation": "on the arm's outer side (world X up); no supports; tip leans out at 45 deg",
        "screw_access_blocked_mm3": access,
        "screws": {"positions_xz_mm": p.screws, "install_patterns": p.install_patterns,
                   "length_note": f"#10 or #12 x 2 in: {50.8 - p.plate_t - t:.0f} mm into the 2x4 "
                                  f"(plate {p.plate_t:g} + pegboard {t:g})"},
        "wheel_fit": wheel,
        "loads": ld,
        "params_mm": {**p.report_params(), "bike_mass_kg": BIKE_MASS_KG,
                      "contact_angle_deg": ld["contact_angle_from_top_deg"],
                      "hub_below_screws": wheel["hub_below_middle_screw_row"],
                      "pull_n": ld["hook_pull_from_wall_n"],
                      "screw_tension_n": ld["screw_max_tension_n"]["static"],
                      "bar_safety_dynamic": ld["bar_root_stress_mpa"]["safety_dynamic"]},
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "params_mm"}, indent=2))

    hook_w.export(RENDERS / "asm-hook.stl")
    board.export(RENDERS / "ref-pegboard.stl")
    stud.export(RENDERS / "ref-2x4.stl")
    trimesh.util.concatenate([rim, tire]).export(RENDERS / "ref-wheel.stl")
    spokes.export(RENDERS / "ref-spokes.stl")
    for old in ("side-section.png",):
        (RENDERS / old).unlink(missing_ok=True)

    render_sheet(mesh, str(RENDERS / "model.png"), title="bike-hook v2: print pose (on the arm's side, no supports), mm",
                 labels=["printed hook"], sections_y=(0.0,), sections_x=(0.0,))
    scene = trimesh.util.concatenate([hook_w, board, rim, tire, spokes]).slice_plane([0, 0, hub[2] - 120], [0, 0, 1])
    render_sheet(scene, str(RENDERS / "in-use.png"),
                 title="bike-hook v2 on the pegboard, 700c wheel straight with its tire on the board (X along the wall, Y out, Z up)",
                 labels=["hook + pegboard + wheel"], sections_y=(), sections_x=())
    sections_png(p, hook_w, rim, tire, spokes, board, stud, wall, hub, RENDERS / "sections.png")


if __name__ == "__main__":
    main()
