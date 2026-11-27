"""Reproducible build for the blue mana keychain (in the style of black-bob-keychain).

    python projects/blue-mana-keychain/build.py        (~1-2 min)

source/blue-mana-2026-11-27-sticker-570px.jpg (the owner's sticker image)
  -> outline: the sticker's grey die-cut line, filled (the white sticker border becomes the keychain's rim)
  -> sub-pixel trace: the image is lightly blurred (JPEG noise), upsampled 4x (cubic), and each point is classed as
     white, cyan, royal blue or slate. Anti-aliased edges are blends of two colours: they split at their midpoint
     instead of turning into a third colour (a royal/white blend looks slate otherwise).
  -> clean-up for printing and to drop the sticker's distressed texture: specks, scratches and hairlines below what a
     0.4 mm nozzle prints are merged into their surroundings
  -> layered heights on a plain white base (4 AMS colours): white field lowest, slate waves behind, royal ring and
     swirls, cyan swirls in front, the drop highest with its highlight cut in
  -> keyring tab at 12 o'clock
  -> 3 print colours (v2): the slate waves print royal blue, at their own height (PRINT_AS)
  -> output/blue-mana-keychain.stl              single-colour print (all bodies merged)
  -> output/blue-mana-keychain-multicolor.3mf   one object, three parts (white, royal, cyan) for the AMS
  -> output/blue-mana-keychain-{white,royal,cyan}.stl
  -> output/blue-mana-keychain-4colour-multicolor.3mf   v1's four colours (white, slate, royal, cyan), same shapes
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
import trimesh  # noqa: E402
from PIL import Image  # noqa: E402
from relief import clean, column_mesh, mask_to_poly, partition, separate_pinches  # noqa: E402
from scipy import ndimage  # noqa: E402
from shapely.geometry import Point, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

OUT = HERE / "output"
RENDERS = HERE / "renders"
ART = HERE / "source" / "blue-mana-2026-11-27-sticker-570px.jpg"
NAME = "blue-mana-keychain"

# --- Design parameters (mm) ------------------------------------------------------------------------------------------
WIDTH = 60.0               # across the sticker outline (die-cut line), left to right; the tab adds to the height
BASE = 0.8                 # plain white base under everything (4 layers): the back is white, colour swaps are above it
FIELD_TOP = 2.0            # white: the field round the drop, the gaps between the swirls and the sticker's border rim
SLATE_TOP = 2.4            # slate-blue waves: the back layer of the swirl ring
ROYAL_TOP = 2.8            # royal-blue ring band and swirls: the middle layer
CYAN_TOP = 3.2             # cyan swirls: the front layer
DROP_TOP = 3.6             # the drop: the highest point
HIGHLIGHT_TOP = 3.0        # the drop's white highlight, cut 0.6 into it
TAB_R = 4.5                # keyring tab (radius), at 12 o'clock
TAB_HOLE_D = 4.0           # for a split ring
TAB_CENTRE_OUT = 3.0       # tab/hole centre, this far above the top of the outline
TAB_FILLET = 1.5           # rounds the tab-to-outline corners
# Colour over the white base: below this depth a column is white (fewer layers mix colours: fewer swaps, less purge).
# Blues hide white well; the lighter slate and cyan get a little more.
COLOUR_DEPTH = {"royal": 0.8, "slate": 1.0, "cyan": 1.0}
# v2 (owner: try 3 colours): the slate waves print royal blue, frees an AMS slot and cuts purge. They keep their own
# height (back layer, 2.4), so the relief still separates them from the royal swirls (2.8). Folding slate into cyan
# instead washed the ring out (renders/three-colour-options.png). The 4-colour version is still built (FOUR_COLOUR_3MF).
PRINT_AS = {"slate": "royal"}
MIN_LINE = 0.3             # colour features (lines, tips) narrower than this are merged away: below what prints
MIN_GAP = 0.25             # white gaps between swirls narrower than this close up (the texture's scratches)
MIN_AREA = 0.2             # islands and holes smaller than this (mm^2) merge into their surroundings (texture specks)
SMOOTH = 0.12              # traced outlines are smoothed along their length (Gaussian sigma, mm)
CORNER_DEG = 45            # ... except at corners sharper than this (swirl tips), which stay crisp

# --- Artwork (source pixels, 570 px JPEG) ----------------------------------------------------------------------------
UPSCALE = 4
BLUR_PX = 0.6              # source-pixel blur before upsampling: JPEG ringing and the texture's 1 px grain
# Print colours, measured from the image (k-means). The image's other shades are blends of these (edges) or the
# distressed texture.
PALETTE = {"white": (254, 255, 255), "cyan": (30, 169, 228), "royal": (3, 101, 177), "slate": (116, 156, 189)}
BLEND_BIAS = 12            # a pixel is read as a blend of two colours only if that fits this much better than one colour
DROP_SEED_PX = (290, 300)  # a point inside the drop (x, y)
DIE_CUT_GREY = dict(max_sat=25, light=(120, 235))   # the grey die-cut line round the sticker


def load():
    return np.asarray(Image.open(ART).convert("RGB")).astype(float)


def outline_mask(img):
    """The sticker shape (source px): the grey die-cut line's largest piece, filled."""
    sat = img.max(-1) - img.min(-1)
    light = img.mean(-1)
    lo, hi = DIE_CUT_GREY["light"]
    grey = (sat < DIE_CUT_GREY["max_sat"]) & (light > lo) & (light < hi)
    lab, n = ndimage.label(grey, np.ones((3, 3)))
    line = lab == np.argmax(np.bincount(lab.ravel())[1:]) + 1
    return ndimage.binary_fill_holes(ndimage.binary_closing(line, iterations=2))


