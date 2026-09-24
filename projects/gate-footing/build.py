"""Reproducible build for the gate footing.

    python projects/gate-footing/build.py

source/polycam-2026-09-24.glb
  -> output/gate-footing-scan-clean.stl   cleaned scan (wavy, but true to the object)
  -> output/gate-footing.step             idealised CAD model (open in Fusion)
  -> output/gate-footing.stl              idealised model, print-ready mesh
  -> output/report.json                   dimensions, checks, parameters
  -> renders/*.png                        previews + scan-vs-model sections
"""

import json
import sys
from dataclasses import asdict, replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / "tools"), str(HERE)]

import meshkit as mk  # noqa: E402
from build123d import export_step  # noqa: E402
from idealized import FootingParams, build  # noqa: E402
from render import render_sheet  # noqa: E402

SOURCE = HERE / "source" / "polycam-2026-09-24.glb"
OUT = HERE / "output"
RENDERS = HERE / "renders"

# --- Scale -----------------------------------------------------------------
# The photo-mode scan's absolute scale is wrong (it says ~415 mm long, and the
# owner says the real part is much smaller). Enter the tape-measured
# end-to-end length here and everything (scan and model) scales to match.
MEASURED_LENGTH_X_MM = 100.0  # owner, tape measure, 2026-09-24

# Any dimension measured directly (in real mm) overrides the scaled value,
# e.g. {"slot_w": 48.0, "height": 102.0}. Field names: see FootingParams.
MEASURED_OVERRIDES: dict = {"slot_w": 15.0}  # owner: "right around 15 mm"

# --- Scan cleanup ------------------------------------------------------------
CUT_HEIGHT_MM = 2.0      # cut the floor away this far above the ground plane
CROP_RADIUS_MM = 400.0   # scan covers ~2 m of patio; keep only near the part
SCAN_SLOT_CENTER_X = -2.5  # slot centre in the cleaned scan (model has it at 0)


def clean_scan():
    raw = mk.load_scan(str(SOURCE))
    leveled = mk.level_to_ground(raw, scan_units_to_mm=1000.0)
    part = mk.cut_above_ground(leveled, CUT_HEIGHT_MM)
    center = part.bounds[:, :2].mean(axis=0)
    shell = mk.cut_above_ground(mk.crop_xy(leveled, center, CROP_RADIUS_MM), CUT_HEIGHT_MM)
    shell = mk.orient_footprint(shell, long_axis="x")
    solid = mk.center_on_bed(mk.cap_bottom(shell, z=0.0))
    solid.apply_translation([-SCAN_SLOT_CENTER_X, 0, 0])
    return solid, leveled, center


def main():
    OUT.mkdir(exist_ok=True)
    RENDERS.mkdir(exist_ok=True)

    # The CAD model is always built at the reference (scan) scale, where the
    # fillets are large enough for OpenCASCADE to build and tessellate cleanly
    # (at 100 mm long the tiny fillets tessellate into self-intersections).
    # Real measurements are converted to reference units, then the finished
    # solid is scaled uniformly by k, which preserves the geometry exactly.
    ref = FootingParams()
    k = MEASURED_LENGTH_X_MM / ref.length if MEASURED_LENGTH_X_MM else 1.0
    ref = replace(ref, **{name: mm / k for name, mm in MEASURED_OVERRIDES.items()})
    params = replace(ref.scaled(k), **MEASURED_OVERRIDES)  # real mm, for the report

    scan, leveled, center = clean_scan()
    scan.apply_scale(k)
    scan_info = mk.report(scan)
    assert scan_info["watertight"], "cleaned scan is not watertight"
    scan.export(OUT / "gate-footing-scan-clean.stl")

    part_ref = build(ref)
    export_step(part_ref.scale(k), str(OUT / "gate-footing.step"))
    model = mk.cad_to_mesh(part_ref)
    model.apply_scale(k)
    model_info = mk.report(model)
    assert model_info["watertight"], "idealised mesh is not watertight"
    model.export(OUT / "gate-footing.stl")

    dev = mk.trimesh.proximity.closest_point(model, scan.vertices[::2])[1]
    report = {
        "scale_factor": k,
        "scale_status": "measured" if MEASURED_LENGTH_X_MM else "SCAN SCALE - NOT REAL SIZE",
        "idealized": model_info,
        "scan_clean": scan_info,
        "scan_to_model_deviation_mm": {"mean": round(float(dev.mean()), 2),
                                       "p90": round(float(mk.np.percentile(dev, 90)), 2),
                                       "max": round(float(dev.max()), 2)},
        "params_mm": asdict(params),
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("scale_status", "scan_to_model_deviation_mm")}, indent=2))

    E = model.extents
    sec_y = [round(f * E[1]) for f in (-0.3, 0.0, 0.47)]
    sec_x = [round(f * E[0]) for f in (-0.36, -0.14, 0.0, 0.14)]
    render_sheet([model, scan], str(RENDERS / "idealized.png"),
                 title="gate-footing: idealised CAD model (black) vs cleaned scan (red)",
                 labels=["idealised model", "cleaned scan"], sections_y=sec_y, sections_x=sec_x)
    render_sheet(scan, str(RENDERS / "scan-clean.png"),
                 title="gate-footing: cleaned scan (watertight, levelled, Z-up, mm)",
                 labels=["cleaned scan"], sections_y=sec_y, sections_x=sec_x)
    context = mk.crop_xy(leveled, center, 1200.0)
    render_sheet(context, str(RENDERS / "raw-scan-context.png"),
                 title="gate-footing: raw Polycam scan, levelled (ground + surroundings)",
                 labels=["raw scan (scan scale)"], sections_y=(round(center[1]),), sections_x=())


if __name__ == "__main__":
    main()
