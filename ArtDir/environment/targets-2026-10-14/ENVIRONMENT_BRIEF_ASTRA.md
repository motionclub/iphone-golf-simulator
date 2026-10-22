# Environment & Visual Upgrade Brief (all sports) — for Astra / Codex
Date: 2026-10-14 · Folder: `ArtDir/environment/targets-2026-10-14/`
Project: Adnan's Party Sports — Unity 6000.3.24f1, URP, iPhone. Look: stylized, bouncy cartoon. Hub direction: "Classic Country Club".

## DIRECTION (read first)
**Modern 2025-era stylized fidelity with classic Nintendo sports charm.**
- PRIMARY look targets (fidelity bar): Mario Tennis Fever (2026), Mario Kart World (2025), Donkey Kong Bananza (2025), Astro Bot (2024), Tiny Glade (2024), Super Mario Party Jamboree (2024), Sky: Children of the Light. Files: `refs/modern_*`.
- CLASSIC refs (Switch Sports 2022, Mario Golf Super Rush 2021, Animal Crossing 2020, Mario Tennis Aces 2018, BotW 2017) are for **layout, readability and charm only — never a fidelity ceiling.** If a classic ref looks flatter than what you can do, do better.
- What "modern" means here: stylized PBR-ish materials (roughness/normal variation, soft spec), rich bounce light (GI), soft shadows + AO, light shafts, detailed wind-blown grass and foliage, real-looking stylized water, wet reflections, depth of field, bloom, atmospheric depth. Every surface should look *made of something*, not flat colour.

## Goal
Make every venue look like a finished Nintendo-quality cartoon game: better **lighting, sky, terrain/foliage, depth/atmosphere, tennis courts, golf courses, hub, post-processing and weather looks**, while staying smooth on iPhone.

## Hard rules
1. **Stage only.** Never commit, push, stash, checkout or reset. `git add` your changes and stop.
2. Do **not** touch animations, hero models/rigs/faces/clothes, gameplay physics, ball flight, scoring, collisions or obstacle data (`ObstacleScan`/TREES filters must keep working — swap visuals only, like `GolfCoursePalms.cs` does).
3. Keep each sport's in-game camera framing **except tennis**, which moves to the close over-the-shoulder cam: position `(player.x, 2.5, player.z - 3.5)`, look at `(0, 1, 3)`, FOV 46 (see `current/tennis_*_2_close.png`). If someone is already changing `TennisShoulderCamera.cs` (there is a `work/tennis-chase-camera/` run), don't fight it — just make the venues look good from that view.
4. **Weather must keep working** (golf: Clear, Gusty, Rain, Storm, Fog — `RoundEvents.Weather`). Build on `WeatherView.cs`; it layers on top of the course look and should keep doing so.
5. **iPhone budget** (see the "fake it cheaply" table below): measure before and after. Target 60 fps (≤16.6 ms) on the High tier and never worse than today on Low (`TennisQuality.Tier`). No real-time GI, no SSR, no volumetrics. Prefer baked/painted tricks: gradient skies, vertex-colour AO, fake fog in shaders, cheap bloom. Respect existing tiers (`SportsPostProcessing` drops glow on Low).
6. Work in small phases. After each phase: re-capture, build sheets, write 3 lines on what changed. Stop and ask if a change needs a new big asset pipeline.

