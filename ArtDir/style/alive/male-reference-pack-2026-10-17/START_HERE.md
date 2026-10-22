# MALE HERO REFERENCE PACK (2026-10-17)

Companion to the female pack `ArtDir/style/alive/neutral-reference-pack-2026-10-15`, same format and rules. Made for the garment
pipeline (male clothes, tennis + golf shoes) and any male look work. Identity source: the locked male plates
`ArtDir/hero/base_lock/male_body_plain.jpg` and `male_head_detail.jpg` (copies in `sources/`).

## What governs what
1. **Identity:** the locked plates in `sources/` and the current in-game male hero. These sheets are AI approximations; they never
   override his face, head, body proportions or age. Same adult man, bald, ~1.75 m.
2. **Tennis construction master:** `01-tennis-cardinal-master` (front/side/back). **Golf master:** `03-golf-cardinal-master`.
   Front and back are the main anchors; sides cross-check depth.
3. **Garment detail:** `09-tennis-polo-construction` (collar tipping, 2-button placket, cuff thickness + air gap, hem out),
   `10-golf-polo-construction` (collar stand + underside, 3-button placket, cuffs, tucked hem),
   `11-shorts-trousers-construction` (shorts waistband/side vents/hem; trousers belt, loops, crease, hem break).
4. **Shoes (dedicated):** `13-tennis-shoe-detail` (herringbone outsole, EVA midsole + toe spring, toe bumper, perforated panels,
   heel counter + tab, padded collar, laces, tongue) and `14-golf-shoe-detail` (low midsole, spiked outsole with traction lugs,
   saddle panel, toe cap, heel counter, laces). Six views each: lateral, medial, front, back, top, sole.
5. **Head/cap:** `07-head-skin-neutral` (bald head, six views), `08-head-cap-neutral` (six-panel cap, curved bill with thickness,
   back strap; cap is a separate removable item, bald scalp underneath).
6. **Supplementary:** `02/04` obliques, `05/06` elevation studies (camera height is approximate), `12-hands`.
   If a supplementary sheet disagrees with a master (seam, panel, pleat, shoe panel), reconcile to the master and to one 3D object.
   Never build different geometry per camera.

## Rules (same as the female pack)
- Clothing colours are examples only. Every garment colour stays customizable; geometry, construction, thickness and material
  response carry the look in light, dark and saturated colours.
- Real separate garments with thickness and air gaps, not the body surface pushed out. Hem over/under the waistband as drawn.
- Neutral A-pose; do not rebind the rig to the drawings; pose the rig to compare.
- These are generated images, not calibrated orthographic captures, topology or animation proof. Fine details (lace count, spike
  count: 6 drawn vs 7 asked) can vary between views.

## Files
`sheets/` (14 PNG: 01-06 at 1024x688, 07-14 at 2048x1360), `sources/` (the two locked plates), `GENERATION_PROMPTS.json` (exact
prompts, settings, job ids, the three sheets regenerated and why), `MANIFEST.json` (sizes + SHA-256), `proof/contact-sheet.jpg`,
`GATE_RESULTS.md`.

## Added 2026-10-17 (chat 11, male face/body to ref)
- `15-body-cardinal-no-clothes` (front/right/back/left) and `16-body-obliques-no-clothes` (45/135/225/315): the bald male with no
  clothes, plain smooth grey base body like `male_body_plain.jpg`, skin-toned head. **Body master = 15**; 16 is supplementary
  (reads a little more muscular than 15: reconcile to 15 and the plate).
- `17-face-detail-neutral`: closer face set (front, 3/4, profile, plus jaw/chin front, lips front, jaw+lips profile close-ups), shirtless
  neck/shoulders, generated from the head plate + sheet 07.
- Same generator and settings (GPT Image 2.5 medium 2k); prompts in GENERATION_PROMPTS.json; 4 credits (15 regenerated once: the first
  was bodybuilder-heavy).
- **Body decision (Adnan, 2026-10-17):** keep the locked body plate `ArtDir/hero/base_lock/male_body_plain.jpg`. Do NOT bulk the body toward
  sheets 15/16 (they read broader/more muscular than the plate: traps, shoulders, delts, flatter belly). Use 15/16 for form reading only.
