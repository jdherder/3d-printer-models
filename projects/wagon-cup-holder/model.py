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

from build123d import (Align, Box, BuildLine, BuildSketch, Circle, Cone, Cylinder, Line, Locations,
                       Plane, Polygon, Pos, RegularPolygon, Rotation, ThreePointArc, extrude, make_face)


@dataclass(frozen=True)
class CupHolderParams:
    # --- Side rail (owner measured ~22.3 mm round tube; assumed the same on the rail) ---
    bar_d: float = 22.3
    bar_clearance: float = 0.2      # on the diameter. The printed bore shrinks ~0.2 mm
    clip_wall: float = 2.8          # ring wall. Thinner = easier snap, thicker = stiffer
    clip_len: float = 70.0          # along the rail (owner has ~120 mm free)
    mouth_width: float = 20.7       # opening between the lips. Narrower than the rail to snap

    # --- Clamp ears + printed M8 x 1.5 bolt with a knob, and a printed hex nut (see fasteners.py) ---
    ear_t: float = 10.0             # ear thickness (X), either side of the mouth
    bolt_drop: float = 6.5          # bolt axis below the rail's lowest point
    bolt_hole_d: float = 9.0        # clears the 8 mm thread. Teardrop-shaped so it prints without support
    nut_af: float = 13.5            # pocket across flats: the printed nut is 13.0, plus clearance
    nut_depth: float = 6.9          # the printed nut is 6.5 thick
    lead_in: float = 3.5            # 45-degree guide at the bottom of the mouth

    # --- Dovetail between clip and module (slides along Y: the module drops on from above) ---
    ear_top_y: float = -4.0         # top of the ears. The module's block rests here
    boss_x0: float = 11.0           # boss on the clip, outboard of the ring (inner edge)
    dt_x0: float = 15.0             # tongue root plane (X)
    dt_h: float = 7.0               # tongue height (X)
    dt_w_root: float = 34.0         # tongue width (Z) at the root. 45-degree flanks widen it by 2*dt_h
    dt_y1: float = 28.0             # top of the tongue and the block (Y). Engagement = dt_y1 - ear_top_y
    dt_clear: float = 0.35          # sliding clearance per side

    # --- Keep-out: the end brackets' red latch and diagonal strut, same at both ends of the bar ---
    safe_window: float = 120.0      # clear length of bar between them (owner, "roughly")
    keepout_reach: float = 26.0     # how far they stick out past the bar's OUTER SURFACE (owner: "maybe 26")

    # --- Neck: flares from the dovetail pad into the web (replaces the old full-width block) ---
    neck_cheek: float = 4.0         # wall left around the dovetail groove at its mouth
    neck_under_r: float = 16.0      # inside fillet from the neck's underside into the web
    neck_top_r: float = 8.0         # inside fillet from the pad's top down to the web's top
    pad_end_x: float = 24.0         # where the pad's flat underside / top end and the blends begin

    # --- Web (carries the cup out and down from the dovetail pad) ---
    web_gap: float = 40.0           # rail axis to the inner face of the web. Must clear the strut + latch (below)
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
    def clip_dz(self) -> float:
        """Z shift that centres the clip (and its dovetail) on the cup module, and so on the clear window."""
        return self.cup_zc - self.clip_len / 2

    @property
    def keepout_x(self) -> float:
        """Outward distance from the rail axis that the latch / strut reach (worst-case reading)."""
        return self.bar_d / 2 + self.keepout_reach

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
    """Bore + mouth (with lead-in) + bolt hole + a nut pocket and slide-in slot on BOTH ears.

    The nut goes in either one (your choice of which side the knob is on); the knob covers the other."""
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
    # Hex nut pockets (flat top, so they only bridge ~5 mm) on the outer face of each ear, plus a slot below each
    # that is open to the ear's bottom end, so the nut slides in from underneath.
    nut_ac = p.nut_af / math.cos(math.radians(30))
    slot_h = yb - 1.0 - p.bolt_y  # negative: slot runs from the nut centre down past the ear's end
    pockets = []
    for side in (-1, 1):
        x0 = -x_out - 1 if side < 0 else x_out - p.nut_depth
        pockets.append(cut_along_x(x0, p.nut_depth + 1, lambda: RegularPolygon(nut_ac / 2, 6, rotation=0)))
        xc = side * (x_out - p.nut_depth / 2 + 0.5)
        pockets.append(Pos(xc, p.bolt_y + slot_h / 2, zb) * Box(p.nut_depth + 1, abs(slot_h), p.nut_af))
    return (bore, mouth, hole, *pockets)


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


