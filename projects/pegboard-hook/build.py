"""Reproducible build for the pegboard hook.

    python projects/pegboard-hook/build.py        (a few seconds)

model.py (build123d, parameters from the owner's photos + caliper)
  -> output/pegboard-hook.step        editable solid for Fusion (print pose)
  -> output/pegboard-hook.stl         print-ready mesh: lying on its side, 0.4 mm flat on the bed side
  -> output/report.json               dimensions, checks, parameters
  -> renders/model.png                shaded views + sections
  -> renders/photo-overlay.png        model outline drawn over the owner's photo (the fit check)
  -> renders/asm-hook.stl, ref-pegboard.stl   hanging on a 1/4" pegboard, for the viewer
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / "tools"), str(HERE)]

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import meshkit as mk  # noqa: E402
import numpy as np  # noqa: E402
import trimesh  # noqa: E402
from build123d import export_step  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from model import HookParams, build_hook, print_pose  # noqa: E402
from PIL import Image  # noqa: E402
from render import render_sheet, section_segments  # noqa: E402

OUT = HERE / "output"
RENDERS = HERE / "renders"
PHOTO = HERE / "source" / "photo-2026-11-05-tape-vertical.jpg"

# --- Real measurements (owner) ---------------------------------------------------
MEASURED = {
    "wire_d": 5.53,     # caliper, 2026-11-05
}

# Photo -> model mapping used to measure the profile (photo-2026-11-05-tape-vertical.jpg, tape inch marks ~245 px apart).
PHOTO_PX_PER_MM = 9.65
PHOTO_ORIGIN_PX = (750.0, 1308.0)     # pixel of the model origin (bottom corner of the wire centreline)

# 1/4" pegboard for context: 1/4" holes on a 1" grid, ~1/4" thick (US standard hardboard pegboard)
BOARD_T, HOLE_D, PITCH = 6.35, 6.35, 25.4


def use_to_zup(mesh):
    """Use frame (x out from board, y up, z across) -> viewer/world Z-up (X out, Y across, Z up)."""
    m = mesh.copy()
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    return m


def pegboard(p: HookParams):
    """A 1/4" pegboard patch in the use frame, holes lined up with the hook's pin and jog."""
    w, h = 3 * PITCH, 4 * PITCH
    yc = p.pin_y + PITCH / 2
    board = trimesh.creation.box(extents=[BOARD_T, h, w])
    board.apply_translation([-p.wire_r - BOARD_T / 2, yc, 0])
    holes = []
    for iy in range(-1, 3):
        for iz in range(-1, 2):
            c = trimesh.creation.cylinder(radius=HOLE_D / 2, height=BOARD_T + 2, sections=32)
            c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
            c.apply_translation([-p.wire_r - BOARD_T / 2, p.pin_y + iy * PITCH, iz * PITCH])
            holes.append(c)
    return board.difference(trimesh.util.concatenate(holes), engine="manifold")


def photo_overlay(use_mesh, p: HookParams, path):
    """Model outline (centre section, z = 0) drawn over the owner's photo, in the photo's pixel frame."""
    img = Image.open(PHOTO).convert("RGB")
    segs = section_segments(use_mesh, [0, 0, 1], [0, 0, 0], [0, 1])
    ox, oy = PHOTO_ORIGIN_PX
    px = np.empty_like(segs)
    px[..., 0] = ox + segs[..., 0] * PHOTO_PX_PER_MM
    px[..., 1] = oy - segs[..., 1] * PHOTO_PX_PER_MM
    fig, axes = plt.subplots(1, 2, figsize=(16, 9))
    for ax, show in zip(axes, (False, True)):
        ax.imshow(img)
        if show:
            ax.add_collection(LineCollection(px, colors="red", lw=1.2))
        ax.set_xlim(560, 1200)
        ax.set_ylim(1360, 760)
        ax.set_axis_off()
    axes[0].set_title("photo (tape: 1 in = 245 px)")
    axes[1].set_title("model outline (red) over the photo")
    fig.suptitle("pegboard-hook: model vs owner's photo", fontsize=14)
    fig.savefig(path, dpi=80, bbox_inches="tight")
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    RENDERS.mkdir(exist_ok=True)
    p = HookParams(**MEASURED)

    hook_use = build_hook(p)
    assert hook_use.is_valid and len(hook_use.solids()) == 1

    printed = print_pose(hook_use, p)
    export_step(printed, str(OUT / "pegboard-hook.step"))
    mesh = mk.cad_to_mesh(printed)
    info = mk.report(mesh)
    assert info["watertight"], "print mesh is not watertight"
    mesh.export(OUT / "pegboard-hook.stl")

    use_mesh = mk.cad_to_mesh(hook_use)
    board = pegboard(p)
    use_to_zup(use_mesh).export(RENDERS / "asm-hook.stl")
    use_to_zup(board).export(RENDERS / "ref-pegboard.stl")
    interference = use_mesh.intersection(board, engine="manifold")
    clash_mm3 = float(abs(interference.volume)) if len(interference.faces) else 0.0

    report = {
        "scale_status": "measured (wire caliper 5.53 mm; profile from tape-scaled photos, about +-1 mm)",
        "print": info,
        "print_orientation": "lying on its side, profile flat on the bed; 0.4 mm flat shaved off the bed side",
        "fit_on_quarter_inch_pegboard": {"board_thickness": BOARD_T, "hole_d": HOLE_D, "pitch": PITCH,
                                         "interference_mm3": round(clash_mm3, 2)},
        "params_mm": p.report_params(),
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"print": info, "derived": p.derived(), "board_interference_mm3": round(clash_mm3, 2)}, indent=2))

    render_sheet(mesh, str(RENDERS / "model.png"), title="pegboard-hook: print pose (lying on its side), mm",
                 labels=["printed hook"], sections_y=(0.0,), sections_x=(-20.0, 0.0, 20.0))
    photo_overlay(use_mesh, p, RENDERS / "photo-overlay.png")


if __name__ == "__main__":
    main()
