# POSTCARD_LOOK — Unity runtime (role A2)

Owner files: `Unity/Assets/Scripts/Course/GolfLook.cs`, `GolfAtmosphere.cs`, `HoleView.cs` (material order only),
`Unity/Assets/Scripts/Game/GolfGame.cs` (light block + per-hole hook), `CameraRig.cs` (near plane),
`Unity/Assets/Resources/Course/Shaders/GolfSurf.shader`, `Unity/Assets/Editor/GolfLookTextureImporter.cs`,
`Unity/Assets/Editor/GolfLookSmoke.cs` (gates), this file.

## 1. How HoleView picks a material (BuildFromModel, per renderer, per slot)

```
not a postcard hole (hole 7, Cliffside, Meadow)  -> EXACTLY the old rule: Palette name -> Mat(colour) (flat URP Lit, S .1), else as imported
postcard hole (Number 8, 9, 10):
  1. name starts "LK_"                         -> GolfLook.Get(name)   (".001" suffixes and " (Instance)" stripped)
  2. imported material has _BaseMap/_MainTex/_BumpMap/_EmissionMap -> keep it as imported
  3. water / lava, never a flat colour:
       MAT_WATER -> LK_WATER, MAT_WATER_SHALLOW -> LK_WATER_SHALLOW, MAT_FOAM -> LK_SURF, MAT_LAVA -> LK_LAVA;
       else by renderer name: WATER_LAVA* -> LK_LAVA, WATER_SHALLOW*/WATER_SHELF* -> LK_WATER_SHALLOW,
       WATER_SURF*/WATER_FOAM* -> LK_SURF, WATER_FALL* -> LK_FALL, any other WATER* -> LK_WATER
  4. Palette name -> Mat(colour) exactly as today (gameplay MAT_FLAG/POLE/CUP/BALL, baseline MAT_* meshes)
  5. anything else -> untouched
then (postcards only) GolfLook.DressModel(model, number)
```
Unchanged byte-for-byte: `Palette` (still read by PostcardImportCheck via reflection), `GroundPrefixes`, the MeshCollider loop,
`GroundHeight`, placement/alignment, placeholders, the whole primitive `BuildGeometry` path. Shadow rule kept: `WATER*` never casts.

`GolfLook.DressModel`: re-swaps LK_ slots (idempotent), shadows OFF for `WATER*`, `LAVA*`, `DRESS_SMOKE*`, `DRESS_CONE*` and any
GolfSurf (transparent) renderer, receive-shadows off for transparent + cone; adds one point light on every `LAVA_LIGHT*` empty;
never adds colliders. GPU instancing is on every LK_ material (`enableInstancing`; URP Lit also batches via the SRP batcher).

## 2. Material table (GolfLook.Table) — tunables

Textures: `Resources/Course/Look/<Tex>_C` (albedo sRGB), `_N` (normal, OpenGL +Y), `_E` (emission sRGB). Tiling stays (1,1): UVs are in tile units.
`Tint` = `_BaseColor` over the albedo (.94 grey everywhere, like EnvV4) ; `Fallback` = flat colour used ONLY when `_C` is missing (warning logged once, never pink).

| LK name | shader | Tex | S | BumpScale | other |
|---|---|---|---|---|---|
| LK_FAIRWAY | URP Lit | Fairway | .10 | .75 | fallback #76D038 (BumpScale 1 read as shag carpet up close) |
| LK_GREEN | URP Lit | Green | .12 | .6 | |
| LK_ROUGH | URP Lit | Rough | .08 | 1.0 | |
| LK_SCRUB | URP Lit | Scrub | .08 | 1.0 | |
| LK_SAND | URP Lit | Sand | .12 | 1.0 | Tint .80 (the bright albedo clipped to white at .94) |
| LK_CLIFF | URP Lit | Cliff | .12 | 1.2 | |
| LK_CLIFF_DARK | URP Lit | CliffDark | .35 | 1.2 | wet |
| LK_ROCK | URP Lit | Rock | .12 | 1.2 | |
| LK_ROCK_WET | URP Lit | Rock | .35 | 1.2 | Tint (.68,.70,.70) |
| LK_PATH | URP Lit | Path | .10 | 1.0 | |
| LK_MASONRY | URP Lit | Masonry | .10 | 1.2 | |
| LK_BASALT | URP Lit + `_EMISSION` | Basalt (+_E) | .15 | 1.4 | `_EmissionColor` (1.8,1.8,1.8) HDR x crack map |
| LK_LAVA | URP Lit + `_EMISSION`, MATTE | Lava (+_E) | .10 | 1.0 | [v2: superseded, see v2.3] `_EmissionColor` (1.0,.65,.50) x glow map, tint .75, no specular / env reflection. No map: emission = fallback orange x1.3 |
| LK_PLANTS | URP Lit (no normal) | Plants | .10 | – | palette atlas, instanced |
| LK_WATER | GolfArcade/TennisWater | – | – | – | _Shallow #1268A8, _Deep #083484, _Sky #2E68B2, _DeepDistance 260, _WaveScale .22, _Sparkle 5 |
| LK_WATER_SHALLOW | GolfArcade/TennisWater | – | – | – | _Shallow #1AC4C4, _Deep #1096B2, _Sky #46AAC8, _DeepDistance 420, _WaveScale .30, _Sparkle 4 |
| LK_SURF | GolfArcade/GolfSurf | Surf | – | – | _VertexAlpha 1, _Lit 1, _SunShare .50, _Emission .35, _Wrap .2 |
| LK_FALL | GolfArcade/GolfSurf | Fall | – | – | _VertexAlpha 0, _Lit 1, _SunShare .40, _Emission .22, _Wrap .8 |
| LK_SMOKE | GolfArcade/GolfSurf | Smoke | – | – | _Color (.62,.56,.56,.85), _Lit .6, _SunShare .3, _Emission .05, _Wrap 1 |

Per-hole tints (`GolfLook.HoleTint`, replaces the table Tint on that hole; the material becomes a copy named `LK_X@<hole>`):
Split (9) fairway/green (.76,.84,.72), rough (.80,.86,.76), sand (.70,.70,.68) — its higher sun lights flat ground ~1.4x Needle's
(measured fairway (155,232,102) vs (132,187,81) before, (128,209,84) after); Crater (10) fairway/green (.90,1.15,.62), rough (.90,1.10,.62) —
the dusk key is orange, the still's grass is lime (measured with it: (133,187,62)).
All tints are sRGB as authored (SetColor converts: .94 → .87 linear). Measured fairway means at the phone camera, real Fairway_C, real lights:
Needle (132,187,81), Split (128,209,84), Crater (133,187,62).

TennisWater notes (the shader is frozen):
* its shallow->deep gradient is `saturate((|worldXZ| - 20) / _DeepDistance)` measured from the WORLD ORIGIN = the tee, not from the shore:
  LK_WATER keeps BOTH ends deep blue (slight lift near the tee); the turquoise comes from the separate `WATER_SHELF` mesh (LK_WATER_SHALLOW).
* `_Sky` is the fresnel target. The phone camera sees the sea at grazing angles (fresnel ~.5-.9), so `_Sky` must be a saturated blue,
  not the tennis pale sky.
* it computes linear fog PER VERTEX (saturated per vertex). A 4-vertex 4 km ocean comes out ~50 % fog colour everywhere
  (measured (136,161,192) with fog vs (25,85,147) without, 60-130 yd away). postcard_look_lib builds WATER_OCEAN as a graded grid
  (16 m cells → 400 m at the rim), which is correct. Runtime safety: `GolfLook.DressModel` densifies any TennisWater WATER* mesh with
  ≤ 64 triangles into an n×n barycentric grid (one n per mesh → no T-junctions, cells ≤ `WaterCellYards` 60 yd, ≤ 60k tris).
  On the baseline FBX: 1 mesh per hole densified, water then measured (26,87,150) = deep blue.
* it animates its swell with _Time (tennis-owned; the brief asks for TennisWater on the ocean). GolfSurf stays static.

Lava lights (`GolfLook.LavaLightColor/Range/Intensity`): orange (1,.45,.12), range 48 yd, intensity 28 (URP point lights fall off 1/d²:
~0.3 at 10 yd, ~1.1 at 5 yd), no shadows, ForcePixel. `AdditionalLightsPerObjectLimit` = 2 (TennisURP) → see §4.

Unknown LK_ name: generic rule `LK_FOO_BAR` → `FooBar_C` / `FooBar_N` on URP Lit, S .12 (warning logged once).

### How to add a material
1. Blender: name the material `LK_<NAME>` (Principled + image nodes for preview), export as usual (no embedded textures).
2. Textures: `Unity/Assets/Resources/Course/Look/<Tex>_C.png` (+ `_N.png`, `_E.png`); the importer sets everything.
3. Add a row to `GolfLook.Table` (or rely on the generic rule above). Run `GolfLookSmoke` (below).

## 3. GolfSurf shader (`GolfArcade/GolfSurf`, Resources/Course/Shaders/GolfSurf.shader)
URP UniversalForward pass, `Blend SrcAlpha OneMinusSrcAlpha`, `ZWrite Off`, `Cull Off`, queue Transparent, fog (`multi_compile_fog`),
instancing (`multi_compile_instancing`); no shader_feature keywords (nothing for a build to strip), no `_Time` (static).
`colour = tex.rgb * _Color.rgb * lerp(1, SH(up) + sun * wrap(N·L) * _SunShare + _Emission, _Lit)`,
`alpha = pow(tex.a * _Color.a, _AlphaPower) * lerp(1, vertexColour.a, _VertexAlpha)`.
Properties: `_MainTex`, `_Color`, `_VertexAlpha` (surf 1 = shoreline closeness from the FBX vertex colour A), `_AlphaPower`, `_Lit`, `_SunShare`, `_Emission`, `_Wrap`.

