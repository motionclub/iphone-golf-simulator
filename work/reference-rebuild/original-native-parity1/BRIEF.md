# OriginalSeam native adoption candidate 1

WORK ONLY. No Unity or native renderer execution and no Assets, Swift production source or project edits by this agent. Staged Swift files + proof harness typecheck; all three patches pass git apply --check -p0.

## Concrete missing paths repaired

1. Export Collect used the disabled legacy MeshRenderer Face. It now uses MatchHeroLook.face and exports OriginalSeamFeatures as skinned Face, including its actual mapped bones, inverse binds, updated weights and prepared half/full morph targets. Existing rig format and 53-bone contract are reused unchanged.
2. Export dropped Body/Face UV0. UV0 now carries existing pigment masks / authored Eye13 UVs, while Body bind coordinates remain separately exported. Native channels are UV0 + bind xy/z at 1/2; legacy Body keeps bind xy/z at 0/1.
3. Export silently discarded runtime LUT textures with empty asset paths. Original* Texture2D maps are now encoded as PNG in an output-only cache, copied beside the export, and marked linear. Expected relative maps: MatchHero_OriginalEye_RelativeIris.png, MatchHero_OriginalEye_RelativeSclera.png and MatchHero_OriginalSeam_RelativeSkinPigment.png. No fixed skin hue is baked.
4. Native performance previously weighted only full Body blink. Both Body/Face now use Unity's half/full interpolation. Clip playback preserves both blink shapes when procedural performance owns them. Anatomical Face skips legacy overlay closure/gaze/brow displacement, matching Unity's OriginalSeam branch.
5. Native character materials now bind exported relative BaseMap and selected tint. Explicit optional Look fields carry skinFinish, skinPigmentUV, anatomicalFace and baseMapLinear; older manifests still decode. Regional pigment and the accepted revision's directional skin lobe are ported.

## Deliberate parity boundary

No new bone/mesh/normal/shape source changes. Reuse prepared Unity runtime mesh data, including feature retreat x2 and isolated blink normal deltas, rather than importing raw FBX morphs separately.

The native surface port includes accepted lip/seam linear pigment, quiet cheeks, male lower-face tint, .28 wrap, .84 diffuse, .075 broad lobe, .95 specular and .45 rim. SceneKit's ambient contribution, shadow attenuation/floor, reflection probes, tone mapping and stage lighting differ from Unity; the .82 SH multiplier and .12 shadow floor are NOT yet certified equivalent. Native material/art gate remains open. This is actionable export/geometry/performance readiness, not a full visual parity claim.

## Root entry points

Apply MatchHeroLockerExport.cs.patch, MatchHeroData.swift.patch and MatchHeroSurfaces.swift.patch with -p0. Their exact baselines/candidates are in source-manifest.json. MatchHeroMotion.swift does not need editing.

Run export-native-parity1.json through the serialized Unity queue. It calls GolfArcade.EditorTools.MatchHeroLockerExport.Run, uses MH_LOCKER_OUT under this work folder (never production CharacterAssets), and enables OriginalSeam + Eye13 + BlinkFinish + accepted skin revision + continuous normals. MH_LOCKER_GOLDEN writes ordinary geometry/bone goldens and the new independent blink_parity JSON. MH_LOCKER_FACE_PARITY=1 adds a forehand track for this proof export only; shipping menus need not retain this unused extra clip.

New blink goldens cover both sexes, Ready/Serve/Forehand/IntroWave, midpoint and contact where present, blink 0/.25/.5/.75/1. Every moved Body eyelid vertex plus distributed unaffected Body/Face samples are included. Positions come from actual Unity CPU skinning after SetFacePerformance, in the same z-mirrored coordinate contract.

