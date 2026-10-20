# Immediate face30 broad-head handoff

Parent requests model-routing to Astra; no further builds/previews/exports by this agent. Accepted Smooth1 + lip3 / native29 remain untouched. This folder is work-only.

## Exact baseline

- Male_baselineBlend: `65dbabd1ddbdcd00b814fee709986acfb9709a6d5f8af465a0c34e3d31d62f1c` — `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/reference-rebuild/face-finish29/smooth-mouth1/Male_OriginalFaceFinish29Smooth1.blend`
- Male_baselineFbx: `106171a7dafb39bcdd224c149ee5e8a29c9a1caa86691b85e760acc18373081c` — `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/reference-rebuild/face-finish29/smooth-mouth1/Male_OriginalFaceFinish29Smooth1.fbx`
- Male_latestCandidateBlend: `6ce6383e37f818cb96260656b4e925d7b9417603617d0a8ef1951784dd546a31` — `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/reference-rebuild/face-finish30/Male_OriginalFaceFinish30.blend`
- Female_baselineBlend: `e846b69013dcf5752d829b9375082f83d6374893bbd22774cb82b852b307e98f` — `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/reference-rebuild/face-finish29/smooth-mouth1/Female_OriginalFaceFinish29Smooth1.blend`
- Female_baselineFbx: `02ac48c1fe531dc6a15d3ed1ad7cedfffc5344d0d41223a536936ebbf9225366` — `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/reference-rebuild/face-finish29/smooth-mouth1/Female_OriginalFaceFinish29Smooth1.fbx`
- Female_latestCandidateBlend: `fc7cc7333640c521360a94f7b5f03f0154c2c78a8256dacfb41c8f7db438a08c` — `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/reference-rebuild/face-finish30/Female_OriginalFaceFinish30.blend`

## Latest status

Initial broad candidate failed source art: scalp scalloping/highlights and nose/philtrum/lip protected-boundary ripples. Root and this agent agreed HOLD; no FBX was exported or production changed.

Latest correction is saved in Male/Female_OriginalFaceFinish30.blend and SOURCE_GATE.json. Its small CPU preview command was launched immediately before the stop instruction; do not treat existing after PNGs as accepted. Latest art remains UNREVIEWED. No actual Unity capture for either version.

Latest changes: entire lip and nose protected via broad smooth quintic masks (not sparse contour pins only); female inner-face broad fit disabled; original scalp curvature relaxation disabled; inserted scalp/chin points use bounded Hermite circular sag <=0.65mm instead of erroneous MLS projection <=1.8mm. Authored corner normals now barycentrically preserved for the complete regenerated mesh, rather than mixing stale retained corners with geometric auto normals at moved/new points. Unity HeroSkinNormals continuous still performs its normal field; CPU before/after source shading is not an exact substitute.

## Recipe and composability

build-face30.py always starts from frozen accepted Smooth1. Original vertex prefixes33472 male /22891 female retain exact indices/weights. New scalp/chin midpoint vertices appended; male/female-candidate.npz records parents (new,a,b), sourceFace per outputtriangle, p and original. Original triangle skin is locally refined only at long scalp/chin edges; adjacent protected faces never split. UV/color/weights/shapes interpolate the same endpoints. Eye13 ReferenceFeatures and all53 bones/rest/hierarchy remain exact.

Broad male depth fit32mm support,3passes,.94strength,7mmcap; protected-point distance fixed<=4mm, quintic fade4..11mm. Whole mouth/nose masks further remove boundary ripples. Scalp/chin field: original chin coordinate relaxation up to3mm/8passes; original scalp no curvature relaxation. Scalp forehead may still see broad depth-fit overlap near1.605..1.625 (do not claim all scalp points fixed; inspect this transition). Edge threshold6.5mm; Hermite sagcap0.65mm.

Every blink-active original point (998male /2157female), mouth/lip/seam/nostril/ala LOOP point fixed. Full prefix shape deltas exact and original weights exact. Sparse per-shape eyelid operation from Astra is composable at original indices; new points never touch protected eyelid faces. Astra owns lid/eye/socket details in face-finish30-lids and knows these contracts. Broad changes can overlap peripheral socket beyond4mm: apply Astra operation to final prefix directly rather than assume disjoint additive far-field.

## Next corrective step

Review latest tiny CPU front/3q images first. If scalp remains rough, inspect Hermite endpoint normals and broad-fit scalp overlap; preserve original scalp points completely, project only inserted arc samples. If feature transition remains rough, protect whole nose/lip region and recompute derivative-consistent local normals, not just contour position pins. Existing HeroSkinNormals.Continuous uses8mm smoothing and20deg cap, so source-normal-only repair can be partially overwritten. Root will own actual integration/capture/export.

Prior failed local fairing: work/reference-rebuild/face-local-surface-finish/ROOT_GATE.json, mean0.209mm held for imperceptible gain; area-normal runtime experiment held. Do not use those shallow bounds as quality target. Targets: /Users/adnanyonathan/Documents/Codex/2026-10-06/open-4/outputs/reference-check/{male,female}-target.png. Current actual: proof/reference-rebuild/face-finish29-lip3 and native29/actual.

## Latest numeric source report

- Male: vertices35630, triangles71026, appended2158; movedoriginal1713, max3.0000mm /mean0.9176mm; protected positions0, original weights0, half/full delta error0.
- Female: vertices24462, triangles48668, appended1571; movedoriginal957, max2.8778mm /mean0.4647mm; protected positions0, original weights0, half/full delta error0.

Blender: /Applications/Blender.app/Contents/MacOS/Blender --background --python <workscript>. Sandbox execution crashes139; work-only CPU commands succeeded with exec_command sandbox_permissions=require_escalated and prefix_rule Blender path. CPU previews use Cycles CPU threads3,16samples480x560. No GPU/Unity/sourceFBX exports by this lane.

Native29 exact count handoff already complete: original-native-adoption29/xctest-source-count.patch, accepted-contract33694 maleBody. Root adopted fresh119resources+50sidecars+6fixtures after all6/native12 PASS; root build-only owns final build. Native fill experiment removed by root; native preview uses established lights, Unity owns actual on-map.
