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
from render import rasterize, render_sheet, section_segments  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402

OUT = HERE / "output"
RENDERS = HERE / "renders"

# --- Owner's setup -------------------------------------------------------------------------------------------------
BOARD = pb.DEFAULT_BOARD         # the owner's pegboard (3/16 in hardboard, 1/4 in holes on 1 in centres)
STUD_2X4 = {"depth": 38.1, "face": 88.9}   # assumed: 2x4 flat behind the pegboard (wide face toward it), centred on the screw rows

# --- Hook variants (model.py HookParams overrides) -------------------------------------------------------------------
HOOKS = {
    # 700c hybrids. The bar is 26 mm across the spoke gap, 44 mm deep along the load.
    "adult": {},
    # 16 and 20 in kids' wheels: their spokes are much closer together, so the bar is slimmer (16 mm across the gap, 38 deep). The seat sits
    # further out, so these small wheels hang lower and their tires clear the bottom of the plate. Kids' bikes are light,
    # so the slimmer bar still has the margin (checked below, per bike).
    "kids": {"tire_max_w": 58.0, "rim_max_w": 28.0, "seat_y": 140.0, "seat_r": 8.0, "bar_len": 22.0,
             "bar_angle_deg": 32.0, "tip_top": 6.0, "seat_z": 8.0, "label": "KIDS"},
}

# --- The owner's bikes (photos 2026-11-11; weights and wheel details estimated from the models, not measured) ---------
# Wheels: bsd_r = half the bead-seat diameter (ISO: 622 for 700c, 406 for 20 in, 305 for 16 in); bed_r = rim spoke-bed
# radius (~ERD / 2). Spoke counts aren't readable in the photos, so each wheel is checked with the likely counts.
WHEEL_700C = {"bsd_r": 311.0, "bed_r": 300.0, "rim_h": 17.0, "rim_w": 21.0, "spoke_d": 2.0,
              "flange_r": 22.0, "flange_half": 35.0, "cross": 3}
WHEEL_20 = {"bsd_r": 203.0, "bed_r": 195.0, "rim_h": 13.0, "rim_w": 22.0, "spoke_d": 2.0,
            "flange_r": 20.0, "flange_half": 30.0, "cross": 2}
WHEEL_16 = {"bsd_r": 152.5, "bed_r": 145.0, "rim_h": 12.0, "rim_w": 22.0, "spoke_d": 2.0,
            "flange_r": 20.0, "flange_half": 28.0, "cross": 1}
BIKES = {
    "trek_fx72": {"name": "Trek FX 7.2 (700x35)", "hook": "adult", "mass_kg": 12.5,
                  "wheel": {**WHEEL_700C, "tire_w": 35.0}, "spokes": [32, 36]},
    "schwinn_trailway": {"name": "Schwinn Trailway (700x40, suspension fork)", "hook": "adult", "mass_kg": 16.5,
                         "wheel": {**WHEEL_700C, "tire_w": 40.0}, "spokes": [36]},
    "nishiki_20": {"name": "Nishiki kids' 20 in (20x1.95)", "hook": "kids", "mass_kg": 12.0,
                   "wheel": {**WHEEL_20, "tire_w": 50.0}, "spokes": [28, 36]},
    "dynacraft_16": {"name": "Dynacraft kids' 16 in (16x2.125, training wheels)", "hook": "kids", "mass_kg": 9.5,
                     "wheel": {**WHEEL_16, "tire_w": 54.0}, "spokes": [20, 28]},
}
# Suggested layout along the wall (hook X positions, mm, multiples of the 1 in hole pitch). Adult and kids' bikes alternate:
# a kid's handlebar hangs ~0.25 m closer to the wall than an adult's, so the two can overlap side to side. 18 in also keeps
# an adult's pedals clear of the kid's bike next to it (15 in was tight).
LAYOUT_X = {"schwinn_trailway": 0.0, "nishiki_20": 457.2, "trek_fx72": 914.4, "dynacraft_16": 1371.6}   # 18 in apart
SECTION_BIKES = ("schwinn_trailway", "dynacraft_16")   # side/plan section render per hook variant
MIN_SPOKE_GAP = 4.0              # mm per side, at the best wheel rotation (you turn the wheel to line up a gap as you hang it)
DYNAMIC_FACTOR = 3.0             # lifting the bike on, knocks

