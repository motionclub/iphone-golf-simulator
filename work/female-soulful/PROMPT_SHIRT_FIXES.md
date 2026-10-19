# Implement the female shirt fixes

Work in `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator`. Implement this task; do not stop at a plan. Use the installed Unity plugin/Unity CLI, Blender MCP and relevant Blender skills to make the work easier. Start with AGENTS.md, then the current status and references below. These explicit instructions supersede historical scope restrictions that conflict with this task.

## Outcome

Finish the female golf polo and tennis top as substantial, separate garments that hold together throughout the character's intended motion range. Golf sleeve/armhole failure is the first priority. The tennis top also needs convincing straps, correctly shaped underarms and torso-side ease; it must stop looking painted onto the body. Preserve the skirts: the user likes them.

Build one general garment solution. Do not fix each animation or emote individually. Use connected construction, appropriate topology and bindings, and general deformation/collision constraints where needed. Continuous joint-driven corrections are acceptable when they generalize anatomically. Named-clip exceptions, frame-window hacks, per-emote replacement meshes and an expanding library of sampled sleeve-pose patches are not an acceptable solution. Use motions to test the solution, not as lookup keys for repairs.

## Authority and current state

Read:
- `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-soulful/CURRENT_STATUS.md`
- `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-soulful/GENERAL_GARMENT_DEFORMATION.md`
- `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/style/alive/neutral-reference-pack-2026-10-15/START_HERE.md`

Open the actual reference images under that reference pack: sheets/01-tennis-cardinal-master.png, sheets/03-golf-cardinal-master.png, sheets/09-tennis-top-construction.png, sheets/10-golf-polo-construction.png and sources/03-clothes-with-weight.png. Cardinal sheets govern neutral construction; the clothes-with-weight board establishes material substance, edge thickness and air gaps. Reference colors are examples; all existing color customization and saved selections must remain functional.

As of 2026-10-16, the working Editor is `/private/tmp/female-soulful-UnityClone`. The latest garment experiments are in this clone and `work/female-soulful/`, not installed into the main project. Production still contains an earlier rejected garment revision. CURRENT_STATUS.md takes precedence over older completion claims in README.md/GATE_RESULTS.md. Verify the actual files before continuing.

No current golf garment candidate passes. The latest actual game proof is `work/female-soulful/proof/golf-clean-cage-cuffs-test/`; it still has poor shoulder/sleeve fit and detail folds. Do not present it as finished.

Useful work files under `work/female-soulful/`:
- `source/golf_top.blend` and `source/tennis_top.blend`: editable garment sources.
- `bind_polo_harmonic.py`: construction-based continuous shoulder weights, no animation inputs.
- `build_cloth_cage.py` and `unity/GarmentClothPrototype.cs`: experimental cage/constraint approach. Modes 1 and 2 use Unity Cloth and failed; mode 3 uses deterministic sewn-edge/body-capsule constraints and also remains unfinished. It is not shipping code; allocations and native parity are unresolved.
- `cage-prototype/unprojected-top.npz`: clean golf source export. The discarded seam projection moved points up to 12mm and introduced seven nonmanifold outer edges/six degenerate triangles. Clean export removes those defects, but this alone did not fix appearance.
- `unity/FemaleGolfRuntimeReview.cs` and `unity/FemaleAliveCapture.cs`: diagnostic and actual muted game captures.

Do not blindly rerun `bind_polo_sleeves.py` or `wrap_correctives.py`: they recreate rejected approaches. General shirt interpolation currently works better than the experimental torso-to-arm DQ arc. Keep the accepted BODY arm-volume system unchanged. Choose or replace garment experiments based on evidence; do not keep tuning a failed architecture indefinitely.

## Preserve

The user said the arm animation now looks better. Freeze the current accepted runtime arm/grip behavior in the clone, including HeroPoseSafety, HeroGripPolish, body HeroArmSkinning and accessory-glove support. Preserve neutral body/head/face/hair geometry, body bindings, source rig/clips, male assets, exact accepted skirt meshes/maps/coverage, maps/turf, world lighting/post-processing and gameplay-camera framing. Keep the original BEFORE face; no new teeth, mouth or dynamic-expression work. Keep the game muted.

Own garment geometry, garment bindings, garment-only runtime corrections, top coverage/contact data and necessary top construction maps. Do not change skin/eye/fabric shader direction in this task; the shader handoff owns that work. Keep shared integration edits minimal and guard against concurrent changes.

## Execution and delivery

Use the running Editor through Unity CLI; do not start another Editor or batch Unity. Relevant skills include blender-director, character-artist, rigging, cloth-sim, retopology and unity-export. Keep captures bounded: disk space is critically low. Clean only proven redundant task-generated data; preserve sources and other work.

Fix neutral construction and deformation, then test continuous arm elevation/rotation/twist, cross-body reach, overhead reach, torso twist, locomotion, jumps, emotes and transitions with the same implementation. Maintain collar/cuff/hem thickness, sleeve air gaps, cloth/body separation, connected seams and garment volume. Do not hide failure with two-sided rendering, exaggerated body hiding or camera changes. Do not redesign accepted arm motion to accommodate the shirt.

Show actual game images inline in chat whenever a meaningful component is ready, with absolute image paths. The user owns appearance judgment and does not want long verification checklists. Continue the authorized work without repetitive confirmation questions. Never claim an all-motion solution based on one pose or one swing.

Deliver the finished tops in Unity AND the native SceneKit lobby. Any new runtime deformation must have a real native solution; Unity Cloth alone is insufficient. Preserve other-task shader changes during export/install. Do not run the broad `install_unity.py` blindly: its pending list spans multiple tasks and could overwrite shared work or install prototypes. Install only reviewed, scoped changes with before-hash guards and explicit new-file packaging.

Update status, GATE_RESULTS.md and focused proof. Stage only the task's explicit files; no commits, broad git add, resets or unrelated changes. Phone frame timing/memory checks are deferred by the user and must not block this task or be claimed as passed. The task is not complete until the two tops look like real garments and the shared deformation solution survives the intended motion range.

If both handoffs run in separate tasks, only one task may drive the shared Unity Editor at a time. Do not overlap captures, asset refreshes, scene changes or temporary material swaps. Keep source-file ownership separate and preserve the other task’s edits.
