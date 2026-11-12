"""Reproducible build for the Black Bob Elementary logo keychain.

    python projects/black-bob-keychain/build.py        (~20 s)

source/logo-2026-11-12-school-site-300px.png (the school's logo; 300 px is the largest the site has)
  -> upscaled 4x, every pixel classified as red / white / black
  -> regions: red ring, white ring text, white field, and the bird (filled black outline) with its red body,
     white feather/bolt details, white beak, and cap (red + white "BB")
  -> thin black lines thickened and tiny white specks dropped so every colour region prints with a 0.4 mm nozzle
  -> "bezel + hero bird" heights (owner's pick, style A), all on a plain red base:
       red base 0.8 | white field 1.8 | red ring 2.8 | white text 3.2 | white details (cut in) 2.4 |
       red bird, black outline, white beak 3.0 | cap 3.4
  -> keyring tab above the ring at 12 o'clock
  -> output/black-bob-keychain.stl             single-colour print (all bodies merged)
  -> output/black-bob-keychain-multicolor.3mf  one object, three parts (red, white, black) for the AMS
  -> output/black-bob-keychain-{red,white,black}.stl
  -> output/report.json, renders/*.png
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / "tools")]

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import manifold3d as m3d  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import meshkit as mk  # noqa: E402
import numpy as np  # noqa: E402
import shapely  # noqa: E402
import trimesh  # noqa: E402
from matplotlib.patches import Polygon as MplPolygon  # noqa: E402
from PIL import Image  # noqa: E402
from scipy import ndimage  # noqa: E402
from shapely import affinity  # noqa: E402
from shapely.geometry import MultiPolygon, Point, Polygon, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402
from skimage import measure  # noqa: E402

OUT = HERE / "output"
RENDERS = HERE / "renders"
LOGO = HERE / "source" / "logo-2026-11-12-school-site-300px.png"
# Ring letters are set in this font (SIL OFL), fitted letter by letter onto the traced ones: it matched the logo's
# lettering best of the bold sans fonts tried (mean overlap 0.88 vs 0.78-0.88 for Inter, DejaVu, FreeSans).
FONT = HERE / "source" / "LiberationSans-Bold.ttf"
RING_TEXT = ("BLACKBOB", "ELEMENTARY")     # top (left to right), bottom (left to right)
NAME = "black-bob-keychain"

# --- Design parameters (mm) ------------------------------------------------------------------------------------------
DIAMETER = 60.0            # outside of the red ring (owner: 55 or 60; 60 keeps the wing details printable)
BASE = 0.8                 # plain red base under everything (4 layers): the back is red, all colour swaps are above it
FIELD_TOP = 1.8            # white background inside the ring (1.0 white over the red, so it doesn't turn pink)
RING_TOP = 2.8             # red ring: a raised bezel around the field
TEXT_TOP = 3.2             # white ring letters, embossed 0.4 above the ring
BIRD_TOP = 3.0             # red bird, its black outline and the white beak: stand 1.2 off the field
INSET_TOP = 2.4            # white feather slits, lightning bolt, tail rays: cut 0.6 into the bird
CAP_TOP = 3.4              # cap (and its "BB"): the highest point
TAB_R = 4.5                # keyring tab (radius), above the ring at 12 o'clock
TAB_HOLE_D = 4.0           # for a split ring
TAB_CENTRE_OUT = 3.5       # tab/hole centre, this far outside the ring
TAB_FILLET = 1.5           # rounds the tab-to-ring corners
# Black lines in the logo are as thin as ~0.35 mm at 60 mm. After smoothing, the red next to them is pulled back by
# BLACK_GROW (white by WHITE_PULL), so every black line grows evenly to >= ~0.6 mm and stays smooth.
BLACK_GROW = 0.13
WHITE_PULL = 0.06
MIN_RED = 0.5              # red bits inside the bird narrower than this are dropped (become black)
MIN_WHITE = 0.45           # white details inside the bird narrower than this are dropped (become red)
COLOUR_DEPTH = {"white": 1.0, "black": 0.8}   # thick enough that the red below doesn't show through
MIN_AREA = 0.15            # specks smaller than this (mm^2) are dropped
SMOOTH = 0.3               # traced outlines are smoothed along their length (Gaussian sigma, mm): no pixel steps or wobble
CORNER_DEG = 40            # ... except at corners sharper than this, which stay crisp
SLIVER = 0.03              # region slivers narrower than 2x this (from overlapping traces) are dropped

# --- Logo geometry (source pixels, measured from the 300 px image) ---------------------------------------------------
UPSCALE = 4
# Circles fitted (least squares) to the colour edges of the upscaled logo:
CENTRE_PX = (149.68, 149.83)       # x, y: centre of the outside of the red ring (the keychain's centre)
R_OUT_PX = 143.39                  # outside of the red ring (a thin white rim outside it is left off: too thin to print)
INNER_CENTRE_PX = (150.19, 150.04) # the inside of the ring is ~0.5 px off-centre in the logo; kept, so the field matches
R_IN_PX = 107.04
PALETTE = {"red": (200, 20, 30), "white": (255, 250, 250), "black": (45, 15, 15)}
# The cap is redrawn, not traced: at 300 px it's ~45 px wide, too blurry to trace cleanly. Smooth closed splines
# through these points (mm, read off a gridded close-up of the logo), all raised to CAP_TOP.
CAP_CROWN = [(-2.6, 16.7), (-2.5, 18.1), (-1.7, 19.7), (-0.1, 20.8), (1.8, 21.15), (3.4, 20.8), (4.5, 19.8),
             (5.0, 18.6), (3.0, 17.7), (0.6, 17.0), (-1.2, 16.6)]
CAP_VISOR = [(-0.2, 16.75), (2.5, 17.45), (5.0, 18.6), (6.6, 18.2), (7.8, 17.4), (6.6, 16.75), (4.5, 16.35),
             (2.0, 16.15), (0.4, 16.3)]
CAP_SEAM = [(-1.6, 16.9), (-1.1, 18.8), (-0.2, 20.6)]   # panel seam, left of the "BB"
CAP_SEAM_W = 0.5
CAP_RIM = 0.45             # black outline around the cap
CAP_BB = dict(centre=(2.25, 19.4), height=2.05, angle=-6.0, bold=0.08)   # "BB" in FONT; bold thickens the strokes
# The beak is redrawn too (the logo's mouth is a few px of anti-aliasing): black lines along the centre of the logo's
# lines, white between them. Everything traced in the beak area is replaced; the gap between the jaws is field.
BEAK_LINE_W = 0.45
BEAK_LOWER_EDGE = [(0.05, 13.1), (1, 12.55), (2, 12.5), (3, 12.6), (4, 12.75), (5, 13.0), (6, 13.3), (7, 13.6),
                   (8, 13.85), (10, 14.15), (12, 14.3), (14, 14.3), (15.5, 14.2), (16.6, 14.0)]
BEAK_TOP_EDGE = [(16.6, 14.0), (15.6, 14.85), (14, 15.55), (12, 16.1), (10, 16.4), (8, 16.6), (6, 16.75), (4.5, 16.9)]
BEAK_UPPER_LEFT = [(4.5, 16.9), (3.6, 15.6), (2.6, 14.3), (1.2, 13.2)]   # closes the upper beak's white (no line)
JAW_LOOP = [(2.9, 11.75), (5, 11.55), (7, 11.35), (9, 11.15), (11, 10.95), (12.8, 10.85), (13.5, 10.5), (13.1, 10.05),
            (12, 9.85), (10, 9.8), (8, 9.8), (6, 9.85), (4, 9.95), (3.0, 10.3), (2.75, 11.0)]
MOUTH_LINE = [(2.8, 11.65, 0.55), (5.5, 11.45, 0.42), (9, 11.12, 0.3), (12.6, 10.85, 0.24)]   # x, y, half-width
BEAK_CORNER_DOT = 0.32
# White bits of the bird that stand at bird height instead of being cut in: everything white whose centre is in this
# box (source px x0, y0, x1, y1): the beak (both jaws) and the eye.
RAISED_WHITE_BOX_PX = (150, 70, 235, 105)

K = DIAMETER / 2 / R_OUT_PX        # mm per source pixel


def px_to_mm(x, y):
    return (x - CENTRE_PX[0]) * K, -(y - CENTRE_PX[1]) * K


def classify():
    """Upscaled label image: 0 red, 1 white, 2 black, 3 transparent."""
    im = Image.open(LOGO).convert("RGBA")
    n = im.size[0] * UPSCALE
    a = np.asarray(im.resize((n, n), Image.LANCZOS)).astype(float)
    pal = np.array(list(PALETTE.values()), float)
    c = ((a[..., None, :3] - pal) ** 2).sum(-1).argmin(-1)
    c[a[..., 3] < 128] = 3
    return c


def disk(r_mm):
    r = max(1, int(round(r_mm / (K / UPSCALE))))
    y, x = np.mgrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


def smooth_ring(xy, sigma):
    """Smooth a closed outline (mm) along its length, keeping sharp corners sharp.

    Resampled evenly, corners found by the turning angle over ~0.25 mm, then each stretch between corners is
    Gaussian-smoothed, with the smoothing faded out towards its corner ends so the corners stay put."""
    from scipy.ndimage import gaussian_filter1d
    step = 0.03
    seg = np.diff(np.r_[xy, xy[:1]], axis=0)
    s = np.r_[0, np.cumsum(np.hypot(*seg.T))]
    total = s[-1]
    if total < 8 * step:
        return xy
    t = np.arange(0, total, step)
    closed = np.r_[xy, xy[:1]]
    p = np.c_[np.interp(t, s, closed[:, 0]), np.interp(t, s, closed[:, 1])]
    n = len(p)
    k = max(2, int(round(0.25 / step)))
    v1 = p - np.roll(p, k, 0)
    v2 = np.roll(p, -k, 0) - p
    ang = np.degrees(np.abs(np.arctan2(v1[:, 0] * v2[:, 1] - v1[:, 1] * v2[:, 0], (v1 * v2).sum(1))))
    peak = ang == ndimage.maximum_filter1d(ang, 2 * k + 1, mode="wrap")
    corners = np.nonzero(peak & (ang > CORNER_DEG))[0]
    sg = sigma / step
    if len(corners) == 0:
        return np.c_[gaussian_filter1d(p[:, 0], sg, mode="wrap"), gaussian_filter1d(p[:, 1], sg, mode="wrap")]
    p = np.roll(p, -corners[0], 0)
    cs = np.r_[corners - corners[0], n]
    out = []
    for a, b in zip(cs[:-1], cs[1:]):
        q = p[a:b + 1] if b < n else np.r_[p[a:], p[:1]]
        sm = np.c_[gaussian_filter1d(q[:, 0], sg, mode="nearest"), gaussian_filter1d(q[:, 1], sg, mode="nearest")]
        i = np.arange(len(q))
        w = np.clip(np.minimum(i, len(q) - 1 - i) / (2 * sg), 0, 1)[:, None]
        out.append((q * (1 - w) + sm * w)[:-1])
    return np.concatenate(out)


def mask_to_poly(mask, smooth=SMOOTH):
    """Boolean mask (upscaled px) -> shapely (multi)polygon in mm. Slightly blurred first so edges come out smooth."""
    m = ndimage.gaussian_filter(np.pad(mask, 2).astype(float), 1.0)
    polys = []
    for c in measure.find_contours(m, 0.5):
        if len(c) < 4:
            continue
        xs = (c[:, 1] - 2 + 0.5) / UPSCALE
        ys = (c[:, 0] - 2 + 0.5) / UPSCALE
        xy = np.c_[px_to_mm(xs, ys)]
        if smooth:
            xy = smooth_ring(xy, smooth)
        if len(xy) < 4:
            continue
        p = Polygon(xy).buffer(0)
        if p.area > 0:
            polys.append(p)
    # Nested contours: a contour inside an even number of others is an outline, inside an odd number it's a hole.
    depth = [sum(q.area > p.area and q.contains(p.representative_point()) for q in polys) for p in polys]
    solid = unary_union([p for p, d in zip(polys, depth) if d % 2 == 0])
    holes = unary_union([p for p, d in zip(polys, depth) if d % 2 == 1])
    return clean(solid.difference(holes).simplify(0.015))


def clean(g):
    """Drop specks; return a (multi)polygon."""
    g = g.buffer(0).buffer(-SLIVER, join_style="mitre").buffer(SLIVER, join_style="mitre")
    parts = [p for p in getattr(g, "geoms", [g]) if p.area >= MIN_AREA]
    g = unary_union(parts) if parts else Polygon()
    # Snap to a fine grid: removes near-touching vertices (pinch points), which would mesh as zero-width slivers.
    return shapely.set_precision(g, 0.005).buffer(0)


def glyph(chars, font):
    """Text (one or more characters) as a shapely polygon in font units (TextPath, size 10)."""
    from matplotlib.textpath import TextPath
    tp = TextPath((0, 0), chars, size=10, prop=font)
    ps = [Polygon(v).buffer(0) for v in tp.to_polygons(closed_only=True) if len(v) > 2]
    depth = [sum(q.area > p.area and q.contains(p.representative_point()) for q in ps) for p in ps]
    solid = unary_union([p for p, d in zip(ps, depth) if d % 2 == 0])
    return solid.difference(unary_union([p for p, d in zip(ps, depth) if d % 2 == 1]))


def fit_letters(mask):
    """Replace the traced ring letters with clean font glyphs, each fitted onto its traced letter.

    Each traced letter is turned upright (top line: tops point out; bottom line: tops point in), its box measured, and
    the glyph is scaled into that box (all letters in a line share one height) and turned back. Letters that touch in
    the logo (the "LA") are one traced blob, so they are fitted as a pair."""
    from matplotlib.font_manager import FontProperties
    font = FontProperties(fname=str(FONT))
    lab, n = ndimage.label(mask)
    blobs = [mask_to_poly(lab == i, smooth=0) for i in range(1, n + 1)]
    blobs = [p for p in blobs if p.area > 1.0]
    out = []
    for text, top in zip(RING_TEXT, (True, False)):
        line = sorted([p for p in blobs if (p.centroid.y > 0) == top], key=lambda p: p.centroid.x)
        upright = []
        for p in line:
            th = np.degrees(np.arctan2(p.centroid.y, p.centroid.x))
            rot = -(th - 90) if top else -(th + 90)
            upright.append((affinity.rotate(p, rot, origin=(0, 0)), rot))
        widths = [q.bounds[2] - q.bounds[0] for q, _ in upright]
        height = np.median([q.bounds[3] - q.bounds[1] for q, _ in upright])
        i = 0
        for (q, rot), w in zip(upright, widths):
            k = max(1, int(round(w / np.median(widths))))
            g = glyph(text[i:i + k], font)
            i += k
            gx0, gy0, gx1, gy1 = g.bounds
            qx0, qy0, qx1, qy1 = q.bounds
            g = affinity.translate(g, -(gx0 + gx1) / 2, -(gy0 + gy1) / 2)
            g = affinity.scale(g, (qx1 - qx0) / (gx1 - gx0), height / (gy1 - gy0), origin=(0, 0))
            g = affinity.translate(g, (qx0 + qx1) / 2, (qy0 + qy1) / 2)
            out.append(affinity.rotate(g, -rot, origin=(0, 0)))
        assert i == len(text), f"traced letters don't match {text!r}"
    return clean(unary_union(out))


def spline_loop(pts, n=400):
    """Smooth closed curve through the points (periodic cubic spline) as a polygon."""
    from scipy.interpolate import splev, splprep
    p = np.asarray(pts, float)
    tck, _ = splprep([np.r_[p[:, 0], p[0, 0]], np.r_[p[:, 1], p[0, 1]]], s=0, per=True)
    x, y = splev(np.linspace(0, 1, n, endpoint=False), tck)
    return Polygon(np.c_[x, y]).buffer(0)


def spline_stroke(pts, width, n=200):
    from scipy.interpolate import splev, splprep
    from shapely.geometry import LineString
    p = np.asarray(pts, float)
    tck, _ = splprep([p[:, 0], p[:, 1]], s=0, k=min(3, len(p) - 1))
    x, y = splev(np.linspace(0, 1, n), tck)
    return LineString(np.c_[x, y]).buffer(width / 2, cap_style="round")


def tapered_stroke(pts):
    """Stroke whose half-width varies along it: (x, y, r) points, joined by hulls of consecutive circles."""
    from scipy.interpolate import interp1d
    p = np.asarray(pts, float)
    t = np.r_[0, np.cumsum(np.hypot(*np.diff(p[:, :2], axis=0).T))]
    f = interp1d(t, p, axis=0, kind="quadratic" if len(p) > 2 else "linear")
    q = f(np.linspace(0, t[-1], 60))
    circles = [Point(x, y).buffer(r, 32) for x, y, r in q]
    return unary_union([unary_union([a, b]).convex_hull for a, b in zip(circles, circles[1:])])


def spline_open(pts, n=200):
    from scipy.interpolate import splev, splprep
    p = np.asarray(pts, float)
    tck, _ = splprep([p[:, 0], p[:, 1]], s=0, k=min(3, len(p) - 1))
    x, y = splev(np.linspace(0, 1, n), tck)
    return np.c_[x, y]


def draw_beak():
    """Returns (white, black, zone): the redrawn beak's white and black, and the area of the trace it replaces."""
    from shapely.geometry import LineString
    lower = spline_open(BEAK_LOWER_EDGE)
    top = spline_open(BEAK_TOP_EDGE)
    left = spline_open(BEAK_UPPER_LEFT, 40)
    upper_fill = Polygon(np.r_[lower, top[1:], left[1:]]).buffer(0)
    lines = unary_union([LineString(lower).buffer(BEAK_LINE_W / 2), LineString(top).buffer(BEAK_LINE_W / 2),
                         Point(BEAK_LOWER_EDGE[0]).buffer(BEAK_CORNER_DOT, 32)])
    jaw_line = spline_loop(JAW_LOOP)
    jaw_black = unary_union([jaw_line.exterior.buffer(BEAK_LINE_W / 2), tapered_stroke(MOUTH_LINE)])
    jaw_white = jaw_line.difference(jaw_black)
    black = unary_union([lines, jaw_black])
    white = unary_union([upper_fill, jaw_white]).difference(black)
    shapes = unary_union([black, white])
    right = box(3.2, 8, 20, 18)
    zone = unary_union([shapes.buffer(0.15), shapes.intersection(right).convex_hull.buffer(0.8)])
    return white, black, zone


