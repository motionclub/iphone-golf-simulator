# Face material30 — isolated satin candidate

GATE: source staging PASS. Satin1 actual ART FAIL: mild cheek gain, forehead still matte. One broader revision staged, actual PENDING. Four-file material.patch validated with git apply --check -p0 before root integration. Native Swift compiler PASS (no GPU). Actual image/art gate PENDING; no reference-quality claim.

Accepted skin finish currently discards the eye/equipment varnish lobe and keeps only pow(nh,18+smoothness*18)*.075. The forehead therefore has a weak, narrow highlight despite higher material smoothness. Candidate widens this to pow(nh,12+smoothness*12)*.13 plus pow(nh,48+smoothness*60)*.018. Peak .148, diffuse/wrap/shadow/ambient/pigment unchanged. Existing color, normals, UVs, morphs, bones, weights and blink unchanged. Eye13 iris spec .70→.85; sclera .45→.52; matte brows retained. No extra texture, shader variant, resource, or manifest field.

Flag VISUAL_CHARACTER_SKIN_POLISH=1, control0. Default remains0. Skin lobe applies only to accepted _SkinFinish / native skinFinish materials; old faces preserve old response. Unity global initialized by existing Tennis/Golf profile, native uniform initialized at material creation. Eye change applies only to OriginalSeam features/native anatomicalFace iris/sclera. Both source paths use identical coefficients. No skin tint is baked.

Root is running its identical two-front pair to face-material30-control / face-material30-satin1; tiny-queue.json also contains an equivalent matched pair. Inspect broad forehead/nose highlights, eye liveliness, mouth/chin shadow preservation, and whether sheen exposes lumps before adoption.

## Actual presentation consumers

Native CharacterModelPreview.Coordinator is used by lobby ClubDesign (cameraDistance2.95), LockerStudio (2.7), MotionClubMenus, onboarding and loading. All call MatchHeroData.buildHero / same MatchHeroSurfaces material creation; no special lobby skin or older face replacement path found. Native tint updates rebuild material and reapply the override. registry Made.look remains original export provenance, but no runtime restoration reads it; only made().colour is used to retrieve skin tone in configureFace. Fresh flag1 exports also record new eye spec normally.

CharacterModelPreview light recipe already has warm camera-left key1050 at40°/38°, cool fill370 at18°/-55°, warm rim520 at35°/160°, cool ambient210. Native29 diagnostics used neutral1100/350 +flat ambient300, explaining muted native forehead and color difference. Candidate leaves real lobby lights unchanged.

NativeParity.swift adds NATIVE_PROOF_LOBBY_LIGHT=1 using the exact native consumer recipe plus NATIVE_PROOF_PRIMARY_ONLY=1 plus NATIVE_PROOF_MATERIAL_ONLY=1 to render only male/female primary Ready/open heads (two per variant) and evaluate only those sparse Face samples. Existing native29 full geometry gate remains the geometry authority. This is a material proof under actual lobby light recipe, not a screenshot of the full SwiftUI screen. Root-only command: zsh work/reference-rebuild/face-material30/run-native-lobby-pair.sh <accepted-native-task-dir>. It uses explicitly selected packaged exports/goldens, compiles current native production sources and saves per-variant runtime/Metal logs, parity and pink audits. Never execute before root grants its serialized GPU interval.

Unity GolfGame.ShowMenu → StandInTheClubhouse/FrameClubhouse uses live golfer and ClubStage home backdrop. ClubStage changes rendering layer/background, not skin or light response; material flag flows through HeroLightingProfile. Tennis native lobby uses CharacterModelPreview rather than Unity UI Lobby.cs (that class handles multiplayer lobby UI only). Root should inspect actual native lobby/locker screen and actual tennis/golf gameplay after integrated geometry pass; diagnostic studio portraits alone do not establish presentation acceptance.

## Remaining constraints

This cannot repair eyelid aperture, head topology/normals, ear faceting or coarse chin. Geometry/detail lanes own those. Native29 proof used E58D64/F5AB7F while Unity two-front forcibly uses EA8D71/FBAE8F. The new proof-only color overrides and pair script pin EA8D71/FBAE8F for a matched material review; production selected skin remains unchanged.

No noisy skin grain added while geometry is unsettled; established relative lip and beard pigment untouched. The target female's fair tone and current selected warmer tone differ; candidate intentionally retains selected skin controls rather than baking a reference preset. Before promotion, inspect both sexes under lobby and real gameplay lights; reject if small-scale oily spots or surface lumps become more conspicuous.


## Revision1 after exact satin1 actual

revision1.patch is incremental against applied satin1 (two files only). Wider exp~7 instead of~16 simulates the broader source reflection visible in the supplied portrait. Peak .22+.018 weighted .5 for accepted rougher smoothness.32 / .775 forehead.364 / 1 nose.40. At forehead half-dot.85, broad response changes 0.00139 control → 0.00909 satin1 → 0.05305 revision1 (pre-light); this is a width change, not a narrow glint boost. No diffuse/tone/exposure change. CPU native compiler PASS and git apply --check -p0 PASS before root integration. No actual revision1 acceptance yet.
