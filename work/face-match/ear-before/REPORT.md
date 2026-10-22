# Face reference matching — staged candidate

**The reference-match goal is not complete.** This snapshot improves the baseline but does not pass G2, G3, or G4. G6 requires Adnan’s approval. The separate native SceneKit locker/out-of-game rendering path was not updated or verified, so parity outside Unity is not claimed.

Both required environment variables were **unset** in every saved capture: `VISUAL_CHARACTER_SKIN_POLISH` and `VISUAL_BLINK_NORMAL_FIELD`. The final runtime uses the face material and coherent blink normals by default, rather than relying on these flags.

Changes retained: fuller male head/jaw silhouette, lower and wider eye apertures, smaller female brows, a lifted/wider female nose, continuous lip contours with a satin finish, restrained cheek warmth, darker brown irises, subtle male stubble, skin-attached lid pigment, and working gaze/brow expression shapes. Rejected trials and their reasons are in [the iteration log](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/proof/iteration-log.md).

This continuation adds small rounded cheekbone volumes, a more front-facing male ear surface with clearer cartilage normals, rounder nasal planes, warmer skin transmission on shaded planes, male ear warmth, and better-positioned upper-lip/lower-cheek stubble. A small male nostril-base pigment is retained; the female pigment trial was rejected. Only HeroFaceReferenceFit.cs, HeroSkinNormals.cs and HeroFaceSkin.shader changed in this continuation.

The mean CIE76 difference across the two fixed cheek patches fell from 9.82 to 8.56 for the male and 5.88 to 3.76 for the female. This is a local color/shading comparison, not a whole-face quality score. [Measurement proof](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/proof/continuation-comparison.json) · [Male previous/current comparison](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/proof/male_progress.png) · [Female previous/current comparison](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/proof/female_progress.png)

## Gates

| Gate | Result | Evidence / limitation |
|---|---|---|
| G1 | **PASS** | 12 sheets exist: before and after, both heroes, front / 30-degree three-quarter / actual gameplay camera. Only frontal targets were supplied; the other sheets explicitly retain those frontal targets on the left. [Proof](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/proof/G1-sheets.json) |
| G2 | **FAIL** | Manual front overlays show deviations up to about 15%, exceeding ~5%. Eye heights/positions, male brow thickness, female nose dimensions and lip proportions still differ. [Proof](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/proof/landmarks.json) |
| G3 | **FAIL** | Skin and cheek shading are closer than the previous candidate, but the court shadow direction and nasal gradients still differ from the studio references. Five-pixel patch measurements show CIE76 differences up to 11.18; these include illumination differences. [Proof](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/proof/skin-patches.json) |
| G4 | **FAIL** | Blink, gaze and brow morphs run, but enlarged closed-lid frames retain small edge/shading artifacts, and the female jaw/neck boundary remains visually hard. Cannot certify the no-tearing/no-seam visual requirement. Topology/weights/binds are retained and no vertices below the head moved. [Proof](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/after/male_idle_3s.mp4) |
| G5 | **PASS** | check.sh reports the same 11 baseline assembly-reference errors and zero new errors. Final Unity Editor capture compiles and renders with zero C# or shader errors. The index contains only 8 face/head source files and their 8 metadata files. [Proof](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/proof/check-comparison.json) |
| G6 | **FAIL** | Not yet approved by Adnan. Agent review is not approval. [Proof](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/proof/G6-approval.json) |

## Before / after sheets

| Hero / angle | Before | After |
|---|---|---|
| male / front | [Before](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/before/male_front_sheet.png) | [After](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/after/male_front_sheet.png) |
| male / threequarter | [Before](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/before/male_threequarter_sheet.png) | [After](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/after/male_threequarter_sheet.png) |
| male / gameplay | [Before](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/before/male_gameplay_sheet.png) | [After](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/after/male_gameplay_sheet.png) |
| female / front | [Before](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/before/female_front_sheet.png) | [After](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/after/female_front_sheet.png) |
| female / threequarter | [Before](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/before/female_threequarter_sheet.png) | [After](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/after/female_threequarter_sheet.png) |
| female / gameplay | [Before](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/before/female_gameplay_sheet.png) | [After](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/after/female_gameplay_sheet.png) |

Canonical requested folders:
`/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/face-match/before/`
`/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/face-match/after/`

Portrait comparisons use the same 24-degree camera and head-relative framing before/after. A uniform crown/chin registration aligns the front images; there is no facial warping, retouching, relighting, or generated evidence. The racket is hidden only in the portrait proof to expose the face. The actual gameplay image retains the normal camera; its near player faces away. The locked targets are frontal studio images, so exact matching-angle 3/4 references and their original light setup are unavailable. Court lights, map, and post-processing were not edited.