After export, root may run run-desktop-proof.sh from repo root. It builds the standalone macOS NativeParity harness using staged files plus unchanged MatchHeroMotion.swift. The harness asserts 53 bones, Body+Face staged morphs, three Body texcoord sources and decoded/native morph weight position parity <.2mm. It writes parity.json and Metal SceneKit pose/stage portraits with a head-following camera. No phone is involved. Inspect full closure, half folds, intact open face and the selected tint/materials in these actual images. The diagnostic stage lights are not a matched Unity studio rig.

Before production resource adoption, register newly exported PNGs with the native resource build (current Xcode projects list assets individually; project-unity.yml is the generator authority). No project changes are staged here. Existing legacy tests hardcode Body counts and must be evaluated against the chosen export, not weakened to accept arbitrary models.

## Source gate

PASS: Swift typecheck; patch applicability; optional backward-compatible metadata; identical underlying bone/weight/morph binary serialization; exact two-stage weights; no production mutation by this agent.

PENDING: Unity exporter compilation/run, generated texture payloads, source-vs-native CPU proof, Metal shader compile, desktop portrait art review, ambient/reflection calibration and production resource registration. Physical phone testing remains deferred.

## Corrected proof texture packaging

The first native harness run stopped at Incomplete garment maps because the Unity exporter writes PNG inputs while native garment() deliberately loads KTX. package-garment-textures.py now packages all 25 referenced garment maps into the work export. Twenty-one exported PNG hashes exactly match current shipped sources; their KTX files are copied byte-exact. Four shoe mask PNGs differ, so they are freshly compressed with the existing cloth TextureConverter workflow (Highest ASTC8x8, linear channels/gamma, preserved alpha, y flip, Clamp, KTX). No material map or shader path is bypassed. garment-texture-package.json records source/output hashes and exact commands. The proof script runs this packaging before building/running. Packaging PASS; the corrected renderer has not been run by this agent.

## Actual desktop Metal repair and verdict

Final desktop sweep PASS: 60 portraits, zero magenta pixels, zero Metal compiler failures. Logs saved as native-runtime.log and native-metal.log; every image is recorded in actual/pink-audit.json. Geometry parity is unchanged: male 43,080 samples max .00433265mm; female 80,700 samples max .01350161mm. Both original 53-bone rigs and half/full shapes are retained. Ready open/half/full and sampled Serve/Forehand poses visibly retain eyes, skin, identity and full closure without white leaks.

Apply ONLY MatchHeroSurfaces.repair1.patch (-p0) against the currently installed prior native sources. It fixes the SceneKit argument parser (individual declarations, no repeated uniforms across modifiers) and removes the SCNMaterial.multiply post-light skin double tint. The full original MatchHeroSurfaces.swift.patch was also updated for reproducible fresh staging, but root already installed that earlier patch and must use repair1 now. Typecheck and repair patch applicability PASS.

The proof camera now sets zNear .01/zFar10; the old default 1m near plane clipped eyes because the camera is .9m away. Portraits use .23 orthographic scale and hide only racket for face inspection. Camera and head-relative light placement changes are proof-only. No production camera change.

Visual verdict for incremental adoption: female face clearly improves at full-body portrait scale by removing stacked black eye outlines and restoring readable brows; male improvement is modest, removing dark painted nostril/feature fragments and giving stronger brows with quieter skin pigment. These existing matched Unity full-body images are a gameplay-scale proxy, not an actual court-motion acceptance. Reference-quality face art remains FAIL. Soft lips, uneven cheek/mouth planes, male partial upper-lid folds and the jagged full-blink crease remain visible close up. No remaining material or closure defect observed here requires holding this bounded improvement once actual default gameplay and native resource-bundle checks pass; those checks still belong to root. SceneKit ambient/shadow/reflection and tone mapping are not calibrated to Unity by this diagnostic stage.

Final source check: production MatchHeroSurfaces.swift already equals final candidate SHA 481bc244a455c68aa945f58225efeaea1c039492be62026e6140ff22d9320cac. Root installation occurred during review. repair1 patch is the preserved exact delta from prior installed source; do not reapply it to this current matching file.
