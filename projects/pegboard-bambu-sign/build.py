"""Reproducible build for the pegboard Bambu Lab badge (v2).

    python projects/pegboard-bambu-sign/build.py        (a minute or two: the rock-in check is the slow part)

A one-piece badge that hangs flush on the pegboard: the Bambu Lab mark + "Bambu Lab" on one line, cut to the logo's
outline (like the badge style on MakerWorld), in three colours: dark badge, white letters, green mark + accent.
The colours are inlaid flush with the front.

It prints FACE-DOWN: the front is the first layers on the plate (smooth, no top-surface texture), the colour changes are
all in the first INLAY mm, and the pegs stand straight up off the back, so nothing needs support. For that the hooks'
behind-board legs rise at 45 deg (pb.PegStyle.hook_leg_angle) instead of straight up (a straight-up leg would be a
horizontal overhang in this pose). The pegs are printed standing up (layers across them), which is fine for a badge this
light, but handle it gently.

  -> output/pegboard-bambu-sign-multicolor.3mf      one object, three parts: badge (dark), letters (white), mark (green)
  -> output/pegboard-bambu-sign.step / .stl         all merged (one colour)
  -> output/pegboard-bambu-sign-{dark,white,green}.stl  the colour bodies
  -> output/report.json                             checks, params, board fit, rock-in
  -> renders/face.png                               front as hung (with the hole grid) + back with the pegs
  -> renders/sign.png                               print pose views + sections
  -> renders/asm-*.stl, ref-pegboard.stl            hung on the board (world Z-up), for the viewer

Board frame (tools/pegboard.py): x out of the board, y up, z across. The badge's back is x = 0 (flush on the board),
its front x = T. Logo coordinates (u right, v up, mm, as seen from the front) map to z = Z_MID - u, y = Y_MID + v.
"""

import json
import sys
from dataclasses import asdict, replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / "tools")]

import meshkit as mk  # noqa: E402
import numpy as np  # noqa: E402
import pegboard as pb  # noqa: E402
import trimesh  # noqa: E402
from build123d import Compound, Face, Location, Plane, Rot, Wire, chamfer, export_step, extrude  # noqa: E402
from render import render_sheet  # noqa: E402
from shapely import affinity  # noqa: E402
from shapely.geometry import Polygon, box as sh_box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

OUT = HERE / "output"
RENDERS = HERE / "renders"
LOGO_SVG = HERE / "source" / "bambulab-logo-2026-11-09.svg"   # Wikimedia Commons "File:BambuLab logo.svg"

BOARD = pb.DEFAULT_BOARD
# Shared pegs (5.7 mm hook sloped 12 deg, 6.1 mm pins), with the hook's leg at 45 deg so it prints face-down without
# supports. The 45 deg leg starts just behind the board (hook_gap 4.8 vs the 3.94 mm board) and rises 6 mm above the hole
# centre, so it reaches 14.5 mm behind the board's front face: less than the steel hook (~15.6), so it fits wherever
# the owner's hooks do.
STYLE = replace(pb.PegStyle(), hook_gap=4.8, hook_rise=6.0, hook_leg_angle=45.0)
HOOK_ROW, PIN_ROW = 1, 0

# ---- Badge ------------------------------------------------------------------------------------------------------------
SIGN_W = 250.0        # overall width (as wide as the A1's 256 mm bed allows, 3 mm spare each side)
BORDER = 6.0          # dark border around the letters (the silhouette is the letters offset by this)
CORNER_R = 1.5        # rounding of the silhouette's corners
NOTCH_FILL = 4.0      # notches in the outline narrower than 2x this are filled (e.g. above the L's foot)
T = 4.0               # badge thickness (20 layers at 0.2)
INLAY = 0.8           # colour depth at the front (4 layers): white this thick hides the dark behind it
BACK_CHAMFER = 0.8    # round the back edge (the top in the print)
FRONT_CHAMFER = 0.4   # the front edge on the plate (takes up elephant's foot)
MIN_GAP = 1.0         # narrowest dark gap allowed between two coloured shapes (2-3 nozzle widths)
PINCH_WALL = 0.5      # the B's upper counter touches its outline at a point in the SVG; shrink it to leave this wall

# Layout on one line, in SVG units: the mark scaled to the B's height and sat on the baseline, then "Bambu", then "Lab".
BASELINE, B_TOP = 87.7, 141.2      # "Bambu" row baseline and B cap top (SVG units, y up)
MARK_GAP = 16.0                    # mark to B
WORD_GAP = 14.0                    # "Bambu" to "Lab" (small enough that the border bridges it)
GREEN, WHITE, DARK = "#00ae42", "#f2f2f2", "#2b2b2e"