def draw_cap():
    from matplotlib.font_manager import FontProperties
    crown = spline_loop(CAP_CROWN)
    visor = spline_loop(CAP_VISOR).difference(crown)
    seam = spline_stroke(CAP_SEAM, CAP_SEAM_W).intersection(crown)
    g = glyph("BB", FontProperties(fname=str(FONT)))
    gx0, gy0, gx1, gy1 = g.bounds
    k = CAP_BB["height"] / (gy1 - gy0)
    g = affinity.scale(affinity.translate(g, -(gx0 + gx1) / 2, -(gy0 + gy1) / 2), k, k, origin=(0, 0))
    g = affinity.rotate(g, CAP_BB["angle"], origin=(0, 0))
    bb = affinity.translate(g, *CAP_BB["centre"]).buffer(CAP_BB["bold"]).intersection(crown.buffer(-0.3))
    return crown, visor, seam, bb


def build_regions():
    c = classify()
    red, white, black = c == 0, c == 1, c == 2
    bird = ndimage.binary_fill_holes(black)
    ny, nx = c.shape
    yy, xx = np.mgrid[:ny, :nx]
    r_px = np.hypot((xx + 0.5) / UPSCALE - CENTRE_PX[0], (yy + 0.5) / UPSCALE - CENTRE_PX[1])

    # White inside the bird: drop slits too narrow to print, then split raised (beak, eye) from cut-in details.
    bw = white & bird & ~black
    bw_ok = ndimage.binary_opening(bw, disk(MIN_WHITE / 2))
    lab, n = ndimage.label(bw_ok)
    x0, y0, x1, y1 = RAISED_WHITE_BOX_PX
    cms = ndimage.center_of_mass(bw_ok, lab, range(1, n + 1))
    keep = [i + 1 for i, (cy, cx) in enumerate(cms) if x0 <= cx / UPSCALE <= x1 and y0 <= cy / UPSCALE <= y1]
    raised = np.isin(lab, keep)
    inset = bw_ok & ~raised
    bird_red = (red | (bw & ~bw_ok)) & bird & ~black
    # Ring letters: white outside the bird that isn't connected to the field.
    lab, _ = ndimage.label(white & ~bird)
    field_labels = np.unique(lab[(r_px < R_IN_PX - 3) & (lab > 0)])
    letters = (lab > 0) & ~np.isin(lab, field_labels) & (r_px < R_OUT_PX)

    R = DIAMETER / 2
    r_in = R_IN_PX * K
    disc = Point(0, 0).buffer(R, 256)
    inner = Point(*px_to_mm(*INNER_CENTRE_PX)).buffer(r_in, 256)
    bird_p = mask_to_poly(bird).intersection(disc)
    text = fit_letters(letters).intersection(disc).difference(inner).difference(bird_p)
    raised_p = mask_to_poly(raised).intersection(bird_p)
    inset_p = mask_to_poly(inset).intersection(bird_p).difference(raised_p)
    red_p = mask_to_poly(bird_red).intersection(bird_p).difference(raised_p).difference(inset_p)
    # Grow the black evenly into what it borders (red by BLACK_GROW, white by WHITE_PULL), but not where red meets white
    # directly. Hairline gaps between the separately traced red and white aren't black; they go to the red.
    whites = unary_union([raised_p, inset_p])
    black_core = bird_p.difference(unary_union([whites, red_p])).buffer(-0.06).buffer(0.06)
    black_p = unary_union([black_core.buffer(WHITE_PULL), black_core.buffer(BLACK_GROW).difference(whites)])
    black_p = black_p.intersection(bird_p)
    raised_p = clean(raised_p.difference(black_p).buffer(-MIN_WHITE / 2).buffer(MIN_WHITE / 2))
    inset_p = clean(inset_p.difference(black_p).buffer(-MIN_WHITE / 2).buffer(MIN_WHITE / 2))
    whites = unary_union([raised_p, inset_p])
    red_p = clean(bird_p.difference(black_p).difference(whites).buffer(-MIN_RED / 2).buffer(MIN_RED / 2))
    black_p = clean(bird_p.difference(unary_union([whites, red_p])))
    ring = disc.difference(inner).difference(text).difference(bird_p)
    field = inner.difference(bird_p)

    # The beak: redrawn, replacing the trace in its area.
    beak_white, beak_black, zone = draw_beak()
    beak = unary_union([beak_white, beak_black])
    red_p, inset_p, black_p = (g.difference(zone) for g in (red_p, inset_p, black_p))
    red_p = clean(red_p.buffer(-MIN_RED / 2).buffer(MIN_RED / 2))
    # Close the hairline left between the traced white (cheek) and the new beak white, where no line separates them.
    raised_p = unary_union([raised_p.difference(zone), beak_white]).buffer(0.2).buffer(-0.2).difference(beak_black)
    raised_p = raised_p.difference(red_p)
    bird_p = unary_union([bird_p.difference(zone), beak]).buffer(0.2).buffer(-0.2)
    black_p = clean(bird_p.difference(unary_union([raised_p, inset_p, red_p])))
    ring = disc.difference(inner).difference(text).difference(bird_p)
    field = inner.difference(bird_p)

    # The cap: redrawn (crown red, "BB" white, visor + seam + rim black), on top of the traced bird.
    crown, visor, seam, bb = draw_cap()
    cap = unary_union([crown, visor]).buffer(CAP_RIM)
    bird_p = unary_union([bird_p, cap])
    ring = ring.difference(cap)
    field = field.difference(cap)
    cap_red = crown.difference(seam).difference(bb.buffer(0.0))
    cap_black = cap.difference(cap_red).difference(bb)

    # Keyring tab at 12 o'clock, filleted into the ring.
    tc = Point(0, R + TAB_CENTRE_OUT)
    tab = unary_union([tc.buffer(TAB_R, 128), box(-TAB_R, R - 2, TAB_R, R + TAB_CENTRE_OUT)])
    outline = unary_union([disc, tab]).buffer(TAB_FILLET, 256).buffer(-TAB_FILLET, 256)
    outline = outline.difference(tc.buffer(TAB_HOLE_D / 2, 96))
    tab = outline.difference(disc)

    regions = {   # name: (polygon, colour, top)
        "ring": (unary_union([ring, tab]), "red", RING_TOP),
        "field": (field, "white", FIELD_TOP),
        "text": (text, "white", TEXT_TOP),
        "bird": (red_p.difference(cap), "red", BIRD_TOP),
        "outline": (black_p.difference(cap), "black", BIRD_TOP),
        "beak": (raised_p.difference(cap), "white", BIRD_TOP),
        "details": (inset_p.difference(cap), "white", INSET_TOP),
        "cap": (cap_red, "red", CAP_TOP),
        "cap-lines": (cap_black, "black", CAP_TOP),
        "cap-bb": (bb, "white", CAP_TOP),
    }
    regions = {k: (clean(p), col, top) for k, (p, col, top) in regions.items()}
    return regions, outline, dict(tab_centre=(tc.x, tc.y), r_in=r_in)


