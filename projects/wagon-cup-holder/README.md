# Wagon cup holder

A cup holder that clamps onto the **right-hand side rail** of the owner's
[MAC Sports push/pull wagon](https://macsports.com/products/mac-sports-push-pull-wagon)
(the push-handle frame, as seen from the pusher) and holds a **20 oz Yeti Rambler** hanging off the
outside of the wagon.

![holder in print orientation](renders/cup-holder.png)

## Goal

A snap-on, bolt-tightened clip on the side rail, with a pocket that holds a 20 oz Yeti tumbler upright,
hanging off the side of the wagon (the owner's idea: "hanging off to the side of the wagon", and hanging
lower rather than level with the rail).

## Status

- [x] Reference photos saved (`source/`): the product photo and six photos of the push frame with a tape measure
- [x] Tube measured by the owner: round, **22.3 mm** diameter, **~120 mm** free length
- [x] Parametric CAD model (`model.py`), STEP + STL, watertight, 0 self-intersections, no supports
- [x] Fits the A1 in one piece (130 × 87 × 88 mm), checked for collisions against the rail and tumbler
- [ ] **Owner: confirm this is the right spot.** The clip goes on the **straight section of the right-hand side
      rail**, with the cup outside it. See "What I read from the photos"
- [ ] **Owner: measure the actual tumbler** (base and widest diameter). The pocket uses retailer figures
- [ ] **Owner: what's near the clip spot?** The red latch, the diagonal flat strut, and the end cap
      (see Open questions)
- [ ] **Print the clip-only test slice first** (`output/wagon-cup-clip-test.stl`, 15 mm, a few minutes)
      to check the snap fit and the bolt clamp on the real tube
- [ ] Print the full holder in PETG, test on the wagon with a full cup, adjust

## What I read from the photos (2026-11-01)

The push frame is a **U-shaped tube**: a foam-covered grip bar across the back (only ~9 in, ~230 mm, between its
end brackets, mostly foam), and at each end a round powder-coated tube bends 90° into a **side rail** that runs
toward the wagon. Each side rail has a black end cap and a red latch, and there's a diagonal flat strut below it.
With the tape, the **right-hand side rail's straight run is roughly 8–9 in (200–230 mm)**, and the owner's "~120 mm free"
fits the stretch between the end cap and the red latch. The outside of the rail is open air. This is the
"hanging off the side" spot, so the model is built for it.

**Assumptions to confirm:** the side rail is the same 22.3 mm round tube the owner measured; the clip
can sit on the free ~120 mm; and nothing outboard of the rail (latch, strut) is in the way of the web.
These are the open questions below, not measurements.

## Measurements

| Feature | Real (mm) | Source | Notes |
|---|---|---|---|
| Tube outer diameter | **22.3** | owner, "about" | Calipers on a painted tube read ±0.2. Re-measure if the clip is loose or tight. Assumed the same on the side rail |
| Free rail length (right side) | **~120** | owner, "roughly" | Clip is 70 mm long |
| Side rail straight run | ~200–230 | tape photos (rough read) | End cap to the bend. The latch is near the bend |
| Grip bar between end brackets | ~230 | tape photos (rough read) | Mostly foam. Not used |
| Tumbler base diameter | 70 (2.75 in) | retailer listing | **Not measured on the owner's cup** |
| Tumbler widest diameter (lid) | 89 (3.5 in) | retailer listing | **Not measured on the owner's cup** |
| Tumbler height | 168–175 (6.6–6.9 in) | retailer listings | Only used to size the taper |

Retailer sources: [Rogue](https://www.roguefitness.com/yeti-rambler-20oz-tumbler),
[Rogue Canada](https://www.roguecanada.ca/yeti-rambler-20oz-stainless-limited-edition).
Enter measured tumbler values in `CUP_OVERRIDES` in `build.py`.

## Design decisions and why

- **Layout (use frame):** the clip wraps the side rail from above, mouth facing down. A **shelf** runs outward
  from the top of the clip, a vertical **web** drops down the outside of the rail, and the **floor plate and pocket** hang
  off the web. The cup axis is **67.8 mm outboard of the rail axis**, and the **cup base is 60 mm below the rail axis**,
  so the pocket rim is 20 mm above it and the rest of the tumbler rises beside the frame.
- **The clamp bolt is essential, not optional.** The cup is beside the rail, so a full cup (~1 kg) is a constant twist
  of about **0.67 N·m** on the clip. A snap-fit's friction at rest is ~0.1 N·m (the lips just touch the tube with no preload).
  So the clip has **two ears and an M4 bolt across the mouth**. Tightening it pulls the C closed around the tube
  (roughly belt-like, so ~4× the bolt force presses on the tube, enough for ~1.5+ N·m even at modest tightness). That's
  a rough estimate, so **verify with the test slice** (try to twist the tightened slice on the real rail by hand).
  *Hardware: 1 × M4 × 35 socket-head screw + 1 × M4 nut.*
- **Bolt access:** the nut slides into a slot from the bottom of the inboard ear (no tool needed to hold it). The screw
  head sits in a pocket on the outboard ear, reached with a hex key **through a 12 mm window in the web, from inside the
  empty pocket**. So tighten the bolt **before** you put the cup in.
- **Snap geometry:** the mouth is 20.7 mm wide against the 22.3 mm tube, so each arm spreads ~0.8 mm
  (≈1% strain at the 2.8 mm wall, fine for PETG). Estimated push-on force is ~5–10 kgf, so
  **test with the clip slice**. If it's too stiff, raise `mouth_width` or lower `clip_wall`. If it's loose, do the reverse.
- **Pocket:** a tapered cone (matches the Yeti's taper) 80 mm deep, with 1 mm radial clearance, wrapping the
  cup 250° so it can't slide out sideways. It's open on one side so it prints without supports.
- **Printed on its side:** the clip's bore axis is vertical on the bed. The ring's layers then run around the
  circle, so the arms flex along the layers. Shelf, web and floor are all prisms extruded along the build axis,
  so they stand on the bed with no overhangs. The pocket lies on a 45° teardrop foot. No supports. The only steep
  faces are small (~4 mm) bridges over the bolt, nut and window openings.
- **Material:** PETG (outdoor, sun, flexing clip). PLA creeps and softens in a hot car or in the sun, and
  ASA/ABS warp on the open-frame A1.
- **Earlier design (superseded):** the first version had the cup standing directly on top of the bar. The owner
  wanted it hanging off the side, and the photos showed the side rail is the place for that. That version is in git history.

## Print settings (suggested, not yet test-printed)

- PETG, 0.2 mm layers, 4–5 walls, 15–20 % gyroid infill, brim on (the web is 88 mm tall and only 6.5 mm thick).
- Orientation is already built into the STL: clip bore vertical, pocket on its side. Don't re-orient it.
- Volume 184 cm³ solid. Expect roughly 80–100 g with those settings.
- If the clip arms crack when snapping, print the clip slice with more walls and a lower mouth interference first.

## Open questions

1. **The red latch and the diagonal strut.** Where exactly are they relative to the free 120 mm? The web is a plate
   88 mm long (along the rail) that sits ~24–30 mm out from the rail axis and drops 60+ mm. If the latch or
   strut is outboard of the rail there, the holder will hit it. A photo of the right rail from outside and below, with a ruler, would settle it.
2. **Is the side rail really 22.3 mm?** The measurement was of "the bar". If the rail differs, set `bar_d` in `build.py`.
3. **Which way should the cup open?** The pocket's side opening faces along the rail (toward the end cap in the current
   layout). Mirror or flip if you'd rather it faced the pusher.
4. Does the owner's tumbler have a handle? (The pocket assumes the plain Rambler.)
5. Would a rubber strip or inner-tube liner on the rail be wanted for extra grip? (Easy to add.)
6. The wagon folds. Does the holder need to come off to fold it? (It does: undo the bolt, pull it off.)

## Pipeline

`python projects/wagon-cup-holder/build.py` (~1 min):
1. `model.py` (build123d): clip ring + ears → shelf + web + floor plate + teardrop pocket (cone cavity, side
   opening) → cut bore, mouth, bolt hole, head pocket, nut slot, hex-key window. Built in the **print frame**
   (rail axis = Z, cup axis = Y), so no rotation is needed.
2. `build.py` centres it, exports STEP + STL, and builds the 15 mm clip test slice.
3. Checks: watertight, 0 self-intersections, interference with a ghost rail and a ghost tumbler (both must be 0),
   overhang area (with a 1° tolerance so the 45° foot isn't miscounted). Writes `output/report.json` and the renders.

Key parameters (`CupHolderParams` in `model.py`): `bar_d`, `bar_clearance`, `clip_wall`, `clip_len`,
`mouth_width`, `web_gap`, `floor_drop`, `cup_base_d`, `cup_top_d`, `pocket_depth`, `pocket_clearance`, `wrap_deg`.
The pocket rim must stay above the shelf (`floor_drop` ≤ ~62 with the default 80 mm pocket), or the cup bulges into the shelf.

## Files

- **Interactive viewer:** https://claude.ai/artifact/Anqg9yywWNz2pW6LNgwWoN (private to the owner).
  Built from `renders/viewer.html` by `tools/make_viewer.py` using `review.json`. Republish to this
  URL on every review (see `docs/review.md`)
- `source/wagon-photo-2026-11-01.jpg`: the owner's first photo (product shot, arrow marks the bar)
- `source/wagon-photo-2026-11-01-rail-1..6.jpg`: the owner's photos of the push frame, with tape measure
- `model.py`: parametric CAD. `build.py`: pipeline
- `output/wagon-cup-holder.step`: editable solid for Fusion (print orientation)
- `output/wagon-cup-holder.stl`: print-ready holder
- `output/wagon-cup-clip-test.stl`: 15 mm clip-only slice for the fit test
- `output/report.json`: dimensions, checks, parameters
- `renders/cup-holder.png`, `renders/sections.png`, `renders/in-use.png`: previews and sections
- `renders/ref-bar.stl`, `renders/ref-tumbler.stl`: ghost rail and tumbler for the viewer

## Log

- **2026-11-01:** Project started. The wagon page gives no tube sizes, so I asked the owner. They pointed to the round
  push bar at the top of the frame (photo) and measured it: 22.3 mm round, ~120 mm free, wants it on the
  pusher's right. Tumbler sizes are from retailer listings (not measured). Built the parametric model: snap C-clip
  + M4 clamp bolt + floor plate + tapered pocket, with the cup standing over the bar. Found while checking the
  physics that a snap-fit alone has ~10× too little grip against rotating around the bar, so I added the
  clamp ears and bolt. Watertight, 0 self-intersections, no collisions, no supports. Committed on branch `wagon-cup-holder`.
- **2026-11-01 (v2):** The owner said they imagined it **hanging off the side of the wagon**, and chose "past the
  right end, hanging lower". They sent six photos with a tape measure. They show the push frame is a U-shaped tube
  with side rails, and the right side rail is the spot. Redesigned: clip on the side rail, shelf + web carrying a
  pocket **67.8 mm outboard** with the cup base **60 mm below the rail**, a hex-key window through the web for the bolt,
  and the nut on a slide-in slot. The cup twist on the clip is now constant (~0.67 N·m), so the bolt clamp is
  essential. Watertight, 0 self-intersections, no collisions with the rail or tumbler, no supports, 130 × 87 × 88 mm.
  Next: owner confirms the spot, checks the latch/strut clearance, measures the tumbler, and prints the clip slice.
