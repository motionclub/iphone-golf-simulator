# Male face painted-form pass (2026-10-18 night) — step 1 of work/male-audit-1018/AUDIT.md

**Status (10-19 01:xx): INSTALLED in `Unity/` + mirrored to the lobby (Swift) + lobby re-synced. Not staged, not committed.**
Installed: shaders HeroFaceSkin / TennisCharacter, scripts MatchHeroLook / HeroFaceReferenceFit / MaleFaceFinish (+ new .meta), exporter
MatchHeroLockerExport (exports `maleFormPass`, runs MaleFaceFinish like FemaleGarmentFinish), GolfArcade MatchHeroData / MatchHeroSurfaces
(male pass port: light model, nose/lip/ear paint, lid crease, form weights, neck, no stubble, saturation, ambient + nose bounce; male eye
tuning in the eye modifiers), work/hero-sync/look_sources.txt (+MaleFaceFinish). Hashes `install/INSTALLED_SHA.txt`; rollback = copy
`install/backup_1019_0054/*` back (and re-run sync_heroes.sh). sync_heroes.sh: 36 CharacterAssets files, goldens + provenance (220 guarded
sources); lobby vs game male head lum .96-.99, MAD 4.6-6.6 (baseline 5-13), `proof/install/`. EditMode 617/617 (tests/editmode).
Not run: Xcode native tests (VisualOverhaulNativeTests), device build. The lobby has no camera-side fill light, so the game's fill x.40 has
no Swift counterpart.

## What changed (male only; the female renders pixel-identical, mean diff 0.000-0.001)
| File (work copy in `unity/`, originals in `unity/orig/`) | Change |
|---|---|
| `MaleFaceFinish.cs` (new) | Male twin of FemaleGarmentFinish's eye part: bind-pose eye frame on `OriginalSeamFeatures`, sclera/iris/pupil get the eye-depth path (`_FemaleSurface` 3 = male tuning), body skin gets `_MaleFormPass` 1 |
| `MatchHeroLook.cs` | one line: `MaleFaceFinish.Attach(this)` after `HeroShoulderDeformation.Attach` |
| `HeroFaceSkin.shader` | `_MaleFormPass` switch: female light model (Lambert core + warm terminator), camera fill x.40, form ambient, rim .65, saturation floor .86; painted nostrils, alar crease, sub-nasal shadow, nasolabial fold, mouth-corner shadows, rosier lips, ear warmth + concha, warm brown-grey stubble with an edge (`_MaleBeard`), sharper lid crease; the neck form term no longer paints a hard rectangle to the chest |
| `TennisCharacter.shader` | male eye tuning under `_FemaleSurface` > 2.5: lash line on the eye's top edge, lower-lid rim, socket corners, caruncle, warmer lighter iris (`_MaleLash`) |
| `HeroFaceReferenceFit.cs` | `MaleEyeTall` 1.10 → 1.18, `MaleIris` 1.0 → 1.12 (vertex positions only, mesh counts unchanged); **nose (Adnan: "way too pointy")**: lower nose flared sideways (`MaleFlare*`), tip broader/lower/taller (`MaleTipW/Y/H`, `MaleTip` .032), bridge + dorsum broader, blend .85, no narrowing, wing bump out to ±26 mm, nose floor -.060/-.0555 |
Paint positions were read off a paint-frame grid render (`proof/z_grid2.jpg`, `z_grid3.jpg`), not guessed.

## Nose (round 2, same night)
Ref (sheet 17, crown-chin = 253.8 mm): wings ±22-24 mm (game was ±12), a round bulb that holds its projection to y -54 then tucks under
(game peaked at -42 and sloped back = a beak, up to 12 mm short under the tip). Fitted offline with chat 11's numpy warp port + renderer:
`tools/nose_model.py` (warp + flare/tip params), `nose_off.py` (views + ref row), `nose_ref.py` (sheet-17 profile), `nose_fit.py` /
`nose_search.py` (profile rms). Result: profile within ~1.3 mm along the whole nose, -0.3 mm at the base; width matches. Nostril / wing-crease
/ columella paint re-placed with paint-frame grid renders (`proof/z_ngrid.jpg`; the paint rides the pre-warp coordinates, so the wing edge
is paint ±19.5 mm). Proof: `proof/NOSE_FINAL_1.jpg` (front, 3/4), `NOSE_FINAL_2.jpg` (profile, 315), `NOSE_FINAL_3_close.jpg`; renders n0 → n8.

