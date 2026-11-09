"""Reproducible build for the pegboard Bambu Lab sign.

    python projects/pegboard-bambu-sign/build.py        (under a minute)

A flat sign that hangs flush on the pegboard with the Bambu Lab logo (mark + "bambu lab") raised in the centre in a second colour.
Two pieces, so each prints the strong / easy way:
  - SIGN: printed face up, back on the bed. The logo sits on top of the plate, so the only colour change is one swap at the
    plate's top (no prime-tower churn). Hidden pockets with keyhole slots in its back drop over the hangers' studs.
  - HANGERS (print 2): a small mount plate with the shared hook peg + pin (tools/pegboard.py) and a T-stud on its front.
    They print on their side, pegs on the bed (layers along the pegs). Hang them on the board first, then push the sign
    flat onto the board over the studs and slide it down 13.6 mm: the studs' heads catch behind the slots' ledges.
Pegs printed into a face-up sign would stand up off the bed and snap at a layer line, and printing the sign on its side would
spread the logo's colour change over every layer, so the pegs are on separate hangers.

  -> output/pegboard-bambu-sign-multicolor.3mf   sign + logo as two parts of one object (assign filaments per part)
  -> output/pegboard-bambu-sign.step / .stl      sign + logo merged (single colour, or for a manual colour change)
  -> output/pegboard-bambu-sign-{base,logo}.stl  the two colour bodies on their own
  -> output/pegboard-bambu-sign-hanger.step/.stl one hanger, print pose (print 2)
  -> output/report.json                          checks, params, board fit, slide-on check
  -> renders/sign.png, renders/hanger.png        views + sections
  -> renders/asm-*.stl, ref-pegboard.stl         hung on the board (world Z-up), for the viewer

Board frame (tools/pegboard.py): x out of the board, y up, z across. The sign's back face is x = 0 (flush on the board).
"""

import json
import sys
from dataclasses import asdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / "tools")]

import meshkit as mk  # noqa: E402
import numpy as np  # noqa: E402
import pegboard as pb  # noqa: E402
import trimesh  # noqa: E402
from build123d import (Axis, Box, Location, Plane, Rot,  # noqa: E402
                       chamfer, export_step, extrude, fillet)
from render import render_sheet  # noqa: E402

OUT = HERE / "output"
RENDERS = HERE / "renders"
LOGO_SVG = HERE / "source" / "bambulab-logo-2026-11-09.svg"   # Wikimedia Commons "File:BambuLab logo.svg"

BOARD = pb.DEFAULT_BOARD
STYLE = pb.PegStyle()          # shared pegs: 6.1 mm pins, 5.7 mm hooks sloped 12 deg (they rock in: pb.rock_in)
C = 0.3                       # sliding clearance per side between sign and hanger

# ---- Hangers (one per column; hook in row 1, pin in row 0) ------------------------------------------------------------
HANGER_COLS = (0, 8)          # 8 in apart: wide enough that the sign can't rock side to side
HOOK_ROW, PIN_ROW = 1, 0
PLATE_T = 3.0                 # hanger plate thickness (sits in a pocket in the sign's back)
PLATE_W = 11.0                # across (z); its bed-side edge is flush with the pegs (prints on its side, no supports)
PLATE_MARGIN = 8.0            # plate below the pin
Z_LO = -STYLE.r               # hanger's bed-side face
ZC = Z_LO + PLATE_W / 2       # stud centre across (z), relative to the hanger's peg column
Y0 = PIN_ROW * pb.PITCH - PLATE_MARGIN
Y1 = HOOK_ROW * pb.PITCH + STYLE.hook_r + 0.5          # mount_plate's default top margin
STUD_Y = (HOOK_ROW + PIN_ROW) / 2 * pb.PITCH      # stud centre height, between the hook and the pin
NECK_W, NECK_H = 5.0, 10.0    # stud neck (z across, y up)
HEAD_W, HEAD_H = PLATE_W, 12.0
HEAD_T = 2.0                  # head thickness (x)

