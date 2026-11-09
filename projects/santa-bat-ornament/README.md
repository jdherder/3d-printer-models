# Santa-hat bat ornament

A flat, hanging Christmas ornament: the paper bat wearing a Santa hat from the owner's wall of
Halloween bats, made printable. It's 50 mm across: a 2 mm black bat with the red hat and white trim layered on top (like the paper one), and hangs from a small black loop on top of the pom-pom.

![colour layout](renders/layout.png)

## Goal

A mostly flat ornament (owner: "a little thickness but not much") that looks like the paper bat with the
Santa hat. Owner's picks: **50 mm across, three colours** (AMS lite: black, red, white).

## Status

- [x] Source captured: `source/photo-2026-11-09-wall-bats.jpg` (the bat with the Santa hat is right of centre)
- [x] Bat outline traced from the photo; hat drawn by hand over it (`renders/photo-trace.png`)
- [x] v1: 99.6 × 65.2 mm, 3 mm thick (3.6 mm at the brim and pom-pom), 3.2 mm hanging hole. Watertight, 0 self-intersections,
      Euler 0 (one through-hole, as intended)
- [x] v2: owner didn't like the hole through the pom-pom. The pom-pom is solid again, with a slim black hanging loop on top
- [x] v3: owner picked 50 mm and three colours. 2.4 mm thick, pom-pom and loop resized for the small scale
- [x] v4: owner chose less waste. Black base + colour layers on top, so all AMS swaps are in the top 4 layers
- [ ] Owner review of v4
- [ ] Test print

## Measurements

No real measurements: the size is the owner's choice (`ORNAMENT_SIZE_MM = 50`, the longest side as it hangs).

| Feature | Value (mm) | Notes |
|---|---|---|
| Overall (as it hangs) | 49.3 × 32.4 | |
| Thickness | 2.0 black base; 2.6 at the red hat; 2.8 at the brim + pom-pom | Red 0.6 (3 layers) so the black doesn't darken it; white 0.8 (4 layers), 0.2 proud of the red like fur |
| Pom-pom | 4.5 dia, solid | True scale would be ~3.3. Enlarged to carry the loop |
| Hanging loop | 4.0 outside, 2.0 hole, 1.0 wall | Black, straight above the pom-pom, joined across ~2.5 mm. Takes thread, thin ribbon, or a wire hook |
| Smallest feature | 1.2 | Wing-claw spikes thinner than this are dropped. At 50 mm that's nearly all of them |
| Thinnest colour region | ≥ 0.4 | No unprintable colour slivers |
| Colour swaps | ~5 | Only in layers 11–14. Black layers 1–10 print in one go |

**Perspective:** the photo looks along the wall from the left, so the bat is squashed sideways. The pom-pom (a
hand-cut circle) reads 0.81 wide/tall, so X is stretched 1.23× (`PERSPECTIVE_X_STRETCH`). This is an estimate. A
straight-on photo of the paper bat (or one with a ruler beside it) would settle it.

## Print settings

- **PLA** (indoor, decorative). Flat on the bed, black face down, no supports. 0.2 mm layers (14 at the trim).
- **AMS lite:** open `output/santa-bat-ornament-multicolor.3mf` (if Bambu Studio asks, load it as one object with multiple parts)
  and set the filament for each part: bat (base + loop) black, hat red, trim white. Layers 1–10 are all black; the colour
  changes are only in layers 11–14 (~5 swaps), so the prime tower is short and the purge waste small. Several on one plate
  share those swaps.
- **One colour:** `output/santa-bat-ornament.stl`. The raised hat shows as relief; paint it if you like.
- Thread thin ribbon, thread, or an ornament hook through the loop. The ornament is rotated so it hangs level from it.

## Open questions

- Is a 2 mm loop hole big enough for what it'll hang from?
- Does the bat look right, especially its width after the perspective stretch?

## Pipeline

`build.py`:
1. Thresholds the dark paper (grey < 110) in a crop around the bat, keeps the largest blob, and traces its contour.
2. Builds the hat from polygons hand-traced on a 5× zoom of the photo (`_HAT_ZOOM`). The white paper is too
   close to the wall colour to threshold.
3. Flips to Y-up, applies the perspective stretch, rotates so the centroid hangs straight below the pom-pom,
   and scales to `ORNAMENT_SIZE_MM`.
4. Drops sub-`MIN_FEATURE` spikes, sizes the pom-pom, adds the hanging loop above it (`LOOP_*`, part of the black bat body), and splits the outline into bat, hat, and trim regions.
5. Extrudes the black base (whole outline) to `THICKNESS`, then the hat (`HAT_LAYER`) and trim (`TRIM_LAYER`) on top of it. Merges them into a
   single-colour STL (manifold3d), and writes the 3MF, SVG, report, and renders.

## Files

- `output/santa-bat-ornament.stl`: single-colour print
- `output/santa-bat-ornament-multicolor.3mf`: one object, three parts (bat + loop / hat / trim) for the AMS lite
- `output/santa-bat-ornament-{bat,hat,trim}.stl`: the colour bodies on their own
- `output/santa-bat-ornament-outline.svg`: coloured outline at 1:1 mm (Fusion import, cutting more paper bats)
- `output/report.json`: checks + parameters
- `renders/photo-trace.png`: trace over the photo; `renders/layout.png`: front/back colours; `renders/model.png`: views + sections
- **Viewer artifact:** https://claude.ai/artifact/AnvmvzdQsUKBGzz1mdb5W5 (publish updates to this URL)

## Log

- **2026-11-09:** Project started from the owner's wall photo. Traced the bat, drew the hat by hand, and corrected the sideways squash
  (1.23×, estimated). v1: 100 mm, 3 mm thick, a hanging hole through an enlarged pom-pom, three colour bodies + a merged
  single-colour STL. Waiting on the owner for size, colour plan, and shape feedback.
- **2026-11-09:** Owner: the hat was in the wrong place in the 3D viewer. That was a viewer-only bug: each colour body was lifted
  to the floor separately, so the hat and trim dropped below where they belong. Fixed with one shared offset. The print files were
  unaffected (the layout and STL were already right).
- **2026-11-09:** v2. The owner wasn't keen on the hole through the pom-pom. Now the pom-pom is a solid 7 mm ball, with a slim black loop on top (5 mm across, 2.6 mm hole), like a glass ornament's cap. A same-size white loop looked like a snowman, so it's smaller and black. Watertight, 0 self-intersections, Euler 0 (the loop's hole).
- **2026-11-09:** v3. Owner: 50 mm, three colours. Thickness 3 → 2.4 mm (fur 0.4 proud) to stay in proportion and cut colour swaps. Pom-pom 4.5 mm, loop 4 mm with a 2 mm hole (smallest that still takes a hook). All colour regions ≥ 0.4 mm wide. Watertight, 0 self-intersections.
- **2026-11-09:** v4. The owner wants less waste. Colours no longer go through the full thickness (~25 AMS swaps). Now it's a black 2 mm base (whole outline + loop) with a red hat 0.6 mm and white trim 0.8 mm layered on top: ~5 swaps, all in layers 11–14. The back is plain black. Watertight, 0 self-intersections.
