"""Reproducible build for the pegboard cutting-mat holder (concept v0.1).

    python projects/pegboard-mat-holder/build.py        (about a minute)

A thin strip on the pegboard with two slots across its top. The owner's two ZenBeya self-healing mats (A3 450 x 300,
A4 300 x 220, ~3 mm thick) stand in the slots, landscape, and lean back: the A3 (back slot) against the board, the A4
(front slot) against the A3, like the product photo.
  -> output/pegboard-mat-holder.step / .stl   print pose (standing on its bottom edge, slots open upward)
  -> output/report.json                       checks, params, mat lean angles
  -> renders/mat-holder.png                   views + sections
  -> renders/asm-*.stl, ref-*.stl             hung on the board with both mats in it (world Z-up), for the viewer

Board frame (tools/pegboard.py): x out of the board, y up, z across. One piece: back plate with 2 shared hooks (row 1)
and 2 pins (row 0), 7 holes apart, and the slot block on its front, as low as the pins.

Thinness vs lean: a mat leans back until its top edge touches the board, so its lean is set by how far its bottom sits
from the board: sin(lean) = distance / mat height. Each extra degree of A3 lean costs ~5 mm of holder depth
(`A3_GAP`). The slots are tilted to each mat's natural lean so the mat sits flat against the slot's back wall.
"""

import json
import math
import sys
from dataclasses import asdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / "tools")]

import meshkit as mk  # noqa: E402
import numpy as np  # noqa: E402
import pegboard as pb  # noqa: E402
import trimesh  # noqa: E402
from build123d import Box, Location, Polygon, export_step, extrude, Plane, BuildPart, BuildSketch  # noqa: E402
from render import render_sheet  # noqa: E402

OUT = HERE / "output"
RENDERS = HERE / "renders"
NAME = "pegboard-mat-holder"

BOARD = pb.DEFAULT_BOARD
STYLE = pb.PegStyle()

# Mats (thickness: owner's calipers; sizes from the listing). Landscape: the long side across the board.
MAT_T = 3.0                    # thickest point (owner's calipers 2026-11-11: 2.5-3.0 mm across the mat)
MATS = {"A3": {"w": 450.0, "h": 300.0}, "A4": {"w": 300.0, "h": 220.0}}

# Mount: hooks in row 1, pins in row 0, in columns 0 and 7 (178 mm apart, so the long strip can't rock side to side).
ROWS = (0, 1)
COLS = (0, 7)
PLATE_T = 3.0                  # back plate (x)
SIDE_MARGIN = 8.0              # plate past the outer pegs (z)
BOTTOM = -STYLE.r              # part's bottom (y), flush with the pins' undersides: it prints standing on this edge

# Slot block, on the plate's front
FLOOR_T = 2.0                  # under the slots
SLOT_DEPTH = 14.0              # mat edge sunk this deep (slot floor to block top)
SLOT_CLEAR = 0.5               # slot = thickest mat + this: 3.5 mm. Printed slots come out a bit narrow, so 0.5 still slides;
                               # a 2.5 mm spot has 1 mm of play, which the lean takes up
A3_GAP = 2.0                   # wall between the plate and the A3 slot (sets the A3's lean, see top docstring)
RIB_T = 2.4                    # wall between the two slots
FRONT_T = 2.4                  # front wall
MOUTH_CHAMFER = 1.5            # lead-in on the front edge of each slot mouth

SLOT_W = MAT_T + SLOT_CLEAR
FLOOR_Y = BOTTOM + FLOOR_T
TOP_Y = FLOOR_Y + SLOT_DEPTH


def lean_a3():
    """A3 leans back until its top back corner touches the board (x = 0)."""
    b = PLATE_T + A3_GAP
    return b, math.asin(b / MATS["A3"]["h"])


def lean_a4(b1, a1, b2):
    """A4 (back face at x = b2 on the floor) leans back until its top back corner touches the A3's front face."""
    h = MATS["A4"]["h"]
    front = lambda y: b1 + MAT_T / math.cos(a1) - y * math.tan(a1)    # A3 front face, y above the floor   # noqa: E731
    f = lambda a: (b2 - h * math.sin(a)) - front(h * math.cos(a))     # > 0: not touching yet           # noqa: E731
    lo, hi = 0.0, math.radians(30)
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) > 0 else (lo, mid)
    return hi