## What's in `targets-2026-10-14/`
- `current/` — 57 real 1920×1080 captures from today's build (scratch clone, batchmode PlayMode). Names: `tennis_<venue>_<1 gameplay|2 close|3 wide|4 surface>`, `golf_<hole>_<weather>_<1 tee_gameplay|2 approach|3 green|4 overview>`, `hub_<1 spawn|2 walk|3 wide>`.
- `refs/` — `modern_*` = primary targets (33 images, 2024–2026); other files = classic charm refs. Sources in `refs/SOURCES.md`. Look reference only; never ship them.
- `sheets/` — 01–14: BEFORE (current) | MODERN TARGET | small CLASSIC CHARM panel (labelled layout/charm only), with captions WRONG NOW / MODERN TECHNIQUE TO COPY / KEEP FROM CLASSIC. 15–18: grids of all current shots. 19: board of all modern targets. `00_overview.jpg` is 01–14.
- `tools/EnvBriefCaptureTests.cs.txt` — the capture script. `tools/build_sheets.py` (run from targets-2026-10-14/, needs Pillow; reads current/*.jpg) — makes the sheets (pass an after folder to get BEFORE | AFTER | REF).

## Venues that exist
- **Tennis** (`TennisVenueKind`): Resort "Tropical Open / Centre Court", Skyscraper "Sky Open / Rooftop Court", Volcano "Magma Open / Crater Court". Tennis has **no weather** today.
- **Golf** (`Course.cs` in `Scripts/Course/Hole.cs`): Cliffside (7 Cliffside, 8 Needle, 9 Split, 12 Island Carry, 15 The Steps), Wild Isles (13 The Spiral, 14 Witch's Lair, 17 Frostbite Fjord, 18 Mesa Canyon, 19 Temple Falls, 20 Windmill Links), Magma Open (10 Crater, 16 Volcano Rim, 21 Obsidian Slab, 22 Ember Causeway, 23 Caldera Crown), Postcards set, Meadow Run (1–3, procedural, not reachable via `JumpToHole`). Captured: 7, 12, 14, 16, 17, 20, 22 (+ weather on 7 and 20).
- **Hub**: `Hub.unity` Country Club plaza (golden hour).

## File map (where the look lives)
| Area | Files |
|---|---|
| Pipeline | `Unity/Assets/Resources/Tennis/Rendering/TennisURP.asset` (the active URP asset, HDR on, MSAA 4x, shadow distance 60), `TennisURP_Renderer.asset`, `Assets/DefaultVolumeProfile.asset`, `ProjectSettings/QualitySettings.asset` |
| Post-processing | `Scripts/Tennis/SportsPostProcessing.cs` (one volume per gameplay camera, tone mapping + glow by tier) |
| Tennis lighting | `Scripts/Tennis/TennisLook.cs` (all tennis light/shading), `HeroLightingProfile.cs`, `HeroRimLight.cs` (rim on its own rendering layer — keep) |
| Tennis venues | `TennisVenue.cs` (court colour, line colour, names), `TennisVenueBuilder.cs` + `.Skyscraper.cs` + `.Volcano.cs` + `.Mesh.cs`, `TennisVenueArt.cs`, `TennisEnvironmentV4.cs`, `TennisResortVista.cs`, `TennisVenueFx.cs`, `TennisQuality.cs` |
| Tennis skies | `Resources/Tennis/Shaders/TennisSky / TennisCoastalSky / TennisRooftopSky / TennisVolcanicSky.shader`, `Resources/Tennis/Premium/SkyRooftop.png` |
| Golf atmosphere | `Scripts/Course/GolfAtmosphere.cs` (per-course sun/sky/bounce/haze, ACES grade), `HoleAtmosphere.cs`, `GolfCourseAtmosphere.cs` |
| Golf surfaces | `Scripts/Course/GolfCourseLook.cs` (surface library: Fairway, Green, Rough, Sand, Water, Lava, Snow, Ice… only holes 1–3, 7–10, 12–23), `GolfCourseFringe.cs`, `GolfCourseFoam.cs`, `GolfPostcardBasalt.cs`, `Resources/Course/{Look,Turf,Surface,Resort,Lava,Backdrop}`, `Resources/Course/Shaders/GolfResortSky.shader`, `Resources/Course/Resort/SkyCoastalSmall.png`, `SkyVolcanic.png` |
| Golf foliage | `GolfCoursePalms.cs`, `Resources/Course/GolfBotanicalInstancing.mat`, `GolfCoastalInstancing.mat`, `ArtDir/env_v5/tree_a*` |
| Golf hole build | `Scripts/Course/HoleView.cs` (loads `Resources/Course/hole_NN` models) |
| Weather | `Scripts/Game/WeatherView.cs`, `GolfGame.Events.cs` (`ForcedWeather`, `ChangeWeather`), `Scripts/Course/RoundEvents.cs`, `Resources/Golf/StormSky.shader`, `WeatherFog.shader`, `WeatherGround.shader`, `WeatherParticle.shader`, `WeatherCommon.hlsl`, `LightningBolt.shader`, `Twister.shader` |
| Hub | `Scripts/Hub/HubArt.cs` (Country Club look, golden hour, grade), `HubWorld.cs`, `HubLayout.cs`, `Resources/Hub/HubSurface.shader`, `HubWater.shader` |
| Older plans to read | `PLAN2D_EnvironmentQuality_CourtPostcard.md`, `VISUAL_OVERHAUL_ART_BIBLE.md`, `art-bible.md`, `ArtDir/UNITY_LOOK.md` |

## Targets (each points to its sheet)
### 1. Lighting (all scenes) — sheets 01, 02, 06, 14
- One warm low-ish key sun + cool blue sky/shadow fill (shadows bluish, not grey). Clear "time of day" per venue.
- Soft contact shadows / AO under trees, props, benches, net posts (vertex AO or blob shadows are fine).
- Heroes: keep `HeroRimLight` and make it visible on the close tennis cam and golf tee cam.
- Turf/rock must take the scene's key colour (sunset holes 16/22 are neon green today — wrong).
### 2. Sky — sheets 06, 07, 13
- Painted cartoon cumulus skies, warm glow at horizon, one per course/venue (not the same gradient everywhere). Slow cloud drift.
### 3. Fog / depth — sheets 06, 07, 12
- Distance fog tinted to horizon colour; far layers lighter and less saturated. Add background layers: hills, far islands, mountains (cheap low-poly cards/meshes outside play area).
### 4. Terrain & foliage (golf) — sheets 06, 07, 08, 10
- Calmer turf palette with clear fairway / rough / green / fringe value steps; softer mow stripes; tiny colour noise.
- Replace realistic pines with round toy trees matching the hub/tennis kit; no foliage floating on water — sit it on rock/land.
- Curvy fairway edges, flowers, rocks, soft bunker lips; water with shallow→deep gradient + shore foam (`GolfCourseFoam`) and calmer normal tiling.
- Snow: blue shadows, sparkle, frosted trees. Lava: emissive rivers with dark crust + bloom, not a loud tiled pattern.
### 5. Tennis courts — sheets 01, 03, 04, 05
- Textured acrylic court (fine grain, gentle sheen, slight baseline wear), court colour contrasting with surround/run-off.
- Bright crisp lines with a little sheen; proper net mesh + white tape + posts; benches, umpire chair, ball kids, signage, flower boxes.
- Crowd/stands that read (simple animated cards are fine) in Resort; Rooftop = dusk with floodlight pools + glowing windows; Volcano = light stone court lit from lava, readable at all times.
- Optional: offer hard / clay / grass surface variants (refs `mta_marina_hard/clay/grass.jpg`).
### 6. Hub — sheet 14
- Keep Classic Country Club layout and palette. Add glow to lamps/windows (emission + bloom), AO in corners, slightly richer paving and hedge detail.
### 7. Post-processing — all
- ACES/Neutral tone mapping, light warm grade per venue, small bloom on emissives/sky, soft vignette. Optional cheap far blur on High only. Low tier stays cheap.
### 8. Weather looks (golf) — sheets 11, 12, 13, 15
- **Rain:** darker cooler light; wet ground (darker turf, sheen, puddles on paths/bunkers via `WeatherGround.shader`); rain visible in stills.
- **Storm:** heavier dark sky, lightning lights the whole scene for a frame, rain sheets toward horizon.
- **Fog:** layered, tinted fog with near colour kept; soft sun glow; far shapes as silhouettes.
- **Gusty:** visibly windy — cloud shadows racing, trees/flags swaying, leaf/grass streaks.
- **Clear:** the improved base look. Make sure changing weather mid-hole blends smoothly.
- Optional later: same presets for tennis (Resort rain = covers/umbrellas? only if cheap).

## Modern look on an iPhone budget (fake it cheaply)
| Modern technique | Cheap iPhone version |
|---|---|
| Global illumination / bounce | Baked lightmaps or baked vertex-colour GI + Light Probes for heroes; for runtime-built venues, a per-venue trilight ambient + ground-bounce colour + hand-placed fill lights baked into vertex colours |
| Soft shadows + AO | One cascaded main-light shadow (soft, short distance), baked AO in vertex colour/texture, blob shadows for small props; no SSAO on Low |
| Volumetric light shafts / fog | Additive gradient cards (god-ray quads) facing camera, height-fog in the shared shader (`WeatherFog`), low fog cards on ground; no volumetrics |
| Wet reflections | Material params only: darker albedo, lower roughness, sky-cubemap reflection, puddle mask texture with ripple normal; no SSR/planar |
| High-detail grass with wind | GPU-instanced grass tufts only within ~15–25 m of camera, vertex-shader wind (shared global wind vector from `Wind`), fade to textured turf beyond |
| Depth of field | Only on High tier, half/quarter-res Gaussian on far background; off on Low; never blur the court/ball |
| Bloom + grade | URP bloom (threshold high, small), ACES/Neutral + per-venue LUT; Low keeps grade, drops bloom |
| Stylized water | Depth-gradient colour from a baked depth texture or vertex colour, scrolling foam texture at shore, cubemap reflection, sun glint |
| Lava / emissives | Emissive flow-map, bloom, vertex-colour warm bounce on nearby rock baked offline |
| Micro detail | Detail normal + tiling detail albedo on turf/stone/court, trim sheets; mip-friendly, ASTC compressed |

## Find more references yourself
Search and save good finds into `refs/` with a clear name (`game_place_what.jpg`) and add a line to `refs/SOURCES.md` (game, URL, what to copy). Prefer official press/eShop images and wiki galleries (mariowiki.com galleries load fine).
Look for **modern (2023–2026)** stylized games first; only use older ones for layout.
Search terms: "Mario Tennis Fever screenshots courts", "Mario Kart World rain / weather screenshots", "Mario Kart World Switch 2 grass meadow", "Donkey Kong Bananza screenshots", "Astro Bot screenshots 4K", "Tiny Glade weather / time of day", "Super Mario Party Jamboree boards", "Kirby and the Forgotten Land screenshots", "Fortnite Chapter 6 storm / rain screenshot", "Split Fiction screenshots", "Ratchet & Clank Rift Apart stylized lighting", "Hi-Fi Rush environment art", "Zelda Tears of the Kingdom sky islands", "Switch 2 stylized screenshots 2025", "Sky Children of the Light clouds"; techniques: "stylized grass wind URP mobile", "stylized water shader URP mobile", "fake god rays cards Unity", "wet surface shader roughness puddles URP", "baked vertex color AO Blender", "GDC stylized lighting talk".
Good sources: mariowiki.com galleries (load fine with curl), playstation.com game pages (image.api.playstation.com), Steam store API `store.steampowered.com/api/appdetails?appids=<id>`, Nintendo press/eShop pages.
Study: how bounce light colours surfaces, shadow colour, material response (court, grass, stone, water), far-layer fading, how lines/net read at gameplay distance, how rain changes ground and light.

## Verify (light tests)
1. Copy `tools/EnvBriefCaptureTests.cs.txt` into an **APFS scratch clone** (`cp -c -R Unity ~/UnityScratch_env`), not the real project, as `Assets/Tests/PlayMode/EnvBriefCaptureTests.cs`. Run:
   `AUDIT_OUT=<repo>/ArtDir/environment/targets-2026-10-14/after Unity -batchmode -projectPath ~/UnityScratch_env -runTests -testPlatform PlayMode -testFilter GolfArcade.PlayTests.EnvBriefCaptureTests -testResults ~/env_after.xml -logFile ~/env_after.log` (run in foreground; it takes ~6 min). Re-clone after your changes so the scratch has them.
2. Convert to jpg (`sips -s format jpeg`), then `python3 tools/build_sheets.py after` → `sheets_after/` with BEFORE | AFTER | MODERN TARGET | classic.
3. Existing tests still pass: `RoundEventsPlayTests`, `CourseReviewTests`, tennis playmode smoke.
4. On-device FPS: build to Adnan's iPhone, play 2 tennis points + 1 golf hole in Rain; report average frame time on High and Low (Xcode GPU report or an on-screen ms counter). Must not regress.
5. Report: what changed per area, before|after|ref sheet paths, frame times, anything skipped.
