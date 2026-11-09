"""Reproducible build for the Santa-hat bat ornament.

    python projects/santa-bat-ornament/build.py        (~10 s)

source/photo-2026-11-09-wall-bats.jpg (the paper bats on the owner's wall)
  -> bat silhouette: dark pixels around the Santa-hat bat, cleaned and traced
  -> Santa hat: hand-traced polygons in photo pixels (the hat's white paper is too close to the wall colour to threshold)
  -> perspective fix (the photo looks along the wall, so the bat is squashed sideways), scale to ORNAMENT_SIZE_MM
  -> layered like the paper craft, to keep AMS colour swaps (and purge waste) to the last few layers:
       a plain black base (whole outline; a small hanging hole through the pom-pom), with a thin red hat and a slightly thicker white
       brim + pom-pom (fur) printed on top of it. The back is a plain black silhouette.
  -> output/santa-bat-ornament.stl            single-colour print (all bodies merged)
  -> output/santa-bat-ornament-multicolor.3mf one object, three parts (assign filaments per part with the AMS lite)
  -> output/santa-bat-ornament-{bat,hat,trim}.stl   the colour bodies on their own
  -> output/santa-bat-ornament-outline.svg   outline in mm (for Fusion, a vinyl cutter, or more paper bats)
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
import trimesh  # noqa: E402
from matplotlib.patches import Polygon as MplPolygon  # noqa: E402
from PIL import Image  # noqa: E402
from scipy import ndimage  # noqa: E402
from shapely import affinity  # noqa: E402
from shapely.geometry import Point, Polygon  # noqa: E402
from shapely.ops import unary_union  # noqa: E402
from skimage import measure  # noqa: E402

OUT = HERE / "output"
RENDERS = HERE / "renders"
PHOTO = HERE / "source" / "photo-2026-11-09-wall-bats.jpg"

# --- Design parameters (mm) ------------------------------------------------------------------------------------------
ORNAMENT_SIZE_MM = 50.0    # wing tip to wing tip, wings level (owner, 2026-11-09)
THICKNESS = 2.0            # black base, the whole outline (10 layers at 0.2, all one colour)
HAT_LAYER = 0.6            # red hat on top of the base (3 layers: thick enough that the black doesn't darken the red)
TRIM_LAYER = 0.8           # white brim + pom-pom on top of the base (4 layers: opaque white, and 0.2 proud of the red, like fur)
POM_MIN_D = 4.4            # pom-pom, at least this big (the paper one would be ~3.3 at 50 mm): room for the hole + wall + fuzz
# Hanging: the smallest reliable hole through the pom-pom (owner, 2026-11-09, after trying a ring on top and a hole in
# the wing, which hung tilted). The pom-pom sits nearly straight above the balance point, so it hangs almost wings-level.
HANG_HOLE_D = 1.2          # smallest that stays open with a 0.4 nozzle (prints ~1.0); fishing line / thread / fine wire
POM_WALL_MIN = 1.2         # pom-pom plastic left around the hole (3 perimeters)
MIN_FEATURE = 1.2          # wing-claw spikes thinner than this get dropped (3 perimeters)
# Fuzzy white trim (owner, 2026-11-09): the brim and pom-pom get a cloud-like edge of small round bumps, like cartoon fur.
FUZZ_DEPTH = 0.4           # bumps stand out from a core inset this far; valleys reach the core
FUZZ_PITCH = 1.0           # bump spacing along the edge (about 2 nozzle widths, so the slicer keeps them)
FUZZ_R = (0.42, 0.58)      # random bump radius range: uneven bumps read as fur rather than a gear
FUZZ_SEED = 7              # fixed, so every build makes the same fur

# --- Photo -> flat geometry ------------------------------------------------------------------------------------------
CROP = (1220, 400, 1700, 900)      # x0, y0, x1, y1 around the Santa-hat bat
DARK_MAX = 110                     # bat paper is ~57 grey, wall ~175, shadows ~100
# The camera looks along the wall from the left, so shapes on the right of the photo are squashed sideways. The
# pom-pom (a hand-cut circle) reads 0.81 wide/tall there, so stretch X by 1/0.81. A straight-on photo would pin this down.
PERSPECTIVE_X_STRETCH = 1.23

# Santa hat, traced by hand on a 5x zoom of the photo: photo pixel = (1380 + x/5, 560 + y/5).
_HAT_ZOOM = dict(
    pom=((340, 175), 57),  # centre, radius
    cone=[(385, 150), (450, 132), (505, 150), (535, 200), (548, 290), (550, 470), (548, 600),
          (290, 420), (300, 380), (340, 300), (385, 235)],
    brim=[(235, 390), (290, 383), (545, 558), (572, 615), (562, 680), (505, 716), (440, 705),
          (215, 545), (196, 455), (205, 415)],
)


def _zoom_to_photo(pts):
    return [(1380 + x / 5, 560 + y / 5) for x, y in pts]


def trace_bat():
    """Largest dark blob in the crop, as a polygon in photo pixels."""
    img = np.asarray(Image.open(PHOTO).convert("L")).astype(float)
    x0, y0, x1, y1 = CROP
    dark = img[y0:y1, x0:x1] < DARK_MAX
    dark = ndimage.binary_opening(dark, iterations=1)
    dark = ndimage.binary_fill_holes(dark)
    lab, n = ndimage.label(dark)
    sizes = ndimage.sum(dark, lab, range(1, n + 1))
    bat = lab == (1 + int(np.argmax(sizes)))
    bat = ndimage.binary_closing(np.pad(bat, 2), iterations=1)
    c = max(measure.find_contours(bat.astype(float), 0.5), key=len)
    poly = Polygon([(x0 + p[1] - 2, y0 + p[0] - 2) for p in c]).buffer(0)
    return poly.simplify(0.6)


def hat_shapes():
    (cx, cy), r = _HAT_ZOOM["pom"]
    pom = Point(1380 + cx / 5, 560 + cy / 5).buffer(r / 5, 64)
    cone = Polygon(_zoom_to_photo(_HAT_ZOOM["cone"])).buffer(1.5).buffer(-1.5)   # soften the tip
    brim = Polygon(_zoom_to_photo(_HAT_ZOOM["brim"])).buffer(0.8).buffer(-0.8)
    return pom, cone, brim


def to_mm(shapes):
    """Photo pixels -> mm: flip Y up, undo the sideways squash, rotate to the hanging pose, scale, centre."""
    flipped = [affinity.scale(s, xfact=PERSPECTIVE_X_STRETCH, yfact=-1.0, origin=(0, 0)) for s in shapes]
    return flipped


def hanging_rotation(outline, pivot):
    """Angle (deg) that puts the centroid straight below the pivot, so it hangs the way it's rendered."""
    c = outline.centroid
    ang = np.degrees(np.arctan2(c.y - pivot.y, c.x - pivot.x))   # direction pivot -> centroid
    return -90.0 - ang


