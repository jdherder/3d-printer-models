"""Idealised, parametric gate footing, built as real CAD (build123d / OpenCASCADE).

The scan is wavy. This model rebuilds the part the way it would be modelled
in Fusion: flat faces, straight drafted walls, and true fillets. Every number
was measured off the cleaned scan (see README "Measurements"). Values are in
mm at *scan scale* until a real measurement is known. `build.py` scales
everything uniformly, then applies any directly measured overrides.

Frame: Z-up, base on Z=0, slot centred on X=0 and running along Y.

Modelling steps (mirrors a Fusion timeline):
  1. Base box L x W x base_h, vertical corners filleted (footprint radius)
  2. Upright block: XZ trapezoid (outer faces drafted) extruded through W
  3. Cut the slot: box with rounded bottom edges, through W
  4. Fillets: upright top Y-ends -> top outer -> top inner (slot lip) ->
     upright/base junction -> base top perimeter
"""

import math
from dataclasses import dataclass, fields, replace

from build123d import Align, Axis, Box, BuildSketch, Plane, Polygon, extrude, fillet


@dataclass(frozen=True)
class FootingParams:
    # Overall
    length: float = 415.0             # X, end wall to end wall
    width: float = 248.0              # Y, along the slot
    height: float = 165.0             # Z, top of the uprights
    footprint_corner_r: float = 55.0  # plan-view corner radius of the base

    # Base slab
    base_h: float = 50.0
    base_edge_r: float = 8.0          # rounding of the base's top perimeter

    # Slot between the uprights (flat, parallel inner faces)
    slot_w: float = 66.0
    slot_floor: float = 45.0          # height of the slot floor above the bed
    slot_floor_r: float = 8.0         # fillet where slot floor meets the walls

    # Uprights
    upright_outer_x: float = 100.0    # |x| of the outer face at base-top height
    upright_draft_deg: float = 15.0   # outer faces lean inward by this angle
    upright_fillet_r: float = 28.0    # outer face -> base top fillet
    upright_top_outer_r: float = 15.0
    upright_top_inner_r: float = 6.0  # slot lip
    upright_end_r: float = 60.0       # rounding of upright tops at the Y ends

    def scaled(self, k: float) -> "FootingParams":
        """Uniformly scale every length (angles untouched)."""
        return replace(self, **{f.name: getattr(self, f.name) * k for f in fields(self)
                                if not f.name.endswith("_deg")})


def _edges(part, axis, pred):
    return part.edges().filter_by(axis).filter_by(pred)


def build(p: FootingParams):
    """Return the footing as a build123d Part."""
    L, W, H, hb = p.length, p.width, p.height, p.base_h
    t = math.tan(math.radians(p.upright_draft_deg))
    near = lambda a, b: abs(a - b) < 1e-3  # noqa: E731

    # 1. Base slab
    base = Box(L, W, hb, align=(Align.CENTER, Align.CENTER, Align.MIN))
    base = fillet(base.edges().filter_by(Axis.Z), p.footprint_corner_r)

    # 2. Upright block (both uprights as one trapezoid; the slot splits it)
    x_bot = p.upright_outer_x + hb * t
    x_top = p.upright_outer_x - (H - hb) * t
    with BuildSketch(Plane.XZ) as upr:
        Polygon((-x_bot, 0), (x_bot, 0), (x_top, H), (-x_top, H), align=None)
    body = base + extrude(upr.sketch, amount=W / 2, both=True)

    # 3. Slot: a cutter box with its bottom edges rounded, so the slot floor
    #    blends into the flat walls with a concave fillet
    cutter = Box(p.slot_w, W + 20, H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cutter = fillet(cutter.edges().filter_by(Axis.Y).group_by(Axis.Z)[0], p.slot_floor_r)
    body -= cutter.translate((0, 0, p.slot_floor))

    # 4. Fillets (order matters for OpenCASCADE)
    body = fillet(_edges(body, Axis.X, lambda e: near(e.center().Z, H)
                         and near(abs(e.center().Y), W / 2)), p.upright_end_r)
    body = fillet(_edges(body, Axis.Y, lambda e: near(e.center().Z, H)
                         and abs(e.center().X) > p.slot_w / 2 + 1), p.upright_top_outer_r)
    body = fillet(_edges(body, Axis.Y, lambda e: near(e.center().Z, H)
                         and near(abs(e.center().X), p.slot_w / 2)), p.upright_top_inner_r)
    body = fillet(_edges(body, Axis.Y, lambda e: near(e.center().Z, hb)
                         and near(abs(e.center().X), p.upright_outer_x)), p.upright_fillet_r)
    base_top = [e for e in body.edges() if near(e.center().Z, hb)
                and abs(e.center().X) > p.upright_outer_x + 20]
    body = fillet(base_top, p.base_edge_r)
    assert body.is_valid, "OpenCASCADE produced an invalid solid"
    return body
