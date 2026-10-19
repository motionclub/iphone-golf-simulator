# Female face: jaw + lips + skin/lip/eye shader (chat 7, 2026-10-17)

Brief: `work/delegation-2026-10-17/07_female_face_shader_male_refs.md`. Reference: `ArtDir/style/alive/neutral-reference-pack-2026-10-15`
(sheet 07 head/skin, S1/S2 for appeal). Gates: `GATE_RESULTS.md`. Working notes: `NOTES.md`.

## What changed

| Part | File (installed path) | Work copy |
|---|---|---|
| Head geometry: jaw + lips sculpt | `Unity/Assets/Resources/Tennis/OriginalSeamBlinkFinish/Female.fbx` | `export/Female_s13.fbx`, blend `export/Female_FaceShader_s13.blend` |
| Lip outline + lip pigment form, lash line, forehead lift | `Unity/Assets/Resources/Tennis/Shaders/HeroFaceSkin.shader` | `unity/HeroFaceSkin.shader` |
| Warm female satin highlight | `Unity/Assets/Resources/Tennis/Shaders/HeroLighting.hlsl` | `unity/HeroLighting.hlsl` |
| Sclera lid shadow, iris depth, pupil | `Unity/Assets/Resources/Tennis/Shaders/TennisCharacter.shader` | `unity/TennisCharacter.shader` |
| SceneKit port of all of the above | `GolfArcade/Unity/MatchHeroSurfaces.swift` | `unity/MatchHeroSurfaces.swift` |

All shader changes are inside the female branches (`_SkinFinish > 1.5`, `_FemaleSurface`/`_FemaleEyeRole`, Swift `!maleFace`,
`skinFinish > 1.5`, `femaleEyeRole`). Male output is unchanged. Originals: `unity/before/` (+ `SHA256.txt`).

## The sculpt (`tools/sculpt_mouth.py`, params `sculpt_p13.json`)

Runs headless on the production head (`work/jaw-sculpt-2026-10-12/Female_JawSculpt.blend`, = installed FBX), in the game's own face
frame (numpy port of `HeroFaceReferenceFit.Warp`, so what is measured is what Unity draws).

1. Upper vermilion border loop slides down to the reference lip proportions (tangential, the loop already existed in the mesh).
2. Midline profile pulled to the reference profile (anchored at the nose base, which is identity-locked): upper lip leads, stomion
   deeper, lower lip tucked behind the upper, a real mentolabial groove, chin pad ~1.8 mm back. Lateral falloff follows the lip
   outline / chin width.
3. Jaw edge out up to 4.5 mm at the jaw angle (front silhouette was 4–6 mm narrower than the reference), fading to zero at the chin
   centre, above the cheek and on the neck.
4. Topology guards. Unity splits vertices at edges past its 60-degree smoothing angle, and the shoulder-fit bank, cover masks and
   correctives are indexed by the imported vertex count (34,443). So: no edge may change side of 60 degrees. `sliver_fix` keeps
   near-degenerate triangles flat, `sharpen_lost` keeps the source's few 62-63-degree creases (vermilion border) past 60,
   `split_guard` moves any remaining changed hinge rigidly. Verified in Unity: Body v=34443 t=68476 (`eval/meshcount_*.txt`).
5. Shape keys get the same delta (blink unchanged), authored custom normals rotated with the surface. Runtime expressions
   (`Face_Smile/Sad/Shock`) are generated from face position and need nothing.

## Lip paint (shader, both engines)

Mouth half-width 26.5 mm, near-flat seam; upper .33(1-u^2.8)^1.5 + cupid's bow, lower .47(1-u^3.4)^1.9 (fit to sheet 07 lip
outline, +6% fullness). Colour relative to the selected skin tone; lower lip lit upper-middle and deeper at its bottom edge and
corners, upper lip deeper by the seam, soft shadow under the lower lip. A screen-space bump was tried and rejected: it banded at
2 px on lip scale.

## Tools

`tools/measure.py` (game-preview silhouettes + stills), `align2.py`/`table.py` (reference overlays in the crown+chin frame),
`jawline.py` (front jaw outline from a z-buffer), `creases.py` (60-degree split check), `export_female.py` (same FBX options as the
10-12 jaw sculpt), `review_state.sh` + `unity/FemaleFaceReview.cs` (Unity matched views / rig / tones), `unity/FemaleFacePerf.cs`
(1080p timing), `unity/FemaleFaceMeshCount.cs`, `patches.py` (CIEDE2000 skin/lip/iris patches), `native.sh` (staging-only lobby
parity: export + SceneKit render with our Swift, nothing installed). Unity clone: `~/female-face-UnityClone` (tmp was wiped by restarts).

## Install / rollback

Install = copy the five work files above over their installed paths (owned by this chat), stage them by explicit path.
Rollback = copy `unity/before/*` back (shaders, Swift); the FBX: `git checkout HEAD -- Unity/Assets/Resources/Tennis/OriginalSeamBlinkFinish/Female.fbx`
(HEAD = the 10-12 jaw-sculpt head, sha 8f6be393…). Installed hashes: `INSTALL_SHA.txt`.

Not done here (shared, chat 6 / hero-sync owns it): the lobby re-export (`work/hero-sync/sync_heroes.sh`: CharacterAssets, goldens,
provenance). Until it runs, `testNativeHeroesMatchTheCurrentUnityHeroLook` and the head-FBX provenance test will report the
change. `native/final/` shows the SceneKit result from a staging export.
