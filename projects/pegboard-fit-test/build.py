"""Reproducible build for the pegboard fit test.

    python projects/pegboard-fit-test/build.py        (a few seconds)

Built only from the shared interface in tools/pegboard.py, so it tests exactly the pegs every catalog part uses.
  -> output/pegboard-fit-test.step / .stl   4 mm plate, one hook peg + one pin 1 in apart, print pose (on its side)
  -> output/report.json                     checks, peg style, board fit
  -> renders/fit-test.png                   views + sections
  -> output/pegboard-peg-gauge.stl          strip of straight pins 6.0-6.4 mm, labelled, to pick PegStyle.d
                                            (STL only: a one-off test piece, and the engraved labels make its STEP ~24k lines)
  -> renders/peg-gauge.png
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
from build123d import Location, export_step  # noqa: E402
from render import render_sheet  # noqa: E402

OUT = HERE / "output"
RENDERS = HERE / "renders"

BOARD = pb.DEFAULT_BOARD          # the owner's board (tools/pegboard.py)
STYLE = pb.PegStyle()
PLATE_T = 4.0
PLATE_Z = (-STYLE.r, 10.0)         # bottom edge flush with the pegs so it prints on its side without supports


GAUGE_DS = (6.0, 6.1, 6.2, 6.3, 6.4)    # pin diameters to try (PegStyle.d is 6.1)
GAUGE_STEP = 15.0                          # off the 1 in grid on purpose, so each pin is tried in a hole on its own


def build():
    return pb.mount_plate(STYLE, cols=(0,), rows=(0, 1), thickness=PLATE_T, margin=8.0, z_range=PLATE_Z)


def build_gauge():
    """Peg gauge: a strip with one straight pin per diameter in GAUGE_DS, each labelled on the front face. Push each pin into a
    hole on its own and pick the snuggest one that still goes in by hand; that becomes PegStyle.d.
    Every pin's underside is level with the others, so each gets the same 0.4 mm bed flat."""
    from build123d import Box, Location, Plane, Text, extrude
    r_max = max(GAUGE_DS) / 2
    y0, y1 = -8.0, (len(GAUGE_DS) - 1) * GAUGE_STEP + 8.0
    z0, z1 = -STYLE.r, 12.0
    strip = Box(PLATE_T, y1 - y0, z1 - z0).locate(Location((PLATE_T / 2, (y0 + y1) / 2, (z0 + z1) / 2)))
    for i, d in enumerate(GAUGE_DS):
        y, zc = i * GAUGE_STEP, d / 2 - STYLE.r       # same underside as a PegStyle peg at z = 0
        pin = pb.pin_peg(pb.PegStyle(d=d), y=y, z=zc)
        label = Plane(origin=(PLATE_T, y, 6.5), x_dir=(0, 0, -1), z_dir=(1, 0, 0)) * Text(f"{d:.1f}", font_size=4.5)
        strip = strip + pin - extrude(label, amount=0.6, dir=(-1, 0, 0))
    assert r_max < BOARD.hole_d / 2 + 0.2
    return strip


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
        "scale_status": "real size (shared peg interface; sizes from the owner's steel hook, diameter from test prints)",
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

    gauge_board = build_gauge()
    pb.to_zup(mk.cad_to_mesh(gauge_board.moved(Location((0, 0, 2.3 * pb.PITCH))))).export(RENDERS / "asm-peg-gauge.stl")  # beside the board
    gauge = pb.lay_on_side(gauge_board, STYLE)
    (OUT / "pegboard-peg-gauge.step").unlink(missing_ok=True)       # no STEP for the gauge (see docstring)
    gauge_mesh = mk.cad_to_mesh(gauge)
    gauge_info = mk.report(gauge_mesh)
    assert gauge_info["watertight"], "peg gauge is not watertight"
    gauge_mesh.export(OUT / "pegboard-peg-gauge.stl")
    report["peg_gauge"] = {**gauge_info, "pin_diameters_mm": list(GAUGE_DS)}
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"peg_gauge": report["peg_gauge"]}, indent=2))
    render_sheet(gauge_mesh, str(RENDERS / "peg-gauge.png"), title="pegboard peg gauge: print pose (on its side), mm",
                 labels=["peg gauge"], sections_y=(0.0,), sections_x=(-6.0,))


if __name__ == "__main__":
    main()
