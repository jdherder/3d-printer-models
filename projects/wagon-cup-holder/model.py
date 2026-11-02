"""Parametric side-hanging cup holder for the MAC wagon's right-hand side rail.

TWO PIECES, so the cup comes off in a couple of seconds for folding the wagon:

  CLIP    stays on the rail: a C ring that snaps on, two ears clamped by a printed M8 knob bolt + nut, and a vertical
          dovetail tongue on its outboard side.
  MODULE  the cup: a tapered ring that holds the 20 oz Yeti, with a stem that sweeps back to a dovetail pad. It drops
          straight down onto the tongue, rests on the ear tops, and lifts straight off. No tool.

v6 changes how both are made. The organic bodies are signed-distance fields with smooth blends (sdf.py), meshed with
marching cubes, so joins are true blends instead of stacked prisms with fillets. Everything that must be exact (the
dovetail tongue and groove, the rail bore, the mouth, the bolt hole and nut pockets) is cut on the mesh afterwards.
The trade: these two pieces are meshes (STL), not editable CAD (STEP). Change the numbers here and rebuild.

FRAMES
  U (use / assembled): X along the rail, centred on the clip. Y outward from the rail (toward the cup). Z up.
      The rail axis is the X axis (Y = Z = 0). The cup axis is vertical at (X = 0, Y = cup_axis_y).
  C (clip print frame): ring axis vertical. x = outward (= U Y), y = up (= U Z), z = along the rail from 0 to clip_len.
      U = (z - clip_len/2, x, y).
  The module prints as it sits in U (cup upright, floor on the bed), turned so its long side runs along the bed's X.
"""

import math
from dataclasses import dataclass

import numpy as np
import trimesh
from shapely.geometry import Polygon as ShapelyPolygon

import sdf


