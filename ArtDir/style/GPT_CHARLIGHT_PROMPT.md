# Astra paste prompt – character lighting look-dev

Read `ArtDir/style/ART_BIBLE.md` §15 Character lighting and the evidence in `ArtDir/style/character-lighting/` (grids, `metrics_before.json`, W1–W4 sheets).
Implement a look-dev test, **stage only, no commit**: a hero-only fill + rim + ambient clamp (extend `HeroPresentationLight` / `HeroAmbient` in `Unity/Assets/Resources/Tennis/Shaders/HeroLighting.hlsl`, presets set from `HeroLightingProfile.cs` and `GolfAtmosphere.cs`). Don't touch animation, rig, face or body meshes, and don't touch venue lighting.
Test on the Resort court and a golf tee (hole 7) for all 4 heroes (MatchHero_Male/Female, GolfKitHero_Male/Female). Then run `character-lighting/tools/CharLightCaptureTests.cs.txt` as a PlayMode test in a scratch clone (foreground batchmode, `AUDIT_OUT=.../after`) across all venues, holes and weather, rebuild the same grids into `character-lighting/after/`, and make before|after|ref sheets for W1–W4.
Pass if: face skin L45–65, a10–20, b18–30; silhouette dL ≥ 15 in every gameplay shot; shirt hue within 12°; matches the lobby within dL 8; no extra realtime lights. Report numbers before → after.