def classify(img):
    """Label every upsampled pixel with a palette index. A pixel near the line between two palette colours (an
    anti-aliased edge) goes to whichever end it's nearer, so blends split at their midpoint."""
    sm = np.stack([ndimage.gaussian_filter(img[..., c], BLUR_PX) for c in range(3)], -1)
    up = np.stack([ndimage.zoom(sm[..., c], UPSCALE, order=3) for c in range(3)], -1)
    pal = np.array(list(PALETTE.values()), float)
    flat = up.reshape(-1, 3)
    best = np.full(len(flat), np.inf)
    lab = np.zeros(len(flat), int)
    for i, c in enumerate(pal):                                   # one colour
        d = np.linalg.norm(flat - c, axis=1)
        m = d < best
        best[m], lab[m] = d[m], i
    for i in range(len(pal)):                                     # a blend of two
        for j in range(i + 1, len(pal)):
            a, b = pal[i], pal[j]
            t = np.clip(((flat - a) @ (b - a)) / ((b - a) @ (b - a)), 0, 1)
            d = np.linalg.norm(flat - (a + t[:, None] * (b - a)), axis=1) + BLEND_BIAS
            m = d < best
            best[m] = d[m]
            lab[m] = np.where(t[m] < 0.5, i, j)
    return lab.reshape(up.shape[:2])


def disk(r_px):
    r = max(1, int(round(r_px)))
    y, x = np.mgrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


def fill_from_neighbours(lab, keep):
    """Pixels not in keep take the label of the nearest kept pixel."""
    _, (iy, ix) = ndimage.distance_transform_edt(~keep, return_indices=True)
    return lab[iy, ix]


def tidy(lab, inside, mm_per_px):
    """Make every colour region printable: drop features thinner than a nozzle line and specks from the texture."""
    names = list(PALETTE)
    white = names.index("white")
    area_px = MIN_AREA / mm_per_px ** 2
    for _ in range(2):
        # Thin white (texture scratches, JPEG fringes) closes up: opening the white removes it.
        w = (lab == white) & inside
        keep_w = ndimage.binary_opening(w, disk(MIN_GAP / 2 / mm_per_px)) | ~inside
        lab = np.where(w & ~keep_w, -1, lab)
        # Thin colour (hairlines, sharp tips below a line width) is merged away the same way, colour by colour.
        for i, n in enumerate(names):
            if i == white:
                continue
            c = lab == i
            lab = np.where(c & ~ndimage.binary_opening(c, disk(MIN_LINE / 2 / mm_per_px)), -1, lab)
        lab = fill_from_neighbours(lab, lab >= 0)
        # Small islands of any colour (specks, holes in a region) take their surroundings' colour.
        for i in range(len(names)):
            cl, n = ndimage.label((lab == i) & inside)
            small = np.bincount(cl.ravel()) < area_px
            small[0] = False
            lab = np.where(small[cl], -1, lab)
        lab = fill_from_neighbours(lab, lab >= 0)
    return np.where(inside, lab, -1)


