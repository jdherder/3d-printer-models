# Custom pegboard parts

Shared tooling: **`tools/pegboard.py`**. Every catalog part hangs on the same pegs, defined once there.

## Catalog

Each part is its own project, named **`projects/pegboard-<thing>/`**. Add a row here when you add one.

| Part | What it is | Pegs | Print | Status |
|---|---|---|---|---|
| [pegboard-fit-test](../projects/pegboard-fit-test/) | Plate with one hook peg + one pin. **Print first** to check the shared pegs on the real board | shared | PETG, on its side, no supports | v4: 12° sloped 5.7 mm hook + 6.1 mm pin (rock-in checked) + **peg gauge** (pins 6.0–6.4 mm) to pick the pin size |
| [pegboard-hook](../projects/pegboard-hook/) | Copy of the owner's steel hook (42 mm arm), printed at the steel wire's 5.53 mm, with a 12° S-bend (it rocks in easily) and a 6.1 mm pin. The reference the peg sizes came from | its own wire (S-bend) + shared pin size | PETG, on its side, no supports | v7: back to 5.53 mm wire (6.1 can't rock in), 6.1 mm pin; rock-in checked |
| [pegboard-spool-holder](../projects/pegboard-spool-holder/) | Arm straight out of the board that holds the A1's active 1 kg spool (face parallel to the board), with an end lip. Bores ≥ 50 mm, spools up to 82 mm wide | shared: 2 hooks side by side + 4 pins 2 and 3 in below | PETG, on its side, supports under the 2nd peg column | v5: sloped 5.7 mm hooks (rock-in checked); next, owner review (where it hangs vs the A1's bed travel) |
| [pegboard-bambu-sign](../projects/pegboard-bambu-sign/) | 250 × 120 mm sign, flush on the board, Bambu Lab logo + text raised in a 2nd colour. Hangs on 2 small hangers via hidden keyhole slots (slide down 14 mm) | shared: 2 hangers, 8 holes apart, hook + pin each | Sign PLA face up, 1 colour change; hangers on their side ×2 | v1.2: sloped hooks so the hangers rock in; next, owner review |
| [pegboard-mat-holder](../projects/pegboard-mat-holder/) | Thin slotted strip (194 × 17 mm) that holds the A3 + A4 cutting mats upright, leaning back against the board | shared: 2 hooks + 2 pins, 7 holes apart | PETG, standing on its bottom edge, supports under the 2 hooks | v0.2 concept (3.5 mm slots for the 2.5–3 mm mats); next, owner review (lean, orientation) |

### Adding a part

1. Copy `projects/_template/` to `projects/pegboard-<thing>/` and get real measurements of whatever it holds.
2. Build it in the board frame (below): the body on the front of `pb.mount_plate(...)`, or your own body plus
   `pb.hook_peg` / `pb.pin_peg`. Don't redraw pegs.
3. In `build.py`: `assert not STYLE.check(BOARD)`, assert `pb.interference_mm3(...) == 0` against `pb.board_mesh(BOARD)`,
   export the print pose (STEP + STL), and export `pb.to_zup(...)` meshes for the viewer (copy `projects/pegboard-fit-test/`).
4. Add a row to the catalog table above and the root `README.md`, then run the review (`/model-review pegboard-<thing>`).

## The standard

| | **Owner's board** (`BOARDS["white_3_16"]`, the default) | 1/4 in board (`BOARDS["quarter"]`) | 1/8 in board (`BOARDS["eighth"]`) |
|---|---|---|---|
| Product | Menards 3/16 × 4 × 8 white pegboard panel (tempered hardboard) | generic | generic |
| Hole grid | 1 in (25.4 mm) | 1 in | 1 in |
| Hole diameter | **1/4 in (6.35 mm)**, owner measured | 1/4 in (6.35 mm) | 3/16 in (4.76 mm) |
| Thickness | **0.155 in (3.94 mm)** actual, from listings | ~6.35 mm | ~3.2 mm |

`pb.DEFAULT_BOARD` is the owner's board, so check every catalog part against it. The owner measured 1/4 in holes on 1 in centres
(the listings had said 9/32 in holes). The thickness is still the listing's 0.155 in.
Update `BOARDS["white_3_16"]` if a caliper says otherwise, then rebuild the catalog.

Fit checks use `board_mesh(..., clearance=pb.FIT_CLEARANCE)` (0.2 mm per side), so "0 interference" leaves real margin.

## Board frame

Build every pegboard part in the board frame. That way the pegs, fit checks and viewer all agree:
- **x** points out of the board. The board's **front face is x = 0**, and the board fills `-thickness ≤ x ≤ 0`.
- **y** points up, and **z** runs across.
- The origin is a hole centre on the front face. Hole centres sit at `(0, row·25.4, col·25.4)`.

The part's back face sits on x = 0, and its body is built out in +x.

## Pegs (`PegStyle`, from the steel hook)

