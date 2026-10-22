# GATE RESULTS: female jaw + lips + skin/lip/eye shader, male reference pack (chat 7, 2026-10-17)

Reference: `ArtDir/style/alive/neutral-reference-pack-2026-10-15/sheets/07-head-skin-neutral.png`. Final geometry = sculpt pass 13
(`export/Female_s13.fbx`, blend `export/Female_FaceShader_s13.blend`). Unity proof = my APFS clone (`~/female-face-UnityClone`),
HeroTurnaround studio (game shaders, tennis light profile), body bind pose, Tan skin `E2A06E`, renders 1080x1080. Head height
crown->chin = 278.5 mm, so 2 % = 5.6 mm. Measured frame: the game's own face frame after `HeroFaceReferenceFit.Warp` (y up from the
sclera centroid, z forward, mm).

Proof images: `proof/04_final_vs_ref.png` (reference / game today / now: front, 3/4, profile + lower-face close-ups),
`proof/03_rig_expressions.png`, `proof/05_tones.png`, `proof/06_native_head.png`, `proof/01..02` (progress pushes).

## JAW: PASS
- Front jaw outline (z-buffer depth step jaw->neck, `tools/jawline.py`), rise above the chin vs reference parabola, x = 0..63 mm:
  max |diff| 3.9 mm (x 63), <= 2.5 mm for x <= 54. Gate 5.6 mm.
- Front silhouette half-width vs reference (crown+chin frame), y -67..-107 (lower cheek -> jaw): -3.0 .. -0.8 mm (was -6.0 .. -4.6).
  At y -62 (cheekbone level, outside the jaw zone) -4.3 mm.
- Profile, chin/under-jaw (z 1.430..1.460, crown+chin frame, horizontal from the cranium fit): 1.0 .. 3.7 mm behind the reference.
- Look: the front V to a narrow chin is now a rounder U; chin groove under the lower lip; chin pad ~1.8 mm back.