## 4. Atmosphere (GolfAtmosphere.Holes) — Golf scene only
Called from `GolfGame.Awake` (camera null) and `GolfGame.StartHole` (after `HoleView.Build`, so the heading comes from the live hole).
Holes 8/9/10 only; any other number = the legacy numbers (sun Euler(50,-30,0) 1.1 white, ambient (.55,.6,.65) on the scene's own
ambient mode, fog (.75,.85,.95) 250..700, scene skybox, fill/rim/post off).
Azimuths are RELATIVE to the tee->pin heading H (0 = down the hole, -90 = golfer's left). Lights: key = the existing `Sun` (soft shadows),
fill = directional "Golf fill" (no shadows), rim = directional "Golf rim" (no shadows). Sky = `GolfArcade/TennisSky` material per hole
(`_Arc` 180, `_Heading` = H + offset, `_SunDir` = the key's direction). [v2: NO post-processing. The cloned TennisPost Volume was removed and `renderPostProcessing`
is forced false: post renders nowhere in this project, see v2.1.]

| | Needle 8 | Split 9 | Crater 10 |
|---|---|---|---|
| key az/el, colour, I | -50/30, (1,.86,.66), 2.3, shadow .72 | -75/42, (1,.95,.86), 2.3, shadow .70 | +40/32, (1,.80,.58), 2.3, shadow .78 |
| fill az/el, colour, I | 160/35, (.80,.88,1), .8 | 150/40, (.74,.85,1), .8 | 170/35, (.62,.55,.90), .55 |
| rim az/el, colour, I | 40/10, (1,.78,.55), .5 | 30/14, (1,.92,.80), .3 | none (lava point lights are the rim) |
| trilight sky/equator/ground | (.42,.58,.86)/(.68,.60,.52)/(.20,.30,.34) | (.42,.58,.86)/(.62,.64,.60)/(.20,.28,.26) | (.34,.24,.40)/(.55,.30,.22)/(.60,.22,.08) |
| fog colour, start..end (yd) | (.74,.82,.90) 200..1500 | (.72,.84,.95) 220..1700 | (.42,.19,.14) 120..1000 |
| sky texture | Tennis/Environment/SkyPanorama | SkyPanorama, COOLED copy (warm haze → blue-white, blue sky untouched; Course/Look/Sky_Split_C wins if present) | Course/Look/Sky_Crater_C (missing → generated ember→aubergine gradient) |
| sky heading offset, exposure | +45 (warm sunlit left half ahead), .95 | -45 (blue cumulus right half ahead), 1.0 | 0, .9 |
| _Horizon/_Zenith/_Sea/_SunColor | (1,.86,.7)/(.18,.45,.9)/(.16,.33,.58)/(1,.8,.52) | (.85,.92,1)/(.16,.46,.92)/(.14,.36,.62)/(1,.95,.85) | (.95,.45,.18)/(.14,.09,.14)/(.30,.12,.08)/(1,.45,.15) |

Why no rim on Crater: TennisURP is Forward with `AdditionalLightsPerObjectLimit` 2; fill + rim directionals would take both per-object
slots and the LAVA_LIGHT point lights would never light the basalt. Fog start ≥ 200 yd on the blue holes keeps the 200-yd-high
orthographic minimap clean. Fog end is beyond the 900-yd far plane on purpose: the horizon is at most ~55 % fogged (soft, not a wash).
The URP shadow distance (42) is not touched: far scenery is unshadowed (accepted by the brief).

Camera: `CameraRig` near plane .05 → .3 (depth precision for overlay meshes). Nothing else changed there.

## 5. Gates / how to verify
* `work/postcard-look/heavy.sh A2-smoke <Unity> -batchmode -projectPath Unity -executeMethod GolfArcade.EditorTools.GolfLookSmoke.Run -logFile <abs>`
  (`GOLF_LOOK_SMOKE_REPORT=<file>` writes the GATE lines): shaders compile and are supported (GolfSurf/TennisWater/TennisSky/URP Lit),
  every LK_ material (textured ones: `_BaseMap` + `_BumpMap` + `_NORMALMAP`; basalt/lava: `_EmissionMap` + `_EMISSION` + emission > 1.05;
  water: `GolfArcade/TennisWater`; surf/fall/smoke: `GolfArcade/GolfSurf`), hole_08/09/10.fbx.meta (isReadable, MikkTSpace tangents),
  Look/ texture import settings + ≤ 25 MB, hole 7 keeps the old rule, holes 8-10: water never flat, no LK_ slot flat, no prop colliders.
* Stills: `GOLF_STILLS_OUT=<dir> heavy.sh ... -executeMethod GolfArcade.EditorTools.PostcardCameraStills.Run` (the real game camera).
* Tuning A/B: `GOLF_LOOK_VARIANTS_OUT=<dir> heavy.sh ... -executeMethod GolfArcade.EditorTools.GolfLookVariants.Run` (in GolfLookSmoke.cs):
  per view `_full`, `_nofog`, `_nopost` and `_swatch` (real LK_ materials laid on the play surface + rock/masonry/basalt boxes,
  a waterfall sheet, surf, crater lava sheet + smoke card) under the real hole lights — works while the hole FBXs are still baseline.

Results of the A2 run (work/postcard-look/runtime/): `smoke_final.txt` 38/38 PASS; `sheet_before_after_atmosphere.jpg`
(before = the old stills, after = PostcardCameraStills on the same baseline FBXs); `sheet_swatch_final.jpg` (top: swatches,
bottom: full); `import_check_after_A2.txt` (PostcardImportCheck: ground/lie/marker gates PASS, 3 palette/lava gates FAIL by design, §7).

## 6. Decisions (A2) and why
* Hole 7 / non-postcard holes: HoleView uses EXACTLY the old rule (gate HOLE7_UNCHANGED_RULE: 245 palette slots flat, 0 different).
* Old MAT_* names on postcard holes stay flat (except water/lava): the baseline meshes have no tile UVs, a texture on them would be garbage.
* Crater key colour deviates from the role note (1,.52,.26): that turned the grass brown (155,134,51). (1,.80,.58) at 32° + HoleTint keeps it lime.
* Split sky = a cooled copy of SkyPanorama made at runtime (the phone camera sees only the painting's warm lowest band = sunset).
  A painted `Course/Look/Sky_Split_C` replaces it automatically if A1 ever adds one.
* Crater has no rim directional (per-object additional light limit 2; the LAVA_LIGHT point lights need a slot).
* GolfSurf computes fog per fragment (InitializeInputDataFog) for the same per-vertex-fog reason as above.

## 7. Project findings outside my files (reported, not changed)
* POST IS OFF PROJECT-WIDE: `TennisURP_Renderer.asset` (and `HeroBaseStudio_Renderer.asset`) have `postProcessData: {fileID: 0}`;
  URP 17 `UniversalRenderer.cs:456` "No postProcessData means that post processes are disabled". (A2's first build wired a cloned TennisPost Volume
  that nothing rendered: measured full vs post-off renders pixel-identical. v2: that wiring is REMOVED, golf renders without post by construction,
  see v2.1; the frozen tennis renderer is not touched, no bloom is added, and the golf look is made of lights and emission alone.)
* `ProjectSettings/QualitySettings.asset` (uncommitted, another chat): quality level 2 — the iPhone default AND the editor's current
  level — now uses `Assets/Characters/HeroBase/Rendering/HeroBaseStudioURP.asset` (per-object light limit 4) instead of TennisURP.
  Every Unity capture in this job therefore renders with HeroBaseStudioURP. Restore before shipping, or confirm it is intended.
* `PostcardImportCheck` (not mine): PALETTE_OVERRIDES_APPLIED / PALETTE_NO_LEAKS / LAVA_READS_ORANGE assume the old flat override;
  they must accept LK_ materials, TennisWater on WATER*, and an emissive textured LK_LAVA (see the A2 report for the run).


# v2 2026-10-04 (continue pass, area R: Unity runtime)

Everything above is the state at the pause; where this section disagrees, THIS section wins. Brief: `ArtDir/environments/14b_POSTCARD_LOOK_CONTINUE.txt`.
Evidence: `work/postcard-look/v2/runtime/` (`smoke_<label>.txt` gate reports with `logs/` and `shots/<label>/` board renders, `importcheck_*.txt`, `stills_test/`, `stills_test_board/`,
`look_textures_sha256_at_final_run.txt`). The final all-gates run is `smoke_s26.txt` (68/68 PASS after the review fixes, v2.12; `smoke_s24.txt` was 67/67 before them; textures as of 10:08 on 2026-10-04). Unity ran at the editor's active quality level 2 "Medium"
= `HeroBaseStudioURP` (see v2.9); the suite also runs under `TennisURP` by swapping the pipeline asset in memory.
Rollback copies of the two editor files I rewrote: `v2/runtime/GolfLookSmoke.cs.at_start`, `v2/runtime/PostcardImportCheck.cs.at_start`.

## v2.0 Scripts (all through heavy.sh, which waits for every other Unity / xcodebuild run; a run is about 1 minute)
| script (work/postcard-look/v2/runtime/) | what |
|---|---|
| `run_smoke.sh <label> [ENV=val ...]` | GolfLookSmoke (all gates below) -> `smoke_<label>.txt`, `logs/smoke_<label>.log`, `shots/<label>/*.jpg`. Env: `GOLF_LOOK_SWEEP=1` adds INFO sweeps (lava heat mapping, lava light intensity / range / lift, shelf and ocean colours, basalt emission); `GOLF_LOOK_LAVA_CANDIDATE=<dir with Lava_C/N/E.png>` and `GOLF_LOOK_SMOKE_CANDIDATE=<dir with Smoke_C.png>` render textures that are not installed yet (the board uses a material NOT named LK_, because `DressModel` would swap an LK_ name for the installed one) |
| `run_importcheck.sh <label>` | PostcardImportCheck -> `importcheck_<label>.txt` |
| `run_stills.sh <label> <outdir> [ENV=val ...]` | PostcardLookStills (never point `<outdir>` at ArtDir/screenshots/golf_postcards/look/ for a test) |
| `protected_check.sh` | PROTECTED_FILES: re-hash Unity/Assets/Scripts/Tennis, Resources/Tennis, Characters, ProjectSettings and diff against `v2/protected_hashes_start.txt` (same file types as that list: no .meta / .jpg / .anim) |
Exit code of the Unity commands: 0 = every gate PASS, 1 = at least one FAIL. Compile check = `grep -c "error CS"` of the log (the scripts print it).

## v2.1 Post-processing is gone from golf (NO_POST_DEPENDENCE)
Post renders nowhere in this project: `TennisURP_Renderer` and `HeroBaseStudio_Renderer` have `postProcessData` none (read by the smoke for both assets), so URP drops bloom / ACES / vignette.
`GolfAtmosphere` no longer creates the cloned TennisPost Volume and forces `renderPostProcessing = false` on the golf camera (`SetupCamera`; on postcard holes it still sets `antialiasing = None`, MSAA comes
from the pipeline asset, and `renderShadows = true`). The golf look therefore cannot change the day a renderer gets PostProcessData, nothing in it needs bloom, and there is NO tone mapper:
the frame is `sRGB(clip(light x albedo + emission))`. Comments that claimed post works are corrected (GolfAtmosphere class comment, GolfLook emission comment, the GolfGame hook comment, RUNTIME.md
sections 4 and 7). `GolfLookProbe.PostPreview` (post forced on in memory) was removed.
Gate NO_POST_DEPENDENCE: holes 8, 9, 10: `renderPostProcessing` false after `Apply`, 0 Volumes in the scene, the phone frame with post forced on is pixel-identical to off (max |diff| 0); both renderer assets have no
PostProcessData; no code line of GolfAtmosphere / GolfLook / HoleView names VolumeProfile / TennisPost / .Volume / Bloom / Tonemapping.

## v2.2 Crater lights, and the rule the hole builder must follow (LAVA_LIGHTS_REACH_BASALT, LAVA_LIGHTS_KEEP_GRASS_GREEN)
* `GolfAtmosphere.Look.FoldFillIntoAmbient` (true on Crater): the cool fill is NOT a directional light any more; its irradiance on flat ground (`colour x intensity x sin(elevation)`, in linear) is added to the
  ambient sky colour (`GolfAtmosphere.AmbientSkyOf(look)`). The table still holds FillColor / FillIntensity / FillElevation, so `v2/tools/lit_predict.py` (which parses them) stays right for flat ground. Reason: every
  additional directional takes one of a renderer's per-object light slots (TennisURP 2, HeroBaseStudioURP 4) that the LAVA_LIGHT point lights need.
* **A renderer only gets the lights nearest ITS bounds.** One 100 yd basalt mesh got ZERO light from point lights 6 yd away (the chosen light was 36 yd off); the same wall cut into five 20 yd chunks was lit
  identically under both assets. **Rule for the hole-10 builder: every ROCK_ wall / skin / column piece within ~25 yd of a LAVA_LIGHT_nn is its own mesh of about <= 20 yd extent; put 3-5 LAVA_LIGHT_nn empties
  about 2.4 yd over the lava, 10-25 yd apart, along the walls and around the pillar** (the spawned point light sits `GolfLook.LavaLightLift` = 4 yd above its empty; lights ignore transform scale).
* Numbers (GolfLook.LavaLightColor / Range / Intensity / Lift): colour (1,.45,.12), **range 52, intensity 600 (v2.12; 200 before the basalt was darkened), lift 4** (was 28 / 48 / 0, which lit 0.2 % of the basalt). Measured on the Crater board, identical under both
  assets: >= +8 luminance levels on 36.7 % of the wall pixels beside a light (gate >= 20 %), +7.7 on average; 0.0 % of the lava pixels brightened by >= 40 levels (gate <= 10 %, no hot spots).
* LAVA_LIGHTS_KEEP_GRASS_GREEN: a fairway ledge 6-40 yd from the lights keeps its hue with the lights on (70 -> 70, gate |shift| <= 4, G clipped 0.0 % <= 5).

## v2.3 Lava (LAVA_ORANGE_NO_BLOOM) and basalt (BASALT_GLOW_ORANGE)
**LK_LAVA is no longer URP Lit.** It is `GolfArcade/GolfLava` (`Resources/Course/Shaders/GolfLava.shader`, new): static, self-lit, one opaque pass, per-fragment distance fog, no lights, no shadows, no `_Time`.
The textures give HOW HOT a texel is and a 4-stop ramp inside the orange band gives its colour:
`heat = saturate(((gammaLum(Lava_C) x 1.5 + gammaLum(Lava_E) x 1.5 - .15 + relief) - .5) x 1.4 + .5)`, `colour = ramp(_Deep (150,33,10) @0, _Crust (186,43,13) @.2, _Flow (224,79,17) @.6, _Hot (255,128,28) @1)`.
All stops are hue 8..28, S >= .75; only `_Deep` (a few % of the texels, the dark-red accents of crater.jpg) is below V .7. Parameters: `GolfLook.Table["LK_LAVA"]` (`RampDeep/Crust/Flow/Hot`, `HeatAlbedo/Glow/Bias/Gain`, `Relief`); `Lava_N` adds relief to the heat.
Why not Lit + albedo + emission (measured on the Crater board with the installed Lava_C/E, `v2/runtime/smoke_s12..s15.txt`): the best tint x multiplier gave 76-78 % of the lava pixels in the band (needs 85 %); the texture's hue spread (red crust ..
yellow veins) is wider than hue 8..28, so brightening fixes "dark" and creates "yellow", and tinting G down creates "red" (R-clipped variants: 70 %). Also, with the sky reflection on (smoothness .3) 40 % of the pixels fell below S .75 (pink wash);
the first-build multiplier (2.6,2.4,2.2) clipped the fissure texel to cream. The ramp passes by construction and does not depend on the scene light, the angle or a tone mapper ("orange with emission alone", no multiplier left to drop).
Measured (installed textures, Crater key light, fog, 4 dressed LAVA_LIGHT lights, 900x1600): phone view in band **90.1 %**, 40-degree view **90.5 %** (misses: only the deep accents, 9.9 / 9.5 % dark), G clipped 0.0 %, cream 0.00 %,
mean (219,83,19) hue 19 S .91 V .86 (crater.jpg pool (212,62,14) h15 S.93 V.83). `v2/runtime/shots/s24/crater_lava_phone.jpg`, `sweep_*` renders in s20.
**Fallback / rollback:** if `GolfLava` is missing GolfLook builds the old Lit look (URP Lit + emission (1.0,.65,.50), tint .75, matte: `Spec.Emission/Tint/NoSpecular` kept for that); to go back for good set `Kind = Kind.Lit` on the
LK_LAVA row. Tunables for look changes: `HeatBias` (lower = redder, more crust; -.1 gave 93 % in band and a yellower flow), `HeatGain` (contrast), the four stops.
**LK_BASALT** (v2.12 changes its tint and makes it matte): `_EmissionColor` multiplier (1.0,.80,.50) (was 1.8 neutral, repair draft (1.5,.85,.5)); with the new Basalt_E the glow is 2.2 % of the wall (joints only), mean hue 16, the brightest quarter (crack cores) (255,131,41) hue 25,
cream 0.00 %, G clipped 0.00 %; lit wall median luminance 52. The old gates EMISSION_RENDERED_HUE and LAVA_CRUST_DARK encoded the dark-cell lava and the neutral multiplier and are gone.
Gates (GolfLookBoards.Crater): LAVA_ORANGE_NO_BLOOM phone + down: >= 85 % of the lava pixels hue 8..28, S >= .75, V >= .70, <= 5 % with G >= 250 (misses listed as dark / pale / yellow / red); BASALT_GLOW_ORANGE: the pixels the emission adds
>= 24 levels to: mean hue 8..32, the brightest quarter hue 12..34, cream <= 1 %, G clipped <= 5 %, coverage <= 20 %; BASALT_RENDERS_DARK: [v2.12: median <= 40 and mean S <= .25 with the emission off, and the wall beside the lava lights median <= 55 / S <= .65; the old <= 90 let a brown wall pass].
UV note from the texture agent (TEXTURES.md v2): Basalt_E glow is hottest at v = 0 mod 1, so author `v = (z - z_lava) / 8` on the walls and columns beside the lava to put the heat right above the pool.

## v2.4 Water colours (SHELF_COLOUR_NOT_LOUDEST, OCEAN_DEEP_BLUE)
The turquoise shelf (#1AC4C4 / #1096B2) was the loudest shape: lit mean (29,166,169) V .66 on Needle, (32,193,201) V .79 on Split. The stills' near-shore water is a mid teal: teal pixels (hue 170..200, S > .45) of needle.jpg / split.jpg have median
V .39-.40, luminance ~70, mean (31,87,101) / (20,80,103); their foam sits at V .72-.84 (luminance 167-190), their deep blue at (39,79,109) h205 / (48,102,140) h202.
* `LK_WATER_SHALLOW`: `_Shallow` #1B6A78, `_Deep` #165C74, `_Sky` (40,105,135). The two ends are nearly equal on purpose: TennisWater's gradient runs from the WORLD ORIGIN (the tee), not from the shore, so the shelf must look the same 30 or 340 yd out.
  Aerial view, real lights: Needle (24,89,103) hue 191 V .40 luminance 76; Split (27,105,124) hue 192 V .49 luminance 90 (foam 228 / 221, sky at the horizon 216 / 228).
* `LK_WATER` (open sea): `_Shallow` #0C5690, `_Deep` #063668, `_Sky` (28,108,156) (was #1268A8 / #083484 / (46,104,178): hue 215, V .63-.66, a little violet and bright next to the stills' h202-206). Phone view mean: Needle (48,100,141) hue 206 V .55, Split (43,101,147) hue 207 V .58.
* Gates (GolfLookBoards.Shelf, holes 8 and 9; aerial camera 45 yd up for shelf + foam, phone camera for the open sea and the sky): SHELF_COLOUR_NOT_LOUDEST [v2.12: no foam on the board any more, the foam clause is gone, see v2.12]: shelf mean hue 175..200, V <= .65, luminance <= .85 x the brightest foam patch (mean of the top 5 % of the LK_SURF pixels) AND below the sky
  just above the horizon; OCEAN_DEEP_BLUE: open-sea mean hue 195..215, S >= .45, V .35..78. The shelf WIDTH is the geometry agent's (1.5-4 m); the board uses a 6 yd shelf with a 2.5 yd surf strip on its shore side.

## v2.5 Grass hue, smoke
* **Grass (GRASS_HUE_LIT, informational for the calibration agent, passes)**: the texture agent re-hued Fairway_C / Green_C / Rough_C / Scrub_C (hue 73.6 / 72.4 / 68.1 / 49.9). Needle (table tint .94) and Crater (existing lime-keeping HoleTint) need no change; Split's old tint (.76,.84,.72) pushed the new albedo to
  hue 80, so `GolfLook.HoleTint` now holds the values the texture agent solved with `v2/tools/lit_predict.py`: `(9, LK_FAIRWAY) (.68,.66,.66)`, `LK_GREEN (.72,.70,.74)`, `LK_ROUGH (.77,.76,.77)`, `LK_SCRUB (.82,.82,.86)`; sand unchanged. The gate measures the central lower
  third of the phone frame filled by one material under the real hole lights (HoleTint, key, fill, ambient, no post): Needle fairway (186,200,72) h67, green h66, rough h60; Split fairway (147,165,68) h71, green h71, rough h67, ridge scrub (124,116,77) h49 (split.jpg (122,111,75) h46);
  Crater fairway (165,189,43) h70, green h69, rough h62 (stills 64..73; before: 86..100). Identical under TennisURP within 2 sRGB levels. Bands in the gate: fairway / green 60..76, rough 54..76.
* **Smoke (SMOKE_SOFT)** [v2.12 raises its opacity: the card below was too faint to pick out]: `LK_SMOKE` `_Color` alpha 1.0 (was .85), tint (.62,.56,.56), `_AlphaPower` 1, `_Emission` .05 (unchanged), NEW `_EdgeFade` .18 (GolfSurf.shader property, default 0 = off elsewhere: the alpha also fades to 0 over the outer 18 % of the card UV, so no texture can show a hard rim).
  The new Smoke_C peaks at alpha .486: effective alpha max .49 (the old one drew .77: a hard grey ball), border alpha 0.000, over the crater sky the card moves the frame by median 4.6 / p99 14.5 luminance levels (a faint translucent plume), edge step p99 1.03 levels/px.
  Gate: effective alpha max <= .55, border <= .02, frame delta p99 8..70 (visible, never a ball), edge step p99 <= 6. The texture agent notes the plume is thinner than crater.jpg's: the hole builder can scale the card up or stack two.

## v2.6 PostcardImportCheck (`GolfArcade.EditorTools.PostcardImportCheck.Run`, `run_importcheck.sh`)
Updated in place; the ground-height (3000 samples, play band 6 m), lie, marker, collider, hazard and placeholder gates are UNTOUCHED. The LK-aware rules live in `PostcardLookMaterialRules` (same file; the smoke calls it too, with `requireLkMeshes: false` while the flat baseline FBXs are installed).
For holes 8, 9, 10 (`CheckMaterials` -> `PostcardLookMaterialRules.Check(..., requireLkMeshes: true)`):
| line | meaning | result on the flat baseline FBXs (`importcheck_i2.txt`) |
|---|---|---|
| PALETTE_OVERRIDES_APPLIED | LK_ slot -> `GolfLook.GetForHole` material (textured URP Lit has `_BaseMap`); WATER* -> TennisWater / GolfSurf (lava: the self-lit lava or an emissive Lit); Palette names (gameplay MAT_FLAG/POLE/CUP/BALL, baseline MAT_*) -> flat game colour | PASS |
| PALETTE_NO_LEAKS | every slot is LK_, water/lava, a Palette name, or carries its own maps (LK_ names allowed on 8-10) | PASS |
| GROUND_ALBEDO_AND_NORMAL (new) | every LK_ ground material (URP Lit rows with a normal map: not PLANTS, the sea, GolfSurf cards, the lava shader) in the instantiated hole has `_BaseMap` AND `_BumpMap` with `_NORMALMAP` on; the hole carries LK_FAIRWAY, LK_GREEN, LK_ROUGH and >= 5 ground kinds | **FAIL until install** (0 LK_ ground slots) |
| NO_FLAT_POSTCARD_GROUND (new) | no visible renderer is a flat `_BaseColor`-only URP Lit (gameplay MAT_FLAG/POLE/CUP/BALL aside) | **FAIL until install** (MAT_ROCK x87 ... on Needle) |
| NO_LAVA_OUTSIDE_HOLE_10 / LAVA_RENDERER_PRESENT / LAVA_SHADER_RENDERS_IN_PIPELINE | as before; the shader may be `Universal Render Pipeline/*`, `Shader Graphs/*` or `GolfArcade/*` | PASS |
| LAVA_READS_ORANGE | the lava is self-lit GolfLava with every ramp stop hue 8..28 / S >= .75 (V >= .7 but `_Deep`) and both textures set; or (fallback Lit) emissive with a multiplier <= 1.5 whose brightest-5 % emission texels (read from the PNG) encode orange without clipping | PASS |
| NO_FOAM_STRIP_8_10, LAVA_LIGHTS_PLACED, ROCK_NEAR_LAVA_CHUNKED, LAVA_MAPPING_DENSITY (v2.12) | see v2.12 | foam FAIL on 8 and 9 until install, lights + chunking FAIL until install, LAVA_MAPPING_DENSITY PASS |
| HOLE7_MATERIALS_FLAT_AS_BEFORE (new, once) | `Cliffside()` hole 7 built through HoleView: every Palette slot is exactly `HoleView.Mat(colour)`, every other slot as imported, 0 LK_ slots, 0 lights added, shadow modes as the old rule | PASS (245 palette slots, 0 different, 169 renderers) |
Baseline result (v2.12: `importcheck_i4.txt`, 57 lines, 10 failed = the six below + NO_FOAM_STRIP_8_10 on 8 and 9 + LAVA_LIGHTS_PLACED + ROCK_NEAR_LAVA_CHUNKED; was 51 / 6): `POSTCARD_IMPORT_CHECK FAIL` = GROUND_ALBEDO_AND_NORMAL and NO_FLAT_POSTCARD_GROUND on each of the three holes. **Those two lines can only be proven on the real installed holes** (after the hole-build phase installs FBXs built with
`postcard_look_lib.export_look_fbx`). Until then they are proven on a scratch hole by the smoke gate IMPORTCHECK_INSTALL_LINES_PROVEN (primitive quads named and materialled like a rebuilt hole 10, instantiated and dressed like HoleView): all 7 LK-aware lines PASS on it, and three injected defects
(fairway left as flat MAT_FAIRWAY; a ground slot swapped to a flat URP Lit; a ground slot with no normal map) each fail the intended line. Every ground / lie / marker / collider gate PASSES on all three baseline holes.

## v2.7 Gate table (GolfLookSmoke; `smoke_s24.txt`, 67 gates; v2.12: `smoke_s26.txt`, 68 gates = + LK_RULES hole10 LAVA_MAPPING_DENSITY)
LAVA_ORANGE_NO_BLOOM (phone, down), BASALT_GLOW_ORANGE, BASALT_RENDERS_DARK, LAVA_LIGHTS_REACH_BASALT, LAVA_LIGHTS_KEEP_GRASS_GREEN, SHELF_COLOUR_NOT_LOUDEST (8, 9), OCEAN_DEEP_BLUE (8, 9), GRASS_HUE_LIT (8, 9, 10), SMOKE_SOFT, NO_POST_DEPENDENCE,
URP_BOTH_ASSETS, IMPORTCHECK_INSTALL_LINES_PROVEN, plus the older SHADER_OK x5 (now incl. GolfLava), MATERIAL LK_* x19 (the LK_LAVA row checks the ramp and its three textures), FBX_META x3, LOOK_TEXTURE_IMPORT, LOOK_FOLDER_SIZE, HOLE7_UNCHANGED_RULE and the per-hole
LK-rules / WATER_NEVER_FLAT / LK_NOT_FLAT / NO_PROP_COLLIDERS lines. 38 gates at the pause -> 53 after the repair draft -> 67 now; the two gates that encoded the old dark-cell lava / neutral multiplier were replaced, none was weakened.
The board suite runs three times: under the active asset (counted), then under TennisURP and HeroBaseStudioURP (reported as `[asset] ...` lines, summarised by URP_BOTH_ASSETS).

## v2.8 PostcardLookStills (`Unity/Assets/Editor/PostcardLookStills.cs`, `run_stills.sh`)
Play mode, the real GolfGame / HoleView / CameraRig / GolfAtmosphere, 900x1600 RenderTexture (MSAA 4), Canvas hidden, golfer / aim line / landing marker hidden, near .3, far 900; PNG output. `PostcardCameraStills.cs` (the older JPG tool) is untouched.
```
GOLF_STILLS_OUT=<dir>          default ArtDir/screenshots/golf_postcards/look/ (created). Test runs: always another dir, e.g. work/postcard-look/v2/runtime/stills_test
GOLF_STILLS_CFG=<shots.json>   a JSON file that REPLACES the default shot list (schema below)
GOLF_STILLS_HOLES=8,9,10       holes the DEFAULT list covers (default all three)
GOLF_STILLS_BOARD=1            lays the real LK_ materials on test strips in front of the tee (rough | fairway | green/sand, a lava sheet on Crater): proves the pipeline on the flat baseline. NEVER for proof shots
Unity -batchmode -projectPath Unity -executeMethod GolfArcade.EditorTools.PostcardLookStills.Run -logFile <abs>      (through work/postcard-look/heavy.sh)
```
Default shots (no cfg): `holeNN_tee` and `holeNN_approach` per hole through `CameraRig.FrameAddress` (4.5 yd behind the ball, 2.4 yd up, looking 1.5 yd ahead = the game's address framing): Needle tee (0,0)->(19,178), approach (19,178)->(-6,340);
Split tee (0,0)->(3,60), approach (11.8,235)->(6,416); Crater tee (0,0)->(14.3,66.2), approach (107.1,159.3)->(261,164.7) (course x, d).
cfg schema (example: `work/postcard-look/v2/runtime/stills_cfg_example.json`):
```
{ "shots": [
  { "name": "hole08_tee",  "hole": 8, "kind": "address",  "ball": [0, 0], "aim": [19, 178], "putting": false },
  { "name": "hole08_arch", "hole": 8, "kind": "landmark", "pos": [x, y, z], "look": [x, y, z], "fov": 50, "ball": [x, d] } ] }
```
* `address`: `ball` = [course x, course d] (the game ball is put there, resting on the ground under it), `aim` = [course x, d] of the target, optional `putting`. Needs `ball` and `aim`.
* `landmark` (the default kind when `pos` is present): `pos` / `look` are Unity WORLD YARDS (x right, y up with the play surface at 6.56, z down the hole); `fov` degrees, default 60; optional `ball` = [course x, course d] puts the game ball there (a shot can then prove the ball is not hidden by the path).
  Hole numbers must be 8, 9, 10; shots of one hole are taken together, in file order.
Output per shot `<name>.png`, plus `stills_stats.json`: `{ tool, unity, pipeline, qualityLevel, board, size:[900,1600], shots:[ { name, hole, file, camera:{pos, look, fov}, mean_rgb:[r,g,b] (0..255, whole frame), luminance,
central_lower_third:{ region:[x0,y0,x1,y1] px (y up), mean_rgb, mean_hsv:[h deg, s, v], luminance }, hue_bands:{ red_0_30, orange_30_60, ... rose_330_360 (12 bands of 30 deg), grey (S<.15), dark (V<.15) } (fractions of all pixels) } ] }`.
Tested on the flat baseline holes: 9 shots from the example cfg (3 landmark shots) in `v2/runtime/stills_test/`, and the 6 default shots with `GOLF_STILLS_BOARD=1` in `stills_test_board/` (a baseline FBX has no tile UVs, so board shots only prove the pipeline).
**v2 repair round 1:** `stills_stats.json` also carries a per-shot `"smoke"` block (the frame rendered a second time with the DRESS_SMOKE cards off) and `GOLF_STILLS_PIPELINE=<URP asset name>` renders under that asset in memory: see the last section of this file.

## v2.9 Which URP asset, and both
The editor's active quality level is 2 "Medium" (also the iPhone default), and `QualitySettings.asset` (another chat's uncommitted change, which I did not touch) points it at `Assets/Characters/HeroBase/Rendering/HeroBaseStudioURP.asset`; the other five levels use `TennisURP`.
The two assets are equal for everything the golf look uses (HDR on, MSAA 4, additional lights per pixel, main-light shadow map 2048, shadow distance 42 with 2 cascades, soft shadows, render scale 1) except the per-object additional-light limit: **TennisURP 2, HeroBaseStudioURP 4**;
neither renderer has PostProcessData. The smoke logs both assets' settings and runs the whole board suite under each by `QualitySettings.renderPipeline = asset` in memory (restored in a finally; `ProjectSettings` is never saved by me; `protected_check.sh` shows the folder byte-identical).
Result: 14/14 board gates PASS under each asset, same PASS/FAIL set, lava point lights reach the basalt identically (36.7 %), grass hue within 2 sRGB levels. The only asset-dependent thing is the per-object light limit, which is why Crater has no additional directional and why walls beside the lava must be small meshes (v2.2).

## v2.10 For the hole-build phase (code against this)
* Export with `postcard_look_lib.export_look_fbx`; material names exactly as LOOK_CONTRACT section 3. `LK_LAVA` -> `GolfArcade/GolfLava` is now WORLD-PROJECTED (v2.12): any `WATER_LAVA` mesh shows the swirl at one tile per 24 m with or without UVs (the old "a baseline mesh without UVs renders one flat orange" is fixed; UVs in tile units, metres / 24, are only read if `_WorldUV` is set to 0). `LK_WATER_SHALLOW` is TennisWater: world-space, no UVs; keep the shelf 1.5-4 m wide.
* Hole 10: LAVA_LIGHT_nn empties 3-5, about 2.4 yd over the lava, 10-25 yd apart, and every ROCK_ piece within ~25 yd of one is <= ~20 yd across (v2.2). Smoke cards `DRESS_SMOKE_nn` with `LK_SMOKE` (UV 0..1 over the card, vertex colour alpha 1): the card fades itself out at its edge; scale it up or stack two for a bigger plume.
* A mesh with `LK_` in its name that is not in `GolfLook.Table` falls back to the generic rule (textures `<PascalName>_C/_N`); the board candidates use non-LK_ names for that reason.
* After install: run `run_importcheck.sh` (GROUND_ALBEDO_AND_NORMAL and NO_FLAT_POSTCARD_GROUND must turn PASS on all three holes), `run_smoke.sh` and `run_stills.sh` with the real tee / approach / landmark shots into ArtDir/screenshots/golf_postcards/look/.

## v2.11 Open / unverified
* Everything above is measured on test boards (real LK_ materials, real lights, real camera geometry) or on the flat baseline holes; NOTHING is measured on the rebuilt hole meshes (not installed). Lava UV density, rock chunk sizes, shelf width and the real LAVA_LIGHT positions are the hole builders'; the numbers may move.
* `GolfLava` has no shadows, no light response and no animation by design; if Adnan wants the lava to react to the lava lights or to look "wet", the Lit fallback exists but measured 76-78 % in band.
* Basalt glow under the real basalt skin: the board uses one Basalt tile on a flat wall; hue is fine, coverage on real columns is unknown.
* The grass tints were verified against the new albedos on flat materials; shadows, bump shading on slopes and the golfer are not in the numbers. Golfer clipping under the new light rig (a pause finding) was not re-measured in this pass.
* Smoke: v2.12 raised the opacity (peak alpha .70, p99 delta 77 levels); the plume is still a thin single wisp next to crater.jpg's billows: the hole builder scales the card up or stacks two. Judge it on the real card in the Game view.
* Unity rewrites `ProjectSettings/QualitySettings.asset` (mtime changes) on exit of every batch run; the content hash stays identical to `protected_hashes_start.txt`.


## v2.12 Review-fix pass (2026-10-04, after the skeptic review of area R)
Evidence: `v2/runtime/smoke_s26.txt` (68/68 PASS, active asset HeroBaseStudioURP; 14/14 under TennisURP and 14/14 under HeroBaseStudioURP), `importcheck_i4.txt`, `stills_test_r2/`, `shots/s26/`, tuning sweeps `smoke_t1.txt`, `smoke_t2.txt`, `smoke_t4d.txt`.
New env for fast tuning (in memory only): `run_smoke.sh <label> GOLF_LOOK_TUNE=1 [GOLF_LOOK_SWEEP=1] [GOLF_LOOK_LAVA_I=600] [GOLF_LOOK_BASALT_TINT=r,g,b] [GOLF_LOOK_BASALT_MATTE=0|1] [GOLF_LOOK_SMOKE=r,g,b,gain,emission,lit]` runs only the Crater and smoke boards (45 s) with the basalt tint x matte x light-intensity and smoke sweeps. Use `bash`, not zsh, for loops over variants.

### Textures this pass was measured with
The texture agent re-installed the Look/ PNGs between 10:41 and 10:43 on 2026-10-04: 27 of 31 are byte-identical to `look_textures_sha256_at_final_run.txt`; **Lava_C / Lava_E / Lava_N and Smoke_C are new** (the new Smoke_C peaks at alpha .52, was .486). Every Unity run of this pass started after 10:47, so all v2.12 numbers use the new files (hashes: `look_textures_sha256_at_s26.txt`, no Look PNG changed after 10:44). With the new Lava the lava gate reads 92.6 % in band, mean (217,79,18) h18 (v2.3 says 90.1 % / (219,83,19) for the previous Lava). The texture agent was still iterating (v4) at the end of this pass: re-run `run_smoke.sh` after any further Look/ change.

### Basalt reads as charcoal, not brown planks (medium finding 1)
* Cause: Basalt_C is already dark and near-neutral (mean (39,36,38)); the brown came from the orange dusk key / ambient on a neutral albedo plus a smoothness .15 sky reflection that puts a floor of ~30 sRGB levels under ANY tint (dim linear values are large in sRGB: tint .5 only took the median from 52 to 41). The sweep (`smoke_t2.txt`) showed matte + a cool tint is what moves it.
* `LK_BASALT`: `NoSpecular = true` (matte: `_SPECULARHIGHLIGHTS_OFF`, `_ENVIRONMENTREFLECTIONS_OFF`) and `Tint (.52,.80,.92)` (sRGB). The orange light is cancelled by the cool tint. Key-lit wall facing the sun, emission off (worst case): mean (36,31,28), **median luminance 29, S .21** (was (69,52,43), 52, .37; crater.jpg basalt (26,25,29) .. (39,32,34), median 30..34, S .2..28). Wall beside the lava lights (lights on): mean (51,35,25), median 33, S .50 (crater.jpg's lava-lit rock (52,27,23), S .5..62). The glow (emission only) is unchanged: 2.1 % of the wall, joints only, mean hue 18, cream 0 %, G clipped 0 %.
* Because the darker rock answers the lava lights less, `GolfLook.LavaLightIntensity` 200 -> **600** (range 52, lift 4 unchanged): >= +8 luminance on 43.5 % of the wall near a light (gate >= 20 %), lava pixels brightened >= 40 levels 0 % (the lava is self-lit GolfLava: it cannot flare), grass ledge 6-40 yd from the lights keeps hue 70 -> 70 (gate |shift| <= 4). Same pass under both URP assets (limit 2 and 4). Intensity 900 also kept the grass at 70 -> 69.
* Gate BASALT_RENDERS_DARK is now: key-lit wall (emission off) median luminance <= 40 AND mean S <= .25; wall beside the lava lights median <= 55 AND mean S <= .65. It was "median <= 90" (a brown wall passed). Residual: the lightest 10 % of the columns have a slight green-grey cast (hue ~83, S .10); the mean is warm-neutral.

### Lava never depends on the mesh UVs (medium finding 2)
* `GolfArcade/GolfLava` gained `_WorldUV` (default 1) and `_WorldTile` (default .0381 = .9144 / 24 tiles per yard): the three maps are projected from the world (from above where |n.y| >= .5, from the side on walls), identical to the board's old UV (metres / 24), so every previous lava number is unchanged. `GolfLook.Spec.WorldUV` (true) and `GolfLook.LavaTilePerYard` carry it. The baseline hole 10 (a WATER_LAVA mesh with NO UVs) used to render one flat orange (`stills_test/hole10_lavarim.png`) and now shows the swirl (`stills_test_r2/hole10_lavarim.png`).
* New always-on ImportCheck line **LAVA_MAPPING_DENSITY** (hole 10): every lava material is GolfLava with the world projection at 1.00 +- 5 % of one tile per 24 m, or (mesh-UV mode `_WorldUV` 0) readable mesh UVs at metres / 24 +- 40 % and a UV span >= 2 tiles; and the lava covers >= 2 tiles across. Baseline: PASS (166.7 tiles). Proven on the scratch hole: lava switched to the mesh UVs of a unit quad over 120 yd FAILS it, a 30 yd lava (1.1 tiles) FAILS it.

### ImportCheck: foam, lava lights, rock chunking (low finding 3)
All three wait for install (INFO "would FAIL" on the flat baseline), like GROUND_ALBEDO_AND_NORMAL; each is proven on the scratch hole by IMPORTCHECK_INSTALL_LINES_PROVEN (passes on a good hole, fails on an injected defect):
* **NO_FOAM_STRIP_8_10** (runtime half of GATES.md NO_FOAM_STRIP; the Blender half measures shore coverage <= 25 %, runs <= 10 m, gaps >= 8 m): no WATER_FOAM* / DRESS_FOAM* renderer, no MAT_FOAM / MAT_SURF slot (the flat baseline has WATER_FOAM + WATER_FOAM_CREST on 8 and 9), every LK_SURF piece is a patch <= 12 yd long and two patches are >= 7 yd apart. Whitewater as SHORT PATCHES (what the ground library builds) passes; a 60 yd band, two patches 3 yd apart and a MAT_FOAM piece fail.
* **LAVA_LIGHTS_PLACED**: 3..5 `LAVA_LIGHT*` empties, nearest pair >= 8 yd, each 0.5..6 yd above the top of the lava and inside its footprint (+8 yd).
* **ROCK_NEAR_LAVA_CHUNKED**: every `ROCK_*` renderer whose bounds are within 25 yd of a LAVA_LIGHT empty is <= 24 yd across (a 70 yd wall fails; with 0 lights it fails too, no vacuous pass).
The shelf gate no longer depends on foam: see below.

### Shelf gate independent of foam (low finding 3)
The board has no surf strip any more. SHELF_COLOUR_NOT_LOUDEST (holes 8, 9): shelf mean hue 175..200, V <= .65, luminance <= 100 (stills' teal ~70) AND <= 1.3 x the open sea in the same aerial frame, never among the brightest 2 % of that frame (share <= 10 %), below the sky at the horizon. Measured: Needle shelf (24,89,103) h191 V .40 lum 76 vs sea lum 62, 0.0 % of the top 2 %; Split (27,105,124) h192 V .48 lum 90 vs sea 74 (the colour values are unchanged from v2.4). Colour retune not needed.

### Smoke readable (low finding 4)
`GolfSurf.shader` has a new `_AlphaGain` (default 1 = as painted) multiplying the painted alpha before the contrast power; `LK_SMOKE` (`GolfLook.Spec.AlphaGain`): tint (1,.95,.92), **gain 1.35** (peak alpha .70; the feathered edge, `_EdgeFade` .18 and border alpha 0 kept), self light .40, lit .8. Card over the Crater sky: moves the frame by median 8.4 / p99 80 levels (was 4.9 / 14.7); edge step p99 4.3 levels/px; brightest tenth of the plume ~ (190,150,140) vs crater.jpg's plume (183,154,150). SMOKE_SOFT is now: peak alpha .55..72, border <= .02, median delta >= 8, p99 28..90, edge step <= 6. The card is still one thin wisp: the hole builder scales it or stacks 2-3 (an alpha .70 card stacks).

### Install-phase items that stay open (low finding 5, not closable here)
Nothing is measured on rebuilt hole meshes yet (the FBXs are still the flat baseline until the hole-build phase installs them): GROUND_ALBEDO_AND_NORMAL, NO_FLAT_POSTCARD_GROUND (x3 holes), NO_FOAM_STRIP_8_10 (8, 9), LAVA_LIGHTS_PLACED, ROCK_NEAR_LAVA_CHUNKED fail on the baseline by design and are proven on the scratch hole. After install: run `run_importcheck.sh`, `run_smoke.sh`, `run_stills.sh` on the installed FBXs.


# v2 2026-10-04 calibration (area K: Game-view calibration, closed the loop under the golf key light)

Evidence: `work/postcard-look/v2/calibrate/` (`smoke_final.txt` = 81/81 gates, `importcheck_final.txt`, `calibration_stats.json`, Game-view sheets `sheet_grass_gameview.jpg`, `sheet_water_gameview.jpg`,
`sheet_crater_gameview.jpg`, `sheet_probe_views.jpg`, `shots_k5/` (the board renders of the final run), `stills_board_final/` (PostcardLookStills on the baseline holes with GOLF_STILLS_BOARD=1),
`probe_p4/` (GolfLookProbe on the ground library's smoke FBXs = real geometry through HoleView.BuildFromModel), `probe_p5/`, `logs/`, `tools/`). Active asset: `HeroBaseStudioURP` (quality level 2); the suite also runs
under `TennisURP` inside every smoke run (`URP_BOTH_ASSETS`: 27/27 under each, identical PASS/FAIL, grass within 2 sRGB levels): the assets do not differ materially for this look, so no separate TennisURP stills run was needed.
Textures were NOT changed (the 30 generated PNGs regenerate byte-identical, Look/ sha256 list before == after: `look_sha256_before.txt`, `look_sha256_after.txt`). `GolfAtmosphere.cs` (key 2.3, fill, rim, trilight, fog) and both shaders are UNCHANGED:
nothing clipped at key 2.3, so no light was lowered.

## K.0 What I changed (every constant, old -> new)
| file | constant | old | new | why |
|---|---|---|---|---|
| `GolfLook.cs` `HoleTint` | `(8, LK_FAIRWAY)` (new entry; was the table tint .94) | .94 | **(.87,.87,.87)** | Needle fairway lit V .78 (stills' (172,186,66) = V .73) -> (173,186,68) V .73 |
| `GolfLook.cs` `HoleTint` | `(8, LK_GREEN)` (new entry; was .94) | .94 | **(.88,.88,.88)** | Needle green V .77 -> (174,185,73) V .72 (still (171,181,64)) |
| `GolfLook.cs` `HoleTint` | `(9, LK_GREEN)` | (.72,.70,.74) | **(.72,.70,.70)** | Split green S .548 (< the stills' .55..66; split.jpg (154,173,75) S .57) -> (154,172,75) S .57, hue 71 unchanged |
| `GolfLook.cs` `HoleTint` | `(8, LK_PATH)` (new entry; was .94) | .94 | **(.86,.86,.86)** | Needle's warm key clipped 4.9 % of the flat path pixels (2.6 % at 255; limit 3 %); stills' flagstones V .63..70 -> 0.1 %, V .68 |
| `GolfLook.cs` `HoleTint` | `(8, LK_SAND)` (new entry; was the table tint .80) | .80 | **(.72,.74,.76)** | sand clipped 2.1 % (near the limit), V .92 / hue 32 against the stills' bunker sand (188,175,142) V .74 hue 43..47 -> (212,185,150) V .83, 0 % |
| `GolfLook.cs` `Table["LK_WATER_SHALLOW"]` | `Shallow` | (27,106,120) #1B6A78 | **(24,93,106)** | the thin shelf edge lit lum 77 (Needle) / 90 (Split) against the stills' teal 66 / 64 and the open sea 63 / 74: x .88 |
| same | `Deep` | (22,92,116) #165C74 | **(19,81,102)** | x .88 |
| same | `Sky` (fresnel target) | (40,105,135) | **(35,92,119)** | x .88 |
| `GolfLookSmoke.cs` | gates | GRASS_HUE_LIT (hue 60..76) | **GRASS_HUE_GAMEVIEW** (hue 64..73 / rough 58..72, S/V bands, scrub), **GRASS_NO_CLIP**, **SURFACES_NO_CLIP**, **SHELF_NOT_LOUDEST**, **SEA_NEAR_FAR_BLUE**, aliases **LAVA_GAMEVIEW_ORANGE**, **BASALT_JOINT_ORANGE**, **SMOKE_SOFT_GAMEVIEW** | see K.1; the old gate ids that still exist keep their thresholds (nothing weakened); GRASS_HUE_LIT was replaced by the stricter GRASS_HUE_GAMEVIEW |
| `GolfLookSmoke.cs` (GolfLookProbe) | probe | - | `Aerial()` (PROBE_SHELF_NOT_LOUDEST), env `GOLF_LOOK_PROBE_KEYSWEEP`, `GOLF_LOOK_PROBE_LAVAISWEEP` | in-memory sweeps, off unless the env var is set |

Not changed: `GolfAtmosphere.cs`, `GolfSurf.shader`, `GolfLava.shader`, `PostcardImportCheck.cs`, `HoleView.cs`, every texture, `LavaLight*`, `LK_BASALT`, `LK_SMOKE`, `LK_LAVA` rows.

## K.1 Gate table (final run `smoke_final.txt`, 81/81 PASS; board = the real LK_ material filling the phone frame under the hole's own lights, no post)
Thresholds: hue band of the stills' greens 64..73 (rough 58..72), S/V from the stills (Needle / Split fairway+green S .55..66 V .55..75, Crater S .72..88 V .55..75, rough V >= .45 / .40, Split scrub hue 40..58 S .30..50 V .40..60), clipped = any channel >= 250 on more than 3 % of the lower 60 % of the frame.
| gate | Needle (8) | Split (9) | Crater (10) |
|---|---|---|---|
| GRASS_HUE_GAMEVIEW fairway | (173,186,68) h66 S.63 V.73 (before (186,200,72) h67 S.64 V.78: **FAIL on V**) | (147,165,68) h71 S.59 V.65 | (165,189,43) h70 S.78 V.74 |
| green | (174,185,73) h66 S.61 V.72 (before V .77 FAIL) | (154,172,75) h71 S.57 V.67 (before S .548 FAIL) | (161,183,44) h69 S.76 V.72 |
| rough | (136,136,57) h60 S.58 V.54 | (121,129,61) h67 S.53 V.51 | (126,129,38) h62 S.71 V.50 |
| scrub (Split ridge) | - | (124,116,77) h49 S.38 V.49 (split.jpg (122,111,75) h46 S.39 V.48) | - |
| GRASS_NO_CLIP (>= 250 / 255) | 0.0 % / 0.0 % on all three materials | 0.0 % / 0.0 % (scrub too) | 0.0 % / 0.0 % |
| SURFACES_NO_CLIP (extra) | sand (212,185,150) 0.0 %, path (172,160,113) 0.1 % (before 4.9 % / 2.6 % at 255: FAIL), rock 0.0 %, masonry 0.0 % | sand (221,202,163), rock, masonry 0.0 % | sand (211,149,103), rock 0.0 % |
| SHELF_NOT_LOUDEST (1.5 yd typical edge, aerial 45 yd up) | (21,78,91) lum 67 <= 1.3 x the stills' teal 66 and <= 1.2 x the open sea beside it 63 = 75; 0.0 % of the brightest 2 % (before lum 77: FAIL) | (24,92,109) lum 79 <= 1.3 x 64 = 83 and <= 1.2 x 74 = 89; 0.0 % (before lum 90: FAIL) | - |
| SHELF_COLOUR_NOT_LOUDEST (6 yd worst-case pocket) | (22,78,91) lum 67 (before 76) | (24,92,109) lum 79 (before 90) | - |
| OCEAN_DEEP_BLUE / SEA_NEAR_FAR_BLUE | phone: (48,100,141) h206 S.66 V.55; near the tee (19,86,132) h205 S.86 V.52 lum 75, far (91,124,157) h210 S.42 V.61 lum 119 | (43,101,147) h207; near (20,91,143) lum 80, far (80,121,160) lum 115 | - |
The stills' water for comparison (measured on the jpgs): teal (hue 170..200, S > .45) needle (27,73,86) lum 66 V .36 / split (19,76,99) lum 64 V .38; blue needle (38,72,96) lum 62 / split (47,96,131) lum 90, far (80,137,182) V .71; white pixels (foam + clouds, S < .2 V > .7) are 9.5 % / 3.9 % of the stills' frames; ours is whitewater patches only.
The open sea itself was left alone: its hue (205..210) is the stills', but it is more saturated near the tee (S .86 vs the stills' .6..64) and brighter than needle.jpg's deep blue (lum 75 vs 62), less than split.jpg's (80 vs 90); within the existing OCEAN_DEEP_BLUE band, not part of the brief's fails.
| gate (Crater board, post OFF, no bloom) | value |
|---|---|
| LAVA_GAMEVIEW_ORANGE (= LAVA_ORANGE_NO_BLOOM phone + down) | 92.6 % / 92.6 % of the lava pixels in hue 8..28, S >= .75, V >= .70 (>= 85 %), G clipped 0.0 % (<= 5), cream 0.00 %, mean (217,79,18) h18 S.92 V.85 (crater.jpg pool (212,62,14) h15 S.93 V.83) |
| BASALT_JOINT_ORANGE (= BASALT_GLOW_ORANGE) | the joints (emission alone) are 2.6 % of the wall, mean hue 18, crack cores (253,128,28) hue 27, cream 0.00 %, G clipped 0.00 % |
| BASALT_RENDERS_DARK | key-lit wall median luminance 30 (<= 40), mean (36,32,30) S .16 (<= .25); beside the lava lights median 35 (<= 55), mean (52,36,26) S .49 (<= .65); the v4 Basalt/Smoke textures (T, 11:12) are the first ones measured in Unity: BASALT passes with S .16 (T's model said .17), the lava lights still reach 42.6 % of the wall (>= +8 luminance) |
| SMOKE_SOFT_GAMEVIEW (= SMOKE_SOFT) | effective alpha max .67 (T's model .672), border 0.000, median |delta lum| **14.8** (T's model 14.9), p99 **61.0** (61.5), edge step p99 2.43 (2.39): T's `smoke_model.py` predicted the Unity run within 1 %; painted peak .50 x AlphaGain 1.35 stays in the .55..72 band |
| UNITY_COMPILE_0_ERRORS | 0 `error CS` in smoke_k5 / importcheck_k5 / stills_k5 / probe_p4 / probe_p5 logs |
| NO_POST_DEPENDENCE | still PASS (no Volume, frame with post forced on == off) |

## K.2 Real geometry, real HoleView path (GolfLookProbe on the ground library's smoke FBXs; the real Resources/Course FBXs were not touched)
`v2/calibrate/tools/run_probe.sh <label>` (heavy.sh-locked) copies `lib_ground/smoke_hole0N/look/hole_0N.fbx` + a fresh-GUID .meta of the real import settings to `Unity/Assets/_GolfLookProbe/` only while it holds the lock and removes them on exit
(`PROBE_FBX10=<fbx>` swaps hole 10's FBX), then runs `GolfLookProbe.Run`. That is the baseline play surfaces + LK_ ground + thin shelf + graded ocean + whitewater patches + cliff skin (hole 10: lava + 4 LAVA_LIGHT empties), no props.
Phone camera, central lower third (hue / S / V / clipped >= 250 over the lower 60 % of the frame): Needle tee h65.7 S.61 V.72 0.05 %, green h66.6 S.62 V.73 0.00 %, arch h66.9 S.62 V.71; Split tee h70.7 S.57 V.67 0.06 %, green h70.7 S.57 V.70, ridge scrub h47.1 S.36 V.50
(split.jpg ridge (122,111,75) h46); Crater tee h69.7 S.78 V.71 0.03 %, green h68.6 S.73 V.68, lava edge h71.9 S.75 V.68. All inside the K.1 bands; the baseline-hole board strips agree (Needle h65.3 V.72, Split h70.2 V.64, Crater h69.6 V.72, 0 % clipped).
Aerial of the real shelf geometry (`PROBE_SHELF_NOT_LOUDEST`, new): Needle shelf 3,769 px = 0.26 % of the frame, mean (35,84,95) lum 74 vs the open sea beside it 83; Split 7,001 px = 0.49 %, (37,96,114) lum 85 vs 87; the shelf is **0.0 %** of the brightest 2 % of the frame (that is the sky). The shelf is a thin edge, not a halo (`sheet_water_gameview.jpg`).
Ground textured: PROBE_GROUND_TEXTURED 0.0 / 2.2 / 0.4 % flat tiles (Needle tee / green / arch), 0.0 / 0.1 / 4.8 % (Split), 0.0 / 0.8 / 0.1 % (Crater), all <= 15 %; the old 99.5 % flat of the installed baseline.

## K.3 Findings that are NOT closed here (install phase / other areas), and what to do about them
1. **Crater walls: `build_cliff_skin(..., piece_m=16)`.** G's default `piece_m=140` makes 15 ROCK_SKIN pieces up to 155 yd, so `ROCK_NEAR_LAVA_CHUNKED` FAILs on the real geometry (probe p1: ROCK_SKIN_01 134 yd, ROCK_SKIN_02 72 yd ...) and a renderer only gets the lights nearest ITS bounds (RUNTIME v2.2).
   I rebuilt the smoke hole 10 with `piece_m=16` (scratch wrapper `tools/smoke_piece.py`, G's 23 gates 0 failed, nothing written to the repo): 122 ROCK_SKIN pieces, widest **20.1 yd**, median 16.3 yd (`piece_sizes_piece16.txt`; default 140 m: 15 pieces, widest 154.7 yd, `piece_sizes_default140.txt`),
   and the probe on that FBX passes `ROCK_NEAR_LAVA_CHUNKED` (47 ROCK_ pieces within 25 yd of a lava light, none wider than 24 yd). **The hole-10 builder must pass `piece_m=16` to both `build_cliff_skin` calls** (the legacy ROCK_WALL pieces 65 yd wide are > 25 yd from every light).
2. **`NO_FOAM_STRIP_8_10` on G's hole 9 smoke FBX FAILS in the runtime check** (probe p1): `WATER_SURF_01` / `_20` are 4.0 yd apart and `WATER_SURF_03` / `_52` 6.0 yd apart (bounds to bounds; the runtime rule wants >= 7 yd), while G's own NO_FOAM_STRIP measures along the shore (min gap 14 m) and passes. The two definitions disagree
   on patches across the channel; not changed here (it is the "no white foam strip" line). Resolve at install: spread those patches or measure the gap along the shore in `PostcardLookMaterialRules.FoamRenderers`. Needle and Crater pass.
3. **Old probe gates that encode superseded designs** (they FAIL on the real geometry, not on this pass's gates): `PROBE_SURF_ALPHA` (expects a continuous strip's vertex-alpha fall-off, the patches average .17), `PROBE_LAVA_CRUST_DARK` (encodes the dark-cell lava: darker half lum 87 > 70, the lava is meant to be mostly bright now),
   `PROBE_LAVA_LIGHTS_REACH_BASALT` (witness view 18.2 % < 20 % on G's PLACEHOLDER light positions, unchanged by the chunking; the board measure is 42.6 %: re-measure with the real LAVA_LIGHT empties).
4. **Crater golfer skin: 17.9 % of skin pixels have R >= 250 (`GOLFER_NOT_CLIPPED hole10` FAIL in the probe; Needle 2.0 %, Split 3.5 % pass).** Not the lava lights (intensity sweep 600 -> 0: identical) and only weakly the key (2.3 -> 1.5: 17.9 -> 11.5 %): GolferView's flat skin under an orange key + the orange trilight ambient saturates R without a tone mapper.
   The golfer is GolferView's (flat HoleView.Mat colours), the grass and every gate in the brief are unclipped (0.0 %), so nothing was lowered. The golfer reads as a warm-lit figure (`probe_p3_golfer.jpg`: Needle / Split / Crater golfer at address); rerun the sweeps with `GOLF_LOOK_PROBE_KEYSWEEP=2.3,1.9,1.5 v2/calibrate/tools/run_probe.sh <label>`.
5. `LK_PATH` shimmer (G's open question): not checked in a Game view, the demo path is not in the probe FBXs' view; the board path (flat quad) shows no z-fighting. Check on the installed Needle.
6. Not measured: a physical iOS build (fog variants, half precision); shadows on slopes; props (no props in the probe FBXs); the Split ridge scrub reads as large soft blobs at the phone camera (hue/S/V are on target, the pattern is bigger-scale than split.jpg's streaky scrub).
7. The `_GolfLookProbe` temp assets are created and removed inside one heavy.sh lock; `git status` shows no `_GolfLookProbe`.

## K.4 Re-run
`work/postcard-look/v2/runtime/run_smoke.sh <label>` (all board gates, both URP assets), `run_importcheck.sh <label>`, `run_stills.sh <label> <outdir> GOLF_STILLS_BOARD=1`, `v2/calibrate/tools/run_probe.sh <label>`, `python3 v2/calibrate/tools/assemble.py` (stats JSON + sheets). Expected on the flat baseline FBXs:
`importcheck_final.txt` 57 gate lines + the POSTCARD_IMPORT_CHECK summary, 10 FAIL = GROUND_ALBEDO_AND_NORMAL x3, NO_FLAT_POSTCARD_GROUND x3, NO_FOAM_STRIP_8_10 (8, 9), LAVA_LIGHTS_PLACED, ROCK_NEAR_LAVA_CHUNKED (identical to `importcheck_i4`: install-only lines; every ground / lie / marker / collider gate PASSES).


# v2 2026-10-04 calibration, round 2 (area K, after the skeptic review of the first calibration)

Evidence: `work/postcard-look/v2/calibrate/r2/` (golfer exposure sweep `sheet_golfer_exposure_sweep.jpg`, `sheet_golfers_r2.jpg`, lava ramp sweeps `sheet_lava_tone.jpg` / `sheet_lava_tone2.jpg`, `sheet_crater_r2.jpg`, `sheet_probe_views_r2.jpg`, `sheet_aerials_r2.jpg`, `sheet_stills_board_r2.jpg`,
`tex_gates_r2b.log` (T's 136 texture gates, 0 FAIL), `look_sha256_before_r2.txt` / `look_sha256_after_r2.txt`, `protected_hashes_r2_snapshot1.txt`, `tools/` (lava_ramp_model.py, lava_ramp_search.py), `backup/` (the six files this round edited, as they were)); `v2/calibrate/calibration_stats_r2.json`; probe runs `v2/calibrate/probe_r2{a,b,f,g,race*,stale}/`;
smoke `v2/runtime/smoke_r2final.txt` (83/83), `smoke_r2tone*.txt` (sweeps); `v2/runtime/importcheck_r2final.txt`; stills `v2/calibrate/stills_board_r2/`. Active asset HeroBaseStudioURP (quality level 2); every smoke run also runs TennisURP and HeroBaseStudioURP (same PASS/FAIL). **No texture PNG was changed** (31 files, sha256 identical before / after).

## K2.0 The review's findings and what was done
| finding (review K) | severity | result |
|---|---|---|
| Crater golfer: skin R clipped on 17.9 % of its pixels (limit 5 %), blue shirt crushed to navy (37,49,64) | medium | **FIXED**: `GolfFigureExposure` (new, Course/) multiplies the golfer's `_BaseColor` per hole; Crater x(.76,.90,1.20). Skin clipped **1.6 %**, shirt (52,72,103) over 12,215 px (was 5,396), figure 2+ channels clipped 1.0 % (was 2.7 %). Needle and Split unchanged (white). New gate GOLFER_SHIRT_READABLE |
| hole-8 probe rendered the flat baseline in 3 of 6 runs (the gates read the swapped model, the frames the old one) | medium | **FIXED, cause only partly proven** (K2.2): the probe waits for >= 5 player-loop frames and exactly 1 HoleView, destroys stray HoleViews, and the new gate PROBE_SWAP_TOOK_EFFECT fails if the scene still holds a mesh of the installed FBX. 3 / 3 final runs textured on all 3 holes; self-test with the baseline injected FAILs on all 3 holes |
| lava reads as orange paint (no black crust) | low | **IMPROVED**: near-black crust ribbons, V < .4 on 3.5 % of the pool (was 0.0 %), still 92.7 % in band. Yellow-white veins NOT added (hue 8..28 band, K2.1) |
| basalt: greenish slabs, regular dash rhythm | low | greenish cast **FIXED** (tint G .80 -> .74, brightest tenth (55,60,55) hue 121 -> (55,55,54) neutral); dash rhythm / branching cracks **NOT changed** (texture generator, K2.3) |
| Split ridge scrub: large soft blobs, not streaks | low | NOT changed (texture side, hue / S / V on target; K2.3) |
| protected files: 14 changed + 14 new files in the protected tree | info | not ours; K2.4 |

## K2.1 Every constant changed (old -> new)
| file | constant | old | new | why |
|---|---|---|---|---|
| `Scripts/Course/GolfAtmosphere.cs` | `Look.FigureExposure` (new field, default white); `Holes[10]` | - | **(.76,.90,1.20)** | golfer skin / shirt under Crater's light (sweep in `probe_r2b`: (1,1,1) 17.9 %, (.85,.95,1.10) 7.9 %, (.80,.92,1.20) 3.7 %, (.75,.90,1.25) 0.9 %, (.70,.88,1.30) 0.0 % skin clipped; shirt (37,49,64) -> (54,75,95) / (53,73,103) / (52,71,106) / (52,70,110)). Needle / Split: white (2.0 % / 3.5 % clipped already pass) |
| `Scripts/Course/GolfFigureExposure.cs` (NEW) | `Set(Color)`, component on the GolferView object | - | - | MaterialPropertyBlock per renderer and material slot: `_BaseColor` x exposure. The golfer's materials are the hero shader's (TennisCustomization, frozen) and golf flat ones, so nothing shared is edited; white clears every block; re-applied when the model is rebuilt (restyle); `GolfAtmosphere.Apply` sets it (Legacy puts it back to white) |
| `Scripts/Course/GolfLook.cs` `Table["LK_LAVA"]` | `RampDeep` | (150,33,10) | **(24,6,3)** (hue 8.6, S .88: stays in the hue / S band, `_Deep` is the one stop allowed below V .7) | near-black crust ribbons |
| same | `RampCrust` | (186,43,13) | **(210,52,16)** | keeps V = .70 reached at the same heat (T's model: crust share 13.2 %, limit 14) so the darker `_Deep` does not widen the dark share |
| `Spec` default (read by T's gates) | `HeatBias` | -.15 | **-.16** | a little more crust (T's model gates still all pass: LAVA_FLOW_BRIGHT crust 13.2 % (6..14), hot 10.2 %, flow 69.7 %, in band 86.9 %; LAVA_NOT_CELLS median aspect 2.97) |
| `Scripts/Course/GolfLook.cs` `Table["LK_BASALT"]` | `Tint` | (.52,.80,.92) | **(.52,.74,.90)** | brightest tenth of the key-lit wall (55,60,55) hue 121 -> (55,55,54) hue 32 S .03; wall mean (36,32,30) -> (36,29,29) S .16 -> .18 (limit .25), median 30 -> 28; T's lit-darkness model passes with the live tint |
| `Editor/GolfLookSmoke.cs` | probe waiting, `PROBE_SWAP_TOOK_EFFECT`, `GOLF_LOOK_PROBE_RACE`, `GOLF_LOOK_PROBE_SELFTEST=stale`, `GOLF_LOOK_PROBE_EXPOSURE`, `GOLF_LOOK_TONE`; gates GOLFER_SHIRT_READABLE, LAVA_HAS_CRUST, BASALT_NOT_GREEN, PROBE_LAVA_HAS_CRUST | - | see K2.2 / K2.4 | new gates; **PROBE_LAVA_CRUST_DARK retired** to an INFO line (it asked for "darker half of the lava luminance <= 70", the dark-cell design; it measured 86..87 and failed since the first calibration, and cannot hold with the lead's 85 % in-band rule; replaced by PROBE_LAVA_HAS_CRUST on real geometry) |
| `Editor/PostcardLookStills.cs` | settle logic | 30 editor ticks | **>= 5 player frames and exactly 1 HoleView**, exit code 2 if a shot was taken unsettled | same race as the probe; the install phase's proof shots must not show the previous hole |

Not changed: the 31 textures, `GolfAtmosphere` key / fill / rim / ambient / fog (nothing clips at key 2.3), both shaders, `HoleView.cs`, `PostcardImportCheck.cs`, `LavaLight*`, LK_SMOKE, every HoleTint, QualitySettings, tennis files.

## K2.2 Gate table (final; `smoke_r2final.txt` = 83/83 PASS under HeroBaseStudioURP, TennisURP and HeroBaseStudioURP blocks identical; probes `probe_r2f`, `probe_r2g`; ImportCheck `importcheck_r2final.txt`)
| gate | result |
|---|---|
| GRASS_HUE_GAMEVIEW hole 8 / 9 / 10 | fairway h66 (173,186,68) / h71 (147,165,68) / h70 (165,189,43); green h66 / h71 / h69; rough h60 / h67 / h62 (bands 64..73, rough 58..72, S / V in the stills' ranges); Split scrub h49. Unchanged from round 1 |
| GRASS_NO_CLIP | 0.0 % (>= 250 and 255) on every grass material of all three holes |
| SHELF_NOT_LOUDEST / SEA_NEAR_FAR_BLUE | Needle shelf lum 67 (<= 1.3 x the stills' 66, <= 1.2 x the sea 63 = 75), 0.0 % of the brightest 2 %; Split 79 (<= 83, <= 89), 0.0 %. Real shelf geometry (probe aerials): Needle 0.26 % of the frame lum 75 vs sea 83; Split 0.49 % lum 85 vs 87. Sea near / far h205 / h210 |
| LAVA_GAMEVIEW_ORANGE | phone 92.7 % / down 92.8 % in hue 8..28, S >= .75, V >= .70 (>= 85), G clipped 0.0 %, mean (216,78,18) h18 (still (212,62,14) h15) |
| **LAVA_HAS_CRUST (new)** / PROBE_LAVA_HAS_CRUST (new, real geometry) | V < .4 on **3.5 %** of 911,933 lava px, luminance sd 26.5 (round 1: 0.0 %, 23.3); real geometry rim view 3.3 % of 391,733 px, in band 93.4 %. The still's pool is 12..30 % darker than V .4; the 85 % rule leaves 15 % for everything that is not bright orange |
| BASALT_JOINT_ORANGE / BASALT_GLOW_ORANGE | joints 2.6 % of the wall, mean hue 18, crack cores (253,127,28) h26, cream 0.00 %, G clipped 0.00 % |
| **BASALT_NOT_GREEN (new)** | brightest tenth of the key-lit wall (55,55,54) hue 32 S .03 (round 1: (55,60,55) hue 121 S .07 = FAIL under this gate) |
| BASALT_RENDERS_DARK / LAVA_LIGHTS_REACH_BASALT | wall median 28 (<= 40), mean (36,29,29) S .18 (<= .25); beside the lights median 33 (<= 55), mean (52,33,26); lights reach 40.9 % of the wall (>= 20) |
| SMOKE_SOFT_GAMEVIEW | effective alpha .67, median 14.8, p99 61.0, edge step 2.43 (unchanged) |
| GOLFER_NOT_CLIPPED hole 8 / 9 / **10** | 2.0 % / 3.5 % / **1.6 %** skin clipped (<= 5 %); shirt 0.0 % / 1.1 % / 0.0 % |
| **GOLFER_SHIRT_READABLE (new)** hole 8 / 9 / 10 | shirt px 15,672 / 16,589 / 12,215 (>= 60 % of the legacy light's), luminance 94 / 100 / 70 (>= 60 % of the legacy 84 = 50), B - R 80 / 92 / 50 (>= 20) |
| **PROBE_SWAP_TOOK_EFFECT (new)** hole 8 / 9 / 10, runs r2f / r2g | PASS x 3 holes x 2 runs: 1 HoleView, 1 'Course model', 0 MeshFilters still on the installed baseline FBX, 128 / 560 / 259 probe meshes, 5 player frames; PROBE_GROUND_TEXTURED hole 8 tee 0.0 % flat, green 2.2 %, arch 0.4 % in every run. Self-test (`GOLF_LOOK_PROBE_SELFTEST=stale`, baseline model injected): FAIL on all 3 holes (105 / 480 / 244 stale mesh filters), so the gate sees the symptom. `GOLF_LOOK_PROBE_RACE=1` (the old 30-tick wait) 5 runs: 1-2 player frames elapsed in 30 ticks, previous HoleView already gone, 0 failures: **the reviewer's 3 failing runs were not reproduced, so the old failure's cause is not proven** (a hole-8 render with 0 frames after StartHole would leave the old model alive; the new wait and gate make that impossible to miss) |
| PostcardImportCheck (`importcheck_r2final.txt`) | 57 gate lines, 10 FAIL, identical to round 1 and install-only by design: GROUND_ALBEDO_AND_NORMAL x3, NO_FLAT_POSTCARD_GROUND x3, NO_FOAM_STRIP_8_10 (holes 8, 9), LAVA_LIGHTS_PLACED, ROCK_NEAR_LAVA_CHUNKED. Every ground-height, lie, marker, collider and sample-coverage line PASSES |
| Probe gates still FAIL (58 / 63, same on r2f / r2g) | PROBE_SURF_ALPHA hole 8 and 9 (expects the old continuous strip's vertex-alpha fall-off; the patches average .17), NO_FOAM_STRIP_8_10 hole 9 on G's smoke FBX (WATER_SURF_01 / _20 4.0 yd and _03 / _52 6.0 yd apart by bounds; runtime wants >= 7), ROCK_NEAR_LAVA_CHUNKED hole 10 (G's default `piece_m=140`: pass `piece_m=16`, K.3 item 1), PROBE_LAVA_LIGHTS_REACH_BASALT hole 10 (witness view 17.5 % < 20 % on G's placeholder light positions; the board measure is 40.9 %). None needs a code change here: all wait for the install phase |
| T's texture gates (`tex_gates_r2b.log`, they read GolfLook.cs live) | 136 GATE lines, 0 FAIL, incl. LAVA_FLOW_BRIGHT, LAVA_NOT_CELLS, BASALT lit darkness with the new tint, SMOKE_SOFT |
| UNITY_COMPILE_0_ERRORS | 0 `error CS` in smoke_r2final / importcheck_r2final / stills_r2final / probe_r2f / probe_r2g. **A later recompile of the main project is blocked by another chat's work in progress** (`Assets/Scripts/Multiplayer/SportsMultiplayer.cs` calls `GolfGame.ConfigureNetwork` / `TennisGame.ConfigureNetwork` / `PredictNetworkSwing`, not defined yet; 12 error CS at 16:36). Not a golf file, not edited; see K2.4 for the final status |

## K2.3 Not done, and why
* **Yellow-white hot veins in the lava.** crater.jpg has them, but the lead's gate is >= 85 % of the lava pixels in hue 8..28 and the ramp stops are gated to that band; a yellow vein is outside it. `_Hot` stays (255,128,28) hue 26.
* **Basalt dash rhythm / branching cracks.** The glow is vertical-joint-only by T's gates (27 vertical stretches, 0 violations); branching diagonal cracks would break that definition, and the regular rhythm in the board render is the 8 m tile repeated 7 times across a 60 yd board wall. On real hole-10 geometry the hole builder breaks it with per-patch UV offsets or a second tile scale (TEXTURES.md "UV note"). Judge on the installed wall.
* **Split ridge scrub streaks.** Scrub_C hue / S / V are on target (h49 S.38 V.49 vs split.jpg h46 S.39 V.48); the pattern is bigger-scale than the still's. Texture side, not changed (it would re-open ALBEDO_DISTINCT and LOOK_FILES).
* Not measured: a physical iOS player build; the lava / basalt / golfer on the installed holes (the FBXs are still the flat baseline); the golfer's white shoes read slightly lilac at B 1.20 in the shade (visible in `sheet_golfers_r2.jpg`), accepted.

## K2.4 Re-run, and the state of the protected files
`v2/calibrate/tools/run_r2_final.sh` runs 3 probes + the race and stale self-tests + smoke + ImportCheck + stills one after another (heavy.sh each); `GOLF_LOOK_PROBE_EXPOSURE="r,g,b;r,g,b"` (golfer exposure sweep), `GOLF_LOOK_TONE=1` (lava ramp and basalt tint sweeps) are in-memory only. `python3 v2/calibrate/tools/assemble_r2.py <smoke label> <probe labels> <stills dir>` rebuilds `calibration_stats_r2.json` and the sheets.
`v2/calibrate/tools/protected_r2.sh`: the files the user named (QualitySettings.asset, every Characters shader, Resources/Tennis/Shaders, TennisPost, TennisURP*, HeroBaseStudio*) are **identical to the job-start hashes** (15 files); the whole protected tree is identical to its snapshot at the start of this round (509 files). Against the job-start list (`v2/protected_hashes_start.txt`, 495 files) 14 files changed and 14 were added by OTHER chats before this round began (12 `Scripts/Tennis/*.cs`, the 2 `Customization/Player*.prefab`, 12 `Characters/MatchHeroes/*_{Emote,Intro}_*.fbx`, `TennisAimPractice.cs`, `TennisShoulderCamera.cs`); this agent wrote none of them (its write set: the files in K2.1, `work/postcard-look/`).
`guards.sh`: 7 PASS (hole_07.blend / .fbx / .meta, Hole.cs hash, Postcards() no drift, GolfGame starts Postcards(), Cliffside()).


# v2 2026-10-04 area U (Unity + gate-tool finish, second continue pass)

Evidence: `work/postcard-look/v2/unity_u/` (wrappers `run_importcheck_staged.sh`, `run_final_unity.sh`, `run_probes_a.sh`; `smoke_u1/u2/u3.run.txt`, `importcheck_*.txt`, `probe_*.out`, `GolfAtmosphere.cs.at_u_start` / `GolfLook.cs.at_u_start` = the files as this pass found them, `GolfAtmosphere.cs.M5_attempt` = the lighting-side attempt below), probe runs `v2/calibrate/probe_ua1..5` (before), `probe_uf1..5` (final code), `probe_uls1..4` + `probe_uex9` (sweeps), smoke `v2/runtime/smoke_u1.txt` / `smoke_u2.txt` (M5 attempt) / `smoke_u3.txt` (final: **83/83 PASS**, TennisURP 29/29, HeroBaseStudioURP 29/29), staged importcheck `v2/unity_u/importcheck_us2.txt`. Every Unity run went through `heavy.sh`; 0 `error CS` in every log. Files edited by this area: `Editor/GolfLookSmoke.cs`, `Editor/PostcardImportCheck.cs`, `RUNTIME.md`, `GATES.md`, `blender/scripts/postcard_look_verify.py`. `GolfAtmosphere.cs`, `GolfLook.cs`, `HoleView.cs`, `GolfGame.cs`, `CameraRig.cs`, `GolfSurf.shader`, `PostcardLookStills.cs`: **unchanged** by this pass (checked against the `.at_u_start` copies).

## U.1 Crater golfer clipping: what is true now, and the lighting-side study (item a)
Starting point (read, not assumed): the reviewers' 17.9 % / crushed navy shirt was already answered by round 2 of the calibration (`GolfFigureExposure`, Crater x(.76,.90,1.20) on the golfer's `_BaseColor`; GolferView.cs is untouched, nothing shared is edited). Measured again, **5 runs of the probe on the final code** (`probe_uf1..5`, identical to the digit; `probe_ua1..5` before the last edits identical too):
| hole | skin px with a channel >= 250 (limit 5 %) | shirt | figure 2+ channels clipped |
|---|---|---|---|
| 8 Needle | 1.9 % | (55,97,132) 15,889 px (legacy light 16,728), luminance 91 | 3.6 % (limit max(5 %, legacy 5.3 % + 2)) |
| 9 Split | 3.3 % | (56,105,145) 16,749 px, luminance 97 | 6.9 % (legacy 5.5 % + 2 = 7.5) |
| 10 Crater | **0.8 %** (was 17.9 %) | (50,69,97) 12,481 px (was (37,49,64) over 5,396), luminance 67, B - R 47 | 0.4 % |
GOLFER_NOT_CLIPPED and GOLFER_SHIRT_READABLE PASS on all three holes in all 5 runs (a gate, repeated more than twice).
**Lighting-side first, as the brief asks: measured, and it does not work without breaking other gates.** `GOLF_LOOK_PROBE_LIGHTSWEEP` (new, in memory only: key intensity / colour / elevation, equator / sky / ground ambient, fill, exposure per variant; prints the golfer AND the grass of the tee view in one line; `GOLF_LOOK_PROBE_HOLES=10` limits it to one hole) over 28 variants (`probe_uls1..4`), no figure exposure:
| variant (Crater) | skin clipped | shirt | tee ground | verdict |
|---|---|---|---|---|
| as the old numbers (key 2.3) | 17.4 % | (33,43,56) 5,016 px: crushed | (167,188,40) h69 V .74 | the finding |
| key 1.8 / 1.5 / 1.2 | 13.2 / 9.0 / **3.1 %** | (33,44,57) .. (34,46,59) 5.7-7.0k px: still crushed | V .67 / .63 / .58 | the key alone fixes the skin only at ~1.2, never the shirt |
| key colour (.8,.78,.66) key 2.0 | 1.1 % | (41,68,83) 13k px | **h79**, V .68 | the dusk key stops being orange; grass leaves the hue band 64..73 |
| sun elevation 45 / 55 at constant ground (k 1.7 / 1.5); 60 with a purple equator (k 1.4) | 11.6 / 7.8 / 6.3 % | (34,46,58) crushed / crushed / (35,52,78) | (165,189,41) h70 V .74 in all three | up-facing skin shares the ground's irradiance: a ground lit to V .74 clips skin whatever the sun angle |
| **M5: key 1.25, fill 1.5 (folded into the sky ambient), equator (.40,.34,.56)** | **2.2 %** | **(39,61,94) 13.6k px** | **(136,160,40) h72 V .63 = crater.jpg's fairway (136,161,26) V .63** | fixes the golfer, **but see the smoke below** |
Why it clips: the golfer is flat URP Lit (smoothness .1), skin albedo R .76 linear; with no tone mapper any up-facing skin lit by the ground's irradiance (R ~ .39 linear at V .74) is > 1.0 in R, and its blue shirt (B albedo .43) only receives blue from the ambient equator (.22 in B), not from the orange key. **M5 was installed and run through the whole smoke** (`smoke_u2.txt`, 80/83): `BASALT_NOT_GREEN` FAIL (the brightest tenth of the key-lit wall is (42,43,57) hue 235, a purple-blue wall), `BASALT_RENDERS_DARK` FAIL (wall S .34 > .25), `GRASS_HUE_GAMEVIEW hole10` FAIL (fairway h75 / green h74 > 73, rough V .38 < .40): the blue equator that the shirt needs paints the vertical basalt blue and moves the grass hue, and the basalt tint (.52,.74,.90) and Crater's HoleTint rows (texture agent's) were solved for the orange key. Fixing those means re-solving two other owners' tint rows, so M5 was **reverted** (`GolfAtmosphere.cs` is byte-identical to its start copy; the attempt is kept as `unity_u/GolfAtmosphere.cs.M5_attempt`). **Last resort kept, minimal, per hole, disclosed:** the round-2 `FigureExposure` on Crater only (a multiplier on the golfer's `_BaseColor`: the light, the walls and every other gate are untouched). One by-product worth knowing, not acted on: M5's ground matches the still better than the shipped one (R,G equal, V .63 vs the shipped .74), so the Crater key could come down ~20 % when the tints are next solved.
**Split below 1 % (asked "if cheap"): not cheap.** `GOLF_LOOK_PROBE_EXPOSURE` sweep on hole 9 (`probe_uex9`): (1,1,1) 3.3 %, (.95,.98,1) 2.3 %, (.92,.97,1) 1.9 %, (.90,.96,1) 1.7 %, (.88,.95,1) 1.5 %, (.85,.95,1.04) 1.2 % and the skin mean drifts (144,113,92) -> (128,109,93); the remaining clipped pixels are the cream trousers / white kit, not skin. Split already passes (3.3 % <= 5 %, legacy 0.0 %), so nothing was changed.

## U.2 Hole 8 probe determinism (item b)
The reviewers' flat-baseline hole-8 renders (3 of 6) were already answered by round 2 (the probe waits for >= 5 player frames and exactly one HoleView, destroys stray HoleViews, `PROBE_SWAP_TOOK_EFFECT`; the old race was not reproducible: 5 of 5 `GOLF_LOOK_PROBE_RACE=1` runs were fine). This pass makes the gate **fail loudly unless the instantiated model carries LK_ materials**: `PROBE_SWAP_TOOK_EFFECT` now also needs >= 20 renderers of the `Course model` with an `LK_` material (GolfLook names its materials by key; the flat baseline FBX carries none). Final code, 5 runs (`probe_uf1..5`): hole 8 **5 of 5 textured** (`PROBE_GROUND_TEXTURED` tee 0.0 %, green 1.3 %, arch 0.2 % flat tiles, <= 15), swap gate PASS on all three holes in all 5 runs: 1 HoleView, 1 'Course model', 0 baseline meshes, **122 of 128 / 554 of 560 / 253 of 259 renderers carry an LK_ material**. `GOLF_LOOK_PROBE_SELFTEST=stale` (baseline injected) still FAILs the gate (round 2: 105 / 480 / 244 stale mesh filters).

## U.3 PostcardImportCheck (item d)
New **preview mode**: `POSTCARD_IMPORT_ASSETS=Assets/_GolfLookProbe` runs every gate on the STAGED FBXs of that folder (swapped in through `HoleView.BuildFromModel`, the real load path; wrapper `unity_u/run_importcheck_staged.sh <label>` copies `v2/hole0N/stage/hole_0N.fbx` with a fresh-GUID `.meta` of the real import settings under `heavy.sh`, nothing is installed, the temp folder is removed). Result on the three staged builds (sha256 in `importcheck_us2.staged_sha256.txt`: eecb67c0..., fe4e6d4c..., f06bc1b2...): **`importcheck_us2.txt`: 57 gate lines, 0 failed, exit 0.** Per hole: PALETTE_OVERRIDES_APPLIED / PALETTE_NO_LEAKS PASS with 899 / 899 / 685 LK_ slots textured by GolfLook (LK_ names accepted), GROUND_ALBEDO_AND_NORMAL PASS (10 / 10 / 5 ground kinds, every one with base map + normal map + `_NORMALMAP`), NO_FLAT_POSTCARD_GROUND PASS, NO_FOAM_STRIP_8_10 PASS, hole 10 LAVA_LIGHTS_PLACED PASS (5 empties, nearest pair 50 yd, 0.5-6 yd over the lava), ROCK_NEAR_LAVA_CHUNKED PASS (71 pieces within 25 yd of a light, none wider than 24 yd), LAVA_READS_ORANGE / LAVA_MAPPING_DENSITY (30.4 tiles) PASS; **ground height (3000 samples: 412 / 1353 / 323 land, 2383 / 1410 / 2531 water, land 6.56..6.89 yd, water 0), lie, marker, collider, hazard-centre and placeholder lines unchanged and PASS**; HOLE7_MATERIALS_FLAT_AS_BEFORE PASS.
One real fix: the staged hole 8 failed `NO_FOAM_STRIP_8_10` first (`WATER_SURF_13` and `_14` "only 5.8 yd apart") because the runtime rule measured the gap between axis-aligned BOUNDS, which over-states how close two DIAGONAL patches are (K.3 item 2 had flagged the disagreement with the Blender gate, which measures along the shore: min gap 15 m). `FoamRenderers` now measures the real plan distance between the two patch meshes (vertex to edge both ways, containment = 0) when the bounds say 'too close'; the 7 yd limit is unchanged. Measured with the Blender probe `v2/gates/tools/surf_pair_gap.py`: the pair is 5.83 yd by bounds and **7.13 yd by mesh** (margin 0.13 yd: thin, a rebuild with other patch seeds can fail it); hole 9 has no pair under 7 yd; on G's smoke FBX of hole 9 the same rule still FAILS (4.2 and 6.5 yd by mesh vs 4.0 / 6.0 by bounds: the rule is not hiding real strips). The smoke gate IMPORTCHECK_INSTALL_LINES_PROVEN (good scratch hole passes, injected defects fail: 60 yd band, two patches 3 yd apart, a MAT_FOAM piece) still passes (`smoke_u3.txt`).
**Which holes still wait on install.** On the INSTALLED files (`importcheck_u3.txt`, 57 lines, 10 failed): holes 8, 9 and 10 are all still the flat baseline (FBX mtimes Oct 3 18:56 / 18:04 / 17:56), so `GROUND_ALBEDO_AND_NORMAL` and `NO_FLAT_POSTCARD_GROUND` (x3), `NO_FOAM_STRIP_8_10` (holes 8, 9) and `LAVA_LIGHTS_PLACED` / `ROCK_NEAR_LAVA_CHUNKED` (hole 10) fail by design until the staged FBXs are copied over; every other line, including all 3000-sample ground-height lines, passes on the installed holes. After install, `run_importcheck.sh` must give the staged result (57 lines, 0 failed): `unity_u/run_importcheck_staged.sh` proves it in advance.

## U.4 Gate tool (item c): see GATES.md "v2 area U"
Five review findings fixed in `postcard_look_verify.py`, every mutant still FAILs and every control PASSes at the blend and the FBX stage (final full self-test `v2/gates/runs_u/selftest_final_h8|9|10.log`, 0 expectations not met), the staged builds pass all gates (94 / 90 / 94 gates, 0 failed), the installed baseline holes keep their old verdicts (only LOOK_FILES turns PASS, two new gates pass or skip). New env / flags: `--stills-dir`, `--require-stills`; probe tools `tools/still_floor.py`, `probe_objects.py`, `run_stills_gate.py`, `tex_window_probe.py`, `surf_pair_gap.py`.

**Final re-run on the final textures (20:05; texture agent's last install Lava_C/E/N 19:57:22, sha256 prefixes `v2/gates/runs_u/look_sha256_at_final_check.txt`):** smoke `v2/runtime/smoke_u4.txt` **83/83 PASS** (TennisURP 29/29, HeroBaseStudioURP 29/29; lava 92.5 % in band, crust 3.8 %), staged importcheck `unity_u/importcheck_us3.txt` **57 gate lines, 0 failed**, `guards.sh` 7 PASS, 0 `error CS`. The golfer probes ran at 19:54-19:56 on the 19:52 textures; the golfer / swap gates do not read the lava or grass textures (flat URP Lit figure, probe FBXs), so the 19:57 Lava install cannot move them.


# v2 2026-10-04 area I (install + Game-view proof)
Holes 8, 9, 10 are installed (staged round 4); notes, numbers, gate lines, sheets and the re-runnable `run_proof.sh`: `work/postcard-look/v2/proof/` (`PROOF.md` first). PostcardImportCheck on the installed files: 57 gate lines, 0 failed; GolfLookSmoke 83/83 (both URP assets);
GolfLookProbe on the installed holes 6/6 under TennisURP and HeroBaseStudioURP; EditMode PostcardHoleTests 37/37 (Unity batch runner works: `-runTests -testPlatform EditMode -testFilter GolfArcade.Tests.PostcardHoleTests`); 0 `error CS`.
The active quality asset is now TennisURP on every level (QualitySettings == git HEAD). New golf-only editor tool `Assets/Editor/PostcardProofMasks.cs` (per-material ID-render masks of the same shots as PostcardLookStills; `GOLF_PROOF_CFG` / `GOLF_PROOF_OUT`; run through heavy.sh).
Open from the proof: LOOK_STILLS_TEXTURED flat-window floor exceeded by hole08_1_tee (18.8 %) and hole09_2_approach (20.0 %); installed hole_08 / hole_09 .blend carry relative image paths (LK_TEXTURED@blend FAIL, Unity side fine).


# v2 repair round 1 2026-10-04 (area unity: smoke readable, stills under both URP assets)
Review finding (high, hole 10): **no readable smoke plume in any of the three Crater stills** (a ghostly streak at x ~830 in the aerial; crater.jpg has bright grey-white plumes). Where this section disagrees with v2.5 / v2.12 (LK_SMOKE numbers), THIS section wins.
Evidence: `v2/unity_r1/` (`stills_base/` = before, `stills_new2/` = after, `stills_new2_studio/` + `stills_studio9/` = HeroBaseStudioURP, `stills_new/` = the interim row, `sweep_s.txt`, `smoke_r1_*` in `v2/runtime/`, rollback copies `*.at_r1_start`). All Unity runs through heavy.sh.

## Root causes (measured)
1. **Fog and a warm tint made the plume darker than the sky.** The board card of SMOKE_SOFT stands 130 yd from the camera (1 % of Crater's 120..1000 yd fog); the hole's cards stand 390 m = 430 yd out, where the dark red-brown fog (.42,.19,.14) takes ~35 % of a surface's colour and the warm ambient tints the rest.
   Same card, same angular size, at 430 yd (new board `SMOKE_SOFT_FAR`): median |delta luminance| **9.9** / p99 **42.5** (130 yd: 14.8 / 61.0); plume colour in the real stills (178,110,95) vs the dusk sky near the horizon (lum ~140): a plume darker than its backdrop. The near-card gate could not see it.
2. **Footprint, not look:** the three cards stand behind the wall or above the frame. Game view (`stills_base`, TennisURP): the plume moves **0.44 % / 0.07 % / 0.00 %** of the tee / approach / lavarim frame (>= 10 levels: 0.09 / 0.02 / 0.00 %), the aerial 2.57 % (1.32 %). The tee frame sees 5.3 % open sky, the approach frame 0.3 % (the wall fills it): a plume has to stand in front of the wall and be big (the painted plume is 19 % of its card, UV 0..1 over the card is the contract). **That is the hole builder's** (GATES.md "v2 repair round 1": `SMOKE_IN_FRAME`, `SMOKE_VISIBLE_STILLS`, `smoke_place_probe.py`).

## What changed (runtime side)
* `GolfSurf.shader`: new `_FogShare` (default 1 = as every other surface; `lerp(colour, MixFog(colour, fog), _FogShare)`).
* `GolfLook.Spec.FogShare` (default 1); **`LK_SMOKE`: tint (1,1,1), AlphaGain 1.35 (peak .67, unchanged), Lit .6 (was .8), SelfLight .40 (unchanged), FogShare .3** (was tint (1,.95,.92), Lit .8, fog 1). The plume keeps 70 % of its own colour at any distance; the own lit colour (189,164,163) = crater.jpg's (183,154,150) within the texture tool's +-14 gate (its model `SMOKE_SOFT runtime band` PASS: median 18.0, p99 69.6; a first try with Lit .5 / SelfLight .55 gave
  (200,171,169) and failed that gate, so it was re-tuned to the pair that satisfies both the Game view and the model; sweeps `v2/unity_r1/sweep_s.txt`, `smoke_r1_u*.txt`).
* `GolfLookSmoke`: smoke board refactored (`SmokeAt(dist)`: the 36 x 44 yd card scaled about the camera by dist / 130, so the angular footprint is identical); **new gate `SMOKE_SOFT_FAR`** at 430 yd (same band as `SMOKE_SOFT`: peak alpha .55..72, border <= .02, median >= 8, p99 28..90, edge step <= 6); `GOLF_LOOK_SMOKE=r,g,b,gain,emission,lit[,fogshare]`; the MATERIAL line of every surf material checks `_FogShare` exists and equals the table.
* `PostcardLookStills`: every shot is rendered a second time with the `DRESS_SMOKE*` renderers off; `stills_stats.json` gains `"smoke": { cards, changed_px, share_changed, readable_px, share_readable (|delta lum| >= 10), delta_lum_median / p95 / p99, plume_mean_rgb }` per shot (no card: `{ "cards": 0 }`); new env **`GOLF_STILLS_PIPELINE=<URP asset name>`** swaps the current quality level's asset IN MEMORY for the run (restored in `Finish`; ProjectSettings never written; the stats `pipeline` field names the asset actually used).
  This closes the low finding "stills rendered under TennisURP only": `run_stills.sh <label> <outdir> GOLF_STILLS_CFG=... GOLF_STILLS_PIPELINE=HeroBaseStudioURP`.

## Numbers (Game view = PostcardLookStills, TennisURP, real hole 10; cfg = the three proof shots + the aerial)
| shot | before: changed / readable / median / p95 | after: changed / readable / median / p95 |
|---|---|---|
| hole10_1_tee | 0.44 % / 0.09 % / 3.5 / 15.6 | 0.91 % / 0.30 % / 6.7 / 28.8 |
| hole10_2_approach | 0.07 % / 0.02 % / 6.7 / 14.7 | 0.08 % / 0.04 % / 9.1 / 26.0 |
| hole10_3_lavarim | 0 / 0 | 0 / 0 (no card in frame) |
| hole10_aerial (extra) | 2.57 % / 1.32 % / 10.4 / 27.3 | 2.89 % / 1.85 % / 17.7 / 54.8 (the plume is a clear pale wisp in `stills_new2/hole10_aerial.png`, was a faint streak) |
The plume is now ~2x as contrasty; its FOOTPRINT is unchanged, so the tee / approach / lavarim stills still show no readable plume: `SMOKE_VISIBLE_STILLS` FAILs (0.30 / 0.04 / 0.00 % vs 1.5 %) until the hole builder moves and sizes the cards. Board: SMOKE_SOFT median 17.8 / p99 68.3 (was 14.8 / 61.0), SMOKE_SOFT_FAR median 15.4 / p99 62.7 (was 9.9 / 42.5), edge step p99 2.5 levels/px, peak alpha .67, border 0.
**HeroBaseStudioURP** (`stills_studio9/`, the 9 proof shots, `pipeline: HeroBaseStudioURP`, taken with the interim LK_SMOKE row) vs the proof stills made under TennisURP: mean |diff| 0.16..1.26 levels, 0.01..1.9 % of the pixels differ by > 8 (the animated sea of holes 8 / 9, hole 10's smoke change). Hole 10 with the final row under both assets (`stills_new2/` TennisURP, `stills_new2_studio/` HeroBaseStudioURP):
`share_readable` identical (tee 0.30 %, approach 0.04 %, aerial 1.85 %, lavarim 0), `changed_px` within 6 px (13,119 / 13,113; 41,610 / 41,611: the sea), plume colour within 0.1 level. The golf look does not depend on the asset (RUNTIME.md v2.9).

## Gates of this round (all PASS unless said)
GolfLookSmoke `smoke_r1_final2.txt`: **84/84 PASS** (was 83; + SMOKE_SOFT_FAR), TennisURP 30/30 and HeroBaseStudioURP 30/30, URP_BOTH_ASSETS PASS, MATERIAL LK_SMOKE PASS (with the `_FogShare` check). PostcardImportCheck `importcheck_r1.txt`: 57 gate lines, 0 failed (no edit needed). 0 `error CS` in every log. `guards.sh` 7 PASS; `protected_check.sh`: the differences are other chats' files (12 emote / intro FBX, 2 customization prefabs, KitV3_016.mat, Tennis scripts), none is ours; QualitySettings.asset == git HEAD.
Blender-side (`postcard_look_verify.py`): hole 10 97 gates, **3 failed = SMOKE_IN_FRAME@blend / @fbx and SMOKE_VISIBLE_STILLS** (the open item below); holes 8 / 9 unchanged (94 / 90 gates, only the known LK_TEXTURED@blend). The texture tool's own `SMOKE_SOFT runtime band` (`golf_look_textures.py --only Smoke` into a scratch dir) PASSes with the new row.

## Open (not closable from this area)
* **Hole 10 `DRESS_SMOKE_nn` placement / size** (hole script `hole10_build.py` section 5, props lib `build_smoke_cards`): needs the plumes in front of the east / north wall and in the tee window, ~150 m wide cards; `smoke_place_probe.py` found two that pass `SMOKE_IN_FRAME` (tee 1.54 %, approach 2.00 %, lavarim 9.73 %): see GATES.md. After a re-stage and install: `run_proof.sh stills` re-shoots the ArtDir stills WITH the smoke stats (the ones there now predate the tool and carry no `smoke` block); the three ArtDir Crater stills also still show the previous plume look.
* `proof/measure.py`'s own SMOKE_SOFT (area I's file, not edited) still passes on a faint share; the verifier's `SMOKE_VISIBLE_STILLS` is the gate that reads the share.
* Seen, not ours: a hard horizontal seam (tee pad vs fairway) crosses the tee frames of holes 8, 9, 10 (hole content).


# v2 repair round 2 2026-10-04 (area unity: near-ground smear, filtering level, UV smear gate; HeroBaseStudioURP stills)
Evidence: `work/postcard-look/v2/unity_r2/` (`sharp.py` = the sharpness metric, `stills_a4|a8|a16/` = the nine proof shots at filtering level 4 / 8 / 16 via the editor-only env `GOLF_LOOK_ANISO`, `stills_final/` = default code under TennisURP, `stills_final_studio/` = the same under HeroBaseStudioURP in memory,
`sharp_before_after.txt`, `lavarim_uv_overlay.png`, `cmp_lavarim_aniso4_vs_16.png`, `cmp_lavarim_aniso8_vs_16.png`, `uv_ground.py` / `uv_bad.py` / `uv_bad_json.py` (Blender, UV Jacobian of the installed ground meshes), `verify/installed_hole8|9|10.log|json`, `selftest_*.log`, rollback copies `*.at_r2_start`),
smoke `v2/runtime/smoke_r2a.txt` (85/85) and the negative run `smoke_r2neg.txt` (84/85, only the new gate fails), `importcheck_r2a.txt` (57 gate lines, 0 failed). Every Unity run went through `heavy.sh`; 0 `error CS` in every log. Files edited by this round: `Scripts/Course/GolfLook.cs` (Load: filtering level), `Editor/GolfLookSmoke.cs` (+ `CheckAniso`), `blender/scripts/postcard_look_verify.py` (+ `GROUND_UV_LOCAL_SMEAR`), `RUNTIME.md`, `GATES.md`.
`GolfAtmosphere.cs`, `HoleView.cs`, `GolfGame.cs`, `CameraRig.cs`, `GolfSurf.shader`, `PostcardImportCheck.cs`, `PostcardLookStills.cs`: unchanged (checked against the `.at_r2_start` copies).

## Finding 1 (low, hole 10): "near grass smeared horizontally, loses blade detail; the lava-rim fairway shows horizontal streaks" ("raise anisotropic level 8-16, check UV density on the shelf strip")
Three different things were in that one sentence. Each was measured, not assumed (metric `sharp.py`: std of a 3x3 Laplacian of luminance = "lap", on grass pixels of a window; windows NEAR = x 200..700 y 1100..1500, MID = x 200..700 y 550..950, LAVARIM_UL = x 0..200 y 740..830 of the 900x1600 Game-view stills).
| what the reviewer saw | root cause (measured) | status |
|---|---|---|
| far / grazing ground of the lava-rim still (and Needle / Split far fairway) is soft and streaky | the importer's aniso 4 is below the footprint ratio of ground 10-25 deg off the horizon (6..16:1): the GPU reads a mip level `log2(major axis / min(ratio, level))`, 1.6 levels too blurry at ratio 12. **Fixed**: `GolfLook.Aniso = 16`, applied at texture load (`GolfLook.Load`), so a re-import (importer says 4) cannot undo it | LAVARIM_UL lap 24.3 -> 27.0 (level 8) -> **27.7 (level 16)**, MID of that shot 30.5 -> 33.1 -> 33.3 (+9 %); visible in `cmp_lavarim_aniso4_vs_16.png` / `cmp_lavarim_aniso8_vs_16.png`: level 16 still gains over 8 inside the streak wedge, so 16 |
| a wedge of hard horizontal streaks in the upper-left fairway of the lava-rim still | **UV smear in the hole 10 mesh, not filtering**: the installed `FAIRWAY_FIRSTCUT` has 3 triangles whose UV Jacobian is 26:1, 4.7:1 and collapsed, 103 m2 in all (largest 72.8 m2); projected into the still with its real camera they cover exactly the wedge (`lavarim_uv_overlay.png`), and level 16 does not remove it. Holes 8 and 9 have NO triangle over 1.3:1 on any FAIRWAY / FIRSTCUT / GREEN / APRON / TEE_BOX / BUNKER mesh. `UV_DENSITY` could not see it (it lets 15 % of a material's area be smeared; this is 1.8 % of the first cut) | **gated, open for the hole builder** (not my file): new `GROUND_UV_LOCAL_SMEAR` (GATES.md "v2 repair round 2"), hole 10 FAILs it at blend and FBX until `FAIRWAY_FIRSTCUT` is re-UV'd (3 triangles around course x 82..93 yd, d 129..160 yd, `uv_bad.py`; 5 more triangles of the same mesh sit between 2:1 and 2.2:1, which the gate allows) |
| soft, diagonal-stroke grass in the lower third of the tee and approach stills | **texel magnification, not filtering**: `Fairway_C` is 1024 px per 10 m = 9.8 mm per texel; the address camera (2.2 m up, pitched 22 deg, 60 deg fov, 1600 px; focal length 1386 px) resolves 2.0 mm per pixel across and 2.6 mm along the view at the bottom row (ground 1.7 m away): **one texel covers 4.8 x 3.8 pixels there**, 3.4 x 1.9 at row 1100 (the reviewer's window starts there), and is 1:1 across the view only above row ~494 and along it only above row ~848 (`sharp.py` windows NEAR and MID; arithmetic in this section's evidence folder). NEAR lap 2.0-3.1 (MID 8-16) on all three holes, and **identical at filtering level 4, 8 and 16** (hole 10 tee 3.05 / 3.05 / 3.05, approach 2.15 / 2.15 / 2.15): no filtering level can add detail a texture does not have | **NOT fixed, not cheap, disclosed**: the cures are (a) more texel density on Fairway / Green / Rough / Scrub (a 2048 px PNG is ~4x the 1024 one: Fairway_C 1.2 MB -> ~4.9 MB, Fairway_N 1.9 -> ~7.6 MB, and the folder is 21.41 MB of the 25 MB `LOOK_FOLDER_SIZE` limit, so it needs another storage decision: the texture area's call), or (b) a detail layer (URP Lit `_DETAIL_MULX2` + a 1-2 mm grass grain): its variant is `shader_feature` and no project material uses it, so an iOS build would STRIP it and the Editor Game view would show a detail the phone never gets; it needs a variant-keeper material in `Resources` and the whole grass calibration re-measured. Not started |
Aniso cost note: per-texture aniso is read only where the quality level allows it (`QualitySettings.anisotropicTextures`: Disabled on Very Low / Low, per texture on Medium and up = the iPhone default level 2); extra taps only where the footprint is elongated (grazing ground), none on the near ground.
**Level 16 vs 4 over the nine proof shots:** mean |difference| 0.15-0.48 levels, 0.01-0.91 % of the pixels differ by more than 8 (`stills_a16` vs `stills_a4`; the level-4 run reproduces the ArtDir stills to within 1-2 levels, mean <= 0.011, except `hole08_3_arch`, mean 0.117: the animated sea). **The nine stills in `ArtDir/screenshots/golf_postcards/look/` were NOT re-shot by this round (area I owns them): they show level 4; `run_proof.sh stills` re-shoots them with this runtime.**
New smoke gate `LOOK_TEXTURE_ANISO_RUNTIME` (`GolfLookSmoke.CheckAniso`): every tiling look texture a table row carries (26: ground, rock, basalt, lava, not sky / plant atlas / alpha cards) is at level >= `GolfLook.Aniso` after `GolfLook.Get`; `LOOK_TEXTURE_IMPORT` (importer, >= 4) is unchanged. Proven both ways: `smoke_r2a.txt` 85/85 PASS (26 textures at 16), and `GOLF_LOOK_ANISO=4 run_smoke.sh r2neg` -> `LOOK_TEXTURE_ANISO_RUNTIME` FAIL (0 of 26, all at 4) and nothing else fails (84/85). The Look `.png` and `.meta` hashes are identical before and after (the level is not written back).
Editor-only experiment hook: `GOLF_LOOK_ANISO=<1..16>` (inside `#if UNITY_EDITOR`; never compiled into a player) sets the level for the run; `run_aniso_sweep.sh` is the sweep.

## Finding 2 (low, gate tool): "stills rendered under TennisURP only; QualitySettings.asset == git HEAD; no HeroBaseStudioURP Game-view still of mine" (fix hint: none for this gate)
Confirmed and no gate change needed: `QualitySettings.asset` is byte-identical to git HEAD (`git hash-object` = `git rev-parse HEAD:...`, ba25e74e), every level uses TennisURP, and the golf look does not depend on the asset (RUNTIME.md v2.9, `URP_BOTH_ASSETS`: TennisURP 30/30, HeroBaseStudioURP 30/30 in `smoke_r2a.txt`). What was missing was my own proof under the other asset: **`stills_final_studio/` = the nine proof shots of the final runtime with `GOLF_STILLS_PIPELINE=HeroBaseStudioURP` (stats `pipeline: HeroBaseStudioURP`)** against `stills_final/` (TennisURP): mean |difference| 0.13-1.51 levels, 0.07-2.52 % of the pixels by more than 8 (the largest: `hole08_1_tee` 2.52 % and `hole08_2_approach` 1.98 %, the animated sea of Needle; holes 9 / 10: 0.07-0.22 %). Same range as repair round 1 (0.16-1.26 levels, <= 1.9 %; the sea animates between runs, the same shot rendered twice under one asset differs by up to 0.10 mean / 0.36 %).

## Gates of this round
| gate | result |
|---|---|
| GolfLookSmoke (`smoke_r2a.txt`) | **85/85 PASS** (84 + `LOOK_TEXTURE_ANISO_RUNTIME`), TennisURP 30/30, HeroBaseStudioURP 30/30, `URP_BOTH_ASSETS` PASS |
| `LOOK_TEXTURE_ANISO_RUNTIME` negative (`smoke_r2neg.txt`, `GOLF_LOOK_ANISO=4`) | FAILs as it must (0 of 26 textures at 16), the other 84 PASS |
| PostcardImportCheck (`importcheck_r2a.txt`) | 57 gate lines, 0 failed, no exception, no error log |
| `postcard_look_verify.py` on the INSTALLED holes (blend + FBX) | hole 8 ALL PASS (96 gates); hole 9 91 PASS, only the known `LK_TEXTURED@blend`; **hole 10 97 PASS, 2 FAIL = `GROUND_UV_LOCAL_SMEAR@blend` and `@fbx` (the real finding above)** |
| verifier self-test | new mutant `ground_uv_smear_local_64to1` FAILs the gate and the control `ctl_ground_uv_aniso_2p9` PASSes it on all three holes at blend and FBX (`SELFTEST_GATE GROUND_UV_LOCAL_SMEAR 3/3 bad, 9/9 good`); full self-test: GATES.md |
| `guards.sh` | 7 PASS |
| LOOK `.png` / `.meta` hashes, QualitySettings content | identical to the start of the round / equal to git HEAD (`protected_check_r2.txt`) |

## Open (not closable from this area)
* **Hole 10 `FAIRWAY_FIRSTCUT` UVs** (hole builder / ground library): 3 triangles at 26:1, 4.7:1 and collapsed; make the UV (lateral offset, arc length) continuous across the first-cut outline or split the long triangles. `GROUND_UV_LOCAL_SMEAR` is the acceptance test (`$B -b --factory-startup --python blender/scripts/postcard_look_verify.py -- 10`).
* **Near-ground texel density** (texture area): the lower third of every tee / approach still is magnified 4-5x; see the table above for the two cures and why the detail-layer one is not a runtime-only change.
* After the hole is re-staged and installed, `run_proof.sh stills` re-shoots the ArtDir stills with level 16 (and the new UVs).


# v2 repair round 3 2026-10-05 (area unity: maroon basalt, smoke edge + cap, ball read, gates that could not see them)
Findings (independent reviewers, hole 10): **high** basalt dark maroon (Game-view mean S .54-.59, crater.jpg (26,25,29) S ~.10; BASALT_JOINTS passed it), **medium** SMOKE_SOFT FAIL on the tee (edge step p99 18.0 > 6) and approach (|dLum| max 132.2 > 110), **low** near-ground smear, **low** ball salmon and darker than the grass round it, **low** stills under TennisURP only (no action).
Evidence: `v2/unity_r3/` (variant sweeps `v1`..`v12`, `stills9_d/` = the final nine stills, `proofcopy_d/` masks, `measure_d2.log`, `GATE_LINES_r3.txt`, tools `basalt_stats.py`, `smoke_stats.py`, `lava_stats.py`, `branch_probe.py`, `selftest_basalt_joints.py`, `run_variants.sh`, `tune_tints.sh`, `tune_grass.sh`, `run_final_chain2.sh`, rollback copies `*.at_r3_start`), smoke `v2/runtime/smoke_r3d.txt` (88/88), `importcheck_r3d.txt`. Every Unity run went through heavy.sh; 0 `error CS` in every log.
Where this section disagrees with v2.3 / v2.5 / the K calibration sections (basalt tint, Crater fog / ambient, smoke row, grass tints), THIS section wins.

## New tool: `GOLF_STILLS_VARIANTS` (PostcardLookStills, experiments only, never proof shots)
`name:key=v[,v];key=v|name2:...` renders every shot again per variant with IN-MEMORY tweaks (put back after each render), written as `<shot>__<variant>.png`: `fog`, `fogcolor`, `fogrange`, `ambient`, `ambeq` / `ambsky` / `ambgnd`, `sun`, `lights` (lava light multiplier), `basalt_tint` / `basalt_emis` / `basalt_smooth`, `smoke=gain,power,softfade,lit,self,fogshare`, `lavafog`, `ballmat=r,g,b,self`, `hide=<renderer prefix>`, `nosmoke=1`. Together with the PostcardProofMasks id render (`basalt_stats.py` reads its basalt id colour) every number below is a Game-view number, not a board number.

## 1. Basalt: where the red entered (measured by switching each source off, TennisURP, the three Crater proof shots, basalt id mask, non-glow pixels)
| variant | tee mean RGB / S | approach | lava rim |
|---|---|---|---|
| shipped before round 3 | (56,28,26) S .54 | (40,17,17) S .58 | (45,22,21) S .53 |
| fog off | (32,20,22) S .38 | (26,11,14) S .57 | (25,12,14) S .54 |
| lava lights off (tee, rim identical; approach barely) | .54 | .57 | .53 |
| emission off | .52 | .57 | .53 |
| ambient off | (48,23,18) S .63 | (27,9,5) S .81 | (32,14,10) S .69 |
**The walls the phone sees are the shadow side** (no key light at all: fog + ambient + the lava lights only). Cause 1: Crater's fog (.42,.19,.14) at 120..1000 yd put 15 % of an ember-red into a wall 250 yd out and 35 % into the cone at 430 yd. Cause 2: the equator ambient (.55,.30,.22) lit every vertical face orange. The tint (.52,.74,.90) could only cancel the KEY (the board wall faces the key, so BASALT_RENDERS_DARK passed). crater.jpg's haze is a neutral smoke-grey ((87,84,90) .. (119,102,105), S .07-.14) and its basalt (17,17,20) .. (27,25,28).
**Fix (GolfAtmosphere hole 10 + GolfLook):** fog (.42,.19,.14) -> **(.29,.25,.26)**; equator (.55,.30,.22) -> **(.33,.36,.31)**; ground bounce (.60,.22,.08) -> **(.48,.34,.18)** (the wall's ambient came out purple, sky-blue + ground-red with G the lowest channel; G is lifted until the shadow side is neutral under the SAME tint that keeps the key-lit side neutral: one tint cannot cancel two differently coloured lights; BASALT_NOT_GREEN is the other side of that trade, the first try with tint (.44,.84,.93) failed it: key-lit brightest tenth (42,61,56) hue 166); `LK_BASALT` tint (.52,.74,.90) -> **(.56,.74,.90)** (key-lit tenth (49,53,54) S .09 -> (53,54,54) S .02). Sky ambient, key, sky texture, lava lights unchanged.
Result (final stills, `measure_d2.log`): non-glow mean **(40,35,37) S .128 / (29,24,25) S .17 / (32,28,30) S .118** (was .54 / .58 / .53), median luminance 35.5 / 23.5 / 28 (was 34 / 21 / 26), glow share 1.8 / 2.1 / 1.5 %. Side effects, all re-measured: grass hue +3 on Crater (fairway h73 = the top of the band, GRASS_HUE_GAMEVIEW hole10 FAIL) -> `HoleTint` (10) fairway / green (.95,1.13,.62), rough (.93,1.09,.62): fairway (164,185,42) h69, green h68, rough h62; the far cone lava lost saturation under the grey fog (tee still 65 % in band) -> `LK_LAVA.FogShare .35` (new `GolfLava._FogShare`): tee 93.1 %, approach 94.8 %, lava rim 92.6 %; golfer probes hole 10 skin clipped 0.2 %, shirt (46,69,98) readable (GOLFER_* PASS).
**What is NOT fixed here (content, other areas):** the glow is still 92.5 / 92.6 / 97.2 % parallel vertical 2-px streaks (junction clusters 1.27 per 100 skeleton px, crater.jpg 8.3-8.8) and the cone still reads as terraced planks: that is Basalt_E and the cone / wall UVs (texture area, hole 10 builder). The gate sees it now (below).

## 2. Smoke
* **Tee edge = a depth cut, not a texture edge.** The cone and a smoke card intersect (DRESS_SMOKE_06..08 stand through the cone's front flank); the depth test cuts the card along a straight line. Hiding the cone: edge step p99 1.26; with it 17.0. New `GolfSurf._SoftFade` (soft intersection on `_CameraDepthTexture`; both URP assets have `m_RequireDepthTexture 1`; where the depth texture is missing the fade is 1 = off, never a black card; default 0 = off for every other material): `LK_SMOKE.SoftFade = 40` yd. Tee edge step 17.0 -> **3.05**.
* **Approach cap.** Three cards stack over the near-black wall; the core reaches alpha ~.9 and moves the frame by 129 levels. `LK_SMOKE`: AlphaGain 1.35 -> **1.10**, AlphaPower 1 -> **1.5** (peak per card .58 -> .33, thin edges thinner; colour Lit .6 / SelfLight .40 / FogShare .3 unchanged). Approach |dLum| p95 117.5 -> **89.6**, max 132.2 -> **101.6** (limit 110); readable share (|dLum| >= 10) tee 1.89 %, approach 3.23 %, lava rim 3.88 % (>= 1.5 %). 14 combinations swept (`v4`, `v5`).
* **Gate re-band (disclosed):** the board gate SMOKE_SOFT / _FAR / _GAMEVIEW had `SmokeAlphaMin .55`, a first-build proxy for visibility that cannot coexist with the Game-view cap on a 3-card stack (peak .58 stacks to ~.9 -> 129 levels); visibility is held by the two delta bands next to it (median >= 8, p99 >= 28; unchanged) and by SMOKE_VISIBLE_STILLS (real frames). `SmokeAlphaMin` .55 -> **.30**; the board card still moves the frame by median 11.9 / p99 40.7 (130 yd) and 10.5 / 37.0 (430 yd). `SmokeAlphaMax .72`, border <= .02, edge <= 6 unchanged.
* New board gate **SMOKE_SOFT_INTERSECTION**: a card cutting an opaque wall at 40 deg: edge step p99 with the table's SoftFade **5.03** (<= 6), the control with `_SoftFade` 0 **38.03** (> 6 and >= 2x), the soft card still moves 24,895 px (>= 3000). PASS under both URP assets.
* **Not fixed (content):** the approach plume is still a round pale cloud with a dark see-through void (stacked cards 09..11 + the texture's two lobes): Smoke_C / `build_smoke_cards` (texture + props area). The runtime cannot split a card into wisps.

## 3. Ball (low)
The game ball gets its OWN copy of the shared flat Lit material (`GolfAtmosphere.RegisterBall`, called by GolfGame after it builds the ball; the shared `Mat(white)` is untouched). `Look.BallExposure` / `BallSelfLight` (default white / 0 = the old ball exactly; Legacy() and holes 8 / 9 / 7 unchanged): Crater **(.75,.92,1.25), self light .14** (15 combinations, `v7`..`v9`). Ball disc (r 10 px) vs the grass ring: tee (170,144,132) lum 149 vs 189 -> (171,170,191) lum 172 vs 188 (S .22 -> .11); approach (165,96,95) lum 111 vs 148 -> (160,135,156) lum 151 vs 154 (S .42 -> .16). Ball visibility ratio (visible px / expected) 1.34 / 1.31 (gate >= .9).

## 4. Near-ground smear (low): measured, NOT fixed
`QualitySettings` level 2 (iPhone default) is "Per Texture" aniso and `GolfLook.Aniso = 16` is applied at load (LOOK_TEXTURE_ANISO_RUNTIME: 26 textures at 16). The new number: **Fairway_C.png itself has gradient ratio gy/gx 0.55** (Green_C 0.54, Rough_C 0.73) = the albedo's grain is horizontal; the Game-view near rows measure 0.91 (row 700) / 0.66 / 0.49 / 0.44 (rows 1000 / 1250 / 1450). On top of that the 4.8 x 3.8 px magnification of a 9.8 mm texel (round 2). Neither is a filtering problem: texture area (isotropic grain, 2048 px) or a detail layer (variant-keeper material + grass recalibration). Not started.

## 5. Gates (what changed; GATES.md "v2 repair round 3")
Runtime board (`GolfLookSmoke`, 85 -> **88** gates, 33/33 per URP asset): new `BASALT_SHADOW_SIDE_NEUTRAL` (wall facing AWAY from the key, 250 yd out, fog + ambient + lava lights, emission off: mean S <= .25, median lum <= 40; now S .13 / lum 28; **negative control with the old fog / ambient / tint: S .63 FAIL while BASALT_RENDERS_DARK still passes**), `LAVA_FAR_ORANGE` (lava slope at 430 yd through the fog: 94.4 % in band; control `GOLF_LOOK_LAVA_FOG=1`: 68.2 % FAIL), `SMOKE_SOFT_INTERSECTION`; MATERIAL checks for `_SoftFade` (smoke) and `_FogShare` (lava); tuning env `GOLF_LOOK_HOLETINT`, `GOLF_LOOK_GRASS_HOLE`, `GOLF_LOOK_LAVA_FOG`, `GOLF_LOOK_CRATER_OLD_ATMOSPHERE`.
Game view (`proof/measure.py`, area I's file, edited additively): BASALT_JOINTS + non-glow mean S <= .25, vertical-line share <= .80, aggregated skeleton junctions >= 3.0 per 100 px; the old vertical-line FLOOR (>= 50 %) is no longer applied (crater.jpg's own wall crops measure 5 / 5 / 37 % by that classification). Self-test `selftest_basalt_joints.py`: neutral branching network PASS, maroon network FAIL, neutral parallel streaks FAIL, neutral ladders FAIL.
Verifier (`postcard_look_verify.py`): `SMOKE_VIS.alpha_readable` .30 -> .20 (re-calibrated with the first calibration's own rule, GATES.md).

## 6. Open / unverified
No physical iPhone (stills are Editor Game view, TennisURP). The same nine shots under HeroBaseStudioURP in memory (`v2/unity_r3/stills9_d_studio/`): hole 10 mean |diff| 0.13-0.93 levels vs TennisURP, readable smoke share identical (1.89 / 3.23 / 3.88 %), basalt non-glow mean S .13 / .16 / .12, lava in band 93.1 / 94.8 / 92.6 %; the board suite 33/33 under each asset. `_SoftFade` needs the camera depth texture: both URP assets request it; on a device where a camera does not generate it the plume simply keeps its hard cut (no black card). Basalt glow structure, smoke shape and ground grain: content, listed above.

## 7. Re-run (when the texture / props / hole areas land new Basalt_E, Smoke_C, Lava or hole 10 builds)
The numbers above were measured on the Look PNGs of `v2/unity_r3/look_png_sha_at_final.txt` (identical to the start of the round) and the installed holes of `hole_sha_at_final.txt`. After another area changes either: `bash work/postcard-look/v2/unity_r3/run_final_chain2.sh <tag>` (smoke suite, importcheck, golfer probes, EditMode tests, nine stills, masks; ~16 min, all through heavy.sh), then `python3 work/postcard-look/v2/unity_r3/measure_r3.py work/postcard-look/v2/unity_r3/stills9_<tag> work/postcard-look/v2/unity_r3/proofcopy_<tag>` (Game-view gates on a PRIVATE copy; area I's `proof/` outputs are not touched), then the verifier with `--stills-dir`. What is texture-sensitive: `LK_BASALT.Tint` and the Crater ambient / fog (basalt S, `BASALT_NOT_GREEN`), `LK_SMOKE` gain / power / SoftFade (approach |dLum| max, readable share), `HoleTint (10)` (grass hue), `LK_LAVA.FogShare` (far lava band). The tuning loops: `run_variants.sh` (stills variants), `tune_tints.sh`, `tune_grass.sh`.


# v2 2026-10-05 area U: plant sway (GolfArcade/GolfPlants + GolfWindSway) - THE CONTRACT (written first, so the props / hole areas can build to it)

Scope (user, 2026-10-04: "i want the gentle sway of the plants with the wind"): PLANTS ONLY move. Lava, surf, fall, sky, water (TennisWater is the tennis shader and keeps its own swell), ground, rocks, masonry stay STATIC.
No grass cards, no ground motion, no post.

## U.0 The vertex colour attribute every PLANT_* mesh carries (Blender -> `postcard_look_lib.export_look_fbx(colors_type="LINEAR")` -> Unity `Mesh.colors`)
* One colour attribute named `Col`, type FLOAT_COLOR, domain POINT (the same slot WATER_SURF uses; it must be the ACTIVE and RENDER colour attribute). Raw linear values (colors_type LINEAR: no sRGB conversion).
* **R = sway weight 0..1**: 0 at the root / pinned point, rising smoothly to the free tip. Tufts, flowers, agave: by height above the base. Shrubs: low (see the table). Vines: 0 at the attach point (top), rising toward the bottom tip.
* **G = per-vertex phase 0..1** (a constant per plant is fine; a spread over the blades is better).
* **B = 0** and **A = 1**. B = 0 is what marks "this mesh carries sway data": a mesh WITHOUT colours reaches the shader as white (B = 1) and is treated as weight 0 = STATIC (so an old plant mesh never slides).
* The weights are the only per-kind control (one shared material). The displacement is LINEAR in the weight (the user's formula, "weight x amplitude x waves"): tip displacement = AmpFull (0.058 yd) x (0.25 .. 1 by wind speed) x w x up to 1.02 (the crosswise part), so a per-kind cap is a cap on the tip weight. How the weight rises along the plant (a cantilever: R = tip x t^1.3..1.6) is the author's: the lower half hardly moves.

| kind (mesh name prefix) | cap at 20 mph | max tip weight that keeps the cap | author with tip weight |
|---|---|---|---|
| PLANT_TUFT*            | 0.06 yd | 1.0 (R cannot exceed 1: 0.0592 yd) | 1.0 (0.8 .. 1.0) |
| PLANT_FLOWER*, PLANT_AGAVE* | 0.05 yd | 0.845 | 0.6 .. 0.84 |
| PLANT_SHRUB*, PLANT_BUSH*, PLANT_TREE* | 0.03 yd | 0.507 | 0.3 .. 0.5 ("shrubs low") |
| PLANT_VINE*            | 0.08 yd | 1.0 (R cannot exceed 1: 0.0592 yd) | 0.9 .. 1.0 |

Gate PLANT_SWAY_COLORS (Blender, blend AND FBX re-import; Unity half: GolfPlantSwayCheck PLANT_SWAY_COLORS_UNITY): exactly one colour attribute; root weight (lowest 4 % of the height, vines: the top) <= 0.05; tip weight > 0.6 (shrubs and trees "low": > 0.25); weight rises with the distance from the root (corr >= 0.5); B = 0; A = 1. Gate PLANT_SWAY_CAPS: AmpFull x tip weight x 1.0198 <= the kind's cap.
(The user's line says "tip weight > .6" for every PLANT_ mesh and, in the same sentence, "shrubs low"; a shrub tip above 0.507 would break its 0.03 yd cap, so shrubs / trees are held to > 0.25 and to the cap: disclosed in GATES.md.)

## U.1 Shader `GolfArcade/GolfPlants` (Unity/Assets/Resources/Course/Shaders/GolfPlants.shader) and the global `_GolfWind`
* The ONLY shader that reads time. `_GolfWind` (global float4, set every frame by `GolfWindSway`): xyz = world wind direction (sin d, 0, cos d) x amplitude (yd), w = time in seconds, wrapped at 600 s (every frequency is a whole number of cycles per loop, so the wrap is invisible). Unset (zero) = no sway.
* World-space displacement along the wind (plus <= 20 % crosswise) of weight x amplitude x (a 0..1 downwind lean whose size breathes with two slow sines, ~0.45 Hz and ~0.83 Hz (each clump has its own whole-cycle frequency: 0.45..0.49 and 0.83..0.87 Hz, 270 + 6k and 498 + 6k cycles per 600 s loop), and a gust envelope 0.6..1 that travels with the wind), phase hashed from the instance pivot's world XZ + the vertex G, so no two clumps move together. Amplitude = 0.058 yd x (0.25 + 0.75 x min(mph, 20) / 20): a faint idle breeze at 0 mph (25 %), monotonic in speed. No stretching of the base (weight 0 = no motion at all).
* Same URP Lit look: same palette atlas (`Plants_C`), tint, smoothness, main + additional lights + shadows + SH ambient + fog; ForwardLit, ShadowCaster and DepthOnly / DepthNormals all apply the SAME sway. SRP Batcher compatible (the URP Lit `UnityPerMaterial` layout), GPU instancing on, forward renderer only (no GBuffer pass: both URP renderer assets are Forward).
* `GolfLook` maps `LK_PLANTS` to it (`Kind.Plants`); `GolfWindSway.SetWind(Wind)` is called from `GolfGame.StartHole`, and the driver also polls `GolfGame.Wind` every frame (the multiplayer path assigns the wind elsewhere).
* Editor/test hooks (stills): `GolfWindSway.FreezeTime` (seconds, null = real time) and `GolfWindSway.ForcedWind`; `PostcardLookStills` env GOLF_STILLS_SWAY=`mph,deg,time` (fixed wind + frozen time) and GOLF_STILLS_SWAY_PAIR=`dt` (a second frame of every shot, dt seconds later) - see U.4.


## U.2 What was built (area U, 2026-10-05)
* `Unity/Assets/Resources/Course/Shaders/GolfPlants.shader` (new, GolfArcade/GolfPlants): URP Lit look + the vertex sway of U.1; ForwardLit / ShadowCaster / DepthOnly / DepthNormals; built on URP's own `LitForwardPass` / `ShadowCasterPass` / `DepthOnlyPass` / `LitDepthNormalsPass` (a thin wrapper vertex function displaces the object-space position by the world-space sway, then the stock vertex function runs); `UnityPerMaterial` = LitInput's (SRP Batcher compatible), GPU instancing, only `multi_compile` keywords (nothing a runtime-made material can lose to stripping).
* `Unity/Assets/Scripts/Course/GolfWindSway.cs` (new): static facade + hidden per-session driver. `SetWind(Wind)` (the hook, called from `GolfGame.StartHole`), `Push()`, `Amplitude(mph)`, `Direction(deg)`, `GlobalValue(wind, t)`, `FreezeTime` / `ForcedWind` (stills), and `Displacement(...)` = the C# mirror of the shader's math. The driver (`LateUpdate`) pushes `_GolfWind` every frame and also follows `GolfGame.Wind` (the multiplayer path assigns it in `GolfGame.Network.cs`, not through StartHole). No per-frame allocation. Created only when golf sets a wind (tennis never creates it); `HideInHierarchy`, so the editor destroys it with the play session.
* `GolfLook`: `Kind.Plants`, `BuildPlants` (same texture, tint, smoothness; falls back to the static URP Lit with an error log if the shader is missing). `GolfGame.cs`: one line after `Wind = Wind.Random(rng)`.
* Tools: `Unity/Assets/Editor/GolfPlantSwayCheck.cs` (+ `run_swaycheck.sh`), `PostcardLookStills` (GOLF_STILLS_SWAY / _SWAY_PAIR / _SWAY_TESTCOLORS / _REALTIME_PAIR, see its header), `v2/sway/sway_gates.py`, `v2/sway/run_all.sh`, fixtures `Unity/Assets/Editor/GolfPlantSwayFixture/` (a 9-row strip and the props library's 21 plants, both written by Blender with the libs' exporter options: `v2/sway/blender/make_fixture.py`, `make_lib_fixture.py`), EditMode `GolfWindSwayTests` (16 tests).

## U.3 Measured (all through heavy.sh; Unity 6000.3.24f1, Metal, TennisURP and, in memory, HeroBaseStudioURP)
| what | result |
|---|---|
| compile | 0 `error CS`; shader imported without errors on Metal, 4 passes, SRP Batcher code 1 like URP Lit (probe calibrated: UI/Default 10, Standard 0) |
| GolfLookSmoke (`runtime/smoke_u2.txt`) | 95 / 95 PASS (TennisURP 33/33, HeroBaseStudioURP 33/33); MATERIAL LK_PLANTS, SHADER_OK GolfPlants, HOLE8/9/10_PLANTS_SWAY_SHADER (822 / 385 / 214 slots) PASS |
| PostcardImportCheck (`runtime/importcheck_u2.txt`) | 60 gate lines, 0 failed; PLANTS_USE_SWAY_SHADER PASS on all three holes |
| EditMode `GolfWindSwayTests` | 16 / 16 |
| GolfPlantSwayCheck (`v2/sway/swaycheck_a17.txt`) | 23 / 25: the two FAILs are the installed holes' own meshes (PLANT_SWAY_COLORS_UNITY, SWAY_GENTLE: 0 of 27 unique plant meshes carry sway colours yet). Mirror vs GPU worst error 0.26 px = 0.0005 yd (1080 samples), Blender-exported fixture through the importer and the shader 0.12 px, shadow slope 0.94 / correlation 0.977, 16 other LK_ materials pixel-identical, both URP assets alike |
| negative control (`swaycheck_neg.txt`, GOLF_SWAY_NEGATIVE=1) | mirror prediction halved -> SWAY_MIRROR_MATCHES_SHADER (14.4 px), SWAY_FBX_CHAIN_ON_GPU (16.5 px), SWAY_SHADOW_FOLLOWS_PLANT (slope 1.88) all FAIL under both assets |
| props library (`v2/sway/blender/props_lib_sway_probe.py`, fixture through Unity) | 21 / 21 PLANT_ kinds pass PLANT_SWAY_COLORS / PLANT_SWAY_CAPS in Blender AND PLANT_SWAY_COLORS_UNITY / SWAY_GENTLE in Unity: tuft 8/8 max 0.0590 yd at 20 mph (cap .06), flower/agave 5/5 0.0467 (.05), shrub 3/3 0.0277 (.03), tree 2/2 0.0178, vine 3/3 0.0578 (.08) |
| a SCRATCH rebuild of hole 8 with the current libs (`v2/sway/scratch_h8/`, not installed; `hole08_build.py -- --out`) | verifier: ALL PASS incl. PLANT_SWAY_COLORS / PLANT_SWAY_CAPS on blend + FBX re-import (`logs/verify_scratch_h8.log`); Unity (GOLF_SWAY_EXTRA_FBX, `swaycheck_scratch8.txt`): 809 plants on 11 meshes, PLANT_SWAY_COLORS_UNITY PASS, SWAY_GENTLE PASS at the real pivots (tuft .0590, flower .0472, shrub .0283, vine .0591 yd at 20 mph; caps .06 / .05 / .03 / .08): once the rebuilt holes are installed the real-mesh gates pass |
| Game-view frame pairs, installed holes + SYNTHETIC colours (`v2/sway/stills_final_r1`, `sway_gates_final.txt`) | 9 shots x 2 clocks (12 mph toward 45, +1.2 s): 0 px change outside the plant mask, plant-less frames identical (0 px), repeat identical, changed plant px per hole 30,255 / 2,539 / 1,807, mirror max displacement at the 12 mph wind: flower .033 / shrub .020 / tuft .041 / vine .040 yd (caps at 20 mph .05 / .03 / .06 / .08); `GolfGame.Wind` == hook wind after every hole start (9 / 9) |
| real time (GOLF_STILLS_REALTIME_PAIR 1.2) | 1.22-1.23 s later, plants hidden: 0 of 12,530,080 non-sea px differ (lava, rocks, ground, surf, fall, smoke, sky); the sea (TennisWater) moved in 384,616 px as before |
| determinism across two Unity runs | 18 frames pixel-identical outside the sea; Crater (no sea) identical in full |
| verifier on the installed holes (`verify_installed_hole*_final.json`) | the ONLY failures are PLANT_SWAY_COLORS / PLANT_SWAY_CAPS (blend + FBX) on each hole; SHADERS_STATIC PASS; self-test (all 3 holes, blend + FBX) 538 lines: 536 expectations met on the full run, the 2 unmet (the flower mutant had no flower to mutate on holes 9 / 10) fixed and re-run PASS (GATES.md) |

## U.4 Stills tool (PostcardLookStills) additions
`GOLF_STILLS_SWAY=<mph>,<deg>,<seconds>` fixes the wind and the plant clock for every shot; `GOLF_STILLS_SWAY_PAIR=<dt>` adds the same-camera frame dt later, the plant-less frames, the plant mask and a `"sway"` block per shot in stills_stats.json (plant_px, changed_px, nonplant_px_diff, repeat_max_diff, outside_plant_changed_px, coloured_plant_objects, mirror_max_disp_yd vs caps_yd, water_px); `<shot>__sway_t1.png`, `__sway_diff.png`, `__sway_water.png` are written next to it; `GOLF_STILLS_REALTIME_PAIR=<dt>` writes `sway_realtime.json`; `GOLF_STILLS_SWAY_TESTCOLORS=1` puts height-based sway colours on plants that have none (in memory, flagged `test_colours`). stills_stats.json also records `anisotropicFiltering` ("Enable" at quality level 2) and `golfLookAniso` (16): carry-over finding "near grass smear": the quality level allows per-texture aniso and GolfLook sets 16 on every tiling texture, so aniso is not the cause (RUNTIME.md v2 repair round 2: texel magnification right under the camera is).
**The sea**: TennisWater reads `_Time.y` (the engine clock) and is the tennis shader's. `Time.timeScale = 0` does not make it reproducible between two Unity runs (both froze at Time.time 0.044; 12 of 18 frames still differed). The frame pairs are therefore rendered inside one player frame and cross-run / real-time comparisons mask the sea (`__sway_water.png`: the pixels that change when WATER_OCEAN / WATER_SHELF are hidden, at both clocks, grown 3 px).
Carry-over finding (gate tool, low: "the arch still's mask frame differs from the proof frame, animated water 11.4 %"): `v2/proof/measure.py` now ALSO measures the consistency without the water pixels (ocean / shelf / surf / fall ID masks grown 2 px); on the existing masks: hole08_3_arch 8.24 % -> 0.00 % of pixels differing by > 8, max channel diff 244 -> 12; all nine shots and the four extras 0.00 % (scratch run `v2/sway/measure_test_METRICS.md`; the proof's own metrics.json is regenerated by `run_proof.sh metrics`).

## U.5 Open / not measurable here
* **The installed hole FBXs predate the sway colours**, so on the real holes every plant is static (B = 1 rule) and SWAY_GENTLE / PLANT_SWAY_COLORS_UNITY / the Blender gates FAIL until the rebuilt plant meshes are installed. The Game-view frame pairs above use synthetic in-memory colours; re-run `v2/sway/run_all.sh <label>` (without `testcolors`) after the install.
* No iOS player build and no device: the shader is compiled for Metal in the macOS editor only; vertex cost is not measured (estimate: about 70 extra ALU ops and four sines per vertex per pass, 4 x 4 bytes of vertex colour).
* DepthOnly / DepthNormals compile with the shader (SWAY_SHADER_COMPILES) but neither pass runs in the current URP configuration (no depth prepass, no SSAO), so only ForwardLit and ShadowCaster are exercised by a render.
* Plants on a hole not built by HoleView (tests that instantiate the FBX directly) see `_GolfWind` = 0 until `GolfWindSway.SetWind` is called: static, never broken.