def build_regions():
    img = load()
    h, w = img.shape[:2]
    inside_src = outline_mask(img)
    ys, xs = np.nonzero(inside_src)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    k = WIDTH / (x1 - x0)                                         # mm per source pixel
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2

    def to_mm(col, row):                                          # upsampled pixel centres -> mm
        return ((col + 0.5) / UPSCALE - cx) * k, (cy - (row + 0.5) / UPSCALE) * k

    inside = ndimage.zoom(inside_src.astype(float), UPSCALE, order=1) > 0.5
    lab = tidy(classify(img), inside, k / UPSCALE)
    names = list(PALETTE)

    def poly(mask, **kw):
        return mask_to_poly(mask, to_mm, smooth=SMOOTH, corner_deg=CORNER_DEG, min_area=MIN_AREA, **kw)

    outline = mask_to_poly(inside, to_mm, smooth=0.4, corner_deg=60, min_area=1.0)
    outline = max(getattr(outline, "geoms", [outline]), key=lambda p: p.area)

    # The drop: the royal piece at the centre, and the white highlight inside it.
    royal = lab == names.index("royal")
    cl, _ = ndimage.label(royal)
    drop_mask = cl == cl[int(DROP_SEED_PX[1] * UPSCALE), int(DROP_SEED_PX[0] * UPSCALE)]
    drop_filled = ndimage.binary_fill_holes(drop_mask)
    highlight_mask = drop_filled & ~drop_mask
    drop = poly(drop_filled)

    # Keyring tab: a disc above the top of the outline, joined to it with rounded corners, with a hole.
    top = outline.bounds[3]
    tc = Point(0.0, top + TAB_CENTRE_OUT)
    tab = unary_union([tc.buffer(TAB_R, 64), box(-TAB_R, top - 6, TAB_R, tc.y)])
    closed = unary_union([outline, tab]).buffer(TAB_FILLET, 64).buffer(-TAB_FILLET, 64)
    # Fillet only the tab's inside corners; the rest of the outline keeps its scallops.
    body = unary_union([outline, tab, closed.intersection(box(-TAB_R - 4, top - 4, TAB_R + 4, top + 20))])
    hole = tc.buffer(TAB_HOLE_D / 2, 64)
    body = body.difference(hole)

    regions = {"field": (body, "white", FIELD_TOP)}
    for n, top_z in (("slate", SLATE_TOP), ("royal", ROYAL_TOP), ("cyan", CYAN_TOP)):
        m = lab == names.index(n)
        if n == "royal":
            m &= ~drop_filled
        regions[n] = (poly(m).intersection(outline), n, top_z)
    regions["drop"] = (drop, "royal", DROP_TOP)
    regions["highlight"] = (poly(highlight_mask), "white", HIGHLIGHT_TOP)
    regions = {kk: (clean(p, min_area=MIN_AREA), c, t) for kk, (p, c, t) in regions.items()}
    info = dict(mm_per_src_px=k, centre_px=(cx, cy), tab_centre=(tc.x, tc.y), lab=lab, to_mm=to_mm,
                src_extent=(-cx * k, (w - cx) * k, (cy - h) * k, cy * k))
    return regions, body, info


# --- Renders ---------------------------------------------------------------------------------------------------------
COLOURS = {"white": "#f4f4f4", "slate": "#7497bd", "royal": "#0a64b0", "cyan": "#22a8e3"}
BG = (0.86, 0.86, 0.84)


def raster(regions, outline, extent, step):
    from shapely import contains_xy
    x0, x1, y0, y1 = extent
    X, Y = np.meshgrid(np.arange(x0, x1, step), np.arange(y1, y0, -step))
    H = np.zeros(X.shape)
    C = np.ones(X.shape + (3,)) * BG
    inside = contains_xy(outline, X, Y)
    H[inside] = BASE
    C[inside] = matplotlib.colors.to_rgb(COLOURS["white"])
    for poly, col, top in regions.values():
        m = contains_xy(poly, X, Y) & inside
        H[m] = top
        C[m] = matplotlib.colors.to_rgb(COLOURS[col])
    return H, C, inside


