"""Parametric cup holder that clamps onto the MAC wagon's push bar (build123d).

Design (see README for the reasoning):
  * A C-shaped clip wraps the round push bar (22.3 mm) over its top, mouth facing down.
    It snaps on (the mouth is narrower than the bar) and holds itself in place.
  * Two ears flank the mouth and an M4 bolt across them clamps the clip onto the bar.
    Without it the clip can rotate on the bar: a cup standing above the bar is an
    inverted pendulum, and snap-fit friction alone is ~10x too weak to hold it.
  * A floor plate sits on top of the clip and a tapered pocket for the 20 oz Yeti
    rises from it. The cup stands directly over the bar, so its weight goes straight
    down through the clip and there's no static twisting torque on the bar.

The model is built in the PRINT frame, not the use frame:

    Z  = the bar axis (clip bore). In use this is horizontal, along the bar.
    Y  = the cup axis, pointing up out of the pocket. In use this is vertical.
    X  = across the pocket (in use: toward/away from the pusher)
    Z=0 is the bed.

Printing this way keeps the clip's layer lines running around the ring (strong
when it flexes) and puts the pocket on its side with a 45-degree teardrop foot
and an open side, so nothing needs supports. `build.py` rotates it so the longest
footprint axis is X and centres it.

Origin: the bar axis is at X=0, Y=0 (running along Z). The cup axis is at
X=0, Z=cup_zc (running along +Y). The clip mouth faces -Y.
"""

import math
from dataclasses import dataclass

from build123d import (Align, BuildSketch, Circle, Cone, Cylinder, Locations, Plane, Polygon,
                       Pos, RegularPolygon, Rotation, extrude)


@dataclass(frozen=True)
class CupHolderParams:
    # --- Push bar (owner measured ~22.3 mm round tube) ---
    bar_d: float = 22.3
    bar_clearance: float = 0.2      # on the diameter. The printed bore shrinks ~0.2 mm
    clip_wall: float = 2.8          # ring wall. Thinner = easier snap, thicker = stiffer
    clip_len: float = 70.0          # along the bar (owner has ~120 mm free)
    mouth_width: float = 20.7       # opening between the lips. Narrower than the bar to snap

    # --- Clamp ears + bolt (M4 x 35 and an M4 nut) ---
    ear_t: float = 8.0              # ear thickness (X), either side of the mouth
    bolt_drop: float = 6.5          # bolt axis below the bar's lowest point
    bolt_hole_d: float = 4.5        # M4 clearance, teardrop-shaped so it prints without support
    head_cbore_d: float = 8.4       # socket-head cap screw pocket
    head_cbore_depth: float = 4.4
    nut_af: float = 7.3             # M4 nut is 7.0 across flats, plus clearance
    nut_depth: float = 3.8          # M4 nut is 3.2 thick
    lead_in: float = 3.5            # 45-degree guide at the bottom of the mouth

    # --- 20 oz Yeti Rambler (retailer figures, NOT yet measured on the owner's cup) ---
    cup_base_d: float = 70.0        # 2.75 in base
    cup_top_d: float = 89.0         # 3.5 in at the lid, the widest point
    cup_h: float = 165.0            # base to the widest point, sets the taper
    pocket_depth: float = 80.0      # how far up the cup the pocket holds it
    pocket_clearance: float = 2.0   # on the diameter, at every height

    # --- Pocket / floor ---
    cup_wall: float = 3.2
    floor_t: float = 6.5            # floor plate thickness above the clip
    wrap_deg: float = 250.0         # how far the pocket wall wraps the cup (>180 holds it)

    # --- Derived ---
    @property
    def bore_r(self) -> float:
        return (self.bar_d + self.bar_clearance) / 2

    @property
    def clip_r_out(self) -> float:
        return self.bore_r + self.clip_wall

    @property
    def floor_y(self) -> float:
        """Y of the pocket floor (where the cup base sits)."""
        return self.clip_r_out + self.floor_t - 1.5  # plate overlaps the ring by 1.5 mm

    @property
    def bolt_y(self) -> float:
        return -(self.bar_d / 2 + self.bolt_drop)

    @property
    def ear_bottom_y(self) -> float:
        nut_ac = self.nut_af / math.cos(math.radians(30))   # across corners, vertex up
        return self.bolt_y - nut_ac / 2 - 2.4

    def pocket_r(self, depth: float) -> float:
        """Inner radius of the pocket `depth` mm above the floor."""
        taper = (self.cup_top_d - self.cup_base_d) / self.cup_h
        return (self.cup_base_d + taper * depth + self.pocket_clearance) / 2

    @property
    def outer_r(self) -> float:
        return self.pocket_r(self.pocket_depth) + self.cup_wall

    @property
    def cup_zc(self) -> float:
        """Z of the cup axis. The pocket sits on the bed (teardrop foot)."""
        return self.outer_r


# --------------------------------------------------------------------------------------
# Clip (C ring + ears + bolt)
# --------------------------------------------------------------------------------------