# ---- Sign ------------------------------------------------------------------------------------------------------------
SIGN_W, SIGN_H = 250.0, 120.0  # across (z) x up (y). As wide as the A1's 256 mm bed allows, with 3 mm to spare each side
CORNER_R = 10.0               # rounded corners (seen from the front)
FRONT_CHAMFER = 1.0           # 45 deg chamfer round the front edge
TOP_MARGIN = 8.0              # sign above the pockets' top
T_BACK = 2.0                  # the slotted layer the stud necks pass through (its ledges hold the heads)
T_CAP = 1.6                   # solid layer over the chambers (8 layers at 0.2; the chamber roofs are short bridges)
POCKET_D = PLATE_T + C        # pocket depth from the sign's back
CHAMBER_T = HEAD_T + 2 * C
SIGN_T = POCKET_D + T_BACK + CHAMBER_T + T_CAP
DROP = HEAD_H + 2 * C + 1.0   # how far the sign slides down onto the studs
NECK_X1 = POCKET_D + T_BACK + 0.25                # stud neck ends (head starts) 0.25 into the chamber

# ---- Logo ------------------------------------------------------------------------------------------------------------
LOGO_W = 220.0                # width of the whole logo (mark + "bambu lab") on the sign; height follows (~64)
LOGO_RAISE = 1.2              # raised above the sign face (6 layers at 0.2)

SIGN_Z_MID = (min(HANGER_COLS) + max(HANGER_COLS)) / 2 * pb.PITCH + ZC
SIGN_Y_TOP = Y1 + C + TOP_MARGIN
SIGN_Y_MID = SIGN_Y_TOP - SIGN_H / 2


def _wire_xy(wire, step=0.5):
    """A closed wire as (x, y) points: line edges by their ends, curves every `step` SVG units."""
    pts = []
    for e in wire.order_edges():
        n = 1 if e.geom_type.name == "LINE" else max(4, int(e.length / step))
        seg = [e.position_at(i / n) for i in range(n + 1)]
        if pts and (seg[-1] - pts[-1]).length < (seg[0] - pts[-1]).length:
            seg = seg[::-1]          # edge runs the other way
        pts += [q for q in seg if not pts or (q - pts[-1]).length > 1e-6]
    return [(q.X, q.Y) for q in pts]


def _closed_face(face, r):
    """face rebuilt as a polygon face (curves in 0.5 SVG unit steps). A hole that touches the outline is shrunk by r,
    so the wall between them is at least r wide instead of pinching to a point."""
    from build123d import Face, Wire
    from shapely.geometry import Polygon as ShPolygon
    outer = ShPolygon(_wire_xy(face.outer_wire())).buffer(0)
    poly = outer
    for w in face.inner_wires():
        hole = ShPolygon(_wire_xy(w)).buffer(0)
        if r and hole.distance(outer.exterior) < 1e-3:
            hole = hole.buffer(-r, join_style="mitre")
        poly = poly.difference(hole)
    poly = poly.simplify(0.02)
    assert poly.geom_type == "Polygon", poly.geom_type
    ring = lambda c: Wire.make_polygon([(x, y, 0) for x, y in list(c)[:-1]], close=True)   # noqa: E731
    return Face(ring(poly.exterior.coords), [ring(i.coords) for i in poly.interiors])


def logo_faces():
    """The full Bambu Lab logo (the four-block mark + "bambu" over "lab"), as build123d faces in SVG units, y up."""
    from build123d import import_svg
    faces = [f.fix() for f in import_svg(str(LOGO_SVG))]   # fix(): the "b" path has a zero-length curve
    assert all(f.is_valid for f in faces), "invalid face in the logo SVG"
    # In the SVG, the B's upper counter touches its outline at one point (a pinch: non-manifold, and a zero-width
    # wall). That counter is shrunk by 0.5 SVG units (~0.25 mm on the sign) so a real wall separates them.
    # Every shape is rebuilt as a plain polygon face in world coordinates (the imported faces carry a y-flip location,
    # which build123d's scale() doesn't apply consistently).
    faces = [_closed_face(f, 0.5 if any(w.distance_to(f.outer_wire()) < 1e-3 for w in f.inner_wires()) else 0.0)
             for f in faces]
    # The "b"'s small slanted accent touches the letter at one corner, which would make a non-manifold (pinched) mesh
    # and a sliver the nozzle can't print. Nudge the smaller of any touching pair away until there's a 1 SVG unit
    # (~0.5 mm on the sign) gap between them.
    for i in range(len(faces)):
        for j in range(i + 1, len(faces)):
            if faces[i].distance_to(faces[j]) < 1e-3:
                k, other = (i, j) if faces[i].area < faces[j].area else (j, i)
                away = (faces[k].center() - faces[other].center()).normalized() * 0.1
                while faces[k].distance_to(faces[other]) < 1.0:
                    faces[k] = faces[k].moved(Location(away))
    assert len(faces) == 13, f"expected the mark (4) + 9 letter shapes in {LOGO_SVG.name}, got {len(faces)}"
    return faces


