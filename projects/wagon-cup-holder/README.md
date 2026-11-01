# Wagon cup holder

A two-piece cup holder for the **right-hand side rail** of the owner's
[MAC Sports push/pull wagon](https://macsports.com/products/mac-sports-push-pull-wagon)
(the push-handle frame, as seen from the pusher). A **clip stays on the rail**, and the **cup module lifts on and
off it in a couple of seconds**, so it can come off for folding the wagon. It holds a **20 oz Yeti Rambler**
hanging off the outside of the wagon.

![holder in print orientation](renders/cup-holder.png)

## Goal

A tool-free way to take the cup off and put it back, with the cup hanging off the side of the wagon, lower than
the rail (the owner's requirements: "hanging off to the side of the wagon", "hanging lower", and "needs to go on
and off quickly as it will need to be off for folding").

## Status

- [x] Reference photos saved (`source/`): the product photo and six photos of the push frame with a tape measure
- [x] Tube measured by the owner: round, **22.3 mm** diameter, **~120 mm** free length
- [x] Parametric CAD model (`model.py`): **clip** + **cup module** + two small test pieces. STEP + STL, watertight,
      0 self-intersections, no collisions in the assembled position, no supports
- [x] Fits the A1 (module 112 × 95 × 88 mm, clip 52 × 40 × 70 mm)
- [ ] **Owner: confirm the clip spot** (straight section of the right-hand side rail) and that the **empty clip
      doesn't block folding**. See "Folding" below
- [x] Tumbler: owner is fine with the retailer figures for now (70 mm base, 89 mm widest). Re-check against the real cup before the full print
- [x] Strut + red latch clearance (v3.1): they sit further out than the bar, ~26 mm (owner's estimate), the same at both ends. The cup
      is now moved out to clear them. **Still an estimate: check it against the real wagon before the full print** (Open questions 2)
- [ ] **Print the three small test pieces first** (a few minutes to an hour each): the clamp slice, and the dovetail pair
- [ ] Print the clip and module in PETG, test on the wagon with a full cup, adjust

## How the quick release works

- The **clip** (ring + ears + M4 bolt) is snapped on and **tightened once with a hex key**. It stays on the rail.
  On its outboard side there's a boss with a **vertical 45° dovetail tongue** (34 mm wide at the root, 48 mm at the tip,
  7 mm tall, **32 mm of vertical engagement**).
- The cup **module** has the matching groove (0.35 mm clearance per side). It **drops straight down onto the tongue**
  and rests on the tops of the clip's ears, so **gravity holds it seated**. To remove it, lift it straight up
  ~32 mm and it comes off with the cup in it, one-handed, no tool.
- The module's weight is carried by the ear tops (a vertical stop). The cup's twist (0.82 N·m full) is carried as a
  couple across the 32 mm dovetail height (~20 N), which is small.
- **No detent yet.** To lift off, the module has to move up 32 mm, and a wagon bump is very unlikely to do that. If it
  hops in testing, add a small click detent (bump on the tongue flank + dimple in the groove) or a lanyard.

### Folding

What stays on the rail when the cup is off: the **clip is 70 mm long and extends about 28 mm above the rail axis,
24 mm below it, 22 mm outboard and 18 mm inboard** (the ears and the dovetail boss). **Whether that blocks folding is the
big unknown.** I can't tell from the photos what the rail does when the wagon folds. Cheap check before printing the
whole thing: print the clip (or just the 15 mm clamp slice, which has the ears but not the boss), clamp it on the right
rail where it would go, and fold the wagon. If it gets in the way, move it along the rail, or loosen the bolt and remove
the whole clip (a hex key and ~10 s) when you fold. Don't want the tool? A thumb-screw or wing-nut instead of the nut
is an easy change.

## What I read from the photos (2026-11-01)

The push frame is a **U-shaped tube**: a foam-covered grip bar across the back (only ~9 in, ~230 mm, between its
end brackets, mostly foam), and at each end a round powder-coated tube bends 90° into a **side rail** that runs
toward the wagon. Each side rail has a black end cap and a red latch, and there's a diagonal flat strut below it.
With the tape, the **right-hand side rail's straight run is roughly 8–9 in (200–230 mm)**, and the owner's "~120 mm free"
fits the stretch between the end cap and the red latch. The outside of the rail is open air. This is the
"hanging off the side" spot, so the model is built for it.

**Assumptions to confirm:** the side rail is the same 22.3 mm round tube the owner measured; the clip
can sit on the free ~120 mm; and nothing outboard of the rail (latch, strut) is in the way of the web.

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

- **Layout (use frame):** the clip wraps the side rail from above, mouth facing down. The cup module hangs off its
  outboard side: a block with the dovetail groove, a web down the outside of the rail, and the floor plate and pocket
  off the web. The cup axis is **83.8 mm outboard of the rail axis**, and the **cup base is 60 mm below the rail axis**, so
  the pocket rim is 20 mm above it and the rest of the tumbler rises beside the frame.
- **The clamp bolt is still essential.** The cup is beside the rail, so a full cup (~1 kg) is a constant twist
  of about **0.82 N·m** on the clip. A snap-fit's friction at rest is ~0.1 N·m (the lips just touch the tube with no
  preload). So the clip has **two ears and an M4 bolt across the mouth**. Tightening it pulls the C closed around the
  tube (roughly belt-like, so ~4× the bolt force presses on the tube, enough for ~1.5+ N·m even at modest tightness).
  That's a rough estimate, so **verify with the clamp test slice** (try to twist the tightened slice on the real rail by hand).
  *Hardware: 1 × M4 × 35 socket-head screw + 1 × M4 nut.*
- **Bolt access:** with the module off, the +X ear's outer face is clear. The nut slides into a slot from the bottom of the
  inboard ear. The head sits in a pocket on the outboard ear.
- **Snap geometry:** the mouth is 20.7 mm wide against the 22.3 mm tube, so each arm spreads ~0.8 mm
  (≈1% strain at the 2.8 mm wall, fine for PETG). Estimated push-on force is ~5–10 kgf, so
  **test with the clamp slice**. If it's too stiff, raise `mouth_width` or lower `clip_wall`. If it's loose, do the reverse.
- **Pocket:** a tapered cone (matches the Yeti's taper) 80 mm deep, with 1 mm radial clearance, wrapping the
  cup 250° so it can't slide out sideways. It's open on one side so it prints without supports.
- **Printed on its side:** both pieces are built in a frame where the clip's bore axis is vertical on the bed. The ring's
  layers then run around the circle, so the arms flex along the layers. The dovetail flanks are 45° so they need no
  supports. The pocket lies on a 45° teardrop foot. The module has **no steep faces at all**, and the clip has ~33 mm² of
  small (~4 mm) bridges over the bolt and nut openings.
- **Material:** PETG (outdoor, sun, flexing clip). PLA creeps and softens in a hot car or in the sun, and
  ASA/ABS warp on the open-frame A1.
- **History:** v1 had the cup standing on top of the bar. v2 hung it off the side rail as one piece, with a hex-key
  window through the web so the bolt could be reached. v3 (this) splits it so the cup comes off without a tool. The window
  is gone, since the bolt is reached with the module off. Earlier versions are in git history.

## Print settings (suggested, not yet test-printed)

- PETG, 0.2 mm layers, 4–5 walls, 15–20 % gyroid infill, brim on (the module's web is 88 mm tall and only 6.5 mm thick).
- Orientation is already built into each STL. Don't re-orient them.
- Volumes: module 203 cm³ and clip 47 cm³ solid. Expect roughly 80–100 g and 25–35 g with those settings.
- **Test prints, in order:**
  1. `wagon-cup-clip-test.stl`: 15 mm ring + ears. Snap it on the real rail, add the M4 bolt, and tighten.
     Check the snap force and try to twist it.
  2. `wagon-dovetail-test-tongue.stl` + `wagon-dovetail-test-groove.stl`: print both, slide them together
     (groove block drops onto the tongue from above). Should slide with a light push and not rattle. Adjust
     `dt_clear` (0.35 mm per side now) if it's too tight or sloppy.
  3. The full clip and module.

## Open questions

1. **Does the empty clip block folding?** See "Folding" above. Test with the clamp slice on the rail.
2. **The red latch and the diagonal strut sit further out than the push bar** (owner, from photos). Owner's answers: same at both ends,
   they reach "maybe 26 mm" out (taken as 26 mm past the bar's **outer surface**, i.e. 37.2 mm from the bar axis, the cautious reading),
   and the 120 mm is the clear, unobstructed stretch of bar between them. The module's web now starts **40 mm** from the bar axis
   (2.8 mm clear of that), the module is 88 mm long inside the 120 mm window (16 mm each side), and the clip is centred on it.
   **Still assumed (modelled as two blocks at the ends of the window, shown in the viewer):** the latch/strut only exist
   beyond the 120 mm window, and nothing else is outboard of the bar inside it. The diagonal strut slopes down from the bracket, so please
   check on the real wagon that it doesn't reach under the cup (the cup base is 60 mm below the bar axis). If it does, raise the cup (`floor_drop`).
3. ~~Is the side rail really 22.3 mm?~~ Confirmed by the owner: **22.3 mm** (set as `bar_d`).
4. **Which way should the cup open?** The pocket's side opening faces along the rail. Mirror or flip if you'd rather it faced the pusher.
5. Does the owner's tumbler have a handle? (The pocket assumes the plain Rambler.)
6. Is a click detent wanted, or is gravity enough?
7. Would a rubber strip or inner-tube liner on the rail be wanted for extra grip? (Easy to add.)

## Pipeline

`python projects/wagon-cup-holder/build.py` (~2 min):
1. `model.py` (build123d): `build_clip` = ring + ears + boss + dovetail tongue, cut bore, mouth, bolt hole, head pocket,
   nut slot. `build_module` = floor plate + teardrop pocket (cone cavity, side opening) + web + dovetail block with its groove.
   Built in the **print frame** (rail axis = Z, cup axis = Y), in the assembled position.
2. `build.py` exports each piece (STEP + STL) in its own print pose, plus the three test pieces.
3. Checks: watertight, 0 self-intersections, overhang area (1° tolerance so the 45° faces aren't miscounted), and
   interference of every pair in the assembled position: module/clip, module/rail, module/tumbler, clip/rail,
   clip/tumbler (all must be 0). Writes `output/report.json` and the renders.

Key parameters (`CupHolderParams` in `model.py`): `bar_d`, `bar_clearance`, `clip_wall`, `clip_len`, `mouth_width`,
`dt_clear`, `dt_w_root`, `dt_y1`, `web_gap`, `keepout_reach`, `safe_window`, `floor_drop`, `cup_base_d`, `cup_top_d`, `pocket_depth`, `pocket_clearance`, `wrap_deg`.

## Files

- **Interactive viewer:** https://claude.ai/artifact/Anqg9yywWNz2pW6LNgwWoN (private to the owner).
  Built from `renders/viewer.html` by `tools/make_viewer.py` using `review.json`. Republish to this
  URL on every review (see `docs/review.md`)
- `source/wagon-photo-2026-11-01.jpg`: the owner's first photo (product shot, arrow marks the bar)
- `source/wagon-photo-2026-11-01-rail-1..6.jpg`: the owner's photos of the push frame, with tape measure
- `model.py`: parametric CAD. `build.py`: pipeline
- `output/wagon-cup-clip.step/.stl`: the clip that stays on the rail
- `output/wagon-cup-module.step/.stl`: the cup module that lifts on and off
- `output/wagon-cup-clip-test.stl`: 15 mm ring + ears slice, for the snap and clamp test
- `output/wagon-dovetail-test-tongue.stl`, `output/wagon-dovetail-test-groove.stl`: sliding-fit test pair
- `output/report.json`: dimensions, checks, parameters
- `renders/cup-holder.png`, `renders/sections.png`, `renders/in-use.png`: previews and sections
- `renders/asm-clip.stl`, `renders/asm-module.stl`, `renders/ref-bar.stl`, `renders/ref-tumbler.stl`:
  assembled-position meshes and the ghost rail and tumbler for the viewer

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
  essential.
- **2026-11-01 (v3):** The owner needs it to **go on and off quickly** because it has to be off for folding. Offered three
  options (stay-on clip + sliding cup module, cam lever, strap). The owner chose the **stay-on clip + sliding module**.
  Split the part in two: the clip (ring, ears, bolt, boss, 45° dovetail tongue) stays on the rail, and the module (dovetail
  block, web, floor, pocket) drops on from above, resting on the ear tops, and lifts straight off. Dropped the shelf and the
  hex-key window. Added two test prints for the sliding fit. All pairs interference-free, both pieces watertight, no steep
  faces on the module. Next: owner checks the empty clip against folding, confirms the clip spot and latch/strut
  clearance, measures the tumbler, and prints the test pieces.
- **2026-11-01 (v3 feedback):** The owner sent two more photos of the push frame: the **diagonal bar and the red latch sit a bit
  further out than the push bar** the holder clips to, so they're in the way of a cup hanging off the outside. Also confirmed the
  **side rail is 22.3 mm** and that the **retailer tumbler figures are fine for now**. No model change yet: I need to know which
  end has the latch and strut, how far out they reach, and how far along the bar they extend before I move the cup.
  Likely fixes: shift the module toward the free end of the bar, push the cup further out (`web_gap`), and/or raise it (`floor_drop`).
- **2026-11-01 (v3.1):** Owner's answers on the strut and latch: the **same at both ends**, they reach **~26 mm** out past the bar,
  and the **120 mm is the clear stretch between them**. Retailer tumbler dims accepted for now. Moved the cup out: `web_gap` 24 → **40 mm**
  (cup axis 83.8 mm from the bar axis, twist 0.67 → 0.82 N·m, still within the clamp's estimated capacity). Centred the clip on the
  module along the bar (16 mm margin to each end of the window for the module). Extended the dovetail block down to the bed so it
  doesn't float (that had created an 805 mm² bridge). Added approximate latch/strut keep-out zones (`renders/ref-keepout.stl`) and
  checked the module and clip against them: 0 interference. Next: owner checks the strut doesn't reach under the cup, then the test prints.
