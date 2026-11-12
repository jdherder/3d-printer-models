"""Reproducible build for the Black Bob Elementary logo keychain.

    python projects/black-bob-keychain/build.py        (~1 min)

source/logo-2026-11-12-school-site-300px.png (the school's logo; 300 px is the largest the site has)
  -> sub-pixel trace: redness and lightness upsampled 8x (cubic), each point classed red / white / black (grey visor)
  -> regions: red ring, white ring text, white field, and the bird (filled black outline) with its red body,
     white feather/bolt details, white beak, and cap (red + white "BB")
  -> thin black lines thickened and tiny white specks dropped so every colour region prints with a 0.4 mm nozzle
  -> "bezel + hero bird" heights (owner's pick, style A), all on a plain red base:
       red base 0.8 | white field 1.8 | red ring 2.8 | white text 3.2 | white details (cut in) 2.4 |
       red bird, black outline, white beak 3.0 | cap 3.4
  -> keyring tab above the ring at 12 o'clock
  -> output/black-bob-keychain.stl             single-colour print (all bodies merged)
  -> output/black-bob-keychain-multicolor.3mf  one object, four parts (red, white, black, grey) for the AMS
  -> output/black-bob-keychain-{red,white,black,grey}.stl
  -> output/report.json, renders/*.png
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / "tools")]

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import meshkit as mk  # noqa: E402
import numpy as np  # noqa: E402
import shapely  # noqa: E402
import trimesh  # noqa: E402
from PIL import Image  # noqa: E402
from scipy import ndimage  # noqa: E402
from shapely import affinity  # noqa: E402
from shapely.geometry import Point, Polygon, box  # noqa: E402
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
# Black lines in the logo are as thin as ~0.3 mm at 60 mm. Every black line grows by BLACK_GROW on each side (evenly,
# after smoothing, so it stays smooth and centred on the logo's line) to >= ~0.45 mm, which a 0.4 mm nozzle prints.
BLACK_GROW = 0.03
MIN_RED = 0.3              # red bits inside the bird narrower than this are dropped (become black)
MIN_RED_CAP = 0.25         # ... on the cap, the red around the "BB" is this thin in the logo (Arachne prints ~0.3)
MIN_WHITE = 0.3            # white details inside the bird narrower than this are dropped (become black)
COLOUR_DEPTH = {"white": 1.0, "black": 0.8, "grey": 0.8}   # thick enough that the red below doesn't show through
MIN_AREA = 0.15            # specks smaller than this (mm^2) are dropped
SMOOTH = 0.15              # traced outlines are smoothed along their length (Gaussian sigma, mm): no pixel steps or wobble
CORNER_DEG = 40            # ... except at corners sharper than this, which stay crisp
SLIVER = 0.03              # region slivers narrower than 2x this (from overlapping traces) are dropped

# --- Logo geometry (source pixels, measured from the 300 px image) ---------------------------------------------------
UPSCALE = 8
# Circles fitted (least squares) to the colour edges of the upscaled logo:
CENTRE_PX = (149.68, 149.83)       # x, y: centre of the outside of the red ring (the keychain's centre)
R_OUT_PX = 143.39                  # outside of the red ring (a thin white rim outside it is left off: too thin to print)
INNER_CENTRE_PX = (150.19, 150.04) # the inside of the ring is ~0.5 px off-centre in the logo; kept, so the field matches
R_IN_PX = 107.04
# Colours are told apart in two smooth fields, upsampled with a cubic spline (sub-pixel edges from the logo's own
# anti-aliasing): redness R - (G+B)/2 and lightness (G+B)/2. Each point goes to the nearest of the three colours in that
# plane, so any blend of two colours (an anti-aliased edge) splits at its midpoint. The cap's grey visor reads black.
PALETTE = {"red": (200, 20, 30), "white": (255, 250, 250), "black": (45, 15, 15)}
# Cap (crown + visor), outlined by hand in source pixels: everything of the bird inside it is raised to CAP_TOP.
CAP_PX = [(135, 71.5), (136.2, 58.7), (142.5, 52.5), (151.2, 49), (162.5, 49.5), (169, 53.5), (174, 58.5), (181, 60),
          (186, 65), (179, 68.5), (168, 69), (152, 73.5), (145, 73)]
# The "BB" on the cap is ~8 px tall in the logo: traced, it's a blob. It's set in this font instead (Bitstream Vera
# licence), fitted onto the traced blob (size, tilt, position): best overlap (0.70) of 7 bold serif and sans fonts.
# Its strokes are thickened by BB_BOLD each side so they print.
BB_FONT = HERE / "source" / "DejaVuSans-Bold.ttf"
BB_BOLD = 0.05
BB_SCALE = 0.92            # a touch smaller than the logo's, so the red around it shows
BB_BELOW_ROW_PX = 62       # the "BB" is above this source row; the visor below it
# The visor is grey in the logo (AMS slot 4). Grey is looked for only inside this outline (source px): lightness
# between GREY_LIGHT, plus the visor's white highlights.
VISOR_PX = [(145, 66.5), (152, 61.5), (160, 59.5), (170, 59), (180, 61.5), (184, 66), (176, 67.5), (165, 68),
            (155, 70), (147, 71)]
GREY_LIGHT = (70, 235)
# White bits of the bird that stand at bird height instead of being cut in: everything white whose centre is in this
# box (source px x0, y0, x1, y1): the beak (both jaws) and the eye.
RAISED_WHITE_BOX_PX = (150, 70, 235, 105)

K = DIAMETER / 2 / R_OUT_PX        # mm per source pixel


def px_to_mm(x, y):
    return (x - CENTRE_PX[0]) * K, -(y - CENTRE_PX[1]) * K


def classify():
    """Upscaled label image: 0 red, 1 white, 2 black, 3 transparent, 4 grey (the visor only)."""
    a = np.asarray(Image.open(LOGO).convert("RGBA")).astype(float)
    # Flatten onto white: transparent pixels hide arbitrary colours that would bleed into the upsampled edge.
    a[..., :3] = a[..., :3] * (a[..., 3:] / 255) + 255 * (1 - a[..., 3:] / 255)
    redness = a[..., 0] - (a[..., 1] + a[..., 2]) / 2
    light = (a[..., 1] + a[..., 2]) / 2
    up = lambda f: ndimage.zoom(f, UPSCALE, order=3)  # noqa: E731
    redness, light, alpha = up(redness), up(light), up(a[..., 3])
    pal = np.array([(r - (g + b) / 2, (g + b) / 2) for r, g, b in PALETTE.values()])
    d = (redness[..., None] - pal[:, 0]) ** 2 + (light[..., None] - pal[:, 1]) ** 2
    c = d.argmin(-1)
    # A sharp red/white edge dips briefly towards black in the spline, leaving a black hairline (~2 px). Real black
    # lines are ~10 px wide here: drop black narrower than ~4 px and give it to the nearer of red and white.
    black = c == 2
    hair = black & ~ndimage.binary_opening(black, iterations=2)
    c[hair] = d[hair][:, :2].argmin(-1)
    c[alpha < 128] = 3
    # Beyond the thin white rim is background (the logo's half-transparent edge pixels would read as a dark ring).
    yy, xx = np.mgrid[:c.shape[0], :c.shape[1]]
    c[np.hypot((xx + 0.5) / UPSCALE - CENTRE_PX[0], (yy + 0.5) / UPSCALE - CENTRE_PX[1]) > R_OUT_PX + 2] = 3
    # The cap's visor is grey (its own filament). Grey elsewhere is just anti-aliasing between black and white, so grey
    # is only looked for under the visor, and thin grey (edge blends) is dropped.
    from skimage.draw import polygon as fill_polygon
    visor = np.zeros(c.shape, bool)
    rr, cc = fill_polygon([y * UPSCALE for _, y in VISOR_PX], [x * UPSCALE for x, _ in VISOR_PX], c.shape)
    visor[rr, cc] = True
    grey = visor & (redness < 50) & (light > GREY_LIGHT[0]) & (light < GREY_LIGHT[1]) | (visor & (c == 1))
    grey = ndimage.binary_opening(ndimage.binary_closing(grey, disk(0.1)), disk(0.12))
    c[grey] = 4
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


def fit_bb(mask):
    """Font "BB" fitted onto the traced BB blob: the slant (and box) with the best overlap, then thickened."""
    from matplotlib.font_manager import FontProperties
    blob = mask_to_poly(mask, smooth=0)
    c = blob.centroid
    g0 = glyph("BB", FontProperties(fname=str(BB_FONT)))
    gx0, gy0, gx1, gy1 = g0.bounds
    g0 = affinity.translate(g0, -(gx0 + gx1) / 2, -(gy0 + gy1) / 2)
    best = None
    for ang in np.arange(-30, 30.1, 1.0):
        q = affinity.rotate(blob, -ang, origin=c)
        qx0, qy0, qx1, qy1 = q.bounds
        g = affinity.scale(g0, (qx1 - qx0) / (gx1 - gx0), (qy1 - qy0) / (gy1 - gy0), origin=(0, 0))
        g = affinity.rotate(affinity.translate(g, (qx0 + qx1) / 2, (qy0 + qy1) / 2), ang, origin=c)
        iou = g.intersection(blob).area / g.union(blob).area
        if best is None or iou > best[0]:
            best = (iou, g, ang)
    g = affinity.scale(best[1], BB_SCALE, BB_SCALE, origin=best[1].centroid)
    return g.buffer(BB_BOLD), blob


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

    # The cap, and the font "BB" in place of the traced one.
    cap = Polygon([px_to_mm(x, y) for x, y in CAP_PX]).buffer(0.3).buffer(-0.3).intersection(bird_p)
    cap_px = np.zeros_like(bird)
    from skimage.draw import polygon as fill_polygon
    rr, cc = fill_polygon([y * UPSCALE for _, y in CAP_PX], [x * UPSCALE for x, _ in CAP_PX], bird.shape)
    cap_px[rr, cc] = True
    # White in the cap: pieces on the crown (above BB_BELOW_ROW_PX) are the "BB"; below that it's the grey visor's
    # highlights, which go black.
    cap_white = white & cap_px & bird
    lab, n = ndimage.label(cap_white)
    cms = ndimage.center_of_mass(cap_white, lab, range(1, n + 1))
    bb_px = np.isin(lab, [i + 1 for i, (cy, _) in enumerate(cms) if cy / UPSCALE < BB_BELOW_ROW_PX])
    bb, bb_traced = fit_bb(bb_px)
    cap_poly_white = mask_to_poly(cap_white & ~bb_px, smooth=0).buffer(0.1)
    grey_p = mask_to_poly(c == 4).intersection(bird_p)
    raised_p = raised_p.difference(bb_traced.buffer(0.15)).difference(cap_poly_white)
    inset_p = inset_p.difference(bb_traced.buffer(0.15)).difference(cap_poly_white)
    red_p = unary_union([red_p, bb_traced.buffer(0.15).intersection(cap)]).difference(bb)

    # Grow every black line evenly (it stays centred on the logo's line). Hairline gaps between the separately traced
    # red and white aren't black: they're dropped from the black first and end up red.
    whites = unary_union([raised_p, inset_p])
    black_core = bird_p.difference(unary_union([whites, red_p, bb, grey_p])).buffer(-0.06).buffer(0.06)
    black_p = black_core.buffer(BLACK_GROW).intersection(bird_p).difference(bb)
    grey_p = clean(grey_p.difference(black_p))
    raised_p = clean(raised_p.difference(black_p).buffer(-MIN_WHITE / 2).buffer(MIN_WHITE / 2))
    inset_p = clean(inset_p.difference(black_p).buffer(-MIN_WHITE / 2).buffer(MIN_WHITE / 2))
    whites = unary_union([raised_p, inset_p, bb, grey_p])
    red_all = bird_p.difference(black_p).difference(whites)
    red_p = unary_union([red_all.difference(cap).buffer(-MIN_RED / 2).buffer(MIN_RED / 2),
                         red_all.intersection(cap).buffer(-MIN_RED_CAP / 2).buffer(MIN_RED_CAP / 2)])
    red_p = clean(red_p)
    black_p = clean(bird_p.difference(unary_union([whites, red_p])))
    ring = disc.difference(inner).difference(text).difference(bird_p)
    field = inner.difference(bird_p)

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
        "cap": (red_p.intersection(cap), "red", CAP_TOP),
        "cap-lines": (black_p.intersection(cap), "black", CAP_TOP),
        "cap-bb": (bb.intersection(cap), "white", CAP_TOP),
        "visor": (grey_p, "grey", CAP_TOP),
    }
    regions = {k: (clean(p), col, top) for k, (p, col, top) in regions.items()}
    return regions, outline, dict(tab_centre=(tc.x, tc.y), r_in=r_in)


def partition(regions, outline, simplify=0.0):
    """One planar partition of the keychain: every region outline noded together (on a 1 µm grid), so neighbouring
    faces share exactly the same edges and vertices. Returns [(face polygon, region name)]. Faces in hairline gaps
    between regions go to the nearest region."""
    from shapely.strtree import STRtree
    names = list(regions)
    polys = [regions[n][0].simplify(simplify) if simplify else regions[n][0] for n in names]
    rings = []
    for g in [outline, *polys]:
        for p in getattr(g, "geoms", [g]):
            rings += [p.exterior, *p.interiors]
    lines = shapely.union_all([shapely.LineString(r.coords) for r in rings], grid_size=0.001)
    faces = list(shapely.get_parts(shapely.polygonize(shapely.get_parts(lines))))
    tree = STRtree(polys)
    out = []
    for f in faces:
        pt = f.representative_point()
        if not outline.contains(pt):
            continue                                         # the keyring hole
        hits = [i for i in tree.query(pt, predicate="within")]
        i = max(hits) if hits else int(tree.nearest(pt))     # later regions win, like the renders
        out.append((shapely.geometry.polygon.orient(f, 1.0), names[i]))
    return out


def column_mesh(faces, span):
    """Watertight mesh of vertical columns, one per face: span(name) -> (z0, z1) or None. Each face gets a top and a
    bottom cap; walls go up only where neighbouring columns differ, split at every height used anywhere so all
    vertices line up. Built directly from the shared partition, so no booleans (and no near-coincident edges)."""
    spans = [span(n) for _, n in faces]
    levels = sorted({z for sp in spans if sp for z in sp})
    verts, index, tris = [], {}, []

    def vid(x, y, z):
        key = (x, y, z)
        if key not in index:
            index[key] = len(verts)
            verts.append(key)
        return index[key]

    owner = {}
    for i, (f, _) in enumerate(faces):
        for ring in [f.exterior, *f.interiors]:
            c = list(ring.coords)
            for p, q in zip(c, c[1:]):
                owner[(p, q)] = i
    for i, ((f, _), sp) in enumerate(zip(faces, spans)):
        if not sp:
            continue
        z0, z1 = sp
        # Constrained Delaunay keeps every ring edge and adds no vertices, so caps meet walls and neighbours exactly.
        for t in shapely.get_parts(shapely.constrained_delaunay_triangles(f)):
            a, b, c = (tuple(map(float, xy)) for xy in list(t.exterior.coords)[:3])
            ccw = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) > 0
            if not ccw:
                b, c = c, b
            tris.append((vid(*a, z1), vid(*b, z1), vid(*c, z1)))      # top, facing up
            tris.append((vid(*a, z0), vid(*c, z0), vid(*b, z0)))      # bottom, facing down
        for ring in [f.exterior, *f.interiors]:
            c = list(ring.coords)
            for p, q in zip(c, c[1:]):
                j = owner.get((q, p))
                other = spans[j] if j is not None else None
                for za, zb in zip(levels, levels[1:]):
                    if not (z0 <= za and zb <= z1):
                        continue
                    if other and other[0] <= za and zb <= other[1]:
                        continue                                       # neighbour fills it: no wall
                    pa, qa, qb, pb = vid(*p, za), vid(*q, za), vid(*q, zb), vid(*p, zb)
                    tris += [(pa, qa, qb), (pa, qb, pb)]               # faces outward (right of p -> q)
    return trimesh.Trimesh(np.array(verts), np.array(tris), process=False)


def pinches(m):
    """(x, y, z0, z1) of vertical edges shared by 4 faces: two columns touching only along a corner."""
    from collections import Counter
    e = np.sort(m.faces[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2), axis=1)
    count = Counter(map(tuple, e))
    out = []
    for (i, j), n in count.items():
        a, b = m.vertices[i], m.vertices[j]
        if n > 2 and a[0] == b[0] and a[1] == b[1]:
            out.append((a[0], a[1], min(a[2], b[2]), max(a[2], b[2])))
    return out


def separate_pinches(regions, outline, spans, r=0.02, rounds=6):
    """Partition the regions, then wherever two columns of a body touch only at a corner (non-manifold), hand a
    tiny disc (radius r) of one of them to a neighbour and partition again. Changes regions in place."""
    for _ in range(rounds):
        faces = partition(regions, outline)
        found = False
        for span in spans.values():
            for x, y, z0, z1 in pinches(column_mesh(faces, span)):
                p = Point(x, y)
                around = [(f, n) for f, n in faces if f.boundary.distance(p) < 1e-9]
                inside = [(f, n) for f, n in around if span(n) and span(n)[0] <= z0 and z1 <= span(n)[1]]
                outside = [(f, n) for f, n in around if (f, n) not in inside]
                if not inside or not outside:
                    continue
                _, c = min(inside, key=lambda fn: fn[0].area)
                _, b = max(outside, key=lambda fn: fn[0].area)
                disc = p.buffer(r, 16)
                cut = regions[c][0].intersection(disc)
                regions[c] = (regions[c][0].difference(disc), *regions[c][1:])
                regions[b] = (unary_union([regions[b][0], cut]), *regions[b][1:])
                found = True
        if not found:
            return faces
    raise AssertionError("couldn't separate pinch points")


COLOURS = {"red": "#c8202c", "white": "#f4f4f4", "black": "#222222", "grey": "#8c8f94"}


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


def compare_render(regions, outline, path, ext=(-6, 18, 8, 23)):
    """The logo next to the model (lit top surface), same area and scale: for checking the trace by eye."""
    from matplotlib.colors import LightSource
    step = 0.03
    H, C, inside = raster(regions, outline, ext, step)
    shade = LightSource(azdeg=315, altdeg=35).hillshade(H, vert_exag=1.0, dx=step, dy=step)
    img = np.clip(C * (0.45 + 0.75 * shade[..., None]), 0, 1)
    img[~inside] = BG
    x0, y0 = px_to_mm(0, 300)
    x1, y1 = px_to_mm(300, 0)
    fig, axes = plt.subplots(1, 2, figsize=(22, 7.5))
    axes[0].imshow(Image.open(LOGO).convert("RGBA"), extent=(x0, x1, y0, y1), interpolation="bicubic")
    axes[0].set_title("logo (300 px)", fontsize=16)
    axes[1].imshow(img, extent=ext)
    axes[1].set_title("keychain, as modelled (mm)", fontsize=16)
    for ax in axes:
        ax.set_xlim(ext[0], ext[1])
        ax.set_ylim(ext[2], ext[3])
    fig.savefig(path, dpi=60, bbox_inches="tight")
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    RENDERS.mkdir(exist_ok=True)
    regions, outline, info = build_regions()

    # Every body is built from one shared planar partition (see column_mesh). Only the top COLOUR_DEPTH of a
    # white/black/grey region is that colour; red fills in below it, so fewer layers hold several colours (fewer AMS
    # swaps, less purge). The red also includes the base under everything.
    def colour_span(col):
        def span(name):
            _, c, top = regions[name]
            start = max(BASE, top - COLOUR_DEPTH.get(c, top))
            if col == "red":
                return (0.0, start if c != "red" else top)
            return (start, top) if c == col else None
        return span

    def check(m, name):
        assert m.is_watertight and m.is_winding_consistent, f"{name} body not watertight"

    spans = {col: colour_span(col) for col in COLOURS}
    spans["merged"] = lambda n: (0.0, regions[n][2])
    faces = separate_pinches(regions, outline, spans)

    colour_meshes = {}
    for col in COLOURS:
        m = column_mesh(faces, spans[col])
        check(m, col)
        colour_meshes[col] = m
        m.export(OUT / f"{NAME}-{col}.stl")

    merged = column_mesh(faces, spans["merged"])
    check(merged, "merged")
    rep = mk.report(merged)
    merged.export(OUT / f"{NAME}.stl")

    scene = trimesh.Scene()
    for col, m in colour_meshes.items():
        scene.add_geometry(m, node_name=f"{col}", geom_name=f"{col}")
    scene.export(OUT / f"{NAME}-multicolor.3mf")

    # Viewer copies, standing up as it hangs (drawing Y -> Z), lifted so the bottom sits on Z=0.
    stand = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
    lift = -float(merged.bounds[0, 1])
    light_faces = partition(regions, outline, simplify=0.05)   # lighter copies so the page stays under 65k verts/mesh
    for col in COLOURS:
        v = column_mesh(light_faces, colour_span(col))
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
    compare_render(regions, outline, RENDERS / "compare-head.png")
    from render import render_sheet
    render_sheet(merged, str(RENDERS / "model.png"), title=f"{NAME}: print pose (flat), mm",
                 labels=["keychain"], sections_y=(0.0, 14.0), sections_x=(0.0, 2.0))


if __name__ == "__main__":
    main()