## Nose round 3 (Adnan: "looks ugly now, make it realistic")
Round 2's Gaussian flare made one wide blob. Replaced by an anatomical nose (`HeroFaceReferenceFit.MaleNose`, designed offline in
`tools/nose2.py`): a ridge on the sheet-17 midline profile (bridge ±7 mm, ball-shaped tip lobule ±8.5 mm), two alar lobes (±16 mm, set back
10 mm, smooth rims), smooth-max union so the creases are geometry, union with the cheek; round-2 Gaussian constants reverted to 10-17.
Then 2 Laplacian relax passes over the nose zone and normals recomputed from the new geometry there (one winding sign voted over the zone).
Bugs found on the way (all fixed): Unity `Vector3.normalized` returns zero under 1e-5 (black spots); orienting new normals by the imported
normal flipped the old nostril pockets (dark marks); the carve next to the base folded the columella; pulling the nostril rims folded the walls.
Gates: offline folds 1 (inside a nostril cavity, back-facing), turned >60° 42 of 2080 nose triangles; profile still on sheet 17;
female pixel-identical. Paint: nostrils + columella + tip highlight on the real underside (grid `proof/z_g.jpg`), warm bounce under the nose.
Proof: `proof/NOSE3_1_front_tq.jpg`, `NOSE3_2_profile.jpg`, `NOSE3_3_close.jpg`, `NOSE3_rig.jpg` (renders m1 → m13, final f1).
Tools: `nose_contour.py` (depth contours offline), `nose_folds.py` (fold gate), MaleFaceReview `nose` set (+ NOSE_OBJ=1 exports the game mesh).

## Round 4 (Adnan: nose sides not smooth, cheekbones too pronounced, one emotion only)
- The game re-derives head normals after the warp (HeroSkinNormals area-continuous, 12 mm, keeps creases > 45 deg), so side-wall lines were
  real geometry. Fix: 8 extra relax passes on the nose side walls only (offline gate `SIDES=1 tools/nose_folds.py`: edges > 20 deg 57 -> 13,
  > 30 deg 16 -> 2, none > 45; 0 folds); tip, wings and profile unchanged.
- Cheekbones: malar push .0035 -> .0015 (warp), 4 relax passes over the cheeks (`MaleCheekZone`, above the jaw rows), cheek-hollow paint
  .60 -> .25, stubble edge softer (`_MaleBeard` .05/.60) and lighter on the upper cheeks (it outlined the cheekbone).
- Expressions: evaluated neutral only from here on (Adnan). Proof: `proof/R4_1_front_tq.jpg`, `R4_2_nose_sides.jpg`,
  `R4_3_session.jpg` (sheet 17 / start of 10-18 / now), `R4_4_tones.jpg`; renders c1, c2, final f2. Female pixel-identical.

## Round 5 (Adnan 10-19: stubble; the nose's bottom sides read as separate circles)
- Nose base: the wing lobes now flow into the tip at the bottom (smooth-max blend 1 mm along the wing tops -> 6 mm toward the base,
  `AlaBaseBlend`), wings a little lower/inward (`AlaX` 14.5, `AlaY` -50.5, `AlaRY` 7.5): one rounded base, crease only above the wings.
  Offline: 0 folds, steep triangles 40 -> 10 (b3 in nose/).
- Stubble (male pass): sheet-17 coverage (upper lip, chin, jaw, lower cheeks, back to the sideburns), darker grey-brown (.70/.64/.58),
  3 mm mottle + fine grain (`_MaleBeard` .10/.55/.85/.9), wide depth feather (a narrow one drew a line in front of the ear).
- Proof: `proof/R5_1_face.jpg`, `R5_2_nose_base.jpg`, `R5_3_profile_lips.jpg`, `R5_4_session.jpg` (start of 10-18 / now), `R5_5_tones.jpg`;
  final render f3; female pixel-identical; neutral expression only.

