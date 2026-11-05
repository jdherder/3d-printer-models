# Pegboard fit test

A small test piece: a 4 mm plate with one shared hook peg and one pin, 1 in apart. It's built only from
`tools/pegboard.py`, so it tests exactly the pegs every catalog part uses. **Print this before any other
catalog part**, and again whenever `PegStyle` or the board changes.

![fit test](renders/fit-test.png)

## Goal

Confirm on the real board that the shared pegs go on and come off cleanly and sit snug. Then tune `PegStyle` /
`BOARDS` in `tools/pegboard.py` (one place, so every part follows).

## Status

- [x] Built from the shared interface. 47.4 × 16.8 × 12.4 mm, watertight, 0 self-intersections,
      0 mm³ overlap with a nominal 1/4" board
- [ ] Owner prints it (PETG) and hangs it on the real board: snug, loose, or tight?
- [ ] Caliper the real board (hole diameter, thickness), then add it to `pegboard.BOARDS` and make it the default

## Measurements

The pegs come from the steel hook (`projects/pegboard-hook`): 5.53 mm diameter, 7.3 mm clear behind the front face,
leg rising 14 mm above the hole centre, 4.5 mm bend radius, 7 mm pin. On a nominal 1/4" board (6.35 mm holes, 6.35 mm thick)
that's 0.41 mm clearance per side in the hole and 0.95 mm of room behind the board.

| Feature | Real (mm) | Notes |
|---|---|---|
| Board hole diameter | ? | Owner to caliper. The nominal is 6.35 |
| Board thickness | ? | Owner to caliper. The nominal is 6.35 |

## Print settings

PETG, on its side (pegs flat on the bed, 0.4 mm flat), no supports. About 15 minutes.

## Pipeline

`build.py` builds `pegboard.mount_plate(PegStyle(), cols=(0,), rows=(0, 1), thickness=4)` with the plate's lower edge flush
with the pegs, lays it on its side (`pegboard.lay_on_side`), exports the STEP and STL, and asserts zero overlap with the board.

## Files

- `output/pegboard-fit-test.stl`: print this
- `output/pegboard-fit-test.step`: editable solid for Fusion
- `output/report.json`: checks, peg style, board fit
- **Viewer artifact:** https://claude.ai/artifact/UwaRj3ht4BSYQHvKqeFPXS (publish updates to this URL)

## Log

- **2026-11-05:** Split out of `pegboard-hook` into its own project, as the check for the shared pegboard interface.