@dataclass(frozen=True)
class CupHolderParams:
    # --- Side rail (owner measured 22.3 mm round tube, confirmed on the side rail) ---
    bar_d: float = 22.3
    bar_clearance: float = 0.2      # on the diameter. The printed bore shrinks ~0.2 mm
    clip_wall: float = 2.8          # ring wall. Thinner = easier snap, thicker = stiffer
    clip_len: float = 70.0          # along the rail (owner has ~120 mm clear)
    mouth_width: float = 20.7       # opening between the lips. Narrower than the rail to snap

    # --- Clamp ears + printed M8 x 1.5 bolt with a knob, and a printed hex nut (see fasteners.py) ---
    ear_t: float = 10.0             # ear thickness, either side of the mouth
    bolt_drop: float = 6.5          # bolt axis below the rail's lowest point
    bolt_hole_d: float = 9.0        # clears the 8 mm thread. Teardrop-shaped so it prints without support
    nut_af: float = 13.5            # pocket across flats: the printed nut is 13.0, plus clearance
    nut_depth: float = 6.9          # the printed nut is 6.5 thick
    lead_in: float = 3.5            # 45-degree guide at the bottom of the mouth
    ear_top_y: float = -4.0         # top of the ears (Z in use). The module's pad rests here
    ear_round: float = 4.0          # rounding of the ears' bottom and side edges

    # --- Dovetail between clip and module (slides along Z: the module drops on from above) ---
    dt_x0: float = 15.5             # tongue root plane, outward from the rail axis
    dt_h: float = 7.0               # tongue height (outward)
    dt_w_root: float = 34.0         # tongue width along the rail at the root. 45-degree flanks widen it by 2*dt_h
    dt_clear: float = 0.35          # sliding clearance per side

    # --- 20 oz Yeti Rambler (retailer figures; owner is fine with these for now) ---
    cup_base_d: float = 70.0        # 2.75 in base
    cup_top_d: float = 89.0         # 3.5 in at the lid, the widest point
    cup_h: float = 165.0            # base to the widest point, sets the taper
    pocket_clearance: float = 2.0   # on the diameter, at every height
    pocket_depth: float = 84.0      # how far up the cup the pocket holds it. Sets the rim, which is also the top of the pad
    cup_wall: float = 3.2
    floor_t: float = 6.5
    floor_drop: float = 60.0        # cup base this far below the rail axis

    # --- Where the module sits ---
    inboard_gap: float = 40.0       # rail axis to the cup's outer wall at the rim (must clear the strut + latch)
    safe_window: float = 120.0      # clear length of bar between the end latches/struts (owner, "roughly")
    keepout_reach: float = 26.0     # how far the latch/strut stick out past the bar's OUTER SURFACE (owner: "maybe 26")

    # --- Shape of the blend ---
    neck_cheek: float = 4.0         # wall left around the dovetail groove
    stem_half_w: float = 20.0       # half width of the stem between the pad and the cup
    pad_stem_k: float = 14.0        # blend between the pad and the stem (plan view)
    pad_round: float = 3.0          # rounding of the pad's front corners (plan view)
    blend_k: float = 14.0           # blend between the stem and the cup (roughly a fillet of k/2)
    top_round_k: float = 3.0        # rounding of every edge that meets the top plane
    base_chamfer: float = 3.0       # 45-degree chamfer round the cup's base, so it prints cleanly on the bed
    floor_fillet: float = 3.0       # rounding inside the pocket where the floor meets the wall (a real tumbler's base edge is rounded too)
    voxel: float = 0.5              # marching-cubes cell size (mm)
    module_faces: int = 90000       # decimation target for the module mesh
    clip_faces: int = 70000

    # --- Derived ---
    @property
    def bore_r(self) -> float:
        return (self.bar_d + self.bar_clearance) / 2

    @property
    def clip_r_out(self) -> float:
        return self.bore_r + self.clip_wall

    @property
    def floor_y(self) -> float:
        """Z of the pocket floor (where the cup base sits), below the rail axis."""
        return -self.floor_drop

    @property
    def top_z(self) -> float:
        """Z of the flat top: the cup's rim, the stem and the dovetail pad all end here."""
        return self.floor_y + self.pocket_depth

    @property
    def bolt_y(self) -> float:
        return -(self.bar_d / 2 + self.bolt_drop)

    @property
    def ear_bottom_y(self) -> float:
        nut_ac = self.nut_af / math.cos(math.radians(30))
        return self.bolt_y - nut_ac / 2 - 2.4

    def pocket_r(self, depth: float) -> float:
        """Inner radius of the pocket `depth` mm above the floor."""
        taper = (self.cup_top_d - self.cup_base_d) / self.cup_h
        return (self.cup_base_d + taper * depth + self.pocket_clearance) / 2

    def r_in(self, z: float) -> float:
        return self.pocket_r(z - self.floor_y)

    def r_out(self, z: float) -> float:
        return self.r_in(z) + self.cup_wall

    @property
    def rim_outer_r(self) -> float:
        return self.r_out(self.top_z)

    @property
    def cup_axis_y(self) -> float:
        return self.inboard_gap + self.rim_outer_r

    @property
    def pad_front(self) -> float:
        """Outward position of the pad's front face (the tongue root plus the sliding clearance)."""
        return self.dt_x0 + self.dt_clear

    @property
    def tongue_tip(self) -> float:
        return self.dt_x0 + self.dt_h + self.dt_clear

    @property
    def keepout_x(self) -> float:
        """Outward distance from the rail axis that the latch / strut reach (worst-case reading)."""
        return self.bar_d / 2 + self.keepout_reach

    def dt_half_width(self, y: float) -> float:
        """Half width (along the rail) of the groove at outward position y: the tongue grown by the clearance."""
        return self.dt_w_root / 2 + (y - self.dt_x0) + 1.414 * self.dt_clear


# ---------------------------------------------------------------------------------------------------------
# Exact prisms (for the cuts and for the tongue)
# ---------------------------------------------------------------------------------------------------------

def prism_z(poly_xy, z0, z1):
    m = trimesh.creation.extrude_polygon(ShapelyPolygon(poly_xy), z1 - z0)
    m.apply_translation([0, 0, z0])
    return m