## Three-second motion proof

[Male idle / blink / gaze / brows](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/after/male_idle_3s.mp4) · [Female idle / blink / gaze / brows](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/after/female_idle_3s.mp4)

Each clip is 90 actual Unity renders at 30 fps, exercising the existing Idle animation and production face deformation with deterministic inputs. Actual morph weights are logged: full blink reaches 100%; gaze moves in both directions; positive and negative brow shapes activate. This proves the exercised deformation path, not spontaneous blink scheduling or an iPhone build. Contact sheets enlarge the eyelids and neck so remaining artifacts are visible.

## Remaining differences and why

- Eyelids: upper contours remain too angular and insufficiently sculpted, especially on the female face. Surface pigment improves definition but cannot reproduce the reference’s raised lid roll. Closed lids retain edge/shading defects from the source lid surface. The final geometry was not certified tear/seam-free.
- Nose: broader nasal planes are rounder and the male nasal-base transition is less harsh. The nostrils and tip still lack the reference’s sculpted definition, especially on the female face. The female pigment trial was rejected because it looked detached; the small male cavity tint remains registered to the revised base.
- Brows/mouth: male brows remain about 15% too thick by the traced bounds. Female lip height and smile volume still differ. The overlay method has ±1 reference-pixel tracing uncertainty and no perspective correction.
- Skin: diffuse gradients remain too flat in some regions and too grey/dark in others. The unchanged court lighting is directional and differs from the softly lit locked references. Material refinements helped, but they have not reproduced that quality.
- Cheeks/jaw/ears: rounded cheek support and the male auricle orientation are closer. The male inner-ear folds now read in front and 3/4 views, but their contours remain coarser than the target. The female jaw is still sharper and its jaw-to-neck edge conspicuous. Both targets are bald, so no hair was added.
- Outside-game presentation: the separate native SceneKit asset/material path still needs an equivalent face-only update and rendered proof. No parity, phone performance, or device-quality claim is made.

## Staged files

Only the following 8 source files and their `.meta` companions are staged (16 paths total). The index was empty at the start. Several face helpers already existed as untracked files; staging those paths necessarily includes their existing helper implementations. Other working-tree changes remain intact. No commit, push, stash, checkout, or reset was performed.

- `Unity/Assets/Editor/HeroFaceMatchCapture.cs`
- `Unity/Assets/Editor/HeroFaceMatchCapture.cs.meta`
- `Unity/Assets/Resources/Tennis/Shaders/HeroFaceSkin.shader`
- `Unity/Assets/Resources/Tennis/Shaders/HeroFaceSkin.shader.meta`
- `Unity/Assets/Scripts/Tennis/HeroBlinkNormalField.cs`
- `Unity/Assets/Scripts/Tennis/HeroBlinkNormalField.cs.meta`
- `Unity/Assets/Scripts/Tennis/HeroFaceReferenceFit.cs`
- `Unity/Assets/Scripts/Tennis/HeroFaceReferenceFit.cs.meta`
- `Unity/Assets/Scripts/Tennis/HeroHeadSurface.cs`
- `Unity/Assets/Scripts/Tennis/HeroHeadSurface.cs.meta`
- `Unity/Assets/Scripts/Tennis/HeroOriginalSeamAnatomy.cs`
- `Unity/Assets/Scripts/Tennis/HeroOriginalSeamAnatomy.cs.meta`
- `Unity/Assets/Scripts/Tennis/HeroSkinNormals.cs`
- `Unity/Assets/Scripts/Tennis/HeroSkinNormals.cs.meta`
- `Unity/Assets/Scripts/Tennis/MatchHeroFacePerformance.cs`
- `Unity/Assets/Scripts/Tennis/MatchHeroFacePerformance.cs.meta`

[Exact staged path list](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/proof/staged-files.txt) · [Capture/source verification](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/proof/source-verification.json)

Runtime geometry audits show zero changed vertices below the head boundary, positive deformation Jacobians, and unchanged triangle indices, bone weights and bind poses. Body proportions, sockets, rig sources, clothes, LockFeet, serve/walk animations, course/map files and post-processing were not edited in this task. Shared `MatchHeroLook.cs`, `TennisCharacter.shader` and `HeroLighting.hlsl` still match their start-of-task hashes.

`Unity/Tools/check.sh` exits 1 with the same 11 missing URP/Core-reference errors as the baseline. Its tests therefore do not run. The final Unity batch capture exits 0 with no C# or shader compile errors.

G6 remains unapproved. Review the after sheets and clips before accepting this candidate; approval does not erase the remaining failed gates.