# ---- Logo shapes (2D, shapely) ---------------------------------------------------------------------------------------

def _wire_xy(wire, step=0.5):
    """A closed wire as (x, y) points: line edges by their ends, curves every `step` SVG units."""
    pts = []
    for e in wire.order_edges():
        n = 1 if e.geom_type.name == "LINE" else max(4, int(e.length / step))
        seg = [e.position_at(i / n) for i in range(n + 1)]
        if pts and (seg[-1] - pts[-1]).length < (seg[0] - pts[-1]).length:
            seg = seg[::-1]          # edge runs the other way
        pts += [q for q in seg if not pts or (q - pts[-1]).length > 1e-6]
    return [(q.X, q.Y) for q in pts]


def svg_shapes():
    """The SVG's 13 shapes as shapely polygons in SVG units (y up), sorted into mark (4), accent (1), "bambu" row, "lab" row."""
    from build123d import import_svg
    faces = [f.fix() for f in import_svg(str(LOGO_SVG))]   # fix(): the "b" path has a zero-length curve
    polys = [Polygon(_wire_xy(f.outer_wire()), [_wire_xy(w) for w in f.inner_wires()]).buffer(0) for f in faces]
    assert len(polys) == 13, f"expected the mark (4) + 9 letter shapes in {LOGO_SVG.name}, got {len(polys)}"
    accent = min(polys, key=lambda p: p.area)
    mark = [p for p in polys if p.bounds[2] < 120]
    rest = [p for p in polys if p not in mark and p is not accent]
    lab = [p for p in rest if p.bounds[3] < 80]
    bambu = [p for p in rest if p.bounds[3] >= 80]
    assert (len(mark), len(lab), len(bambu)) == (4, 3, 5), (len(mark), len(lab), len(bambu))
    return mark, accent, bambu, lab


def layout():
    """Shapes on one line, in mm, centred on (0, 0): returns (green shapes, white shapes, scale mm per SVG unit)."""
    mark, accent, bambu, lab = svg_shapes()
    mk_bounds = unary_union(mark).bounds
    ms = (B_TOP - BASELINE) / (mk_bounds[3] - mk_bounds[1])                 # mark as tall as the B
    b_left = min(p.bounds[0] for p in bambu)
    mark = [affinity.translate(affinity.scale(p, ms, ms, origin=(mk_bounds[2], mk_bounds[1])),
                               b_left - MARK_GAP - mk_bounds[2], BASELINE - mk_bounds[1]) for p in mark]
    lab_dx = max(p.bounds[2] for p in bambu) + WORD_GAP - min(p.bounds[0] for p in lab)
    lab = [affinity.translate(p, lab_dx, BASELINE - min(q.bounds[1] for q in lab)) for p in lab]
    green, white = mark + [accent], bambu + lab
    allb = unary_union(green + white).bounds
    s = (SIGN_W - 2 * BORDER) / (allb[2] - allb[0])
    cx, cy = (allb[0] + allb[2]) / 2, (allb[1] + allb[3]) / 2
    to_mm = lambda p: affinity.scale(affinity.translate(p, -cx, -cy), s, s, origin=(0, 0))   # noqa: E731
    green, white = [to_mm(p) for p in green], [to_mm(p) for p in white]
    green, white = fix_contacts(green, white)
    return green, white, s


def fix_contacts(green, white):
    """Make the shapes printable as inlays: no counter pinched against its outline, and at least MIN_GAP of dark between
    any two shapes (in the SVG the B's accent touches the B at a corner)."""
    def unpinch(p):
        out = Polygon(p.exterior)
        for ring in p.interiors:
            hole = Polygon(ring)
            if hole.distance(out.exterior) < 1e-6:
                hole = hole.buffer(-PINCH_WALL, join_style="mitre")
            out = out.difference(hole)
        return out
    green, white = [unpinch(p) for p in green], [unpinch(p) for p in white]
    shapes = green + white
    for i in range(len(shapes)):
        for j in range(i + 1, len(shapes)):
            if shapes[i].distance(shapes[j]) < MIN_GAP:
                k, o = (i, j) if shapes[i].area < shapes[j].area else (j, i)
                d = np.subtract(shapes[k].centroid.coords[0], shapes[o].centroid.coords[0])
                d = d / np.linalg.norm(d) * 0.05
                while shapes[k].distance(shapes[o]) < MIN_GAP:
                    shapes[k] = affinity.translate(shapes[k], *d)
    return shapes[:len(green)], shapes[len(green):]


