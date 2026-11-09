"""Pegboard interface: the board standard and the pegs that hold a part on it. Use this for any custom pegboard part.

    import pegboard as pb
    style, board = pb.PegStyle(), pb.DEFAULT_BOARD
    part = my_body + pb.hook_peg(style, y=pb.PITCH) + pb.pin_peg(style)     # build123d solids
    clash = pb.interference_mm3(meshkit.cad_to_mesh(part), pb.board_mesh(board, clearance=pb.FIT_CLEARANCE))   # want 0

BOARD FRAME (every function here works in it; build parts in it too):
  x = out of the board. The board's front face is the plane x = 0, and the board fills -thickness <= x <= 0.
  y = up.
  z = across, along a row of holes.
  The origin is the centre of one hole on the front face. Hole centres are at (0, j*PITCH, i*PITCH).
A part's back face sits on x = 0. Its upper pegs are hooks (through the board, then up behind it). Its lower pegs are
straight pins that stop it rotating out. To hang it, tilt the part, push the hook tips up through the holes, then swing the
bottom in until the pins drop into their holes.

PegStyle defaults are measured from the owner's steel hook (projects/pegboard-hook), which is known to work on their board. Test them with projects/pegboard-fit-test.
See docs/pegboard.md.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import trimesh

PITCH = 25.4    # 1 in hole grid (both standard board types)


@dataclass(frozen=True)
class Board:
    name: str
    hole_d: float
    thickness: float
    pitch: float = PITCH


BOARDS = {
    # Nominal US hardboard pegboard. Real boards vary (holes 6.0-7.1 mm, 5-6.35 mm thick). Measure yours and add it here.
    "quarter": Board("1/4 in pegboard (1/4 in holes)", hole_d=6.35, thickness=6.35),
    "eighth": Board("1/8 in pegboard (3/16 in holes)", hole_d=4.76, thickness=3.2),
    # The owner's board (2026-11-05): Menards "3/16 x 4 x 8 White Pegboard Panel", white tempered hardboard.
    # Owner measured holes ~0.25 in on 1 in centres (listings had said 9/32 in). Thickness is still the listing's 0.155 in.
    "white_3_16": Board("3/16 in white hardboard (owner's, Menards)", hole_d=6.35, thickness=3.94),
}
DEFAULT_BOARD = BOARDS["white_3_16"]    # the owner's board: what every catalog part is checked against


@dataclass(frozen=True)
class PegStyle:
    """Peg geometry. Defaults come from the owner's steel hook, with the diameters tuned by test prints and pb.rock_in."""
    d: float = 6.1           # pin diameter. The steel wire is 5.53 (caliper). Printed at 5.53, then 5.9, the pegs were still loose
                             # in the owner's ~6.35 mm holes (test prints 2026-11-05). Settle it with the peg gauge (pegboard-fit-test)
    hook_d: float = 5.7      # hook diameter. Thinner than the pin so the sloped hook can rock in (rock_in: a 6.1 mm hook jams,
                             # level or sloped; 5.7 at 12 deg passes, with 6.1 pins). The hook's play doesn't matter: weight seats it
    hook_slope: float = 12.0 # the through-board part rises toward the back, like the steel hook's S-jog (v4 went in easily,
                             # v5's level step was much harder). The slope guides the hook as it rocks in
    hook_gap: float = 7.3    # clear space from the board's front face to the inside of the hook's rising leg (max board thickness)
    hook_rise: float = 14.0  # the hook leg's top end, above the hole centre
    bend_r: float = 4.5      # centreline radius of the hook's bend
    pin_len: float = 7.0     # how far a straight pin sticks into the board past the front face
    embed: float = 1.0       # how far pegs reach into the part (x > 0) so they fuse with it

    @property
    def r(self):
        return self.d / 2

    @property
    def hook_r(self):
        return self.hook_d / 2

    @property
    def leg_x(self):
        """x of the hook's rising-leg centreline."""
        return -(self.hook_gap + self.hook_r)

    def check(self, board: Board) -> list[str]:
        """Problems with this style on a board ([] if none)."""
        msgs = []
        for name, d in (("pin", self.d), ("hook", self.hook_d)):
            if d >= board.hole_d:
                msgs.append(f"{name} {d} mm does not fit {board.hole_d} mm holes")
        if self.hook_gap < board.thickness:
            msgs.append(f"hook gap {self.hook_gap} mm is less than the board thickness {board.thickness} mm")
        if self.leg_x + self.bend_r > -board.thickness + 1.0:
            msgs.append("the hook's bend starts more than 1 mm inside the hole, so it may bind; reduce bend_r or raise hook_gap")
        return msgs


# --------------------------------------------------------------------------------------------------------------------
# Pegs (build123d solids, board frame)
# --------------------------------------------------------------------------------------------------------------------

