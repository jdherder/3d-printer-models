"""Reproducible build for the pegboard hook.

    python projects/pegboard-hook/build.py        (a few seconds)

model.py (build123d, parameters from the owner's photos + caliper)
  -> output/pegboard-hook.step        editable solid for Fusion (print pose)
  -> output/pegboard-hook.stl         print-ready mesh: lying on its side, 0.4 mm flat on the bed side
  -> output/report.json               dimensions, checks, parameters
  -> renders/model.png                shaded views + sections
  -> renders/photo-overlay.png        model outline drawn over the owner's photo (the fit check)
  -> output/pegboard-fit-test.stl/.step   small plate with one hook + one pin from the shared tools/pegboard.py interface
  -> renders/fit-test.png             its preview
  -> renders/asm-*.stl, ref-pegboard.stl   hung on a 1/4" pegboard (world Z-up), for the viewer
"""

import json
from dataclasses import asdict
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
from build123d import Location, export_step  # noqa: E402
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

BOARD = pb.BOARDS["quarter"]     # nominal; replace with the owner's measured board when known
STYLE = pb.PegStyle()             # shared peg geometry (its defaults come from this hook)
FIT_TEST_Z = (-STYLE.r, 10.0)     # fit-test plate: bottom edge flush with the pegs so it prints on its side without supports


def fit_test():
    """Shared-interface test piece: a 4 mm plate with one hook and one pin (1 in apart), built with tools/pegboard.py.
    Print it before any custom part to check the pegs on the real board."""
    return pb.mount_plate(STYLE, cols=(0,), rows=(0, 1), thickness=4.0, margin=8.0, z_range=FIT_TEST_Z)


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

    # ---- Fit-test piece from the shared interface (tools/pegboard.py) -------------------------------------
    assert not STYLE.check(BOARD), STYLE.check(BOARD)
    coupon = fit_test()
    coupon_print = pb.lay_on_side(coupon, STYLE)
    export_step(coupon_print, str(OUT / "pegboard-fit-test.step"))
    coupon_mesh = mk.cad_to_mesh(coupon_print)
    coupon_info = mk.report(coupon_mesh)
    assert coupon_info["watertight"], "fit test is not watertight"
    coupon_mesh.export(OUT / "pegboard-fit-test.stl")

    # ---- Hung on the board (board frame) -------------------------------------------------------------------
    hook_board = mk.cad_to_mesh(use_to_board(hook_use, p))
    coupon_board = mk.cad_to_mesh(coupon.moved(Location((0, 0, pb.PITCH))))     # next column over, for the viewer
    board = pb.board_mesh(BOARD, rows=range(-1, 3), cols=range(-1, 2))
    pb.to_zup(hook_board).export(RENDERS / "asm-hook.stl")
    pb.to_zup(coupon_board).export(RENDERS / "asm-fit-test.stl")
    pb.to_zup(board).export(RENDERS / "ref-pegboard.stl")
    fit = {"board": BOARD.name, "hole_d": BOARD.hole_d, "thickness": BOARD.thickness, "pitch": BOARD.pitch,
           "steel_hook_interference_mm3": pb.interference_mm3(hook_board, board),
           "fit_test_interference_mm3": pb.interference_mm3(coupon_board, board)}

    report = {
        "scale_status": "measured (wire caliper 5.53 mm; profile from tape-scaled photos, about +-1 mm)",
        "print": info,
        "fit_test_print": coupon_info,
        "print_orientation": "both lie on their side (pegs flat on the bed), 0.4 mm flat shaved off the bed side",
        "fit_on_board": fit,
        "peg_style_mm": asdict(STYLE),
        "params_mm": {**p.report_params(), "fit_test_plate_thickness": 4.0},
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"print": info, "fit_test": coupon_info, "fit": fit, "derived": p.derived()}, indent=2))

    render_sheet(mesh, str(RENDERS / "model.png"), title="pegboard-hook: print pose (lying on its side), mm",
                 labels=["printed hook"], sections_y=(0.0,), sections_x=(-20.0, 0.0, 20.0))
    render_sheet(coupon_mesh, str(RENDERS / "fit-test.png"), title="pegboard fit test: print pose (on its side), mm",
                 labels=["fit test"], sections_y=(0.0,), sections_x=(-8.0, 0.0))
    photo_overlay(mk.cad_to_mesh(hook_use), p, RENDERS / "photo-overlay.png")


if __name__ == "__main__":
    main()
