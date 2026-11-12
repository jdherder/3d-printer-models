# Black Bob Elementary keychain

A multicolour keychain of the Black Bob Elementary logo (the thunderbird in a cap, inside the red name ring), with
height steps between the colours. Several will print on one plate.

![top surface](renders/relief.png)

## Goal

A keychain that reads like the logo and feels layered: the red ring is a raised bezel, the letters are embossed, the bird
stands off a recessed white field, and the cap is the highest point (owner's pick, "style A"). The back is plain.

## Status

- [x] Source: `source/logo-2026-11-12-school-site-300px.png`, the school site's original upload. 300 px is the largest
      that exists there (Cloudinary returns the same 300 px for the untransformed original). `…-web-300px.webp` is the
      owner's lossy copy, kept for reference only.
- [x] v1: traced, style A heights, 60 mm, keyring tab. Watertight, 0 self-intersections, Euler 0 (the tab hole)
- [ ] Owner review of v1 (viewer link below)
- [ ] Test print (P2S + AMS), then adjust heights and line widths

## Measurements

No real measurements. The size is the owner's choice: "55 or 60 mm". **60 mm** was picked to keep the wing slits and tail rays printable.

| Feature | Value (mm) | Notes |
|---|---|---|
| Diameter (outside of the red ring) | 60.0 | `DIAMETER`. The logo's thin white outer rim is left off (~0.8 mm, too fragile/dirty on a keychain) |
| Overall incl. tab | 60 × 68 | |
| Heights (top of each colour) | red base 0.8, white field 1.8, cut-in white details 2.4, red ring 2.8, bird + outline + beak 3.0, letters 3.2, cap 3.4 | Style A |
| Colour depth | white 1.0, black 0.8 | Below that it's red (`COLOUR_DEPTH`), so fewer layers hold all three colours |
| Keyring hole | 4.0, 2.5 wall | Tab at 12 o'clock, outside the ring so it doesn't cut "BLACK BOB" |
| Black lines | ≥ ~0.6 | The logo's hairline outlines are ~0.35 mm at this size. Lines thinner than 0.6 grow 0.12 per side; wider black is untouched |
| White details in the bird | ≥ 0.45 wide | Narrower slits are dropped (become red) |

## Print settings

- **P2S + AMS 2 Pro** (A1 works too): red, white, black. PLA is fine. PETG holds up better on keys.
- Open `output/black-bob-keychain-multicolor.3mf`. If Bambu Studio asks, load it as one object with multiple parts,
  then set the parts: red, white, black. Flat, back down, no supports, 0.2 mm layers (17 layers).
- Layers 1–4 are all red. The colour swaps run from 0.8 mm up. For a plate of several, add copies in Bambu Studio:
  they share the swaps, so the purge per keychain goes down.
- Single colour: `output/black-bob-keychain.stl` (the relief still shows. Paint or ink the top if you like).

## Open questions

- Is the black outline too heavy? It had to grow to print. Alternative: drop the black and let the height step
  outline the bird (2 colours, much less purge).
- Should the heights be bigger? The total is now 3.4 mm.
- Is 4 mm right for their split ring?

## Pipeline

`build.py`: the logo is upscaled 4× (Lanczos), and each pixel is classified to the nearest of red, white or black. The circles are fitted to the
ring edges (the inner edge is ~0.5 px off-centre in the logo and is kept that way). Bird = the filled black outline. White
inside the bird splits into raised (beak and eye, `RAISED_WHITE_BOX_PX`) and cut-in (slits, bolt, tail rays). Letters =
white in the ring not connected to the field. The cap is a hand-drawn outline (`CAP_PX`). Contours are traced on a slightly blurred
mask and snapped to a 0.005 mm grid. Each colour body is built as stacked slabs per height step and unioned with manifold3d (unioning region by region left pinch points).

## Files

- `output/black-bob-keychain-multicolor.3mf`: print this (3 parts)
- `output/black-bob-keychain.stl`: single-colour solid
- `output/black-bob-keychain-{red,white,black}.stl`: colour bodies
- `renders/layout.png` (source vs colours vs heights), `renders/relief.png`, `renders/relief-head.png`, `renders/model.png`
- **Review page:** https://claude.ai/artifact/5FYvjmwh3QfyWj5R3MaU21 (`renders/viewer.html`; republish to this URL)

## Log

- **2026-11-12:** Workshopped options with the owner. Picked 55–60 mm, style A heights, plain back, several per plate.
  The owner sent the school site's image URL. Its original is also 300 px, but lossless, so it's the source. Built v1 at 60 mm and published the review page.