def silhouette(shapes):
    """The badge outline: every shape offset by BORDER (sharp points bevelled), merged, holes and narrow notches filled,
    corners rounded by CORNER_R."""
    u = unary_union(shapes).buffer(BORDER, join_style="mitre", mitre_limit=1.5)
    u = Polygon(u.exterior)
    u = Polygon(u.buffer(NOTCH_FILL).buffer(-NOTCH_FILL).exterior)
    x0, y0, x1, _ = u.bounds                                 # straight bottom edge (no scallops under round letters)
    u = unary_union([u, sh_box(x0 + BORDER, y0, x1 - BORDER, y0 + BORDER)])
    u = u.buffer(-CORNER_R).buffer(CORNER_R)                 # round convex corners
    u = u.buffer(CORNER_R).buffer(-CORNER_R)                 # and concave ones
    return Polygon(u.exterior).simplify(0.02)


def place_pegs(sil):
    """Pick the two peg columns (as far apart as possible) and the badge's height on the board so that, at both columns,
    the hook and the pin 1 in below it sit inside the outline with a margin. Returns (cols apart, u of the left peg column,
    v of the hook row) in logo mm."""
    m = 1.2                                                  # badge material round each peg (3 lines)
    half = max(STYLE.r, STYLE.hook_r) + m
    best = None
    u0, v0, u1, v1 = sil.bounds
    for k in range(9, 3, -1):
        for u_l in np.arange(u0, u1 - k * pb.PITCH, 0.5):
            for v_h in np.arange(v0, v1, 0.25):
                rects = [sh_box(u - half, v_h - pb.PITCH - STYLE.r - m, u + half, v_h + STYLE.hook_r + m)
                         for u in (u_l, u_l + k * pb.PITCH)]
                if all(sil.contains(r) for r in rects):
                    clear = min(sil.exterior.distance(r) for r in rects)
                    if best is None or clear > best[0]:
                        best = (clear, k, float(u_l), float(v_h))
        if best:
            return best[1], best[2], best[3], best[0]
    raise AssertionError("no place on the badge for two hook + pin pairs")


# ---- 3D (build123d, board frame) -------------------------------------------------------------------------------------

def _face(poly):
    ring = lambda c: Wire.make_polygon([(x, y, 0) for x, y in list(c)[:-1]], close=True)   # noqa: E731
    return Face(ring(poly.exterior.coords), [ring(i.coords) for i in poly.interiors])


def slab(polys, x0, x1, y_mid, z_mid):
    """Extrude logo-plane polygons (u right, v up) from x0 to x1 in the board frame."""
    plane = Plane(origin=(x0, y_mid, z_mid), x_dir=(0, 0, -1), z_dir=(1, 0, 0))      # local x = u (= -z), y = v (= y)
    return extrude(Compound([plane * _face(p) for p in polys]), amount=x1 - x0, dir=(1, 0, 0))


def build():
    green, white, scale = layout()
    sil = silhouette(green + white)
    k, u_l, v_h, clear = place_pegs(sil)
    z_mid = u_l + k * pb.PITCH            # the left peg (smaller u) is in column k, the right one in column 0
    y_mid = HOOK_ROW * pb.PITCH - v_h
    cols = (0, k)

    base = slab([sil], 0, T, y_mid, z_mid)
    back = [e for e in base.edges() if abs(e.center().X) < 1e-6]
    front = [e for e in base.edges() if abs(e.center().X - T) < 1e-6]
    base = chamfer(back, BACK_CHAMFER)
    base = chamfer([e for e in base.edges() if abs(e.center().X - T) < 1e-6], FRONT_CHAMFER) if front else base
    white_s = slab(white, T - INLAY, T, y_mid, z_mid)
    green_s = slab(green, T - INLAY, T, y_mid, z_mid)
    dark = base - white_s - green_s
    for c in cols:
        dark = dark + pb.hook_peg(STYLE, HOOK_ROW * pb.PITCH, c * pb.PITCH) + pb.pin_peg(STYLE, PIN_ROW * pb.PITCH, c * pb.PITCH)
    info = {"cols": cols, "peg_clearance_to_edge": round(clear, 1), "z_mid": z_mid, "y_mid": y_mid, "scale": scale,
            "sil": sil, "green": green, "white": white}
    return dark, white_s, green_s, info


def print_pose(solid):
    """Face-down on the plate: board x -> bed Z = T - x (the front is the first layer, the pegs point up)."""
    return solid.moved(Location((0, 0, T)) * Rot(0, 90, 0))


# ---- Renders ---------------------------------------------------------------------------------------------------------

