# Wagon cup holder

A two-piece cup holder for the **right-hand side rail** of the owner's
[MAC Sports push/pull wagon](https://macsports.com/products/mac-sports-push-pull-wagon)
(the push-handle frame, as seen from the pusher). A **clip stays on the rail**, and the **cup module lifts on and
off it in a couple of seconds**, so it can come off for folding the wagon. It holds a **20 oz Yeti Rambler**
hanging off the outside of the wagon. The clip has **no screw**: a ring snaps onto the rail and a **second C-grip snaps onto the angled strut**, so the
clip and the cup come off together when the handle has to fold. The strut grip faces so that **a full cup pushes it on tighter**, not off.

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
- [x] Printed: the clip test (fit well), the dovetail pair (will probably work) and the full v6 parts (**"worked for the most part"**). The printed bolt snapped; real M4 hardware was planned, then
      the owner found the **bolted clip blocks folding the handle** even with the cup off
- [x] Strut measured: **13.5 mm square**, straight line ~59°, depth below the bar axis ≈ 1.63·x − 7 mm (x from the pivot screw). Owner confirmed which end it hangs from and the layout
- [x] **v7 built: two-point clip** (ring + leg + strut C-grip, no screw). 0 interference with rail, strut, tumbler, latch zones. The module is unchanged (the printed one still fits)
- [x] Printed the v7 clip: "worked really well", the grip fit the strut nicely, but it **un-snapped from the strut under a full cup**. v7.1 (deeper lips, thicker walls) **still didn't hold** a full cup
- [x] **v8 built: the strut grip is flipped** so the closed wall of the C faces the cup and the mouth faces the bar. The cup's pull now presses the strut into a solid wall. Same ring, dovetail and module (printed module still fits)
- [x] Owner report: lifting the tumbler out sometimes lifts the whole module off the dovetail and it "sticks" to the cup. **Added a 10 mm vent hole through the pocket floor** (module reprint, or drill the printed one)
- [x] Owner thinks the sticking is the tumbler **wedging in the tapered pocket**, not suction. **v8.2: pocket opened up** (floor clearance 2 → 4 mm on the diameter, plus a draft that adds 0.02 mm per mm of height, so 85.4 mm at the rim). The vent hole stays
- [ ] **Print `wagon-strut-grip-test.stl`** (v8: three C-clips, lips 1.2 / 1.6 / 2.0 mm = 16 / 20 / 24 mm tall), check which goes on by hand and stays on, then print the full v8 clip (with supports)
- [ ] **Owner: check the arm side** (see "How it works") and that the strut gap looks right (nominal 5.5 mm, could be 4 to 7)
- [ ] Print the full clip **with supports** (see "Print settings"), try it on the wagon with a full cup, fold the handle
- [ ] Ruler reading of the gap from the bar's surface to the strut's inner face (to pin the gap down)

## How it works

- The **clip** has two grips. A **ring** (22.5 mm bore, 2.8 mm wall, 70 mm long) snaps onto the right-hand side rail at the **strut end** of the clear stretch. A diagonal **arm** runs down
  from under the ring's outboard ear to a **C-shaped grip** (13.8 mm square tunnel, 22 mm long, 3 mm walls, 1.6 mm lips, with a lead-in) that snaps onto the **angled strut** about 45 mm below the bar. No screw, nut or tool.
- **Why the C faces the way it does (v8):** the cup (~1 kg, 84 mm out) twists the clip about the bar, so the strut grip (~43 mm below the bar) is pushed toward the cup with about 1.9 × the cup's weight (~19 N, 2–3× in bumps).
  In v7 / v7.1 the C's mouth faced the cup, so that load tried to push the strut out through the mouth and the lips let go. In **v8 the closed wall faces the cup and the mouth faces the bar**: the load presses the strut into a solid 3 mm wall.
  The lips now only keep the clip on when the cup isn't pulling (empty clip, bumps that swing the cup back). The strut grip also stops the clip sliding along the bar (the strut slopes). The ring can rotate about 2° to absorb ±1.5 mm of strut-gap error.
- **Putting it on (untested, tell me how it feels):** 1) hold the clip above the bar, a little out from the strut, ring mouth (it faces down) above the bar; 2) push it **in toward the wagon** so the strut snaps into the grip through its bar-side mouth;
  3) **slide it down along the strut** until the ring clicks onto the bar from above. To take it off: lift it up along the strut until the ring clears the bar, then pull it out. The weight of the cup never pulls it off.