def slot_cutter(b, a):
    """(x, y) polygon of a slot whose back wall passes through (b, FLOOR_Y) leaning back at angle a, with a lead-in
    chamfer on its front mouth edge. Extends above the block so the cut is clean."""
    u = np.array([-math.sin(a), math.cos(a)])           # up the mat
    n = np.array([math.cos(a), math.sin(a)])            # out of its back face, toward the front
    pb_ = np.array([b, FLOOR_Y])
    pf = pb_ + SLOT_W * n
    reach = lambda p: (TOP_Y - p[1]) / u[1]             # noqa: E731  distance along u from p to the block top
    tf, tb = reach(pf), reach(pb_)
    above = 5.0
    pts = [pb_, pf, pf + (tf - MOUTH_CHAMFER) * u, pf + tf * u + [MOUTH_CHAMFER, 0], pf + tf * u + [MOUTH_CHAMFER, above],
           pb_ + tb * u + [0, above], pb_ + (tb + above / u[1]) * u]
    return [tuple(map(float, p)) for p in pts]


def geometry():
    b1, a1 = lean_a3()
    b2 = b1 + SLOT_W / math.cos(a1) + RIB_T             # A4 slot's back wall on the floor
    a2 = lean_a4(b1, a1, b2)
    front_x = b2 + SLOT_W / math.cos(a2) + FRONT_T
    return b1, a1, b2, a2, front_x


def build():
    b1, a1, b2, a2, front_x = geometry()
    z0, z1 = min(COLS) * pb.PITCH - SIDE_MARGIN, max(COLS) * pb.PITCH + SIDE_MARGIN
    plate = pb.mount_plate(STYLE, cols=COLS, rows=ROWS, thickness=PLATE_T, margin=-BOTTOM, z_range=(z0, z1))
    with BuildPart() as bp:
        with BuildSketch(Plane.XY.offset(z0)):
            Polygon((PLATE_T - 0.5, BOTTOM), (front_x, BOTTOM), (front_x, TOP_Y), (PLATE_T - 0.5, TOP_Y), align=None)
        extrude(amount=z1 - z0)
    block = bp.part
    for b, a in ((b1, a1), (b2, a2)):
        with BuildPart() as cp:
            with BuildSketch(Plane.XY.offset(z0 - 1)):
                Polygon(*slot_cutter(b, a), align=None)
            extrude(amount=z1 - z0 + 2)
        block = block - cp.part
    return plate + block


def mat_ref(name, b, a, zc):
    """A mat standing in its slot (back face on the slot's back wall), board frame."""
    m = MATS[name]
    box = trimesh.creation.box(extents=[MAT_T, m["h"], m["w"]])
    box.apply_translation([MAT_T / 2, m["h"] / 2, 0])               # back-bottom edge on the origin
    box.apply_transform(trimesh.transformations.rotation_matrix(a, [0, 0, 1]))   # lean back (top toward -x)
    box.apply_translation([b, FLOOR_Y + 0.05, zc])
    return box