## Round 6 (Adnan 10-19: "stubble looks horrible, look at the ref"; nose has no nostrils)
- Stubble rebuilt: no square cells, no 3 mm mottle. Even grey-brown tint (.70/.67/.64) over sheet-17 coverage (upper lip with a clean gap
  under the nose, chin, jaw, lower cheeks), plus round ~0.3 mm hair grain from smooth noise that fades to its average when a pixel spans
  several hairs (`foot` = bind-pose footprint).
- Nostrils: teardrop crescents (deep at the outer end, tapering up to the columella), near-black, soft shading into the opening, lit alar
  rims; the nose underside gets a stronger warm bounce so they read against skin, not shadow. Placed from a 1 mm grid (`proof/z_q.jpg`).
- Proof: `proof/R6_1_stubble.jpg`, `R6_2_nose.jpg`, `R6_3_tones.jpg`, `R6_4_dressed.jpg`; final render f4; female pixel-identical.
- Limit: the nose is a warp of the existing mesh plus paint; the ref's sculpted alar rims and open nostrils would need a Blender sculpt
  (vertex-count guard 44,168, see male-face-body).

## Round 7 (Adnan 10-19: remove the stubble; above the lip looked disfigured and blurred)
- Stubble off (`_MaleBeard.z` 0; the code stays for later).
- Philtrum: 12 relax passes from the nose base to just above the lip (`MalePhiltrumZone`): the source mesh's sharp ridges there showed as
  light vertical streaks (the game keeps creases over 45 deg hard; offline over 45 deg 24 -> 0, no folds). Every vertex any region moved
  now takes its full geometric normal (a partial blend at the zone edge kept warp-Jacobian normals: light drips under the columella).
  Nostril-rim highlight and underside bounce no longer spill onto the philtrum.
- Proof: `proof/R7_1_lip.jpg`, `R7_2_face.jpg` (start of 10-18 / now), `R7_3_profile.jpg`; final render f5; female pixel-identical.

## Round 8 (Adnan 10-19: "it's wrinkled ... might be the lips")
- Roughness map (`tools/rough_map.py`) + lower-face renders (`tools/low_view.py`): the source mouth was lumpy (wavy lip outline, corner
  creases, zigzag seam), the chin's underside scalloped, cheeks banded. Fix in the warp post-step: 8 relax passes over the mouth area
  (`MaleMouthZone`), 4 along the jaw underside (`MaleJawUnderZone`), then a clean lip volume (`MaleLips`: upper bulge 3.2 mm with a slight
  bow, lower roll 3.0 mm, soft 1 mm seam; seam y -78.5 face frame = paint -70); cheek zone widened to the jaw angle/jaw line, 6 passes.
  Jaw half-width changes <= 2 mm. Painted nasolabial fold at 30 %, smile-line form .35 -> .12.
- Proof: `proof/R8_1_front.jpg`, `R8_2_tq.jpg`, `R8_3_mouth.jpg`; final render w2; female pixel-identical.

## Proof (`proof/`)
`FINAL_1_front_tq.jpg`, `FINAL_2_eyes_lips.jpg`, `FINAL_3_lower.jpg` (sheet 17 / before / after), `p4_tones.jpg` (six skin tones),
`p4_dressed.jpg` (cap + polo), `p5_rig.jpg` (blink/smile/sad/shock), `p5_neck.jpg` (neck band gone). Progress p1-p4 in `cmp_*`.
Before = `../male-audit-1018/unity_out/now` (same tool, same tree).

## Loop
`tools/cycle.sh <tag> [AUDIT_SETS=views,tones,dressed,rig,body,female]` copies `unity/` into the clone and renders; `tools/cmp.sh <tag>`.
The `HeroFaceSkin` "All subshaders removed" import warning is pre-existing (the original shader gives it too, `logs/origcheck.log`).

## To install (needs Adnan's go)
1. Copy the 5 files into `Unity/Assets/...` (shaders → `Resources/Tennis/Shaders`, scripts → `Scripts/Tennis`); backup = `unity/orig/`.
2. Port to `GolfArcade/Unity/MatchHeroSurfaces.swift` (male face body + male eye path), then `work/hero-sync/sync_heroes.sh`
   (re-exports the lobby heroes with the new eye geometry; the native look-source guard test fails until this runs).
3. EditMode tests + a lobby-vs-game parity sheet.
Not in this pass (AUDIT steps 2-5): brow height / far brow poking out at 3/4, jaw kink, shoes, polo, cap.
