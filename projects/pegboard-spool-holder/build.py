"""Reproducible build for the pegboard spool holder.

    python projects/pegboard-spool-holder/build.py        (under a minute)

Holds the A1's active spool "sideways" on the pegboard behind the printer: the spool hangs on a straight arm that sticks
out of the board, with the spool's face parallel to the board (like a paper-towel holder), instead of on the printer.
  -> output/pegboard-spool-holder.step / .stl   print pose (on its side; supports only under the 2nd peg column)
  -> output/report.json                         checks, params, board fit, spool fit
  -> renders/spool-holder.png                   views + sections
  -> renders/asm-*.stl, ref-*.stl               hung on the board with a 1 kg spool on it (world Z-up), for the viewer

Board frame (tools/pegboard.py): x out of the board, y up, z across. Two columns of pegs, 1 in apart: two hooks side by
side in one row (they share the rocking axis, so both go in together) and four pins, 2 and 3 holes below. It prints on its side,
so the layers run along the pegs and the arm (the strong way for both). Column 0's pegs and the arm sit on the bed; column 1's
pegs are 25.4 mm up and need supports under them (slicer: tree supports, on build plate only).
"""

import json
import sys
from dataclasses import asdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / "tools")]

import meshkit as mk  # noqa: E402
import pegboard as pb  # noqa: E402
import trimesh  # noqa: E402
from build123d import Axis, Box, Location, export_step  # noqa: E402
from render import render_sheet  # noqa: E402

OUT = HERE / "output"
RENDERS = HERE / "renders"

BOARD = pb.DEFAULT_BOARD
STYLE = pb.PegStyle()

# Mount: hooks in hole row 3, pins in rows 0 and 1, in two adjacent columns (two hooks share the load and stop the part
# twisting). The 3 in hook-to-bottom-pin span is the lever against the spool's pull-out moment; the second pin row
# spreads the bearing load over more holes and takes up slop.
ROWS = (0, 3)                 # (bottom pin row, hook row)
EXTRA_PIN_ROWS = (1,)         # more pins between them (row 2 would sit only 1 in under the hooks and add little)
COLS = (0, 1)
PLATE_T = 5.0
PLATE_MARGIN = 8.0            # plate below the pin

# Arm (the spool's hub rides on its top). Width is across the board (z), which is the print height. It spans both peg
# columns so it rests on the bed and sits centred between the hooks.
ARM_W = (max(COLS) - min(COLS)) * pb.PITCH + 2 * pb.PegStyle().r    # z, 31.5
ARM_H = 22.0                  # y (deep for stiffness; the spool only touches the top)
ARM_TOP = max(ROWS) * pb.PITCH - 4.8    # y of the arm's top, just under the hook row
ARM_REACH = 82.0              # usable length in front of the plate (spools up to ~80 mm wide)
CROWN_R = 16.0                # rounded top: an arc tighter than any spool bore (>= 25 mm radius), so the spool rides on
                              # one smooth line along the top. It spans +-45 deg and blends into 45 deg chamfers down
                              # the sides, so the bed side still prints as a 45 deg overhang with no support
LIP_H = 8.0                   # end stop rising above the arm top, keeps the spool from walking off
LIP_T = 6.0                   # lip thickness along the arm
ROOT_FILLET = 4.0             # where the arm meets the plate

# Reference spools (for fit checks and the viewer). Spool bores are 52-57 mm on nearly every 1 kg spool.
SPOOL = {"od": 200.0, "width": 68.0, "bore": 53.0}     # Bambu-style 1 kg (the owner's Overture is ~200 x 68 x 55)
MIN_BORE = 50.0               # the smallest bore the arm + lip should pass through
MAX_WIDTH = ARM_REACH         # widest spool that fits between the plate and the lip

Z0 = -STYLE.r                 # part's bed-side face, flush with the pegs' underside (prints on its side, no supports)


def arm_profile_pts(top):
    """Key points (y, z) of the arm's cross-section top: side, chamfer/arc tangent point, crown, mirrored."""
    import math
    zc, hw = Z0 + ARM_W / 2, ARM_W / 2
    a = CROWN_R * math.sin(math.pi / 4)                     # arc half-chord at the +-45 deg tangent points
    y_t = top - CROWN_R * (1 - math.cos(math.pi / 4))       # y of the tangent points
    y_s = y_t - (hw - a)                                    # where the 45 deg chamfer meets the side
    return zc, a, y_t, y_s


