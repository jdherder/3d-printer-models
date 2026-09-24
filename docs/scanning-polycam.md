# Scanning with Polycam (iOS)

## Export

- Export **GLB** (textured mesh, metres, Y-up) and drop it in
  `projects/<name>/source/` with a dated name, for example `polycam-2026-09-24.glb`.
- `tools/meshkit.load_scan` handles GLB, OBJ, PLY, and STL.

## Scale is not reliable

Photo mode builds geometry from photos. Its absolute size can be far off. The
gate-footing scan came out obviously too big. LiDAR mode (Pro iPhones) is closer
but still not caliper-accurate. **Always record at least one real measurement**
(overall length is easiest) in the project README. `build.py` scales the mesh to
match it.

Better: put an object of known size in the scene (a ruler or a credit card,
85.6 × 54 mm) so the scale can be checked afterwards.

## Getting better scans

- Put the object on a plain surface with some texture (not glossy, not
  featureless). Dark or shiny plastic scans poorly, and a light dusting of
  talc or dry shampoo helps.
- Walk a full orbit at two or three heights, with lots of overlap. Get down low
  for vertical faces.
- Slots, holes, and undersides won't be captured if the camera can't see them.
  Scan the object upside-down separately if the underside matters, or measure
  those features by hand.
- Crop tightly in Polycam if you can. The pipeline removes the floor anyway,
  since it fits the ground plane and cuts just above it.

## What the pipeline does (`tools/meshkit.py`)

1. Merges the texture-seam duplicate vertices.
2. Fits the ground plane with RANSAC, then levels it so the ground is Z=0 (mm, Z-up).
3. Cuts 2 mm above the ground and keeps the largest piece (the object).
4. Squares the footprint to X/Y and centres the part.
5. Drops the cut edge to Z=0 and caps it, giving a flat, watertight base.
6. Reports dimensions, watertightness, self-intersections, and A1 fit.