def _groove(p: CupHolderParams, zc: float, y1: float):
    """The dovetail groove cutter: the clip's tongue grown by `dt_clear`, open at the pad's inner face and at both ends in Y."""
    k = 1.414 * p.dt_clear                        # normal clearance on a 45-degree flank

    def hw(x):
        return p.dt_w_root / 2 + (x - p.dt_x0) + k

    xa, xb = p.dt_x0 - 0.5, p.dt_x0 + p.dt_h + p.dt_clear

    def groove():
        Polygon((xa, zc - hw(xa)), (xb, zc - hw(xb)), (xb, zc + hw(xb)), (xa, zc + hw(xa)), align=None)

    return _extrude_y(groove, p.ear_top_y - 1, y1 + 1)


def _dovetail_block(p: CupHolderParams, length: float, y1: float | None = None, zc: float | None = None,
                    x_out: float | None = None):
    """A plain block with the groove. Used only for the dovetail sliding-fit test piece.
    `zc` is the Z of the groove centre (defaults to the block's own centre). The block starts at Z=0 so it stands on the bed."""
    y1 = p.dt_y1 if y1 is None else y1
    zc = length / 2 if zc is None else zc
    x_in = p.dt_x0 + p.dt_clear
    x_out = p.dt_x0 + p.dt_h + p.dt_clear + 6.0 if x_out is None else x_out

    def block():
        Polygon((x_in, p.ear_top_y), (x_out, p.ear_top_y), (x_out, y1), (x_in, y1), align=None)

    return _prism_z(block, 0.0, zc + length / 2) - _groove(p, zc, y1)


def _neck(p: CupHolderParams, z_full: float):
    """The shaped bracket between the dovetail pad and the web, WITHOUT the groove.

    Side profile (X, Y), extruded along Z: a flat pad under the clip's tongue, an inside fillet sweeping the
    underside down into the web, and a smaller one blending the pad's top down to the web's top.
    Plan profile (X, Z), extruded along Y and intersected: starts `neck_cheek` wider than the groove mouth and
    flares at 45 degrees, so the cheeks stay a constant thickness around the groove and every overhang is 45 degrees.
    """
    y_end = p.floor_y + p.pocket_depth            # web / pocket rim height
    x_in = p.dt_x0 + p.dt_clear
    xw = p.web_gap
    ru, rt = p.neck_under_r, p.neck_top_r
    xp = p.pad_end_x
    y0, y1 = p.ear_top_y, p.dt_y1
    c45 = math.cos(math.radians(45))

    # Side profile, counter-clockwise from the pad's inner-bottom corner.
    with BuildSketch(Plane.XY) as sk:
        with BuildLine():
            Line((x_in, y0), (xp, y0))
            ThreePointArc((xp, y0), (xp + ru * c45, y0 - ru + ru * c45), (xp + ru, y0 - ru))
            Line((xp + ru, y0 - ru), (xw + 2.0, y0 - ru))
            Line((xw + 2.0, y0 - ru), (xw + 2.0, y_end))
            Line((xw + 2.0, y_end), (xp + rt, y_end))
            ThreePointArc((xp + rt, y_end), (xp + rt - rt * c45, y1 - rt + rt * (1 - c45)), (xp, y1 - 0.0))
            Line((xp, y1), (x_in, y1))
            Line((x_in, y1), (x_in, y0))
        make_face()
    side = extrude(sk.sketch, amount=z_full)

    # Plan profile: groove half-width at the mouth + cheek, growing 1:1 with x (45 degrees).
    zc = p.cup_zc
    k = 1.414 * p.dt_clear
    hw0 = p.dt_w_root / 2 + k + p.neck_cheek     # half-width at x = dt_x0
    hw = lambda x: hw0 + (x - p.dt_x0)           # noqa: E731
    xa, xb = x_in - 1.0, xw + 3.0

    def plan():
        Polygon((xa, zc - hw(xa)), (xb, zc - hw(xb)), (xb, zc + hw(xb)), (xa, zc + hw(xa)), align=None)

    return side & _extrude_y(plan, y0 - ru - 5, y1 + 5)


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

    # The neck is added AFTER the cavity cut. It ends at x = web_gap + 2, inboard of the cavity, so nothing
    # needs trimming. Its groove stays open at the pad's inner face and at the top and bottom.
    return body + web - cavity - opening + (_neck(p, 2 * R) - _groove(p, zc, p.dt_y1))


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
    """Both pieces as a dict, in the shared print frame (assembled position, clip centred on the module)."""
    p = p or CupHolderParams()
    return {"clip": Pos(0, 0, p.clip_dz) * build_clip(p), "module": build_module(p)}
