# Paste prompt for GPT-6 Astra (Codex): audit the art bible and plan only

You're helping make Party Sports (Unity 6000.3.24f1, URP, iPhone) look like Adnan's reference images everywhere. **This pass is research and planning only.**

## Rules
- Write only `ArtDir/style/AUDIT_AND_PLAN.md`. You may add a section to `ArtDir/style/ART_BIBLE.md` called "## Suggested changes (Astra)", and leave the rest of that file as it is.
- No project changes: don't touch scenes, materials, shaders, scripts, settings or packages. No `git add`, commit, push, stash or checkout.
- Keep tests light: reading files, sampling images, and (optionally) opening Unity read-only for screenshots in a scratch copy only.

## Read first
1. `ArtDir/style/ART_BIBLE.md` and `ArtDir/style/ART_BIBLE_palette.png`
2. `ArtDir/style/VISUAL_STANDARD_AND_JUICE.md`
3. The refs `ArtDir/style/refs/r1.png` to `r5.png`: r1 hub, r2 resort tennis close cam, r3 golf tee, r4 venues grid, r5 weather grid.
4. `ArtDir/environment/targets-2026-10-14/`: `ENVIRONMENT_BRIEF_ASTRA.md`, `sheets/`, `current/` (today's real captures), `refs/`.

## Then inspect the real project
Look at the URP asset(s) and renderer, Volume profiles, the directional lights and environment lighting settings, skyboxes, fog settings, materials and shaders used by courts, grass, foliage, water and lava, the weather system scripts, particle prefabs, and any camera shake or feedback code. List the file paths you check.

## Write `ArtDir/style/AUDIT_AND_PLAN.md` with
**(a) Bible critique.** Cover gaps, contradictions, and numbers that are unrealistic for iPhone. **Sample your own colors from r1–r5** (with code) and compare them with the bible's hex values. Flag any that are off and say what you'd use instead.
**(b) Gap map.** For each system (palette, value, lighting, post, sky, fog/depth, materials/shaders, environment kit, glow, readability, weather, VFX, juice, perf), compare what the project does today with what the bible says, with file paths and today's capture as evidence.
**(c) Build plan in phases.** Each phase lists its goal, the files it'll touch, what it'll measure (for example sky and ground lightness, FPS, draw calls) and which golden shots prove it's done (BEFORE | AFTER | REF sheets):
1. Fix the art bible.
2. Look-dev scene: resort court with the close cam vs r2, then the golf tee vs r3.
3. Master shaders (M_Ground, M_Foliage, M_Prop, M_Water, M_Emissive, M_Sky).
4. Lighting and post presets (Midday, Golden, Dusk-Neon, Volcano, Snow).
5. Weather global parameters plus the WeatherDirector.
6. VFX and juice library.
7. Rollout venue by venue.
**(d) Questions for Adnan.** Short, decision-type questions only.

Keep it plain English and concise. Finish with a 5-line summary of your top concerns and the first phase you'd start.
