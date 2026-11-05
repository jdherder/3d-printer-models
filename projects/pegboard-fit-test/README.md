# Pegboard fit test

A small test piece: a 4 mm plate with one shared hook peg and one pin, 1 in apart. It's built only from
`tools/pegboard.py`, so it tests exactly the pegs every catalog part uses. **Print this before any other
catalog part**, and again whenever `PegStyle` or the board changes.

![fit test](renders/fit-test.png)

## Goal

Confirm on the real board that the shared pegs go on and come off cleanly and sit snug. Then tune `PegStyle` /
`BOARDS` in `tools/pegboard.py` (one place, so every part follows).

## Status

- [x] Built from the shared interface. 47.4 × 16.8 × 12.4 mm, watertight, 0 self-intersections
- [x] Checked against the owner's board (Menards 3/16 white hardboard, listing values: 7.14 mm holes, 3.94 mm thick):
      clears it with 0.2 mm per side to spare
- [ ] Owner prints it (PETG) and hangs it on the real board: snug, loose, or tight?
- [ ] Caliper the real board (hole diameter, thickness) and correct `BOARDS["white_3_16"]` if it differs

## Measurements

The pegs come from the steel hook (`projects/pegboard-hook`): 5.53 mm diameter, 7.3 mm clear behind the front face,
leg rising 14 mm above the hole centre, 4.5 mm bend radius, 7 mm pin. On the owner's board that's 0.8 mm clearance per
side in the hole and 3.4 mm of room behind the board, so expect it to be a little loose. If it's sloppy, the pegs can grow to ~6.5 mm.

| Feature | Value (mm) | Source |
|---|---|---|
| Board | Menards "3/16 x 4 x 8 White Pegboard Panel" | owner, 2026-11-05 |
| Hole diameter | 7.14 (9/32 in) | retailer listings for this panel; caliper to confirm |
| Thickness | 3.94 (0.155 in) | retailer listings; caliper to confirm |

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
- **2026-11-05:** The owner's board is a Menards 3/16 in white hardboard panel. Added it as `pegboard.DEFAULT_BOARD`
  (listing values 7.14 mm holes, 3.94 mm thick), and fit checks now leave 0.2 mm per side. The fit test clears it.
