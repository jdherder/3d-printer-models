"""Parametric wall hook that hangs a bike vertically by its front rim, with the bike perpendicular to the wall, the
front wheel straight, and both tires resting against the pegboard ("riding up the wall").

Why it's shaped like this: with the wheel straight and its tire on the wall, nothing coming straight out of the wall can
reach the rim without going through the tire. So the arm comes out *beside* the wheel, and a bar turns 90 deg and reaches
sideways through the spokes, just inside the rim. The rim rests on the bar's upper, wall-side edge, about 50 deg down
from the top of the wheel. There, the rim's push on the bar points through the hub, so the wheel hangs still whether or not
it is free to spin. The same push pulls the wheel toward the wall, which presses the tire flat against the pegboard.
You hang the bike by lifting the front wheel a little, sliding it sideways onto the bar, and letting it down.

World frame (Z-up), used for modelling:
  X = along the wall (the bar points +X, the arm is on the -X side of the wheel)
  Y = out from the pegboard's front face (Y = 0); the 2x4 is behind the pegboard
  Z = up
  The origin is a pegboard hole centre. Screws go through pegboard holes (1 in grid) into the 2x4 behind, in three rows
  (z = +25.4, 0, -25.4) so the hook works whether 2 or 3 hole rows land over the 2x4 (see `install_patterns`).

Print pose: lying on the arm's outer side (the X = x_min face on the bed). Plate, arm and bar all grow straight up
from the bed, and the tip leans out at 45 deg, so it needs no supports.
"""

import math
from dataclasses import asdict, dataclass

from build123d import (Align, Axis, Box, BuildPart, BuildSketch, Circle, Cylinder, Location, Locations, Mode, Plane,
                       Polygon, SlotCenterToCenter, Text, Vector, add, chamfer, extrude, fillet)

PITCH = 25.4