def arm_section(top, height, xa, xb):
    """The arm's cross-section (crowned top, 45 deg chamfers, flat sides and bottom) extruded along x from xa to xb."""
    from build123d import BuildLine, BuildPart, BuildSketch, Plane, Polyline, ThreePointArc, extrude, make_face
    zc, a, y_t, y_s = arm_profile_pts(top)
    yb, z1 = top - height, Z0 + ARM_W
    with BuildPart() as bp:
        with BuildSketch(Plane.YZ.offset(xa)):              # sketch local (u, v) = world (y, z)
            with BuildLine():
                Polyline((y_t, zc + a), (y_s, z1), (yb, z1), (yb, Z0), (y_s, Z0), (y_t, zc - a))
                ThreePointArc((y_t, zc - a), (top, zc), (y_t, zc + a))
            make_face()
        extrude(amount=xb - xa)
    return bp.part


def build():
    from build123d import fillet
    plate = pb.mount_plate(STYLE, cols=COLS, rows=ROWS, thickness=PLATE_T, margin=PLATE_MARGIN, z_range=(Z0, Z0 + ARM_W))
    for row in EXTRA_PIN_ROWS:
        for col in COLS:
            plate = plate + pb.pin_peg(STYLE, row * pb.PITCH, col * pb.PITCH)
    x0, x1 = PLATE_T, PLATE_T + ARM_REACH + LIP_T
    arm = arm_section(ARM_TOP, ARM_H, x0 - 1, x1)
    lip = arm_section(ARM_TOP + LIP_H, ARM_H + LIP_H, x1 - LIP_T, x1)
    body = arm + lip
    part = plate + body
    root = [e for e in part.edges().filter_by(Axis.Z)
            if abs(e.center().X - PLATE_T) < 0.01 and abs(e.center().Y - (ARM_TOP - ARM_H)) < 0.01]
    if root:
        part = fillet(root, ROOT_FILLET)
    return part


def spool_ref(spool):
    """A plain spool (two flanges + hub tube) resting on the arm, against the plate, in the board frame."""
    bore_r, od_r, w = spool["bore"] / 2, spool["od"] / 2, spool["width"]
    yc = ARM_TOP - bore_r                                     # bore resting on the crown's top line
    zc = Z0 + ARM_W / 2
    parts = []
    for x, t, ro in ((PLATE_T + 0.5, 3.0, od_r), (PLATE_T + 0.5 + w - 3.0, 3.0, od_r), (PLATE_T + 0.5, w, bore_r + 8)):
        outer = trimesh.creation.cylinder(radius=ro, height=t, sections=96)
        inner = trimesh.creation.cylinder(radius=bore_r, height=t + 2, sections=96)
        ring = outer.difference(inner, engine="manifold")
        ring.apply_transform(trimesh.transformations.rotation_matrix(1.5707963, [0, 1, 0]))
        ring.apply_translation([x + t / 2, yc, zc])
        parts.append(ring)
    return trimesh.util.concatenate(parts), yc


