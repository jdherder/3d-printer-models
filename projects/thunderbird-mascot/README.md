# Thunderbird mascot figurine

A small standing figurine of the Black Bob Elementary Thunderbird, the costume mascot (red bird in a red "BB" ball
cap, big white beak, white chest burst and zigzag trim). Multicolour for the AMS: red, white, black.

![figure](renders/figure.png)

## Goal

A desk or shelf figurine that clearly reads as *our* Thunderbird. It's a chibi interpretation built in code, not a
scan, so the shapes are clean and easy to change by parameter. It's a sibling of `projects/black-bob-keychain` (the logo).

## Status

- [x] Source: `source/costume-photo-2026-11-14-instagram.png` (owner's screenshot of the school's Instagram post)
- [x] v1: chibi figure on a black base, 80 mm tall, 3 colours. Watertight, 0 self-intersections, colour bodies disjoint
- [ ] Owner review: likeness, proportions, size, a name on the base?
- [ ] Test print (P2S + AMS 2 Pro), then adjust

## Measurements

No real object: the size is our choice. **80 mm tall** (`HEIGHT_MM`) is a first guess for "little".

| Feature | Value (mm) | Notes |
|---|---|---|
| Overall W × D × H | 62.7 × 56.4 × 80.0 | Footprint = the base |
| Base | 62.7 × 56.4 × 5.2 | Black, rounded edge |
| Eyes | 5.4 tall | Black, Ø 1.5 white highlight, "friendly" (as the keychain) |
| "BB" on the cap | 4.4 tall | DejaVu Sans Bold (matplotlib's bundled font) |
| Claw tips | ~0.9 | Smallest feature |

Euler number of the merged solid is 0, not 2: base, leg, body, leg, base form one loop (a "handle"). That's expected.

## Print settings

- **P2S + AMS 2 Pro** (A1 + AMS lite works too): PLA, red / white / black. Indoors only, so PLA is fine.
- Open `output/thunderbird-mascot-multicolor.3mf`, load as one object with multiple parts, set the parts' filaments.
- Upright on the base. **Supports needed** under the beak, cap brim and wing tips: tree supports, "support on build
  plate only" will mostly do. 0.12–0.16 mm layers look nicer on the curves.
- Single colour: `output/thunderbird-mascot.stl`.

## Open questions

- Does it read as the Thunderbird? Beak shape/size, the white "goggle" face patch, the chest burst, leg length.
- Size: 80 mm OK, or bigger (100–120 mm is easier to paint/see, more filament and time)?
- Add a name on the base ("BLACK BOB" / "THUNDERBIRDS")? A pose (waving wing)? A tail?

## Pipeline

`build.py` (~45 s):
- **Shapes** are signed-distance fields, meshed by marching cubes (0.3 mm voxel) and decimated (pymeshlab): red body
  (torso + head + wings + tail + tongue, smoothly blended), red cap, white parts (beak, legs, feet), black claws. Eyes
  and highlights are analytic spheres (marching-cubes facets that small made sliver triangles).
- **Decals** are exact boolean regions that recolour the red skin: chest starburst, face goggles (`cone_decal`: the
  outline swept from a point inside the head, so its walls meet the surface squarely), zigzag hem and wing tips
  (`zigzag_region`), and the BB (cap only).
- **Colour bodies** (manifold3d): black = claws + eyes − highlights + base; white = white parts + highlights +
  decal regions − black; red = red − decals − white − black. Lessons: never subtract a solid that shares skin with
  the one it's cut from, avoid coplanar faces (claws are clipped 0.35 above the soles), scale *before* the booleans,
  and build the merged STL from the raw shapes, not the colour bodies.
- Every parameter is at the top of `build.py` in design mm (≈76 mm tall); `HEIGHT_MM` scales the result.

## Files

- `output/thunderbird-mascot-multicolor.3mf`: print this (3 parts)
- `output/thunderbird-mascot.stl`: single-colour solid
- `output/thunderbird-mascot-{red,white,black}.stl`: colour bodies
- `renders/figure.png`: front / three-quarter / side / back
- **Review page:** https://claude.ai/artifact/WYCbtWrxjguZYgr4q8fuSh (`renders/viewer.html`; republish to this URL)

## Log

- **2026-11-14 (v1):** Owner shared a photo of the costume mascot and asked for a little figurine. Built a chibi
  version: cap with BB, goggle face, hooked beak with the red mouth showing, chest burst, zigzag hem and wing tips,
  white legs and three-toed feet with black claws, black base. 80 mm tall. Published for review.
