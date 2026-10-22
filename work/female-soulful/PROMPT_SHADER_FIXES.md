# Implement the female character shader/material improvement

Work in `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator`. Implement this task; do not stop at recommendations or a plan. Use the installed Unity plugin/Unity CLI and relevant lookdev, materials, stylized-style and texture-workflow skills. Use Blender MCP when inspection or material authoring benefits from it. Read AGENTS.md first. These explicit instructions authorize female character material work despite older garment-only notes.

## Outcome

Make the female character's skin, eyes, clothing, cap and shoes achieve a substantial, visible improvement toward the supplied reference's polished stylized appearance. The user wants bright, appealing, lively character presentation, with original identity and restrained existing expressions. They rejected the previous mouth/teeth changes; do not bring them back.

The last shader pass looked almost unchanged. Do not repeat another tiny tint/roughness adjustment and call the material stage finished. Skin should have clean, readable form and broad controlled satin highlights; eyes should have convincing glossy depth; clothes should read as matte knit with appropriate texture and soft fabric sheen. Materials must respond differently to light. Increasing gloss everywhere is not the goal.

## Read and visually compare

- `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-soulful/CURRENT_STATUS.md`
- `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-soulful/SHADER_REFERENCE_GAPS.md`
- `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/style/alive/neutral-reference-pack-2026-10-15/START_HERE.md`

Open these actual images under that reference pack: sheets/07-head-skin-neutral.png, sheets/08-head-cap-neutral.png, sheets/03-golf-cardinal-master.png, sheets/10-golf-polo-construction.png, sheets/12-hands-footwear.png and sources/03-clothes-with-weight.png.

Inspect the direct comparison:
`/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-soulful/proof/review/reference-vs-current-shaders.jpg`

The reference is generated imagery, not a source shader or calibrated rendering setup. Infer the desired appearance; do not invent its shader settings. Its lighting, camera, skin selection and geometry differ from Unity's. Separate those effects before attributing everything to material code. Preserve selectable skin colors rather than baking a fixed tan color into the shader. Generated facial proportions do not authorize changing the original face.

## Current visible gaps

- Skin: current face reads pale/chalky and too evenly filled. Reference has richer light-to-shadow separation, rounded form and clearer broad satin highlights. Avoid yellow/orange grading, oily shine, dirty AO, visible pore noise or washed-out highlights.
- Eyes: current iris/sclera look flat and graphic. Improve material depth and controlled reflections without changing eye size, placement or head proportions, or using oversized catchlights as a substitute.
- Fabric: current polo reads overly smooth/rubbery; seams look drawn on. Reference shows matte knit breakup, soft grazing sheen, rounded fold shading and better collar/cuff separation. Distinguish genuine shader shortcomings from missing thickness/air gaps, which belong to the garment task.
- Cap/footwear: integrate fabric, brim, rubber and hardware responses with the character's material quality. Preserve existing geometry and customization.

Reference material appearance is currently FAIL. Shader code existing or compiling is not evidence of a finished visual match. Older completion statements in the work README/GATE_RESULTS are superseded by SHADER_REFERENCE_GAPS.md.

## Existing implementation and tools

Reuse the working Unity Editor at `/private/tmp/female-soulful-UnityClone`; control it through Unity CLI. Do not start another Editor or batch Unity. Relevant clone/production paths are under `Assets/Resources/Tennis/Shaders/`:
- `HeroLighting.hlsl`
- `HeroFaceSkin.shader`
- `TennisCloth.shader`

Female material setup is `Assets/Scripts/Tennis/FemaleGarmentFinish.cs`; source mirrors are under `work/female-soulful/unity/`. Inspect actual active materials/flags and the eye shader rather than assuming edits are wired. The current cloth branch uses `_FemaleSurface`; preserve the existing fabric-map version/ID encoding. The earlier skin branch has conservative highlights and color/ambient changes; inspect its actual effect before designing a stronger response.

Previous matched before/after image: `work/female-soulful/proof/review/female-material-before-after.jpg`. Current source captures: `work/female-soulful/proof/surfaces-current/`. These are historical evidence, not permission to label current production as the original BEFORE. Native material work is in `GolfArcade/Unity/MatchHeroData.swift` and `MatchHeroSurfaces.swift`; the previous female port compiles, but latest final visual parity is unfinished.

## Scope and protections

Female materials/shaders/textures and their necessary runtime/native wiring are in scope. Preserve male rendering and shared defaults with explicit female-only behavior where appropriate. Preserve body/head/face/hair geometry, body bindings, source rig/clips, accepted runtime arm/grip behavior, garment/skirt meshes and coverage, maps/turf, world lights/post-processing and gameplay-camera framing. Keep the game muted. No new teeth, mouth shapes or dynamic expression layer.

A separate shirt task owns geometry, fit and deformation. Do not overwrite its experiments or try to conceal ripping/flat construction through shaders. Share material settings carefully: this task owns material parameters in FemaleGarmentFinish; preserve garment-only changes in the same file, including any temporary diagnostics until deliberately reconciled. Avoid unrelated MatchHeroLook changes.

## Execution and delivery

Establish a clean baseline and identify what the current lights, material inputs, normals and shader branches each contribute. Use controlled comparisons with the same character geometry, pose, skin/clothing selections, camera, lighting and exposure. Temporary diagnostic lighting is allowed for analysis, but the final result must work in the unchanged game environments. Do not alter world lighting or exposure to manufacture improvement.

Iterate one major material variable at a time against a written gap list. Show actual Unity before/after images inline in chat with absolute paths after meaningful changes; include close-ups and unchanged gameplay-camera views. The user wants visible results and owns appearance acceptance. Keep cloth detail stable at phone distance; retain light, dark and saturated clothing choices and all saved customization. Do not use generated images as implementation proof.

Carry the final material behavior into the native SceneKit lobby and render it with the real app material/data/motion sources. Compilation alone is insufficient. Do not overwrite concurrent garment exports or run the broad `install_unity.py` blindly: it spans both tasks and could install failed prototypes. Guard shared edits and install only reviewed scoped changes.

Disk space is critically low; keep proof captures small and preserve all source assets/unrelated work. Phone performance is explicitly deferred: do not repeatedly request a device or claim target-device readiness. Finish with focused proof and honest gates, update status, and stage only explicit task files. No commits, broad git add, resets or unrelated modifications. Do not stop after a subtle cleanup and describe the reference match as complete.

If both handoffs run in separate tasks, only one task may drive the shared Unity Editor at a time. Do not overlap captures, asset refreshes, scene changes or temporary material swaps. Keep source-file ownership separate and preserve the other task’s edits.
