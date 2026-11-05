"""Reproducible build for the wagon cup holder (v6: two organic pieces, CLIP stays on, MODULE lifts off).

    python projects/wagon-cup-holder/build.py        (about 1 minute)

model.py (signed-distance-field bodies + exact cuts; see its docstring)
  -> output/wagon-cup-clip.stl             clip: stays on the rail (printed ring-axis-vertical)
  -> output/wagon-cup-module.stl           cup module: lifts on and off the clip's dovetail (printed upright)
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
from model import (CupHolderParams, mirror_along_rail, build_clip, build_module, clip_to_U, print_pose, prism_z, strut_frame,  # noqa: E402
                   strut_ghost, boolean_difference)
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


def dovetail_tests(p, clearances=(0.30, 0.20, 0.10)):
    """Short exact pieces to test the sliding fit only, printed flat: one plate with the tongue, and one groove block per clearance
    (per side). 0.35 was the first test; the full parts are now at p.dt_clear."""
    wr, h = p.dt_w_root / 2, p.dt_h
    x0 = p.dt_x0
    plate = ShapelyPolygon([(-30, x0 - 5), (30, x0 - 5), (30, x0), (-30, x0)])
    tongue = ShapelyPolygon([(-wr, x0 - 1), (wr, x0 - 1), (wr, x0), (wr + h, x0 + h), (-wr - h, x0 + h), (-wr, x0)])
    tongue_piece = prism_z(list(plate.union(tongue).exterior.coords)[:-1], 0.0, DOVETAIL_TEST_H)
    grooves = {}
    for c in clearances:
        q = replace(p, dt_clear=c)
        block = prism_z([(-30, q.pad_front), (30, q.pad_front), (30, q.pad_front + 12), (-30, q.pad_front + 12)], 0.0, DOVETAIL_TEST_H)
        y0, y1 = x0 - 0.5, q.tongue_tip
        groove = prism_z([(-q.dt_half_width(y0), y0), (q.dt_half_width(y0), y0), (q.dt_half_width(y1), y1), (-q.dt_half_width(y1), y1)],
                         -1.0, DOVETAIL_TEST_H + 1.0)
        grooves[c] = boolean_difference(block, [groove])
    return tongue_piece, grooves


def strut_grip_test(p):
    """Three short C-clips for the square strut, same clearance (p.grip_clearance), with deeper and deeper lips, to find how much
    holding power is enough. In v8 the C's closed wall faces the cup, so these lips only keep the clip on when the cup is not pulling.
    Print upright, with the mouth side toward you. Told apart by height: 16 mm = lip 1.2, 20 mm = lip 1.6 (the default), 24 mm = lip 2.0; walls 3.0."""
    from shapely.geometry import box
    lead, rr = p.grip_lead, 2.5
    parts, x = [], 0.0
    for lip, wall, height in ((1.2, 3.0, 16.0), (1.6, 3.0, 20.0), (2.0, 3.0, 24.0)):
        s = p.strut_size + p.grip_clearance
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
    clip_info["supports"] = ("needed under the strut grip and leg: with the ring axis vertical the grip tunnel runs ~31 deg above horizontal, "
                             "so its ceiling and the leg underside overhang. Use normal (auto) supports, 'support on build plate + model'; "
                             "the ring, mouth and dovetail print without")
    # Left-hand side: the mirror image of the right clip (the module is symmetric along the rail, so it is shared).
    clip_C_left = mirror_along_rail(clip_C, p, frame="C")
    clip_U_left = mirror_along_rail(clip_U)                      # the real-use pose of the left clip, for the fit checks
    _, clip_left_info = export_print("wagon-cup-clip-left", clip_C_left)
    clip_left_info["supports"] = clip_info["supports"]
    assert abs(clip_left_info["volume_cm3"] - clip_info["volume_cm3"]) < 0.05, "left clip is not the mirror of the right one"
    tongue_t, groove_ts = dovetail_tests(p)
    _, tongue_info = export_print("wagon-dovetail-test-tongue", tongue_t)
    groove_info = {}
    for c, g in groove_ts.items():
        _, groove_info[f"{c:.2f}_mm_per_side"] = export_print(f"wagon-dovetail-test-groove-{c:.2f}", g)
    (OUT / "wagon-dovetail-test-groove.stl").unlink(missing_ok=True)
    grip = strut_grip_test(p)
    assert grip.is_watertight, "strut grip test is not watertight"
    grip.export(OUT / "wagon-strut-grip-test.stl")
    grip_info = {"extents_mm": [round(float(v), 1) for v in grip.extents], "watertight": bool(grip.is_watertight),
                 "note": "three C-clips for the 13.5 mm square strut, 0.3 mm clearance; lips 1.2 / 1.6 / 2.0 mm = 16 / 20 / 24 mm tall; print upright"}

    for stale in ("wagon-bolt.stl", "wagon-nut.stl", "wagon-cup-clip-test.stl"):    # the screw clamp is gone: the strut grip locks the clip
        (OUT / stale).unlink(missing_ok=True)

    # ---- Ghosts + checks (assembled, real use orientation) --------------------------------------------
    rail, cup, keepout = rail_ghost(p), tumbler_ghost(p), keepout_ghost(p)
    strut = strut_ghost(p)                                                  # nominal gap: the clip's grip is built around this
    strut_view = strut_ghost(p, t0=-59.0, t1=215.0)                         # pivot screw down toward the lower frame, for the viewer
    pairs = {
        "module_vs_clip": (module_U, clip_U), "module_vs_rail": (module_U, rail), "module_vs_tumbler": (module_U, cup),
        "clip_vs_rail": (clip_U, rail), "clip_vs_tumbler": (clip_U, cup),
        "module_vs_latch_strut_zone": (module_U, keepout), "clip_vs_latch_strut_zone": (clip_U, keepout),
        "clip_vs_strut": (clip_U, strut), "module_vs_strut": (module_U, strut),
    }
    checks = {f"interference_{k}_cm3": round(interference_cm3(a, b), 4) for k, (a, b) in pairs.items()}
    # module_vs_clip is a CONTACT (the pad rests on the ear tops): marching-cubes noise of ~0.2 mm leaves a couple of mm3.
    for k, v in checks.items():
        limit = 0.01 if "module_vs_clip" in k else 0.002
        assert v < limit, f"{k} = {v} cm3: parts collide"

    # The same checks for the left side: the mirrored clip, strut and latch zones against the SAME module (unmirrored), rail and tumbler.
    strut_L, keepout_L = mirror_along_rail(strut), mirror_along_rail(keepout)
    pairs_L = {
        "module_vs_clip_left": (module_U, clip_U_left), "clip_left_vs_rail": (clip_U_left, rail), "clip_left_vs_tumbler": (clip_U_left, cup),
        "clip_left_vs_latch_strut_zone": (clip_U_left, keepout_L), "module_vs_latch_strut_zone_left": (module_U, keepout_L),
        "clip_left_vs_strut_left": (clip_U_left, strut_L), "module_vs_strut_left": (module_U, strut_L),
    }
    checks_L = {f"interference_{k}_cm3": round(interference_cm3(a, b), 4) for k, (a, b) in pairs_L.items()}
    for k, v in checks_L.items():
        limit = 0.01 if "module_vs_clip" in k else 0.002
        assert v < limit, f"{k} = {v} cm3: parts collide on the left side"
    checks.update(checks_L)

    # How far the strut's position can differ from my estimate before the clip must rotate on the bar (informational, not a pass/fail):
    gap_sensitivity = {}
    for gap in (4.0, 7.0):
        st = strut_ghost(p, gap=gap)
        gap_sensitivity[f"gap_{gap:g}_mm"] = {"clip_overlap_mm3": round(interference_cm3(clip_U, st) * 1000, 1),
                                              "module_overlap_mm3": round(interference_cm3(module_U, st) * 1000, 1),
                                              "rotation_to_follow_deg": round(float(np.degrees(np.arctan(abs(gap - p.strut_gap_in) / np.hypot(*strut_frame(p)[0][1:])))), 2)}

    # viewer meshes: light copies (the viewer limits meshes to 65k vertices)
    for name, m, faces in (("asm-module", module_U, 36000), ("asm-clip", clip_U, 26000), ("asm-clip-left", clip_U_left, 26000)):
        decimate(m, faces).export(RENDERS / f"{name}.stl")
    strut_view.export(RENDERS / "ref-strut.stl")
    mirror_along_rail(strut_view).export(RENDERS / "ref-strut-left.stl")
    rail.export(RENDERS / "ref-bar.stl")
    cup.export(RENDERS / "ref-tumbler.stl")
    keepout.export(RENDERS / "ref-keepout.stl")

    # ---- Report -------------------------------------------------------------------------------------------
    taper = (p.cup_top_d - p.cup_base_d) / p.cup_h
    params = {k: round(v, 3) if isinstance(v, float) else v for k, v in asdict(p).items()}
    params.update({
        "bore_d": round(2 * p.bore_r, 2),
        "snap_spread_each_lip": round((p.bar_d - p.mouth_width) / 2, 2),
        "clamp": "two-point: ring on the bar + a leg to a C-clip on the angled strut. No screw, nut or pockets",
        "strut_nominal_gap_mm": p.strut_gap_in,
        "strut_gap_sensitivity": gap_sensitivity,
        "grip_centre_depth_below_bar_axis_mm": round(float(p.strut_depth(p.grip_x)), 1),
        "arm_y_out_mm": p.arm_y_out,
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
        "clip": clip_info, "clip_left": clip_left_info, "module": module_info,
        "dovetail_test_tongue": tongue_info, "dovetail_test_groove": groove_info, "strut_grip_test": grip_info,
        "checks": checks, "params_mm": params,
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"clip": clip_info, "module": module_info, "checks": checks}, indent=2))

    # ---- Renders ---------------------------------------------------------------------------------------------
    cy = p.cup_axis_y
    assembled = trimesh.util.concatenate([module_U, clip_U])
    views = {"from the rail side, above": ((0.0, 1.0, -0.55), (0, 0, 1)), "from the rail side, below": ((0.35, 1.0, 0.7), (0, 0, 1)),
             "from outboard, above": ((-0.5, -1.0, -0.6), (0, 0, 1)), "from underneath": ((0.0, 0.15, 1.0), (0, 1, 0))}
    fig, axs = plt.subplots(2, 2, figsize=(16, 16))
    for ax, (name, (d, up)) in zip(axs.ravel(), views.items()):
        img, ext = rasterize(assembled, np.array(d, float), np.array(up, float), px=800)
        ax.imshow(img, extent=ext)
        ax.set_title(name)
        ax.axis("off")
    fig.suptitle("wagon cup holder v8: two-point clip + cup module, in use orientation (rail along X, Z up; the strut-side end is +X)", fontsize=15)
    fig.savefig(RENDERS / "cup-holder.png", dpi=55, bbox_inches="tight")
    plt.close(fig)

    fig, axs = plt.subplots(2, 2, figsize=(18, 14))
    col = ("black", "tab:green", "tab:blue", "tab:red", "tab:orange")
    gx = p.grip_x
    section_axes(axs[0, 0], [module_U, clip_U, rail, strut, cup], col, [1, 0, 0], [gx, 0, 0], [1, 2],
                 f"across the rail through the grip (X=+{gx:g}): module (black), clip with arm + grip (green), rail + strut (blue/red), tumbler (orange)")
    section_axes(axs[0, 1], [module_U, clip_U, rail, strut], col, [0, 0, 1], [0, 0, 10.0], [0, 1],
                 "plan at Z=+10: module (black) with the clip's dovetail tongue (green) in its groove, rail (blue), strut (red)")
    section_axes(axs[1, 0], [module_U, cup], ("black", "tab:blue"), [0, 1, 0], [0, p.cup_axis_y, 0], [0, 2],
                 "through the cup axis: module wall and floor (black), tumbler (blue)")
    origin, Rg = strut_frame(p)
    segs_ax = axs[1, 1]
    sec = clip_U.section(plane_origin=origin, plane_normal=Rg[:, 2])
    for e in sec.entities:
        pts = sec.vertices[e.points] - origin
        segs_ax.plot(pts @ Rg[:, 0], pts @ Rg[:, 1], "k", lw=2)
    sz = p.strut_size
    segs_ax.add_patch(plt.Rectangle((-sz / 2, -sz / 2), sz, sz, fc="#9ca3af", ec="#1f2937", alpha=0.7, zorder=0))
    segs_ax.set_aspect("equal"); segs_ax.grid(alpha=0.4); segs_ax.set_xlim(-16, 22); segs_ax.set_ylim(-16, 16)
    segs_ax.set_title("section across the strut at the grip: the 13.5 mm square strut (grey) in the C. Cup side is to the right", fontsize=11)
    fig.suptitle("wagon cup holder v8: cross-sections (real orientation, mm)", fontsize=15)
    fig.savefig(RENDERS / "sections.png", dpi=70, bbox_inches="tight")
    plt.close(fig)

    img_views = {"from the rail side, above": views["from the rail side, above"], "from outboard, above": views["from outboard, above"]}
    fig, axs = plt.subplots(1, 2, figsize=(16, 8))
    full = trimesh.util.concatenate([module_U, clip_U, strut_view, rail, cup])
    for ax, (name, (d, up)) in zip(axs, img_views.items()):
        img, ext = rasterize(full, np.array(d, float), np.array(up, float), px=800)
        ax.imshow(img, extent=ext)
        ax.set_title(name + " (with the rail, the strut and the tumbler)")
        ax.axis("off")
    fig.savefig(RENDERS / "in-use.png", dpi=55, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
