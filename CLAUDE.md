# Agent guide: 3d-printer-models

This repo holds 3D models for printing: raw scans, cleanup pipelines, CAD
exports, and print-ready meshes. **Each model is a project in `projects/<name>/`.**
Global context lives here and in `docs/`, and each project's `README.md` holds that project's context.

## Start of every session

1. Read this file, then `projects/<name>/README.md` for the project you're
   working on. The project README's **Status / Next steps / Open questions**
   sections tell you where things stand.
2. Before ending a session, update that README (status, decisions, log
   entry) so the next session can pick up without re-deriving anything.

## Owner's setup

| What | Details |
|---|---|
| Printer | **Bambu Lab A1** (bed-slinger, open frame). Build volume **256 × 256 × 256 mm**. 0.4 mm nozzle (stock). See `docs/bambu-a1.md` |
| Slicer | Bambu Studio (takes STL / 3MF / STEP) |
| CAD | **Autodesk Fusion**, for hands-on edits. See `docs/fusion.md` for mesh import and export |
| Scanning | **Polycam on iOS**, exports GLB (metres, Y-up, textured). See `docs/scanning-polycam.md` |

## Conventions

- **Units: millimetres. Z-up.** The part rests on Z=0, centred on the XY origin,
  with its longest footprint axis along X. (Polycam is metres/Y-up, and the
  pipeline converts.)
- **Don't trust scan scale.** Photo-mode Polycam scans can be off by a lot.
  Always get at least one real tape or caliper measurement from the owner and
  record it in the project README. Scale correction happens in `build.py`.
- **Printable output must be watertight (manifold)**, with no self-intersections
  and a flat base. Check it with `python tools/inspect_mesh.py <file>`.
- **Fit check:** anything bigger than 256 mm on any axis must be split
  (with alignment pins/keys) or scaled. `report()` flags this.
- **Outdoor or load-bearing parts:** default to PETG. PLA creeps and degrades
  in sun, and ASA/ABS warp on the open-frame A1.

## Repo layout

```
CLAUDE.md               this file (global agent context)
README.md               human overview + project index
docs/                   workflow notes: printer, Fusion, Polycam
tools/                  shared Python tooling (import from project build scripts)
  meshkit.py            scan → solid pipeline steps, CAD→mesh repair, printability report
  render.py             headless PNG previews + cross-sections (no GPU)
  inspect_mesh.py       CLI report for any mesh
projects/
  _template/            copy this to start a new project
  <name>/
    README.md           project context: goal, measurements, status, log
    build.py            reproducible pipeline: source/ → output/ + renders/
    idealized.py        (optional) parametric CAD model fitted to the scan
    source/             raw inputs, never edited (scans, photos, reference)
    output/             generated, print-ready files (STL/3MF/STEP) + report.json
    renders/            generated PNG previews (read these to "see" the model)
    fusion/             (optional) Fusion exports (.f3d/.step) from the owner
```

Rules:
- **Never modify files in `source/`.** Add new scans with a dated name.
- Everything in `output/` and `renders/` must be regenerable by
  `python projects/<name>/build.py`. Change the script, not the output.
- Commit generated outputs too, so the owner can grab STLs straight from GitHub.
- Binary files are committed directly (no LFS). If a file gets over ~50 MB,
  raise it with the owner before committing.

## Tooling

```
pip install -r requirements.txt     # the SessionStart hook does this on the web
python projects/<name>/build.py     # rebuild one project
python tools/inspect_mesh.py file.stl
python tools/render.py file.stl out.png
```

- Python + `trimesh` for mesh work. `pymeshlab` checks self-intersections and
  does repair (on Linux it needs `libopengl0`). `manifold3d` does fast mesh booleans.
- **`build123d`** (OpenCASCADE) is for parametric CAD: real fillets and chamfers, and STEP
  export that Fusion opens as an editable solid. Tessellate with
  `meshkit.cad_to_mesh()` (it stitches OCC's hairline seams so the STL is watertight).
  Fillet order matters. If a fillet fails, apply it earlier or build it into the
  sketch or cutter shape instead.
- You can't open a 3D viewer, so **render PNGs and look at them** (Read the
  image). Cross-sections show more than shaded views for checking dimensions.
- Polycam GLBs duplicate vertices at texture seams. `meshkit.load_scan` merges
  them. Without that, one object looks like hundreds of fragments.

## Working with the owner

- Ask for real measurements early (overall L × W × H plus any critical fit
  dimension, like a slot the gate post sits in).
- **Scans are wavy, and real parts usually aren't.** When the owner wants a clean part,
  don't just smooth the mesh. Measure profiles off the cleaned scan (cross-sections)
  and rebuild the part as parametric CAD (`idealized.py`, see gate-footing),
  then overlay model vs scan sections to check the fit. Keep the parameters at scan scale
  and apply the real measurements in `build.py`.
- Scans can't see hidden faces (undersides, slot interiors). Ask about them.
- Keep a short dated **Log** at the bottom of each project README.