- **Arm orientation (check before you print):** viewed from outside the wagon, cup toward you, the **strut end is on your LEFT**. A short diagonal **arm** runs from under the ring's outboard ear, down and to the left, to the grip on the strut's upper side. The ring sits on the bar at the left end of the clear stretch.
- On the clip's outboard side is the vertical **dovetail tongue** (34 mm wide at the root, 48 mm at the tip, 7 mm tall, 28 mm of vertical engagement). It is unchanged, so other attachments can be made for it.
- The cup **module** has the matching groove (0.35 mm clearance per side). It **drops straight down onto the tongue** and rests on the tops of the clip's ears, so **gravity holds it seated**. To remove it, lift it ~28 mm.
- To fold the wagon: lift the cup off, then pull the clip off the bar and strut in one motion (or leave the cup on and lift both off together).
- The cup is a **tapered ring** that follows the Yeti's taper, closed at the bottom, open at the top. A slim **stem** sweeps from its inboard side back to the dovetail pad. The rim, the stem and the pad all end in one **flat top plane**.
- **Vent hole:** a 10 mm hole through the middle of the pocket floor (`vent_d`) lets air in under the tumbler's base when it is lifted out, so it can't suck the module up with it. It also drains rain. Prints fine (vertical hole).
- **No detent yet.** To lift off, the module has to move up 28 mm; a wagon bump is very unlikely to do that. If it hops in testing, add a click detent or a lanyard.

### How it's made (v6)

