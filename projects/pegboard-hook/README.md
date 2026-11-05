# Pegboard hook

A standard steel pegboard hook: one bent 5.53 mm wire (a short leg that goes through
the board and rises behind it, an S-jog, a back leg against the board, and an arm that
angles up) plus a short welded pin that sits in the hole below and stops it rotating out.

![model over the owner's photo](renders/photo-overlay.png)

## Goal

Model the owner's existing hook so it can be printed. *(Owner to confirm: an exact
plastic copy, or a stronger/longer/different printable version based on it?)*

## Status

- [x] Source captured: three photos with tape and caliper (`source/photo-2026-11-05-*.jpg`)
- [x] Real measurements recorded (below)
- [x] Parametric model (`model.py`, build123d), traced from the tape photo. The outline overlays
      the photo within about 1 mm (`renders/photo-overlay.png`)
- [x] Print-ready STL + STEP: lying on its side, 0.4 mm flat on the bed side. 57.2 × 53.9 × 5.1 mm,
      watertight, 0 self-intersections
- [ ] Owner review: shape, intended use, board thickness and hole size
- [ ] Test print, then adjust

## Measurements

| Feature | Real (mm) | Source | Notes |
|---|---|---|---|
| Wire diameter | **5.53** | caliper | Pin looks like the same wire (~5.5 mm in the photo) |
| Overall (footprint × height) | 57.2 × 53.9 | tape photo | Photo reads ~57.9 × 53.9 (tip edge to arm end, top to bottom bend) |
| Arm | 42.0 long, 12.6° up | tape photo | Reaches 43.8 mm out from the board face |
| Behind-board leg | 12 mm tall, centre 12.85 behind the back leg | tape photo | Leaves 7.3 mm for the board |
| S-jog | ~26° slope | tape photo | Least certain part (it's curved) |
| Pin | 13.0 above the bottom corner, sticks out 7.0 | tape photo | |
| Bend radius | 4.5 (centreline) | estimated | One radius for every bend |

Photo scale: `photo-2026-11-05-tape-vertical.jpg`, tape inch marks 245 px apart (9.65 px/mm). The model
origin (bottom corner of the wire centreline) is at pixel (750, 1308). Both are in `build.py`, and the
overlay render uses them. Positions are good to about ±1 mm.

## Print settings

- **PETG** (default for load-bearing). Lying flat on its side, no supports. The 0.4 mm flat gives a 3.1 mm wide first layer.
  A brim may help, since the contact patch is thin.
- At 5.5 mm the wire is all perimeters, so infill doesn't matter. Plastic this thin is far weaker
  and more flexible than steel. Fine for light things (keys, cables, small tools). It will bend under heavy ones.

## Open questions

- **What's it for?** Exact copy, or a printable improvement (thicker arm, longer arm, a lip on the end,
  double hook)? Plastic needs more section than steel to carry the same load.
- **Board thickness and hole size.** On a nominal 1/4" board (6.35 mm holes, 6.35 mm thick), the
  model's S-jog clips the hole edges slightly (~42 mm³ overlap in the check). The real hook's
  jog seems to as well in the photo. Real boards often have bigger holes or are thinner. A caliper
  reading of the hole and the board would settle it, and the jog can be flattened to suit.
- The pin's ~1 in (24 mm in the photo) spacing from the jog: does the real hook sit tight or a little loose?

## Pipeline

`build.py` builds the hook in the use frame (`model.py`: a circle swept along a filleted polyline,
plus a cylinder for the pin), lays it on its side and shaves the bed flat (`print_pose`), and exports
the STEP and STL. It also checks the hook against a 1/4" pegboard patch, renders previews, and draws
the model outline over the photo. Parameters are in `HookParams` (`model.py`). Real measurements go in
`MEASURED` in `build.py`.

## Files

- `output/pegboard-hook.stl`: print this (Bambu Studio)
- `output/pegboard-hook.step`: editable solid for Fusion
- `output/report.json`: checks + parameters
- `renders/photo-overlay.png`: model vs photo; `renders/model.png`: views + sections
- **Viewer artifact:** https://claude.ai/artifact/S5AyTFWVq79VooqWJUmkQr (publish updates to this URL)

## Log

- **2026-11-05:** Project started from three owner photos (tape + caliper, wire 5.53 mm). Traced the wire
  path and pin off the tape photo and built a parametric sweep in build123d. Outline matches the photo within ~1 mm.
  Printable version lies on its side with a 0.4 mm flat. Published the viewer. Waiting on the owner: intended use, and board
  thickness/hole size (the jog clips a nominal 1/4" hole slightly).
