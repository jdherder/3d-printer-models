# Custom pegboard parts

Shared tooling: **`tools/pegboard.py`**. Reference part: **`projects/pegboard-hook/`**, the owner's steel hook,
modelled from photos. The peg defaults come from it, and its build also makes the fit-test piece.

## The standard

| | 1/4 in board (`BOARDS["quarter"]`) | 1/8 in board (`BOARDS["eighth"]`) |
|---|---|---|
| Hole grid | 1 in (25.4 mm) square | 1 in (25.4 mm) square |
| Hole diameter | 1/4 in (6.35 mm) nominal | 3/16 in (4.76 mm) |
| Thickness | ~6.35 mm (real boards are often 5–6 mm) | ~3.2 mm |

These are nominal values, and real boards vary. Once the owner calipers their board, add it to `BOARDS` and make it the default.

## Board frame

Build every pegboard part in the board frame. That way the pegs, fit checks and viewer all agree:
- **x** points out of the board. The board's **front face is x = 0**, and the board fills `-thickness ≤ x ≤ 0`.
- **y** points up, and **z** runs across.
- The origin is a hole centre on the front face. Hole centres sit at `(0, row·25.4, col·25.4)`.

The part's back face sits on x = 0, and its body is built out in +x.

## Pegs (`PegStyle`, from the steel hook)

| Field | Default | Meaning |
|---|---|---|
| `d` | 5.53 | Peg diameter. The steel wire, which leaves 0.4 mm clearance per side in a 6.35 mm hole |
| `hook_gap` | 7.3 | Clear space behind the front face for the board. It must exceed the board thickness |
| `hook_rise` | 14.0 | How high the hook's rising leg reaches above the hole centre |
| `bend_r` | 4.5 | Centreline radius of the hook's bend |
| `pin_len` | 7.0 | How far the anti-rotation pin reaches past the front face |

- `hook_peg(style, y, z)`: an upper peg that goes straight through the board, bends, and rises behind it. It carries the load.
- `pin_peg(style, y, z)`: a lower straight pin. It stops the part rotating or lifting out.
- `mount_plate(style, cols, rows, thickness)`: a back plate with hooks in the top row of holes and pins in the bottom row. Build the part's body on its front face (x = thickness).
- `style.check(board)`: lists the problems if the pegs won't fit that board.

To hang a part, tilt it, push the hook tips up through the holes, then swing the bottom in until the pins drop into place.
Use at least two holes of vertical span (a hook row above a pin row). For anything heavy or wide, put hooks in two or more columns.

## Checks and previews

```python
import meshkit as mk, pegboard as pb
board = pb.board_mesh(pb.BOARDS["quarter"], rows=range(-1, 3), cols=range(-1, 2))
assert pb.interference_mm3(mk.cad_to_mesh(part), board) == 0      # the part fits as hung
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
- PETG by default. Plastic pegs at 5.5 mm are fine for light and medium loads (tools, cables, small bins).
  For heavy loads, add more peg columns or a wider plate rather than bigger pegs. The hole caps the peg size.
- **First, print `projects/pegboard-hook/output/pegboard-fit-test.stl`** (a plate with one hook and one pin) and hang it on
  the real board. If it's loose or tight, adjust `PegStyle` in one place and every part follows.