def logo_solid(x_face):
    """The logo, centred on the sign, raised from x_face by LOGO_RAISE. Logo right = board -z (seen from the front)."""
    from build123d import Compound
    faces = logo_faces()
    bb = Compound(faces).bounding_box()
    s = LOGO_W / (bb.max.X - bb.min.X)
    scaled = [f.scale(s) for f in faces]
    bb2 = Compound(scaled).bounding_box()
    centre = Location((-(bb2.min.X + bb2.max.X) / 2, -(bb2.min.Y + bb2.max.Y) / 2, 0))
    face_plane = Plane(origin=(x_face, SIGN_Y_MID, SIGN_Z_MID), x_dir=(0, 0, -1), z_dir=(1, 0, 0))   # local u right, v up
    placed = [face_plane * f.moved(centre) for f in scaled]
    solid = extrude(Compound(placed), amount=LOGO_RAISE, dir=(1, 0, 0))     # out of the sign face
    height = (bb.max.Y - bb.min.Y) * s
    stroke = 11.3 * s          # letter stroke width: 11.3-11.6 SVG units
    gap = 7.22 * s             # the mark's straight gaps: 7.22 SVG units (the smallest gaps in the logo)
    return solid, round(height, 1), round(stroke, 1), round(gap, 1)


def box(x0, x1, y0, y1, z0, z1):
    return Box(x1 - x0, y1 - y0, z1 - z0).locate(Location(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)))


def hanger(col=0):
    """Mount plate (shared hook + pin) with a T-stud on the front. All in the board frame, for the hanger in column `col`."""
    z = col * pb.PITCH
    plate = pb.mount_plate(STYLE, cols=(col,), rows=(PIN_ROW, HOOK_ROW), thickness=PLATE_T, margin=PLATE_MARGIN,
                           z_range=(z + Z_LO, z + Z_LO + PLATE_W))
    zc = z + ZC
    neck = box(PLATE_T - 0.5, NECK_X1, STUD_Y - NECK_H / 2, STUD_Y + NECK_H / 2, zc - NECK_W / 2, zc + NECK_W / 2)
    head = box(NECK_X1, NECK_X1 + HEAD_T, STUD_Y - HEAD_H / 2, STUD_Y + HEAD_H / 2, zc - HEAD_W / 2, zc + HEAD_W / 2)
    return plate + neck + head


def sign_base():
    """The sign plate with its two hidden hanger pockets + keyhole slots (in the final, hung position)."""
    z0, z1 = SIGN_Z_MID - SIGN_W / 2, SIGN_Z_MID + SIGN_W / 2
    y0, y1 = SIGN_Y_TOP - SIGN_H, SIGN_Y_TOP
    plate = box(0, SIGN_T, y0, y1, z0, z1)
    plate = fillet(plate.edges().filter_by(Axis.X), CORNER_R)
    front = [e for e in plate.edges() if abs(e.center().X - SIGN_T) < 1e-6]
    plate = chamfer(front, FRONT_CHAMFER)
    for col in HANGER_COLS:
        zc = col * pb.PITCH + ZC
        ent_y0 = STUD_Y - DROP - HEAD_H / 2 - C        # entry opening: the stud head goes in here, then slides up
        pocket = box(-1, POCKET_D, Y0 - DROP - C, Y1 + C, zc - PLATE_W / 2 - C, zc + PLATE_W / 2 + C)
        entry = box(POCKET_D - 0.1, POCKET_D + T_BACK + 0.1, ent_y0, STUD_Y - DROP + HEAD_H / 2 + C,
                    zc - HEAD_W / 2 - C, zc + HEAD_W / 2 + C)
        slot = box(POCKET_D - 0.1, POCKET_D + T_BACK + 0.1, ent_y0, STUD_Y + NECK_H / 2 + 0.05,
                   zc - NECK_W / 2 - C, zc + NECK_W / 2 + C)
        chamber = box(POCKET_D + T_BACK, POCKET_D + T_BACK + CHAMBER_T, ent_y0, STUD_Y + HEAD_H / 2 + C,
                      zc - HEAD_W / 2 - C, zc + HEAD_W / 2 + C)
        plate = plate - pocket - entry - slot - chamber
    return plate


