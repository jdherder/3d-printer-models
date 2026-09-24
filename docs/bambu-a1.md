# Bambu Lab A1 notes

- **Build volume:** 256 × 256 × 256 mm. Parts bigger than that get split, with
  alignment pins or dovetails, or scaled down.
- **Kinematics:** bed-slinger (the Y axis moves the bed). Tall, narrow parts wobble,
  so orient long axes along X where possible, or add a brim.
- **Enclosure:** none. ASA and ABS warp and crack, so avoid them. PLA and PETG are
  the everyday materials, and TPU works for flexible parts.
- **Nozzle:** 0.4 mm stock (hardened 0.4 / 0.2 / 0.6 / 0.8 swaps available).
- **AMS lite:** multi-colour is possible, but assume single material unless told otherwise.
- **Slicer:** Bambu Studio. STL is fine. 3MF keeps plate and settings. STEP imports
  as solids.

## Material guidance

| Use | Material | Notes |
|---|---|---|
| Indoor, decorative, jigs | PLA | Easiest. Softens around 55 °C and creeps under constant load |
| Outdoor, sun, load-bearing | **PETG** | UV/heat tolerant enough, tougher. Dry the filament first |
| Flexible feet, bumpers | TPU 95A | Print slowly, no AMS |

## Design rules of thumb (0.4 mm nozzle)

- Walls: at least 1.2 mm (3 perimeters). Structural parts: 4–6 perimeters plus 15–30 % gyroid infill.
- Overhangs up to ~45° without supports. Bridges up to ~30 mm are fine.
- Clearance for press or slip fits between printed parts: 0.2–0.3 mm per side.
- Holes print slightly undersize, so add ~0.2 mm, or drill or ream them.
- Put the flat, largest face on the bed. Lay out layer lines so loads don't split
  them apart (layers are weakest in Z).
