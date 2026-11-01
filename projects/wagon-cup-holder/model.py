"""Parametric side-hanging cup holder for the MAC wagon's right-hand side rail (build123d).

TWO PIECES, so the cup comes off in a couple of seconds for folding the wagon:

  CLIP    stays on the rail. A C-shaped ring (mouth facing down) that snaps on, two ears
          with an M4 bolt that clamp it (tightened ONCE with a hex key), and a boss on the
          outboard side carrying a vertical 45-degree dovetail tongue.
  MODULE  the cup. A block with the matching dovetail groove, a web dropping down the
          outside of the rail, and a floor plate + tapered pocket for the 20 oz Yeti,
          outboard of the rail with the cup base `floor_drop` below it. It drops straight
          down onto the tongue and rests on the tops of the clip's ears, so gravity holds
          it seated, and it lifts straight off. No tool needed.

Why a bolted clamp at all: the cup hangs off the side of the rail, so its weight is a
constant twist on the clip (~0.7 N*m), far more than snap-fit friction. The bolt is set once;
the dovetail then carries that twist as a couple across its 32 mm height.

The model is built in the PRINT frame, not the use frame:

    Z  = the rail axis (clip bore). In use this is horizontal, fore-aft.
    Y  = the cup axis, pointing up out of the pocket. In use this is vertical.
    X  = outward from the rail, toward the cup (in use: away from the wagon's side)
    Z=0 is the bed.

Printing this way keeps the clip's layer lines running around the ring (strong when it flexes),
and every plate and the dovetail are prisms extruded along Z or Y, with 45-degree flanks, so they
need no supports. The pocket lies on its side on a 45-degree teardrop foot with an open side.

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

    # --- Dovetail between clip and module (slides along Y: the module drops on from above) ---
    ear_top_y: float = -4.0         # top of the ears. The module's block rests here
    boss_x0: float = 11.0           # boss on the clip, outboard of the ring (inner edge)
    dt_x0: float = 15.0             # tongue root plane (X)
    dt_h: float = 7.0               # tongue height (X)
    dt_w_root: float = 34.0         # tongue width (Z) at the root. 45-degree flanks widen it by 2*dt_h
    dt_y1: float = 28.0             # top of the tongue and the block (Y). Engagement = dt_y1 - ear_top_y
    dt_clear: float = 0.35          # sliding clearance per side

    # --- Web (carries the cup out and down from the dovetail block) ---
    web_gap: float = 24.0           # rail axis to the inner face of the web (clears the ears + bolt tip)
    web_t: float = 6.5

    # --- 20 oz Yeti Rambler (retailer figures, NOT yet measured on the owner's cup) ---
    cup_base_d: float = 70.0        # 2.75 in base
    cup_top_d: float = 89.0         # 3.5 in at the lid, the widest point
    cup_h: float = 165.0            # base to the widest point, sets the taper
    pocket_depth: float = 80.0      # how far up the cup the pocket holds it
    pocket_clearance: float = 2.0   # on the diameter, at every height

    # --- Pocket / floor ---
    cup_wall: float = 3.2
    floor_t: float = 6.5
    floor_drop: float = 60.0        # cup base this far below the rail axis
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
    y_top, y_bot = p.ear_top_y, p.ear_bottom_y
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
    # Screw head sits in a pocket on the +X (outboard) ear, reached with the module off.
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


def _tongue_profile(p: CupHolderParams, zc: float):
    """Dovetail tongue in the (x, z) plane: narrow at the root, 45-degree flanks flaring outward."""
    w = p.dt_w_root / 2
    x0, h = p.dt_x0, p.dt_h
    return [(x0, zc - w), (x0 + h, zc - w - h), (x0 + h, zc + w + h), (x0, zc + w)]


def build_clip(p: CupHolderParams, length: float | None = None, dovetail: bool = True):
    """The clip that stays on the rail. `dovetail=False` gives the plain ring + ears (clamp test slice)."""
    length = p.clip_len if length is None else length
    part = _clip_solid(p, length)
    if dovetail:
        zc = length / 2

        def boss():
            Polygon((p.boss_x0, p.ear_top_y), (p.dt_x0, p.ear_top_y), (p.dt_x0, p.dt_y1),
                    (p.boss_x0, p.dt_y1), align=None)

        def tongue():
            Polygon(*_tongue_profile(p, zc), align=None)

        part = part + _prism_z(boss, 0.0, length) + _extrude_y(tongue, p.ear_top_y, p.dt_y1)
    for cut in _clip_cuts(p, length):
        part = part - cut
    return part


# --------------------------------------------------------------------------------------
# Cup module (dovetail block + web + floor + pocket)
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


def _dovetail_block(p: CupHolderParams, length: float, y1: float | None = None):
    """The module's dovetail block with its groove (clearance `dt_clear` around the clip's tongue)."""
    y1 = p.dt_y1 if y1 is None else y1
    x_in = p.dt_x0 + p.dt_clear
    x_out = p.web_gap + 2.0                       # merges into the web (24..) and ends clear of the cup

    def block():
        Polygon((x_in, p.ear_top_y), (x_out, p.ear_top_y), (x_out, y1), (x_in, y1), align=None)

    zc = length / 2
    k = 1.414 * p.dt_clear                        # normal clearance on a 45-degree flank

    def hw(x):
        return p.dt_w_root / 2 + (x - p.dt_x0) + k

    xa, xb = p.dt_x0 - 0.5, p.dt_x0 + p.dt_h + p.dt_clear

    def groove():
        Polygon((xa, zc - hw(xa)), (xb, zc - hw(xb)), (xb, zc + hw(xb)), (xa, zc + hw(xa)), align=None)

    blk = _prism_z(block, 0.0, length)
    return blk - _extrude_y(groove, p.ear_top_y - 1, y1 + 1)


def build_module(p: CupHolderParams | None = None):
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

    # Web: a vertical plate (a prism along Z) from the floor up to the rim, tangent to the pocket.
    x_web1 = p.web_gap + p.web_t

    def web_profile():
        Polygon((p.web_gap, y_plate0), (x_web1, y_plate0), (x_web1, y_end), (p.web_gap, y_end), align=None)

    web = _prism_z(web_profile, 0.0, 2 * R)

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

    # The dovetail block is added AFTER the cavity cut. It ends at x = web_gap + 2, inboard of
    # the cavity, so nothing needs trimming. Its groove stays open at the top and the bottom.
    return body + web - cavity - opening + _dovetail_block(p, p.clip_len)


def build_dovetail_test(p: CupHolderParams | None = None, y_len: float = 14.0):
    """Two short pieces to test the sliding fit only: a boss + tongue block and a groove block."""
    p = p or CupHolderParams()
    L = p.clip_len
    zc = L / 2
    y1 = p.ear_top_y + y_len

    def base():
        Polygon((p.boss_x0 - 6, p.ear_top_y), (p.dt_x0, p.ear_top_y), (p.dt_x0, y1), (p.boss_x0 - 6, y1), align=None)

    def tongue():
        Polygon(*_tongue_profile(p, zc), align=None)

    tongue_piece = _prism_z(base, 0.0, L) + _extrude_y(tongue, p.ear_top_y, y1)
    return tongue_piece, _dovetail_block(p, L, y1=y1)


def build(p: CupHolderParams | None = None):
    """Both pieces as a dict, in the shared print frame (assembled position)."""
    p = p or CupHolderParams()
    return {"clip": build_clip(p), "module": build_module(p)}
