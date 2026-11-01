"""Reproducible build for the wagon cup holder (two pieces: CLIP stays on, MODULE lifts off).

    python projects/wagon-cup-holder/build.py

model.py (parametric build123d, built in the print frame)
  -> output/wagon-cup-clip.step/.stl             clip: stays on the rail
  -> output/wagon-cup-module.step/.stl           cup module: lifts on and off the clip's dovetail
  -> output/wagon-cup-clip-test.stl              15 mm ring + ears slice, for the snap/clamp test print
  -> output/wagon-dovetail-test-tongue.stl       short tongue block -+ sliding-fit test print
  -> output/wagon-dovetail-test-groove.stl       short groove block -+ (print both, slide together)
  -> output/report.json                          dimensions, checks, parameters
  -> renders/*.png                               previews, sections, in-use pose
  -> renders/asm-*.stl, ref-*.stl                assembled-position meshes for the viewer / sections
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
import meshkit as mk  # noqa: E402
import numpy as np  # noqa: E402
import trimesh  # noqa: E402
from build123d import Align, Axis, Cone, Cylinder, Pos, Rotation, export_step  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from model import CupHolderParams, build, build_clip, build_dovetail_test  # noqa: E402
from render import render_sheet, section_segments  # noqa: E402

OUT = HERE / "output"
RENDERS = HERE / "renders"

# --- Real measurements (owner) ------------------------------------------------
# Change a value here (or in CupHolderParams) and re-run. Nothing is scan-derived.
MEASURED = {
    "bar_d": 22.3,      # owner, 2026-11-01: "about 22.3 mm" round tube (assumed the same on the side rail)
}
# Retailer figures for a 20 oz Yeti Rambler, NOT measured on the owner's cup yet:
#   cup_base_d 70 (2.75 in), cup_top_d 89 (3.5 in at the lid), cup_h ~165.
# Put the real numbers here once measured, e.g. {"cup_base_d": 71.0, "cup_top_d": 88.5}
CUP_OVERRIDES: dict = {}

CLIP_TEST_LEN = 15.0
DOVETAIL_TEST_Y = 14.0


def bbox_center(bb):
    return (bb.min.X + bb.max.X) / 2, (bb.min.Y + bb.max.Y) / 2


def shifted(solid, cx, cy):
    return Pos(-cx, -cy, 0) * solid


def print_pose(solid):
    """Individual print pose: longest footprint axis along X, centred on the XY origin, resting on Z=0."""
    bb = solid.bounding_box()
    turn = (bb.max.Y - bb.min.Y) > (bb.max.X - bb.min.X)
    s = solid.rotate(Axis.Z, 90) if turn else solid
    bb2 = s.bounding_box()
    cx, cy = bbox_center(bb2)
    return Pos(-cx, -cy, -bb2.min.Z) * s


def overhang_area_mm2(mesh, max_angle_deg=45.0, tol_deg=1.0):
    """Area of faces that face down more steeply than the overhang limit (excluding the bed contact).
    The tolerance keeps faces at exactly 45 deg (the teardrop foot, dovetail flanks) from tipping over on rounding."""
    limit = -np.sin(np.radians(max_angle_deg + tol_deg))
    n, c = mesh.face_normals, mesh.triangles_center
    bad = (n[:, 2] < limit) & (c[:, 2] > 0.05)
    return float(mesh.area_faces[bad].sum())


def keepout_mesh(p, cx, cy):
    """Approximate zones where the end brackets' red latch + diagonal strut live, one at each end of the
    clear window, centred on the cup module. Only the OUTWARD REACH (keepout_reach past the bar surface) is
    from the owner; the Y extent and the 'they sit only beyond the clear window' assumption are mine."""
    zc = p.cup_zc
    half = p.safe_window / 2
    x0, x1 = 0.0, p.keepout_x
    y0, y1 = -110.0, 15.0
    depth = 40.0
    boxes = []
    for z0, z1 in ((zc + half, zc + half + depth), (zc - half - depth, zc - half)):
        b = trimesh.creation.box(extents=[x1 - x0, y1 - y0, z1 - z0])
        b.apply_translation([(x0 + x1) / 2 - cx, (y0 + y1) / 2 - cy, (z0 + z1) / 2])
        boxes.append(b)
    return trimesh.util.concatenate(boxes)


def interference_cm3(a, b):
    inter = a.intersection(b, engine="manifold")
    return float(abs(inter.volume)) / 1000.0 if len(inter.faces) else 0.0


def section_axes(ax, meshes, normal, origin, axes, title,
                 colors=("black", "tab:green", "tab:blue", "tab:red", "tab:orange")):
    for m, c in zip(meshes, colors):
        segs = section_segments(m, normal, origin, axes)
        if len(segs):
            ax.add_collection(LineCollection(segs, colors=c, lw=1.3))
    ax.autoscale()
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.4)
    ax.set_title(title, fontsize=11)


def export_piece(name, solid):
    """Export one printable piece (STEP + STL) in its own print pose and return its mesh + report."""
    posed = print_pose(solid)
    export_step(posed, str(OUT / f"{name}.step"))
    mesh = mk.cad_to_mesh(posed)
    info = mk.report(mesh)
    assert info["watertight"], f"{name} mesh is not watertight"
    assert info.get("self_intersecting_faces", 0) == 0, f"{name} mesh self-intersects"
    info["overhang_area_over_45deg_mm2"] = round(overhang_area_mm2(mesh), 1)
    mesh.export(OUT / f"{name}.stl")
    return mesh, info


def main():
    OUT.mkdir(exist_ok=True)
    RENDERS.mkdir(exist_ok=True)
    for stale in ("wagon-cup-holder.step", "wagon-cup-holder.stl"):   # v1/v2 single-piece outputs
        (OUT / stale).unlink(missing_ok=True)

    p = replace(CupHolderParams(), **MEASURED, **CUP_OVERRIDES)
    parts = build(p)

    # ---- Printable pieces -------------------------------------------------------------------
    clip_mesh, clip_info = export_piece("wagon-cup-clip", parts["clip"])
    module_mesh, module_info = export_piece("wagon-cup-module", parts["module"])

    _, clamp_info = export_piece("wagon-cup-clip-test", build_clip(p, CLIP_TEST_LEN, dovetail=False))
    tongue, groove = build_dovetail_test(p, DOVETAIL_TEST_Y)
    _, tongue_info = export_piece("wagon-dovetail-test-tongue", tongue)
    _, groove_info = export_piece("wagon-dovetail-test-groove", groove)

    # ---- Assembled-position meshes (shared frame) for the viewer, sections and checks ---------------
    cb = parts["clip"].bounding_box()
    mb = parts["module"].bounding_box()
    cx = (min(cb.min.X, mb.min.X) + max(cb.max.X, mb.max.X)) / 2
    cy = (min(cb.min.Y, mb.min.Y) + max(cb.max.Y, mb.max.Y)) / 2
    clip = mk.cad_to_mesh(shifted(parts["clip"], cx, cy))
    module = mk.cad_to_mesh(shifted(parts["module"], cx, cy))
    rail_p = Pos(0, 0, -20) * Cylinder(p.bar_d / 2, 160, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cone = Cone(p.cup_base_d / 2, p.cup_top_d / 2, p.cup_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cup_p = Pos(p.pocket_cx, p.floor_y, p.cup_zc) * (Rotation(-90, 0, 0) * cone)
    rail = mk.cad_to_mesh(shifted(rail_p, cx, cy))
    cup = mk.cad_to_mesh(shifted(cup_p, cx, cy))
    keepout = keepout_mesh(p, cx, cy)
    keepout.export(RENDERS / "ref-keepout.stl")
    clip.export(RENDERS / "asm-clip.stl")
    module.export(RENDERS / "asm-module.stl")
    rail.export(RENDERS / "ref-bar.stl")
    cup.export(RENDERS / "ref-tumbler.stl")

    # ---- Checks (assembled position) -------------------------------------------------------------
    checks = {
        "interference_module_vs_clip_cm3": round(interference_cm3(module, clip), 3),
        "interference_module_vs_rail_cm3": round(interference_cm3(module, rail), 3),
        "interference_module_vs_tumbler_cm3": round(interference_cm3(module, cup), 3),
        "interference_clip_vs_rail_cm3": round(interference_cm3(clip, rail), 3),
        "interference_clip_vs_tumbler_cm3": round(interference_cm3(clip, cup), 3),
        "interference_module_vs_latch_strut_zone_cm3": round(interference_cm3(module, keepout), 3),
        "interference_clip_vs_latch_strut_zone_cm3": round(interference_cm3(clip, keepout), 3),
    }
    for name, val in checks.items():
        assert val < 0.01, f"{name} = {val}: parts collide"

    taper = (p.cup_top_d - p.cup_base_d) / p.cup_h
    params = {k: round(v, 2) if isinstance(v, float) else v for k, v in asdict(p).items()}
    params.update({
        "bore_d": round(2 * p.bore_r, 2),
        "snap_spread_each_lip": round((p.bar_d - p.mouth_width) / 2, 2),
        "bolt_needed": "M4 x 35 socket-head screw + M4 nut",
        "pocket_base_d": round(2 * p.pocket_r(0), 2),
        "pocket_rim_d": round(2 * p.pocket_r(p.pocket_depth), 2),
        "pocket_outer_d": round(2 * p.outer_r, 2),
        "cup_axis_offset_from_rail": round(p.pocket_cx, 1),
        "pocket_rim_height_above_rail_axis": round(p.floor_y + p.pocket_depth, 1),
        "cup_base_below_rail_axis": round(-p.floor_y, 1),
        "est_cup_torque_on_clip_Nm": round(1.0 * 9.81 * p.pocket_cx / 1000, 2),
        "dovetail_engagement_mm": round(p.dt_y1 - p.ear_top_y, 1),
        "dovetail_width_tip_mm": round(p.dt_w_root + 2 * p.dt_h, 1),
        "clip_extent_above_rail_axis": round(p.dt_y1, 1),
        "clip_extent_below_rail_axis": round(-p.ear_bottom_y, 1),
        "clip_extent_outboard_of_rail_axis": round(p.dt_x0 + p.dt_h, 1),
        "tumbler_taper_mm_per_mm_dia": round(taper, 4),
        "latch_strut_reach_from_rail_axis": round(p.keepout_x, 1),
        "web_clearance_to_latch_strut": round(p.web_gap - p.keepout_x, 1),
        "module_clearance_to_window_ends_each_side": round((p.safe_window - 2 * p.outer_r) / 2, 1),
        "clip_clearance_to_window_ends_each_side": round((p.safe_window - p.clip_len) / 2, 1),
    })
    report = {
        "dimensions_status": "Tube measured by owner (22.3 mm); assumed same on the right side rail. "
                             "Tumbler from retailer figures, NOT measured.",
        "clip": clip_info,
        "module": module_info,
        "clamp_test_slice": clamp_info,
        "dovetail_test_tongue": tongue_info,
        "dovetail_test_groove": groove_info,
        "checks": checks,
        "params_mm": params,
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"clip": clip_info, "module": module_info, "checks": checks}, indent=2))

    # ---- Renders --------------------------------------------------------------------------------
    rail_y = -cy                                   # the rail axis (Y_print = 0) in the shared frame
    render_sheet([module, clip, rail, cup], str(RENDERS / "cup-holder.png"),
                 title="wagon cup holder, print orientation, assembled (black = module, red = clip, "
                       "blue = 22.3 mm rail, green = Yeti 20 oz from retailer dims)",
                 labels=["cup module", "clip", "side rail", "tumbler"],
                 sections_y=(rail_y,), sections_x=())

    fig, axs = plt.subplots(2, 2, figsize=(18, 14))
    z_sec = p.cup_zc - 14
    section_axes(axs[0, 0], [clip, module, rail, keepout], [0, 0, 1], [0, 0, z_sec], [0, 1],
                 f"across the rail at z={z_sec:.0f}: clip (black), module (green), rail (blue)")
    section_axes(axs[0, 1], [module, cup], [0, 1, 0], [0, p.floor_y + p.pocket_depth / 2 - cy, 0], [0, 2],
                 "across the pocket mid-height: wall (black), tumbler (green)")
    section_axes(axs[1, 0], [clip, module], [0, 1, 0], [0, 10.0 - cy, 0], [0, 2],
                 "through the dovetail at y=+10 above the rail axis: tongue (black) in groove (green)")
    section_axes(axs[1, 1], [clip, module, keepout], [0, 1, 0], [0, p.bolt_y - cy, 0], [0, 2],
                 "through the bolt axis: ears, nut slot, head pocket (black), latch/strut zones (blue)")
    fig.suptitle("wagon cup holder: cross-sections (print orientation, mm)", fontsize=15)
    fig.savefig(RENDERS / "sections.png", dpi=70, bbox_inches="tight")
    plt.close(fig)

    # In-use pose: rail horizontal (fore-aft), cup upright, hanging off the outside of the rail.
    # Print frame (X out, Y up, Z along the rail) -> use frame (rail, out, up) = (z, x, y).
    use = trimesh.util.concatenate([module, clip, rail, cup, keepout])
    use.vertices = np.c_[use.vertices[:, 2], use.vertices[:, 0], use.vertices[:, 1]]
    use.vertices -= [use.bounds[:, 0].mean(), use.bounds[:, 1].mean(), use.bounds[0, 2]]
    use.fix_normals()
    render_sheet(use, str(RENDERS / "in-use.png"),
                 title="in use: rail along X, clip on the rail, cup module hanging off the outside",
                 labels=["module + clip + rail + tumbler + latch/strut zones"], sections_y=(0.0,), sections_x=())


if __name__ == "__main__":
    main()