def _clip_solid(p: CupHolderParams, length: float):
    """Solid ring + ears, before the bore, mouth and bolt are cut."""
    w = p.mouth_width / 2
    ring = Cylinder(p.clip_r_out, length, align=(Align.CENTER, Align.CENTER, Align.MIN))
    y_top, y_bot = -4.0, p.ear_bottom_y
    with BuildSketch(Plane.XY) as sk:
        for s in (-1, 1):
            x0, x1 = sorted((s * w, s * (w + p.ear_t)))
            Polygon((x0, y_top), (x1, y_top), (x1, y_bot), (x0, y_bot), align=None)
    return ring + extrude(sk.sketch, length)


def _clip_cuts(p: CupHolderParams, length: float):
    """Bore + mouth (with lead-in) + bolt hole, head pocket and nut trap."""
    w = p.mouth_width / 2
    bore = Pos(0, 0, -1) * Cylinder(p.bore_r, length + 2, align=(Align.CENTER, Align.CENTER, Align.MIN))

    yb = p.ear_bottom_y
    li = p.lead_in
    with BuildSketch(Plane.XY.offset(-1)) as sk:
        Polygon((-w, 0), (w, 0), (w, yb + li), (w + li, yb - 0.1),
                (-(w + li), yb - 0.1), (-w, yb + li), align=None)
    mouth = extrude(sk.sketch, length + 2)

    # Bolt, head pocket and nut trap all lie along X at (y = bolt_y, z = length/2).
    def teardrop(r):
        """Circle with a 45-degree point on top (+Z), so a horizontal hole prints without support."""
        k = r / math.sqrt(2)
        Circle(r)
        Polygon((-k, k), (k, k), (0, r * math.sqrt(2)), align=None)

    def cut_along_x(x0, depth, draw):
        with BuildSketch(Plane.YZ.offset(x0)) as sk:
            with Locations((p.bolt_y, length / 2)):
                draw()
        return extrude(sk.sketch, depth)

    x_out = w + p.ear_t
    hole = cut_along_x(-x_out - 1, 2 * x_out + 2, lambda: teardrop(p.bolt_hole_d / 2))
    head = cut_along_x(-x_out - 1, p.head_cbore_depth + 1, lambda: teardrop(p.head_cbore_d / 2))
    # Hex nut with a flat top (rotation 0 puts flats up/down), so it only bridges ~4 mm.
    nut = cut_along_x(x_out - p.nut_depth, p.nut_depth + 1,
                      lambda: RegularPolygon(p.nut_af / 2 / math.cos(math.radians(30)), 6, rotation=0))
    return bore, mouth, hole, head, nut


def build_clip(p: CupHolderParams, length: float | None = None):
    """Just the clip, for the short fit-test print."""
    length = p.clip_len if length is None else length
    part = _clip_solid(p, length)
    for cut in _clip_cuts(p, length):
        part = part - cut
    return part


# --------------------------------------------------------------------------------------
# Pocket + full part
# --------------------------------------------------------------------------------------

def _extrude_y(draw, y0: float, y1: float):
    """Extrude a 2D shape drawn in (x, z) world coordinates so it spans Y = y0..y1.

    `draw` runs inside a BuildSketch on the XY plane, where the sketch's (x, y) stand
    for world (x, z). Rotating by +90 deg about X sends local z -> world -Y and local
    y -> world +Z, so sketching at local z = -y1 and extruding by (y1 - y0) gives Y in [y0, y1].
    """
    with BuildSketch(Plane.XY.offset(-y1)) as sk:
        draw()
    return Rotation(90, 0, 0) * extrude(sk.sketch, amount=y1 - y0)


def build(p: CupHolderParams | None = None):
    p = p or CupHolderParams()
    R, zc, yf = p.outer_r, p.cup_zc, p.floor_y
    y_plate0 = yf - p.floor_t
    y_end = yf + p.pocket_depth

    # Plate + pocket wall: the teardrop silhouette (circle with 45-degree tangents down
    # to a flat foot on the bed), extruded along +Y.
    a = R * (math.sqrt(2) - 1)  # half-width of the flat foot
    s = R / math.sqrt(2)

    def teardrop():
        with Locations((0, zc)):
            Circle(R)
        Polygon((-a, 0), (a, 0), (s, zc - s), (0, zc), (-s, zc - s), align=None)

    body = _extrude_y(teardrop, y_plate0, y_end)

    # Pocket cavity: a cone along +Y rising from the floor.
    r0, r1 = p.pocket_r(0), p.pocket_r(p.pocket_depth + 2)
    cone = Cone(r0, r1, p.pocket_depth + 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cavity = Pos(0, yf, zc) * (Rotation(-90, 0, 0) * cone)

    # Side opening facing +Z: leaves wrap_deg of wall around the cup, cut above the floor only.
    half = (360.0 - p.wrap_deg) / 2
    far = 4 * R
    fan = [(0, zc)] + [(far * math.sin(math.radians(ang)), zc + far * math.cos(math.radians(ang)))
                       for ang in (-half, -half / 2, 0, half / 2, half)]

    def sector():
        Polygon(*fan, align=None)

    opening = _extrude_y(sector, yf, y_end + 5)

    # The clip is solid here. Its bore, mouth and bolt are cut last, so the floor plate
    # merges with the ring wall without ever entering the bore.
    part = body + _clip_solid(p, p.clip_len) - cavity - opening
    for cut in _clip_cuts(p, p.clip_len):
        part = part - cut
    return part