def hook_peg(style: PegStyle, y: float = 0.0, z: float = 0.0, slope_deg: float | None = None, cross_depth: float = 2.0):
    """Upper peg for the hole centred at (0, y, z): back through the board, a bend, then a leg rising behind it.
    The through-board part rises toward the back at slope_deg (default style.hook_slope, like the steel hook's S-jog),
    crossing the hole's centre `cross_depth` behind the front face. The slope guides the hook as it rocks in; a level
    peg (0) can jam (see rock_in)."""
    slope_deg = style.hook_slope if slope_deg is None else slope_deg
    import math
    from build123d import BuildLine, BuildPart, BuildSketch, Circle, FilletPolyline, Plane, Vector, sweep
    t = math.tan(math.radians(slope_deg))
    y_at = lambda x: y + (-cross_depth - x) * t     # noqa: E731
    pts = [Vector(style.embed, y_at(style.embed), z), Vector(style.leg_x, y_at(style.leg_x), z),
           Vector(style.leg_x, y + style.hook_rise, z)]
    with BuildPart() as part:
        with BuildLine() as path:
            FilletPolyline(*pts, radius=style.bend_r)
        with BuildSketch(Plane(origin=pts[0], z_dir=(pts[1] - pts[0]).normalized())):
            Circle(style.hook_r)
        sweep(path=path.wires()[0])
    return part.part


def pin_peg(style: PegStyle, y: float = 0.0, z: float = 0.0):
    """Lower peg for the hole centred at (0, y, z): a straight pin (anti-rotation)."""
    from build123d import Cylinder, Location
    length = style.pin_len + style.embed
    return Cylinder(style.r, length, rotation=(0, 90, 0)).locate(Location((style.embed - length / 2, y, z)))


def mount_plate(style: PegStyle, cols=(0,), rows=(0, 1), thickness: float = 4.0, margin: float = 8.0,
                z_range: tuple | None = None, top_margin: float | None = None, top_round: bool = True):
    """A back plate on the front face with hooks in the top row of holes and pins in the bottom row.
    cols / rows are hole indices (z = col*PITCH, y = row*PITCH). Build the part's body on its front (x = thickness).
    z_range overrides the plate's z extent, e.g. to make its edge flush with the pegs for printing on its side.

    To hang a part you rock it in around the hooks, so whatever sits on the board above the hooks swings into the board.
    By default the plate stops just above the hook (`top_margin`, default peg radius + 0.5 mm) and its top back edge
    is rounded (`top_round`) so it can rock in like the steel hook. Keep a part's body clear of the board above
    the hooks for the same reason."""
    from build123d import Axis, Box, Location, fillet
    top = max(rows) * PITCH
    tm = style.hook_r + 0.5 if top_margin is None else top_margin
    y0, y1 = min(rows) * PITCH - margin, top + tm
    z0, z1 = z_range or (min(cols) * PITCH - margin, max(cols) * PITCH + margin)
    plate = Box(thickness, y1 - y0, z1 - z0).locate(Location((thickness / 2, (y0 + y1) / 2, (z0 + z1) / 2)))
    if top_round:
        edge = min(plate.edges().filter_by(Axis.Z), key=lambda e: (e.center().X, -e.center().Y))
        plate = fillet(edge, radius=min(thickness, tm) - 0.3)
    for c in cols:
        plate = plate + hook_peg(style, top, c * PITCH)
        if min(rows) != max(rows):
            plate = plate + pin_peg(style, min(rows) * PITCH, c * PITCH)
    return plate


