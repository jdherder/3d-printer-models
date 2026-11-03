"""Reproducible build for the wagon cup holder (v6: two organic pieces, CLIP stays on, MODULE lifts off).

    python projects/wagon-cup-holder/build.py        (about 1 minute)

model.py (signed-distance-field bodies + exact cuts; see its docstring)
  -> output/wagon-cup-clip.stl             clip: stays on the rail (printed ring-axis-vertical)
  -> output/wagon-cup-module.stl           cup module: lifts on and off the clip's dovetail (printed upright)
  -> output/wagon-cup-clip-test.stl        26 mm ring + ears slice, for the snap / clamp test print
  -> output/wagon-dovetail-test-tongue.stl, wagon-dovetail-test-groove.stl    sliding-fit test pair
  -> output/report.json                    dimensions, checks, parameters
  -> renders/*.png                         previews and sections
  -> renders/asm-*.stl, ref-*.stl          assembled-position meshes (real use orientation) for the viewer and checks

These pieces are meshes (STL), not editable CAD. Change numbers in model.py and rebuild.
"""

import json
import sys
from dataclasses import asdict, replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / "tools"), str(HERE)]

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import trimesh  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from model import (CupHolderParams, build_clip, build_module, clip_to_U, print_pose, prism_x, prism_z,  # noqa: E402
                   boolean_difference, boolean_union)
from render import rasterize, section_segments  # noqa: E402
from sdf import decimate  # noqa: E402
from shapely.geometry import Polygon as ShapelyPolygon  # noqa: E402

OUT = HERE / "output"
RENDERS = HERE / "renders"

# --- Real measurements (owner) ------------------------------------------------
MEASURED = {
    "bar_d": 22.3,      # owner, 2026-11-01: "about 22.3 mm" round tube, confirmed on the side rail
}
# Retailer figures for a 20 oz Yeti Rambler (owner OK with these for now): base 70, widest 89, height ~165.
CUP_OVERRIDES: dict = {}

STRUT_MM = 13.5                # owner, 2026-11-03: the angled strut is 13.5 mm in both directions (a square section)

CLIP_TEST_LEN = 20.0           # long enough for the 7.4 mm nut pocket and the 9.6 mm head pocket plus walls

# Standard M4 hardware the clip is designed for (see README). Used for the fit checks and the viewer only.
BOLT_LEN = 30.0                # the shortest common length that works: engages 2.5 of the nut's 3.2 mm. 35 mm engages it fully
WASHER_OD, WASHER_T = 9.0, 0.8
HEAD_D, HEAD_H = 7.0, 4.0     # M4 socket cap screw
SHANK_D = 4.0
NUT_AF, NUT_T = 7.0, 3.2
DOVETAIL_TEST_H = 14.0


def overhang_area_mm2(mesh, max_angle_deg=45.0, tol_deg=1.0, ignore_bed_mm=1.0):
    """Area of faces that face down more steeply than the overhang limit. The first mm above the bed is ignored (a rounded or
    chamfered first layer is not an overhang)."""
    limit = -np.sin(np.radians(max_angle_deg + tol_deg))
    n, c = mesh.face_normals, mesh.triangles_center
    bad = (n[:, 2] < limit) & (c[:, 2] > ignore_bed_mm)
    return float(mesh.area_faces[bad].sum())


def interference_cm3(a, b):
    inter = a.intersection(b, engine="manifold")
    return float(abs(inter.volume)) / 1000.0 if len(inter.faces) else 0.0


def mesh_report(m):
    return {"extents_mm": [round(float(v), 1) for v in m.extents], "faces": int(len(m.faces)),
            "watertight": bool(m.is_watertight), "winding_consistent": bool(m.is_winding_consistent),
            "euler_number": int(m.euler_number), "volume_cm3": round(float(m.volume) / 1000.0, 1),
            "fits_A1_as_is": bool(np.all(m.extents <= 256.0)),
            "overhang_area_over_45deg_mm2": round(overhang_area_mm2(m), 1)}


