"""Parametric side-hanging cup holder for the MAC wagon's right-hand side rail (build123d).

Design (see README for the reasoning):
  * A C-shaped clip wraps the round side rail (22.3 mm), mouth facing down. It snaps
    on (the mouth is narrower than the rail), and two ears with an M4 bolt clamp it so
    it can't rotate. Clamping is essential here: the cup hangs off the side of the
    rail, so its weight is a constant twist on the clip (~0.7-1 N*m), far more than
    snap-fit friction.
  * A shelf runs outward from the top of the clip, a vertical web drops down along the
    outside of the rail, and a floor plate + tapered pocket for the 20 oz Yeti hang
    off the web, outboard of the rail, with the cup base `floor_drop` below the rail.

The model is built in the PRINT frame, not the use frame:

    Z  = the rail axis (clip bore). In use this is horizontal, fore-aft.
    Y  = the cup axis, pointing up out of the pocket. In use this is vertical.
    X  = outward from the rail, toward the cup (in use: away from the wagon's side)
    Z=0 is the bed.

Printing this way keeps the clip's layer lines running around the ring (strong
when it flexes), and every plate (shelf, web, floor) is a prism extruded along Z
or Y, so it stands on the bed with no overhangs. The pocket lies on its side on a
45-degree teardrop foot with an open side. No supports are needed.

Origin: the rail axis is at X=0, Y=0 (running along Z). The cup axis is at
X=pocket_cx, Z=cup_zc (running along +Y). The clip mouth faces -Y (down in use).
"""

import math
from dataclasses import dataclass

from build123d import (Align, Box, BuildSketch, Circle, Cone, Cylinder, Locations, Plane, Polygon,
                       Pos, RegularPolygon, Rotation, extrude)


@dataclass(frozen=True)
class CupHolderParams:
    # --- Side rail (owner measured ~22.3 mm round tube; assumed the same on the rail) ---
    bar_d: float = 22.3
    bar_clearance: float = 0.2      # on the diameter. The printed bore shrinks ~0.2 mm
    clip_wall: float = 2.8          # ring wall. Thinner = easier snap, thicker = stiffer
    clip_len: float = 70.0          # along the rail (owner has ~120 mm free)
    mouth_width: float = 20.7       # opening between the lips. Narrower than the rail to snap

    # --- Clamp ears + bolt (M4 x 35 and an M4 nut) ---
    ear_t: float = 8.0              # ear thickness (X), either side of the mouth
    bolt_drop: float = 6.5          # bolt axis below the rail's lowest point
    bolt_hole_d: float = 4.5        # M4 clearance, teardrop-shaped so it prints without support
    head_cbore_d: float = 8.4       # socket-head cap screw pocket
    head_cbore_depth: float = 4.4
    nut_af: float = 7.3             # M4 nut is 7.0 across flats, plus clearance
    nut_depth: float = 3.8          # M4 nut is 3.2 thick
    lead_in: float = 3.5            # 45-degree guide at the bottom of the mouth
    window_d: float = 12.0          # hex-key access hole through the web, in line with the bolt

    # --- Shelf / web (carries the cup out and down from the clip) ---
    web_gap: float = 24.0           # rail axis to the inner face of the web (clears the ears + bolt tip)
    web_t: float = 6.5
    shelf_t: float = 6.5            # thickness of the shelf joining the clip to the web

    # --- 20 oz Yeti Rambler (retailer figures, NOT yet measured on the owner's cup) ---
    cup_base_d: float = 70.0        # 2.75 in base
    cup_top_d: float = 89.0         # 3.5 in at the lid, the widest point
    cup_h: float = 165.0            # base to the widest point, sets the taper
    pocket_depth: float = 80.0      # how far up the cup the pocket holds it
    pocket_clearance: float = 2.0   # on the diameter, at every height

    # --- Pocket / floor ---
    cup_wall: float = 3.2
    floor_t: float = 6.5
    floor_drop: float = 60.0        # cup base this far below the rail axis (rim must stay above the shelf)
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
        """Y of the pocket floor (where the cup base sits), below the rail axis."""
        return -self.floor_drop

    @property
    def bolt_y(self) -> float:
        return -(self.bar_d / 2 + self.bolt_drop)

    @property
    def ear_bottom_y(self) -> float:
        nut_ac = self.nut_af / math.cos(math.radians(30))   # across corners
        return self.bolt_y - nut_ac / 2 - 2.4

    @property
    def bolt_z(self) -> float:
        return self.clip_len / 2

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

    @property
    def pocket_cx(self) -> float:
        """X of the cup axis: the pocket's outer wall is tangent to the web's inner face."""
        return self.web_gap + self.outer_r


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
    """Bore + mouth (with lead-in) + bolt hole, head pocket (+X ear) and nut slot (-X ear)."""
    w = p.mouth_width / 2
    bore = Pos(0, 0, -1) * Cylinder(p.bore_r, length + 2, align=(Align.CENTER, Align.CENTER, Align.MIN))

    yb = p.ear_bottom_y
    li = p.lead_in
    with BuildSketch(Plane.XY.offset(-1)) as sk:
        Polygon((-w, 0), (w, 0), (w, yb + li), (w + li, yb - 0.1),
                (-(w + li), yb - 0.1), (-w, yb + li), align=None)
    mouth = extrude(sk.sketch, length + 2)

    zb = length / 2

    def teardrop(r):
        """Circle with a 45-degree point on top (+Z), so a horizontal hole prints without support."""
        k = r / math.sqrt(2)
        Circle(r)
        Polygon((-k, k), (k, k), (0, r * math.sqrt(2)), align=None)

    def cut_along_x(x0, depth, draw):
        with BuildSketch(Plane.YZ.offset(x0)) as sk:
            with Locations((p.bolt_y, zb)):
                draw()
        return extrude(sk.sketch, depth)

    x_out = w + p.ear_t
    hole = cut_along_x(-x_out - 1, 2 * x_out + 2, lambda: teardrop(p.bolt_hole_d / 2))
    # Screw head sits in a pocket on the +X (outboard) ear, reached through the web window.
    head = cut_along_x(x_out - p.head_cbore_depth, p.head_cbore_depth + 1,
                       lambda: teardrop(p.head_cbore_d / 2))
    # The nut slides in from the bottom of the -X ear into a hex pocket with a flat top,
    # so it only bridges ~4 mm. The slot below it is open to the ear's bottom end.
    nut_ac = p.nut_af / math.cos(math.radians(30))
    nut = cut_along_x(-x_out - 1, p.nut_depth + 1,
                      lambda: RegularPolygon(nut_ac / 2, 6, rotation=0))
    slot_h = yb - 1.0 - p.bolt_y  # negative: slot runs from the nut centre down past the ear's end
    slot = Pos(-x_out - 1 + (p.nut_depth + 1) / 2, p.bolt_y + slot_h / 2, zb) * Box(
        p.nut_depth + 1, abs(slot_h), p.nut_af)
    return bore, mouth, hole, head, nut, slot


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


