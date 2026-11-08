# Pegboard spool holder

Holds the A1's active spool on the pegboard behind the printer, instead of on the printer's own spool holder.
The spool hangs "sideways": a straight arm sticks out of the board and the spool sits on it with its face parallel to the
board, like a paper-towel holder. Catalog part: see `docs/pegboard.md`.

![spool holder](renders/spool-holder.png)

## Goal

A spool holder that hangs on the shared pegs, takes any normal 1 kg spool, and is strong enough to carry it full.

## Status

- [x] v1 designed: one column of shared pegs (hook in a hole, pin 2 holes / 2 in below), 5 mm plate, 22 × 26 mm arm with
      45° chamfered top edges (the spool turns on the 10 mm flat between them), 82 mm of reach, 8 mm end lip.
      106 × 73 × 22 mm print, watertight, 0 self-intersections, clears the board (0.1 mm per side)
- [x] Spool checks: arm + lip pass through a 50 mm bore; spools up to 82 mm wide fit; the reference 200 × 68 mm spool
      (53 mm bore) clears the arm and board
- [ ] Owner review: where it hangs behind the A1, filament path, fixed arm vs spinning hub (Open questions)
- [ ] Test print and hang with a full spool

## Measurements

| Feature | Value (mm) | Source |
|---|---|---|
| Reference spool | 200 OD × 68 wide, 53 bore | typical 1 kg spool (Bambu); not measured yet |
| Spool bores handled | ≥ 50 | design limit (`MIN_BORE`) |
| Widest spool | 82 | `ARM_REACH` |
| Board | Menards 3/16 in white, 6.35 holes, 1 in grid | `pegboard.DEFAULT_BOARD` |

Where a 200 mm spool ends up, relative to the hook's hole: centre 31 below, bottom 131 below, top 69 above;
centre 40 out from the board, front face 74 out. The arm tip is 93 mm out from the board.

## Print settings

PETG (it carries ~1.2 kg all the time, and PLA creeps). On its side as exported: the pegs and the arm lie flat on the bed,
so the layers run along both. No supports (the bed-side chamfer is a 45° overhang). 4 walls, 20–30 % gyroid.
About 55 cm³, so roughly 70 g of filament.

## Open questions

- **Where does it hang behind the A1?** The A1's bed slides toward the board, and the spool stands 74 mm out from it, so the
  spool must sit above or beside the bed's travel. Which hole should the hook go in?
- **Filament path:** does the filament reach the A1's PTFE tube / runout sensor from there, or should I add a tube guide
  or clip?
- **Drag:** v1 is a fixed arm (the spool's bore turns on the flat top, PETG on plastic). If the drag is too much, v2 could add
  a spinning hub on two 608 bearings.
- Measure the real spools (Overture, etc.): outside diameter, width and bore.

## Pipeline

`build.py` builds `pegboard.mount_plate(PegStyle(), cols=(0,), rows=(0, 2), thickness=5)` with its bed-side edge flush
with the pegs, adds the arm and lip, lays it on its side (`pegboard.lay_on_side`), exports the STEP and STL, and asserts:
zero overlap with the board, the arm + lip pass through a 50 mm bore, and the reference spool clears the arm and board.
Parameters at the top of `build.py` (`ARM_*`, `LIP_*`, `ROWS`, `SPOOL`).

## Files

- `output/pegboard-spool-holder.stl`: print this
- `output/pegboard-spool-holder.step`: editable solid for Fusion
- `output/report.json`: checks, params, board fit, spool fit
- **Viewer artifact:** https://claude.ai/artifact/7qNGasQkhXUMmqVtrSyc8Q (publish updates to this URL)

## Log

- **2026-11-08:** v1. The owner wants the A1's active spool on the pegboard behind the printer, held sideways. One peg column
  (hook + pin 2 in apart) so it prints on its side with every peg on the bed; a fixed arm with a chamfered top and an end lip.