def build_shapes():
    bat_px = trace_bat()
    pom_px, cone_px, brim_px = hat_shapes()
    bat, pom, cone, brim = to_mm([bat_px, pom_px, cone_px, brim_px])

    outline = unary_union([bat, pom, cone, brim])
    rot = hanging_rotation(outline, pom.centroid)
    shapes = [affinity.rotate(s, rot, origin=pom.centroid) for s in (bat, pom, cone, brim)]
    outline = unary_union(shapes)
    minx, miny, maxx, maxy = outline.bounds
    k = ORNAMENT_SIZE_MM / max(maxx - minx, maxy - miny)
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    bat, pom, cone, brim = [affinity.scale(affinity.translate(s, -cx, -cy), k, k, origin=(0, 0)) for s in shapes]

    # Thin claw spikes don't print at 0.4 mm: open the bat by MIN_FEATURE/2 and close again.
    r = MIN_FEATURE / 2
    bat = bat.buffer(-r, join_style="round").buffer(r * 2, join_style="round").buffer(-r, join_style="round")
    bat = max(getattr(bat, "geoms", [bat]), key=lambda g: g.area)

    # Solid pom-pom (a little bigger than the paper one so the white prints cleanly).
    pc = pom.centroid
    pom_r = max(POM_MIN_D / 2, np.sqrt(pom.area / np.pi))
    pom = pc.buffer(pom_r, 96)

    trim = unary_union([fuzz(brim, FUZZ_SEED), fuzz(pom, FUZZ_SEED + 1)])
    # Red cusps between the fur bumps are thinner than the nozzle: drop them (the black base shows there, like an outline).
    hat = cone.difference(trim).buffer(-0.2, join_style="round").buffer(0.2, join_style="round")
    hat = max(getattr(hat, "geoms", [hat]), key=lambda g: g.area)
    bat = bat.difference(unary_union([cone, brim, pom]))
    # Fill any pinholes where the hand-traced hat meets the traced bat.
    outline = unary_union([bat, hat, trim])
    gaps = Polygon(outline.exterior).difference(outline)
    bat = unary_union([bat, gaps.buffer(0.02)]).difference(unary_union([hat, trim]))
    bat = max(getattr(bat, "geoms", [bat]), key=lambda g: g.area)

    # Hanging hole through the pom-pom centre; turn the whole ornament (slightly) so the balance point hangs exactly
    # below it, so the renders show how it really hangs.
    hole_c = pc
    c = mass_centroid(bat, hat, trim)
    turn = -90.0 - np.degrees(np.arctan2(c.y - hole_c.y, c.x - hole_c.x))
    bat, hat, trim, cone = [affinity.rotate(g, turn, origin=hole_c) for g in (bat, hat, trim, cone)]
    hole = hole_c.buffer(HANG_HOLE_D / 2, 64)
    bat, trim = bat.difference(hole), trim.difference(hole)
    return dict(bat=bat, hat=hat, trim=trim, hole=hole, cone=cone.difference(hole), rot_deg=rot + turn, px_to_mm=k,
                pom_r=pom_r, hole_centre=(hole_c.x, hole_c.y), hang_turn_deg=turn,
                hole_wall=float(min(hole.exterior.distance(g.exterior) for g in getattr(trim, "geoms", [trim])
                                    if Polygon(g.exterior).contains(hole_c))))