@dataclass
class HookParams:
    # --- wheel the slot is sized for ---
    tire_max_w: float = 50.0          # widest tire the arm clears (2 in). A 2.4 in MTB tire needs ~62
    rim_max_w: float = 30.0           # widest rim (outer) the slot between the arm and the tip takes

    # --- plate on the pegboard (screws through pegboard holes into the 2x4; 8 holes in 3 rows, see `screws`) ---
    plate_t: float = 12.0
    plate_z: float = 40.0             # plate spans z = -plate_z .. +plate_z (screw rows at +-PITCH)
    plate_chamfer: float = 5.0       # 45 deg round the plate's front edges (not the arm side). Also clears small wheels' tires,
                                      # which rest on the board just below the plate and curve away from it
    plate_corner_r: float = 10.0      # rounded outline corners on the side away from the arm (they print at the top)
    plate_corner_cut: float = 8.0     # the corner above the arm prints on the bed, so it's cut at 45 deg instead of rounded
    screw_hole_d: float = 6.0         # #10 or #12 screws (they also pass the 1/4 in pegboard holes)
    head_d: float = 12.7              # washer/pan head, for the clearance checks
    cbore_d: float = 13.6             # counterbore so the heads sit flush (#10 washer/pan heads are 9.5-12.7)
    cbore_depth: float = 3.0          # leaves 9 mm under the head; a 2 in screw then reaches ~38 mm into the 2x4
    label: str = "ADULT"              # pressed into the plate's face so the variants can't get mixed up
    label_size: float = 8.0

    # --- arm (beside the wheel, along Y) ---
    arm_w: float = 28.0               # in X
    arm_root_z: float = -40.0         # arm underside at the plate (deep root), tapering up to the bar's underside
    arm_taper_end_y: float = 95.0     # where the taper reaches the bar's underside

    # --- bar (through the spokes, along X) ---
    # Its section (in Y, Z) is a slot whose long axis points at the wheel's hub: the rim's push on the bar points there too
    # (so the bar is deepest the way it's loaded), and so do the spokes (so it's narrow across the gap between two spokes).
    # The slot's upper rounded end is the rim seat.
    seat_y: float = 118.0             # seat centre, out from the pegboard. Sets where the rim sits: ~53 deg round from the top
                                      # on a 700x38, 59 deg on a 29x2.4. Closer to the wall, that angle grows and the rim's
                                      # pull on the screws (weight x tan angle) climbs fast
    seat_z: float = 5.0               # seat centre height (screw rows at +-25.4 must stay clear of the bar)
    seat_r: float = 13.0              # slot half-width = seat radius (bar is 26 mm across the spoke gap)
    bar_len: float = 18.0             # slot centre-to-centre length (bar is 44 mm deep along the load)
    bar_angle_deg: float = 55.0       # slot axis, from vertical toward the wall (the rim's contact angle, roughly)
    tip_rise: float = 18.0            # tip ramps up this far above the bar at 45 deg (prints without supports)
    tip_top: float = 8.0              # flat on top of the tip
    side_gap: float = 6.0             # clearance between the widest tire and the arm, and the widest rim and the tip (x2 for rim)

    @property
    def x_arm_in(self):
        """Arm's inner (+X) face: one head radius + 4 mm left of the screw column at X = 0, so the driver clears."""
        return -(self.head_d / 2 + 4.0)

    @property
    def x_min(self):
        return self.x_arm_in - self.arm_w

    @property
    def x_wheel(self):
        """Nominal wheel centre plane: the widest tire just clears the arm."""
        return self.x_arm_in + self.tire_max_w / 2 + self.side_gap

    @property
    def x_tip(self):
        """Where the tip's 45 deg ramp starts."""
        return self.x_wheel + self.rim_max_w / 2 + self.side_gap

    @property
    def x_max_bar(self):
        return self.x_tip + self.tip_rise + self.tip_top

    @property
    def x_max_plate(self):
        return 3 * PITCH + self.cbore_d / 2 + 7.0

    @property
    def contact_centre(self):
        """(y, z) of the seat's centre (the rim sits on this rounded end of the bar)."""
        return (self.seat_y, self.seat_z)

    @property
    def contact_r(self):
        return self.seat_r

    @property
    def bar_u(self):
        """Unit (y, z) along the slot, from its lower end toward the seat (points away from the hub)."""
        a = math.radians(self.bar_angle_deg)
        return (-math.sin(a), math.cos(a))

    @property
    def bar_low_centre(self):
        uy, uz = self.bar_u
        return (self.seat_y - self.bar_len * uy, self.seat_z - self.bar_len * uz)

    @property
    def z_top(self):
        return self.seat_z + self.seat_r

    @property
    def z_bar_bottom(self):
        return self.bar_low_centre[1] - self.seat_r

    @property
    def screws(self):
        """(x, z) of every screw hole, all on pegboard holes, in three rows 1 in apart. A driver can reach each one straight on:
        the bar and arm block the middle row everywhere except past the bar's far end, so the middle row has one hole, at
        3 in. The arm's deep root also covers the bottom row's hole under it."""
        top = [(-PITCH, PITCH), (0.0, PITCH), (PITCH, PITCH), (3 * PITCH, PITCH)]
        mid = [(3 * PITCH, 0.0)]
        bottom = [(0.0, -PITCH), (PITCH, -PITCH), (3 * PITCH, -PITCH)]
        return top + mid + bottom

    @property
    def install_patterns(self):
        """Which holes get screws, depending on how many hole rows are over the 2x4 (its face is 3.5 in, so either 2 or 3
        rows are, depending on where the hole grid falls). With 2, mount the hook so its top and middle rows are on them:
        top + bottom would put the screws below the load and they'd pull out far harder."""
        return {
            "three_rows_over_2x4": self.screws,
            "two_rows_over_2x4_top_and_middle": [s for s in self.screws if s[1] >= 0],
        }

    def derived(self) -> dict:
        return {
            "x_arm_inner_face": round(self.x_arm_in, 1),
            "x_wheel_nominal": round(self.x_wheel, 1),
            "slot_arm_to_tip": round(self.x_tip - self.x_arm_in, 1),
            "reach_to_seat": round(self.seat_y, 1),
            "reach_overall": round(self.bar_low_centre[0] + self.seat_r, 1),
            "bar_across_spokes": round(2 * self.seat_r, 1),
            "bar_along_load": round(self.bar_len + 2 * self.seat_r, 1),
            "overall_x": round(self.x_max_bar - self.x_min, 1),
            "plate_w": round(self.x_max_plate - self.x_min, 1),
            "plate_h": round(2 * self.plate_z, 1),
        }

    def report_params(self) -> dict:
        d = asdict(self)
        d.update(self.derived())
        return d