def lit(regions, outline, ext, step):
    from matplotlib.colors import LightSource
    H, C, inside = raster(regions, outline, ext, step)
    shade = LightSource(azdeg=315, altdeg=35).hillshade(H, vert_exag=1.0, dx=step, dy=step)
    img = np.clip(C * (0.45 + 0.75 * shade[..., None]), 0, 1)
    img[~inside] = BG
    return img, H, inside


def full_extent(outline):
    x0, y0, x1, y1 = outline.bounds
    return (x0 - 1, x1 + 1, y0 - 1, y1 + 1)


def layout_render(regions, outline, info, path):
    """Source art, print colours, and a height map, side by side."""
    ext = full_extent(outline)
    H, C, inside = raster(regions, outline, ext, 0.08)
    fig, axes = plt.subplots(1, 3, figsize=(24, 9.5))
    axes[0].imshow(Image.open(ART), extent=info["src_extent"])
    axes[0].set_title("source art (570 px)")
    axes[1].imshow(C, extent=ext)
    axes[1].set_title("print colours (mm)")
    im = axes[2].imshow(np.ma.masked_where(~inside, H), extent=ext, cmap="viridis", vmin=BASE, vmax=DROP_TOP)
    axes[2].set_title("top heights (mm): " + ", ".join(f"{t:g}" for t in sorted({BASE, *[r[2] for r in regions.values()]})))
    fig.colorbar(im, ax=axes[2], fraction=0.04)
    for ax in axes:
        ax.set_xlim(ext[0], ext[1])
        ax.set_ylim(ext[2], ext[3])
        ax.grid(True, alpha=0.3)
    fig.suptitle(f"{NAME}: colour layout and heights", fontsize=15)
    fig.savefig(path, dpi=70, bbox_inches="tight")
    plt.close(fig)


def relief_render(regions, outline, path, zoom=None):
    ext = zoom or full_extent(outline)
    step = 0.025 if zoom else 0.05
    img, _, _ = lit(regions, outline, ext, step)
    x0, x1, y0, y1 = ext
    fig, ax = plt.subplots(figsize=(11, 11 * (y1 - y0) / (x1 - x0)))
    ax.imshow(img, extent=ext)
    ax.set_title(f"{NAME}: top surface, lit from the upper left (mm)")
    fig.savefig(path, dpi=90, bbox_inches="tight")
    plt.close(fig)


def compare_render(regions, outline, info, path, ext):
    """The art next to the model (lit top surface), same area and scale: for checking the trace by eye."""
    img, _, _ = lit(regions, outline, ext, 0.025)
    fig, axes = plt.subplots(1, 2, figsize=(22, 11 * (ext[3] - ext[2]) / (ext[1] - ext[0])))
    axes[0].imshow(Image.open(ART), extent=info["src_extent"], interpolation="bicubic")
    axes[0].set_title("sticker art", fontsize=16)
    axes[1].imshow(img, extent=ext)
    axes[1].set_title("keychain, as modelled (mm)", fontsize=16)
    for ax in axes:
        ax.set_xlim(ext[0], ext[1])
        ax.set_ylim(ext[2], ext[3])
    fig.savefig(path, dpi=60, bbox_inches="tight")
    plt.close(fig)


def options_render(regions, outline, path):
    """The 4-colour version next to the two ways of printing it in 3 colours."""
    ext = full_extent(outline)
    fig, axes = plt.subplots(1, 3, figsize=(27, 10.5))
    for ax, (title, as_) in zip(axes, [("v1: 4 colours", {}), ("3 colours: slate printed royal (v2)", {"slate": "royal"}),
                                       ("3 colours: slate printed cyan", {"slate": "cyan"})]):
        img, _, _ = lit(recolour(regions, as_), outline, ext, 0.06)
        ax.imshow(img, extent=ext)
        ax.set_title(title, fontsize=18)
        ax.axis("off")
    fig.savefig(path, dpi=60, bbox_inches="tight")
    plt.close(fig)


def recolour(regions, as_):
    return {k: (p, as_.get(c, c), t) for k, (p, c, t) in regions.items()}


