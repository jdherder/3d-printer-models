"""Parametric model of a 1/4" pegboard hook: a bent round wire with a welded anti-rotation pin.

Coordinates while modelling ("use frame", as the hook hangs on the board, seen from the side):
  x = out from the board (the board's front face is at x = -wire_r, the hook's back leg sits against it)
  y = up
  z = across the hook (the wire's centreline lies in z = 0)
The origin is the sharp corner where the back leg meets the arm (the intersection of their centrelines).

The wire path, from the top tip down (all centreline points, mm):
  tip_top   top end of the short leg that goes through the board and rises behind it
  jog_back  corner behind the board, where that leg turns into the sloped jog
  jog_front corner in front of the board, where the jog turns down into the back leg
  corner    bottom of the back leg, where the arm starts
  arm_end   free end of the arm
All corners use one bend radius. The pin is a separate straight stub, welded to the back leg and pointing into the board
(it sits in the hole one pitch below the jog and stops the hook rotating out).

Values come from the owner's photos (2026-11-05, tape scale ~9.65 px/mm) and one caliper reading (wire 5.53 mm),
so positions are good to roughly +-1 mm. See the project README.
"""

from dataclasses import asdict, dataclass

from build123d import (Axis, Box, BuildLine, BuildPart, BuildSketch, Circle, Cylinder, FilletPolyline, Location, Mode,
                       Plane, Vector, sweep)


@dataclass
class HookParams:
    wire_d: float = 5.53              # caliper (owner)
    pin_d: float = 5.53               # looks like the same wire in the photos (~5.5 mm)
    bend_r: float = 4.5               # centreline bend radius at every corner (inner radius ~1.7 mm)

    tip_top: tuple = (-12.85, 52.3)   # top end of the behind-board leg
    jog_back: tuple = (-12.85, 40.3)  # behind-board corner (jog slopes ~26 deg down toward the front)
    jog_front: tuple = (0.0, 34.1)    # front corner, top of the back leg
    arm_end: tuple = (41.0, 9.2)      # arm rises ~13 deg above horizontal

    pin_y: float = 13.0               # pin axis height above the bottom corner
    pin_tip_x: float = -9.8           # pin sticks ~7 mm into the board past the back leg's surface

    print_flat: float = 0.4           # mm shaved off the bed side so a round wire has a flat first layer (3.1 mm wide)

    @property
    def wire_r(self):
        return self.wire_d / 2

    def derived(self) -> dict:
        """Numbers worth showing the owner (mm / deg)."""
        import math
        ax, ay = self.arm_end
        jx0, jy0 = self.jog_back
        jx1, jy1 = self.jog_front
        return {
            "arm_length": round(math.hypot(ax, ay), 1),
            "arm_angle_deg": round(math.degrees(math.atan2(ay, ax)), 1),
            "arm_reach_from_board": round(ax + self.wire_r, 1),
            "jog_angle_deg": round(math.degrees(math.atan2(jy0 - jy1, jx1 - jx0)), 1),
            "board_gap_behind_back_leg": round(-jx0 - 2 * self.wire_r, 1),   # max board thickness the hook accepts
            "pin_protrusion": round(-self.pin_tip_x - self.wire_r, 1),
        }

    def report_params(self) -> dict:
        d = {k: v for k, v in asdict(self).items()}
        d.update(self.derived())
        return d


def path_points(p: HookParams):
    return [Vector(*p.tip_top, 0), Vector(*p.jog_back, 0), Vector(*p.jog_front, 0), Vector(0, 0, 0),
            Vector(*p.arm_end, 0)]


def build_hook(p: HookParams):
    """The hook in the use frame, full round wire (no print flat)."""
    pts = path_points(p)
    start_dir = (pts[1] - pts[0]).normalized()
    with BuildPart() as part:
        with BuildLine() as path:
            FilletPolyline(*pts, radius=p.bend_r)
        with BuildSketch(Plane(origin=pts[0], z_dir=start_dir)):
            Circle(p.wire_r)
        sweep(path=path.wires()[0])
        pin_len = -p.pin_tip_x
        with BuildPart(mode=Mode.ADD):
            with BuildPart(Location((-pin_len / 2, p.pin_y, 0))):
                Cylinder(p.pin_d / 2, pin_len, rotation=(0, 90, 0))
    return part.part


def use_to_board(solid, p: HookParams):
    """Use frame -> the shared board frame (tools/pegboard.py): front face at x = 0, the pin's hole centre at the origin."""
    return solid.moved(Location((p.wire_r, -p.pin_y, 0)))


def print_pose(solid, p: HookParams):
    """Lay the hook on its side for printing: profile in XY, shave `print_flat` off the bottom, rest it on Z = 0,
    centre the footprint on the origin. The use frame's x/y become the bed's X/Y (X is the longer footprint axis)."""
    r = p.wire_r
    if p.print_flat > 0:
        big = 400.0
        cutter = Box(big, big, big).locate(Location((0, 0, -r + p.print_flat - big / 2)))
        solid = solid - cutter
    bb = solid.bounding_box()
    return solid.moved(Location((-(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z)))
