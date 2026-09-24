"""Shared mesh utilities for turning phone scans into printable solids.

Conventions (see CLAUDE.md): millimetres, Z-up, part resting on Z=0,
centred on the XY origin, longest footprint axis along X.

Typical scan pipeline (each step is a plain function so project build
scripts can mix and match or insert custom steps):

    mesh = load_scan(path)                 # merge UV-seam duplicate vertices
    mesh = level_to_ground(mesh)           # RANSAC ground plane -> Z=0, mm, Z-up
    mesh = cut_above_ground(mesh, 2.0)     # drop the floor, keep the object
    mesh = orient_footprint(mesh)          # square the footprint to X/Y
    mesh = cap_bottom(mesh)                # flat, watertight base at Z=0
    report(mesh)                           # dims, watertight, fits-on-A1

Run `python tools/inspect_mesh.py <file>` for a quick report on any mesh.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp
import shapely.geometry as sg
import trimesh
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

# Bambu Lab A1 build volume in mm (X, Y, Z).
A1_BUILD_VOLUME = np.array([256.0, 256.0, 256.0])


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------

def load_scan(path: str) -> trimesh.Trimesh:
    """Load a scan (GLB/OBJ/PLY/STL) as a single geometry-only mesh.

    Textured exports (Polycam GLB) duplicate vertices along UV seams, which
    makes the surface look like hundreds of disconnected islands. Rebuilding
    the mesh from positions only merges those back together.
    """
    loaded = trimesh.load(path)
    if isinstance(loaded, trimesh.Scene):
        loaded = loaded.to_geometry()
    mesh = trimesh.Trimesh(loaded.vertices.copy(), loaded.faces.copy(), process=True)
    mesh.merge_vertices()
    return mesh


# --------------------------------------------------------------------------
# Ground plane / levelling
# --------------------------------------------------------------------------

def fit_ground_plane(points: np.ndarray, threshold: float, iterations: int = 2000,
                     up_hint=(0.0, 1.0, 0.0), seed: int = 0):
    """RANSAC plane fit. Returns (unit normal, point on plane, inlier mask).

    The normal is flipped to agree with `up_hint` (glTF/Polycam is Y-up).
    """
    rng = np.random.default_rng(seed)
    best = None
    n_pts = len(points)
    for _ in range(iterations):
        p = points[rng.choice(n_pts, 3, replace=False)]
        n = np.cross(p[1] - p[0], p[2] - p[0])
        norm = np.linalg.norm(n)
        if norm < 1e-12:
            continue
        n /= norm
        inliers = np.abs((points - p[0]) @ n) < threshold
        if best is None or inliers.sum() > best.sum():
            best = inliers
    # Least-squares refinement on the inliers (SVD of centred points).
    pts = points[best]
    centroid = pts.mean(axis=0)
    normal = np.linalg.svd(pts - centroid)[2][-1]
    if normal @ np.asarray(up_hint) < 0:
        normal = -normal
    inliers = np.abs((points - centroid) @ normal) < threshold
    return normal, centroid, inliers


def level_to_ground(mesh: trimesh.Trimesh, scan_units_to_mm: float = 1000.0,
                    threshold_mm: float = 5.0, up_hint=(0.0, 1.0, 0.0)) -> trimesh.Trimesh:
    """Rotate so the dominant ground plane is Z=0 with +Z up, and convert to mm.

    Polycam exports metres, Y-up. `scan_units_to_mm` scales to millimetres;
    tweak it (e.g. 1000 * measured/scanned) to correct scan scale error.
    """
    mesh = mesh.copy()
    mesh.apply_scale(scan_units_to_mm)
    normal, origin, _ = fit_ground_plane(mesh.vertices, threshold_mm, up_hint=up_hint)
    mesh.apply_translation(-origin)
    mesh.apply_transform(trimesh.geometry.align_vectors(normal, [0.0, 0.0, 1.0]))
    return mesh


# --------------------------------------------------------------------------
# Object extraction
# --------------------------------------------------------------------------

def face_components(mesh: trimesh.Trimesh) -> np.ndarray:
    """Label faces by edge-connected component (fast, scipy-based)."""
    adj = mesh.face_adjacency
    graph = sp.coo_matrix((np.ones(len(adj)), (adj[:, 0], adj[:, 1])),
                          shape=(len(mesh.faces),) * 2)
    return connected_components(graph, directed=False)[1]


def largest_component(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    labels = face_components(mesh)
    keep = np.flatnonzero(labels == np.argmax(np.bincount(labels)))
    return mesh.submesh([keep], append=True)


def crop_xy(mesh: trimesh.Trimesh, center_xy, radius: float) -> trimesh.Trimesh:
    """Keep faces whose centroid is within `radius` of `center_xy`."""
    d = np.linalg.norm(mesh.triangles_center[:, :2] - np.asarray(center_xy), axis=1)
    return mesh.submesh([np.flatnonzero(d < radius)], append=True)


def cut_above_ground(mesh: trimesh.Trimesh, cut_height: float = 2.0) -> trimesh.Trimesh:
    """Slice off everything below `cut_height` and keep the largest piece.

    The floor contact zone of a scan is fused with the ground, so we cut a
    little above it; `cap_bottom` later extends the walls back down to Z=0.
    """
    cut = trimesh.intersections.slice_mesh_plane(mesh, [0, 0, 1], [0, 0, cut_height])
    cut.merge_vertices()
    return largest_component(cut)


# --------------------------------------------------------------------------
# Orientation
# --------------------------------------------------------------------------

def orient_footprint(mesh: trimesh.Trimesh, long_axis: str = "x") -> trimesh.Trimesh:
    """Rotate about Z so the minimum-area footprint rectangle is axis aligned,
    longest side along `long_axis`, and centre the part on the XY origin."""
    mesh = mesh.copy()
    low = mesh.vertices[mesh.vertices[:, 2] < mesh.bounds[0, 2] + 10.0][:, :2]
    T2, extents = trimesh.bounds.oriented_bounds_2D(low)
    R = np.eye(4)
    R[:2, :2] = T2[:2, :2]
    if np.linalg.det(R[:3, :3]) < 0:  # never mirror the part
        R[1, :3] *= -1
    mesh.apply_transform(R)
    wants_x = long_axis == "x"
    if (mesh.extents[0] < mesh.extents[1]) == wants_x:
        mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 0, 1]))
    return center_on_bed(mesh)


def center_on_bed(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    mesh = mesh.copy()
    c = mesh.bounds.mean(axis=0)
    mesh.apply_translation([-c[0], -c[1], -mesh.bounds[0, 2]])
    return mesh


# --------------------------------------------------------------------------
# Closing the mesh
# --------------------------------------------------------------------------

def boundary_loops(mesh: trimesh.Trimesh) -> list[list[int]]:
    import networkx as nx
    edges, counts = np.unique(mesh.edges_sorted, axis=0, return_counts=True)
    graph = nx.Graph()
    graph.add_edges_from(edges[counts == 1].tolist())
    return [list(c) for c in nx.cycle_basis(graph)]


def cap_bottom(mesh: trimesh.Trimesh, z: float = 0.0, tol: float = 0.5) -> trimesh.Trimesh:
    """Close open boundary loops lying on the cut plane with a flat cap at `z`.

    Loop vertices are dropped to `z` (extending the side walls straight
    down) and the footprint polygon(s) are triangulated, holes included.
    Loops that are not on the bottom plane are reported, not capped.
    """
    loops = boundary_loops(mesh)
    zmin = mesh.bounds[0, 2]
    bottom = [lp for lp in loops if np.ptp(mesh.vertices[lp, 2]) < tol
              and abs(mesh.vertices[lp, 2].mean() - zmin) < tol]
    other = [lp for lp in loops if lp not in bottom]
    if other:
        print(f"cap_bottom: {len(other)} non-bottom hole(s) left open "
              f"(sizes {[len(o) for o in other]}); fill them before printing")
    vertices = mesh.vertices.copy()
    loop_vids = np.concatenate(bottom)
    vertices[loop_vids, 2] = z

    # Shells are loops not inside another; odd nesting depth => hole.
    polys = sorted(((sg.Polygon(vertices[lp, :2]), lp) for lp in bottom),
                   key=lambda p: -p[0].area)
    shells: list[list] = []
    for poly, _ in polys:
        depth = sum(s[0].contains(poly) for s in shells) + sum(
            h.contains(poly) for s in shells for h in s[1])
        if depth % 2 == 0:
            shells.append([poly, []])
        else:
            owner = [s for s in shells if s[0].contains(poly)][-1]
            owner[1].append(poly)

    tree = cKDTree(vertices[loop_vids, :2])
    cap_faces = []
    for shell, holes in shells:
        poly = sg.Polygon(shell.exterior.coords, [h.exterior.coords for h in holes])
        cv, cf = trimesh.creation.triangulate_polygon(poly, engine="earcut")
        dist, idx = tree.query(cv)
        assert dist.max() < 1e-6, "cap triangulation introduced new vertices"
        cap_faces.append(loop_vids[idx][cf])

    solid = trimesh.Trimesh(vertices, np.vstack([mesh.faces, *cap_faces]), process=True)
    solid.fix_normals()
    return solid


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------

def self_intersecting_faces(mesh: trimesh.Trimesh) -> int | None:
    """Count self-intersecting faces via PyMeshLab (None if unavailable)."""
    try:
        import pymeshlab
    except Exception:
        return None
    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(mesh.vertices, mesh.faces))
    ms.compute_selection_by_self_intersections_per_face()
    return int(ms.current_mesh().selected_face_number())


def fits_build_volume(extents, volume=A1_BUILD_VOLUME) -> bool:
    """True if the part fits in some axis-permuted orientation (flat rotations only)."""
    e = np.sort(np.asarray(extents))
    return bool(np.all(e <= np.sort(volume)))


def report(mesh: trimesh.Trimesh, check_self_intersections: bool = True) -> dict:
    ext = mesh.extents
    info = {
        "extents_mm": [round(float(v), 1) for v in ext],
        "faces": int(len(mesh.faces)),
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "euler_number": int(mesh.euler_number),
        "volume_cm3": round(float(mesh.volume) / 1000.0, 1) if mesh.is_watertight else None,
        "fits_A1_as_is": bool(np.all(ext <= A1_BUILD_VOLUME)),
        "fits_A1_any_axis_order": fits_build_volume(ext),
    }
    if check_self_intersections:
        info["self_intersecting_faces"] = self_intersecting_faces(mesh)
    return info


# --------------------------------------------------------------------------
# Repair / CAD tessellation
# --------------------------------------------------------------------------

def repair(mesh: trimesh.Trimesh, merge_tol: float = 0.01, max_hole_edges: int = 30) -> trimesh.Trimesh:
    """Stitch near-coincident vertices and close tiny holes (PyMeshLab).

    CAD tessellations (e.g. OpenCASCADE fillet ends) often leave hairline
    T-junction gaps that make an otherwise perfect solid non-watertight.
    """
    import pymeshlab
    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(mesh.vertices, mesh.faces))
    ms.meshing_merge_close_vertices(threshold=pymeshlab.PureValue(merge_tol))
    ms.meshing_remove_duplicate_faces()
    ms.meshing_remove_null_faces()
    ms.meshing_repair_non_manifold_edges()
    ms.meshing_close_holes(maxholesize=max_hole_edges)
    m = ms.current_mesh()
    out = trimesh.Trimesh(m.vertex_matrix(), m.face_matrix(), process=True)
    out.fix_normals()
    return out


def cad_to_mesh(part, tolerance: float = 0.05, angular_tolerance: float = 0.1) -> trimesh.Trimesh:
    """Tessellate a build123d Part into a watertight trimesh (mm)."""
    import os
    import tempfile

    from build123d import export_stl
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "part.stl")
        export_stl(part, path, tolerance=tolerance, angular_tolerance=angular_tolerance)
        mesh = trimesh.load(path, force="mesh")
    return repair(mesh)
