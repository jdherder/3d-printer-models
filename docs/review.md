# Model review process

Use this to review a model with the owner after any meaningful change (first
cleanup, idealised rebuild, new measurements, a fix after a test print). It
pairs the agent's automated checks with an **interactive 3D page** the owner
can spin around on any device.

In a Claude session, run **`/model-review <project>`** (skill:
`.claude/skills/model-review/`). It runs every step below.

## 1. Rebuild from source

```bash
python projects/<name>/build.py
```

Outputs are always regenerated, never hand-edited. The build must finish
without assertion failures.

## 2. Automated checks (agent)

Read `projects/<name>/output/report.json` and confirm:

| Check | Pass |
|---|---|
| `watertight`, `winding_consistent` | `true` |
| `self_intersecting_faces` | `0` |
| `euler_number` | `2` for a single solid with no through-holes (each through-hole subtracts 2) |
| `scale_status` | Measured. If it's still scan scale, **say so plainly**, because the size is not real |
| `fits_A1_as_is` / `fits_A1_any_axis_order` | If false, the part needs splitting or scaling |
| `scan_to_model_deviation_mm` (idealised models) | Mean within a few mm. Look at *where* the large deviations are |

For any other mesh: `python tools/inspect_mesh.py <file>`.

## 3. Visual check (agent)

Read the PNGs in `projects/<name>/renders/` (the agent can't open a 3D viewer,
but it can look at images):
- Shaded views: does the shape look right, and are there artefacts (spikes, holes, a leftover floor)?
- Cross-sections, model (black) vs scan (red): the model should sit on the scan's
  average surface. A consistent offset in one place is a modelling error, not
  scan noise.

Fix anything found before involving the owner.

## 4. Interactive review page

```bash
python tools/make_viewer.py projects/<name>
```

This reads `projects/<name>/review.json` and writes `renders/viewer.html`, a
single self-contained page (~0.5–1 MB) with:
- orbit, zoom, and pan, plus Iso/Front/Side/Top buttons
- a toggle for each mesh (e.g. the idealised model as a solid, the original scan as a wireframe overlay)
- the Bambu A1 256 mm build volume for size context
- a **"preview at real size"** box: type a length and every dimension plus the A1
  fit check updates
- a notes panel (what changed, what to look at)

`review.json` fields are documented at the top of `tools/make_viewer.py`.
Dimensions can point at model parameters (`"param": "slot_w"`), so the page always
matches the last build. Meshes must be under 65k vertices.

**Share it:** in a Claude session, publish `renders/viewer.html` as an Artifact.
Record the artifact URL in the project README (under *Files*). Next time,
publish to that same URL so the owner's link keeps working. Without Claude, open
`viewer.html` in a browser (it needs internet access for three.js).

## 5. Owner review checklist

Ask the owner to look for:
1. **Shape:** does it match the real part? Anything missing, like holes, ribs, or text?
2. **Flat faces and edges:** are faces flat where they should be, and are the edge
   roundings about the right size?
3. **Scan overlay:** toggle the scan on. Where the model and scan disagree, which is right?
4. **Size:** type the measured length into the real-size box. Do the listed
   dimensions (slot width etc.) match their tape measure?
5. **Fit and printing:** does it fit the A1? Any orientation or material concerns?

## 6. Record the outcome

In the project README:
- tick or add items under **Status**
- put new real measurements in **Measurements**, and in `build.py`
  (`MEASURED_LENGTH_X_MM` / `MEASURED_OVERRIDES`)
- add a dated **Log** entry: what was reviewed, the owner's feedback, and what changes next