def fuzz(poly, seed):
    """Cloud-like fur edge: a core inset by FUZZ_DEPTH, plus round bumps of random size centred along the core's edge."""
    rng = np.random.default_rng(seed)
    core = poly.buffer(-FUZZ_DEPTH, join_style="round")
    ring = core.exterior
    n = max(6, int(round(ring.length / FUZZ_PITCH)))
    start = rng.uniform(0, 1)
    bumps = []
    for i in range(n):
        d = ((i + start + rng.uniform(-0.15, 0.15)) / n) % 1.0 * ring.length
        bumps.append(ring.interpolate(d).buffer(rng.uniform(*FUZZ_R), 24))
    return unary_union([core, *bumps])


def mass_centroid(bat, hat, trim):
    """Balance point: base (whole outline) plus the thin colour layers on top, weighted by volume."""
    parts = [(unary_union([bat, hat, trim]), THICKNESS), (hat, HAT_LAYER), (trim, TRIM_LAYER)]
    w = sum(g.area * t for g, t in parts)
    x = sum(g.centroid.x * g.area * t for g, t in parts) / w
    y = sum(g.centroid.y * g.area * t for g, t in parts) / w
    return Point(x, y)


def extrude(poly, h):
    """Polygon (possibly multi) -> watertight mesh from z=0 to h."""
    # A 0.01 mm simplify drops near-duplicate points that make the triangulation leaky.
    parts = [trimesh.creation.extrude_polygon(g.simplify(0.01), h) for g in getattr(poly, "geoms", [poly]) if g.area > 0.05]
    return trimesh.util.concatenate(parts)


