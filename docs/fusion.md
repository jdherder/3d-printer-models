# Autodesk Fusion workflow

## Opening an idealised model (preferred)

When a project has `output/<name>.step`, use **File → Open** (or Insert → Insert
into Current Design). It arrives as a real solid body with fillets, ready to edit
with Press Pull, Fillet, and so on. The parameters live in the project's `idealized.py`.
Tell the agent about any changes so it can mirror them (or export your edited
STEP into `fusion/`).

## Bringing a cleaned scan into Fusion

1. **Insert → Insert Mesh** and pick `projects/<name>/output/*-clean.stl`.
   Set the units to **millimetres**. The mesh is already Z-up with its base on Z=0.
   (Fusion's default is Y-up. If the model lies on its side, go to Preferences →
   General → Default modeling orientation → **Z up**, or rotate it on insert.)
2. Use it as a **reference body**. The best results usually come from sketching
   on top of the mesh:
   - Mesh workspace → **Create Mesh Section Sketch** at a few heights and planes.
   - Trace the profiles with lines, arcs, and fillets, then extrude or revolve
     a clean solid.
3. Or convert it directly (only good for simple, low-poly meshes):
   Mesh → **Modify → Convert Mesh** (Prismatic or Faceted). Big scans convert
   slowly and give a faceted body that's awkward to edit.

## Handing work back to the repo

Put Fusion outputs in `projects/<name>/fusion/`:
- `*.step`: the solid, for re-import or the slicer (Bambu Studio opens STEP)
- `*.stl` or `*.3mf`: the mesh for printing
- A note in the project README with the key parameters (user parameters in
  Fusion, like slot width and wall thickness), so agents can reason about them.

Export tips: File → Export → STEP. For printing, right-click the body →
**Save As Mesh**, choose 3MF or STL, and set the refinement to High.
