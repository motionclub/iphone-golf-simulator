# OriginalSeam Eye13 blink-finish candidate 1

WORK ONLY. Existing accepted original head; no new face/model or legacy FaceCraft work. No production Assets mutation or Unity invocation by this agent.

## Diagnosis

Blink11's full closure passes at canonical rest: 0 eye-visible rays per aperture in the tested front grid, even before new geometry. Its Body aperture margins have Head weights varying male .864-.929 / female .836-.974, while ReferenceFeatures are Head-only. Coincident upper/lower closure vertices therefore separate after Head/Neck motion. Applying existing recorded Unity Ready/Serve/Forehand/IntroWave matrices reproduces thousands of visible-eye rays. More retreat cannot seal the skin opening.

## Single source candidate

`Male_OriginalSeamBlinkFinish1.blend/.fbx` and `Female_OriginalSeamBlinkFinish1.blend/.fbx` start from stable no-morph Eye13 source, retaining its eye UVs/materials. Reuse prior scoped blink11 half/full position targets; fix the defective skinning contract at the existing eye aperture. Pin Body Head influence to 1 within 4mm of the inner boundary, with a smooth fade to unchanged original weights at 16mm. Other deform influences reduce proportionally; non-deform mask groups stay exact.

925 male / 2158 female Body vertices have changed weights. Both Body and ReferenceFeatures open rest positions, corner normals, topology, UV buffers are exact hashes against Eye13. The original 53 bones, hierarchy/rest matrices, source identity and every weight outside the eyelid field remain exact. No unrelated face position or normal changes are introduced.

## Source gate

`blink-finish1-stages-gate.json`: PASS for both bodies under recorded Ready/Serve/Forehand/IntroWave sample2 matrices at blink 0/.25/.5/.75/1. The eye-visible aperture decreases at every stage, and all 16 tested full-blink apertures have zero eye rays. `blink11-posed-diagnosis.json` records the corresponding old-source failure. `blink-finish1-posed-full-gate.json` separately checks a narrow closure grid. `blink-finish1-front-cull-gate.json` repeats those full-blink tests using only front-facing source triangles, matching Unity back-face culling: all aperture leak counts remain zero. Source previews `*_source_ready_blink_*` use recorded Ready transforms and simulate the current runtime full feature retreat ×2; they are Blender geometry previews, not actual Unity proof.

Correcting weights changes the **posed** open eye margins, even though open rest geometry/normals are exact. Maximum source-predicted open position change is 2.4mm male / 3.2mm female in Ready/Forehand/Intro, and 7.3mm male / 9.6mm female in Serve. This matches the eye's actual Head motion; root must assess open/half/full appearance and transition under actual animation. A source ray pass does not certify blink aesthetics or preserved posed facial appearance.

## Root integration / actual checks

Back up the stable optional FBXs, then replace `Unity/Assets/Resources/Tennis/OriginalSeamEyeMaterial/Male.fbx` and `Female.fbx` with the candidate exports, preserving their existing meta/import settings. No C# patch required: retain current PrepareBlinkMesh normal isolation and full feature ×2 retreat, and current piecewise half/full target weights. Candidate feature full target retreats 6mm in source and is intended to become 12mm through existing runtime preparation.

Root now uses a separate review resource `OriginalSeamBlinkFinish` selected by `VISUAL_ORIGINAL_BLINK=1`, preserving stable Eye13 resources. Run capture-blink-finish1-poses.json with the optional work-only VisualOverhaulCharacterCapture.cs.patch: OriginalSeam1, OriginalEyeMaterial1, OriginalBlink1; Ready front/threequarter blink 0/25/50/75/100 plus open full/Intro photos. Compare open with Eye13 actual, closed with failed blink11 actual. Inspect .25/.5/.75 for eyeball breakthrough, jagged/folded lid margins and unrelated face faceting. The optional VISUAL_CHARACTER_BLINK_POSES capture branch adds Serve/Forehand/IntroWave at .5 length and distinct contact times, with open/full front and threequarter cameras following the animated anatomical frame. Then assess at least Serve and Forehand open/closed in existing game lighting; the source-weight delta is greatest in Serve. Native/Unity morph-and-skin parity and phone proof remain separate adoption gates.

If also refreshing the explicit OriginalEyeMaterial0 matched-control path, use the same source weight/shape geometry there so eye-material comparisons remain geometrically matched. Leave production default OriginalSeam promotion pending actual animation and native parity validation.
