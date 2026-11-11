# Bike hook (vertical, on a 2x4)

A wall hook that hangs a bike vertically by its front rim, as if the bike were riding up the wall. It screws to a
horizontal 2x4 that is fastened to the studs. Printed in PETG.

![on the 2x4 with a 700c wheel](renders/in-use.png)

## Goal

A hook that is clearly strong enough for an everyday (non-e) bike hung off the ground, prints without supports on the
A1, and installs with ordinary wood screws.

## Status

- [x] Concept + parametric model (`model.py`, build123d), v1 (2026-11-11)
- [x] Strength estimate, screw access check, and a 700c wheel + spokes hung on it (`report.json`)
- [ ] Owner's numbers: bike weight, wheel/tire size, spoke count, how the 2x4 is mounted (see Open questions)
- [x] Viewer published (2026-11-11)
- [ ] Owner review of the viewer
- [ ] Test print, hang the bike, check after a few weeks for any sag

## How it works

One constant-width (32 mm) part, seen from the side:

- **Lip** over the top of the 2x4. The bike's weight bears straight down through it into the board, so the screws
  don't carry the weight.
- **Plate** down the 2x4's front face. The hook tries to tip forward about the plate's bottom edge, which bears on the board.
- **Two vertical screws through the lip** into the 2x4's top edge stop the top pulling away. They're loaded sideways
  (shear), the strong way for wood screws, with a 89 mm lever. You drive them from above, so the arm is never in the way.
- **One horizontal screw** low in the plate stops it lifting or swinging.
- **Arm** tapers from 54 mm deep at the plate. Its top slopes down 5° so the rim slides out against the **tip**, which
  rises 35 mm. To come off, the rim has to lift about 31 mm.

You hang the bike the way you would on a steel J-hook: lift it by the saddle, turn the front wheel, and hook the rim with
the tip between two spokes. The wheel has to be turned for any wall J-hook, because the arm can only get inside the rim
by passing through the spokes at an angle.

**Print orientation is what makes it strong.** It prints lying on its side, so every layer is a full copy of the side profile.
The bending from the bike runs along the extruded lines and never pulls layers apart. Printed standing up, the same part
would be several times weaker.

## Strength (v1 estimate, `report.json` → `strength`)

Assumes a **16 kg bike** (not measured yet) and ×3 for the jolt of hanging it or knocking it.

| Check | Value |
|---|---|
| Worst arm stress, bike just hanging | 0.8 MPa (8 MPa is the creep limit used for "holds for years without sagging") |
| Same, with the ×3 jolt | 2.4 MPa vs ~30 MPa for printed PETG along the layers → **safety factor ~12** |
| Each lip screw, sideways load | ~90 N hanging, ~260 N with the jolt (a #10 in a 2x4 is good for ~400 N design, much more ultimate) |

The plastic has a big margin. The weak links are the screws in the 2x4 and the 2x4's own fastening to the studs, and both
are easy to make strong (see Install). Don't use it for an **e-bike** (25+ kg) without redoing the numbers.

## Measurements

Nothing measured yet. These are the assumptions, and all of them are parameters:

| Feature | Assumed (mm) | Source | Notes |
|---|---|---|---|
| 2x4 | 38.1 × 88.9 (1.5 × 3.5 in) | nominal | Flat on the wall, wide face out. The lip reaches 30 of the 38 mm back |
| Bike weight | 16 kg | typical | `BIKE_MASS_KG` in `build.py` |
| Wheel | 700c, rim bed radius 300, 32 mm tire, 32 spokes | typical | `WHEEL` in `build.py` |
| Hook width (passes between spokes) | 32 | design | Best spoke gap 9.5 mm per side on a 32-spoke wheel; you pick the gap as you hook it |
| Reach | 100 from the 2x4 face, 138 from the wall | design | |

## Print settings

- **PETG**, lying on its side (as in the STL), **no supports**, 0.2 mm layers. The whole side face is on the bed, so no brim is needed.
- **5–6 walls, 30–40 % gyroid infill.** Strength is in the walls. About 110–130 g.
- The screw holes print sideways, so they have a teardrop point on top (no sagging bridge). If a hole is tight, run a 3/16 in drill through it.

## Install

1. 2x4 flat on the wall, level, at the height that puts the front wheel where you want it. The rim seat is about 2 mm
   above the 2x4's top. Fasten it to **every stud it crosses**, with two 3 in structural or construction screws per stud.
2. Seat the hook's lip on top of the 2x4 and push the plate flat against its face.
3. Two **#10 × 2 in** washer-head (cabinet) or pan-head wood screws down through the lip, with 1/8 in pilot holes (they're
   only 18 mm apart along the grain, so pilot holes prevent splitting). One more through the plate's bottom hole.
4. If you have carbon rims or want to protect the finish, glue a strip of old inner tube on the arm top.

## Open questions

- **Bike:** weight, and is any of them an e-bike? Road, gravel or MTB?
- **Wheel:** size (700c / 29 / 27.5 / 26), tire width, spoke count. A wide MTB tire may need more reach or a taller tip;
  fewer spokes leave more room for the arm.
- **The 2x4:** flat on the wall (wide face out), as assumed, or on edge? Is it already up, and how high?
- **Wall clearance:** hanging straight from the hook, the 700c wheel misses the 2x4 only when turned 80° or more. In practice
  the tire just rests against the 2x4, which is normal for vertical hooks. If the owner would rather it hang free with less
  turn, the reach can grow (stress is tiny, so there's room).

## Pipeline

`build.py`: builds the hook (`model.py`), lays it on its side (`print_pose`) and exports STEP + STL. Then it:
- runs the beam estimate on real cross-sections of the mesh (`strength`)
- checks a screwdriver can reach each hole straight on (`screw_access`)
- hangs a modelled wheel (rim + tire + spokes) on the arm, slides it down the slope until it stops, and rotates it to
  find the best and worst spoke gap (`wheel_fit`). It also finds the smallest wheel turn that clears the 2x4 and wall.

Hook parameters are in `HookParams` (`model.py`). Bike/wheel assumptions are at the top of `build.py`.

## Files

- `output/bike-hook.stl`: print this (Bambu Studio)
- `output/bike-hook.step`: editable solid for Fusion
- `output/report.json`: checks, params, strength, screw loads, wheel fit
- `renders/model.png`: print pose views; `renders/in-use.png`: on the 2x4 with a wheel; `renders/side-section.png`: zoomed side section
- **Viewer artifact:** https://claude.ai/artifact/J58YQJDJZxmdjDr6LM3aJt (publish updates to this URL)

## Log

- **2026-11-11:** Project started from the owner's brief: PETG, hang the bike vertically by the front wheel at about head
  height, screwed to a horizontal 2x4 on the studs. v1: lip over the 2x4 plus a plate on its face, lip screws in shear, tapered
  arm with a 35 mm tip. Prints on its side with no supports. Estimated safety factor ~12 on the plastic for a 16 kg bike with
  a ×3 jolt. Built a 700c wheel check: the arm fits between spokes with 9.5 mm to spare. Waiting on the owner's bike and wheel numbers.