def fill_small_holes(g, max_area=0.5):
    """Close pinholes left where colour regions nearly meet (they'd mesh as non-manifold pinch points)."""
    # A tiny close first heals zero-width slits and pieces that touch only along an edge (non-manifold when extruded).
    g = g.buffer(0.003, join_style="mitre").buffer(-0.003, join_style="mitre")
    out = [Polygon(p.exterior, [i for i in p.interiors if Polygon(i).area > max_area]) for p in getattr(g, "geoms", [g])]
    return shapely.set_precision(unary_union(out), 0.005).buffer(0)


def extrude(poly, z0, z1):
    parts = [trimesh.creation.extrude_polygon(g, z1 - z0) for g in getattr(poly, "geoms", [poly]) if g.area > 0.01]
    m = trimesh.util.concatenate(parts)
    m.apply_translation([0, 0, z0])
    return m


def to_manifold(mesh):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(mesh.vertices, np.float32),
                                 tri_verts=np.asarray(mesh.faces, np.uint32)))


def from_manifold(man):
    m = man.to_mesh()
    return trimesh.Trimesh(m.vert_properties[:, :3], m.tri_verts, process=False)


def tidy(m):
    """Merge coincident vertices and drop zero-area stray shells (manifold leaves a few at near-touching walls)."""
    m = trimesh.Trimesh(m.vertices, m.faces)
    parts = m.split(only_watertight=False)
    m = trimesh.util.concatenate([p for p in parts if p.area > 1e-3])
    return m