def print_pose(solid):
    """Sign: back on the bed, face up (board x -> bed Z). Seen from above, the logo reads the right way round."""
    return solid.moved(Location((0, 0, 0)) * Rot(0, -90, 0))


def _section_region(mesh, z, flip_x=False):
    """Even-odd filled region of a horizontal mesh section (shapely), optionally mirrored in X (to view it from below)."""
    from shapely.geometry import Polygon as ShPolygon
    region = ShPolygon()
    for loop in mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1]).discrete:
        xy = loop[:, :2] * ([-1, 1] if flip_x else [1, 1])
        region = region.symmetric_difference(ShPolygon(xy).buffer(0))
    return region


def _fill(ax, region, colour, **kw):
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MplPath
    geoms = getattr(region, "geoms", [region])
    for g in geoms:
        rings = [np.array(g.exterior.coords)] + [np.array(r.coords) for r in g.interiors]
        verts = np.vstack(rings)
        codes = np.concatenate([[MplPath.MOVETO] + [MplPath.LINETO] * (len(r) - 2) + [MplPath.CLOSEPOLY] for r in rings])
        ax.add_patch(PathPatch(MplPath(verts, codes), facecolor=colour, edgecolor="none", **kw))


def render_face(base_m, logo_m, path):
    """Colour drawing of the sign: the front as hung (base + logo) and the back, with the pockets and keyhole slots."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (front, back) = plt.subplots(1, 2, figsize=(13, 6.8))
    _fill(front, _section_region(base_m, float(base_m.bounds[1, 2]) - 0.05), "#2b2b2e")
    _fill(front, _section_region(logo_m, float(logo_m.bounds[1, 2]) - 0.05), "#00ae42")
    # Seen from behind, deepest layer first: chamber roof (orange), chamber layer, slotted layer, back face.
    _fill(back, _section_region(base_m, SIGN_T - T_CAP / 2, flip_x=True), "#e0a030")
    _fill(back, _section_region(base_m, POCKET_D + T_BACK + 0.1, flip_x=True), "#9a9aa2")
    _fill(back, _section_region(base_m, POCKET_D + 0.1, flip_x=True), "#6a6a72")          # the slotted layer
    _fill(back, _section_region(base_m, 0.05, flip_x=True), "#2b2b2e")                     # the back face
    for ax, title in ((front, "front (as hung)"), (back, "back, seen from behind: pockets (grey), slots, chambers (orange)")):
        ax.set_title(title)
        ax.set_aspect("equal")
        ax.set_xlim(-SIGN_W / 2 - 5, SIGN_W / 2 + 5)
        ax.set_ylim(-SIGN_H / 2 - 5, SIGN_H / 2 + 5)
        ax.grid(alpha=0.3)
    fig.suptitle(f"pegboard-bambu-sign: {SIGN_W:.0f} x {SIGN_H:.0f} x {SIGN_T:.1f} mm, logo {LOGO_W:.0f} mm wide, raised {LOGO_RAISE} mm")
    fig.tight_layout()
    fig.savefig(path, dpi=90)
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    RENDERS.mkdir(exist_ok=True)
    assert not STYLE.check(BOARD), STYLE.check(BOARD)

    # ---- Sign (two colour bodies) ----
    base = sign_base()
    logo, logo_h, logo_stroke, logo_gap = logo_solid(SIGN_T)
    base_p, logo_p = print_pose(base), print_pose(logo)
    bb = (base_p + logo_p).bounding_box()
    dx, dy = -(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2
    shift = Location((dx, dy, -bb.min.Z))
    base_p, logo_p = base_p.moved(shift), logo_p.moved(shift)
    sign_p = base_p + logo_p
    export_step(sign_p, str(OUT / "pegboard-bambu-sign.step"))
    base_m, logo_m, sign_m = (mk.cad_to_mesh(s) for s in (base_p, logo_p, sign_p))
    for name, m in (("base", base_m), ("logo", logo_m), ("sign", sign_m)):
        assert m.is_watertight, f"{name} is not watertight"
    base_m.export(OUT / "pegboard-bambu-sign-base.stl")
    logo_m.export(OUT / "pegboard-bambu-sign-logo.stl")
    sign_m.export(OUT / "pegboard-bambu-sign.stl")
    info = mk.report(sign_m)
    scene = trimesh.Scene()
    for name, m in (("sign (base colour)", base_m), ("logo (logo colour)", logo_m)):
        scene.add_geometry(m, node_name=name, geom_name=name)
    scene.export(OUT / "pegboard-bambu-sign-multicolor.3mf")

    # ---- Hanger ----
    h_board = hanger(0)
    h_print = pb.lay_on_side(h_board, STYLE)
    export_step(h_print, str(OUT / "pegboard-bambu-sign-hanger.step"))
    h_mesh = mk.cad_to_mesh(h_print)
    h_info = mk.report(h_mesh)
    assert h_info["watertight"], "hanger is not watertight"
    h_mesh.export(OUT / "pegboard-bambu-sign-hanger.stl")

    # ---- Fit checks (board frame) ----
    hangers = trimesh.util.concatenate([mk.cad_to_mesh(hanger(c)) for c in HANGER_COLS])
    rows = range(PIN_ROW - 1, HOOK_ROW + 2)
    cols = range(min(HANGER_COLS) - 1, max(HANGER_COLS) + 2)
    board_fit = pb.board_mesh(BOARD, rows=rows, cols=cols, clearance=pb.FIT_CLEARANCE)
    # A sloped hook overlaps a little in the strict flush check (like the steel hook); that's information only.
    # The real test is whether it rocks on: pb.rock_in, calibrated on the owner's hook prints.
    clash = sum(pb.interference_mm3(mk.cad_to_mesh(hanger(c)), board_fit) for c in HANGER_COLS)
    rock = pb.rock_in(mk.cad_to_mesh(h_board), BOARD, hook_y=HOOK_ROW * pb.PITCH)
    assert rock["ok"], f"hanger won't rock onto the board: {rock}"

    sign_hung = mk.cad_to_mesh(base + logo)
    # Slide-on: the sign goes flat onto the board DROP mm high, then slides down. Check the pose at each step.
    slide = {}
    for f in np.linspace(0, 1, 9):
        s = sign_hung.copy()
        s.apply_translation([0.01, f * DROP, 0])          # 0.01 off the board face (touching faces aren't overlap)
        slide[round(float(f * DROP), 1)] = pb.interference_mm3(s, hangers)
    assert all(v == 0.0 for v in slide.values()), f"sign hits the hangers while sliding on: {slide}"
    # Push-on: at the top of the slide, the sign must go straight in from the front without hitting the studs.
    push = {}
    for off in (SIGN_T, SIGN_T / 2, 2.0, 0.5):
        s = sign_hung.copy()
        s.apply_translation([off, DROP, 0])
        push[round(off, 1)] = pb.interference_mm3(s, hangers)
    assert all(v == 0.0 for v in push.values()), f"sign hits the studs as it's pushed on: {push}"
    # Retention: hung, the stud heads overlap the slot ledges, so pulling the sign straight off the board catches.
    s = sign_hung.copy()
    s.apply_translation([1.0, 0, 0])
    caught = pb.interference_mm3(s, hangers)
    assert caught > 0, "sign isn't held: it would come straight off the studs"
    s = sign_hung.copy()
    s.apply_translation([0.01, 0, 0])
    board_view = pb.board_mesh(BOARD, rows=range(-6, 4), cols=range(-2, 7))
    assert pb.interference_mm3(s, board_view) == 0.0, "sign overlaps the board"

    pb.to_zup(mk.cad_to_mesh(base)).export(RENDERS / "asm-sign.stl")
    pb.to_zup(mk.cad_to_mesh(logo)).export(RENDERS / "asm-logo.stl")
    pb.to_zup(hangers).export(RENDERS / "asm-hangers.stl")
    pb.to_zup(board_view).export(RENDERS / "ref-pegboard.stl")

    hook_y = HOOK_ROW * pb.PITCH
    report = {
        "scale_status": "real size (shared peg interface; sign size is the owner's choice, default 250 x 120 mm, as big as the A1 bed allows)",
        "print": info,
        "print_orientation": "sign face up, back on the bed, no supports (pockets open to the bed; chamber roofs are ~12 mm bridges)",
        "colour": {"swaps": 1, "swap_at_mm": round(SIGN_T, 2), "logo_layers_at_0.2": round(LOGO_RAISE / 0.2)},
        "hanger_print": h_info,
        "hanger_print_orientation": "on its side, pegs flat on the bed (0.4 mm flat at the pin; the sloped hook sits ~0.6 mm higher at its front), no supports. Print 2",
        "fit_on_board": {"board": BOARD.name, "hole_d": BOARD.hole_d, "thickness": BOARD.thickness,
                         "pitch": BOARD.pitch, "clearance_checked_per_side": pb.FIT_CLEARANCE,
                         "hanger_flush_overlap_mm3_info_only": clash,
                         "hanger_rock_in": {**rock, "give_mm": pb.ROCK_IN_GIVE},
                         "holes_used": f"2 hangers, {max(HANGER_COLS) - min(HANGER_COLS)} holes apart: hook + pin 1 in below each",
                         "sign_top_above_hook_hole_mm": round(SIGN_Y_TOP - hook_y, 1),
                         "sign_bottom_below_hook_hole_mm": round(hook_y - (SIGN_Y_TOP - SIGN_H), 1),
                         "sign_past_outer_hanger_columns_mm": round(SIGN_Z_MID + SIGN_W / 2 - max(HANGER_COLS) * pb.PITCH, 1)},
        "slide_on_check": {"drop_mm": DROP, "interference_while_sliding_mm3": slide,
                           "interference_pushing_on_mm3": push, "pull_off_blocked_mm3": caught},
        "params_mm": {**asdict(STYLE), "pitch": pb.PITCH, "sign_width": SIGN_W, "sign_height": SIGN_H,
                      "sign_thickness": round(SIGN_T, 2), "total_thickness": round(SIGN_T + LOGO_RAISE, 2),
                      "corner_radius": CORNER_R, "front_chamfer": FRONT_CHAMFER,
                      "logo_width": LOGO_W, "logo_height": logo_h, "logo_stroke": logo_stroke, "logo_smallest_gap": logo_gap, "logo_raise": LOGO_RAISE,
                      "hanger_spacing": (max(HANGER_COLS) - min(HANGER_COLS)) * pb.PITCH,
                      "hook_to_pin": (HOOK_ROW - PIN_ROW) * pb.PITCH, "drop": DROP,
                      "hanger_plate_t": PLATE_T, "stud_neck": [NECK_W, NECK_H], "stud_head": [HEAD_W, HEAD_H, HEAD_T],
                      "slot_clearance": C,
                      "hole_clearance_per_side": round((BOARD.hole_d - STYLE.d) / 2, 2)},
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("print", "hanger_print", "fit_on_board", "slide_on_check")}, indent=2))

    render_sheet([sign_m, logo_m], str(RENDERS / "sign.png"), title="pegboard-bambu-sign: print pose (face up), mm",
                 labels=["sign", "logo"], sections_y=(STUD_Y + dy, SIGN_Y_MID + dy),     # print X = -z + dx, Y = y + dy
                 sections_x=(-(max(HANGER_COLS) * pb.PITCH + ZC) + dx, -SIGN_Z_MID + dx))
    render_face(base_m, logo_m, RENDERS / "face.png")
    render_sheet(h_mesh, str(RENDERS / "hanger.png"), title="pegboard-bambu-sign hanger: print pose (on its side), mm, print 2",
                 labels=["hanger"], sections_y=(0.0,), sections_x=(0.0,))


if __name__ == "__main__":
    main()
