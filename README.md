# 3D Printer Models

Models for 3D printing on a **Bambu Lab A1**: scans from Polycam (iOS), edits in
Autodesk Fusion, and reproducible Python cleanup pipelines.

## Projects

| Project | Status | Description |
|---|---|---|
| [gate-footing](projects/gate-footing/) | Idealised CAD model done (STEP + STL); waiting on real measurements for scale | Plastic foot that holds up a metal gate |

## Layout

- `projects/<name>/` has one folder per model: `source/` (raw), `build.py`,
  `output/` (print-ready), `renders/` (previews), and a `README.md` with status and notes
- `tools/` holds shared mesh tooling (`meshkit.py`, `render.py`, `inspect_mesh.py`)
- `docs/` holds workflow notes for the [A1](docs/bambu-a1.md), [Fusion](docs/fusion.md), and
  [Polycam scanning](docs/scanning-polycam.md)
- `CLAUDE.md` is guidance for AI agents working in this repo

## Quick start

```bash
pip install -r requirements.txt
python projects/gate-footing/build.py
python tools/inspect_mesh.py projects/gate-footing/output/gate-footing-clean.stl
```

New project: copy `projects/_template/` to `projects/<name>/` and fill in the README.
