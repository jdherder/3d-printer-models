"""Black Bob "4 B's" keychain: a big tilted, cropped BB framed by Be safe / Be kind / Be helpful / Be the best you.

    python projects/black-bob-4bs-keychain/build.py

  -> output/black-bob-4bs-keychain-multicolor.3mf  one object, three parts (red, white, black) for the AMS
  -> output/black-bob-4bs-keychain.stl            single-colour solid
  -> output/black-bob-4bs-keychain-{red,white,black}.stl
  -> output/report.json, renders/*.png, renders/view-*.stl (review page)

Everything is 2D shapely geometry first (drawing coords, Y up, mm, centred on the square), then each colour is
stacked from flat slabs (one per height interval) and unioned with manifold3d.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / "tools")]

import manifold3d as mf  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import meshkit as mk  # noqa: E402
import numpy as np  # noqa: E402
import shapely  # noqa: E402
import trimesh  # noqa: E402
from matplotlib.colors import LightSource  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from shapely import affinity  # noqa: E402
from shapely.geometry import Point, Polygon, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

OUT = HERE / "output"
RENDERS = HERE / "renders"
FONT = FontProperties(fname=str(HERE / "source" / "LiberationSans-Bold.ttf"))   # SIL OFL, same as keychain #1
NAME = "black-bob-4bs-keychain"

# --- Design parameters (mm) ------------------------------------------------------------------------------------------
SIZE = 56.0                # outside of the red frame (square)
CORNER_R = 9.0             # frame outer corner radius
FRAME_W = 8.0              # red frame band, outer edge to the black line
LINE_W = 0.8               # black line on the inside edge of the frame (2 extrusion widths)
WINDOW_R = 4.0             # window corner radius (outer edge of the black line)

# The four B's: (text, side, text rotation), angles CCW from the top side. Top and bottom both read upright (owner, v3);
# right reads top-to-bottom, left bottom-to-top.
SIDES = [("BE SAFE", 0, 0), ("BE KIND", -90, -90), ("BE HELPFUL", 90, 90), ("BE THE BEST YOU", 180, 0)]
TEXT_CAP = 3.6             # cap height of the frame text
TEXT_MAX_LEN = 42.0        # longest a side's text may run; "BE THE BEST YOU" is shrunk to fit (cap ~3.2)

# BB: two separate Bs in the letters' own frame, then tilted together and cropped by the window.
BB_CAP = 29.0              # cap height of each B
BB_ANGLE = 45.0            # tilt, counter-clockwise (rising to the right)
BB_PITCH = 23.9            # centre-to-centre along the letters' baseline (B advance ~28.9, so they overlap ~5)
BB_STAGGER = 8.0           # first B sits this much higher than the second (across the baseline)
BB_FRONT = 2               # which B is in front (1 = first/left, 2 = second/right)

# Heights (top of each region). The back is plain red; style like keychain #1 (field recessed, BB the high point).
BASE = 0.8                 # red under everything
FIELD_TOP = 2.4            # white window (1.6 white over the red base: thinner printed pinkish on keychain #1)
FRAME_TOP = 3.4            # red frame and the black line on its inside edge
TEXT_TOP = 3.8             # white frame text, embossed 0.4
FRONT_B_TOP = FRAME_TOP    # the B in front: flush with the black line (owner: the BB can't stand above the border)
BACK_B_TOP = 2.8           # the B behind: 0.4 off the field, 0.6 (3 layers) under the front B: the step separates them
COLOUR_DEPTH = {"white": 1.6, "black": 0.8}   # only the top this much is that colour; red below

TAB_W = 10.0               # keyring tab: rounded, centred above the frame
TAB_HOLE_D = 4.0
TAB_HOLE_Y = SIZE / 2 + 2.0   # hole centre (3.0 wall above it, round top)
MIN_FEATURE = 0.4          # crop slivers narrower than this are dropped (Arachne prints ~0.34 minimum)

COLOURS = {"red": "#c8102e", "white": "#f4f4f4", "black": "#222222"}


def rrect(half, r):
    return box(-half + r, -half + r, half - r, half - r).buffer(r, quad_segs=32)


def glyph(text):
    """Text as a shapely polygon, TextPath size 10, holes resolved by nesting depth."""
    from matplotlib.textpath import TextPath
    tp = TextPath((0, 0), text, size=10, prop=FONT)
    # Flatten the Bezier curves at 100x size: matplotlib's flattening tolerance is absolute, so at size 10 it's faceted.
    from matplotlib.transforms import Affine2D
    polys = tp.to_polygons(transform=Affine2D().scale(100), closed_only=True)
    ps = [Polygon(v / 100).buffer(0) for v in polys if len(v) > 2]
    depth = [sum(q.area > p.area and q.contains(p.representative_point()) for q in ps) for p in ps]
    solid = unary_union([p for p, d in zip(ps, depth) if d % 2 == 0])
    return solid.difference(unary_union([p for p, d in zip(ps, depth) if d % 2 == 1]))


CAP_UNITS = glyph("H").bounds[3]   # cap height in TextPath units


def text_shape(text, cap):
    g = affinity.scale(glyph(text), cap / CAP_UNITS, cap / CAP_UNITS, origin=(0, 0))
    x0, _, x1, _ = g.bounds
    return affinity.translate(g, -(x0 + x1) / 2, -cap / 2)        # centred on its cap-height box


def opening(g, w=MIN_FEATURE):
    """Drop parts narrower than w."""
    return g.buffer(-w / 2, join_style="mitre").buffer(w / 2, join_style="mitre").intersection(g)


def build_regions():
    """Disjoint 2D regions: name -> (polygon, colour, top)."""
    outer = rrect(SIZE / 2, CORNER_R)
    tab = box(-TAB_W / 2, 0, TAB_W / 2, TAB_HOLE_Y).union(Point(0, TAB_HOLE_Y).buffer(TAB_W / 2, quad_segs=32))
    body = outer.union(tab).difference(Point(0, TAB_HOLE_Y).buffer(TAB_HOLE_D / 2, quad_segs=32))
    win_half = SIZE / 2 - FRAME_W
    window_out = rrect(win_half, WINDOW_R)                              # outer edge of the black line
    window = rrect(win_half - LINE_W, WINDOW_R - LINE_W)               # white window
    line = window_out.difference(window)

    # Frame text: centred in the band, reading clockwise round the frame.
    band_mid = SIZE / 2 - FRAME_W / 2
    texts, text_caps = [], {}
    for txt, side, ang in SIDES:
        t = text_shape(txt, TEXT_CAP)
        w = t.bounds[2] - t.bounds[0]
        cap = TEXT_CAP * min(1.0, TEXT_MAX_LEN / w)
        t = text_shape(txt, cap)
        text_caps[txt] = round(cap, 2)
        cx, cy = affinity.rotate(Point(0, band_mid), side, origin=(0, 0)).coords[0]
        t = affinity.translate(affinity.rotate(t, ang, origin=(0, 0)), cx, cy)
        texts.append(t)
    text = unary_union(texts)
    frame = body.difference(window_out).difference(text)

    # BB: each B centred on its own point in the letters' frame, then tilted together.
    b = text_shape("B", BB_CAP)
    centres = [(-BB_PITCH / 2, BB_STAGGER / 2), (BB_PITCH / 2, -BB_STAGGER / 2)]
    bs = [affinity.rotate(affinity.translate(b, *c), BB_ANGLE, origin=(0, 0)) for c in centres]
    front_b = bs[BB_FRONT - 1]
    back_b = bs[2 - BB_FRONT]
    front = opening(front_b.intersection(window))
    back = opening(back_b.intersection(window).difference(front))
    field = opening(window.difference(front).difference(back))
    leftover = window.difference(front).difference(back).difference(field)   # slivers: join the back B
    back = back.union(leftover).buffer(0)
    # Snap everything to a 1 µm grid so neighbouring regions share exact vertices (near-coincident ones made a
    # degenerate sliver triangle where the two Bs meet).
    snap = lambda g: shapely.set_precision(g, 0.001)  # noqa: E731
    frame, line, text, field, back, front = map(snap, (frame, line, text, field, back, front))

    regions = {
        "frame": (frame, "red", FRAME_TOP),
        "line": (line, "black", FRAME_TOP),
        "text": (text, "white", TEXT_TOP),
        "field": (field, "white", FIELD_TOP),
        "back_b": (back, "red", BACK_B_TOP),
        "front_b": (front, "red", FRONT_B_TOP),
    }
    info = {"text_caps": text_caps, "outline": body}
    return regions, info


def colour_span(colour, col, top):
    """Z range a region contributes to colour `col`."""
    start = max(BASE, top - COLOUR_DEPTH.get(colour, top))
    if col == "red":
        return (0.0, start if colour != "red" else top)
    return (start, top) if colour == col else None


def cross_section(g):
    rings = []
    for p in getattr(g, "geoms", [g]):
        if p.is_empty or p.area < 1e-6:
            continue
        rings.append(np.asarray(p.exterior.coords)[:-1])
        rings += [np.asarray(i.coords)[:-1] for i in p.interiors]
    return mf.CrossSection(rings, mf.FillRule.EvenOdd)


def solid(regions, span_of):
    """Stack flat slabs: for each Z interval, extrude the union of regions that cover it."""
    spans = {k: span_of(c, t) for k, (_, c, t) in regions.items()}
    zs = sorted({z for s in spans.values() if s for z in s})
    parts = []
    for z0, z1 in zip(zs, zs[1:]):
        g = unary_union([regions[k][0] for k, s in spans.items() if s and s[0] <= z0 and s[1] >= z1])
        if g.is_empty:
            continue
        parts.append(cross_section(g.simplify(0.002)).extrude(z1 - z0).translate((0, 0, z0)))
    m = mf.Manifold.batch_boolean(parts, mf.OpType.Add)
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)


# --- Renders ---------------------------------------------------------------------------------------------------------
def raster(regions, info, step=0.04):
    x0, y0, x1, y1 = info["outline"].bounds
    xs = np.arange(x0 - 1, x1 + 1, step)
    ys = np.arange(y0 - 1, y1 + 1, step)
    X, Y = np.meshgrid(xs, ys)
    pts = shapely.points(X.ravel(), Y.ravel())
    H = np.zeros(X.size)
    C = np.full((X.size, 3), 0.92)
    for _, (g, col, top) in regions.items():
        shapely.prepare(g)
        hit = shapely.contains(g, pts)
        H[hit] = top
        C[hit] = matplotlib.colors.to_rgb(COLOURS[col])
    return H.reshape(X.shape), C.reshape(X.shape + (3,)), (xs[0], xs[-1], ys[0], ys[-1])


def relief_render(regions, info, path, zoom=None):
    H, C, ext = raster(regions, info)
    ls = LightSource(azdeg=315, altdeg=40)
    shade = ls.hillshade(H, vert_exag=8, dx=0.04, dy=0.04)
    flat = ls.hillshade(np.zeros((3, 3)))[1, 1]
    shaded = np.clip(C * (0.35 + 0.65 * shade / flat)[..., None], 0, 1)
    fig, ax = plt.subplots(figsize=(8, 9))
    ax.imshow(shaded, origin="lower", extent=ext)
    if zoom:
        ax.set_xlim(zoom[0], zoom[1])
        ax.set_ylim(zoom[2], zoom[3])
    ax.set_title(f"{NAME}: top, lit from upper left (height steps exaggerated), mm")
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)


def height_render(regions, info, path):
    H, _, ext = raster(regions, info, step=0.08)
    fig, ax = plt.subplots(figsize=(8, 9))
    im = ax.imshow(np.where(H > 0, H, np.nan), origin="lower", extent=ext, cmap="viridis")
    fig.colorbar(im, ax=ax, label="top height (mm)", shrink=0.7)
    ax.set_title("Heights (top of each region)")
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    RENDERS.mkdir(exist_ok=True)
    regions, info = build_regions()

    def check(m, name):
        assert m.is_watertight and m.is_winding_consistent, f"{name} body not watertight"

    bodies = {}
    for col in COLOURS:
        m = solid(regions, lambda c, t, col=col: colour_span(c, col, t))
        check(m, col)
        bodies[col] = m
        m.export(OUT / f"{NAME}-{col}.stl")

    merged = solid(regions, lambda c, t: (0.0, t))
    check(merged, "merged")
    rep = mk.report(merged)
    merged.export(OUT / f"{NAME}.stl")

    scene = trimesh.Scene()
    for col, m in bodies.items():
        scene.add_geometry(m, node_name=col, geom_name=col)
    scene.export(OUT / f"{NAME}-multicolor.3mf")

    # Viewer copies, standing up as it hangs (drawing Y -> Z), bottom on Z=0.
    stand = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
    lift = -float(merged.bounds[0, 1])
    for col, m in bodies.items():
        v = m.copy()
        v.apply_translation([0, 0, -float(merged.bounds[1, 2]) / 2])
        v.apply_transform(stand)
        v.apply_translation([0, 0, lift])
        v.export(RENDERS / f"view-{col}.stl")

    params = {
        "size": SIZE,
        "overall_width": round(float(merged.extents[0]), 1),
        "overall_height": round(float(merged.extents[1]), 1),
        "thickness": round(float(merged.extents[2]), 2),
        "frame_w": FRAME_W, "line_w": LINE_W,
        "window": round(SIZE - 2 * FRAME_W - 2 * LINE_W, 1),
        "base": BASE, "field_top": FIELD_TOP, "frame_top": FRAME_TOP, "text_top": TEXT_TOP,
        "back_b_top": BACK_B_TOP, "front_b_top": FRONT_B_TOP,
        "bb_cap": BB_CAP, "bb_angle_deg": BB_ANGLE, "bb_stagger": BB_STAGGER, "bb_pitch": BB_PITCH,
        "text_cap": TEXT_CAP, "text_cap_longest": min(info["text_caps"].values()),
        "tab_hole_d": TAB_HOLE_D,
    }
    report = {
        "scale_status": f"designer's choice: {SIZE:g} mm square frame (matches the 56 mm concept sketch)",
        "print": rep,
        "print_orientation": "flat on the bed, plain red back down (no supports)",
        "text_caps_mm": info["text_caps"],
        "region_areas_mm2": {k: round(float(g.area), 1) for k, (g, _, _) in regions.items()},
        "params_mm": params,
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))

    relief_render(regions, info, RENDERS / "relief.png")
    relief_render(regions, info, RENDERS / "relief-overlap.png", zoom=(-10, 14, -12, 12))
    height_render(regions, info, RENDERS / "heights.png")
    from render import render_sheet
    render_sheet(merged, str(RENDERS / "model.png"), title=f"{NAME}: print pose (flat), mm",
                 labels=["keychain"], sections_y=(0.0, 24.0), sections_x=(0.0, -24.0))


if __name__ == "__main__":
    main()
