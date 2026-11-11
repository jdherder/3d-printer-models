# 3D Printer Models

Models for 3D printing on a **Bambu Lab A1**: scans from Polycam (iOS), edits in
Autodesk Fusion, and reproducible Python cleanup pipelines.

## Projects

Pegboard parts form a catalog, with shared pegs: see [docs/pegboard.md](docs/pegboard.md).

| Project | Status | Description |
|---|---|---|
| [gate-footing](projects/gate-footing/) | Real size (100 mm), print-ready STEP + STL; next: test print | Plastic foot that holds up a metal gate |
| [wagon-cup-holder](projects/wagon-cup-holder/) | v9: right and left clips (mirror images) + one shared cup module; snap-on ring + strut grip, no screws; next: print and test the left clip | Side-rail cup holder for a 20 oz Yeti on a MAC wagon, quick on/off for folding |
| [pegboard-hook](projects/pegboard-hook/) | v7: 5.53 mm wire like v4 (6.1 can't rock in), 6.1 mm pin, 12° S-bend, rock-in checked; next: reprint | Pegboard catalog: copy of the steel hook, the reference for the shared pegs |
| [pegboard-fit-test](projects/pegboard-fit-test/) | v4: 5.7 mm hook sloped 12° + 6.1 mm pin (rock-in checked), peg gauge (6.0–6.4 mm pins); next: print both, pick the pin size | Pegboard catalog: test piece for the shared hook peg + pin (`tools/pegboard.py`) |
| [santa-bat-ornament](projects/santa-bat-ornament/) | v10: 50 mm wingspan, black base + red/white layered on top, raised white trim with rounded edges, 1.2 mm hole through the pom-pom; next: test print | Flat hanging ornament: the paper wall bat in a Santa hat |
| [pegboard-spool-holder](projects/pegboard-spool-holder/) | v5: two sloped 5.7 mm hooks (rock-in checked) + four pins (3 in span), 82 mm rounded-top arm with end lip; next: owner review, test print | Pegboard catalog: holds the A1's active spool on the board behind the printer |
| [pegboard-bambu-sign](projects/pegboard-bambu-sign/) | v1.2: 250 × 120 mm, full logo raised 1.2 mm (one colour change), 2 hangers with the shared sloped hooks (rock-in checked) + keyhole slots; next: owner review, test print | Pegboard catalog: Bambu Lab logo sign that hangs flush on the board |
| [pegboard-mat-holder](projects/pegboard-mat-holder/) | v0.2: 194 × 17 mm strip, 3.5 mm slots, 2 tilted slots, 2 hooks + 2 pins (rock-in checked); next: test print | Pegboard catalog: holds the A3 + A4 cutting mats leaning against the board |
| [bike-hook](projects/bike-hook/) | v2.1: on the pegboard (8 holes in 3 rows, works with 2 or 3 rows over the 2x4 behind), arm beside the wheel + bar through the spokes, wheel straight with tires on the board, no supports; next: owner's 2x4/bike/wheel numbers, test print | Wall hook that hangs a bike vertically by its front rim, perpendicular to the wall |

## Layout

- `projects/<name>/` has one folder per model: `source/` (raw), `build.py`,
  `output/` (print-ready), `renders/` (previews), and a `README.md` with status and notes
- `tools/` holds shared mesh tooling (`meshkit.py`, `render.py`, `inspect_mesh.py`)
- `docs/` holds workflow notes for the [A1](docs/bambu-a1.md), [Fusion](docs/fusion.md), [pegboard parts](docs/pegboard.md),
  [Polycam scanning](docs/scanning-polycam.md), and the [model review process](docs/review.md)
- `CLAUDE.md` is guidance for AI agents working in this repo

## Quick start

```bash
pip install -r requirements.txt
python projects/gate-footing/build.py
python tools/inspect_mesh.py projects/gate-footing/output/gate-footing.stl
python tools/make_viewer.py projects/gate-footing   # interactive 3D review page
```

New project: copy `projects/_template/` to `projects/<name>/` and fill in the README.