def main():
    OUT.mkdir(exist_ok=True)
    RENDERS.mkdir(exist_ok=True)
    assert not STYLE.check(BOARD), STYLE.check(BOARD)

    part = build()
    printed = pb.lay_on_side(part, STYLE)
    export_step(printed, str(OUT / "pegboard-spool-holder.step"))
    mesh = mk.cad_to_mesh(printed)
    info = mk.report(mesh)
    assert info["watertight"], "spool holder is not watertight"
    mesh.export(OUT / "pegboard-spool-holder.stl")

    hung = mk.cad_to_mesh(part)
    rows, cols = range(-4, 5), range(-4, 5)
    board = pb.board_mesh(BOARD, rows=rows, cols=cols)
    # The sloped hooks overlap a little in the strict flush check (like the steel hook): information only.
    clash = pb.interference_mm3(hung, pb.board_mesh(BOARD, rows=range(-1, max(ROWS) + 2), cols=range(-1, 2), clearance=pb.FIT_CLEARANCE))
    rock = pb.rock_in(hung, BOARD, hook_y=max(ROWS) * pb.PITCH)
    assert rock["ok"], f"spool holder won't rock onto the board: {rock}"

    # Spool checks: the arm + lip (cross-section) must pass through the smallest bore, and the reference spool must clear
    # the arm (resting on it) and the board.
    xsec_h = ARM_H + LIP_H
    passes = (ARM_W ** 2 + xsec_h ** 2) ** 0.5 < MIN_BORE        # lip's bounding box diagonal, conservative
    assert passes, "arm + lip won't pass through a 50 mm spool bore"
    spool, spool_y = spool_ref(SPOOL)
    spool_vs_part = pb.interference_mm3(hung, spool)
    assert spool_vs_part < 1.0, f"reference spool overlaps the arm ({spool_vs_part} mm^3)"
    assert pb.interference_mm3(spool, board) == 0.0, "reference spool hits the board"

    pb.to_zup(hung).export(RENDERS / "asm-spool-holder.stl")
    pb.to_zup(spool).export(RENDERS / "ref-spool.stl")
    pb.to_zup(board).export(RENDERS / "ref-pegboard.stl")

    peg_top_y = max(ROWS) * pb.PITCH
    report = {
        "scale_status": "real size (shared peg interface; spool sizes from common 1 kg spools)",
        "print": info,
        "print_orientation": "on its side, column 0 pegs and the arm flat on the bed (0.4 mm flat); supports under column 1 pegs only",
        "fit_on_board": {"board": BOARD.name, "hole_d": BOARD.hole_d, "thickness": BOARD.thickness,
                         "pitch": BOARD.pitch, "clearance_checked_per_side": pb.FIT_CLEARANCE,
                         "flush_overlap_mm3_info_only": clash, "rock_in": {**rock, "give_mm": pb.ROCK_IN_GIVE}, "holes_used": "two adjacent columns: 2 hooks side by side, 4 pins 2 and 3 holes (2 and 3 in) below"},
        "spool_fit": {"reference_spool": SPOOL, "min_bore_mm": MIN_BORE, "max_spool_width_mm": MAX_WIDTH,
                      "arm_plus_lip_passes_min_bore": passes,
                      "spool_centre_below_hook_hole_mm": round(peg_top_y - spool_y, 1),
                      "spool_centre_out_from_board_mm": round(PLATE_T + 0.5 + SPOOL["width"] / 2, 1),
                      "spool_bottom_below_hook_hole_mm": round(peg_top_y - spool_y + SPOOL["od"] / 2, 1),
                      "spool_top_above_hook_hole_mm": round(spool_y + SPOOL["od"] / 2 - peg_top_y, 1),
                      "spool_front_from_board_mm": round(PLATE_T + 0.5 + SPOOL["width"], 1)},
        "params_mm": {**asdict(STYLE), "plate_thickness": PLATE_T, "pitch": pb.PITCH, "hook_to_pin": (max(ROWS) - min(ROWS)) * pb.PITCH, "hook_spacing": (max(COLS) - min(COLS)) * pb.PITCH,
                      "pin_rows_below_hooks": [max(ROWS) - r for r in sorted((min(ROWS), *EXTRA_PIN_ROWS))],
                      "arm_width": ARM_W, "arm_height": ARM_H, "arm_crown_radius": CROWN_R, "arm_reach": ARM_REACH,
                      "lip_height": LIP_H, "lip_thickness": LIP_T,
                      "arm_tip_from_board": PLATE_T + ARM_REACH + LIP_T,
                      "hole_clearance_per_side": round((BOARD.hole_d - STYLE.d) / 2, 2),
                      "room_behind_board": round(STYLE.hook_gap - BOARD.thickness, 2)},
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("print", "fit_on_board", "spool_fit")}, indent=2))

    render_sheet(mesh, str(RENDERS / "spool-holder.png"), title="pegboard-spool-holder: print pose (on its side), mm",
                 labels=["spool holder"], sections_y=(0.0,), sections_x=(20.0,))


if __name__ == "__main__":
    main()