def print_pose(part):
    """Stand it on its bottom edge: board y -> bed Z (slots open up), board z -> bed X (the long way), board x -> bed Y.
    Shave 0.4 mm so the pins sit on a flat first layer. Supports only under the two hooks."""
    from build123d import Rotation
    big = 1000.0
    part = part - Box(big, big, big).locate(Location((0, BOTTOM + 0.4 - big / 2, 0)))
    posed = part.moved(Rotation(90, 0, 0)).moved(Rotation(0, 0, 90))
    bb = posed.bounding_box()
    return posed.moved(Location((-(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z)))


def main():
    OUT.mkdir(exist_ok=True)
    RENDERS.mkdir(exist_ok=True)
    assert not STYLE.check(BOARD), STYLE.check(BOARD)

    part = build()
    printed = print_pose(part)
    export_step(printed, str(OUT / f"{NAME}.step"))
    mesh = mk.cad_to_mesh(printed)
    info = mk.report(mesh)
    assert info["watertight"], "mat holder is not watertight"
    mesh.export(OUT / f"{NAME}.stl")

    hung = mk.cad_to_mesh(part)
    hook_y = max(ROWS) * pb.PITCH
    clash = pb.interference_mm3(hung, pb.board_mesh(BOARD, rows=range(-1, 3), cols=range(-1, max(COLS) + 2), clearance=pb.FIT_CLEARANCE))
    rock = pb.rock_in(hung, BOARD, hook_y=hook_y)
    assert rock["ok"], f"mat holder won't rock onto the board: {rock}"

    b1, a1, b2, a2, front_x = geometry()
    zc = (min(COLS) + max(COLS)) / 2 * pb.PITCH
    a3, a4 = mat_ref("A3", b1, a1, zc), mat_ref("A4", b2, a2, zc)
    board = pb.board_mesh(BOARD, rows=range(-1, 14), cols=range(-6, 14))
    for nm, m in (("A3", a3), ("A4", a4)):
        assert pb.interference_mm3(m, hung) < 0.5, f"{nm} mat hits the holder"
    assert pb.interference_mm3(a3, board) < 0.5 and pb.interference_mm3(a4, a3) < 0.5
    pb.to_zup(hung).export(RENDERS / "asm-mat-holder.stl")
    pb.to_zup(trimesh.util.concatenate([a3, a4])).export(RENDERS / "ref-mats.stl")
    pb.to_zup(board).export(RENDERS / "ref-pegboard.stl")

    ext = hung.bounds[1] - hung.bounds[0]
    report = {
        "scale_status": "real size (shared peg interface; mat sizes from the listing, thickness 2.5-3.0 mm by the owner's calipers)",
        "print": info,
        "print_orientation": "standing on its bottom edge, slots open up, pins on the bed (0.4 mm flat); supports under the 2 hooks only",
        "fit_on_board": {"board": BOARD.name, "clearance_checked_per_side": pb.FIT_CLEARANCE,
                         "flush_overlap_mm3_info_only": clash, "rock_in": {**rock, "give_mm": pb.ROCK_IN_GIVE},
                         "holes_used": f"2 hooks (row {max(ROWS)}) + 2 pins (row {min(ROWS)}), columns {COLS[0]} and {COLS[1]} ({(COLS[1]-COLS[0])} holes apart)"},
        "mats": {"A3_lean_deg": round(math.degrees(a1), 2), "A4_lean_deg": round(math.degrees(a2), 2),
                 "A3_top_above_hook_hole_mm": round(FLOOR_Y + MATS['A3']['h'] * math.cos(a1) - hook_y, 1),
                 "A3_overhang_each_side_mm": round((MATS["A3"]["w"] - ext[2]) / 2, 1),
                 "A4_overhang_each_side_mm": round((MATS["A4"]["w"] - ext[2]) / 2, 1)},
        "params_mm": {**asdict(STYLE), "holder_depth": round(front_x, 1), "holder_width": round(float(ext[2]), 1),
                      "holder_height": round(float(ext[1]), 1), "block_height": round(TOP_Y - BOTTOM, 1),
                      "plate_thickness": PLATE_T, "slot_width": SLOT_W, "slot_depth": SLOT_DEPTH, "mat_thickness": MAT_T,
                      "hook_spacing": (max(COLS) - min(COLS)) * pb.PITCH, "a3_gap": A3_GAP, "rib": RIB_T, "front_wall": FRONT_T},
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("print", "fit_on_board", "mats")}, indent=2))
    print(json.dumps({k: report["params_mm"][k] for k in ("holder_depth", "holder_width", "holder_height", "block_height")}))

    render_sheet(mesh, str(RENDERS / "mat-holder.png"), title=f"{NAME}: print pose (standing on its bottom edge), mm",
                 labels=["mat holder"], sections_y=(0.0,), sections_x=(20.0,))


if __name__ == "__main__":
    main()