def build_hook(p: HookParams):
    """The hook in the world frame (see the module docstring)."""
    (c1y, c1z), (c2y, c2z) = p.contact_centre, p.bar_low_centre
    r = p.seat_r
    ztop, zbot = p.z_top, p.z_bar_bottom
    with BuildPart() as part:
        # Plate on the pegboard (built on its own so its edges can be chamfered cleanly)
        add(_plate(p))

        # Arm: side profile (Y, Z) extruded along X over the arm's width. Its top is level with the seat's top; it runs
        # out to the bar, which it merges into.
        prof = [(p.plate_t - 1, ztop), (c1y, ztop), (c2y, zbot + 1), (p.arm_taper_end_y, zbot + 1),
                (p.plate_t - 1, p.arm_root_z)]
        with BuildSketch(Plane(origin=(p.x_min, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))) as sk:
            Polygon(*prof, align=None)
            v = min(sk.vertices(), key=lambda v: (Vector(v) - Vector(p.x_min, p.arm_taper_end_y, zbot + 1)).length)
            fillet(v, 25.0)
        extrude(amount=p.arm_w)

        # Bar: slot section (Y, Z) pointing at the hub, extruded along X from the arm's outer face to past the tip.
        uy, uz = p.bar_u
        with BuildSketch(Plane(origin=(p.x_min, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))):
            with Locations(((c1y + c2y) / 2, (c1z + c2z) / 2)):
                SlotCenterToCenter(p.bar_len, 2 * r, rotation=math.degrees(math.atan2(uz, uy)))
        extrude(amount=p.x_max_bar - p.x_min)

        # Tip: 45 deg ramp leaning away from the wheel, on top of the seat end (section in X, Z, extruded along Y).
        tip = [(p.x_tip - 1, c1z), (p.x_max_bar, c1z), (p.x_max_bar, ztop + p.tip_rise),
               (p.x_tip + p.tip_rise, ztop + p.tip_rise), (p.x_tip, ztop)]
        half = 0.8 * r
        with BuildSketch(Plane(origin=(0, c1y - half, 0), x_dir=(1, 0, 0), z_dir=(0, 1, 0))):
            Polygon(*[(x, -z) for x, z in tip], align=None)
        extrude(amount=2 * half)

        # Under the arm, the plate's bottom-edge chamfer would leave a groove between plate and arm: fill it back in.
        c = p.plate_chamfer
        with Locations(Location(((p.x_min + p.x_arm_in) / 2, p.plate_t - (c + 1) / 2, -p.plate_z + (c + 1) / 2))):
            Box(p.x_arm_in - p.x_min, c + 1, c + 1)

        # Screw holes + counterbores through the plate (along Y). They're horizontal when printed, so their tops are
        # truncated teardrops: 45 deg up to a short flat that bridges (they look nearly round from the front).
        for (x, z) in p.screws:
            for r, y0, depth in ((p.screw_hole_d / 2, -1.0, p.plate_t + 2),
                                 (p.cbore_d / 2, p.plate_t - p.cbore_depth, p.cbore_depth + 0.5)):
                with BuildSketch(Plane(origin=(x, y0, z), x_dir=(0, 0, 1), z_dir=(0, 1, 0))):   # local +y = world +X (up)
                    Circle(r)
                    Polygon(*_truncated_teardrop(r), align=None)
                extrude(amount=depth, mode=Mode.SUBTRACT)

        # Label, pressed 0.6 mm into the face between the screw columns, readable from the front (looking at the wall).
        if p.label:
            lx = (PITCH + 3 * PITCH) / 2
            with BuildSketch(Plane(origin=(lx, p.plate_t, 0), x_dir=(-1, 0, 0), z_dir=(0, 1, 0))):
                Text(p.label, font_size=p.label_size, align=(Align.CENTER, Align.CENTER))
            extrude(amount=-0.6, mode=Mode.SUBTRACT)
    return part.part


def _truncated_teardrop(r):
    """Wedge that turns a circle (radius r) into a teardrop pointing +y, cut flat at the circle's top."""
    a, b = r / math.sqrt(2), r * (math.sqrt(2) - 1)
    return [(0.0, 0.0), (a, a), (b, r), (-b, r), (-a, a)]


def _plate(p: HookParams):
    """Plate in world coordinates: outline in X/Z with rounded corners away from the arm and a 45 deg cut on the corner
    above it, chamfered round its front edges except the arm side (where the arm carries on)."""
    x0, x1, zt, k = p.x_min, p.x_max_plate, p.plate_z, p.plate_corner_cut
    with BuildPart() as pl:
        with BuildSketch(Plane(origin=(0, p.plate_t, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))) as sk:   # local y = world Z
            Polygon((x0, -zt), (x1, -zt), (x1, zt), (x0 + k, zt), (x0, zt - k), align=None)
            for q in ((x1, -zt), (x1, zt)):
                v = min(sk.vertices(), key=lambda v: (Vector(v) - Vector(q[0], q[1], 0)).length)
                fillet(v, p.plate_corner_r)
        extrude(amount=p.plate_t)
        front = pl.faces().sort_by(Axis.Y)[-1]
        edges = [e for e in front.edges() if abs(e.center().X - x0) > 1e-3]
        chamfer(edges, p.plate_chamfer)
    return pl.part


def print_pose(solid, p: HookParams):
    """Arm's outer side (X = x_min) on the bed: world X becomes print Z. Footprint centred, longest side along X."""
    s = solid.rotate(Axis.Y, -90)                # world (x, y, z) -> (-z, y, x): world X is now up
    s = s.rotate(Axis.Z, 90)                     # longest footprint side (world Y, 118 mm) along X
    bb = s.bounding_box()
    return s.moved(Location((-(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z)))