## LIPS: PASS (with the frame note below)
- Width (paint, corner to corner): 53.0 mm vs reference 53.3 mm scaled by eye spacing (-0.6 %).
- Height/width, measured the same way on both images (lip-colour threshold 0.40): 0.362 vs 0.371 (-2.4 %). Threshold-sensitive:
  0.38 gives -12 % (the reference's under-lip shadow joins the lip), 0.42 gives +0.8 %.
- Profile (midline, anchored at the identity-locked nose base, reference subnasale->menton scaled to ours): after - target at
  y -59..-125 within 1.14 mm (max, at the upper vermilion border, where the 60-degree crease guard holds it), mean 0.24 mm.
  Upper lip leads, stomion recessed, lower lip tucked 4-5 mm behind the upper lip, mentolabial groove ~3 mm (all were inverted or
  flat before: the lower lip stuck out past the upper).
- Cupid's bow + corners: painted bow (peaks at +-7.4 mm), near-flat seam, corners tucked (geometry 1.2 mm + paint).
- Frame note: in the cranium-anchored frame the lips sit 5-6 mm behind the reference, because the reference's whole midface
  (its nose too, 5-10 mm) projects further from its larger cartoon skull. Matching that would move her locked nose.

## IDENTITY: PASS (Adnan sign-off PENDING)
- Vertex movement outside the jaw/lip zone (`eval/s13_delta.npy`): max 0.20 mm. Eyes/brows region 0.03 mm, ears 0.17 mm, nose 0.19 mm,
  neck below the jaw 0.05 mm, skull 0. Gate 0.5 mm. 3,564 vertices moved, max 5.3 mm.
- Adnan was sent proof 01 and 02 during the run; no reply yet. Not read as a different person by me (same eyes, nose, ears, skull,
  proportions; see proof 04).

## RIG: PASS
- Unity import: Body v=34,443 t=68,476, 2 shape keys = identical to before (`eval/meshcount_before.txt`, `meshcount_s13.txt`).
  This matters: the shoulder-fit bank, cover masks and correctives are vertex-indexed. The first candidate imported 34,446
  (Unity splits vertices at folds past 60 degrees) and crashed `FemaleShoulderFit` in the locker export; fixed with the
  sliver / split guards (no edge changes side of 60 degrees: `tools/creases.py` NEW 0, LOST 0).
- Blink, smile, sad, shock, smile+blink: clean, no tearing, painted lips ride the skin (`proof/03_rig_expressions.png`).
- Neck seam: the head is one mesh with the body; neck vertices move <= 0.05 mm, no step.
- `HeroFaceReferenceFit` log in every run: belowHeadChanges=0, topology/weights/binds same.

## SKIN: PASS on face, lips and eyes; 1 FAIL line (neck)
CIEDE2000, reference patch vs the same region of the Unity front render (`eval/patches_final.json`, `tools/patches.py`):

| patch | before | now |
|---|---|---|
| forehead | 7.6 | 4.5 |
| cheek L / R | 3.3 / 2.6 | 1.6 / 1.4 |
| chin | 2.6 | 4.6 |
| upper lip | 6.2 | 0.4 |
| lower lip | 8.8 | 2.3 |
| iris (whole disk) | 16.2* | 1.6 |
| neck | 11.9 | **10.0 FAIL** |

*before value from a small box (the disk measure came later; the iris was visibly lighter and orange).
- Neck FAIL: in the reference the neck sits in the chin's cast shadow (its neck is 18 % darker than its cheek); ours is lit by the
  game key. Not faked with pigment.
- No yellow cast: forehead hotspot was pale/yellow (clipped red); now warm (sheen takes the skin hue), da/db within 3.6.
- All six palette tones checked (`proof/05_tones.png`): lips stay relative to the tone, no grey or yellow shift.

## NATIVE: PASS (staging export; install = chat 6)
- `tools/native.sh final`: `MatchHeroLockerExport.RunDistance` from the clone -> staging copy of CharacterAssets -> Unity
  `CaptureLobbyParity` vs the app's own SceneKit code (`lobby_render.swift`) with our `MatchHeroSurfaces.swift`.
- Female, 5 looks x 4 framings (body, head, torso, feet): luminance ratio 0.956..0.999, mean abs difference 3.8..9.0 / 255
  (`native/final/sheets/PARITY.md`); the hero-sync baseline was 5..13. Head sheet: `proof/06_native_head.png`. Residual: the
  iris reads a touch redder in SceneKit.
- The parity rig's framings are body/head/torso/feet, not the sheet's 0/45/90 cameras.

## PERFORMANCE (60 fps @ >= 1080p request): PASS on this Mac, device NOT RUN
- `unity/FemaleFacePerf.cs`, Unity Metal (Apple M5), 1920x1080 MSAA 4, both heroes, 400 frames synced by readback:
  before 11.6 ms (pair) / 9.6 ms (face fills frame); after 9.5 / 7.5 ms. No measurable cost (run noise > difference).
  The change is a few ALU ops in the female face/eye branches: no texture, no pass, no keyword.
- Face textures untouched (no new compression). iPhone/Apple TV timing not run.

## MALE_PACK: PASS (Adnan accepted 2026-10-17; sent to garment-pipeline)
- `ArtDir/style/alive/male-reference-pack-2026-10-17/`: 14 sheets incl. 13 tennis-shoe and 14 golf-shoe detail sheets, sources,
  GENERATION_PROMPTS.json, MANIFEST.json, START_HERE.md, GATE_RESULTS.md, proof/contact-sheet.jpg.
- Generated with Adnan's OK on the connected image service (GPT Image 2.5 medium, refs = locked male plates), ~14 credits.
  3 sheets regenerated once (layout copy / lost colours). Hand-off to garment-pipeline after Adnan accepts it.

## Not done / open
- Lobby re-export and goldens/provenance (shared files, chat 6): until it runs, the native freshness tests flag the changed
  look sources.
- Eye: the sclera's grey band under the upper lid is mostly the lid geometry's own shadow; softened but still wider than the reference.
- The reference's bold winged eyeliner was not copied (identity/style call): the lash line is darker and sits on the lid edge.