def export_print(name, mesh):
    posed = print_pose(mesh)
    assert posed.is_watertight, f"{name} is not watertight"
    posed.export(OUT / f"{name}.stl")
    return posed, mesh_report(posed)


TUMBLER_BASE_EDGE_R = 3.5     # assumed rounding of the tumbler's base edge (a real one is rounded; the owner can measure)


def tumbler_ghost(p):
    """The 20 oz tumbler: a cone from the retailer figures with a rounded base edge."""
    z0, rb, rr = p.floor_y, p.cup_base_d / 2, TUMBLER_BASE_EDGE_R
    arc = [(rb - rr + rr * np.sin(a), z0 + rr - rr * np.cos(a)) for a in np.linspace(0, np.pi / 2, 9)]
    prof = [(0, z0)] + arc + [(p.cup_top_d / 2, z0 + p.cup_h), (0, z0 + p.cup_h)]
    m = trimesh.creation.revolve(np.array(prof), sections=96)
    m.apply_translation([0, p.cup_axis_y, 0])
    return m


def rail_ghost(p):
    m = trimesh.creation.cylinder(radius=p.bar_d / 2, height=160.0, sections=96)
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))   # axis -> X
    return m


def keepout_ghost(p):
    """Approximate zones for the end brackets' red latch + diagonal strut: beyond each end of the clear window,
    reaching `keepout_reach` past the bar's surface. Only that reach is from the owner; the rest is my assumption."""
    half = p.safe_window / 2
    boxes = []
    for x0, x1 in ((half, half + 40.0), (-half - 40.0, -half)):
        b = trimesh.creation.box(extents=[x1 - x0, p.keepout_x, 125.0])
        b.apply_translation([(x0 + x1) / 2, p.keepout_x / 2, -110.0 + 62.5])
        boxes.append(b)
    return trimesh.util.concatenate(boxes)


def hardware_ghosts(p, bolt_len=BOLT_LEN):
    """The M4 cap screw (with its washer) and nut, in the clip's own frame C, so the checks prove they fit the pockets."""
    x_out = p.mouth_width / 2 + p.ear_t
    zc, yb = p.clip_len / 2, p.bolt_y
    floor_x = -(x_out - p.head_cbore_depth)                  # floor of the head pocket (the washer rests on it)

    def cyl_x(r, x0, x1):
        m = trimesh.creation.cylinder(radius=r, height=x1 - x0, sections=64)
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))      # axis -> x
        m.apply_translation([(x0 + x1) / 2, yb, zc])
        return m

    under = floor_x - WASHER_T                               # underside of the head
    bolt = boolean_union([cyl_x(WASHER_OD / 2, under, floor_x), cyl_x(HEAD_D / 2, under - HEAD_H, under),
                          cyl_x(SHANK_D / 2, under, under + bolt_len)])
    seat = x_out - p.nut_depth
    r = NUT_AF / 2 / np.cos(np.radians(30))
    hexagon = [(yb + r * np.cos(np.radians(60 * i)), zc + r * np.sin(np.radians(60 * i))) for i in range(6)]
    nut = prism_x(hexagon, seat, seat + NUT_T)
    return bolt, nut, {"bolt_len_mm": bolt_len, "tip_x": round(under + bolt_len, 2), "nut_seat_x": round(seat, 2),
                       "nut_engaged_mm": round(max(min(under + bolt_len, seat + NUT_T) - seat, 0.0), 2),
                       "tip_past_ear_face_mm": round(max(under + bolt_len - x_out, 0.0), 2)}


def dovetail_tests(p):
    """Two short exact pieces to test the sliding fit only, printed flat: a plate with the tongue, and a block with the groove."""
    wr, h = p.dt_w_root / 2, p.dt_h
    x0 = p.dt_x0
    plate = ShapelyPolygon([(-30, x0 - 5), (30, x0 - 5), (30, x0), (-30, x0)])
    tongue = ShapelyPolygon([(-wr, x0 - 1), (wr, x0 - 1), (wr, x0), (wr + h, x0 + h), (-wr - h, x0 + h), (-wr, x0)])
    tongue_piece = prism_z(list(plate.union(tongue).exterior.coords)[:-1], 0.0, DOVETAIL_TEST_H)
    block = prism_z([(-30, p.pad_front), (30, p.pad_front), (30, p.pad_front + 12), (-30, p.pad_front + 12)], 0.0, DOVETAIL_TEST_H)
    y0, y1 = x0 - 0.5, p.tongue_tip
    groove = prism_z([(-p.dt_half_width(y0), y0), (p.dt_half_width(y0), y0), (p.dt_half_width(y1), y1), (-p.dt_half_width(y1), y1)],
                     -1.0, DOVETAIL_TEST_H + 1.0)
    return tongue_piece, boolean_difference(block, [groove])


