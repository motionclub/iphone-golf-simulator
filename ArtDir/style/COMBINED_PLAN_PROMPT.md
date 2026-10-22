# Combined pass: environment plan + character lighting

Read first:
- ArtDir/style/AUDIT_AND_PLAN.md (the environment plan, phases 1-7, decisions in section D)
- ArtDir/style/ART_BIBLE.md, especially section 15 Character lighting
- ArtDir/style/character-lighting/ (before grids, W1-W4 sheets, metrics_before.json, tools/CharLightCaptureTests.cs.txt)
- ArtDir/style/refs/r1-r5.png

Goal: one plan, one look. The world and the heroes are tuned together so the heroes always pop out of the new environments, in every venue and weather.

How to merge:
- Character lighting runs alongside Phase 4 (lighting, post, sky and depth presets). Every lighting preset (Midday, Golden, Dusk-Neon, Volcano, Snow) also sets its hero rim color/strength and hero ambient clamp. One owner for both.
- Hero work stays in the hero shaders only (HeroLighting.hlsl: HeroPresentationLight / HeroAmbient; presets from HeroLightingProfile.cs and GolfAtmosphere.cs). Hero shaders stay out of the Phase 3 material migration.
- Phase 5 weather must also feed the hero clamp, so fog can't grey skin and storm can't drain it.
- Phase 2 look-dev (Resort close cam, golf hole 7 tee) includes all 4 heroes.
- Recent feedback: tonight's hero-lighting look-dev (VISUAL_HERO_LIGHTING=1) made heroes brighter but flat and grey. Apply the fixes in ArtDir/style/character-lighting/FIX_PROMPT.md first (fill 0.95->0.35 off-axis, shadow floor .4->.15, ambient clamp min .12 / sat .60, skin roll-off (.60,.95), rim scaled by key direction capped .35). The environment itself has not been changed yet; its contrast and haze are below the refs, so Phase 2/4 must deepen shadows and add layered distance haze. Never flatten the world or heroes to gain readability.

Rules: stage only (git add), never commit/push/stash/checkout. Don't touch animations, rig, face or body meshes, gameplay, cameras or physics. 60 fps target on all tiers. Captures in a scratch clone, foreground batchmode.

Light tests, every phase:
- Re-capture the same environment shots and the character-lighting grids; build BEFORE | AFTER | REF sheets.
- Heroes: face skin L45-65, silhouette contrast 15 or more vs background in every gameplay shot, within 8 L of the lobby.
- Heroes also: saturation 0.62 or more, darkest 5% of hero pixels L 3-12 (keep form shading).
- World: contrast and distance haze closer to r1-r5 than today's captures.
- Tell me in 3 lines what changed, with sheet paths. My eye is the final check.
