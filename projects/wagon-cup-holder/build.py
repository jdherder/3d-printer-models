"""Reproducible build for the wagon cup holder.

    python projects/wagon-cup-holder/build.py

model.py (parametric build123d, built in the print frame; no rotation needed)
  -> output/wagon-cup-holder.step        editable solid for Fusion (print orientation)
  -> output/wagon-cup-holder.stl         print-ready mesh
  -> output/wagon-cup-clip-test.stl      15 mm slice of the clip only, for the snap-fit test print
  -> output/report.json                  dimensions, checks, parameters
  -> renders/*.png                       previews, sections, in-use pose
  -> renders/ref-bar.stl, ref-tumbler.stl  ghost bar + tumbler for the viewer / sections
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
from model import CupHolderParams, build, build_clip  # noqa: E402
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


def final_transform(part_bb):
    """Print frame -> output frame: just centre the footprint on the XY origin (Z is the bed).
    The longest footprint axis is already X (asserted in main)."""
    return (part_bb.min.X + part_bb.max.X) / 2, (part_bb.min.Y + part_bb.max.Y) / 2


def to_final_cad(solid, cx, cy):
    return Pos(-cx, -cy, 0) * solid


def to_final_mesh(mesh, cx, cy):
    m = mesh.copy()
    m.apply_translation([-cx, -cy, 0])
    return m


def overhang_area_mm2(mesh, max_angle_deg=45.0, tol_deg=1.0):
    """Area of faces that face down more steeply than the overhang limit (excluding the bed contact).
    The tolerance keeps faces at exactly 45 deg (the teardrop foot) from tipping over on rounding."""
    limit = -np.sin(np.radians(max_angle_deg + tol_deg))
    n, c = mesh.face_normals, mesh.triangles_center
    bad = (n[:, 2] < limit) & (c[:, 2] > 0.05)
    return float(mesh.area_faces[bad].sum())


def interference_cm3(a, b):
    inter = a.intersection(b, engine="manifold")
    return float(abs(inter.volume)) / 1000.0 if len(inter.faces) else 0.0


def section_axes(ax, meshes, normal, origin, axes, title, colors=("black", "tab:blue", "tab:red")):
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

    p = replace(CupHolderParams(), **MEASURED, **CUP_OVERRIDES)

    # ---- Main part ----------------------------------------------------------------
    solid_p = build(p)
    bb = solid_p.bounding_box()
    assert (bb.max.X - bb.min.X) >= (bb.max.Y - bb.min.Y), "longest footprint axis should be X"
    cx, cy = final_transform(bb)
    solid = to_final_cad(solid_p, cx, cy)
    export_step(solid, str(OUT / "wagon-cup-holder.step"))
    model = mk.cad_to_mesh(solid)
    info = mk.report(model)
    assert info["watertight"], "cup holder mesh is not watertight"
    assert info.get("self_intersecting_faces", 0) == 0, "cup holder mesh self-intersects"
    model.export(OUT / "wagon-cup-holder.stl")

    # ---- Clip-only fit-test slice -----------------------------------------------------
    clip_p = build_clip(p, CLIP_TEST_LEN)
    ccx, ccy = final_transform(clip_p.bounding_box())
    clip = mk.cad_to_mesh(to_final_cad(clip_p, ccx, ccy))
    clip_info = mk.report(clip)
    assert clip_info["watertight"], "clip test mesh is not watertight"
    clip.export(OUT / "wagon-cup-clip-test.stl")

    # ---- Ghost bar + tumbler (same frame as the part) -----------------------------------
    bar_p = Pos(0, 0, -20) * Cylinder(p.bar_d / 2, 160, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cone = Cone(p.cup_base_d / 2, p.cup_top_d / 2, p.cup_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cup_p = Pos(p.pocket_cx, p.floor_y, p.cup_zc) * (Rotation(-90, 0, 0) * cone)
    bar = mk.cad_to_mesh(to_final_cad(bar_p, cx, cy))
    cup = mk.cad_to_mesh(to_final_cad(cup_p, cx, cy))
    bar.export(RENDERS / "ref-bar.stl")
    cup.export(RENDERS / "ref-tumbler.stl")

    # ---- Checks ---------------------------------------------------------------------------
    overhang = overhang_area_mm2(model)
    checks = {
        "overhang_area_over_45deg_mm2": round(overhang, 1),
        "interference_with_bar_cm3": round(interference_cm3(model, bar), 3),
        "interference_with_tumbler_cm3": round(interference_cm3(model, cup), 3),
    }
    assert checks["interference_with_tumbler_cm3"] < 0.01, "tumbler collides with the pocket"
    assert checks["interference_with_bar_cm3"] < 0.01, "bar collides with the clip"

    taper = (p.cup_top_d - p.cup_base_d) / p.cup_h
    params = {k: round(v, 2) if isinstance(v, float) else v for k, v in asdict(p).items()}
    params.update({
        "bore_d": round(2 * p.bore_r, 2),
        "snap_spread_each_lip": round((p.bar_d - p.mouth_width) / 2, 2),
        "bolt_length_needed": "M4 x 35 + M4 nut",
        "pocket_base_d": round(2 * p.pocket_r(0), 2),
        "pocket_rim_d": round(2 * p.pocket_r(p.pocket_depth), 2),
        "pocket_outer_d": round(2 * p.outer_r, 2),
        "cup_axis_offset_from_rail": round(p.pocket_cx, 1),
        "pocket_rim_height_above_rail_axis": round(p.floor_y + p.pocket_depth, 1),
        "cup_base_below_rail_axis": round(-p.floor_y, 1),
        "est_cup_torque_on_clip_Nm": round(1.0 * 9.81 * p.pocket_cx / 1000, 2),
        "tumbler_taper_mm_per_mm_dia": round(taper, 4),
    })
    report = {
        "dimensions_status": "Tube measured by owner (22.3 mm); assumed same on the right side rail. Tumbler from retailer figures, NOT measured.",
        "part": info,
        "clip_test": clip_info,
        "checks": checks,
        "params_mm": params,
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"part": info, "checks": checks}, indent=2))

    # ---- Renders --------------------------------------------------------------------------
    rail_y = -cy                                   # the rail axis (Y_print = 0) in the final frame
    render_sheet([model, bar, cup], str(RENDERS / "cup-holder.png"),
                 title="wagon cup holder, print orientation (black = holder, red = 22.3 mm rail, "
                       "blue = Yeti 20 oz from retailer dims)",
                 labels=["cup holder", "side rail", "tumbler"],
                 sections_y=(rail_y,), sections_x=())

    # Cross-sections that render_sheet can't draw (planes whose normal is Z or whose axes differ).
    fig, axs = plt.subplots(2, 2, figsize=(18, 14))
    z_mid = p.clip_len / 2
    section_axes(axs[0, 0], [model, bar], [0, 0, 1], [0, 0, z_mid], [0, 1],
                 f"across the rail at z={z_mid:g}: clip + shelf + web (black), rail (blue)")
    section_axes(axs[0, 1], [model, cup], [0, 1, 0], [0, p.floor_y + p.pocket_depth / 2 - cy, 0], [0, 2],
                 "across the pocket mid-height: wall (black), tumbler (blue)")
    section_axes(axs[1, 0], [model, bar], [0, 1, 0], [0, p.bolt_y - cy, 0], [0, 2],
                 "through the bolt axis: ears, nut slot, key window (black), rail (blue)")
    section_axes(axs[1, 1], [clip], [0, 0, 1], [0, 0, CLIP_TEST_LEN / 2], [0, 1],
                 "fit-test clip slice (15 mm), at the bolt")
    fig.suptitle("wagon cup holder: cross-sections (print orientation, mm)", fontsize=15)
    fig.savefig(RENDERS / "sections.png", dpi=70, bbox_inches="tight")
    plt.close(fig)

    # In-use pose: rail horizontal (fore-aft), cup upright, hanging off the outside of the rail.
    # Print frame (X out, Y up, Z along the rail) -> use frame (rail, out, up) = (z, x, y).
    use = trimesh.util.concatenate([model, bar, cup])
    use.vertices = np.c_[use.vertices[:, 2], use.vertices[:, 0], use.vertices[:, 1]]
    use.vertices -= [use.bounds[:, 0].mean(), use.bounds[:, 1].mean(), use.bounds[0, 2]]
    use.fix_normals()
    render_sheet(use, str(RENDERS / "in-use.png"),
                 title="in use: rail along X, cup hanging off its outside (holder + rail + tumbler)",
                 labels=["holder + rail + tumbler"], sections_y=(0.0,), sections_x=())


if __name__ == "__main__":
    main()