def strut_grip_test():
    """Three short C-clips for the square strut, from snug to loose, so the owner can find which one snaps on and holds.
    Print upright. They differ in clearance and are told apart by height: 16 mm = 0.2 mm clearance, 20 mm = 0.4, 24 mm = 0.6."""
    from shapely.geometry import box
    wall, lip, lead, rr = 2.5, 1.0, 1.2, 2.5
    parts, x = [], 0.0
    for clearance, height in ((0.2, 16.0), (0.4, 20.0), (0.6, 24.0)):
        s = STRUT_MM + clearance
        h = s / 2 + wall
        outer = box(-h, -h, h, h).buffer(-rr).buffer(rr)                      # rounded outside corners
        mouth_w = s - 2 * lip                                                 # narrower than the strut, so it snaps over it
        mouth = ShapelyPolygon([(-mouth_w / 2, 0), (mouth_w / 2, 0), (mouth_w / 2, h - lead), (mouth_w / 2 + lead, h + 0.1),
                                (-mouth_w / 2 - lead, h + 0.1), (-mouth_w / 2, h - lead)])
        profile = outer.difference(box(-s / 2, -s / 2, s / 2, s / 2)).difference(mouth)
        m = trimesh.creation.extrude_polygon(profile, height)
        m.apply_translation([x, 0, 0])
        parts.append(m)
        x += s + 2 * wall + 6.0
    mesh = trimesh.util.concatenate(parts)
    mesh.apply_translation([-(mesh.bounds[0, 0] + mesh.bounds[1, 0]) / 2, 0, 0])
    return mesh


def section_axes(ax, meshes, colors, normal, origin, axes, title):
    for m, c in zip(meshes, colors):
        segs = section_segments(m, normal, origin, axes)
        if len(segs):
            ax.add_collection(LineCollection(segs, colors=c, lw=1.3))
    ax.autoscale()
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.4)
    ax.set_title(title, fontsize=11)


