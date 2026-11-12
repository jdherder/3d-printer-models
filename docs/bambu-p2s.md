# Bambu Lab P2S + AMS 2 Pro notes

The owner's second printer (added 2026-11). The design rules of thumb in
[`bambu-a1.md`](bambu-a1.md) apply here too. This page covers what's different.

- **Build volume:** 256 × 256 × 256 mm, the same as the A1, so the existing fit
  checks (`fits_A1_*` in `report.json`) hold for both printers.
- **Kinematics:** CoreXY, so the bed only moves in Z. Tall, narrow parts don't get
  the A1's Y-axis wobble.
- **Enclosure:** yes. This makes **ASA** (and ABS) practical for heat- and
  UV-exposed parts like car interiors and outdoor fixtures. Keep the door and lid
  closed for ASA/ABS and open for PLA.
- **AMS 2 Pro:** 4 sealed slots with active filament drying. Use it to dry
  PETG/ASA/TPU before a print. Multi-colour or multi-material prints are possible
  (for example, a support-interface material), but assume a single material unless
  the owner says otherwise. Keep TPU out of the AMS.
- **Slicer:** Bambu Studio, same as the A1.

## Which printer?

| Part | Printer | Why |
|---|---|---|
| PLA / PETG, everyday | Either | Same volume and same rules |
| ASA / ABS (car interior, hot sun, outdoor UV) | **P2S** | Needs the enclosure |
| Multi-material, or filament that must be dried | **P2S** | AMS 2 Pro |
| Tall and narrow | P2S preferred | No bed-slinger wobble |

Hardware details not recorded here (stock nozzle type, chamber heating, max
temperatures): confirm with the owner before relying on them.