def _prism_z(draw, z0: float, z1: float):
    """Extrude a 2D shape drawn in world (x, y) so it spans Z = z0..z1."""
    with BuildSketch(Plane.XY.offset(z0)) as sk:
        draw()
    return extrude(sk.sketch, amount=z1 - z0)


def build(p: CupHolderParams | None = None):
    p = p or CupHolderParams()
    R, zc, cx, yf = p.outer_r, p.cup_zc, p.pocket_cx, p.floor_y
    y_plate0 = yf - p.floor_t
    y_end = yf + p.pocket_depth

    # Floor plate + pocket wall: the teardrop silhouette (circle with 45-degree tangents down
    # to a flat foot on the bed), extruded along +Y.
    a = R * (math.sqrt(2) - 1)  # half-width of the flat foot
    s = R / math.sqrt(2)

    def teardrop():
        with Locations((cx, zc)):
            Circle(R)
        Polygon((cx - a, 0), (cx + a, 0), (cx + s, zc - s), (cx, zc), (cx - s, zc - s), align=None)

    body = _extrude_y(teardrop, y_plate0, y_end)

    # Web: a vertical plate (a prism along Z) from the floor up to the shelf, tangent to the pocket.
    shelf_y1 = p.clip_r_out
    shelf_y0 = shelf_y1 - p.shelf_t
    x_web1 = p.web_gap + p.web_t

    def web_profile():
        Polygon((p.web_gap, y_plate0), (x_web1, y_plate0), (x_web1, shelf_y1), (p.web_gap, shelf_y1), align=None)

    web = _prism_z(web_profile, 0.0, 2 * R)

    # Shelf: joins the top of the clip to the web (a prism along Z, the clip's length).
    def shelf_profile():
        Polygon((0, shelf_y0), (x_web1, shelf_y0), (x_web1, shelf_y1), (0, shelf_y1), align=None)

    shelf = _prism_z(shelf_profile, 0.0, p.clip_len)

    # Pocket cavity: a cone along +Y rising from the floor.
    r0, r1 = p.pocket_r(0), p.pocket_r(p.pocket_depth + 2)
    cone = Cone(r0, r1, p.pocket_depth + 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cavity = Pos(cx, yf, zc) * (Rotation(-90, 0, 0) * cone)

    # Side opening facing +Z: leaves wrap_deg of wall around the cup, cut above the floor only.
    half = (360.0 - p.wrap_deg) / 2
    far = 4 * R
    fan = [(cx, zc)] + [(cx + far * math.sin(math.radians(ang)), zc + far * math.cos(math.radians(ang)))
                        for ang in (-half, -half / 2, 0, half / 2, half)]

    def sector():
        Polygon(*fan, align=None)

    opening = _extrude_y(sector, yf, y_end + 5)

    # Hex-key window through the web, in line with the bolt (reached from inside the empty pocket).
    r = p.window_d / 2
    k = r / math.sqrt(2)
    xw0 = p.ear_t + p.mouth_width / 2 + 0.5

    def window_shape():
        with Locations((p.bolt_y, p.bolt_z)):
            Circle(r)
            Polygon((-k, k), (k, k), (0, r * math.sqrt(2)), align=None)

    with BuildSketch(Plane.YZ.offset(xw0)) as sk:
        window_shape()
    window = extrude(sk.sketch, x_web1 + p.web_t - xw0)

    # The clip is solid here. Its bore, mouth and bolt are cut last, so the shelf merges
    # with the ring wall without ever entering the bore.
    part = body + web + shelf + _clip_solid(p, p.clip_len) - cavity - opening - window
    for cut in _clip_cuts(p, p.clip_len):
        part = part - cut
    return part