# Printed PETG. Along the layers (arm) vs across them (the bar runs up the print, so its bending pulls layers apart).
PETG_ALONG_MPA, PETG_ALONG_SUSTAINED_MPA = 30.0, 8.0
PETG_ACROSS_MPA, PETG_ACROSS_SUSTAINED_MPA = 15.0, 4.0
SCREW_WITHDRAWAL_N = 580.0       # #10 wood screw, ~33 mm into SPF: design (allowable) value, ~1/5 of ultimate


# ---------------------------------------------------------------------------------------------------------------------
# Wheel
# ---------------------------------------------------------------------------------------------------------------------

def tire_outer_r(w):
    return w["bsd_r"] + 0.95 * w["tire_w"]


def wheel_parts(w, hub, phase=0.0):
    """Rim + tire and spokes in world coordinates. The wheel is straight: its plane is x = hub[0], axle along X.
    Spokes are laced `cross`-cross (0 = radial): rim holes alternate flanges, and on each flange the spokes alternate
    leading/trailing, each reaching the hub `cross` flange holes round from its rim hole."""
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
    n = w["spokes"]
    for i in range(n):
        a = phase + 2 * math.pi * i / n
        side = 1 if i % 2 else -1
        lead = 1 if (i // 2) % 2 else -1
        ah = a + lead * w["cross"] * 4 * math.pi / n                # one flange hole = 2 pi / (n / 2)
        q0 = R @ np.array([w["flange_r"] * math.cos(ah), w["flange_r"] * math.sin(ah), side * w["flange_half"]]) + hub
        q1 = R @ np.array([(w["bed_r"] + 2) * math.cos(a), (w["bed_r"] + 2) * math.sin(a), 0.0]) + hub
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
    lo, hi = est - 10.0, est + 3.0

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
        phase = (8 * math.pi / w["spokes"]) * k / n_phase        # the lacing pattern repeats every 4 spokes
        _, _, _, segs = wheel_parts(w, hub, phase)
        dmin = np.inf
        for q0, q1 in segs:
            line = q0 + (q1 - q0) * np.linspace(0, 1, 500)[:, None]
            near = np.linalg.norm(line - hub, axis=1) > w["bed_r"] * 0.4
            if near.any():
                dmin = min(dmin, tree.query(line[near])[0].min() - w["spoke_d"] / 2)
        res.append((phase, dmin))
    return max(res, key=lambda r: r[1]), min(res, key=lambda r: r[1])


# ---------------------------------------------------------------------------------------------------------------------
# Loads
# ---------------------------------------------------------------------------------------------------------------------

def loads(p: HookParams, hub, x_load, mass_kg):
    """The rim pushes on the seat along the line to the hub (radial), so its vertical part is the bike's weight."""
    W = mass_kg * 9.81
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
        "bike_mass_kg_assumed": mass_kg,
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

def pegboard_patch(cols=range(-5, 8)):
    m = pb.board_mesh(BOARD, rows=range(-10, 4), cols=cols, sections=8)
    m.vertices = m.vertices[:, [2, 0, 1]]                # board frame (x out, y up, z across) -> world (X, Y, Z)
    return m


def stud_and_wall():
    t = BOARD.thickness
    stud = trimesh.creation.box(extents=[1900, STUD_2X4["depth"], STUD_2X4["face"]])
    stud.apply_translation([700, -t - STUD_2X4["depth"] / 2, 0])
    wall = trimesh.creation.box(extents=[2000, 12.7, 700])
    wall.apply_translation([700, -t - STUD_2X4["depth"] - 6.35, -150])
    return stud, wall


def screw_access(p: HookParams, hook_w):
    """Each screw goes straight in along Y: the head, then a driver bit (with an extension) must not touch the hook."""
    blocked = 0.0
    for x, z in p.screws:
        head = trimesh.creation.cylinder(radius=p.head_d / 2, segment=[[x, p.plate_t + 0.3, z], [x, p.plate_t + 8, z]])
        bit = trimesh.creation.cylinder(radius=4.0, segment=[[x, p.plate_t + 8, z], [x, 300, z]])
        blocked += overlap(head, hook_w) + overlap(bit, hook_w)
    return round(blocked, 1)


def sections_png(p, hook_w, rim, tire, spokes, board, stud, wall, hub, path, title):
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
    fig.suptitle(title, fontsize=14)
    fig.savefig(path, dpi=75, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------------------------------------------------

def build_variant(name, p: HookParams):
    hook = build_hook(p)
    assert hook.is_valid and len(hook.solids()) == 1, name
    printed = print_pose(hook, p)
    export_step(printed, str(OUT / f"bike-hook-{name}.step"))
    mesh = mk.cad_to_mesh(printed)
    info = mk.report(mesh)
    assert info["watertight"], f"{name}: print mesh is not watertight"
    mesh.export(OUT / f"bike-hook-{name}.stl")
    hook_w = mk.cad_to_mesh(hook)
    access = screw_access(p, hook_w)
    assert access < 1.0, f"{name}: a screw can't be driven straight in: {access} mm3 blocked"
    return mesh, hook_w, {"print": info, "screw_access_blocked_mm3": access, "params_mm": p.report_params()}


def check_bike(key, bike, p: HookParams, hook_w):
    """Hang this bike's front wheel on its hook: rest position, rim (not tire) on the seat, spoke gaps, loads."""
    seat = (*p.contact_centre, p.contact_r)
    w0 = {**bike["wheel"], "spokes": bike["spokes"][0]}
    hub = hang(hook_w, w0, p.x_wheel, seat)
    tire_ok = {}
    for xw in (p.x_arm_in + w0["tire_w"] / 2 + 1, p.x_wheel, p.x_tip - w0["rim_w"] / 2 - 1):   # against arm, centred, tip
        tire_ok[f"x{xw:+.1f}"] = bool(abs(hang(hook_w, w0, xw, seat)[2] - hang(hook_w, w0, xw, seat, with_tire=False)[2]) < 0.5)
    assert all(tire_ok.values()), f"{key}: the tire, not the rim, rests on the hook: {tire_ok}"
    gaps, best_phase = {}, None
    for n in bike["spokes"]:
        best, worst = spoke_gaps(hook_w, {**bike["wheel"], "spokes": n}, hub)
        gaps[f"{n}_spokes"] = {"best_mm": round(float(best[1]), 1), "worst_mm": round(float(worst[1]), 1)}
        assert best[1] >= MIN_SPOKE_GAP, f"{key}: bar doesn't fit between {n} spokes ({best[1]:.1f} mm)"
        if best_phase is None:
            best_phase = best[0]
    ld = loads(p, hub, p.x_wheel, bike["mass_kg"])
    assert ld["contact_angle_from_top_deg"] < 62, f"{key}: rim sits too far round the wheel: {ld}"
    assert ld["arm_root_stress_mpa"]["safety_creep"] >= 2 and ld["bar_root_stress_mpa"]["safety_creep"] >= 2, (key, ld)
    return hub, best_phase, {
        "name": bike["name"], "hook": bike["hook"], "mass_kg_estimated": bike["mass_kg"],
        "wheel": bike["wheel"], "tire_outer_r": round(tire_outer_r(bike["wheel"]), 1),
        "hub_mm": [round(float(v), 1) for v in hub], "hub_below_middle_screw_row": round(float(-hub[2]), 1),
        "rim_rests_on_seat_not_tire": tire_ok, "spoke_gaps_per_side": gaps, "loads": ld}


def main():
    OUT.mkdir(exist_ok=True)
    RENDERS.mkdir(exist_ok=True)
    for old in ("bike-hook.stl", "bike-hook.step"):
        (OUT / old).unlink(missing_ok=True)
    for old in ("side-section.png", "model.png", "sections.png", "asm-hook.stl", "ref-wheel.stl", "ref-spokes.stl"):
        (RENDERS / old).unlink(missing_ok=True)
    board = pegboard_patch(cols=range(-12, 62))
    stud, wall = stud_and_wall()
    t = BOARD.thickness

    variants, hooks = {}, {}
    for name, kw in HOOKS.items():
        p = HookParams(**kw)
        mesh, hook_w, info = build_variant(name, p)
        variants[name], hooks[name] = info, (p, hook_w)
        render_sheet(mesh, str(RENDERS / f"model-{name}.png"),
                     title=f"bike-hook ({name}): print pose (on the arm's side, no supports), mm",
                     labels=[f"{name} hook"], sections_y=(0.0,), sections_x=(0.0,))

    # The plates as you'd see them standing at the wall (looking along -Y; +X is on your left), plus a 3/4 view.
    fig, axes = plt.subplots(2, 2, figsize=(16, 11))
    for row, name in enumerate(hooks):
        m = hooks[name][1]
        for col, (vd, up, title) in enumerate([((0, -1, 0), (0, 0, 1), "facing the wall"),
                                                ((0.5, -1, -0.45), (0, 0, 1), "from the front, left and above")]):
            img, ext = rasterize(m, np.array(vd, float), np.array(up, float), px=800)
            axes[row, col].imshow(img, extent=ext)
            axes[row, col].set_title(f"{name} hook: {title}")
            axes[row, col].axis("off")
    fig.suptitle("bike-hook plates: counterbored screw holes, chamfered edges, labels", fontsize=14)
    fig.savefig(RENDERS / "plates.png", dpi=70, bbox_inches="tight")
    plt.close(fig)

    bikes, scene, flat = {}, [], {}
    for key, bike in BIKES.items():
        p, hook_w = hooks[bike["hook"]]
        hub, phase, res = check_bike(key, bike, p, hook_w)
        bikes[key] = res
        dx = LAYOUT_X[key]
        rim, tire, spokes, _ = wheel_parts({**bike["wheel"], "spokes": bike["spokes"][0]}, hub, phase)
        for m in (rim, tire, spokes):
            m.apply_translation([dx, 0, 0])
        h = hook_w.copy()
        h.apply_translation([dx, 0, 0])
        h.export(RENDERS / f"asm-hook-{key}.stl")
        trimesh.util.concatenate([rim, tire]).export(RENDERS / f"ref-wheel-{key}.stl")
        spokes.export(RENDERS / f"ref-spokes-{key}.stl")
        scene += [h, rim, tire, spokes]
        ld = res["loads"]
        flat.update({f"{key}_mass_kg": bike["mass_kg"], f"{key}_contact_deg": ld["contact_angle_from_top_deg"],
                     f"{key}_screw_n": ld["screw_max_tension_by_pattern_static_n"]["three_rows_over_2x4"],
                     f"{key}_spoke_gap": min(g["best_mm"] for g in res["spoke_gaps_per_side"].values()),
                     f"{key}_hub_below": res["hub_below_middle_screw_row"], f"{key}_x": dx})
        if key in SECTION_BIKES:
            rim0, tire0, sp0, _ = wheel_parts({**bike["wheel"], "spokes": bike["spokes"][0]}, hub, phase)
            sections_png(p, hook_w, rim0, tire0, sp0, board, stud, wall, hub, RENDERS / f"sections-{bike['hook']}.png",
                         f"{bike['hook']} hook with the {bike['name']}: wheel straight, tire on the pegboard, rim on the bar")

    report = {
        "scale_status": "designed (no scan). Pegboard = owner's (3.94 mm), 2x4 flat behind it (3 hole rows show wood). "
                        "Bike weights and wheel details are estimates from the bike models (see README)",
        "print_orientation": "on the arm's outer side (world X up); no supports; tip leans out at 45 deg",
        "screws": {"install": "three hole rows are over the 2x4: use all 8 holes",
                   "length_note": f"#10 or #12 x 2 in, heads in the counterbores: "
                                  f"{50.8 - (HookParams().plate_t - HookParams().cbore_depth) - t:.0f} mm into the 2x4"},
        "variants": variants,
        "bikes": bikes,
        "layout_x_mm": LAYOUT_X,
        "params_mm": {**variants["adult"]["params_mm"], **{f"kids_{k}": v for k, v in variants["kids"]["params_mm"].items()},
                      **flat},
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: {b: {"angle": v["loads"]["contact_angle_from_top_deg"], "gaps": v["spoke_gaps_per_side"],
                             "screw": v["loads"]["screw_max_tension_n"], "arm": v["loads"]["arm_root_stress_mpa"],
                             "bar": v["loads"]["bar_root_stress_mpa"], "hub_below": v["hub_below_middle_screw_row"]}
                         for b, v in bikes.items()} for k in ["bikes"]}, indent=1))
    print(json.dumps({n: v["print"] for n, v in variants.items()}, indent=1))

    board.export(RENDERS / "ref-pegboard.stl")
    stud.export(RENDERS / "ref-2x4.stl")
    full = trimesh.util.concatenate(scene + [board])
    render_sheet(full.slice_plane([0, 0, -330], [0, 0, 1]), str(RENDERS / "in-use.png"),
                 title="the four bikes' front wheels on their hooks, as laid out (X along the wall, Y out, Z up)",
                 labels=["hooks + pegboard + wheels"], sections_y=(), sections_x=())

if __name__ == "__main__":
    main()
