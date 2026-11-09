# 3D Printer Models

Models for 3D printing on a **Bambu Lab A1**: scans from Polycam (iOS), edits in
Autodesk Fusion, and reproducible Python cleanup pipelines.

## Projects

Pegboard parts form a catalog, with shared pegs: see [docs/pegboard.md](docs/pegboard.md).

| Project | Status | Description |
|---|---|---|
| [gate-footing](projects/gate-footing/) | Real size (100 mm), print-ready STEP + STL; next: test print | Plastic foot that holds up a metal gate |
| [wagon-cup-holder](projects/wagon-cup-holder/) | v9: right and left clips (mirror images) + one shared cup module; snap-on ring + strut grip, no screws; next: print and test the left clip | Side-rail cup holder for a 20 oz Yeti on a MAC wagon, quick on/off for folding |
| [pegboard-hook](projects/pegboard-hook/) | v6: 12° S-bend back (it went in easily), 6.1 mm wire; next: reprint | Pegboard catalog: copy of the steel hook, the reference for the shared pegs |
| [pegboard-fit-test](projects/pegboard-fit-test/) | v3: 6.1 mm pegs + peg gauge (6.0–6.4 mm); next: print the gauge, pick the size | Pegboard catalog: test piece for the shared hook peg + pin (`tools/pegboard.py`) |
| [santa-bat-ornament](projects/santa-bat-ornament/) | v9: 50 mm wingspan, black base + red/white layered on top (~5 AMS swaps), raised soft-edged textured white trim, 1.2 mm hole through the pom-pom; next: test print | Flat hanging ornament: the paper wall bat in a Santa hat |
| [pegboard-spool-holder](projects/pegboard-spool-holder/) | v4: two hooks side by side + four pins (3 in span), 82 mm rounded-top arm with end lip; next: owner review, test print | Pegboard catalog: holds the A1's active spool on the board behind the printer |

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
