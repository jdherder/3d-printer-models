"""Parametric wall hook that hangs a bike vertically by its front rim, screwed to a horizontal 2x4.

The hook is one constant-width extrusion of a side profile, so it prints lying on its side with no supports and
every layer runs along the profile: the bending loads from the bike are carried along the filament, never across
layer lines.

Profile frame (how the hook sits on the wall, seen from the side; the print pose is this frame as is):
  x = out from the 2x4's front face (the face is x = 0; the wall is behind, at x = -board_depth)
  y = up (y = 0 is the 2x4's top face)
  z = across the hook, along the 2x4 (the profile is extruded symmetrically, |z| <= width / 2)

Parts of the profile:
  lip     sits on top of the 2x4 (y = 0 .. lip_t, x = -lip_depth .. 0). It carries the bike's weight straight down
          into the board, and its two vertical screws stop the top of the hook pulling away from the wall.
  plate   against the 2x4's front face (x = 0 .. plate_t, y = -plate_h .. lip_t). Its bottom edge bears on the
          board; one horizontal screw near the bottom keeps it from lifting or swinging.
  arm     tapers from the plate out to the seat. Its top slopes down `top_slope_deg` so the rim slides into the crook.
  crook   where the rim sits (concave radius `crook_r`), against the inside face of the tip at x = reach.
  tip     rises `tip_h` above the seat so the rim can't slide off.
"""

import math
from dataclasses import asdict, dataclass

from build123d import (Axis, Box, BuildPart, BuildSketch, Cylinder, Location, Locations, Mode, Polygon, Vector, chamfer,
                       extrude, fillet)


@dataclass
class HookParams:
    # --- the 2x4 (nominal 2x4 = 1.5 x 3.5 in), mounted flat on the wall: wide face out, horizontal ---
    board_depth: float = 38.1         # 1.5 in: how far the 2x4 stands off the wall (lip screws are centred on this)
    board_face: float = 88.9          # 3.5 in: height of the 2x4's front face

    # --- hook body ---
    width: float = 32.0               # constant extrusion width (also the arm width that passes between the spokes)
    lip_depth: float = 30.0           # how far the lip reaches back over the 2x4's top (< board_depth)
    lip_t: float = 10.0
    plate_t: float = 14.0             # with #10 x 2 in screws: 51 - 14 = 37 mm into a 38 mm board
    plate_h: float = 80.0             # plate runs this far below the 2x4's top (face is 88.9 tall)
    reach: float = 100.0              # 2x4 face to the inside face of the tip (where the rim stops)
    top_slope_deg: float = 5.0        # arm top slopes down toward the crook
    crook_r: float = 10.0
    tip_h: float = 35.0               # tip top above the seat (the lowest point of the crook)
    tip_t: float = 16.0
    seat_depth: float = 26.0          # arm depth (top to bottom) under the seat
    belly_y: float = -44.0            # where the arm's underside meets the plate front
    belly_r: float = 14.0             # concave fillet there
    edge_chamfer: float = 1.5         # on both side faces' outlines (45 deg, prints fine on the bed side)
    corner_r: float = 3.0             # small convex corners
    inner_corner_r: float = 2.0       # where the lip meets the plate (2x4 edges are eased ~3 mm, so this still seats)

    # --- screws: #10 (4.8 mm) wood screws with washer/pan heads, e.g. cabinet screws ---
    screw_hole_d: float = 5.4         # clearance (holes print a little small)
    head_d: float = 12.7              # washer-head screw (for the clearance checks)
    lip_screw_x: float = -19.05       # centred on the 2x4's top face
    lip_screw_dz: float = 9.0         # two lip screws at z = +-this
    face_screw_y: float = -68.0       # one face screw through the plate (21 mm above the 2x4's bottom edge)

    # ---- derived geometry ----
    @property
    def seat_y(self):
        """Height of the arm's top surface where it meets the tip's inside face (before the crook fillet)."""
        return self.lip_t - (self.reach - self.plate_t) * math.tan(math.radians(self.top_slope_deg))

    def outline(self):
        """Profile polygon (CCW) and the fillet radius for each vertex (0 = sharp)."""
        p = self
        s = p.seat_y
        pts = [
            ((-p.lip_depth, 0.0), p.corner_r),                       # lip back, bottom
            ((0.0, 0.0), -p.inner_corner_r),                          # 2x4 front-top edge (concave)
            ((0.0, -p.plate_h), p.corner_r),                         # plate back, bottom
            ((p.plate_t, -p.plate_h), p.corner_r),                   # plate front, bottom
            ((p.plate_t, p.belly_y), -p.belly_r),                    # belly root (concave)
            ((p.reach + p.tip_t, s - p.seat_depth), 12.0),           # under the tip
            ((p.reach + p.tip_t, s + p.tip_h), p.tip_t / 2 - 0.5),   # tip top, outside
            ((p.reach, s + p.tip_h), p.tip_t / 2 - 0.5),             # tip top, inside
            ((p.reach, s), -p.crook_r),                              # crook (concave)
            ((p.plate_t, p.lip_t), 10.0),                            # arm top meets the lip top (shallow)
            ((-p.lip_depth, p.lip_t), p.corner_r),                   # lip back, top
        ]
        return pts

    def derived(self) -> dict:
        s = self.seat_y
        return {
            "seat_y": round(s, 1),
            "tip_top_y": round(s + self.tip_h, 1),
            "reach_from_wall": round(self.reach + self.board_depth, 1),
            "overall_out_from_board": round(self.reach + self.tip_t, 1),
            "overall_height": round(s + self.tip_h + self.plate_h, 1),
            "root_depth": round(self.lip_t - self.belly_y, 1),
        }

    def report_params(self) -> dict:
        d = asdict(self)
        d.update(self.derived())
        return d


