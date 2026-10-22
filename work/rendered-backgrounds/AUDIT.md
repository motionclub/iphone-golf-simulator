# Rendered backgrounds — audit + approach (2026-10-17, chat 2)

## What really renders (verified in the clone)
- `DreamEnvironment` (on by default, release always) is the **final owner** of sky + sun + fog on every tennis point
  (location 100+venue) and every golf hole. It replaces whatever skybox the venue set with `GolfArcade/DreamSky`
  sampling a painted panorama (u offset +.35, altitude x2, no relation to the sun) and drives the sun from the real
  clock: `Euler(lerp(24,58,day), -105+(h_EST-12)*7, 0)`; fog linear (tennis 45–800 m).
  - Resort (100), golf 7/8/9/12/15 → `Environment/LuminousCoast/ArchipelagoSky`.
  - Other locations → previous skybox `_Panorama` (Skyscraper `SkyRooftop`, Volcano `SkyVolcanic`, golf `SkyCoastalSmall`/`SkyVolcanic`).
- Capture at 14:00 EST clear (`before/resort_day/resort_capture.txt`): sun az 89° el 58°, skybox DreamSky+ArchipelagoSky,
  fog 45–800, far clip 1000 m.

## Painted textures sampled at runtime
| Texture | Where |
|---|---|
| ArchipelagoSky | DreamSky (resort, golf coastal), LuminousCoastPilot.Sky (golf 12) |
| SummerSky | sea `_SkyMap` (resort tennis, golf 12) |
| SkyCoastalSmall | GolfResortSky (golf non-magma), sea `_SkyMap` (TennisResortMaterials:76), clubhouse glass `_ReflectionMap` (TennisEnvironmentV4:70), DreamSky fallback |
| SkyVolcanic | GolfResortSky magma holes, TennisVolcanicSky, DreamSky (volcano) |
| SkyRooftop | TennisRooftopSky + every skyscraper facade `_SkyPanorama` (TennisTowerAtmosphere) |
| CloudTops | skyscraper facades `_CloudTops` + 7 km "Cloud sea" mesh (TennisCloudAtmosphere) |
| Course/Lava/ash_cloud | SkyMagma (overwritten by GolfAtmosphere/Dream) |
| Sky/clouds.png | SkyGradient legacy golf fallback |
| Club/scene-*.jpg | menus (ClubStage) — not a venue background; out of this brief unless Adnan says |
Hub/plaza sky is already a CPU-procedural gradient on a 760 m dome (no painting) but its sun disc is placed at az 21 while the light is az 176 (cheat).

## What gives the painting away (resort, `proof/00_before_resort_diagnosis.jpg`)
1. **Scale/stretch**: altitude scale 2.0 stretches the cliffs to twice their painted height.
2. **Sun mismatch**: painted sun glow sits far left of the panorama at all times; the real sun moves with the clock (az 89° el 58° at 14:00).
3. **Long lens smear**: 2048 px over 360° = 5.7 px/deg; the 27° stare-down and any long lens shows a blur.
4. **No parallax**: a 2 m dolly moves the headland but not the islands/clouds (they are at infinity).
5. **Seam**: a brightness step in the sky at ring 180 (edge blend of the panorama).
6. **Baked clouds** never drift and are lit by the painted sun; night = darkened painting with stars.
7. **Painted reflections**: sea and clubhouse glass reflect a different painting (SummerSky/SkyCoastalSmall).

## Approach per layer (decided before building)
- **Sky dome** — `GolfArcade/RenderedSky`: a single-scattering (Rayleigh+Mie, Nishita) sky-view LUT computed on the CPU
  from the *actual* `RenderSettings.sun` direction whenever it moves (64×32, a few ms, rare), sampled by the skybox
  (1 fetch) + analytic sun disc + moon/stars at night. The same LUT drives fog colour, ambient and aerial perspective.
- **Clouds** — cumulus volumes built in Blender (numpy SDF + fbm → OpenVDB) and rendered in Cycles as **six-way
  lightmaps** (light from ±X/±Y/±Z, + alpha). At runtime each card is relit from the real sun (any time of day,
  sunset tint, moon) — no baked sun. Cards sit at true 3D positions (2–9 km), drift with the wind, and use a far-depth
  band so the near scene's far clip is untouched. Thin cirrus is a procedural layer in the sky shader.
- **Mid/far scenery** — real 3D meshes from Blender (karst towers for the resort, per venue later), high-res sculpt →
  decimated low-poly + baked normal/AO/albedo atlas, own `GolfArcade/DistantScenery` shader: sun from the real light,
  sky ambient from the LUT, aerial perspective toward the LUT colour in the view direction (so silhouettes melt into
  exactly the sky behind them). Depth written into a far band (log distance) so no far-clip change is needed;
  renderer bounds overridden so CPU culling does not drop them.
- **Reflections** — the rendered sky (LUT + clouds) is blitted into a small equirect RT when the sun moves and fed to
  `_SkyMap`/`_ReflectionMap`/`_SkyPanorama` in place of the paintings.
- Pre-rendered pieces = only the cloud lightmaps and the scenery bakes, all from our own Blender scenes.