| Field | Default | Meaning |
|---|---|---|
| `d` | 6.1 | **Pin** diameter. The steel wire is 5.53. Prints at 5.53 and 5.9 were loose in the owner's holes. Pick the final size with the peg gauge |
| `hook_d` | 5.7 | **Hook** diameter. Thinner than the pin so the sloped hook rocks in (`rock_in`); a 6.1 mm hook jams, level or sloped. Its play doesn't matter: the load seats it |
| `hook_slope` | 12 | The hook's through-board part rises toward the back at this angle, like the steel hook's S-jog. It guides the hook as it rocks in |
| `hook_gap` | 7.3 | Clear space behind the front face for the board. It must exceed the board thickness |
| `hook_rise` | 14.0 | How high the hook's rising leg reaches above the hole centre |
| `bend_r` | 4.5 | Centreline radius of the hook's bend |
| `pin_len` | 7.0 | How far the anti-rotation pin reaches past the front face |

- `hook_peg(style, y, z)`: an upper peg that goes back through the board (rising at `hook_slope`), bends, and rises behind it. It carries the load.
- `pin_peg(style, y, z)`: a lower straight pin. It stops the part rotating or lifting out.
- `mount_plate(style, cols, rows, thickness)`: a back plate with hooks in the top row of holes and pins in the bottom row. Build the part's body on its front face (x = thickness).
- `style.check(board)`: lists the problems if the pegs won't fit that board.

Fit checks keep `FIT_CLEARANCE` = 0.1 mm per side. The owner's printed pegs come out loose rather than fat.

**Rocking in:** a part goes on by rocking around its hooks, so anything on the board above the hooks swings into the board.
`mount_plate` stops the plate just above the hooks and rounds its top back edge (the first fit test, with 8 mm of plate above
the hook, was harder to put on). Keep a part's body clear of the board above its hook row, or round it the same way.

**The flush check is strict for sloped wires.** `interference_mm3` assumes the part hangs perfectly flush. Straight pegs like
`hook_peg` must pass it. A sloped wire like the steel hook's S-bend fails it, yet rocks in fine and goes in more easily than a level
step (owner's prints, v4 vs v5). For those, report the overlap and trust a test print.

**Rock-in check (`pb.rock_in`).** It simulates taking the hung part off (tilt the bottom out about the hook row, slide in x/y)
with the holes `ROCK_IN_GIVE` = 0.3 mm larger than nominal, for the hardboard's give. That value is calibrated on the owner's
`pegboard-hook` prints: it passes v4 (5.53 mm, 12° S-jog, went in easily) and fails v5 (5.9 mm level step, much harder).
Every catalog part's build asserts it. Findings (2026-11-09):
- A **level 6.1 mm hook jams**. Its straight part sits in a 3.94 mm-long hole with ~0.1 mm clearance, so it can only tilt ~3°.
  The fit test and spool holder had this hook until v4/v5. If those prints were hard to put on, that's why.
- At 6.1 mm, a slope steep enough to guide the hook doesn't fit through the hole (or 5.9 mm). **5.7 mm with a 12° slope passes**,
  and so does 5.53 at 8–12°. The pins don't need to shrink: 6.1 mm pins pass with the 5.7 mm sloped hook.
  So `PegStyle` now has a thinner sloped hook (`hook_d`, `hook_slope`) and a snug pin (`d`).
- The steel-hook copy's own S-jog needs 5.53 mm (5.7 jams there).
- A sloped hook overlaps a little in the strict flush check. Report that as information and assert `rock_in` instead.

To hang a part, tilt it, push the hook tips up through the holes, then swing the bottom in until the pins drop into place.
Use at least two holes of vertical span (a hook row above a pin row). For anything heavy or wide, put hooks in two or more columns.

## Checks and previews

```python
import meshkit as mk, pegboard as pb
board = pb.board_mesh(pb.DEFAULT_BOARD, rows=range(-1, 3), cols=range(-1, 2), clearance=pb.FIT_CLEARANCE)
assert pb.interference_mm3(mk.cad_to_mesh(part), board) == 0      # fits as hung, with 0.2 mm per side to spare
pb.to_zup(mk.cad_to_mesh(part)).export("renders/asm-part.stl")    # for the review viewer
pb.to_zup(board).export("renders/ref-pegboard.stl")
```

## Printing

- **Pegs are the weak point.** Print with the pegs lying in the bed plane, so the layers run along them.
  A peg printed standing up snaps off at a layer line. `lay_on_side(part, style)` sets this pose: it puts the pegs on
  the bed with a 0.4 mm flat for the first layer, and needs no supports if the pegs are the lowest thing.
  So it suits parts whose pegs are all in one column, or parts designed so the peg column sits on the bed.
- With pegs in more than one column, some pegs won't touch the bed when it lies on its side. Either accept supports
  under those pegs, or make the pegs a separate printed or steel piece.
- PETG by default. Plastic pegs at ~6 mm are fine for light and medium loads (tools, cables, small bins).
  For heavy loads, add more peg columns or a wider plate rather than bigger pegs. The hole caps the peg size.
- **First, print `projects/pegboard-fit-test/output/pegboard-fit-test.stl`** (a plate with one hook and one pin) and hang it on
  the real board. If it's loose or tight, print the **peg gauge** (`pegboard-peg-gauge.stl`, labelled pins 6.0–6.4 mm), pick the snuggest pin that
  still goes in by hand, and set `PegStyle.d` to it. Every part's pins follow. The hook stays thinner (`hook_d`); after changing
  sizes, rebuild and let `rock_in` confirm the hooks still go in.
