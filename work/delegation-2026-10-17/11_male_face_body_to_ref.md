# Chat 11 — Male face (jaw, lips, everything) + body + skin shader to the reference

Adnan (10-17): "for the male model, i want to do the same thing that we did with the female jaw/lips + shader as well as any other discrepancies with his face or body ... trying to get the character as close as possible to the ref. that might mean making more ref images for the male im not sure if theres one with just the model and not all of the clothes"

## Read first
- `AGENTS.md`, `CLAUDE.md`, and `work/delegation-2026-10-17/README.md`, especially **"Sharing the machine"**: heavy.sh allows 1 Unity + 1 Blender machine-wide, a second concurrent job needs ≥35 % free memory and swap < 5 GB, one heavy job per chat, book on SCHEDULE.md, no helpers that launch Unity/Blender, clones in `~/`, Unity muted (GOLF_MUTE=1 + Editor mute).
- The female version of this job, which you should copy in method: `work/female-face-shader/` (GATE_RESULTS, proof, tools) and memory note `female-face-jaw-lips-shader-1017` (including the 34,443-vertex 60° split trap). Its brief was `work/delegation-2026-10-17/07_female_face_shader_male_refs.md`.
- The male reference pack: `ArtDir/style/alive/male-reference-pack-2026-10-17/` (START_HERE, MANIFEST, GENERATION_PROMPTS, sheets 01–14). Sheet 07 is the uncapped head/skin. **No sheet shows the unclothed male body.**
- The male identity plate: `ArtDir/hero/base_lock/male_body_plain.jpg`, plus `face_lock/`. The long male head history is in the memory notes `herobase-male-micro1*`, `jaw-sculpt-2026-10-12` and `bald-base-pass-2026-10-12`: read the current-state ones before sculpting.
- The male garments were just rebuilt to the pack by male-garments-refpack (memory note `male-garments-refpack`). Garments belong to garment-pipeline/male-garments chats: don't edit garment meshes.

## Phase 0: Missing references
Make an **unclothed male body reference set** in the same style and identity as the pack: front, side, back and 3/4, in neutral grey or skin with the bald head and no clothes. Base it on `male_body_plain.jpg`, sheet 07 and the face_lock, and use the same generator/method as the pack's GENERATION_PROMPTS. Add a closer face set (front, 3/4, profile, plus jaw/lip detail) if sheet 07 isn't enough. Record prompts and credits in the pack MANIFEST, give Adnan the credit estimate first, and push the images to him.

## Phase 1: Face
Measure every view against the reference: jaw, chin, lips, nose, eyes/brow, cheeks, ears and skull. Fix every discrepancy, not only jaw/lips. Sculpt in Blender headless on the current production male head, keeping topology, UVs, expressions/blendshapes and the mouth rig, and keeping the neck weld clean. Recompute or bake normals; never keep stale custom-normal offsets. Prove it with overlays per view.

## Phase 2: Body
Compare the body to the new unclothed refs and the identity plate: proportions, shoulders, chest, arms, hands, torso, pelvis, legs and feet. Fix discrepancies without changing height (1.65–1.75 m), the rig, or bindings that garments depend on. If a body change would break garment fit, list it and coordinate with garment-pipeline (local_ea58a91e-c723-4667-b476-5ac0af170719) and male-garments-refpack (local_982d9e7a-d485-4417-910b-ec88d0dab465) before installing.

## Phase 3: Skin / eye / lip shader
Match the reference in Unity **and** SceneKit, using the male branches of HeroLighting/HeroFaceSkin/TennisCharacter and `MatchHeroSurfaces.swift`. Female branches must stay unchanged. Measure shader cost at 1080p.

## Gates (work/male-face-body/GATE_RESULTS.md, binary)
JAW, LIPS, FACE_OTHER (nose/eyes/ears/cheeks vs ref), BODY (silhouette overlay ≤ ~3 % per view), IDENTITY (still reads as him; Adnan sees it), RIG (expressions, no tearing, neck seam ≤ 0.5 mm), SKIN (ΔE ≤ 5 vs ref patches under game light), NATIVE (SceneKit = Unity at 3 views), PERF (60 fps at ≥1080p unchanged), GARMENT_FIT (worn garments still pass the garment chats' stress check, or coordinated).

## Rules
Branch `10/13`, big pre-existing staged index: stage only your reviewed files and never commit. Install into `Unity/` only files you own; hero prefabs go as a patch to the integration chat. Push proof images to Adnan every ~15–20 min. Stop and show Adnan if his identity drifts.