v1–v5.1 stacked flat prisms (a plate, a block, a disc, a bracket) and filleted where they met. That always reads as assembled. v6 builds
each piece as **one continuous field with smooth blends** (`sdf.py`, `model.py`), then meshes it. Joins are true blends and every edge that meets
the top plane is rounded. Everything that has to be exact (the dovetail tongue and groove, the rail bore, the snap mouth, the strut grip's cavity and mouth) is **cut exactly afterwards** on the mesh. The cup now **prints upright** (floor on the bed), so the pocket is a plain closed
ring: the side opening that caused the "notch" in v5 is gone.

**The trade:** the clip and module are now **meshes (STL), not editable CAD (STEP)**, so they can't be opened as solids in Fusion. Change the numbers in
`model.py` and rebuild. The last editable STEP version (v5.1) is in git history (commit "v5.1: clean up the notch").

### Folding

The old bolted clip stayed on the bar and got in the way when the handle folded down (owner test, 2026-11-03). v7 is built to come **off entirely**: the ring snaps off the bar and the grip snaps off the strut, so nothing is left on the
frame. Take both off to fold; the cup can stay in the clip and come off with it.

- **Snap geometry:** the mouth is 20.7 mm wide against the 22.3 mm tube, so each arm spreads ~0.8 mm (≈1% strain, fine for PETG). The owner's test
  print fit well.
- **Printing:** the **module prints upright** (base chamfered at exactly 45°, the stem's underside is a self-supporting ≥45° sweep, the dovetail groove is a vertical channel).
  The **clip prints with its ring axis vertical** (layers run around the ring, so the arms flex along the layers). The module overhang area is 41.9 mm². **The clip is ~646 mm² (v8) and needs supports:** in this pose the strut grip's tunnel
  runs ~31° above horizontal, so its ceiling overhangs (mostly 20–35° from flat, at 45–61 mm above the bed). The ring, mouth and dovetail print clean.
- **Material:** PETG (outdoor, sun, flexing clip). PLA creeps and softens in a hot car or in the sun, and ASA/ABS warp on the open-frame A1.
- **History:** v1 cup on top of the bar; v2 hung off the side rail; v3 split into clip + module (quick release); v3.1 moved the cup out to clear the strut; v4 shaped bracket instead of a slab; v5 printed M8 bolt and nut (snapped);
  v5.1 trimmed the notch; v6 rebuilt both pieces as one blended form; v6.1 standard M4 hardware, recessed; **v7 (this) two-point pop-off clip, no hardware**. Earlier versions are in git history.

## Print settings (suggested, not yet test-printed)

- PETG, 0.2 mm layers, 4–5 walls, 15–20 % gyroid infill. Brim on the clip (it stands on a small footprint). The module stands on a ~88 mm base, so it needs less.
- Orientation is already built into each STL. Don't re-orient them.
- **Clip: turn supports on** (normal/auto, "build plate and model"), then clean the grip's tunnel with a small tool. Support the leg and the grip only; the ring bore, mouth and dovetail don't need it. Paint supports off the bore if the slicer puts any there.
- Volumes: module ~144 cm³ and clip ~47 cm³ solid. Expect roughly 60–80 g and 25–35 g with those settings.
- **Test prints, in order:**
  1. `wagon-strut-grip-test.stl`: three C-clips, 0.3 mm clearance, lips **1.2 / 1.6 / 2.0 mm** (16 / 20 / 24 mm tall), **mouth toward you**. Push each onto the strut from the bar side (the mouth faces the bar when worn), then push it the way a full cup would (outward, away from the bar: it should jam against the closed wall) and tell me which one goes on and off by hand but doesn't fall off by itself.
  2. `wagon-dovetail-test-tongue.stl` + `wagon-dovetail-test-groove.stl` (already done: "will probably work").
  3. The full clip (with supports) and, if the module needs it, the module. The printed v6 module already fits the new clip (the dovetail is unchanged).

## Open questions

1. **Strut gap:** the nominal 5.5 mm between the bar surface and the strut's inner face is a guess (photos say 4 to 7). The ring can absorb ±1.5 mm by rotating ~2°. A ruler reading would pin it down.
2. **Is the strut hollow?** (A hollow tube could squash a little in the grip; a solid bar would not.)
3. **Grip lip depth:** which test clip (lip 1.2 / 1.6 / 2.0 mm) goes on by hand and stays on? Set `grip_lip` to it. Also: does the install motion (in toward the wagon, then down) feel natural? Did the ring ever lift off the bar when the cup bounced?
4. **What hit when the old clip blocked folding?** Does anything else foul when the handle folds (e.g. the leg against the latch)?
5. **Does the strut slope in under the cup?** The cup base is 60 mm below the bar axis; the model checks this against the 59° line with 0 overlap.
6. Does the owner's tumbler have a handle? Is its base edge rounded? (The ghost tumbler assumes a 3.5 mm base-edge radius.)
7. **Does the tumbler now lift out without bringing the module with it?** (Pocket 74 mm at the floor, 85.4 mm at the rim.) If it still does, the next step is a light retention on the dovetail (a click detent, or two small magnets in the boss and pad). Is the tumbler too loose now?

## Pipeline

`python projects/wagon-cup-holder/build.py` (~2 min):
1. `model.py`: `build_module` = tapered cup ring + stem/pad as signed-distance fields, smooth-unioned, hollowed, top plane rounded, meshed with marching cubes (`sdf.py`,
   0.5 mm cells, decimated), then the dovetail groove cut exactly. `build_clip` = ring + ears + boss + arm + strut-grip envelope as a field, meshed, the dovetail tongue unioned exactly, then the bore,
   mouth, strut keep-out and the grip's mouth (facing the bar) cut exactly. Booleans are `manifold3d`. Only the largest body is kept (booleans on coplanar faces leave slivers).
2. `build.py` exports each piece in its print pose and the test pieces, and models the rail, tumbler, latch zones and the angled strut as ghosts for the fit checks and the viewer; it also runs the strut-gap sensitivity (4 and 7 mm).
3. Checks, in the assembled (real use) pose: both pieces watertight and one body, overhang area, and the interference of every pair: module/clip (a contact, ≤ 0.01 cm³),
   module/rail, module/tumbler, clip/rail, clip/tumbler, clip/strut, module/strut, both vs the latch zones (all must be ~0).

Key parameters (`CupHolderParams` in `model.py`): `bar_d`, `clip_wall`, `clip_len`, `mouth_width`, `dt_clear`, `strut_gap_in`, `strut_slope`, `grip_clearance`, `grip_x`, `inboard_gap`, `floor_drop`, `pocket_depth`, `cup_*`,
`pocket_clearance`, `pocket_draft`, `stem_half_w`, `blend_k` (how soft the stem-to-cup blend is), `top_round_k`, `pad_stem_k`, `base_chamfer`, `voxel`.
Needs `scikit-image` (marching cubes), in `requirements.txt`.

## Files

- **Interactive viewer:** https://claude.ai/artifact/Anqg9yywWNz2pW6LNgwWoN (private to the owner).
  Built from `renders/viewer.html` by `tools/make_viewer.py` using `review.json`. Republish to this URL on every review (see `docs/review.md`)
- `source/wagon-photo-2026-11-01.jpg`, `source/wagon-photo-2026-11-01-rail-1..6.jpg`, `source/wagon-photo-2026-11-03-strut-*.jpg` (caliper on the strut, top-down; tape beside the strut, front): the owner's photos
- `model.py`: the two pieces. `sdf.py`: the blend toolkit. `build.py`: pipeline
- `output/wagon-cup-clip.stl`: the clip that stays on the rail
- `output/wagon-cup-module.stl`: the cup module that lifts on and off
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

- **2026-11-03 (v7, two-point clip built):** Owner confirmed the concept drawing (the strut hangs from the left end of the bar viewed from outside), the layout (ring at the strut end, grip ~45 mm below it), and said the existing clip tolerance is good
  (strut grip test not printed yet). **Replaced the screw clamp with a leg + C-grip on the strut.** Removed the ear screw hole and pockets for this variant (`two_point=True`; the screw path remains for `two_point=False`). Grip: 13.9 mm square tunnel (13.5 + 0.4),
  18 mm long, 2.5 mm walls, 1 mm lips and a 1.2 mm lead-in, at 24 mm from the ring's strut-side end, ~65 mm below the bar axis. Leg 16 mm wide. Checks: clip vs strut 0, module vs strut 0, clip vs rail/tumbler/latch zones 0, module vs clip 0.002 cm³ (contact).
  Gap sensitivity (informational): at 4 mm and 7 mm gap the clip would need to rotate <2° to follow. **Printability: the clip needs supports** (710.8 mm² of overhang from the tilted grip tunnel and leg underside in the print pose). Accepted for now rather than
  loosening the grip. Module unchanged (so the owner's printed module still fits). Dropped the M4 hardware and the 20 mm clamp slice (`wagon-cup-clip-test.stl`). Viewer config updated. Next: owner prints the strut grip test (16/20/24) and reports which works; then the full clip with supports.
- **2026-11-03 (v7.1, grip holds harder):** Owner printed the v7 clip: **"worked really well", the strut grip fit nicely, but under pressure (a full cup) it wasn't tight enough and un-snapped.**
  Reasoning: the cup (~1 kg, 84 mm out) twists the clip about the bar, and the strut grip sits ~43 mm below the bar, so it takes ~1.9 × the cup's weight (~19 N static, 2–3× that in bumps) **pushing the strut toward the grip's mouth**: the load is an ejection force, the same direction as the snap-off.
  A 1 mm lip on 2.5 mm walls snaps off at about the force it snaps on with, so that was too little margin. **Changes (clip only, the module is unchanged):** lips 1.0 → **1.6 mm** deep, walls 2.5 → **3.0 mm** (stiffer lips; holding force goes up ~2.8×, estimated),
  clearance 0.4 → **0.3 mm** (less rattle and cocking), grip 18 → **22 mm** long (less rocking), lead-in 1.2 → 1.6 mm (so it is still pressable). Lip bending strain ~2.5% (PETG is fine for this, not for repeated hard use). All interference checks still 0; overhang area 820.9 mm² (supports as before).
  Rebuilt `wagon-strut-grip-test.stl` as three lip depths at the new clearance. Fallback if it still pops: flip the C so its closed wall faces the cup and the mouth faces the bar (then the cup load pushes the strut into a solid wall; needs a leg re-route), or add a strap slot. Next: owner prints the grip test, then the full clip.
- **2026-11-03 (v8, strut grip flipped):** Owner printed v7.1: **still not enough holding force on the strut for a full cup**, and suggested flipping the clip so the cup's force pushes it on tighter instead of pulling it off. Agreed: lips can't solve it, because the cup's load
  (~1.9 × its weight at the grip) points straight at the mouth. **Redesign:** the C's **closed wall now faces the cup** and its **mouth faces the bar** (the lips sit in the gap between the bar and the strut). The cup's load now presses the strut into the 3 mm outer wall. The old inboard
  leg plate is gone (it would have blocked the new mouth); instead a **diagonal arm** (16 mm wide, Y 12.9–24 mm) runs from under the ring's outboard ear down and toward the pivot to the grip's up-slope side wall, staying on the ring side of the strut so it never crosses it.
  Install motion: in toward the wagon (strut into the mouth), then down along the strut until the ring clicks onto the bar from above. Checks all pass: clip vs strut/rail/tumbler/latch zones 0, module vs strut 0, module vs clip 0.002 cm³ (contact). Gap sensitivity: a 7 mm gap would need ~1.7° of rotation
  (the outer wall then sits against the strut face instead). Overhang 646 mm² (supports on). Grip test rebuilt (lips 1.2 / 1.6 / 2.0, mouth toward you). Not yet tested on the wagon. Next: owner prints the grip test, then the full clip.
- **2026-11-04 (vent hole):** Owner: **lifting the cup out sometimes brings the whole cup holder off the dovetail, and it "sticks" to the cup.** Likely cause (not confirmed): the pocket is closed at the bottom, so the tumbler's flat base seals against the floor and suction
  (plus friction in the taper) lifts the ~80 g module, which is held only by gravity. **Fix: a 10 mm vent hole through the floor on the cup axis** (`vent_d`). Module is still one watertight body (now genus 1), overhang unchanged (41.9 mm²), 0 interference with the tumbler,
  clip, rail and strut. The dovetail and the clip are unchanged. The module needs a reprint, or **drill a 10 mm hole through the middle of the floor of the printed one to test it first**. If it still lifts the module, next options are a dovetail retention (detent or magnets) or a looser pocket.
- **2026-11-04 (v8.2, pocket opened up):** Owner is pretty sure the sticking is **wedging**: the tumbler jams in the pocket and lifts the (gravity-held) module with it. The pocket followed the retailer taper with only 1 mm of room per side at every height, so a tumbler a
  little bigger than the listing (or tilted as it is lifted) binds. **Changes (module only):** `pocket_clearance` 2.0 → **4.0 mm** on the diameter at the floor, and new `pocket_draft` **0.02 mm per mm** of height, so the pocket is 74.0 mm at the floor and 85.4 mm at the rim (was 72 / 81.7 at the same heights:
  the tumbler is ~70 / ~79.7 mm there on the retailer numbers). That leaves about 2 mm per side at the floor and ~2.8 mm at the rim for a tumbler that is bigger than the listing, and the tumbler can tip ~2° without binding. Side effects: the cup axis moves out from 84.0 to **85.9 mm** from the rail (the strut and latch gaps get bigger),
  the module is 115.7 mm long (was 112.1; the zone checks still pass), and the cup is a little looser. All checks still 0 (tumbler, rail, clip, strut, latch zones), watertight, overhang 42 mm². The vent hole stays (it also drains water). The dovetail and clip are unchanged. Needs a module reprint.
  If it still drags the module up: a dovetail retention (detent or magnets). If it rattles: set `pocket_clearance` to 3.