def check_body(m, name):
    """Watertight as saved: an STL reload merges coincident vertices, which exposes zero-width slivers."""
    re = trimesh.Trimesh(m.vertices, m.faces)   # merges vertices like a reload
    assert re.is_watertight and len(re.split(only_watertight=False)) == len(m.split(only_watertight=False)), name


def union(meshes):
    # simplify() collapses the sub-micron edges a boolean can leave where traced outlines nearly coincide; those would
    # otherwise merge into non-manifold edges when the STL is reloaded.
    u = m3d.Manifold.batch_boolean([to_manifold(m) for m in meshes], m3d.OpType.Add)
    return from_manifold(u.simplify(0.001))


COLOURS = {"red": "#c8202c", "white": "#f4f4f4", "black": "#222222"}


BG = (0.86, 0.9, 0.95)


def raster(regions, outline, extent, step):
    """Top-down height and colour images of the regions, as modelled."""
    from shapely import contains_xy
    x0, x1, y0, y1 = extent
    X, Y = np.meshgrid(np.arange(x0, x1, step), np.arange(y1, y0, -step))
    H = np.zeros(X.shape)
    C = np.ones(X.shape + (3,)) * BG
    inside = contains_xy(outline, X, Y)
    H[inside] = BASE
    C[inside] = matplotlib.colors.to_rgb(COLOURS["red"])
    for poly, col, top in regions.values():
        m = contains_xy(poly, X, Y) & inside
        H[m] = top
        C[m] = matplotlib.colors.to_rgb(COLOURS[col])
    return H, C, inside