def prism_y(poly_xz, y0, y1):
    """Polygon drawn in world (x, z), extruded to span world Y = y0..y1."""
    m = trimesh.creation.extrude_polygon(ShapelyPolygon(poly_xz), y1 - y0)
    m.apply_translation([0, 0, -y1])
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))   # (u, v, w) -> (u, -w, v)
    return m


def prism_x(poly_yz, x0, x1):
    """Polygon drawn in world (y, z), extruded to span world X = x0..x1."""
    m = trimesh.creation.extrude_polygon(ShapelyPolygon(poly_yz), x1 - x0)
    m.apply_transform(np.array([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1.0]]))   # (u, v, w) -> (w, u, v)
    return m


def keep_largest(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Boolean operations on coplanar surfaces can leave microscopic fragments. Keep only the main body."""
    parts = mesh.split(only_watertight=False)
    if len(parts) <= 1:
        return mesh
    main = max(parts, key=lambda q: abs(q.volume) if q.is_watertight else 0.0)
    main.remove_unreferenced_vertices()
    return main


def boolean_difference(base, cutters):
    return keep_largest(trimesh.boolean.difference([base] + list(cutters), engine="manifold"))


def boolean_union(parts):
    return keep_largest(trimesh.boolean.union(list(parts), engine="manifold"))


# ---------------------------------------------------------------------------------------------------------
# Module (U frame)
# ---------------------------------------------------------------------------------------------------------

def module_field(p: CupHolderParams):
    cy = p.cup_axis_y
    z_base = p.floor_y - p.floor_t
    z_hi = p.top_z + 5.0
    grid = sdf.Grid(lo=(-50.0, 12.0, z_base - 4.0), hi=(50.0, cy + p.rim_outer_r + 4.0, z_hi + 1.0), h=p.voxel)
    X, Y, Z = grid.xyz()

    # Cup: a tapered ring (outer wall follows the tumbler's taper) with a 45-degree chamfer round its base.
    c = p.base_chamfer
    rb = p.r_out(z_base)
    t = p.r_out(z_base + 1.0) - rb                       # the wall's own outward lean, per mm of height
    cz = c / (1.0 - t)                                   # chamfer height that makes the slope exactly 45 degrees
    cup_outer = sdf.revolve_profile(np.sqrt(X ** 2 + (Y - cy) ** 2), Z, [
        (0.0, z_base), (rb - c, z_base), (p.r_out(z_base + cz), z_base + cz), (p.r_out(z_hi), z_hi), (0.0, z_hi)])

    # Pocket: a cone with a rounded floor edge. Convex, so rounding = shrink the polygon then grow the field.
    r0, r1 = p.r_in(p.floor_y), p.r_in(z_hi + 6.0)
    cav_poly = [(-r0, p.floor_y), (r0, p.floor_y), (r1, z_hi + 6.0), (-r1, z_hi + 6.0)]
    shrunk = ShapelyPolygon(cav_poly).buffer(-p.floor_fillet, join_style=2)
    cavity = sdf.sd_polygon(np.sqrt(X ** 2 + (Y - cy) ** 2), Z, list(shrunk.exterior.coords)[:-1]) - p.floor_fillet

    # Stem + pad. Plan view (X, Y): a pad that flares at 45 degrees with the groove's cheeks, blending into a slimmer stem.
    yf, yt = p.pad_front, p.tongue_tip
    hw0 = p.dt_half_width(yf) + p.neck_cheek
    hw1 = p.dt_half_width(yt) + p.neck_cheek
    pad_poly = [(-hw0, yf), (hw0, yf), (hw1, yt), (hw1, yt + 3.0), (-hw1, yt + 3.0), (-hw1, yt)]
    # round the pad's convex corners (shrink the polygon, grow the field), then blend it into the stem
    pad_shrunk = ShapelyPolygon(pad_poly).buffer(-p.pad_round, join_style=2)
    pad = sdf.sd_polygon(X, Y, list(pad_shrunk.exterior.coords)[:-1]) - p.pad_round
    y_stem0, y_stem1 = yt - 2.0, cy
    plan = sdf.smin(pad, sdf.sd_rect(X, Y, 0.0, (y_stem0 + y_stem1) / 2, p.stem_half_w, (y_stem1 - y_stem0) / 2), p.pad_stem_k)
    # Side view (Y, Z): a flat seat on the ear tops, then a 45-degree underside sweeping down into the cup wall.
    seat_end = yf + (p.ear_t + p.mouth_width / 2) - p.dt_x0          # seat as wide as the ear top that carries it
    ramp_end = p.inboard_gap + 8.0     # ends inside the cup wall, well above the cup's base
    side_poly = [(yf, p.ear_top_y), (seat_end, p.ear_top_y), (ramp_end, p.ear_top_y - (ramp_end - seat_end)),
                 (ramp_end, p.top_z + 4.0), (yf, p.top_z + 4.0)]
    side = sdf.sd_polygon(Y, Z, side_poly)
    neck = np.maximum(plan, side)

    body = sdf.smin(cup_outer, neck, p.blend_k)
    m = sdf.smax(body, -cavity, 1.0)
    m = sdf.smax(m, Z - p.top_z, p.top_round_k)           # flat top, every edge that meets it rounded
    return m, grid


def build_module(p: CupHolderParams | None = None) -> trimesh.Trimesh:
    """The cup module in the U frame, with the dovetail groove cut exactly."""
    p = p or CupHolderParams()
    field, grid = module_field(p)
    mesh = sdf.to_mesh(field, grid, target_faces=p.module_faces)
    y0, y1 = p.dt_x0 - 0.5, p.tongue_tip
    groove = prism_z([(-p.dt_half_width(y0), y0), (p.dt_half_width(y0), y0),
                      (p.dt_half_width(y1), y1), (-p.dt_half_width(y1), y1)], -80.0, p.top_z + 10.0)
    return boolean_difference(mesh, [groove])


# ---------------------------------------------------------------------------------------------------------
# Clip (C frame)
# ---------------------------------------------------------------------------------------------------------

def build_clip(p: CupHolderParams | None = None, length: float | None = None, dovetail: bool = True) -> trimesh.Trimesh:
    """The clip in its print frame C (ring axis vertical). `dovetail=False` gives the plain ring + ears (clamp test slice)."""
    p = p or CupHolderParams()
    L = p.clip_len if length is None else length
    zc = L / 2
    w = p.mouth_width / 2
    x_out = w + p.ear_t
    ear_top = p.ear_top_y
    ear_bot = p.ear_bottom_y

    grid = sdf.Grid(lo=(-x_out - 3.0, ear_bot - 3.0, -3.0), hi=(x_out + 3.0 if not dovetail else p.dt_x0 + p.dt_h + 3.0,
                                                                  p.top_z + 3.0 if dovetail else p.clip_r_out + 3.0, L + 3.0),
                    h=p.voxel * 0.8)
    X, Y, Z = grid.xyz()

    # Ring: a rail-sized cylinder, ends softened.
    ring = sdf.smax(np.sqrt(X ** 2 + Y ** 2) - p.clip_r_out, np.abs(Z - zc) - L / 2, 1.5)
    # Ears: rounded blocks either side of the mouth, blending into the ring.
    ears = None
    for s in (-1, 1):
        # A taller box with generous rounding, then cut flat at the ear top: every edge is soft except the top, which is
        # the seat the module's pad rests on and must stay flat and sharp.
        e = sdf.sd_round_box(X, Y, Z, (s * (w + p.ear_t / 2), (ear_bot + ear_top + 12.0) / 2, zc),
                             (p.ear_t / 2, (ear_top + 12.0 - ear_bot) / 2, L / 2), p.ear_round)
        e = np.maximum(e, Y - ear_top)
        ears = e if ears is None else np.minimum(ears, e)
    if dovetail:
        # Boss: the vertical plate on the outboard side that the module's pad faces. Same outline as the pad's front face.
        hw_pad = p.dt_half_width(p.pad_front) + p.neck_cheek
        boss_y0, boss_y1 = ear_top - 8.0, p.top_z       # starts inside the ear, so the two overlap instead of just touching
        boss = sdf.sd_round_box(X, Y, Z, ((p.dt_x0 + 11.0) / 2, (boss_y0 + boss_y1) / 2, zc),
                                ((p.dt_x0 - 11.0) / 2, (boss_y1 - boss_y0) / 2, hw_pad), 3.0)
        # Boss and ears meet at an EXACT corner (the module's pad sits right in it), so no smooth union between them.
        ears = np.minimum(ears, boss)
    body = sdf.smin(ring, ears, 4.0)
    body = sdf.smax(body, np.abs(Z - zc) - L / 2, 0.8)       # smooth unions bulge where shapes share a plane: cut the ends flat
    mesh = sdf.to_mesh(body, grid, target_faces=p.clip_faces)

    parts = [mesh]
    if dovetail:
        # The tongue: an exact dovetail prism (plan in x, z), root inside the boss, standing from the ear top to the rim.
        x0, x1 = p.dt_x0 - 1.0, p.dt_x0 + p.dt_h
        wr = p.dt_w_root / 2
        tongue_poly = [(x0, zc - wr), (p.dt_x0, zc - wr), (x1, zc - wr - p.dt_h), (x1, zc + wr + p.dt_h),
                       (p.dt_x0, zc + wr), (x0, zc + wr)]
        parts.append(prism_y(tongue_poly, ear_top, p.top_z))
        mesh = boolean_union(parts)

    # ---- exact cuts ----
    cut = []
    cut.append(trimesh.creation.cylinder(radius=p.bore_r, height=L + 4.0, sections=160))            # bore
    cut[-1].apply_translation([0, 0, zc])
    yb, li = ear_bot, p.lead_in
    cut.append(prism_z([(-w, 0), (w, 0), (w, yb + li), (w + li, yb - 0.1), (-(w + li), yb - 0.1), (-w, yb + li)],
                       -2.0, L + 2.0))                                                                # mouth + lead-in
    r = p.bolt_hole_d / 2
    k = r / math.sqrt(2)
    circ = ShapelyPolygon([(p.bolt_y + r * math.cos(a), zc + r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 64, endpoint=False)])
    tri = ShapelyPolygon([(p.bolt_y - k, zc + k), (p.bolt_y + k, zc + k), (p.bolt_y, zc + r * math.sqrt(2))])
    tear = circ.union(tri)
    cut.append(prism_x(list(tear.exterior.coords)[:-1], -x_out - 1.0, x_out + 1.0))                  # bolt hole (teardrop)
    nut_ac = p.nut_af / math.cos(math.radians(30))
    hexagon = [(p.bolt_y + nut_ac / 2 * math.cos(math.radians(60 * i)), zc + nut_ac / 2 * math.sin(math.radians(60 * i))) for i in range(6)]
    slot_poly = [(p.bolt_y, zc - p.nut_af / 2), (yb - 1.0, zc - p.nut_af / 2), (yb - 1.0, zc + p.nut_af / 2), (p.bolt_y, zc + p.nut_af / 2)]
    for side in (-1, 1):                                                                              # nut pocket + slide-in slot, both ears
        xa, xb = (x_out - p.nut_depth, x_out + 1.0) if side > 0 else (-x_out - 1.0, -x_out + p.nut_depth)
        cut.append(prism_x(hexagon, xa, xb))
        cut.append(prism_x(slot_poly, xa, xb))
    return boolean_difference(mesh, cut)


# ---------------------------------------------------------------------------------------------------------
# Frames
# ---------------------------------------------------------------------------------------------------------

def clip_to_U(mesh: trimesh.Trimesh, p: CupHolderParams) -> trimesh.Trimesh:
    """C frame -> U frame: U = (z - clip_len/2, x, y)."""
    m = mesh.copy()
    m.apply_transform(np.array([[0, 0, 1, -p.clip_len / 2], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1.0]]))
    return m


def print_pose(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Rest on Z=0, longest footprint axis along X, footprint centred on the XY origin."""
    m = mesh.copy()
    e = m.bounds[1] - m.bounds[0]
    if e[1] > e[0]:
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 0, 1]))
    c = (m.bounds[0] + m.bounds[1]) / 2
    m.apply_translation([-c[0], -c[1], -m.bounds[0, 2]])
    return m