def build_hook(p: HookParams):
    """The hook in the profile frame (see the module docstring)."""
    pts = p.outline()
    with BuildPart() as part:
        with BuildSketch() as sk:
            Polygon(*[q for q, _ in pts], align=None)
            for q, r in pts:
                if r:
                    v = min(sk.vertices(), key=lambda v: (Vector(v) - Vector(q[0], q[1], 0)).length)
                    fillet(v, abs(r))
        extrude(amount=p.width / 2, both=True)
        side_edges = part.edges().group_by(Axis.Z)
        chamfer(side_edges[0] + side_edges[-1], p.edge_chamfer)

        # Screw holes are horizontal when printed, so they get a teardrop point toward +z (up, away from the bed):
        # a square of side r turned 45 deg, with its bottom corner on the hole axis, so its top sides are tangent.
        r = p.screw_hole_d / 2
        off = r / math.sqrt(2)
        L = 60.0
        with BuildPart(mode=Mode.SUBTRACT):
            for dz in (-p.lip_screw_dz, p.lip_screw_dz):        # lip screws: vertical (along y)
                with Locations(Location((p.lip_screw_x, 0, dz))):
                    Cylinder(r, L, rotation=(90, 0, 0))
                with Locations(Location((p.lip_screw_x, 0, dz + off), (0, 45, 0))):
                    Box(r, L, r)
            with Locations(Location((0, p.face_screw_y, 0))):    # face screw: horizontal (along x)
                Cylinder(r, L, rotation=(0, 90, 0))
            with Locations(Location((0, p.face_screw_y, off), (45, 0, 0))):
                Box(L, r, r)
    return part.part


def to_world(vertices):
    """Profile frame -> world (Z-up) for numpy vertex arrays: X along the 2x4, Y out from its face, Z up."""
    return vertices[:, [2, 0, 1]]


def print_pose(solid):
    """Lying on its side (profile flat on the bed), footprint centred, resting on Z = 0."""
    bb = solid.bounding_box()
    return solid.moved(Location((-(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z)))