FULL = (-31, 31, -31, 39)


def flat_render(regions, outline, path):
    """Source logo, print colours, and a height map, side by side."""
    H, C, inside = raster(regions, outline, FULL, 0.08)
    fig, axes = plt.subplots(1, 3, figsize=(24, 9.5))
    x0, y0 = px_to_mm(0, 300)
    x1, y1 = px_to_mm(300, 0)
    axes[0].imshow(Image.open(LOGO).convert("RGBA"), extent=(x0, x1, y0, y1))
    axes[0].set_title("source logo (300 px)")
    axes[1].imshow(C, extent=FULL)
    axes[1].set_title("print colours (mm)")
    Hm = np.ma.masked_where(~inside, H)
    im = axes[2].imshow(Hm, extent=FULL, cmap="viridis", vmin=BASE, vmax=CAP_TOP)
    axes[2].set_title("top heights (mm): " + ", ".join(f"{t:g}" for t in sorted({BASE, *[r[2] for r in regions.values()]})))
    fig.colorbar(im, ax=axes[2], fraction=0.04)
    for ax in axes:
        ax.set_xlim(FULL[0], FULL[1])
        ax.set_ylim(FULL[2], FULL[3])
        ax.grid(True, alpha=0.3)
    fig.suptitle(f"{NAME}: colour layout and heights", fontsize=15)
    fig.savefig(path, dpi=70, bbox_inches="tight")
    plt.close(fig)


