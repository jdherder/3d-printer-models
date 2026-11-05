"""Reproducible build for the pegboard hook.

    python projects/pegboard-hook/build.py        (a few seconds)

model.py (build123d, parameters from the owner's photos + caliper)
  -> output/pegboard-hook.step        editable solid for Fusion (print pose)
  -> output/pegboard-hook.stl         print-ready mesh: lying on its side, 0.4 mm flat on the bed side
  -> output/report.json               dimensions, checks, parameters
  -> renders/model.png                shaded views + sections
  -> renders/photo-overlay.png        model outline drawn over the owner's photo (the fit check)
  -> renders/asm-hook.stl, ref-pegboard.stl   hung on a 1/4" pegboard (shared board frame, world Z-up), for the viewer
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
import pegboard as pb  # noqa: E402
import numpy as np  # noqa: E402
from build123d import export_step  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from model import HookParams, build_hook, print_pose, use_to_board  # noqa: E402
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

BOARD = pb.DEFAULT_BOARD          # the owner's board (tools/pegboard.py)


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

    # ---- The steel hook replica --------------------------------------------------------------------------
    hook_use = build_hook(p)
    assert hook_use.is_valid and len(hook_use.solids()) == 1
    printed = print_pose(hook_use, p)
    export_step(printed, str(OUT / "pegboard-hook.step"))
    mesh = mk.cad_to_mesh(printed)
    info = mk.report(mesh)
    assert info["watertight"], "print mesh is not watertight"
    mesh.export(OUT / "pegboard-hook.stl")

    # ---- Hung on the board (board frame) -------------------------------------------------------------------
    hook_board = mk.cad_to_mesh(use_to_board(hook_use, p))
    board = pb.board_mesh(BOARD, rows=range(-1, 3), cols=range(-1, 2))
    pb.to_zup(hook_board).export(RENDERS / "asm-hook.stl")
    pb.to_zup(board).export(RENDERS / "ref-pegboard.stl")
    fit = {"board": BOARD.name, "hole_d": BOARD.hole_d, "thickness": BOARD.thickness, "pitch": BOARD.pitch,
           "clearance_checked_per_side": pb.FIT_CLEARANCE,
           "interference_mm3": pb.interference_mm3(
               hook_board, pb.board_mesh(BOARD, rows=range(-1, 3), cols=range(-1, 2), clearance=pb.FIT_CLEARANCE))}
    assert fit["interference_mm3"] == 0.0, f"hook comes within {pb.FIT_CLEARANCE} mm of the board: {fit}"

    report = {
        "scale_status": "measured (wire caliper 5.53 mm; profile from tape-scaled photos, about +-1 mm)",
        "print": info,
        "print_orientation": "lying on its side, profile flat on the bed; 0.4 mm flat shaved off the bed side",
        "fit_on_board": fit,
        "params_mm": p.report_params(),
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"print": info, "fit": fit, "derived": p.derived()}, indent=2))

    render_sheet(mesh, str(RENDERS / "model.png"), title="pegboard-hook: print pose (lying on its side), mm",
                 labels=["printed hook"], sections_y=(0.0,), sections_x=(-20.0, 0.0, 20.0))
    photo_overlay(mk.cad_to_mesh(hook_use), p, RENDERS / "photo-overlay.png")


if __name__ == "__main__":
    main()
