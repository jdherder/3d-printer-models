# Pegboard hook

A standard steel pegboard hook: one bent 5.53 mm wire (a short leg that goes through
the board and rises behind it, an S-jog, a back leg against the board, and an arm that
angles up) plus a short welded pin that sits in the hole below and stops it rotating out.

![model over the owner's photo](renders/photo-overlay.png)

## Goal

**Catalog part** (see the catalog in `docs/pegboard.md`): a printable copy of the owner's steel hook, for light
things like keys, cables and small tools. It's also the **reference** for the shared pegboard interface: the
`PegStyle` defaults in `tools/pegboard.py` are this hook's measurements. The fit test for those pegs is its own project,
`projects/pegboard-fit-test`.

## Status

- [x] Source captured: three photos with tape and caliper (`source/photo-2026-11-05-*.jpg`)
- [x] Real measurements recorded (below)
- [x] Parametric model (`model.py`, build123d), traced from the tape photo. The outline overlays
      the photo within about 1 mm (`renders/photo-overlay.png`)
- [x] Print-ready STL + STEP: lying on its side, 0.4 mm flat on the bed side. 57.6 × 54.2 × 5.7 mm,
      watertight, 0 self-intersections
- [x] In the catalog, built for the owner's board (Menards 3/16 white hardboard, `pegboard.DEFAULT_BOARD`)
- [x] v4 test print: printed well and hung, but a little loose in the holes
- [x] v5 print (5.9 mm wire, level step): much harder to get in, and still loose
- [ ] Reprint v6 (12° jog back, 6.1 mm wire). Pick the final diameter with the peg gauge (`pegboard-fit-test`)

## Measurements

| Feature | Real (mm) | Source | Notes |
|---|---|---|---|
| Wire diameter | **5.53** steel; **printed at 6.1** | caliper; test prints | Printed at 5.53 and at 5.9, it was loose. Follows the shared peg diameter (`PegStyle.d`) |
| Overall (footprint × height) | 57.2 × 53.9 | tape photo | Photo reads ~57.9 × 53.9 (tip edge to arm end, top to bottom bend) |
| Arm | 42.0 long, 12.6° up | tape photo | Reaches 43.8 mm out from the board face |
| Behind-board leg | 12 mm tall, centre 12.85 behind the back leg | tape photo | Leaves 7.3 mm for the board |
| S-jog | **12°**, crossing the hole 25.4 above the pin | test prints | The owner's prints are the real check. 12° went in easily. A level step (v5) was much harder, because the slope guides the hook as it rocks in. The flush-hang overlap in `report.json` is information only | Traced at ~26° with the front corner 3.3 mm lower. That can't hang flush on a 1 in grid: the wire's underside met the board face ~3 mm below the hole. Now defined by the hole it passes through (`jog_*` in `model.py`). The back corner and top leg still match the photo |
| Pin | 13.0 above the bottom corner, sticks out 7.0 | tape photo | |
| Bend radius | 3.5 (centreline) | fit | Must exceed the wire radius (3.05 at 6.1 mm) or the bends self-intersect. 4.5 looked closer to the photo |

Photo scale: `photo-2026-11-05-tape-vertical.jpg`, tape inch marks 245 px apart (9.65 px/mm). The model
origin (bottom corner of the wire centreline) is at pixel (750, 1308). Both are in `build.py`, and the
overlay render uses them. Positions are good to about ±1 mm.

## Print settings

- **PETG** (default for load-bearing). Lying flat on its side, no supports. The 0.4 mm flat gives a 3.1 mm wide first layer.
  A brim may help, since the contact patch is thin.
- At 5.5 mm the wire is all perimeters, so infill doesn't matter. Plastic this thin is far weaker
  and more flexible than steel. Fine for light things (keys, cables, small tools). It will bend under heavy ones.

## Open questions

- **Does the real hook hang flush** (back leg flat against the board)? If so, the photo is off at the jog's front corner and
  the adjusted model is closer to the truth. A caliper reading of the gap between the top of the pin and the underside of the
  jog, measured at the back leg, would settle it.
- This hook only fits thin boards like the owner's. On a 1/4 in board (6.35 mm holes and thickness) the jog clips the holes.

## Pipeline

`build.py` builds the hook in its use frame (`model.py`: a circle swept along a filleted polyline,
plus a cylinder for the pin), lays it on its side and shaves the bed flat (`print_pose`), and exports
the STEP and STL. It moves the hook into the shared board frame (`model.use_to_board`) and checks it hung on
`pegboard.board_mesh(BOARDS["quarter"])`. It also renders previews and draws the model outline over the photo.
Parameters are in `HookParams` (`model.py`). Real measurements go in `MEASURED` in `build.py`.

## Files

- `output/pegboard-hook.stl`: print this (Bambu Studio)
- `output/pegboard-hook.step`: editable solid for Fusion
- `output/report.json`: checks + parameters (including `fit_on_board` interference)
- `renders/photo-overlay.png`: model vs photo; `renders/model.png`: views + sections
- **Viewer artifact:** https://claude.ai/artifact/S5AyTFWVq79VooqWJUmkQr (publish updates to this URL)

## Log

- **2026-11-05:** Project started from three owner photos (tape + caliper, wire 5.53 mm). Traced the wire
  path and pin off the tape photo and built a parametric sweep in build123d. Outline matches the photo within ~1 mm.
  Printable version lies on its side with a 0.4 mm flat. Published the viewer. Waiting on the owner: intended use, and board
  thickness/hole size (the jog clips a nominal 1/4" hole slightly).
- **2026-11-05 (v2):** The owner wants this as a baseline for future custom pegboard parts. Extracted the board interface into
  `tools/pegboard.py` + `docs/pegboard.md`, with peg defaults from this hook (5.53 mm, 7.3 mm gap behind the board, 14 mm rise, 7 mm pin).
  Added the fit-test piece (0 interference on a nominal 1/4" board). Next: the owner prints the fit test and calipers the board.
- **2026-11-05 (v3):** The owner wants the hook kept as a part in the growing catalog. Moved the fit test to its own project
  (`pegboard-fit-test`), so this project is just the hook. Added a catalog table to `docs/pegboard.md`.
- **2026-11-05 (v4):** The owner's board is a Menards 3/16 in white hardboard panel (listing values: 9/32 in holes, 0.155 in thick),
  now `pegboard.DEFAULT_BOARD`. The traced hook didn't fit it (28 mm³ overlap, and tilting or moving the pin alone couldn't fix it).
  The jog is now defined by the hole it passes through (12°, front corner 3.3 mm higher than traced) and the bend radius is 3.0. It now
  clears with 0.2 mm per side to spare. Shared fit checks now use `FIT_CLEARANCE` = 0.2 mm.
- **2026-11-05 (v5):** The owner printed v4: it printed well and hung, but was a little loose in the holes. The owner measured the holes at
  ~0.25 in (6.35 mm) on 1 in centres, not the listings' 9/32 in. The printed wire is now 5.9 mm (shared `PegStyle.d`), and the S-jog is
  level, since any slope binds with a fatter wire in smaller holes. It clears with 0.2 mm per side to spare. The S-bend now reads as a step.
- **2026-11-05 (v6):** The owner printed v5: the level step was much harder to get in than v4's 12° jog, and it was still loose.
  Back to 12°, and the wire went from 5.9 to 6.1 mm (shared `PegStyle.d`). The bend radius went from 3.0 to 3.5 so the thicker wire
  doesn't self-intersect, with a guard added. The flush-hang interference check is now information only: it predicted the wrong
  winner, and the prints are the test. Next: the peg gauge picks the final diameter.