def relief_render(regions, outline, path, zoom=None):
    """Lit top-down view of the coloured top surface, as modelled."""
    from matplotlib.colors import LightSource
    ext = zoom or FULL
    step = 0.03 if zoom else 0.06
    H, C, inside = raster(regions, outline, ext, step)
    shade = LightSource(azdeg=315, altdeg=35).hillshade(H, vert_exag=1.0, dx=step, dy=step)
    img = np.clip(C * (0.45 + 0.75 * shade[..., None]), 0, 1)
    img[~inside] = BG
    x0, x1, y0, y1 = ext
    fig, ax = plt.subplots(figsize=(11, 11 * (y1 - y0) / (x1 - x0)))
    ax.imshow(img, extent=ext)
    ax.set_title(f"{NAME}: top surface, lit from the upper left (mm)")
    fig.savefig(path, dpi=90, bbox_inches="tight")
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    RENDERS.mkdir(exist_ok=True)
    regions, outline, info = build_regions()

    # Each body is built as stacked slabs, one per height step: at each step, the union of the regions that are that
    # colour there, with hairline gaps and pinholes between neighbouring regions closed. Extruding regions one by one and
    # unioning them leaves zero-width pinch points where traced regions nearly touch.
    # Only the top COLOUR_DEPTH of a white/black region is that colour; red fills in below it. Fewer layers then hold
    # all three colours, so fewer AMS swaps and less purge.
    spans = {c: [] for c in COLOURS}          # colour -> [(poly, z0, z1)]
    for poly, col, top in regions.values():
        start = max(BASE, top - COLOUR_DEPTH.get(col, top))
        spans["red"].append((poly, BASE, start))
        spans[col].append((poly, start, top))
    levels = sorted({BASE, *[z for sp in spans.values() for _, z0, z1 in sp for z in (z0, z1)]})

    def slab_body(items, with_base, simplify=0.0):
        slabs = [extrude(outline, 0, BASE)] if with_base else []
        for lo, hi in zip(levels, levels[1:]):
            polys = [p for p, z0, z1 in items if z0 <= lo and z1 >= hi and z1 > z0]
            if not polys:
                continue
            area = fill_small_holes(unary_union(polys))
            if simplify:
                area = area.simplify(simplify).buffer(0)
            if not area.is_empty:
                slabs.append(extrude(area, lo, hi))
        return tidy(union(slabs))

    colour_meshes = {}
    for col in COLOURS:
        m = slab_body(spans[col], col == "red")
        check_body(m, col)
        colour_meshes[col] = m
        m.export(OUT / f"{NAME}-{col}.stl")

    # Single-colour solid: the same, over all regions regardless of colour.
    merged = slab_body([(p, BASE, t) for p, _, t in regions.values()], True)
    check_body(merged, "merged")
    merged.fix_normals()
    rep = mk.report(merged)
    merged.export(OUT / f"{NAME}.stl")

    scene = trimesh.Scene()
    for col, m in colour_meshes.items():
        scene.add_geometry(m, node_name=f"{col}", geom_name=f"{col}")
    scene.export(OUT / f"{NAME}-multicolor.3mf")

    # Viewer copies, standing up as it hangs (drawing Y -> Z), lifted so the bottom sits on Z=0.
    stand = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
    lift = -float(merged.bounds[0, 1])
    for col in COLOURS:   # lighter copies (outlines simplified to 0.05 mm) so the page stays under 65k vertices/mesh
        v = slab_body(spans[col], col == "red", simplify=0.05)
        v.apply_translation([0, 0, -CAP_TOP / 2])
        v.apply_transform(stand)
        v.apply_translation([0, 0, lift])
        v.export(RENDERS / f"view-{col}.stl")

    areas = {k: round(float(p.area), 1) for k, (p, _, _) in regions.items()}
    params = {
        "diameter": DIAMETER,
        "overall_width": round(float(merged.extents[0]), 1),
        "overall_height": round(float(merged.extents[1]), 1),
        "base": BASE, "field_top": FIELD_TOP, "ring_top": RING_TOP, "text_top": TEXT_TOP,
        "bird_top": BIRD_TOP, "inset_top": INSET_TOP, "cap_top": CAP_TOP,
        "tab_hole_d": TAB_HOLE_D,
        "tab_hole_wall": round(TAB_R - TAB_HOLE_D / 2, 2),
        "ring_inner_d": round(2 * info["r_in"], 1),
        "black_line_grow": BLACK_GROW, "smooth_sigma": SMOOTH, "min_white": MIN_WHITE,
    }
    report = {
        "scale_status": f"designer's choice: {DIAMETER:g} mm across the red ring (owner picked 55-60 mm)",
        "print": rep,
        "print_orientation": "flat on the bed, plain red back down (no supports)",
        "region_areas_mm2": areas,
        "params_mm": params,
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))

    flat_render(regions, outline, RENDERS / "layout.png")
    relief_render(regions, outline, RENDERS / "relief.png")
    relief_render(regions, outline, RENDERS / "relief-head.png", zoom=(-6, 18, 8, 23))
    relief_render(regions, outline, RENDERS / "relief-wing.png", zoom=(-28, -10, -12, 4))
    from render import render_sheet
    render_sheet(merged, str(RENDERS / "model.png"), title=f"{NAME}: print pose (flat), mm",
                 labels=["keychain"], sections_y=(0.0, 14.0), sections_x=(0.0, 2.0))


if __name__ == "__main__":
    main()