def lay_on_side(solid, style: PegStyle, flat: float = 0.4, z_peg: float = 0.0):
    """Print pose with the pegs flat on the bed (the strong way: layers run along the pegs, no supports under them).
    Shaves `flat` mm off the bed side of the pegs at z = z_peg for a flat first layer, puts the bed at Z = 0 and centres XY.
    The board frame's x / y stay as the bed's X / Y."""
    from build123d import Box, Location
    big = 1000.0
    cut_z = z_peg - style.r + flat
    solid = solid - Box(big, big, big).locate(Location((0, 0, cut_z - big / 2)))
    bb = solid.bounding_box()
    return solid.moved(Location((-(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z)))


# --------------------------------------------------------------------------------------------------------------------
# Board meshes and fit checks (trimesh, board frame)
# --------------------------------------------------------------------------------------------------------------------

FIT_CLEARANCE = 0.1   # mm per side a part must clear the holes by. Was 0.2, but the owner's printed pegs came out loose, not fat


def board_mesh(board: Board, rows=range(-1, 3), cols=range(-1, 2), sections: int = 32,
               clearance: float = 0.0) -> trimesh.Trimesh:
    """A patch of pegboard covering the given hole rows / cols, for fit checks and viewers.
    clearance > 0 shrinks the holes by that much per side, so a zero-interference check leaves that margin."""
    rows, cols = list(rows), list(cols)
    p = board.pitch
    h, w = len(rows) * p, len(cols) * p
    yc, zc = (rows[0] + rows[-1]) / 2 * p, (cols[0] + cols[-1]) / 2 * p
    slab = trimesh.creation.box(extents=[board.thickness, h, w])
    slab.apply_translation([-board.thickness / 2, yc, zc])
    holes = []
    for j in rows:
        for i in cols:
            c = trimesh.creation.cylinder(radius=board.hole_d / 2 - clearance, height=board.thickness + 2, sections=sections)
            c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
            c.apply_translation([-board.thickness / 2, j * p, i * p])
            holes.append(c)
    return slab.difference(trimesh.util.concatenate(holes), engine="manifold")


def interference_mm3(part: trimesh.Trimesh, board: trimesh.Trimesh) -> float:
    """Volume where a hung part overlaps the board (0 = it fits as placed)."""
    inter = part.intersection(board, engine="manifold")
    return round(float(abs(inter.volume)), 2) if len(inter.faces) else 0.0


# --------------------------------------------------------------------------------------------------------------------
# Rock-in check: can the part actually be put on the board?
# --------------------------------------------------------------------------------------------------------------------

ROCK_IN_GIVE = 0.3   # mm the hole may "give" (hardboard edge, print tolerance). Calibrated on the owner's prints of
                     # projects/pegboard-hook: with 0.3 the sim passes v4 (5.53 mm, 12 deg S-jog: went in easily) and
                     # fails v5 (5.9 mm, level step: much harder to get in). With 0.15 it fails both


def _board_hit(pts, board, give, margin=0.03):
    """(hits the board, entirely in front of it) for points in the board frame."""
    x, y, z = pts.T
    inslab = (x > -board.thickness + margin + give) & (x < -margin - give)     # touching a face is fine
    if not inslab.any():
        return False, bool((x > 0.5).all())
    yi, zi = y[inslab], z[inslab]
    hy, hz = np.round(yi / board.pitch) * board.pitch, np.round(zi / board.pitch) * board.pitch
    inhole = (yi - hy) ** 2 + (zi - hz) ** 2 < (board.hole_d / 2 - margin + give) ** 2
    return bool((~inhole).any()), False


def rock_in(part: trimesh.Trimesh, board: Board = DEFAULT_BOARD, hook_y: float = PITCH, give: float = ROCK_IN_GIVE,
            dtheta_deg: float = 0.5, step: float = 0.1, max_states: int = 60000, seed: int = 0) -> dict:
    """Search for a way to take the hung part off the board (= put it on, in reverse): tilt the bottom out about the hook
    row (y = hook_y) while sliding in x / y, until it's entirely in front of the board. Rigid parts, holes `give` mm larger.
    Returns {"ok", "max_tilt_deg", "states"}. The strict flush check (interference_mm3) can't tell a hook that rocks in
    from one that jams; this can (see ROCK_IN_GIVE)."""
    import heapq
    pts, _ = trimesh.sample.sample_surface_even(part, 150000, seed=seed)
    pts = np.vstack([pts, part.vertices]) - [0, hook_y, 0]

    def pose(k, i, j):
        th = np.radians(k * dtheta_deg)
        c, s = np.cos(th), np.sin(th)
        x = pts[:, 0] * c - pts[:, 1] * s + i * step
        y = pts[:, 0] * s + pts[:, 1] * c + hook_y + j * step
        return np.c_[x, y, pts[:, 2]]

    if _board_hit(pose(0, 0, 0), board, give)[0]:
        return {"ok": False, "why": "overlaps the board when hung", "states": 1}
    start = (0, 0, 0)
    seen, parent, heap = {start}, {start: None}, [(0.0, start)]
    moves = [(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1) if (a, b, c) != (0, 0, 0)]
    while heap and len(seen) < max_states:
        _, cur = heapq.heappop(heap)
        for m in moves:
            n = (cur[0] + m[0], cur[1] + m[1], cur[2] + m[2])
            if n in seen or n[0] < 0 or n[0] * dtheta_deg > 120:
                continue
            seen.add(n)
            hit, free = _board_hit(pose(*n), board, give)
            if hit:
                continue
            parent[n] = cur
            if free:
                path = [n]
                while parent[path[-1]] is not None:
                    path.append(parent[path[-1]])
                return {"ok": True, "max_tilt_deg": max(q[0] for q in path) * dtheta_deg, "states": len(seen)}
            heapq.heappush(heap, (-(n[0] * dtheta_deg * 0.5 + n[1] * step), n))
    return {"ok": False, "why": "jams: no way found to tilt it on", "states": len(seen)}


def to_zup(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Board frame -> world Z-up (X out of the board, Y across, Z up), e.g. for the review viewer."""
    m = mesh.copy()
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    return m
