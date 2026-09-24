---
name: model-review
description: Review a 3D model project with the owner. Rebuild it, run printability checks, inspect the renders, generate the interactive 3D viewer page, publish it as an Artifact, and record the outcome. Use when the owner asks to review, visualise, show, or check a model in projects/<name>/, or after a meaningful model change.
---

# Model review

Argument: a project name or path (e.g. `gate-footing`). If none is given and
only one project exists besides `_template`, use it. Otherwise ask.

Follow `docs/review.md`. In short:

1. **Context:** read `projects/<name>/README.md` (status, measurements, and any
   recorded viewer artifact URL).
2. **Rebuild:** `python projects/<name>/build.py`. If it fails, fix the cause first.
3. **Checks:** read `output/report.json`. Confirm it's watertight, has 0 self-intersections,
   and has Euler number 2 (unless there are through-holes). Check the scale status, A1 fit, and scan
   deviation. Note any failure. Don't hide it.
4. **Look:** Read the PNGs in `renders/`. Check the shape and the model-vs-scan sections.
   Fix obvious problems before showing the owner.
5. **Viewer:** if `review.json` is missing, create it (see the docstring in
   `tools/make_viewer.py` and `projects/gate-footing/review.json`). Keep the `notes`
   current: what changed since the last review and what the owner should check.
   Then run `python tools/make_viewer.py projects/<name>`.
6. **Publish:** publish `projects/<name>/renders/viewer.html` with the Artifact tool.
   If the README records a viewer URL, pass it as `url` to update that artifact in
   place. Otherwise publish new (icon `cube`) and add the URL to the README's *Files*
   section. Also send the main render PNG (`renders/idealized.png` or
   `renders/scan-clean.png`) with SendUserFile as a quick still view.
7. **Report** to the owner, briefly: the link, the check results (especially if it's still
   at scan scale or doesn't fit the A1), and the owner checklist from `docs/review.md` §5.
8. **Record:** add a dated Log entry to the project README. Commit and push
   (`renders/viewer.html` included).
