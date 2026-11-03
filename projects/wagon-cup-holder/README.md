# Wagon cup holder

A two-piece cup holder for the **right-hand side rail** of the owner's
[MAC Sports push/pull wagon](https://macsports.com/products/mac-sports-push-pull-wagon)
(the push-handle frame, as seen from the pusher). A **clip stays on the rail**, and the **cup module lifts on and
off it in a couple of seconds**, so it can come off for folding the wagon. It holds a **20 oz Yeti Rambler**
hanging off the outside of the wagon. The clip is clamped by a **standard M4 screw, washer and nut** (an ordinary hardware kit has them).

![the holder](renders/cup-holder.png)

## Goal

A tool-free way to take the cup off and put it back, with the cup hanging off the side of the wagon, lower than
the rail, and the whole thing looking like **one natural, flowing object** (the owner's words: "weird notches, walls, angles that
feel unnatural... it could all just flow together more seamlessly").

## Status

- [x] Reference photos saved (`source/`)
- [x] Tube measured by the owner: round, **22.3 mm** (confirmed on the side rail), **~120 mm** clear
- [x] Owner OK with the retailer figures for the tumbler for now
- [x] Strut + red latch: they sit further out than the bar (~26 mm, same at both ends). The cup is placed to clear them
- [x] **v6 rebuilt as one blended form** (see "How it's made"): module 112.1 × 87.7 × 90.5 mm,
      clip 51.8 × 42.9 × 70 mm. Both single watertight bodies, 0 interference everywhere
- [x] Printed: the clip test (fit well), the dovetail pair (will probably work) and the full parts (**"worked for the most part"**). **The printed bolt snapped**, so the clamp uses real M4 hardware now (clip needs a reprint)
- [ ] **Owner: does v6 look right?** Natural, flowing, no weird notches
- [ ] **Owner: check the strut doesn't slope in under the cup** (cup base is 60 mm below the rail axis)
- [ ] **Owner: does the empty clip block folding?** (see "Folding")
- [ ] Print the full clip and module in PETG, test on the wagon with a full cup, adjust

## How it works

- The **clip** (ring + ears) is snapped on and **tightened with an M4 screw** (3 mm hex key). It stays on the rail.
  On its outboard side a vertical **dovetail tongue** (34 mm wide at the root, 48 mm at the tip, 7 mm tall,
  **28 mm of vertical engagement**).
- The cup **module** has the matching groove (0.35 mm clearance per side). It **drops straight down onto the tongue**
  and rests on the tops of the clip's ears, so **gravity holds it seated**. To remove it, lift it straight up
  ~28 mm and it comes off with the cup in it, one-handed, no tool.
- The cup is a **tapered ring** that follows the Yeti's taper, closed at the bottom, open at the top. A slim **stem** sweeps from its
  inboard side back to the dovetail pad. The rim, the stem and the pad all end in one **flat top plane** (24 mm above the rail axis).
- **No detent yet.** To lift off, the module has to move up 28 mm; a wagon bump is very unlikely to do that. If it hops in testing,
  add a small click detent (bump on the tongue flank + dimple in the groove) or a lanyard.

### How it's made (v6)

v1–v5.1 stacked flat prisms (a plate, a block, a disc, a bracket) and filleted where they met. That always reads as assembled. v6 builds
each piece as **one continuous field with smooth blends** (`sdf.py`, `model.py`), then meshes it. Joins are true blends and every edge that meets
the top plane is rounded. Everything that has to be exact (the dovetail tongue and groove, the rail bore, the snap mouth, the bolt hole and
the nut pockets) is **cut exactly afterwards** on the mesh. The cup now **prints upright** (floor on the bed), so the pocket is a plain closed
ring: the side opening that caused the "notch" in v5 is gone.

**The trade:** the clip and module are now **meshes (STL), not editable CAD (STEP)**, so they can't be opened as solids in Fusion. Change the numbers in
`model.py` and rebuild. The last editable STEP version (v5.1) is in git history (commit "v5.1: clean up the notch").

### Folding

What stays on the rail when the cup is off: the **clip is 70 mm long and extends about 24 mm above the rail axis,
27.8 mm below it, ~22 mm outboard and ~20 mm inboard** (the ears and the dovetail tongue). **Whether that blocks folding is still unknown.**
Cheap check: clamp the 20 mm clamp slice (`wagon-cup-clip-test.stl`, ears but no tongue) on the right rail where the clip would go and fold the wagon. If it gets in the way,
move it along the rail, or loosen the screw and take the whole clip off (a few turns of a hex key) when you fold.

## What I read from the photos (2026-11-01)

The push frame is a **U-shaped tube**: a foam-covered grip bar across the back (~9 in between its end brackets, mostly foam), and at each end a round
powder-coated tube bends into a **side rail** toward the wagon. Each side rail has a black end cap and a red latch, and a diagonal flat strut below it.
The right-hand side rail's straight run is roughly 8–9 in, and the owner's "~120 mm" is the clear, unobstructed stretch between the latch/strut at each end.
The outside of the rail is open air. This is the "hanging off the side" spot.

**Owner's answers on the strut and latch:** the same at both ends, they reach "maybe 26 mm" out. I took that as 26 mm past the bar's **outer surface**
(37.2 mm from the bar axis, the cautious reading). The cup's outer wall is **40 mm** from the bar axis at the rim (2.9 mm clear of that).

## Measurements

| Feature | Real (mm) | Source | Notes |
|---|---|---|---|
| Tube outer diameter | **22.3** | owner, confirmed on the side rail | Calipers on a painted tube read ±0.2 |
| Clear rail length | **~120** | owner, "roughly" | Clip is 70 mm long, the cup ring is 88.07 mm wide. Cup + clip are centred on it |
| Strut + latch reach past the bar's surface | ~26 | owner, "maybe" | Same at both ends. Modelled as two blocks beyond the clear window |
| **Angled strut section** | **13.5 × 13.5** (square) | owner, calipers, 2026-11-03 | Same both ways. Not yet known if hollow |
| Strut: inner face past the bar's surface | ~4–7 (estimate) | top-down photos: caliper shot scaled off the 22.3 mm bar gave ~7, the horizontal-tape shot gave ~4 | The two disagree by 3 mm (perspective). The ring can rotate on the bar, which absorbs a few mm. Ask for one ruler reading |
| Strut: outer face past the bar's surface | ~15–20 (estimate) | same two photos | The owner had guessed ~26 |
| **Strut slope and depth** | **~59° from horizontal.** Centreline depth below the bar axis ≈ **1.63 × x − 7 mm**, x = distance along the bar from the strut's pivot screw | three vertical-tape photos (2026-11-03): 65 / 130 / 200 mm at x = 44 / 84 / 127 mm | Fit within ~1 mm of those three points, but they're pixel readings of photos at slightly different depths: treat as ±10%. At x = 30 / 43 / 73 / 103: ≈ 42 / 63 / 112 / 161 mm |
| Bracket screws, centre to centre | ~150–165 | tape photos | The clear stretch (~120 mm, owner) starts ~13 mm from the strut's pivot screw |
| Tumbler base diameter | 70 (2.75 in) | retailer listing | Owner OK with this for now |
| Tumbler widest diameter (lid) | 89 (3.5 in) | retailer listing | Owner OK with this for now |
| Tumbler height | 168–175 (6.6–6.9 in) | retailer listings | Only used to size the taper |

Retailer sources: [Rogue](https://www.roguefitness.com/yeti-rambler-20oz-tumbler),
[Rogue Canada](https://www.roguecanada.ca/yeti-rambler-20oz-stainless-limited-edition).
Enter measured tumbler values in `CUP_OVERRIDES` in `build.py`.

## Design decisions and why

- **Layout (use frame: rail along X, Z up):** the clip wraps the side rail from above, mouth facing down. The module hangs off its outboard side. The cup axis is
  **84 mm outboard of the rail axis**, and the **cup base is 60 mm below it**, so the rim is 24 mm above it.
- **The clamp is still essential.** The cup is beside the rail, so a full cup (~1 kg) is a constant twist of about **0.82 N·m** on the clip.
  A snap-fit's friction at rest is ~0.1 N·m. So the clip has **two ears and an M4 screw across the mouth**: tightening pulls the C closed around the tube
  (roughly belt-like, so ~4× the bolt force presses on the tube). That's an estimate, so **verify with the clamp slice** (try to twist the tightened slice on the real rail).
- **Hardware: standard M4, sized for what kits actually contain.** (The printed M8 bolt snapped. M8 then needed 45 mm bolts, and most kits stop short of 40 mm, even in M4.)
  The screw **head and washer sit in a round pocket in the INBOARD ear** (reachable with the module on) and the **nut in a hex pocket in the OUTBOARD ear** (slid in from the bottom
  of the ear, captive so it can't spin). Both pockets are cut deep (5 mm of an 8 mm ear), which shortens the run the screw must cross, and each leaves a **3 mm wall** to bear on.
  Buy / use: **M4 socket cap screw, 30 mm or 35 mm**, **one M4 hex nut** (plain, 7 mm across flats, 3.2 mm thick; **not nyloc**, it is too tall), **one standard M4 washer** (9 mm OD, 0.8 mm; a bigger one won't fit the pocket)
  and a **3 mm hex key**. Checked against the model: **M4 × 30 engages 2.5 of the nut's 3.2 mm (~3½ threads)**, **M4 × 35 engages it fully and pokes out 2.5 mm**, M4 × 40 pokes out 7.5 mm. **M4 × 25 is too short.**
  Hex-head M4 also fits (the round pocket is 9.6 mm). Stainless is best outdoors. **Snug, then 1/8 turn.** A 3 mm key makes it easy to crush PETG. The clip hangs 24.3 mm below the rail axis (was 27.8 with M8).
  The model includes the screw, washer and nut as ghosts and checks that they fit the holes and pockets with no collision.
- **Snap geometry:** the mouth is 20.7 mm wide against the 22.3 mm tube, so each arm spreads ~0.8 mm (≈1% strain, fine for PETG). The owner's test
  print fit well.
- **Printing:** the **module prints upright** (base chamfered at exactly 45°, the stem's underside is a self-supporting ≥45° sweep, the dovetail groove is a vertical channel).
  The **clip prints with its ring axis vertical** (layers run around the ring, so the arms flex along the layers). Overhang area over 45°: module 62.5 mm² (the pad's flat seat),
  clip 247.3 mm² (flat-topped nut pockets and slots, ≤ 8 mm bridges). No supports.
- **Material:** PETG (outdoor, sun, flexing clip). PLA creeps and softens in a hot car or in the sun, and ASA/ABS warp on the open-frame A1.
- **History:** v1 cup on top of the bar; v2 hung off the side rail; v3 split into clip + module (quick release); v3.1 moved the cup out to clear the strut; v4 shaped bracket
  instead of a slab; v5 printed M8 bolt and nut (snapped); **v6.1 standard M4 hardware, recessed**; v5.1 trimmed the notch; **v6 (this) rebuilt both pieces as one blended form**. Earlier versions are in git history.

## Print settings (suggested, not yet test-printed)

- PETG, 0.2 mm layers, 4–5 walls, 15–20 % gyroid infill. Brim on the clip (it stands on a small footprint). The module stands on a ~88 mm base, so it needs less.
- Orientation is already built into each STL. Don't re-orient them.
- Volumes: module 142 cm³ and clip 49.9 cm³ solid. Expect roughly 60–80 g and 25–35 g with those settings.
- **Test prints, in order:**
  1. `wagon-cup-clip-test.stl`: **20 mm ring + ears (new M4 pockets)**. Snap it on, slide the nut into the outboard pocket from below, drop the washer and screw into the inboard pocket,
     tighten with the 3 mm key, and try to twist it on the rail. The clip you printed already (10 mm ears for the printed M8) fit the rail well, and the ring and mouth are unchanged.
  2. `wagon-dovetail-test-tongue.stl` + `wagon-dovetail-test-groove.stl`: now flat pieces, 14 mm tall. The groove block slides down onto the tongue.
     Adjust `dt_clear` (0.35 mm per side now) if it's too tight or sloppy.
  3. The full clip and module.

## Open questions

1. **Does the empty clip block folding?** See "Folding" above.
2. **Does the diagonal strut slope in under the cup?** The cup base is 60 mm below the bar axis. If it does, raise the cup (`floor_drop`).
3. **Is there room for the screw head and a 3 mm hex key on the inboard side?** (The head is recessed 0.2 mm inside the ear, so nothing sticks out.)
4. Does the owner's tumbler have a handle? Is its base edge rounded? (The ghost tumbler assumes a 3.5 mm base-edge radius; the pocket floor has a 3 mm fillet.)
5. Is a click detent wanted, or is gravity enough?
6. Would a rubber strip or inner-tube liner on the rail be wanted for extra grip? (Easy to add.)

## Pipeline

`python projects/wagon-cup-holder/build.py` (~2 min):
1. `model.py`: `build_module` = tapered cup ring + stem/pad as signed-distance fields, smooth-unioned, hollowed, top plane rounded, meshed with marching cubes (`sdf.py`,
   0.5 mm cells, decimated), then the dovetail groove cut exactly. `build_clip` = ring + ears + boss as a field, meshed, the dovetail tongue unioned exactly, then the bore,
   mouth, bolt hole and nut pockets + slots cut exactly. Booleans are `manifold3d`. Only the largest body is kept (booleans on coplanar faces leave slivers).
2. `build.py` exports each piece in its print pose and the test pieces, and models the M4 screw, washer and nut as ghosts for the fit checks and the viewer.
3. Checks, in the assembled (real use) pose: both pieces watertight and one body, overhang area, and the interference of every pair: module/clip (a contact, ≤ 0.01 cm³),
   module/rail, module/tumbler, clip/rail, clip/tumbler, both vs the strut/latch zones, bolt vs clip/module/rail, nut vs clip/module (all must be ~0).

Key parameters (`CupHolderParams` in `model.py`): `bar_d`, `clip_wall`, `clip_len`, `mouth_width`, `dt_clear`, `inboard_gap`, `floor_drop`, `pocket_depth`, `cup_*`,
`pocket_clearance`, `stem_half_w`, `blend_k` (how soft the stem-to-cup blend is), `top_round_k`, `pad_stem_k`, `base_chamfer`, `voxel`.
Needs `scikit-image` (marching cubes), in `requirements.txt`.

## Files

- **Interactive viewer:** https://claude.ai/artifact/Anqg9yywWNz2pW6LNgwWoN (private to the owner).
  Built from `renders/viewer.html` by `tools/make_viewer.py` using `review.json`. Republish to this URL on every review (see `docs/review.md`)
- `source/wagon-photo-2026-11-01.jpg`, `source/wagon-photo-2026-11-01-rail-1..6.jpg`, `source/wagon-photo-2026-11-03-strut-*.jpg` (caliper on the strut, top-down; tape beside the strut, front): the owner's photos
- `model.py`: the two pieces. `sdf.py`: the blend toolkit. `build.py`: pipeline
- `output/wagon-cup-clip.stl`: the clip that stays on the rail
- `output/wagon-cup-module.stl`: the cup module that lifts on and off
- `output/wagon-cup-clip-test.stl`: 20 mm ring + ears slice, for the snap and clamp test
- `output/wagon-strut-grip-test.stl`: three C-clips for the 13.5 mm square strut (0.2 / 0.4 / 0.6 mm clearance = 16 / 20 / 24 mm tall), print upright
- `output/wagon-dovetail-test-tongue.stl`, `output/wagon-dovetail-test-groove.stl`: sliding-fit test pair
- `output/report.json`: dimensions, checks, parameters
- `renders/cup-holder.png`, `renders/sections.png`, `renders/in-use.png`: previews and sections
- `renders/asm-*.stl`, `renders/ref-*.stl`: light assembled-position meshes, the ghost rail, tumbler and strut/latch zones, for the viewer

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
- **2026-11-01 (v4):** The owner didn't like the **big bulk block** between the clip and the cup holder, and asked for something
  more flowing and integrated. Replaced it with a shaped neck (`_neck` in `model.py`): a flat pad under the dovetail whose cheeks are a constant
  4 mm around the groove and flare at 45° out to the web (so every overhang stays 45°), a **16 mm inside fillet** sweeping the underside into
  the web, and an **8 mm blend** from the pad's top down to the web's top. It no longer spans the module's full width. Module 190 cm³ (was 203),
  still 0 overhang, 0 interference with the clip, rail, tumbler and keep-out zones. The dovetail test pieces keep their plain block (they only test
  the sliding fit). Further ideas if it still feels heavy: hollow or window the neck, lower the engagement (`dt_y1`) so the pad is shorter, or
  curve the web in toward the bar near the top once we know where the strut sweeps in.
- **2026-11-02 (v5):** The owner printed the three test parts: **the clip fit well**, and the dovetail pair "will probably work" but that print
  was messy (they were 70 mm tall posts on a small footprint). Decided to go straight to the full print. The owner also asked for a **printed
  bolt and nut**. A printed M4 would strip, so the ears are redesigned for a **printed M8 × 1.5 knob bolt and hex nut** (`fasteners.py`): ears
  8 → 10 mm thick, 9 mm bolt hole, 13.5 mm nut pockets and slide-in slots on both ears (nut on either side), clamp slice 15 → 26 mm. The knob
  lets the clamp be tightened by hand, without a hex key. Checks: bolt and nut watertight and mesh with 0 interference at any position,
  the bolt clears the clip, module and rail, the nut fits its pocket. **The clip geometry changed, so the old clip that "fit well" was the
  M4 version. The bore, mouth and ring are unchanged, so the snap fit should be identical.** Next: owner prints the bolt, the nut and the new
  clamp slice (quick), and the full clip and module.
- **2026-11-02 (v5.1):** The owner circled a **notch in the holder piece** in the viewer. It was two things: the pocket's side opening (intentional, so
  the pocket prints on its side without supports), and a leftover where the back wall (a full-height 87.6 mm plate) stuck up ~19 mm past the lip of the
  curved wall with a hard square corner and a thin slit between them. Fixed: the web now stops at `z_top` (72.65 mm, set by the 4 mm cheek the dovetail
  groove needs), its top outer corner is chamfered along the pocket's outer circle up to the lip, the opening angle is derived so the lip ends level
  with it (wrap 250° → 262°), and the whole module, including the round floor disc, is cut flat at that height. Module 188 → 184 cm³, and
  **88 → 73 mm tall**. Still 0 overhang and 0 interference everywhere. Did not trim the web lower than the groove allows: that would have left no wall
  on the groove's +Z side.
- **2026-11-02 (v6):** The owner still found **"weird notches, walls, angles that feel unnatural"** and asked for the model to **"flow together more seamlessly"**.
  Diagnosis: every version so far was a union of flat prisms with fillets, which always looks assembled. **Rebuilt both pieces from scratch as one blended form.**
  Module: a tapered closed cup ring (it prints upright, so the side opening, and the notch it caused, are gone), with a slim stem that sweeps back to the
  dovetail pad, joined by smooth blends, ending in one flat top plane with every edge rounded. Clip: ring + rounded ears + boss as one blended body with the dovetail
  tongue and all the fit-critical cuts made exactly. Cup base 45° chamfered, stem underside ≥ 45°, so it still prints with no supports. **Trade-off: the pieces are now meshes (STL), not
  editable STEP.** Module 142 cm³ (was 184), one body, 0 interference with the clip (contact only), rail, tumbler, bolt, nut and the strut/latch zones.
  Found and fixed on the way: a bug where the stem's 45° underside ran past the cup's base and stuck out as a blob; smooth unions bulging at shared planes (the clip's ends,
  the boss-to-ear seat); a 5 mm pocket-floor fillet that collided with a sharp-edged ghost tumbler (now a 3 mm fillet and a 3.5 mm base-edge radius on the ghost).
  Added `scikit-image` to `requirements.txt`. Next: owner reviews the look, and prints the bolt/nut/clamp slice and then the full parts.
- **2026-11-03:** The owner printed the full v6 parts: **"the model worked for the most part"**. **The printed M8 bolt snapped** and its thread didn't fit well with the printed nut,
  so they'll use a real bolt and nut and asked what to buy and what sizes are common in a set. Answer: **M8 × 45 mm hex bolt + M8 hex nut + M8 fender washer (~24 mm OD)**, or
  5/16"-18 × 1¾" with a 5/16" nut and fender washer in imperial. Checked against the model: nothing needs to change (9.0 mm hole, 13.5 mm hex pocket, 6.9 mm deep, 20.7 mm gap, 10 mm ears).
  45 mm is the right length with a washer; 40 mm only just engages the nut; 35 mm is too short. Avoid nylon-insert nuts (too tall for the pocket). Offered: a printed hex-socket knob
  that slips over the bolt head for finger-tightening (the bolt carries the load, the knob only turns it). Waiting on: what else "for the most part" covers (what didn't work?).
- **2026-11-03 (v6.1):** Owner asked whether to go back to M3 or M4 now that real bolts are the plan, then noted **most kits don't include a 40 mm bolt, even in M4**. Tried M3/M4/M5/M8 ears in the model first:
  all build; M4 hangs 3.5 mm lower than M8 would; M3 is too fiddly (5.5 mm nut, 1.9 mm seat strip). Went with **M4 and redesigned the clip so a common M4 × 30 works**: ears 10 → **8 mm**, bolt hole 4.5 mm, the screw head + 9 mm
  washer in a **5 mm-deep round pocket in the inboard ear**, the nut in a **5 mm-deep hex pocket in the outboard ear** (7.4 mm AF), 3 mm walls behind both, clamp slice 26 → 20 mm. Verified: M4 × 30 engages 2.5 of the nut's 3.2 mm,
  M4 × 35 fully. All 12 interference checks pass with a modelled screw, washer and nut in place. Checked that the **module the owner already printed fits the new clip equally** (contact only, 1.9 mm³), so **only the clip needs
  reprinting**. Removed `fasteners.py` and the printed bolt/nut STLs (git history has them). Asked: what is the longest M4 in the owner's kit?
- **2026-11-03 (hardware kit):** The owner found a candidate kit: Kernmax 320-piece **M4 socket head cap screw assortment** (12.9 black-oxide alloy steel; M4 × 25/30/35/40/45/50 mm, with hex nuts, flat washers, spring washers and a hex key).
  Checked against the clip: **M4 × 30 and × 35 are in it** (use 30 first, 35 if it feels short); M4 SHCS head (7 × 4 mm) fits the 9.6 mm pocket; plain hex nut fits the 7.4 mm pocket. Things to check on arrival: flat washer is
  ~9 mm OD × 0.8 mm (a 10 mm one won't fit the pocket; leave it out, and an M4 × 30 then engages the nut fully); don't use the spring washers in the pocket. **Black oxide rusts outdoors**: oil the screw, or use A2 stainless
  if it becomes a nuisance. 12.9 steel will crush PETG, so snug + 1/8 turn only. Next: owner prints the 20 mm clamp slice and tries the hardware, then the full clip.
- **2026-11-03 (two-point clip idea):** The owner folded the handle with the cup piece off: **the bolted clip, still on the bar, blocks the fold.** They proposed using the angled strut for support, then, keeping the dovetail
  so other attachments can be made, **a clip that is similar to now but extends down and clips a second time onto the strut**. Reasoning: two grips locate the clip fully (the strut grip stops rotation about the bar and sliding along it),
  so the ears, screw and nut can go, and the whole clip pops off in one motion for folding. Risks noted: the frame has play (make the strut grip forgiving), the cup moves out a few mm for the grip, the arm must pass under the module's stem.
  Owner measured the strut: **13.5 mm in both directions** (square section). From the top-down caliper photo (scaled off the 22.3 mm bar) the strut's inner face is ~7 mm and its outer face ~20 mm past the bar's surface
  (~31 mm from the bar axis; the model's keep-out used 37). From the front tape photo the strut is **steeper than assumed, ~55°**, so it is ~60 mm below the bar axis about 40 mm from its bracket pivot, and the grip
  would sit near the ring's strut-side end with a ~45 mm arm. **Built `wagon-strut-grip-test.stl`**: three C-clips (0.2 / 0.4 / 0.6 mm clearance, 1 mm lips, 2.5 mm walls, lead-in) to find which snaps on and holds the real strut.
  Next: owner prints it and reports which clip works, confirms C and one D with a ruler, and says which end of the bar the strut hangs from on the right-hand frame (the arm goes to that end). Then build the two-point clip.
- **2026-11-03 (strut photos):** The owner sent six photos with no text: an overview, a view from above, a horizontal tape from the bar across to the strut, and **three vertical tapes hung from the top of the bar at three
  places along it** with the strut crossing behind each. Read off: the strut is a straight line at **~59°**, **depth below the bar axis ≈ 1.63·x − 7 mm** (x from the pivot screw): 65 / 130 / 200 mm at x = 44 / 84 / 127 mm
  (three points within ~1 mm of the fit; they are my pixel readings, so ±10%). So at the window's strut-side end the strut is shallow (14 mm at x = 13), ~45 mm down at x = 31, ~110 mm at the window's middle. That favours putting the
  ring at the **strut-side end of the clear stretch** with a **short leg (~30 mm)** to the strut grip, not a long arm from the middle. Horizontal-tape photo gives the bar-to-strut gap as ~4 mm vs ~7 from the caliper shot: they disagree, so asked for one
  ruler reading. Drew a **concept diagram** of the two-point clip on the measured frame for the owner to check. Open: which end of the bar the strut hangs from on the **right-hand** frame (the arm goes to that end); which strut-grip test clip
  (16/20/24 mm = 0.2/0.4/0.6 mm clearance) works; what hit when the handle folded. Not yet modelled: the two-point clip.

