# GATE RESULTS: male face + skin/lip/eye shader to the male reference pack; body compared (chat 11, 2026-10-17)

References: `ArtDir/style/alive/male-reference-pack-2026-10-17` sheet 07 (head/skin), new sheet 17 (face detail, jaw/lip close-ups), new
sheets 15/16 (no-clothes body), locked plate `ArtDir/hero/base_lock/male_body_plain.jpg`. Adnan 10-17: "match ref on all three" (eyes,
skull width, ears). Measured in the game's own face frame (mm from the source eye line, the numpy port of `HeroFaceReferenceFit.Warp`
in `tools/off.py`), sheet 07 mapped crown+chin (head 253.8 mm; 2 % = 5.1 mm). Unity proof = `~/male-face-UnityClone`, HeroTurnaround
studio, game shaders, Tan `E2A06E`, 1080x1080. Final state = sculpt s13 (`export/Male_s13.fbx`) + warp constants + shaders (review s14).

Proof: `proof/06_final_vs_ref.jpg` (ref / before / now: front, 3/4, profile), `proof/07_lower_face_ref_before_now.jpg` (sheet 17 jaw+lips
/ before / now), `proof/04_rig_expressions.jpg`, `proof/05_tones.jpg`, `proof/01..03` (progress pushes), native sheets
`native/final/sheets/tennis_male_head.png`, Phase 0 sheets `ArtDir/.../proof/contact-sheet-15-17.jpg`.

## REFS (phase 0): PASS
- Sheets 15 (body cardinal, no clothes), 16 (body obliques), 17 (face detail + jaw/chin, lips, jaw+lips profile) added to the pack,
  MANIFEST/GENERATION_PROMPTS/START_HERE/GATE_RESULTS updated. 4 credits (estimate given first: 3-6; 15 regenerated once, first try
  bodybuilder-heavy).

## JAW: PASS
- Front jawline (z-buffer face->neck edge, `tools/jawline.py`) vs the sheet-07 jaw edge (luminance step under the jaw), x = 24..63 mm:
  max |diff| 3.3 mm (was 6.5), mean 1.4 mm. Our jaw now rises toward the ear like the reference (was ~6 mm low at x 39-63: a square base).
- Profile chin / under-chin (y -92..-132): max 1.6 mm, rms 0.7 (was 7.4 / 4.6: chin and mentolabial area 4-7 mm too far forward).
- Jaw edge smooth (one broad taper move instead of local bumps; `eval/lowerface_s13.jpg`).

## LIPS: PASS
- Profile y -60..-92: max 4.5 mm, rms 2.4 (was 5.0 / 3.2): upper lip now leads the lower lip (it was inverted: lower lip 2 mm ahead).
- Paint (HeroFaceSkin + SceneKit): seam straight with corners 1 mm down (was 3.5 mm up = a smile); thin bowed upper lip 5.0 mm centre /
  6.8 mm at the bow peaks (ref ~5.9 / 7.9), fuller lower lip 10.5 mm (ref ~9.8); width 70 mm (ref 66-70). Upper lip deeper/browner than
  the lower like the reference. The mesh's old upturned corner groove is softened (smoothing brush), still faintly visible in close-up.

