# Custom pegboard parts

Shared tooling: **`tools/pegboard.py`**. Every catalog part hangs on the same pegs, defined once there.

## Catalog

Each part is its own project, named **`projects/pegboard-<thing>/`**. Add a row here when you add one.

| Part | What it is | Pegs | Print | Status |
|---|---|---|---|---|
| [pegboard-fit-test](../projects/pegboard-fit-test/) | Plate with one hook peg + one pin. **Print first** to check the shared pegs on the real board | shared | PETG, on its side, no supports | v3: 6.1 mm pegs + **peg gauge** (6.0–6.4 mm) to pick the final size |
| [pegboard-hook](../projects/pegboard-hook/) | Copy of the owner's steel hook (42 mm arm), printed at 6.1 mm wire, with a 12° S-bend (it rocks in easily). The reference the peg sizes came from | its own wire (S-bend) | PETG, on its side, no supports | v6: 12° S-bend restored (v5's level step was hard to get in), 6.1 mm wire |
| [pegboard-spool-holder](../projects/pegboard-spool-holder/) | Arm straight out of the board that holds the A1's active 1 kg spool (face parallel to the board), with an end lip. Bores ≥ 50 mm, spools up to 82 mm wide | shared: 2 hooks side by side + 4 pins 2 and 3 in below | PETG, on its side, supports under the 2nd peg column | v3: two hooks, 3 in span, 4 pins; next, owner review (where it hangs vs the A1's bed travel) |

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
| `d` | 6.1 | Peg diameter. The steel wire is 5.53. Prints at 5.53 and 5.9 were loose in the owner's holes. Pick the final size with the peg gauge |
| `hook_gap` | 7.3 | Clear space behind the front face for the board. It must exceed the board thickness |
| `hook_rise` | 14.0 | How high the hook's rising leg reaches above the hole centre |
| `bend_r` | 4.5 | Centreline radius of the hook's bend |
| `pin_len` | 7.0 | How far the anti-rotation pin reaches past the front face |

- `hook_peg(style, y, z)`: an upper peg that goes straight through the board, bends, and rises behind it. It carries the load.
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
  still goes in by hand, and set `PegStyle.d` to it. Every part follows.
