# Pegboard Bambu Lab badge

A one-piece badge that hangs flush on the pegboard: the Bambu Lab mark + "Bambu Lab" on one line, cut to the logo's
outline, in three colours (dark badge, white letters, green mark + accent) inlaid flush with the front. The shape and
colours follow a badge the owner liked on MakerWorld. Catalog part: see `docs/pegboard.md`.

![front and back](renders/face.png)

## Goal

A sign for the printer corner, as wide as the A1 can print, in one piece, hung from the board's holes, and printable
with no supports and a clean front.

## Status

- [x] v1 / v1.1 / v1.2 (2026-11-09): a 250 × 120 mm plate with the logo raised on top, hung from 2 separate hangers via
      keyhole slots. **Test print (2026-11-10):** the slots needed supports ("a disaster"), and one end of the front came
      out rough (that end most likely curled up off the bed and the nozzle dragged over it)
- [x] **v2 (2026-11-11):** redesigned as one piece, printed **face-down**. Owner chose a flush (inlaid) front over raised
      letters: raised letters plus pegs can't be one piece without supports (see "Why face-down")
- [x] 250 × 42.5 × 4.0 mm (pegs stand 14.5 mm off the back). Watertight, Euler 2,
      0 self-intersections. Rock-in check passes (`pb.rock_in`). Narrowest dark gap between colours 1.05 mm
- [ ] Owner review
- [ ] Test print and hang

## Why face-down

The pegs stick out of the back. Face-up (back on the plate), they'd hang under the part and the whole badge would need
supports. On its edge, every layer would need colour changes. Face-down, the front is the first layers on the plate
(smooth, and no top surface to go rough), the colours are all in the first 0.8 mm, and the pegs point straight up.
For the hooks to print without support in that pose, their behind-board leg rises at **45°** instead of straight up
(`PegStyle.hook_leg_angle`). They reach 14.5 mm behind the board's front face, less than your steel hooks.

The trade-off: the pegs are printed standing up (layers across them), the weak direction. The badge weighs about 30 g,
so the load is tiny, but don't lever it off the board by the edge. Rock it off the way it went on.

## Hanging it

2 hooks in one row, **8 holes apart**, each with a pin in the hole below. Tilt the badge (bottom out), push both hook tips
up through the holes, and swing the bottom in until the pins drop in. The badge's top sits 12.7 mm above
the hook holes and its bottom 29.8 mm below them.

## Measurements

| Feature | Value (mm) | Notes |
|---|---|---|
| Badge | 250 × 42.5 × 4.0 | `SIGN_W`, `T`. Outline = letters + 6.0 mm border (`BORDER`), notches under 8 mm filled, straight bottom |
| Letters | 23.0 tall (B), strokes 4.9 | the SVG's letters, "Lab" moved up beside "Bambu"; the mark scaled to the B's height |
| Colour inlay | 0.8 deep | white this thick hides the dark behind it |
| Narrowest dark gap | 1.05 | `MIN_GAP` 1.0. The B's accent is moved off the B (they touch in the SVG); the B's upper counter is shrunk 0.5 where it pinched its outline |
| Pegs | 5.7 hook (12° through the board, 45° leg, rises 6), 6.1 pins | shared `PegStyle` with `hook_gap` 4.8, `hook_rise` 6, `hook_leg_angle` 45 |
| Peg spacing | 203.2 (8 holes) | chosen by `place_pegs`: as wide as the outline allows with ≥ 1.2 of badge round each peg |

## Print settings

Open `output/pegboard-bambu-sign-multicolor.3mf` in Bambu Studio (load it as one object with multiple parts if it asks)
and set the filaments: **badge** dark grey or black, **letters** white, **mark + accent** green. As exported it lies
face-down: don't flip it.
- **Plate:** the front is printed on it, so the plate's finish is the badge's finish (textured PEI gives a matte texture,
  smooth PEI a gloss). Clean it with dish soap; glue stick if PLA lifts.
- **Brim:** add a 3–5 mm outer brim. A long thin part like this can curl at the ends (the v1 sign's rough end).
- **No supports.** If Bambu Studio adds any, turn them off: nothing overhangs.
- PLA is fine (indoor, ~30 g). 0.2 mm layers. Colour changes only in the first 4 layers (dark, white and green in each),
  so the prime tower stays short.
- One colour: `output/pegboard-bambu-sign.stl` (the logo won't show; it's flush).

## Open questions

- Colours: dark grey + white + green like the MakerWorld badge, or something else?
- The hooks' 45° legs reach 14.5 mm behind the board's front face. Your steel hooks reach ~15.6, so it should fit
  wherever they do.

## Pipeline

`build.py`: imports the logo SVG (`source/`), lays it out on one line (`layout`), fixes contacts the nozzle can't print
(`fix_contacts`), offsets it into the badge outline (`silhouette`), picks the peg columns and the badge's height on the
board (`place_pegs`), extrudes the badge and the inlays in the board frame, adds the shared pegs, and lays it face-down.
It asserts: watertight, 0 self-intersections, the inlays start on the plate, every colour gap ≥ `MIN_GAP`, and the badge
rocks onto the board (`pb.rock_in`). Outputs: the 3MF, merged STEP + STL, per-colour STLs, `report.json`, renders,
viewer meshes.

## Files

- `output/pegboard-bambu-sign-multicolor.3mf`: print this (three colours)
- `output/pegboard-bambu-sign.stl` / `.step`: merged, one colour / for Fusion
- `output/pegboard-bambu-sign-{dark,white,green}.stl`: the colour bodies
- `output/report.json`: checks, params, board fit, rock-in
- **Viewer artifact:** https://claude.ai/artifact/4U8kSuKhftWVvXnfHajBFU (publish updates to this URL)

## Log

- **2026-11-09:** v1. Owner wants a sign that hangs flat on the pegboard, Bambu Lab logo raised in a second colour, hung
  from the board's holes. Chose separate peg hangers + keyhole slots so the sign prints face up with one colour change
  and the pegs print the strong way. First cut used the mark alone on a 150 mm square.
- **2026-11-09 (v1.2):** Owner wasn't sure the pegs had room to go into the holes, and suggested moving the hooks up so they
  stick out of the top of the sign. The hangers already go on before the sign, so nothing is above them; the real problem
  was the hook's shape. A new rock-in simulation (`pb.rock_in`, calibrated on the owner's v4/v5 hook prints) showed the
  level 6.1 mm hook jams. Now 5.7 mm with a 12° slope, which passes. The same check fails the fit test and spool holder
  (flagged in `docs/pegboard.md`).
- **2026-11-09 (v1.1):** Owner wanted the "Bambu Lab" text too and the sign as big as the 256 mm bed allows. Now the full
  logo, 220 mm wide, on a 250 × 120 mm sign; hangers 8 holes apart.
- **2026-11-10:** Owner printed v1.2 (white sign, black logo). One end of the front came out rough: most likely that end
  lifted off the bed and the nozzle dragged over the top layers (the model is symmetric and the other end was clean).
- **2026-11-11 (v2):** Owner: the supports the hanger slots needed were a disaster; wants one piece, thinner is fine, and
  liked a MakerWorld badge (logo-outline shape; dark, white, green). One piece + raised letters can't print without
  supports, so the owner chose a flush, face-down badge. New: one-line layout, outline badge, 3-colour inlay, hooks with
  45° legs (`PegStyle.hook_leg_angle`, added to the shared tooling) so they print upright without support.