def to_manifold(mesh):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(mesh.vertices, np.float32),
                                 tri_verts=np.asarray(mesh.faces, np.uint32)))


def from_manifold(man):
    m = man.to_mesh()
    return trimesh.Trimesh(m.vert_properties[:, :3], m.tri_verts, process=False)  # merging would break it


def write_svg(shapes, path):
    minx, miny, maxx, maxy = unary_union([shapes["bat"], shapes["hat"], shapes["trim"]]).bounds
    pad = 2
    w, h = maxx - minx + 2 * pad, maxy - miny + 2 * pad

    def d(poly):
        out = []
        for g in getattr(poly, "geoms", [poly]):
            for ring in [g.exterior, *g.interiors]:
                pts = [(x - minx + pad, maxy - y + pad) for x, y in ring.coords]
                out.append("M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts) + " Z")
        return " ".join(out)

    body = "\n".join(f'  <path d="{d(shapes[k])}" fill="{c}" fill-rule="evenodd" stroke="none"/>'
                     for k, c in (("bat", "#222"), ("hat", "#c8323c"), ("trim", "#f4f4f4")))
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.2f}mm" height="{h:.2f}mm" '
                    f'viewBox="0 0 {w:.2f} {h:.2f}">\n{body}\n</svg>\n')


def photo_overlay(path):
    img = Image.open(PHOTO).convert("RGB")
    bat = trace_bat()
    pom, cone, brim = hat_shapes()
    fig, axes = plt.subplots(1, 2, figsize=(16, 9))
    for ax, show in zip(axes, (False, True)):
        ax.imshow(img)
        if show:
            for s, c in ((bat, "yellow"), (cone, "cyan"), (brim, "lime"), (pom, "magenta")):
                ax.add_patch(MplPolygon(np.asarray(s.exterior.coords), fill=False, ec=c, lw=1.5))
        ax.set_xlim(CROP[0], CROP[2])
        ax.set_ylim(CROP[3], CROP[1])
        ax.set_axis_off()
    axes[0].set_title("photo")
    axes[1].set_title("traced bat (yellow), hat (cyan), brim (green), pom-pom (magenta)")
    fig.savefig(path, dpi=80, bbox_inches="tight")
    plt.close(fig)


