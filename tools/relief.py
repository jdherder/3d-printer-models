"""Layered-relief helpers for flat multicolour parts traced from artwork (keychains, badges, ornaments).

The part is a set of 2D regions, each with a colour and a top height, all standing on a base. The regions are noded
into one planar partition and every colour body is meshed straight from it as vertical columns with shared vertices,
so each body is watertight by construction (no booleans). This is the black-bob-keychain pipeline, made shareable;
see projects/blue-mana-keychain/build.py for a user.

    faces = separate_pinches(regions, outline, spans)      # regions: {name: (polygon, colour, top)}
    mesh = column_mesh(faces, spans["white"])               # span(name) -> (z0, z1) or None

Units are millimetres throughout.
"""

from collections import Counter

import numpy as np
import shapely
import trimesh
from scipy import ndimage
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree
from skimage import measure


def smooth_ring(xy, sigma, corner_deg=40.0, step=0.03):
    """Smooth a closed outline (mm) along its length, keeping sharp corners sharp.

    Resampled evenly, corners found by the turning angle over ~0.25 mm, then each stretch between corners is
    Gaussian-smoothed, with the smoothing faded out towards its corner ends so the corners stay put."""
    from scipy.ndimage import gaussian_filter1d
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
    corners = np.nonzero(peak & (ang > corner_deg))[0]
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


def clean(g, sliver=0.03, min_area=0.15, grid=0.005):
    """Drop slivers narrower than 2*sliver and specks under min_area (mm^2); snap to a fine grid (no pinch points)."""
    g = g.buffer(0).buffer(-sliver, join_style="mitre").buffer(sliver, join_style="mitre")
    parts = [p for p in getattr(g, "geoms", [g]) if p.area >= min_area]
    g = unary_union(parts) if parts else Polygon()
    return shapely.set_precision(g, grid).buffer(0)


def mask_to_poly(mask, to_mm, smooth=0.15, corner_deg=40.0, blur=1.0, simplify=0.015, **clean_kw):
    """Boolean mask (pixels) -> shapely (multi)polygon in mm. to_mm(col, row) maps pixel-centre coordinates to mm.
    The mask is blurred slightly first so the contour comes out sub-pixel smooth, then smoothed along its length."""
    m = ndimage.gaussian_filter(np.pad(mask, 2).astype(float), blur) if blur else np.pad(mask, 2).astype(float)
    polys = []
    for c in measure.find_contours(m, 0.5):
        if len(c) < 4:
            continue
        xy = np.c_[to_mm(c[:, 1] - 2, c[:, 0] - 2)]
        if smooth:
            xy = smooth_ring(xy, smooth, corner_deg)
        if len(xy) < 4:
            continue
        p = Polygon(xy).buffer(0)
        if p.area > 0:
            polys.append(p)
    # Nested contours: a contour inside an even number of others is an outline, inside an odd number it's a hole.
    tree = STRtree(polys)
    depth = []
    for p in polys:
        pt = p.representative_point()
        depth.append(sum(polys[j].area > p.area for j in tree.query(pt, predicate="within")))
    solid = unary_union([p for p, d in zip(polys, depth) if d % 2 == 0])
    holes = unary_union([p for p, d in zip(polys, depth) if d % 2 == 1])
    return clean(solid.difference(holes).simplify(simplify), **clean_kw)


def partition(regions, outline, simplify=0.0):
    """One planar partition: every region outline noded together (on a 1 µm grid), so neighbouring faces share
    exactly the same edges and vertices. regions = {name: (polygon, ...)}; later regions win where they overlap.
    Returns [(face polygon, region name)]. Faces in hairline gaps between regions go to the nearest region; faces
    outside the outline (holes) are dropped."""
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
            continue
        hits = list(tree.query(pt, predicate="within"))
        i = max(hits) if hits else int(tree.nearest(pt))
        out.append((shapely.geometry.polygon.orient(f, 1.0), names[i]))
    return out


def column_mesh(faces, span):
    """Watertight mesh of vertical columns, one per face: span(name) -> (z0, z1) or None. Each face gets a top and a
    bottom cap; walls go up only where neighbouring columns differ, split at every height used anywhere so all
    vertices line up."""
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
        for t in shapely.get_parts(shapely.constrained_delaunay_triangles(f)):
            a, b, c = (tuple(map(float, xy)) for xy in list(t.exterior.coords)[:3])
            if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) <= 0:
                b, c = c, b
            tris.append((vid(*a, z1), vid(*b, z1), vid(*c, z1)))
            tris.append((vid(*a, z0), vid(*c, z0), vid(*b, z0)))
        for ring in [f.exterior, *f.interiors]:
            c = list(ring.coords)
            for p, q in zip(c, c[1:]):
                j = owner.get((q, p))
                other = spans[j] if j is not None else None
                for za, zb in zip(levels, levels[1:]):
                    if not (z0 <= za and zb <= z1):
                        continue
                    if other and other[0] <= za and zb <= other[1]:
                        continue
                    pa, qa, qb, pb = vid(*p, za), vid(*q, za), vid(*q, zb), vid(*p, zb)
                    tris += [(pa, qa, qb), (pa, qb, pb)]
    return trimesh.Trimesh(np.array(verts), np.array(tris), process=False)


def pinches(m):
    """(x, y, z0, z1) of vertical edges shared by 4 faces: two columns touching only along a corner."""
    e = np.sort(m.faces[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2), axis=1)
    out = []
    for (i, j), n in Counter(map(tuple, e)).items():
        a, b = m.vertices[i], m.vertices[j]
        if n > 2 and a[0] == b[0] and a[1] == b[1]:
            out.append((a[0], a[1], min(a[2], b[2]), max(a[2], b[2])))
    return out


def separate_pinches(regions, outline, spans, r=0.02, rounds=8):
    """Partition the regions, then wherever two columns of a body touch only at a corner (non-manifold), hand a
    tiny disc (radius r) of one of them to a neighbour and partition again. Changes regions in place; returns faces."""
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
