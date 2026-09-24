# 3D Printer Models

Models for 3D printing on a **Bambu Lab A1**: scans from Polycam (iOS), edits in
Autodesk Fusion, and reproducible Python cleanup pipelines.

## Projects

| Project | Status | Description |
|---|---|---|
| [gate-footing](projects/gate-footing/) | Real size (100 mm), print-ready STEP + STL; next: test print | Plastic foot that holds up a metal gate |

## Layout

- `projects/<name>/` has one folder per model: `source/` (raw), `build.py`,
  `output/` (print-ready), `renders/` (previews), and a `README.md` with status and notes
- `tools/` holds shared mesh tooling (`meshkit.py`, `render.py`, `inspect_mesh.py`)
- `docs/` holds workflow notes for the [A1](docs/bambu-a1.md), [Fusion](docs/fusion.md),
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