def main():
    OUT.mkdir(exist_ok=True)
    RENDERS.mkdir(exist_ok=True)
    regions, outline, info = build_regions()

    # Only the top COLOUR_DEPTH of a coloured region is that colour; white fills in below it (and is the base).
    # as_ maps an art colour to the filament it prints in.
    def colour_span(col, as_):
        def span(name):
            _, c, top = regions[name]
            c = as_.get(c, c)
            start = max(BASE, top - COLOUR_DEPTH.get(c, top))
            if col == "white":
                return (0.0, top) if c == "white" else (0.0, start)
            return (start, top) if c == col else None
        return span

    def check(m, name):
        assert m.is_watertight and m.is_winding_consistent, f"{name} body not watertight"

    printed = [c for c in COLOURS if c not in PRINT_AS]
    variants = {"": (PRINT_AS, printed), "-4colour": ({}, list(COLOURS))}
    spans = {f"{col}{v}": colour_span(col, as_) for v, (as_, cols) in variants.items() for col in cols}
    spans["merged"] = lambda n: (0.0, regions[n][2])
    faces = separate_pinches(regions, outline, spans, r=0.08, rounds=12)   # manifold for both colourings

    for v, (as_, cols) in variants.items():
        scene = trimesh.Scene()
        for col in cols:
            m = column_mesh(faces, spans[f"{col}{v}"])
            check(m, col + v)
            scene.add_geometry(m, node_name=col, geom_name=col)
            if not v:
                m.export(OUT / f"{NAME}-{col}.stl")
        scene.export(OUT / f"{NAME}{v}-multicolor.3mf")

    merged = column_mesh(faces, spans["merged"])
    check(merged, "merged")
    rep = mk.report(merged)
    merged.export(OUT / f"{NAME}.stl")

    # Viewer copies, standing up as it hangs (drawing Y -> Z), lifted so the bottom sits on Z=0.
    stand = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
    lift = -float(merged.bounds[0, 1])
    light_faces = partition(regions, outline, simplify=0.05)
    for col in printed:
        v = column_mesh(light_faces, colour_span(col, PRINT_AS))
        v.apply_translation([0, 0, -DROP_TOP / 2])
        v.apply_transform(stand)
        v.apply_translation([0, 0, lift])
        v.export(RENDERS / f"view-{col}.stl")

    params = {
        "width": WIDTH,
        "overall_width": round(float(merged.extents[0]), 1),
        "overall_height": round(float(merged.extents[1]), 1),
        "base": BASE, "field_top": FIELD_TOP, "slate_top": SLATE_TOP, "royal_top": ROYAL_TOP,
        "cyan_top": CYAN_TOP, "drop_top": DROP_TOP, "highlight_top": HIGHLIGHT_TOP,
        "tab_hole_d": TAB_HOLE_D, "tab_hole_wall": round(TAB_R - TAB_HOLE_D / 2, 2),
        "print_colours": printed, "print_as": PRINT_AS,
        "min_line": MIN_LINE, "min_gap": MIN_GAP, "mm_per_source_px": round(info["mm_per_src_px"], 4),
    }
    report = {
        "scale_status": f"designer's choice: {WIDTH:g} mm across the sticker outline",
        "print": rep,
        "print_orientation": "flat on the bed, plain white back down (no supports)",
        "region_areas_mm2": {k: round(float(p.area), 1) for k, (p, _, _) in regions.items()},
        "params_mm": params,
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))

    options_render(regions, outline, RENDERS / "three-colour-options.png")
    regions = recolour(regions, PRINT_AS)
    layout_render(regions, outline, info, RENDERS / "layout.png")
    relief_render(regions, outline, RENDERS / "relief.png")
    relief_render(regions, outline, RENDERS / "relief-swirls.png", zoom=(-30, -8, 2, 22))
    compare_render(regions, outline, info, RENDERS / "compare-swirls.png", ext=(-30, -8, 2, 22))
    from render import render_sheet
    render_sheet(merged, str(RENDERS / "model.png"), title=f"{NAME}: print pose (flat), mm",
                 labels=["keychain"], sections_y=(0.0, 18.0), sections_x=(0.0, -20.0))


if __name__ == "__main__":
    main()
