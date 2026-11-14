"""Reproducible build for the pegboard screwdriver holder (concept v0.1).

    python projects/pegboard-screwdriver-holder/build.py        (about a minute)

Holds the owner's 6 Ryobi screwdrivers upright on the pegboard so they can't tip. The current steel holder has one wire
ring per driver: the shaft sits loosely in it and the handle can lean any way. This holder supports each driver at two
heights instead:
  1. a CUP in the top shelf: the handle's yellow bolster drops into a close-fitting pocket with a 45 degree conical
     floor, so the handle self-centres and its sides are held, and
  2. a GUIDE HOLE in a bottom shelf ~50 mm lower: the shaft passes through it, so the driver can only lean a few degrees.
Drop each driver in from above, tip first. The holes are sized for the tip (a slotted blade is wider than its shaft).

  -> output/pegboard-screwdriver-holder.step / .stl   print pose (standing on its bottom shelf, as it hangs)
  -> output/report.json                               checks, params, tilt limits
  -> renders/screwdriver-holder.png                   views + sections
  -> renders/asm-*.stl, ref-*.stl                     hung on the board with the drivers in it (world Z-up), for the viewer

Board frame (tools/pegboard.py): x out of the board, y up, z across. One piece: back plate with 2 shared hooks (row 1)
and 2 pins (row -1), a top shelf with the cups, a bottom shelf with the guide holes, and ribs between the stations.
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
from build123d import Box, Cone, Cylinder, Location, Rotation, export_step  # noqa: E402
from render import render_sheet  # noqa: E402

OUT = HERE / "output"
RENDERS = HERE / "renders"
NAME = "pegboard-screwdriver-holder"

BOARD = pb.DEFAULT_BOARD
STYLE = pb.PegStyle()

# The drivers, left to right as they hang now. Only shaft 5.03 / 6.43 and the big slotted blade 9.58 are measured
# (owner's calipers, 2026-11-14). Everything marked est is read off the photos and MUST be measured before printing:
#   grip = widest part of the handle (sets the spacing), bolster = widest part of the yellow collar at the handle's
#   bottom (sets the cup), tip = width of a slotted blade (sets the holes; Phillips tips are narrower than the shaft).
TOOLS = [  # name, grip, bolster, shaft, tip, handle_len, shaft_len
    ("slotted, small",   32.0, 30.0, 5.03, 5.0, 100.0, 100.0),   # shaft measured
    ("slotted, small 2", 32.0, 30.0, 5.0,  5.0, 100.0, 100.0),   # est
    ("slotted, medium",  32.0, 30.0, 6.0,  6.5, 100.0, 100.0),   # est
    ("slotted, large",   35.0, 33.0, 6.43, 9.58, 110.0, 125.0),  # shaft + blade measured
    ("Phillips #1",      32.0, 30.0, 5.0,  5.0, 100.0, 100.0),   # est
    ("Phillips #2",      35.0, 33.0, 6.43, 6.43, 110.0, 125.0),  # est
]

GRIP_GAP = 4.0          # air between neighbouring handles (z)
CUP_CLEAR = 0.75        # cup radius over the bolster radius (1.5 mm on the diameter)
HOLE_CLEAR = 0.75       # hole radius over max(shaft, tip) / 2
CUP_WALL = 7.0          # straight wall of the cup above its conical floor: how much of the bolster's side is held
CUP_LEAD = 1.5          # 45 deg lead-in chamfer at the cup's mouth
CONE_DEG = 45.0         # cup floor cone, from horizontal (prints without supports)

ROWS = (-1, 1)          # pins in row -1, hooks in row 1: 2 holes apart, so the guide shelf sits 50 mm below the cups
PLATE_T = 3.0           # back plate (x)
BACK_WALL = 2.0         # plate to the back of the biggest cup
FRONT_WALL = 3.0        # front of the biggest cup to the shelf's front face
END_WALL = 3.0          # outer cup to the holder's end
RIB_T = 2.4             # ribs between stations, from the bottom shelf to the top shelf
BOTTOM = min(ROWS) * pb.PITCH - STYLE.r   # holder's bottom (y), flush with the pins' undersides: it prints standing on this
GUIDE_T = 3.4           # bottom shelf thickness (2.6 left after the 0.4 mm print flat)
TOP_Y = 31.0            # top shelf's top face (y): 5.6 mm above the hook hole, so it still rocks on
SHELF_UNDER = 3.0       # solid below the bottom of the cup's cone


def r_hole(t):
    return max(t[3], t[4]) / 2 + HOLE_CLEAR


def r_cup(t):
    return t[2] / 2 + CUP_CLEAR


def layout():
    """z centres of the stations, holder z range, and the 2 peg columns (as far apart as the holder allows)."""
    zs = [0.0]
    for a, b in zip(TOOLS, TOOLS[1:]):
        zs.append(zs[-1] + (a[1] + b[1]) / 2 + GRIP_GAP)
    z0 = zs[0] - r_cup(TOOLS[0]) - END_WALL
    z1 = zs[-1] + r_cup(TOOLS[-1]) + END_WALL
    n = int((z1 - z0 - 2 * 8.0) // pb.PITCH)                    # columns 0..n, at least 8 mm in from each end
    shift = n * pb.PITCH / 2 - (z0 + z1) / 2
    return [z + shift for z in zs], (z0 + shift, z1 + shift), (0, n)


def x_centre():
    return PLATE_T + BACK_WALL + max(r_cup(t) for t in TOOLS)


def cone_h(t):
    return (r_cup(t) - r_hole(t)) * math.tan(math.radians(CONE_DEG))


def shelf_bottom():
    return TOP_Y - CUP_WALL - max(cone_h(t) for t in TOOLS) - SHELF_UNDER


def box(x0, x1, y0, y1, z0, z1):
    return Box(x1 - x0, y1 - y0, z1 - z0).locate(Location(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)))


def vcyl(r, y0, y1, x, z):
    return Cylinder(r, y1 - y0).moved(Rotation(-90, 0, 0)).moved(Location((x, (y0 + y1) / 2, z)))


def vcone(r0, r1, y0, y1, x, z):
    """Cone along +y: radius r0 at y0, r1 at y1."""
    return Cone(r0, r1, y1 - y0).moved(Rotation(-90, 0, 0)).moved(Location((x, (y0 + y1) / 2, z)))


def build():
    zs, (z0, z1), cols = layout()
    xc = x_centre()
    front = xc + max(r_cup(t) for t in TOOLS) + FRONT_WALL
    sb = shelf_bottom()
    plate = pb.mount_plate(STYLE, cols=cols, rows=ROWS, thickness=PLATE_T, margin=-BOTTOM, z_range=(z0, z1))
    body = box(PLATE_T - 0.5, front, sb, TOP_Y, z0, z1)                       # top shelf
    body += box(PLATE_T - 0.5, front, BOTTOM, BOTTOM + GUIDE_T, z0, z1)       # bottom shelf
    walls = [z0 + RIB_T / 2] + [(a + b) / 2 for a, b in zip(zs, zs[1:])] + [z1 - RIB_T / 2]
    for zw in walls:
        body += box(PLATE_T - 0.5, front, BOTTOM, TOP_Y, zw - RIB_T / 2, zw + RIB_T / 2)
    for t, z in zip(TOOLS, zs):
        rc, rh = r_cup(t), r_hole(t)
        y_cone = TOP_Y - CUP_WALL
        body -= vcyl(rc, y_cone, TOP_Y + 1, xc, z)
        body -= vcone(rc, rc + CUP_LEAD + 1, TOP_Y - CUP_LEAD, TOP_Y + 1, xc, z)          # lead-in
        body -= vcone(rh, rc, y_cone - cone_h(t), y_cone, xc, z)
        body -= vcyl(rh, BOTTOM - 1, y_cone, xc, z)                             # through both shelves
    return plate + body


def driver_ref(t, z):
    """Rough screwdriver for the viewer, seated in its cup: bolster cone resting on the cup cone. Board frame."""
    _, grip, bolster, shaft, tip, hl, sl = t
    rb, rg, ferrule = bolster / 2, grip / 2, 5.0
    k = math.tan(math.radians(CONE_DEG))
    prof = [(0, -sl), (shaft / 2, -sl), (shaft / 2, 0), (ferrule, 0), (rb, (rb - ferrule) * k),
            (rb, (rb - ferrule) * k + 10), (rg * 0.85, (rb - ferrule) * k + 22), (rg, hl * 0.45), (rg, hl * 0.85),
            (rg * 0.7, hl), (0, hl)]
    m = trimesh.creation.revolve(prof, sections=48)          # about +Z
    if tip > shaft + 0.5:                                     # slotted blade wider than the shaft
        blade = trimesh.creation.box(extents=[tip, 1.2, 14])
        blade.apply_translation([0, 0, -sl + 7])
        m = trimesh.util.concatenate([m, blade])
    m.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))   # +Z -> +Y
    # bolster cone (r = ferrule + h/k) on the cup cone (r = r_hole + (y - y_cone_bottom)/k), with CUP_CLEAR of air
    y_cone_bot = TOP_Y - CUP_WALL - cone_h(t)
    y0 = y_cone_bot + (ferrule - r_hole(t) + CUP_CLEAR) * k
    m.apply_translation([x_centre(), y0, z])
    return m


def tilt_limits(t):
    """Worst-case lean (deg) each support alone allows, from its radial play and the 2-point span."""
    span = (TOP_Y - CUP_WALL) - (BOTTOM + GUIDE_T / 2)
    guide_play = r_hole(t) - t[3] / 2
    return {"guide_and_cup_deg": round(math.degrees(math.atan((guide_play + CUP_CLEAR) / span)), 1),
            "old_ring_style_deg": "~15-30 (one loose ring, from the photos)"}


def print_pose(part):
    """Stand it as it hangs: board y -> bed Z (cups open up), board z -> bed X, board x -> bed Y.
    Shave 0.4 mm so the pins and bottom shelf sit on a flat first layer. Supports only under the 2 hooks."""
    big = 1000.0
    part = part - Box(big, big, big).locate(Location((0, BOTTOM + 0.4 - big / 2, 0)))
    posed = part.moved(Rotation(90, 0, 0)).moved(Rotation(0, 0, 90))
    bb = posed.bounding_box()
    return posed.moved(Location((-(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z)))


def main():
    OUT.mkdir(exist_ok=True)
    RENDERS.mkdir(exist_ok=True)
    assert not STYLE.check(BOARD), STYLE.check(BOARD)
    zs, (z0, z1), cols = layout()
    assert z1 - z0 <= 250, f"holder is {z1 - z0:.0f} mm wide: too wide for the 256 mm bed"

    part = build()
    printed = print_pose(part)
    export_step(printed, str(OUT / f"{NAME}.step"))
    mesh = mk.cad_to_mesh(printed)
    info = mk.report(mesh)
    assert info["watertight"], "holder is not watertight"
    mesh.export(OUT / f"{NAME}.stl")

    hung = mk.cad_to_mesh(part)
    hook_y = max(ROWS) * pb.PITCH
    clash = pb.interference_mm3(hung, pb.board_mesh(BOARD, rows=range(-1, 3), cols=range(-1, cols[1] + 2),
                                                    clearance=pb.FIT_CLEARANCE))
    rock = pb.rock_in(hung, BOARD, hook_y=hook_y)
    assert rock["ok"], f"holder won't rock onto the board: {rock}"

    drivers = [driver_ref(t, z) for t, z in zip(TOOLS, zs)]
    for t, d in zip(TOOLS, drivers):
        assert pb.interference_mm3(d, hung) < 1.0, f"{t[0]} hits the holder"
    for a, b in zip(drivers, drivers[1:]):
        assert pb.interference_mm3(a, b) == 0, "neighbouring handles touch"
    board = pb.board_mesh(BOARD, rows=range(-3, 8), cols=range(-2, cols[1] + 3))
    pb.to_zup(hung).export(RENDERS / "asm-screwdriver-holder.stl")
    pb.to_zup(trimesh.util.concatenate(drivers)).export(RENDERS / "ref-screwdrivers.stl")
    pb.to_zup(board).export(RENDERS / "ref-pegboard.stl")

    ext = hung.bounds[1] - hung.bounds[0]
    xc = x_centre()
    report = {
        "scale_status": "real size, but handle/bolster sizes are ESTIMATES from photos (shafts 5.03/6.43 and blade 9.58 measured)",
        "print": info,
        "print_orientation": "standing as it hangs (cups open up), bottom shelf + pins on the bed (0.4 mm flat); supports under the 2 hooks only",
        "fit_on_board": {"board": BOARD.name, "clearance_checked_per_side": pb.FIT_CLEARANCE,
                         "flush_overlap_mm3_info_only": clash, "rock_in": {**rock, "give_mm": pb.ROCK_IN_GIVE},
                         "holes_used": f"2 hooks (row {max(ROWS)}) + 2 pins (row {min(ROWS)}), columns {cols[0]} and {cols[1]}"},
        "stations": [{"tool": t[0], "z_mm": round(z, 1), "cup_d": round(2 * r_cup(t), 2), "hole_d": round(2 * r_hole(t), 2),
                      **tilt_limits(t)} for t, z in zip(TOOLS, zs)],
        "params_mm": {**asdict(STYLE), "holder_width": round(float(ext[2]), 1), "holder_front_x": round(float(hung.bounds[1][0]), 1), "holder_height": round(TOP_Y - BOTTOM, 1),
                      "cup_wall": CUP_WALL, "cup_clearance_dia": 2 * CUP_CLEAR, "hole_clearance_dia": 2 * HOLE_CLEAR,
                      "support_span": round((TOP_Y - CUP_WALL) - (BOTTOM + GUIDE_T / 2), 1), "grip_gap": GRIP_GAP,
                      "hook_spacing": (cols[1] - cols[0]) * pb.PITCH, "cup_centre_x": round(xc, 1)},
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("print", "fit_on_board")}, indent=2))
    print(json.dumps(report["stations"], indent=1))
    print(json.dumps({k: report["params_mm"][k] for k in ("holder_width", "holder_front_x", "holder_height", "support_span")}))

    render_sheet([mesh], str(RENDERS / "screwdriver-holder.png"), title=f"{NAME}: print pose (as it hangs), mm",
                 labels=["holder"], sections_y=(0.0,), sections_x=(0.0,))
    render_sheet([pb.to_zup(trimesh.util.concatenate([hung] + drivers))], str(RENDERS / "hung-with-drivers.png"),
                 title=f"{NAME}: hung, with the drivers (world Z-up, X out of the board)", labels=["holder + drivers"],
                 sections_y=(float(zs[3]),), sections_x=(float(xc),))


if __name__ == "__main__":
    main()