def _fill(ax, geom, colour, **kw):
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MplPath
    for g in getattr(geom, "geoms", [geom]):
        rings = [np.array(g.exterior.coords)] + [np.array(r.coords) for r in g.interiors]
        codes = np.concatenate([[MplPath.MOVETO] + [MplPath.LINETO] * (len(r) - 2) + [MplPath.CLOSEPOLY] for r in rings])
        ax.add_patch(PathPatch(MplPath(np.vstack(rings), codes), facecolor=colour, edgecolor="none", **kw))


def render_face(info, path):
    """Front as hung (colours, over the board's hole grid) and the back seen from behind (pegs marked)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    sil, z_mid, y_mid = info["sil"], info["z_mid"], info["y_mid"]
    fig, (front, back) = plt.subplots(2, 1, figsize=(13, 8.5))
    for ax, flip in ((front, 1), (back, -1)):
        u0, v0, u1, v1 = sil.bounds
        # board holes in logo coordinates: u = z_mid - z, v = y - y_mid
        for j in range(-3, 4):
            for i in range(-2, 12):
                u, v = z_mid - i * pb.PITCH, j * pb.PITCH - y_mid
                ax.add_patch(plt.Circle((flip * u, v), BOARD.hole_d / 2, color="#cfc8bb", zorder=0))
        _fill(ax, affinity.scale(sil, flip, 1, origin=(0, 0)), DARK, zorder=1)
    for p in info["white"]:
        _fill(front, p, WHITE, zorder=2)
    for p in info["green"]:
        _fill(front, p, GREEN, zorder=2)
    for c in info["cols"]:
        u = z_mid - c * pb.PITCH
        for j, col, lab in ((HOOK_ROW, "#e0a030", "hook"), (PIN_ROW, "#5b8fd9", "pin")):
            v = j * pb.PITCH - y_mid
            back.add_patch(plt.Circle((-u, v), STYLE.r, color=col, zorder=3))
            back.annotate(lab, (-u + 5, v), color="white", fontsize=9, va="center", zorder=4)
    for ax, title in ((front, "front, as hung (pegboard holes behind in tan)"), (back, "back, seen from behind: hooks (orange) + pins (blue)")):
        ax.set_title(title)
        ax.set_aspect("equal")
        ax.set_xlim(-SIGN_W / 2 - 8, SIGN_W / 2 + 8)
        ax.set_ylim(sil.bounds[1] - 8, sil.bounds[3] + 8)
        ax.set_facecolor("#efebe3")
    fig.suptitle(f"pegboard-bambu-sign v2: {SIGN_W:.0f} mm one-piece badge, colours inlaid {INLAY} mm, printed face-down")
    fig.tight_layout()
    fig.savefig(path, dpi=90)
    plt.close(fig)


# ---- Main ------------------------------------------------------------------------------------------------------------

def main():
    OUT.mkdir(exist_ok=True)
    RENDERS.mkdir(exist_ok=True)
    for stale in ("pegboard-bambu-sign-base.stl", "pegboard-bambu-sign-logo.stl", "pegboard-bambu-sign-hanger.stl",
                  "pegboard-bambu-sign-hanger.step"):
        (OUT / stale).unlink(missing_ok=True)
    for stale in ("asm-hangers.stl", "asm-logo.stl", "hanger.png"):
        (RENDERS / stale).unlink(missing_ok=True)
    assert not STYLE.check(BOARD), STYLE.check(BOARD)

    dark, white, green, info = build()
    parts_p = {n: print_pose(s) for n, s in (("dark", dark), ("white", white), ("green", green))}
    bb = Compound(list(parts_p.values())).bounding_box()
    shift = Location((-(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z))
    parts_p = {n: s.moved(shift) for n, s in parts_p.items()}
    meshes = {n: mk.cad_to_mesh(s) for n, s in parts_p.items()}
    for n, m in meshes.items():
        assert m.is_watertight, f"{n} is not watertight"
        m.export(OUT / f"pegboard-bambu-sign-{n}.stl")
    merged_p = parts_p["dark"] + parts_p["white"] + parts_p["green"]
    export_step(merged_p, str(OUT / "pegboard-bambu-sign.step"))
    merged = mk.cad_to_mesh(merged_p)
    rep = mk.report(merged)
    assert rep["watertight"] and rep["self_intersecting_faces"] == 0, rep
    merged.export(OUT / "pegboard-bambu-sign.stl")
    scene = trimesh.Scene()
    for n, label in (("dark", "badge (dark)"), ("white", "letters (white)"), ("green", "mark + accent (green)")):
        scene.add_geometry(meshes[n], node_name=label, geom_name=label)
    scene.export(OUT / "pegboard-bambu-sign-multicolor.3mf")

    # Printability: the lowest point is the front (colour starts on the plate), nothing overhangs below the back except the pegs.
    z_front = float(meshes["dark"].bounds[0, 2])
    assert abs(float(meshes["white"].bounds[0, 2]) - z_front) < 1e-3, "white letters don't start on the plate"

    # Fit on the board (board frame)
    hung = mk.cad_to_mesh(dark + white + green)
    cols = info["cols"]
    rows, colr = range(PIN_ROW - 2, HOOK_ROW + 3), range(min(cols) - 2, max(cols) + 3)
    board_fit = pb.board_mesh(BOARD, rows=rows, cols=colr, clearance=pb.FIT_CLEARANCE)
    s = hung.copy()
    s.apply_translation([0.01, 0, 0])
    flush = pb.interference_mm3(s, board_fit)
    rock = pb.rock_in(hung, BOARD, hook_y=HOOK_ROW * pb.PITCH)
    assert rock["ok"], f"badge won't rock onto the board: {rock}"

    pb.to_zup(mk.cad_to_mesh(dark)).export(RENDERS / "asm-sign.stl")
    pb.to_zup(mk.cad_to_mesh(white)).export(RENDERS / "asm-white.stl")
    pb.to_zup(mk.cad_to_mesh(green)).export(RENDERS / "asm-green.stl")
    pb.to_zup(pb.board_mesh(BOARD, rows=range(-3, 5), cols=range(-2, max(cols) + 3))).export(RENDERS / "ref-pegboard.stl")

    sil = info["sil"]
    shapes = info["green"] + info["white"]
    min_gap = min(a.distance(b) for i, a in enumerate(shapes) for b in shapes[i + 1:])
    assert min_gap >= MIN_GAP - 1e-6, min_gap
    hook_y = HOOK_ROW * pb.PITCH
    sil_top, sil_bot = sil.bounds[3] + info["y_mid"], sil.bounds[1] + info["y_mid"]
    report = {
        "scale_status": "real size (shared pegs; badge size is the owner's choice: as wide as the A1 bed allows)",
        "print": rep,
        "print_orientation": "face-down on the plate, no supports: colours in the first 0.8 mm, pegs pointing up "
                             "(the hooks' legs rise at 45 deg so they don't overhang)",
        "colours": {"dark": "badge + pegs", "white": "Bambu Lab letters", "green": "mark + B accent",
                    "colour_layers_mm": INLAY, "volume_cm3": {n: round(float(m.volume) / 1000, 1) for n, m in meshes.items()}},
        "fit_on_board": {"board": BOARD.name, "hole_d": BOARD.hole_d, "thickness": BOARD.thickness, "pitch": BOARD.pitch,
                         "flush_overlap_mm3_info_only": flush, "rock_in": {**rock, "give_mm": pb.ROCK_IN_GIVE},
                         "holes_used": f"2 hooks in one row, {max(cols) - min(cols)} holes apart, each with a pin 1 hole below",
                         "badge_top_above_hook_hole_mm": round(sil_top - hook_y, 1),
                         "badge_bottom_below_hook_hole_mm": round(hook_y - sil_bot, 1),
                         "hook_reach_behind_front_face_mm": round(-float(hung.bounds[0, 0]), 1),
                         "peg_margin_to_badge_edge_mm": info["peg_clearance_to_edge"]},
        "params_mm": {**asdict(STYLE), "pitch": pb.PITCH, "sign_width": round(sil.bounds[2] - sil.bounds[0], 1),
                      "sign_height": round(sil.bounds[3] - sil.bounds[1], 1), "sign_thickness": T, "inlay": INLAY,
                      "border": BORDER, "letter_height": round((B_TOP - BASELINE) * info["scale"], 1),
                      "letter_stroke": round(11.3 * info["scale"], 1), "min_colour_gap": round(min_gap, 2),
                      "peg_spacing": (max(cols) - min(cols)) * pb.PITCH,
                      "hole_clearance_per_side": round((BOARD.hole_d - STYLE.d) / 2, 2)},
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("print", "fit_on_board", "params_mm")}, indent=2))

    render_face(info, RENDERS / "face.png")
    pegs = merged.vertices[merged.vertices[:, 2] > T + 1]
    peg_x = float(pegs[pegs[:, 0] > 0, 0].mean())              # the right-hand peg column in the print pose
    render_sheet([merged], str(RENDERS / "sign.png"), title="pegboard-bambu-sign v2: print pose (face-down), mm",
                 labels=["badge"], sections_y=(0.0,), sections_x=(peg_x, 0.0))


if __name__ == "__main__":
    main()
