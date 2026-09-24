# Gate footing

A plastic foot that holds up a metal gate. It's a rectangular base slab with
two raised uprights running front to back, and a slot between them where the gate sits.

![idealised model vs scan](renders/idealized.png)

## Goal

A clean, smooth, accurate, printable model of the footing. The real part has smooth
sides and edges, and the scan is wavy, so the deliverable is an **idealised
parametric CAD model** fitted to the scan, not a smoothed scan.
*(Owner to confirm the end use: print a replacement? exact replica or improved?)*

## Status

- [x] Polycam scan imported (`source/polycam-2026-09-24.glb`)
- [x] Scan cleaned: floor removed, levelled, squared up, flat base, watertight
- [x] **Idealised CAD model** (`idealized.py`, build123d): flat faces, flat parallel
      slot walls, straight drafts, true fillets, mirror-symmetric. Exported as
      STEP (Fusion) and STL (Bambu Studio). Mean deviation from the scan is 0.6 mm at real size
      (2.5 mm at scan scale), mostly where the scan is wavy.
- [x] **Real size:** 100 mm long (the owner's measurement) with the slot modelled at 15.4 mm (caliper 15.1 mm + print clearance). Output is 100 × 59.8 × 39.8 mm and
      fits the A1 in one piece.
- [ ] Check the width (59.8), height (39.8) and base thickness (12.0) against the real part.
      These are scaled from the scan, not measured.
- [ ] Underside: solid, hollow, or ribbed? (not captured)
- [ ] Choose the material and orientation, then test print (scale down first to check the fit?)

## Measurements

**Real (owner, 2026-09-24):** longest dimension **100 mm**. Slot **15.1 mm** (caliper). The first estimate was "right around 15".
Both are set in `build.py` (`MEASURED_LENGTH_X_MM`, `MEASURED_OVERRIDES`). The two agree:
scaling the scan to 100 mm makes the slot 15.9 mm, which confirms the scan's proportions.

`FootingParams` in `idealized.py` holds the values at scan scale. Real = scan × k, where k = 100 / 415 = 0.241.
Only **measured** values were measured directly. Everything else is scaled from the scan.

| Parameter | Scan scale (mm) | Real (mm) | Source |
|---|---|---|---|
| `length`: end wall to end wall (X) | 415 | **100.0** | measured |
| `width`: along the slot (Y) | 248 | 59.8 | scaled |
| `height`: top of the uprights | 165 | 39.8 | scaled |
| `base_h`: base slab thickness | 50 | 12.0 | scaled |
| `slot_w`: gap between the uprights | 66 | **15.4** | measured 15.1 + 0.3 print clearance |
| `slot_floor`: slot floor height | 45 | 10.8 | scaled |
| `upright_outer_x`: outer face at base top, from centre | 100 | 24.1 | scaled |
| `upright_draft_deg`: outer face lean | 15° | 15° | scan |
| `footprint_corner_r` | 55 | 13.3 | scaled |
| `upright_fillet_r` (upright to base) | 28 | 6.7 | scaled |
| `upright_end_r` (top corners at the Y ends) | 60 | 14.5 | scaled |
| `upright_top_outer_r` / `upright_top_inner_r` | 15 / 6 | 3.6 / 1.4 | scaled |
| `base_edge_r` / `slot_floor_r` | 8 / 8 | 1.9 / 1.9 | scaled |

## Modelling decisions (idealised model)

- **The slot walls are flat, parallel, and vertical** (as the owner described). The scan's
  slot interior is its noisiest area (the camera can't see into it), and it read as 60–75 mm
  wide at scan scale depending on height. The model uses the owner's caliper reading of 15.1 mm plus
  0.3 mm clearance, so **15.4 mm**.
- The upright *outer* faces have a 15° draft. That's consistent across the scan
  (x = 92 → 76 mm over z = 80 → 140).
- The part is mirror-symmetric about the slot centre. The scan's slot centre was 2.5 mm off,
  and the cleaned scan is shifted to match.
- The upright top edges are flat and rounded. The scan's top is slightly crowned (≤3 mm),
  which is treated as noise.
- Solid underneath. The real underside is unknown. For printing, use infill or
  hollow it later.

## Printing notes

- 100 × 59.8 × 39.8 mm, so it easily fits the A1 in one piece. Print it **base down with no supports**:
  the drafts, fillets and rounded upright ends are all self-supporting.
- Solid volume is 110 cm³. With 4–5 walls and 20–30 % gyroid infill, expect roughly 50–70 g.
- Outdoors under load: **PETG**.
- The slot is modelled at 15.4 mm so that it prints at about the real 15.1 mm (printed slots usually come out
  ~0.2–0.3 mm narrow). If the test print is too tight or too loose, adjust `slot_w` in `MEASURED_OVERRIDES`
  and rebuild.

## Pipeline

`python projects/gate-footing/build.py` (about 1.5 min):
1. **Scan cleanup** (`tools/meshkit.py`): merge seam vertices → RANSAC ground plane,
   level to Z=0 (mm, Z-up) → keep the largest piece above 2 mm → crop to a 400 mm radius →
   square the footprint → drop the cut edge to Z=0 and cap → watertight.
2. **Idealised model** (`idealized.py`, build123d/OpenCASCADE): base box → drafted
   upright block → slot cut → fillets. The model is **always built at scan scale**, with
   measured overrides converted to that scale, and then the finished solid is scaled by k.
   At 100 mm the small fillets tessellated into self-intersections, and a uniform scale of the
   finished solid is exact. Exported as STEP. Tessellated and repaired to STL
   (`meshkit.cad_to_mesh`).
3. Scale the scan by the same k, write `report.json` (checks and scan-to-model
   deviation), and render the PNGs.

## Files

- **Interactive viewer:** https://claude.ai/artifact/99u6vaQgsGqaAUmchUXR9R
  (private to the owner). Built from `renders/viewer.html` by `tools/make_viewer.py` using
  `review.json`. Republish to this URL on every review (see `docs/review.md`).
- `source/polycam-2026-09-24.glb`: raw Polycam export (≈2 m of ground around the part)
- `output/gate-footing.step`: **idealised model for Fusion** (editable solid)
- `output/gate-footing.stl`: idealised model for Bambu Studio
- `output/gate-footing-scan-clean.stl`: cleaned but wavy scan, useful as a reference body in Fusion
- `output/report.json`: dimensions, watertight/self-intersection checks, deviation, params
- `renders/idealized.png`: model vs scan, views and cross-sections
- `renders/scan-clean.png`, `renders/raw-scan-context.png`

## Log

- **2026-09-24:** Repo set up. Scan cleaned into a watertight solid. The owner flagged that the size
  is wrong: the scan has no floor left, so the photo-mode scan scale is at fault. Waiting on
  measurements. The owner asked for smooth sides and flat faces, so I built the idealised
  parametric CAD model (build123d), which is symmetric with flat slot walls and real fillets, exported
  as STEP and STL. Watertight, 0 self-intersections.
- **2026-09-24:** First review with the interactive 3D viewer (link above). The owner was happy with
  the idealised shape. The review process is now documented (`docs/review.md`, `/model-review`).
  Next: real measurements for scale.
- **2026-09-24:** Owner measured a 100 mm length and a ~15 mm slot. These agree with the scan's
  proportions (15.9 mm predicted). I rebuilt at real size: 100 × 59.8 × 39.8 mm, watertight, 0
  self-intersections, 0.6 mm mean deviation from the scan, fits the A1. Fixed two scale problems: the base-edge
  selection threshold is now relative to the model's size, and the CAD is built at reference scale and then
  scaled (building directly at 100 mm gave 54 self-intersecting triangles). The viewer now frames the
  part rather than the whole build volume. Next: the owner checks the remaining dimensions, then a test print.
- **2026-09-24:** Owner's caliper reads the slot at ~15.1 mm, and they asked to widen it. Set `slot_w` to 15.4
  (15.1 + 0.3 mm print clearance). Rebuilt: watertight, 0 self-intersections, slot 15.4 mm at every height.
  Next: test print and check the gate fit.
