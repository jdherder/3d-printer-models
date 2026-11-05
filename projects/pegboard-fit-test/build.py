"""Reproducible build for the pegboard fit test.

    python projects/pegboard-fit-test/build.py        (a few seconds)

Built only from the shared interface in tools/pegboard.py, so it tests exactly the pegs every catalog part uses.
  -> output/pegboard-fit-test.step / .stl   4 mm plate, one hook peg + one pin 1 in apart, print pose (on its side)
  -> output/report.json                     checks, peg style, board fit
  -> renders/fit-test.png                   views + sections
  -> renders/asm-fit-test.stl, ref-pegboard.stl   hung on the board (world Z-up), for the viewer
"""

import json
import sys
from dataclasses import asdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / "tools")]

import meshkit as mk  # noqa: E402
import pegboard as pb  # noqa: E402
from build123d import export_step  # noqa: E402
from render import render_sheet  # noqa: E402

OUT = HERE / "output"
RENDERS = HERE / "renders"

BOARD = pb.DEFAULT_BOARD          # the owner's board (tools/pegboard.py)
STYLE = pb.PegStyle()
PLATE_T = 4.0
PLATE_Z = (-STYLE.r, 10.0)         # bottom edge flush with the pegs so it prints on its side without supports


def build():
    return pb.mount_plate(STYLE, cols=(0,), rows=(0, 1), thickness=PLATE_T, margin=8.0, z_range=PLATE_Z)


def main():
    OUT.mkdir(exist_ok=True)
    RENDERS.mkdir(exist_ok=True)
    assert not STYLE.check(BOARD), STYLE.check(BOARD)

    part = build()
    printed = pb.lay_on_side(part, STYLE)
    export_step(printed, str(OUT / "pegboard-fit-test.step"))
    mesh = mk.cad_to_mesh(printed)
    info = mk.report(mesh)
    assert info["watertight"], "fit test is not watertight"
    mesh.export(OUT / "pegboard-fit-test.stl")

    hung = mk.cad_to_mesh(part)
    board = pb.board_mesh(BOARD, rows=range(-1, 3), cols=range(-1, 2))
    clash = pb.interference_mm3(hung, pb.board_mesh(BOARD, rows=range(-1, 3), cols=range(-1, 2), clearance=pb.FIT_CLEARANCE))
    assert clash == 0.0, f"fit test comes within {pb.FIT_CLEARANCE} mm of the board ({clash} mm^3)"
    pb.to_zup(hung).export(RENDERS / "asm-fit-test.stl")
    pb.to_zup(board).export(RENDERS / "ref-pegboard.stl")

    report = {
        "scale_status": "real size (shared peg interface, sizes from the owner's steel hook)",
        "print": info,
        "print_orientation": "on its side, pegs flat on the bed, 0.4 mm flat on the bed side, no supports",
        "fit_on_board": {"board": BOARD.name, "hole_d": BOARD.hole_d, "thickness": BOARD.thickness,
                         "pitch": BOARD.pitch, "clearance_checked_per_side": pb.FIT_CLEARANCE,
                         "interference_mm3": clash},
        "params_mm": {**asdict(STYLE), "plate_thickness": PLATE_T, "pitch": pb.PITCH,
                      "hole_clearance_per_side": round((BOARD.hole_d - STYLE.d) / 2, 2),
                      "room_behind_board": round(STYLE.hook_gap - BOARD.thickness, 2)},
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"print": info, "fit_on_board": report["fit_on_board"]}, indent=2))

    render_sheet(mesh, str(RENDERS / "fit-test.png"), title="pegboard-fit-test: print pose (on its side), mm",
                 labels=["fit test"], sections_y=(0.0,), sections_x=(-8.0, 0.0))


if __name__ == "__main__":
    main()
