# Chat 7 — Female face (jaw + lips) and skin shader to the reference, then the male reference pack

You are one of several parallel chats in this repo; see `work/delegation-2026-10-17/README.md` for who owns what. Read `AGENTS.md` and `CLAUDE.md` first, then `ArtDir/style/alive/neutral-reference-pack-2026-10-15/START_HERE.md`, look at its PNGs (`sheets/07-head-skin-neutral.png`, `08-head-cap-neutral.png`, `sources/01-playful-competitor.png`, `02-acting-range.png`, `S4 female_body_plain.jpg`), then `work/female-soulful/SHADER_REFERENCE_GAPS.md`, `REFERENCE_ANALYSIS.md` and `CURRENT_STATUS.md`. Also read the memory notes `female-shader-pass-20261016`, `herobase-female-head-microf1`/`microf2`/`microf3`, `herobase-female-custom-normal-offsets`, `jaw-sculpt-2026-10-12` and `bald-base-pass-2026-10-12`.

## Adnan's instruction (10-17)
"Need to work on character models to match the ref images shown of the woman. Used it for shaders as well, trying to get the facial structure, mainly jaw and lips as close as possible so it looks a bit more real, and then also getting the shader to match the ref. [...] then taking all of this and creating ref images for the male characters."

This explicitly expands scope: **female jaw and lips geometry may change to match the reference.** It overrides the reference pack's "no jaw change" note and the older locked-identity notes, for jaw and lips only. Keep everything else about her identity: eyes, nose, ears, skull, bald scalp, neck, body proportions and age. Stop and show Adnan if she starts to read as a different person.

## Phase 1: Female jaw + lips (geometry)
- Measure the reference against the current head from matched views: front, 3/4 and profile from sheet 07, plus S1/S2 for appeal. Measure jawline contour, chin width/projection, jaw angle position, lip fullness, lip line/cupid's bow, philtrum, mouth corners and lip volume in profile.
- Sculpt in Blender headless on the current production female head. Keep topology, UVs, blendshapes/expressions and mouth rig working, and keep the seam to the neck/body welded. Remember the custom-normal trap: authored normal offsets flatten new forms, so recompute them or bake them fresh.
- Use overlays of plate vs head at each view as proof.

## Phase 2: Female skin, eyes and lips shader to the reference
- Build on the 10-16 shader pass (installed, staged: `HeroLighting.hlsl`, `HeroFaceSkin.shader`, `TennisCharacter.shader` female branches). Close the remaining gaps in `SHADER_REFERENCE_GAPS.md`: skin tone/value, subsurface warmth, highlight shape, lip colour/sheen, eye clarity. Don't add a yellow tint or plastic gloss, and don't change world lights.
- Deliver in Unity **and** the native SceneKit lobby (`GolfArcade/Unity/MatchHeroSurfaces.swift`). Matched-view renders against the reference sheet are the proof.

## Phase 3: Male reference pack (after Adnan has seen phases 1–2)
- Create a male reference pack in the same format and style as the female pack (`ArtDir/style/alive/male-reference-pack-2026-10-17/`): tennis + golf cardinal masters, obliques, head/skin, top construction, shorts/trousers construction, and **dedicated tennis-shoe and golf-shoe detail sheets** (several angles, real performance-shoe construction: outsole, midsole, upper panels, toe box, heel counter, lacing; golf with spikes/cleats). Base them on the locked male identity plate (`ArtDir/hero/base_lock/male_body_plain.jpg`) and the current male hero; don't change his identity. Reuse the method in the female pack's `GENERATION_PROMPTS.json`/`MANIFEST.json`, and record your prompts the same way. Clothing colours are examples only (customizable).
- Show Adnan the pack. When he accepts it, tell the garment chat (`garment-pipeline`) where it is and which sheets govern male clothes and shoes. That chat fits the male garments; you don't edit garment meshes.

## You own
Female head/face geometry (jaw/lips zone), female skin/eye/lip shader branches (`HeroLighting.hlsl`, `HeroFaceSkin.shader`, `TennisCharacter.shader`), the matching native surface code, and the male reference pack. Not garments or `TennisCloth` (garment chat), clips (chats 1/4), `HeroPoseSafety` (chat 3), skies (chat 2), or male geometry/shaders.

## Gates (work/female-face-shader/GATE_RESULTS.md, binary)
- JAW: jaw contour overlay vs reference front and profile within ~2 % of head height along the jawline.
- LIPS: lip height/width/projection within ~5 % of the reference at front and profile; cupid's bow and corners match.
- IDENTITY: eyes/nose/ears/skull unchanged (vertex delta ≤ 0.5 mm outside the jaw/lip zone); Adnan has seen it.
- RIG: all expressions/blendshapes and mouth moves work with no tearing, and the neck seam has no step (≤ 0.5 mm).
- SKIN: skin, lip and eye colour/value in matched renders within ΔE ≤ 5 of the reference patches under the game's lights, with no yellow cast.
- NATIVE: SceneKit renders match Unity at 3 views.
- MALE_PACK: all sheets present, including tennis-shoe and golf-shoe detail sheets; MANIFEST + prompts recorded; Adnan has seen it.

## Rules
Branch `10/13`, big pre-existing staged index: preserve it. Stage only your reviewed files; no commits, resets or broad `git add`. Unity only in your own APFS clone (`cp -cR Unity /private/tmp/female-face-UnityClone`), one Editor, `GOLF_MUTE=1`. Headless Blender, not the MCP. Disk ~38 GB: keep proof small and delete nothing that isn't yours. Install into `Unity/` only files you own; shared prefabs go as a patch to chat 6. Push proof images to Adnan every ~15–20 min. Needs from other chats go in `work/delegation-2026-10-17/REQUESTS.md`.
