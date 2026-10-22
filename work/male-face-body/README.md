# Male face + skin/lip/eye shader to the male reference pack (chat 11, 2026-10-17)

Brief: `work/delegation-2026-10-17/11_male_face_body_to_ref.md`. Gates: `GATE_RESULTS.md`. Method copied from `work/female-face-shader`.

## What changed (installed + staged)

| Part | Installed path | Work copy |
|---|---|---|
| Head sculpt: nasion, upper lip forward, lower lip / mentolabial / chin back, jaw taper toward the ear, mouth-corner groove softened | `Unity/Assets/Resources/Tennis/OriginalSeamBlinkFinish/Male.fbx` | `export/Male_s13.fbx` (+ `.blend`) |
| Male face-fit constants: eyes to source size + height, skull 2 % narrower (jaw/neck keep the old width), ears full size and 4 mm lower, straighter higher nose (dorsum target, tip .024, pull .70 ending above the lip, wider wings), sclera 3 % inset | `Unity/Assets/Scripts/Tennis/HeroFaceReferenceFit.cs` (male consts at the top) | `unity/HeroFaceReferenceFit.cs` |
| Male skin: frame remap (eyes no longer lowered), lips (shape, straight seam, colour), stubble, no pink blush, darker lash line + lid crease | `Unity/Assets/Resources/Tennis/Shaders/HeroFaceSkin.shader` | `unity/HeroFaceSkin.shader` |
| Same frame remap for the body skin path | `Unity/Assets/Resources/Tennis/Shaders/TennisCharacter.shader` | `unity/TennisCharacter.shader` |
| SceneKit port of all shader changes | `GolfArcade/Unity/MatchHeroSurfaces.swift` | `unity/MatchHeroSurfaces.swift` |

All shader/Swift changes are in male branches (`_SkinFinish` .5..1.5 / `maleFace`); female output unchanged. Originals: `unity/before/`
(`SHA256.txt`); installed hashes: `INSTALL_SHA.txt`. Reference pack additions (sheets 15-17) are in `ArtDir/style/alive/male-reference-pack-2026-10-17/`.

**Shader frame note:** `_HeadEye` is the finished sclera centroid. The male eyes are no longer lowered 10 mm by the warp, so every male
shader zone below the orbit adds the old drop back (`hp.y += .010*(1-orbit)`), keeping mouth/beard/jaw paint on the same geometry.
Anyone adding male face zones: measure in that remapped frame.

## How it was built (`tools/`)
- `snap_m.py` (Blender) -> `source_male_1017.npz`; then everything is numpy, no Blender/Unity slot:
  `off.py` (male warp port with the constants as parameters + slicing), `compare_m.py` (sheet 07 front/profile tables in the face frame),
  `sculpt_off.py` (game-frame Gaussian bumps / smoothing brush -> per-vertex warp inversion -> 60-degree guards over basis AND blink keys),
  `fitbumps.py` (least-squares bump amplitudes vs the reference profile), `render_off.py` / `look3.py` / `lookmouth.py` (numpy previews),
  `jawline.py`, `probe_p.py`. Params of the final sculpt: `eval/s13.json` (s14 = + ear drop, same mesh).
- `apply_m.py` (Blender: delta -> basis + keys, normals rotated, FBX) and `cycle.sh <tag>` (apply -> clone -> mesh count -> review),
  `review.sh <tag> <set...>` (views | rig | tones | dressed | body), `perf.sh before|after`, `native.sh` + `native2.sh` (lobby parity),
  `patches_lm.py` (landmark-anchored CIEDE2000 skin patches), `body_cmp2.py` (body widths vs sheet 15 / plate).
- Unity editor tools (clone only): `unity/MaleFaceReview.cs`, `MaleFacePerf.cs`, `MaleFaceMeshCount.cs`.
- Clone: `~/male-face-UnityClone` (has the male-garments prefab patch + two clone-only exporter guards for its parity run).

## Install / rollback
Install = copy the five work files over their paths and stage them by explicit path (done 2026-10-17).
Rollback: `cp unity/before/{HeroFaceSkin.shader,TennisCharacter.shader} Unity/Assets/Resources/Tennis/Shaders/`,
`cp unity/before/HeroFaceReferenceFit.cs Unity/Assets/Scripts/Tennis/`, `cp unity/before/MatchHeroSurfaces.swift GolfArcade/Unity/`,
`git checkout HEAD -- Unity/Assets/Resources/Tennis/OriginalSeamBlinkFinish/Male.fbx` (HEAD = the 10-12 jaw sculpt, sha 92401c27…).

## Not done here
Lobby re-export (chat 6, REQUESTS.md), cap re-hug to the narrower skull (own session). Body: unchanged by Adnan's decision (the plate governs).
