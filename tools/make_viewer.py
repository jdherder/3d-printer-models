"""Build a self-contained interactive 3D review page for a project.

    python tools/make_viewer.py projects/<name>

Reads projects/<name>/review.json and writes projects/<name>/renders/viewer.html:
a single HTML file (three.js from cdnjs, meshes embedded) that you can open
locally or publish as a claude.ai Artifact. See docs/review.md.

review.json:
{
  "title": "Gate footing: idealised model",
  "subtitle": "Parametric CAD rebuild of the Polycam scan · Z-up · millimetres",
  "meshes": [                                  # first mesh drives dims and fit check
    {"path": "output/gate-footing.stl", "label": "Idealised model", "style": "solid"},
    {"path": "output/gate-footing-scan-clean.stl", "label": "Original scan",
     "style": "wire", "visible": false}
  ],
  "dims": [{"label": "Slot width", "param": "slot_w"}, {"label": "Base", "mm": 50}],
  "scale_note": "Showing scan scale ...",      # optional
  "notes_title": "What changed from the scan",  # optional
  "notes": "..."                                # optional
}

A dim may give "mm" directly or "param": a key of output/report.json's
"params_mm" (so the page always matches the last build).
"""

import base64
import html
import json
import sys
from pathlib import Path

import numpy as np
import trimesh

TEMPLATE = Path(__file__).with_name("viewer_template.html")


def pack_mesh(path: Path, crease: float | None) -> dict:
    """Quantised, base64 mesh in three.js Y-up coordinates (~10 bytes/vertex)."""
    mesh = trimesh.load(path, force="mesh")
    if crease:  # split vertices at sharp edges so CAD edges stay crisp
        mesh = trimesh.graph.smooth_shade(mesh, angle=crease)
    v, n, f = mesh.vertices, mesh.vertex_normals, mesh.faces
    if len(v) >= 65536:
        raise ValueError(f"{path}: {len(v)} vertices; simplify below 65k for the viewer")
    v = np.c_[v[:, 0], v[:, 2], -v[:, 1]]  # Z-up -> Y-up
    n = np.c_[n[:, 0], n[:, 2], -n[:, 1]]
    scale = float(np.abs(v).max()) / 32000.0
    enc = lambda a: base64.b64encode(a.tobytes()).decode()  # noqa: E731
    return {"scale": scale,
            "pos": enc(np.round(v / scale).astype("<i2")),
            "nrm": enc(np.round(n * 127).astype("i1")),
            "idx": enc(f.astype("<u2"))}


def main(project_dir: str):
    project = Path(project_dir).resolve()
    cfg = json.loads((project / "review.json").read_text())
    report_path = project / "output" / "report.json"
    params = json.loads(report_path.read_text()).get("params_mm", {}) if report_path.exists() else {}

    meshes = []
    for m in cfg["meshes"]:
        crease = None if m.get("style") == "wire" else m.get("crease", 0.35)
        meshes.append({**{k: v for k, v in m.items() if k != "path"},
                       "data": pack_mesh(project / m["path"], crease)})
    dims = []
    for d in cfg.get("dims", []):
        mm = d["mm"] if "mm" in d else params[d["param"]]
        dims.append({"label": d["label"], "mm": mm})

    page_cfg = {k: v for k, v in cfg.items() if k not in ("meshes", "dims")}
    page_cfg.update(meshes=meshes, dims=dims)
    page = (TEMPLATE.read_text()
            .replace("__TITLE__", html.escape(cfg.get("page_title", cfg["title"])))
            .replace("__CONFIG__", json.dumps(page_cfg).replace("</", "<\\/")))
    out = project / "renders" / "viewer.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(page)
    print(f"wrote {out.relative_to(Path.cwd()) if out.is_relative_to(Path.cwd()) else out} "
          f"({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python tools/make_viewer.py projects/<name>")
    main(sys.argv[1])