def main():
    OUT.mkdir(exist_ok=True)
    RENDERS.mkdir(exist_ok=True)
    for stale in OUT.glob("*.step"):        # v1-v5.1 exported editable STEP solids. v6 pieces are meshes (STL only).
        stale.unlink()

    p = replace(CupHolderParams(), **MEASURED, **CUP_OVERRIDES)
    
    # ---- The two pieces -----------------------------------------------------------------------
    module_U = build_module(p)
    clip_C = build_clip(p)
    clip_U = clip_to_U(clip_C, p)

    module_print, module_info = export_print("wagon-cup-module", module_U)
    clip_print, clip_info = export_print("wagon-cup-clip", clip_C)
    _, slice_info = export_print("wagon-cup-clip-test", build_clip(p, CLIP_TEST_LEN, dovetail=False))
    tongue_t, groove_t = dovetail_tests(p)
    _, tongue_info = export_print("wagon-dovetail-test-tongue", tongue_t)
    _, groove_info = export_print("wagon-dovetail-test-groove", groove_t)
    grip = strut_grip_test()
    assert grip.is_watertight, "strut grip test is not watertight"
    grip.export(OUT / "wagon-strut-grip-test.stl")
    grip_info = {"extents_mm": [round(float(v), 1) for v in grip.extents], "watertight": bool(grip.is_watertight),
                 "note": "three C-clips for the 13.5 mm square strut; clearance 0.2 / 0.4 / 0.6 mm = 16 / 20 / 24 mm tall; print upright"}

    # ---- Hardware: standard M4 screw + washer + nut (placed in the assembled pose) -------------------------
    bolt_C, nut_C, hardware = hardware_ghosts(p)
    bolt_U, nut_U = clip_to_U(bolt_C, p), clip_to_U(nut_C, p)
    for stale in ("wagon-bolt.stl", "wagon-nut.stl"):        # the printed M8 bolt and nut snapped; real hardware is used now
        (OUT / stale).unlink(missing_ok=True)

    # ---- Ghosts + checks (assembled, real use orientation) --------------------------------------------
    rail, cup, keepout = rail_ghost(p), tumbler_ghost(p), keepout_ghost(p)
    pairs = {
        "module_vs_clip": (module_U, clip_U), "module_vs_rail": (module_U, rail), "module_vs_tumbler": (module_U, cup),
        "clip_vs_rail": (clip_U, rail), "clip_vs_tumbler": (clip_U, cup),
        "module_vs_latch_strut_zone": (module_U, keepout), "clip_vs_latch_strut_zone": (clip_U, keepout),
        "bolt_vs_clip": (bolt_U, clip_U), "bolt_vs_module": (bolt_U, module_U), "bolt_vs_rail": (bolt_U, rail),
        "nut_vs_clip": (nut_U, clip_U), "nut_vs_module": (nut_U, module_U),
    }
    checks = {f"interference_{k}_cm3": round(interference_cm3(a, b), 4) for k, (a, b) in pairs.items()}
    # module_vs_clip is a CONTACT (the pad rests on the ear tops): marching-cubes noise of ~0.2 mm leaves a couple of mm3.
    for k, v in checks.items():
        limit = 0.01 if "module_vs_clip" in k else 0.002
        assert v < limit, f"{k} = {v} cm3: parts collide"

    # viewer meshes: light copies (the viewer limits meshes to 65k vertices)
    for name, m, faces in (("asm-module", module_U, 36000), ("asm-clip", clip_U, 26000)):
        decimate(m, faces).export(RENDERS / f"{name}.stl")
    bolt_U.export(RENDERS / "asm-bolt.stl")
    nut_U.export(RENDERS / "asm-nut.stl")
    rail.export(RENDERS / "ref-bar.stl")
    cup.export(RENDERS / "ref-tumbler.stl")
    keepout.export(RENDERS / "ref-keepout.stl")

    # ---- Report -------------------------------------------------------------------------------------------
    taper = (p.cup_top_d - p.cup_base_d) / p.cup_h
    params = {k: round(v, 3) if isinstance(v, float) else v for k, v in asdict(p).items()}
    params.update({
        "bore_d": round(2 * p.bore_r, 2),
        "snap_spread_each_lip": round((p.bar_d - p.mouth_width) / 2, 2),
        "hardware": "M4 x 30 (or 35) socket cap screw + 9 mm washer + M4 hex nut. Head in the inboard ear, nut in the outboard ear",
        "hardware_fit": hardware,
        "pocket_base_d": round(2 * p.pocket_r(0), 2),
        "pocket_rim_d": round(2 * p.r_in(p.top_z), 2),
        "pocket_outer_rim_d": round(2 * p.rim_outer_r, 2),
        "cup_axis_offset_from_rail": round(p.cup_axis_y, 1),
        "cup_base_below_rail_axis": round(-p.floor_y, 1),
        "top_above_rail_axis": round(p.top_z, 1),
        "est_cup_torque_on_clip_Nm": round(1.0 * 9.81 * p.cup_axis_y / 1000, 2),
        "tumbler_taper_mm_per_mm_dia": round(taper, 4),
        "latch_strut_reach_from_rail_axis": round(p.keepout_x, 1),
        "web_clearance_to_latch_strut": round(p.inboard_gap - p.keepout_x, 1),
        "module_clearance_to_window_ends_each_side": round(p.safe_window / 2 - p.rim_outer_r, 1),
        "clip_clearance_to_window_ends_each_side": round((p.safe_window - p.clip_len) / 2, 1),
        "dovetail_engagement_mm": round(p.top_z - p.ear_top_y, 1),
        "dovetail_width_tip_mm": round(p.dt_w_root + 2 * p.dt_h, 1),
        "clip_extent_below_rail_axis": round(-p.ear_bottom_y, 1),
        "clip_extent_above_rail_axis": round(p.top_z, 1),
    })
    report = {
        "dimensions_status": "Tube measured by owner (22.3 mm, confirmed on the side rail). Tumbler from retailer figures (owner OK for now).",
        "clip": clip_info, "module": module_info, "clamp_test_slice": slice_info,
        "dovetail_test_tongue": tongue_info, "dovetail_test_groove": groove_info, "strut_grip_test": grip_info,
        "hardware": hardware, "checks": checks, "params_mm": params,
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"clip": clip_info, "module": module_info, "checks": checks}, indent=2))

    # ---- Renders ---------------------------------------------------------------------------------------------
    cy = p.cup_axis_y
    assembled = trimesh.util.concatenate([module_U, clip_U, bolt_U, nut_U])
    views = {"from the rail side, above": ((0.0, 1.0, -0.55), (0, 0, 1)), "from the rail side, below": ((0.35, 1.0, 0.7), (0, 0, 1)),
             "from outboard, above": ((-0.5, -1.0, -0.6), (0, 0, 1)), "from underneath": ((0.0, 0.15, 1.0), (0, 1, 0))}
    fig, axs = plt.subplots(2, 2, figsize=(16, 16))
    for ax, (name, (d, up)) in zip(axs.ravel(), views.items()):
        img, ext = rasterize(assembled, np.array(d, float), np.array(up, float), px=800)
        ax.imshow(img, extent=ext)
        ax.set_title(name)
        ax.axis("off")
    fig.suptitle("wagon cup holder v6: clip + cup module + printed bolt and nut, in use orientation (rail along X, Z up)", fontsize=15)
    fig.savefig(RENDERS / "cup-holder.png", dpi=55, bbox_inches="tight")
    plt.close(fig)

    fig, axs = plt.subplots(2, 2, figsize=(18, 14))
    col = ("black", "tab:green", "tab:red", "tab:red", "tab:blue", "tab:orange")
    set1 = [module_U, clip_U, bolt_U, nut_U, rail, cup]
    section_axes(axs[0, 0], set1, col, [1, 0, 0], [0, 0, 0], [1, 2],
                 "mid-plane across the rail (X=0): module (black), clip (green), bolt/nut (red), rail (blue), tumbler (orange)")
    section_axes(axs[0, 1], [module_U, clip_U, rail], col, [0, 0, 1], [0, 0, 10.0], [0, 1],
                 "plan at Z=+10: module (black) with the clip's dovetail tongue (green) in its groove, rail (blue)")
    section_axes(axs[1, 0], [module_U, cup], ("black", "tab:blue"), [0, 1, 0], [0, cy, 0], [0, 2],
                 "through the cup axis: module wall and floor (black), tumbler (blue)")
    section_axes(axs[1, 1], [clip_U, bolt_U, nut_U, module_U], col, [0, 0, 1], [0, 0, p.bolt_y], [0, 1],
                 "plan through the clamp bolt axis: clip ears (green), bolt and nut (red), module (black)")
    fig.suptitle("wagon cup holder v6: cross-sections (real orientation, mm)", fontsize=15)
    fig.savefig(RENDERS / "sections.png", dpi=70, bbox_inches="tight")
    plt.close(fig)

    img_views = {"from the rail side, above": views["from the rail side, above"], "from outboard, above": views["from outboard, above"]}
    fig, axs = plt.subplots(1, 2, figsize=(16, 8))
    full = trimesh.util.concatenate([module_U, clip_U, bolt_U, nut_U, rail, cup])
    for ax, (name, (d, up)) in zip(axs, img_views.items()):
        img, ext = rasterize(full, np.array(d, float), np.array(up, float), px=800)
        ax.imshow(img, extent=ext)
        ax.set_title(name + " (with the 22.3 mm rail and the tumbler)")
        ax.axis("off")
    fig.savefig(RENDERS / "in-use.png", dpi=55, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
