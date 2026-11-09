# Santa-hat bat ornament

A flat, hanging Christmas ornament: the paper bat wearing a Santa hat from the owner's wall of
Halloween bats, made printable. It's 3 mm thick and hangs from a hole in the pom-pom.

![colour layout](renders/layout.png)

## Goal

A mostly flat ornament (owner: "a little thickness but not much") that looks like the paper bat with the
Santa hat. Size is free (no real part to match). It prints in one colour or, with the AMS lite, in black + red + white.

## Status

- [x] Source captured: `source/photo-2026-11-09-wall-bats.jpg` (the bat with the Santa hat is right of centre)
- [x] Bat outline traced from the photo; hat drawn by hand over it (`renders/photo-trace.png`)
- [x] v1: 99.6 × 65.2 mm, 3 mm thick (3.6 mm at the brim and pom-pom), 3.2 mm hanging hole. Watertight, 0 self-intersections,
      Euler 0 (one through-hole, as intended)
- [ ] Owner review: shape, size, colours
- [ ] Test print

## Measurements

No real measurements: the size is a design choice (`ORNAMENT_SIZE_MM = 100`, the longest side as it hangs).
If the owner wants it to match the paper bats, measure one paper bat's wingspan and set the size from that.

| Feature | Value (mm) | Notes |
|---|---|---|
| Overall (as it hangs) | 99.6 × 65.2 | |
| Thickness | 3.0, and 3.6 at the brim + pom-pom | The white "fur" stands 0.6 mm proud |
| Pom-pom | 9.0 dia, 3.2 hole | Enlarged from ~6.5 so the hole keeps a 2.9 mm wall. It joins the hat along ~9 mm |
| Smallest feature | 1.2 | Wing-claw spikes thinner than this were dropped |

**Perspective:** the photo looks along the wall from the left, so the bat is squashed sideways. The pom-pom (a
hand-cut circle) reads 0.81 wide/tall, so X is stretched 1.23× (`PERSPECTIVE_X_STRETCH`). This is an estimate. A
straight-on photo of the paper bat (or one with a ruler beside it) would settle it.

## Print settings

- **PLA** (indoor, decorative). Flat on the bed, back face down, no supports. 0.2 mm layers.
- **One colour:** print `output/santa-bat-ornament.stl`. The raised brim and pom-pom show the hat. Paint the hat red if you like.
- **AMS lite:** open `output/santa-bat-ornament-multicolor.3mf` (if Bambu Studio asks, load it as one object with
  multiple parts) and set the filament for each part: bat black, hat red, trim white. Every colour goes through the
  full thickness, so the back shows the hat too (mirrored).
- Thread ribbon or an ornament hook through the pom-pom. The ornament is rotated so it hangs level from that hole.

## Open questions

- Is 100 mm the right size?
- One colour or multi-colour?
- Does the bat look right, especially its width after the perspective stretch?
- Hat on both sides (as now), or a plain black back?

## Pipeline

`build.py`:
1. Thresholds the dark paper (grey < 110) in a crop around the bat, keeps the largest blob, and traces its contour.
2. Builds the hat from polygons hand-traced on a 5× zoom of the photo (`_HAT_ZOOM`). The white paper is too
   close to the wall colour to threshold.
3. Flips to Y-up, applies the perspective stretch, rotates so the centroid hangs straight below the pom-pom,
   and scales to `ORNAMENT_SIZE_MM`.
4. Drops sub-`MIN_FEATURE` spikes, enlarges the pom-pom, cuts the hole, and splits the outline into bat, hat, and trim regions.
5. Extrudes each colour, merges them into a single-colour STL (manifold3d), writes the 3MF, SVG, report, and renders.

## Files

- `output/santa-bat-ornament.stl`: single-colour print
- `output/santa-bat-ornament-multicolor.3mf`: one object, three parts (bat / hat / trim) for the AMS lite
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