def flat_render(shapes, path):
    fig, axes = plt.subplots(1, 2, figsize=(16, 8.5))
    for ax, back in zip(axes, (False, True)):
        for k, c in ((("bat", "#2a2a2a"), ("hat", "#2a2a2a"), ("trim", "#2a2a2a")) if back else
                     (("bat", "#2a2a2a"), ("hat", "#c8323c"), ("trim", "#f4f4f4"))):
            for g in getattr(shapes[k], "geoms", [shapes[k]]):
                for ring, fc in [(g.exterior, c), *[(i, "white") for i in g.interiors]]:
                    xy = np.asarray(ring.coords)
                    if back:
                        xy = xy * [-1, 1]
                    ax.add_patch(MplPolygon(xy, fc=fc, ec="#2a2a2a" if back else "#555", lw=0.6))
        ax.autoscale()
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.3)
        ax.set_title("back (mirror): plain black" if back else "front, as it hangs (mm)")
    fig.suptitle("santa-bat-ornament: colour layout", fontsize=15)
    fig.savefig(path, dpi=70, bbox_inches="tight")
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    RENDERS.mkdir(exist_ok=True)
    s = build_shapes()

    outline = unary_union([s["bat"], s["cone"], s["trim"]]).buffer(0.01).buffer(-0.01)   # cone, not hat: no pinholes at the fur cusps
    bat = extrude(outline, THICKNESS)
    hat = extrude(s["hat"], HAT_LAYER).apply_translation([0, 0, THICKNESS])
    trim = extrude(s["trim"], TRIM_LAYER).apply_translation([0, 0, THICKNESS])
    for name, m in (("bat", bat), ("hat", hat), ("trim", trim)):
        assert m.is_watertight, f"{name} body not watertight"
        m.export(OUT / f"santa-bat-ornament-{name}.stl")

    # Single-colour print: everything merged into one solid.
    # Merge with the whole hat cone (it overlaps the white), not the multi-colour hat part, which only just touches the
    # fur bumps: overlapping solids union cleanly, touching ones leave knife-edge contacts.
    cone = extrude(s["cone"], HAT_LAYER).apply_translation([0, 0, THICKNESS])
    merged = from_manifold(to_manifold(bat) + to_manifold(cone) + to_manifold(trim))
    merged.fix_normals()
    info = mk.report(merged)
    assert info["watertight"] and info["self_intersecting_faces"] == 0, info
    merged.export(OUT / "santa-bat-ornament.stl")

    # Multi-colour: one object, three parts (Bambu Studio asks "load as a single object with multiple parts?": yes).
    scene = trimesh.Scene()
    for name, m in (("bat (black)", bat), ("hat (red)", hat), ("trim (white)", trim)):
        scene.add_geometry(m, node_name=name, geom_name=name)
    scene.export(OUT / "santa-bat-ornament-multicolor.3mf")

    write_svg(s, OUT / "santa-bat-ornament-outline.svg")

    # Viewer copies (Z-up, standing as it hangs: drawing X stays X, drawing Y becomes Z).
    stand = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
    # One shared lift for all three bodies (lifting each by its own lowest point moved the hat off the bat).
    lift = -float(merged.bounds[0, 1])
    for name, m in (("bat", bat), ("hat", hat), ("trim", trim)):
        v = m.copy()
        v.apply_translation([0, 0, -THICKNESS / 2])
        v.apply_transform(stand)
        v.apply_translation([0, 0, lift])
        v.export(RENDERS / f"view-{name}.stl")

    hole_x, hole_y = s["hole_centre"]
    assert s["hole_wall"] >= POM_WALL_MIN - 0.01, s
    params = {
        "ornament_size": ORNAMENT_SIZE_MM,
        "width": round(float(merged.extents[0]), 1),
        "height": round(float(merged.extents[1]), 1),
        "thickness": THICKNESS,
        "thickness_at_hat": THICKNESS + HAT_LAYER,
        "thickness_at_trim": THICKNESS + TRIM_LAYER,
        "hang_hole_d": HANG_HOLE_D,
        "hang_hole_wall": round(s["hole_wall"], 2),
        "pom_pom_d": round(2 * s["pom_r"], 1),
        "min_feature": MIN_FEATURE,
        "perspective_x_stretch": PERSPECTIVE_X_STRETCH,
    }
    report = {
        "scale_status": "designer's choice, not measured: scaled so the longest side is "
                        f"{ORNAMENT_SIZE_MM:g} mm (shape traced from a photo; sideways squash corrected by estimate)",
        "print": info,
        "print_orientation": "flat on the bed, back face down (no supports)",
        "hanging": {"hole_centre_mm": [round(hole_x, 1), round(hole_y, 1)],
                    "rotated_from_photo_deg": round(float(s["rot_deg"]), 1)},
        "params_mm": params,
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))

    photo_overlay(RENDERS / "photo-trace.png")
    flat_render(s, RENDERS / "layout.png")
    from render import render_sheet
    render_sheet(merged, str(RENDERS / "model.png"), title="santa-bat-ornament: print pose (flat), mm",
                 labels=["ornament"], sections_y=(0.0, hole_y), sections_x=(0.0, hole_x))


if __name__ == "__main__":
    main()