## FACE_OTHER: PASS (nose tip + ear lobe residuals listed)
- Eyes: opening 33 x 12.5 mm (ref ~33 x 12; was 42 x 23), iris ~14 mm (ref ~14; was ~24), eye line at 47 % of crown-chin like the ref
  (was 51 %: the warp's 10 mm "Settle" drop is off for the male). Lash line darker/wider + upper-lid crease shadow; sclera 3 % inset so
  no white specks at the corners.
- Skull: front half-width y +14..+110 max 1.3 mm, rms 0.7 (was 9.5 max: 8.5 % warp widening -> 2 % narrower than source).
- Ears: full size (shrinks 2 x 14 % -> 2 x 2 %), 4 mm lower: span y +10..-64 (ref +8..-64; was +12..-61). Eye/ear band front max 5.5 mm,
  rms 2.5 (was 10.3 max).
- Nose: profile y -20..-52 max 3.2, rms 1.2 (was 9.7 / 6.6: bridge 5-10 mm low); nose base -52..-60 max 4.0 (columella notch of the ref).
  Wings wider/fuller (warp narrowing .24 -> .10). Brow/nasion max 1.8 (was 4.7).
- Cheek/mouth band front max 2.9 rms (worst row 8.2 mm was the old ear lobe, now fixed by the ear drop: 5.5).

## IDENTITY: PENDING (Adnan sign-off)
- Same bald man, brows, eye colour, ears, skull shape class; changes are the ones Adnan asked for (eyes, skull, ears to the ref).
  Proofs 01-03 + 06 pushed. Head below 15 cm under the eyes moves <= 0.015 mm (neck, collar zone untouched).

## RIG: PASS
- Unity import: Body v=44,168 t=87,566, 2 shape keys = identical to before (`eval/meshcount_before.txt` vs `meshcount_s13.txt`).
  Guard (`tools/sculpt_off.py split_guard_scale`): no edge crosses Unity's 60-degree split angle in the basis OR the blink keys
  (the first export, basis-only guard, lost 6 splits = 44,162).
- Blink, smile, sad, shock, smile+blink clean, no tearing (`proof/04_rig_expressions.jpg`). Neck seam: one mesh, neck verts moved
  <= 0.015 mm. HeroFaceReferenceFit runs on the new constants (no exceptions in any review log).

## SKIN: PASS on face/lips/chin; FAIL lines: upper-lip stubble 5.1, jaw R 6.3, neck 12.3
CIEDE2000, landmark-anchored patches (eye line, nostrils, mouth seam, chin), sheet-07 front vs Unity front (`eval/patches_s14.json`):

| patch | before (m0) | now |
|---|---|---|
| forehead | 2.3 | 2.5 |
| cheek L / R | 3.4 / 3.1 | 4.6 / 3.0 |
| upper-lip stubble | 15.2 | **5.1** |
| upper lip | 18.1 | 4.6 |
| lower lip | 2.7 | 3.6 |
| chin stubble | 3.4 | 3.8 |
| jaw stubble L / R | 8.5 / 11.5 | 2.2 / **6.3** |
| neck | 13.0 | **12.3** |
(both columns: same landmark method, `eval/patches_m0_lm.json` / `eval/patches_s14.json`; before rows: eye 549 / nostril 675 / seam 748)
- Jaw R vs L: the studio key comes from the hero's left, the reference is lit frontally; their mean is 4.3.
- Neck: as for the female, the reference neck sits in the chin's cast shadow; not faked with pigment.
- Male cheek blush (pink apples) removed; stubble now visible (neutral grey-brown, densest on the upper lip). All six palette tones
  keep lips/stubble relative to the tone (`proof/05_tones.jpg`).

## NATIVE: PASS (staging export; install = chat 6)
- `tools/native.sh` + `tools/native2.sh`: `MatchHeroLockerExport.RunDistance` from the clone -> staging copy of CharacterAssets ->
  Unity `CaptureLobbyParity` vs the app's SceneKit code with our `MatchHeroSurfaces.swift`. Male, 6 looks x 4 framings: luminance ratio
  0.959..0.990, MAD 4.9..10.3/255 (head 4.9..6.5); hero-sync baseline 5..13. `native/final/sheets/PARITY.md`.
- To export at all, the clone needed male-garments-refpack's prefab patch (their garments are installed, the prefab patch is not:
  RunDistance threw on `KitV2 Kit_Sock_L [gp]`, 3 bones / 2 bindposes). Resolved 10-18: male-garments-refpack applied the prefab patch
  to the working tree; RunDistance passes there.

## PERF: PASS on this Mac, device NOT RUN
- `unity/MaleFacePerf.cs`, Metal (Apple M5), 1920x1080 MSAA 4, both heroes, 400 frames synced by readback:
  before 6.23 ms (pair) / 5.92 ms (male face fills the frame); after 5.81 / 5.50 ms. No measurable cost (noise > difference).

## GARMENT_FIT: PASS for clothes; cap = follow-up
- Body vertices below 15 cm under the eyes (collars and everything worn) move <= 0.015 mm; polo collar renders clean (proof 06 bottom row).
- Caps (HeroAccessories, fitted 10-13 to the old skull): the bill now sits on the brows exactly as in reference sheet 08; the band
  stands a little off the narrower temples. A re-hug with `work/accessories/py/cap_export.py` on the new head is proposed as a follow-up.

## BODY: PASS vs the locked plate (Adnan 10-17: "Keep the body as is (the plate governs). Don't change the body.")
- Torso/leg widths (centre-line runs, crown..sole = 1) vs the plate `male_body_plain.jpg`: within -6..+8 % at every torso/leg row
  (neck, feet and the plate's separated-arm rows excluded); the base_lock gates passed on this body earlier.
- Vs the new sheet 15 (a bulkier AI build): traps -33 %, shoulders -10 % (front) / -15 % (side), mid-chest -6 %; side: waist +15..17 %
  deeper, seat +27 %, shin +23 %. Pack rule (START_HERE): the sheets never override the locked plate's body proportions. Adnan chose
  the plate; sheet 15/16 stay as a muscle/form reference only. Body not changed.

## Not done / open
- Lobby re-export (shared CharacterAssets, goldens/provenance): chat 6. Until then the native freshness tests flag the look sources.
- Cap re-hug to the narrower skull: running in its own session (re-hug-male-tennis-golf).
- Nose tip definition and nostril shape are still simpler than the reference; mouth-corner groove faint.
