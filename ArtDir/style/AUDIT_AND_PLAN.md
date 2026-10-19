# Visual audit and build plan — 14 October 2026

**Audit and plan only.** This document proposes future work; it does not authorize implementation. No Unity assets, code, settings, packages, cameras, physics, characters or Git staging were changed for this pass. The art bible is unchanged.

**Decision recorded after the audit:** target **60 fps on every quality tier**, including Low. Never use 30 fps as a target or fallback. Reduce visual cost to retain 60 fps; on-device verification is still required.

**Visual choices recorded:** 2B blue acrylic court with green surround; 4B subtle far-background blur on High, keeping both players, ball, net and court sharp and preserving 60 fps; 5B restrained material detail. Decision 3 remains open: Adnan could not distinguish the generated grading examples. Show matched actual Unity Neutral/ACES renders before choosing; do not exaggerate grading merely to force a visible difference. These choices set the planned direction, not permission to implement.

The direction is sound: modern material response, soft bounce, layered atmosphere and charming sports silhouettes. The biggest improvement will come from making those systems agree, starting with one resort court. The game already contains many of the necessary techniques; replacing everything would waste working systems and risk weather and gameplay.

## Evidence and limits

Read: `GPT_AUDIT_PROMPT.md`, `ART_BIBLE.md`, `ART_BIBLE_palette.png`, `VISUAL_STANDARD_AND_JUICE.md`, `pal.py`, `palette.json`, all five style references, and the environment brief, capture grids, comparison sheets and reference collection under `ArtDir/environment/targets-2026-10-14/`.

In this document, **E** means that environment folder. Capture names refer to `E/current/<name>.png`; sheet numbers refer to `E/sheets/`. Unity paths below are relative to `Unity/Assets/` unless they start with `Unity/ProjectSettings` or `Unity/Packages`. Proposed files are explicitly marked **new**.

The supplied captures are visual evidence of the supplied build, not proof that every current source branch or quality tier rendered that way. For example, current source includes court micro-normal controls, moving grass patches and lava cooling plates that are poorly represented in those captures. A fresh baseline must precede implementation. No Unity session, build, device benchmark or gameplay test was run for this audit.

Use r1–r5 for the intended composition and palette relationships. Use `E/refs/modern_*` for the fidelity bar: Mario Tennis Fever court finish and surroundings; Astro Bot foliage, contact shading and water; Mario Kart World grass and city lighting; DK Bananza depth, snow and lava; Tiny Glade weather and warm stone. Classic references remain layout/readability references. AI concepts cannot establish physically consistent lighting or a mobile cost budget.

## A. Bible critique

### Independent color sampling

I sampled named regions again, independently of `pal.py`. These are **displayed sRGB colors**, after the reference's imagined lighting and grading. They are not material albedos, HDR emission values or sun colors. The suggested values below are reference swatches, not colors to paste directly into Unity materials.

The original script selects a pixel by sorting RGB sums, rather than taking the median of each channel. Its glow percentile can select unrelated bright pixels inside a mixed region. Its working directory is also hard-coded to `/workspace/juice/his_refs/`. Keep the broad palette, but replace ambiguous role names and record sample boxes. Different valid boxes naturally produce different colors.

Reproduce this table from the repository root; this code only reads images and prints results. Boxes are normalized `(left, top, right, bottom)`. S and L mean **HSL**, not HSV saturation or perceived luminance.

```python
from pathlib import Path
from PIL import Image
import numpy as np
import colorsys

samples = [
    ('r1', 'upper blue sky', (.30,.04,.40,.11)),
    ('r1', 'lit pavers', (.585,.77,.615,.79)),
    ('r1', 'shaded pavers', (.785,.77,.815,.79)),
    ('r1', 'navy roof', (.085,.32,.115,.34)),
    ('r2', 'clear sky', (.47,.03,.53,.09)),
    ('r2', 'lit cloud', (.585,.19,.615,.21)),
    ('r2', 'court', (.61,.79,.72,.87)),
    ('r2', 'surround', (.045,.65,.075,.71)),
    ('r3', 'clear sky', (.38,.03,.46,.08)),
    ('r3', 'near grass', (.62,.76,.72,.84)),
    ('r3', 'foliage core', (.90,.12,.94,.18)),
    ('r3', 'far hill', (.25,.24,.30,.28)),
    ('r4', 'rooftop court', (.12,.41,.18,.45)),
    ('r4', 'volcano court', (.80,.38,.90,.44)),
    ('r4', 'ice', (.10,.80,.18,.87)),
    ('r4', 'magma rock', (.88,.75,.91,.79)),
    ('r5', 'rain sky', (.19,.03,.27,.10)),
    ('r5', 'rain turf', (.29,.39,.36,.45)),
    ('r5', 'storm sky', (.68,.04,.76,.11)),
    ('r5', 'storm turf', (.79,.39,.86,.45)),
    ('r5', 'fog ambient sky', (.28,.53,.33,.58)),
    ('r5', 'fog sun glow', (.19,.53,.21,.57)),
    ('r5', 'gusty clear sky', (.685,.535,.715,.555)),
    ('r5', 'gusty sunlit grass', (.86,.82,.92,.88)),
]
for ref, role, box in samples:
    im = Image.open(Path('ArtDir/style/refs') / f'{ref}.png').convert('RGB')
    w, h = im.size
    crop = im.crop(tuple(int(v*d) for v,d in zip(box, (w,h,w,h))))
    rgb = np.rint(np.median(np.asarray(crop).reshape(-1,3), axis=0)).astype(int)
    hue, lightness, saturation = colorsys.rgb_to_hls(*(rgb/255))
    print(ref, role, '#%02X%02X%02X' % tuple(rgb),
          f'S={saturation*100:.1f} L={lightness*100:.1f}')
```

| Ref / role | Bible | Independent sample, S / L | What I would use |
|---|---|---|---|
| r1 upper blue sky | #CEB4BC | #A8B5D4, 34 / 75 | Add this blue zenith; retain lilac for warmer cloud regions. |
| r1 lit pavers | #D4A784 | #DDAC83, 57 / 69 | Both fit; use the new swatch for this lit patch. |
| r1 shaded pavers | #D2A281 | #957D79, 12 / 53 | Replace the mislabeled shadow sample. It is visibly cooler and darker. |
| r1 navy roof | #494F6B | #43496B, 23 / 34 | Keep the existing family; difference is small. |
| r2 clear sky | #7FB4F3 | #46A0F1, 86 / 61 | Separate clear blue from pale cloud-edge sky. |
| r2 lit cloud | #F4F7FC target | #F3EAE4, 38 / 92 | Use warm lit tops; retain cool blue bellies separately. |
| r2 court | #2089D8 | #1A87D9, 79 / 48 | Keep the blue court family. |
| r2 surround | #367A86 | #559691, 28 / 46 | Add this lighter, quieter sunlit surround. |
| r3 clear sky | #58B7FE | #4AB1FD, 98 / 64 | Keep both blue samples; allow highly saturated sky. |
| r3 near grass | #86AB29 | #8FB02F, 58 / 44 | Keep the olive/lime family with restrained stripes. |
| r3 foliage core | #235321 | #244F26, 37 / 23 | Keep; the original sample is representative. |
| r3 far hill | #75A3B0 | #8AAFB4, 22 / 62 | Add this paler layer rather than one universal haze swatch. |
| r4 rooftop court | #1A4D9C | #1F519C, 67 / 37 | Keep the cobalt family. |
| r4 volcano court | #887D80 | #877B7D, 5 / 51 | Keep the quiet stone court. |
| r4 ice | #4CA4C6 | #669ECE, 52 / 60 | Use both cyan and blue within the ice depth ramp. |
| r4 magma rock | #421518 | #2A202D, 17 / 15 | Add cool charcoal-violet; avoid making every rock burgundy. |
| r5 rain sky | #7085A2 | #798DAA, 22 / 57 | Keep as a range. |
| r5 rain turf | #456438 | #486540, 22 / 32 | Keep; the intended desaturation matters most. |
| r5 storm sky | #3B567D | #385275, 35 / 34 | Keep. |
| r5 storm turf | #38563F | #3C5C42, 21 / 30 | Keep. |
| r5 fog ambient sky | #E2D2C1 | #ACB4C5, 18 / 72 | Separate cool fog ambient from warm sunlight. |
| r5 fog sun glow | #E2D2C1 | #FBE5C5, 87 / 88 | Use for the localized glow, not the entire fog volume. |
| r5 gusty clear sky | #83C0F2 | #73BBF9, 92 / 71 | Keep the existing hue family; allow stronger blue. |
| r5 gusty sunlit grass | #5D7734 | #9CAF4C, 39 / 49 | Keep the darker swatch for shade; add this sunlit value. |

### Rules to fix before building

1. **Use relationships, not universal percentages.** Non-emissive r3 sky reaches S98; volcano stone is S5. Daytime blue sky samples are L61–64, below the stated L67–80. Dark magma can be L15. Warm haze need not become bluer. Retain warm key/cool fill as a default, with biome exceptions. HSL is useful for tracking drift, but use linear luminance and grayscale images for readability.
2. **Separate atmosphere roles.** Define zenith, cloud top, cloud belly, horizon and fog separately. Match fog to the relevant horizon region, not every sky pixel. Allow gradients beneath painted clouds. The fog concept has warm sunlight inside cool ambient haze.
3. **Preserve modern surface detail.** The strict parameter lists omit the normals, roughness variation, court aggregate, water depth and lava flow masks requested by the environment brief. Permit quiet, mipmapped detail maps. “No thin detail” should mean no unreadable visual noise; it cannot ban net strings, court lines and grass blades.
4. **Define six families, with purposeful variants.** Six masters do not exist yet, while shader creation is forbidden. Allow their initial creation/refactoring, then control additions. Keep useful water, ice, foliage and lava variants; a pulsing window shader cannot replace flowing lava, and an unlit sky cannot replace every lit island. Keep HLSL; Shader Graph is an authoring option, not a quality requirement. Do not delete one-offs before parity is proved.
5. **Resolve post and lighting ownership.** Choose one tonemapper for both tiers after a small Neutral/ACES comparison. ACES only on High would change the palette. Bloom thresholds select brightness, not material names: a bright sky or white highlight can bloom too. Reserve strong glow for accents, but permit restrained sky bloom. Do not tint shadows blue twice through both ambient and a fixed 35% shader overlay.
6. **Fit lighting to runtime construction.** These scenes build much of their scenery in code; checking “baked” in scene settings does not bake it. Begin with painted/vertex AO and bounce, trilight ambient and existing shadow/fill lights. Lightmaps/probes need a deliberate asset workflow later. Preserve the existing hero rim layer rather than rewriting character shaders to match the bible's camera-facing rim rule.
7. **Use real units and material-specific weather.** Golf world coordinates are yards; tennis/hub are approximately meters. Convert fog distances, wind amplitudes and texel density explicitly. Grass must not become polished plastic at smoothness .75. Wet stone, turf, sand and metal need different responses. Snow is currently a biome precipitation form, not a sixth gameplay weather state. Keep slow drying; forcing every transition into 3–5 seconds would remove existing persistence.
8. **Keep gameplay feedback out of the art rewrite.** Existing tennis hit holds are 14/30/45 ms by grade, with input still read. The proposed global `Time.timeScale=0` for 50–80 ms would change simulation behavior. Preserve current timing, live camera policy, animations, collisions and obstacle motion. Feedback should reuse confirmed events, never add speculative hits or change hazard timing.
9. **Make budgets empirical.** The bible's Low30 target conflicts with the brief's “never worse than today” and the runtime's 60/120 request policy. Adnan has now resolved this: target 60 fps on every tier, never 30. Reduce visual cost rather than accepting a 30 fps tier. 150k total triangles may leave little room after two heroes; allocate environment cost after measuring the fixed characters. Draw count alone misses fragment cost, shadow passes, transparency and texture bandwidth. A 300-particle cap conflicts with existing weather; replace it with measured per-effect/tier limits. Do not force every sky atlas under 1024.

`VISUAL_STANDARD_AND_JUICE.md` is useful as a catalog, but its r5 description lists more states than the four-panel image contains, and its five-versus-six-master wording is inconsistent. Its studio claims and tool prices are not verified technical requirements. Cinemachine, VFX Graph and Feel are not installed in the package manifest; none is needed to begin. A Decal Renderer Feature is also absent; keep existing pooled marks unless a measured alternative wins.

## B. Gap map: project versus target

The baseline is uneven rather than empty. These are source findings paired with visible evidence; performance remains unmeasured.

| System | What exists / evidence | Gap and recommended response |
|---|---|---|
| Palette | `Scripts/Tennis/TennisVenue.cs`, `Scripts/Course/GolfTurfPalette.cs`, `Scripts/Hub/HubArt.cs` define separate palettes. Resort is teal; magma turf remains lime in sheets 16–18. | Adopt role palettes per preset. r2 wants blue court against quieter green; r4 wants readable stone in the crater. Keep hub cream/navy/gold. |
| Value | `TennisLook.cs` and venue builders combine albedo, ambient and grade. Supplied resort court sample L26; volcano L4. Golf clear sky L37 versus turf L38. | Court/ball separation and daytime sky/ground hierarchy are the first visual problems. Measure named regions, not whole-frame averages containing HUD. |
| Lighting | `Scripts/Tennis/TennisLook.cs`, `TennisVenueBuilder.Skyscraper.cs`, `.Volcano.cs`; `Scripts/Course/GolfAtmosphere.cs`, `GolfCourseAtmosphere.cs`; `Scripts/Hub/HubArt.cs`. Resort sun 1.65; hub 1.42, trilight ambient and point spills already exist. | Unify intent and ownership. Add cheap contact/bounce where missing; do not merely increase exposure. Scene YAML is a bootstrap, not the final runtime rig. Preserve `Scripts/Tennis/HeroRimLight.cs` and its dedicated rendering layer. |
| Post | `Resources/Tennis/Rendering/TennisPost.asset` uses ACES; `Scripts/Tennis/TennisLook.cs` overrides bloom to .28 and contrast/saturation to 5/8. `SportsPostProcessing.cs` disables Low bloom. Hub builds a separate Neutral profile, bloom .7 and Gaussian DOF. | Serialized profile values are not all runtime values. Hub post does not use the gameplay tier wrapper. `TennisLook.ReplayFocus` and `Scripts/Game/IntroLens.cs` also lack an explicit High check. One policy must gate every DOF/bloom entry point. |
| Sky | `Resources/Tennis/Shaders/TennisCoastalSky.shader`, `TennisRooftopSky.shader`, `TennisVolcanicSky.shader`, `Resources/Course/Shaders/GolfResortSky.shader`; panorama textures and hub procedural sky already exist. | Sheets 06–07 show broad saturated sky with little depth; hub is stronger. Improve painted cloud scale, belly lighting and horizon integration. Hub's painted sun direction differs from its lighting direction; decide whether to preserve this artistic cheat. |
| Fog / depth | Resort runtime fog is 180–900 world units; golf often extends beyond 1000. `Scripts/Course/Backdrop.cs`, `Resources/Course/Shaders/GolfDistantLand.shader`, `Resources/Golf/WeatherFog.shader` already provide depth tools. | Sheets 07/12 show flat horizons or a gray fog wall. Calibrate per venue extent and golf units; preserve near color and layer distant silhouettes. Do not impose a universal 120 m cutoff. |
| Materials / shaders | `Resources/Tennis/Shaders/TennisWorldSurface.shader` has aggregate normals, polish, vertex tint, masonry and reflection controls. `Resources/Course/Shaders/GolfGround.shader`, `GolfOcean.shader`, `GolfIce.shader`, `GolfLava.shader` have specialist responses. `Resources/Hub/HubSurface.shader` supplies wrap light, sheen and wind. | Source capability exceeds what some supplied captures show. Trace actual material assignments first. Make acrylic, turf, stone and ice distinct without adding noisy detail. Keep ocean depth/foam and lava cooling/flow controls during consolidation. |
| Environment kit | `Scripts/Course/GolfCoursePalms.cs`, `GolfResortDress.cs`, `GolfCliffSculpt.cs`; `Resources/Course/GolfBotanicalInstancing.mat`, `GolfCoastalInstancing.mat`; `Scripts/Tennis/TennisEnvironmentV4.cs`, `TennisResortVista.cs`. Instancing and rounded botanical replacements already exist. | Sheets 17–18 still show inconsistent tree silhouettes and green conifers in snow. Reuse and extend the kit. Hole14 approach appears to lose its supporting land while overview shows land: investigate visibility/material/LOD before adding geometry. Preserve original colliders and `ObstacleScan` inputs. |
| Glow | Rooftop windows, lava and hub lamps already use emission; `TennisVenueFx.cs` supplies pulse/flow/flicker. Hub also has point-light spills. | Sheets 04/05/14 suggest weak integration, not absent implementation. Tune surface glow, local painted bounce and post together. Do not add hundreds of real lights or blanket-brighten the crater. |
| Readability | `TennisVenue.cs` defines lines/court; actual camera comes from `Scripts/Tennis/TennisShoulderCamera.cs`. Sheet16 reveals thin distant net detail and dark courts. | Test both the supplied close reference view and the actual accepted live camera. r2 court and surround have similar L48/L46; hue, saturation and white boundaries also separate them. Do not require a large lightness gap everywhere or blindly double physical line widths. |
| Weather | `Scripts/Game/WeatherView.cs` already blends sky, sun, ambient, fog, precipitation, wet overlay, lightning and audio. `Scripts/Course/RoundEvents.cs` defines five states and snow/ash by biome. `Scripts/Course/GolfWindSway.cs` feeds `_GolfWind`. | r5 needs more convincing wet/dull turf, layered fog and visible wind. Existing `_Wetness` is material-local to the ground overlay, not a scene-wide contract. Add a visual adapter, avoiding duplicate wet darkening and competing weather writers. Tennis has no weather today. |
| VFX | `Scripts/Tennis/TennisFx.cs` builds pooled flashes, rings, fuzz, dust, marks and confetti using `Resources/Tennis/Fx`. `Scripts/Game/ShotEffects.cs` handles trails and surface impacts. Weather particles are created in code; no environment ParticleSystem prefabs were found. | Standardize existing recipes/materials before inventing a library. Storm rain capacity is 2600; snow 3200; these are maxima, not measured visible counts. Stills cannot prove sway, lifetime quality or peak overdraw. |
| Juice | `Scripts/Tennis/TennisHitFeel.cs`, `TennisRules.cs`, `TennisJuice.cs`, `Scripts/Game/Haptics.cs`, `EventSounds.cs`, `CameraRig.cs` already implement feedback. `TennisJuice.Punch` deliberately sets zero; live camera cuts are guarded. | Document which events actually trigger each channel. A `Shake` property does not prove that the live camera consumes it. Improve effect identity/audio balance within current camera and timing behavior; do not restore disabled punch or extend hit-stop as an art task. |
| Performance | Active `Resources/Tennis/Rendering/TennisURP.asset`: HDR, depth texture, 4× MSAA, render scale1, two per-pixel additional lights, 4096 main shadow map. Renderer has contact SSAO and hero AO exemption. `Scripts/Tennis/TennisQuality.cs` applies tiers; golf expands shadow distance/cascades. | High-only AO already exists. Grass in `Scripts/Course/GolfCoastalTurf.cs` has a moving 12 m patch, three instanced submissions and camera fade at 26–35 m; that exceeds the brief's suggested 15–25 m range and needs measurement. Some sky importers allow 2048. No device numbers justify a global reduction or expansion yet. |

Additional inspected configuration: `Unity/ProjectSettings/GraphicsSettings.asset`, `QualitySettings.asset`; `Scenes/Tennis.unity`, `Golf.unity`, `Hub.unity`; `DefaultVolumeProfile.asset`; `Resources/Tennis/Rendering/TennisURP_Renderer.asset`; `Unity/Packages/manifest.json`; foliage/water/weather shader implementations and material import settings. The active URP is 17.3.0. Local package source confirms tonemapping enum 2 is ACES and additional-light mode1 is per-pixel. No authored lightmap asset set was found for these runtime-built venues.

### Measured capture baseline

Component-median samples from the supplied PNGs. Golf ground box is `(.56,.76,.65,.83)`; sky box `(.45,.03,.58,.11)`. Use the same sampling code above with the corresponding capture path. These are local regions, not averages of an entire semantic surface. Tennis uses the same ground box. Cloud coverage differs; sky samples cannot be treated as identical cloud-free areas.

| Capture | Sky HSL L | Ground HSL S / L |
|---|---:|---:|
| `golf_07_clear_1_tee_gameplay` | 37.1 | 74.5 / 38.4 |
| `golf_07_gusty_1_tee_gameplay` | 50.8 | 76.2 / 37.8 |
| `golf_07_rain_1_tee_gameplay` | 60.6 | 64.2 / 37.3 |
| `golf_07_storm_1_tee_gameplay` | 33.3 | 69.0 / 34.1 |
| `golf_07_fog_1_tee_gameplay` | 72.4 | 55.9 / 41.8 |
| `tennis_resort_2_close` | — | 100.0 / 25.7 |
| `tennis_volcano_2_close` | — | 40.0 / 3.9 |

This supports the visible concern: wet-weather turf stays quite saturated while the sky changes dramatically. It does not prove wet shading is absent. Reference rain/storm turf samples are about S22/L32 and S21/L30, respectively. Their positions and lighting differ, so use these as direction checks until matched look-dev masks exist.

## C. Phased build plan — proposed, not executed

### Common proof and measurement rules

Before implementation, make a fresh baseline in a disposable scratch copy using `E/tools/EnvBriefCaptureTests.cs.txt`; never open the real project for audit captures. The supplied test has 57 frames, but only seven clear golf holes, weather on 7/20, three tennis venues and the hub. It cannot prove all-course coverage. Keep the actual live tennis camera plus the locked r2 comparison camera; preserve golf/hub framing and all gameplay data.

For future phases, propose outputs under `ArtDir/style/proof/phase_01` through `phase_07`: `before/`, `after/`, `sheets/`, `measurements.md`. None are created in this audit. Every sheet should show **BEFORE | AFTER | REF**. Include the relevant modern reference as an additional panel and classic layout reference only when useful. `E/tools/build_sheets.py` already handles an after folder and modern/classic panels; extend its reference selection for r1–r5 and isolated close/surface tests before relying on it. Replace stale “wrong now” captions with measured observations.

Use identical camera, resolution, tier, weather seed and capture time before/after. Record ROI coordinates, hex, HSL and linear luminance; separate cloud from blue sky. Compare ball and line silhouettes at actual phone display size, with grayscale/blur views. Palette tolerances are alerts, not proof of artistic quality. Final visual gates require Adnan's review of actual game renders.

On device, record model, OS, build, resolution, tier and governor reductions. Warm up, then measure the same two tennis points, hub walk and a golf hole in rain on High and Low; add storm/particle peaks. Report rendered-frame mean, p95/p99 ms, CPU/GPU time, batches/SetPass, visible and shadow triangles, transparent cost, memory and hitches. Use a 60 Hz run for the initial comparison. `Scripts/Game/FrameProbe.cs` counts Update intervals, so cross-check with actual rendered frames when `OnDemandRendering` renders less often. `Scripts/Tennis/TennisFrameGovernor.cs` already accounts for that distinction. High and Low target: 60 rendered fps (16.7 ms frame budget). Neither tier may use 30 fps as its target or fallback; report sustained misses and reduce visual cost to meet 60. Record sustained behavior after several minutes, not just an unloaded scene. Editor screenshots are not an FPS check.

### Phase 1 — Fix the bible

**Goal:** Agree on a coherent visual contract before touching rendering. Retain the modern fidelity bar and classic charm; adopt role-specific samples, material detail allowances, six shader families, consistent tonemapping, units, weather ownership and provisional device budgets.

**Files:** `ArtDir/style/ART_BIBLE.md`; later its `pal.py`, `palette.json`, palette image and `VISUAL_STANDARD_AND_JUICE.md`, if the revised standard requires them. These remain future changes.

**Measure / gate:** Every numeric target identifies its units, whether it describes a displayed pixel or material input, and a reference region. Apply the confirmed 60 fps target on all tiers and resolve DOF policy; remove contradictory master restrictions. GATE: all listed contradictions have a written decision.

**Golden proof:** A baseline/target board for resort close vs r2, golf07 tee vs r3, hub walk vs r1, r4 venues and r5 weather. The AFTER panel is explicitly “documentation only; render unchanged.” No visual improvement or FPS gain claimed.

### Phase 2 — Resort close-camera look-dev, then golf tee

**Goal:** Make one small area convincing before rollout: blue acrylic, restrained green runoff, clear tape/lines, soft contact shading, richer sky and layered islands. Then establish turf, rough, rounded trees and water in the golf07 tee view. Keep existing heroes and camera behavior.

**Files:** **new** `Scenes/LookDev_Tennis.unity`, `Scenes/LookDev_Golf.unity` and isolated look-dev assets; controlled prototype settings in `Scripts/Tennis/TennisLook.cs`, `TennisVenue.cs`, `TennisVenueArt.cs`, `Resources/Tennis/Shaders/TennisWorldSurface.shader`; golf prototypes using `Scripts/Course/GolfTurfPalette.cs`, `GolfCourseAtmosphere.cs`, `GolfCoastalTurf.cs`. Prefer isolated overrides until approved.

**Measure / gate:** Starting displayed targets: court L48, clear blue sky L61–64, lit golf turf L44, dark foliage L23; ±5 L is an investigation band for matched regions, not a pixel-copy mandate. Track stripe contrast, court/runoff hue separation and line/net stability in motion. No loss of ball readability, collision parity or Low performance. Compare Neutral/ACES here; lock one for both tiers. GATE: resort approved first, then golf, with measured device cost.

**Golden proof:** `tennis_resort_2_close`, `_4_surface`, actual `_1_gameplay` vs r2 plus modern Tennis Fever/Astro Bot details; `golf_07_clear_1_tee_gameplay`, `_2_approach`, `_3_green` vs r3 plus modern Mario Kart World. Include a short live rally/grass-motion clip.

### Phase 3 — Six master material families

**Goal:** Consolidate the approved response while retaining specialized features. M_Ground: acrylic/turf/sand/ice variants; M_Foliage: opaque rounded foliage and wind; M_Prop: stone/wood/metal and AO; M_Water: shallow/deep color, foam, cubemap/glint; M_Emissive: window and flowing-lava variants; M_Sky: painted sky with separate backdrop support.

**Files:** Refactor the existing shaders named in the gap map and `Resources/Tennis/Shaders/TennisBotanical.shader`, `Resources/Course/Shaders/GolfCoastalFoliage.shader`, `Resources/Hub/HubWater.shader`. **New** family materials under `Resources/Environment/Materials/`; shared HLSL only where it reduces duplication. Update runtime material assignment in `TennisLook.cs`, `GolfCourseLook.cs`, `GolfResortDress.cs`, `HubArt.cs` incrementally. Hero shaders remain outside this migration.

**Measure / gate:** Old/new parity before each material switch; preserve instancing, SRP batching, shadow/depth/normal passes and vertex-channel meanings. Record shader variants, texture memory, draw and GPU cost. Verify normal maps at phone scale do not shimmer. No blanket asset deletion. GATE: each family passes on High/Low and retains all required weather inputs.

**Golden proof:** Resort surface vs r2; golf tee/green vs r3; hole12 shore, hole17 ice and hole22 lava vs r4/modern water/snow/lava details; hub pavers vs r1. Use unlit/albedo and final-lit diagnostic views in the isolated scene to catch double tinting.

### Phase 4 — Lighting, post, sky and depth presets

**Goal:** Centralize Midday, Golden, Dusk-Neon, Volcano and Snow. Establish one owner for sun, ambient, fog, sky, reflections and post. Fade backdrop layers by venue scale; add restrained baked/painted bounce and optional light-shaft cards.

**Files:** **new** `Scripts/Environment/LightingPreset.cs`, `EnvironmentLook.cs`, preset/profile assets under `Resources/Environment/Looks/`; adapt `TennisLook.cs`, both tennis venue lighting partials, `GolfAtmosphere.cs`, `GolfCourseAtmosphere.cs`, `HubArt.cs`, `SportsPostProcessing.cs`, `Scripts/Game/IntroLens.cs`; existing sky shaders/textures and backdrop builders. No new real-time GI, SSR or volumetrics.

**Measure / gate:** Record effective runtime values after all overrides, not only serialized assets. Preserve highlight detail in snow, neutral stone in volcano and dark-but-visible rooftop play. Keep one shadowed main light; budget extra non-shadow lights separately. Verify bloom/DOF policy at every entry point and restore it after replay/intro. GATE: each preset passes fixed shots and High/Low device costs without changing hero assets.

**Golden proof:** Resort close vs r2; hub walk/wide vs r1; skyscraper close/surface, volcano close/surface, golf17 ice and golf22 approach vs r4 and corresponding modern panels. Daytime golf approach must show three distinguishable depth layers without hiding the destination.

### Phase 5 — Weather globals and WeatherDirector

**Goal:** Add a presentation-only adapter around existing `WeatherView`, not a second weather simulation. Drive wetness, snow deposition, storm darkness, fog and visual wind from the current five weather states, biome and authoritative game wind. Clear restores the approved venue look. Snow/ash remain biome interpretations of rain/storm.

**Files:** **new** `Scripts/Environment/WeatherDirector.cs`; adapt `Scripts/Game/WeatherView.cs`, `Scripts/Course/GolfWindSway.cs`, `Resources/Golf/WeatherCommon.hlsl`, `WeatherGround.shader`, `WeatherFog.shader`, `StormSky.shader`, `WeatherParticle.shader`, and master-family inputs. Read `RoundEvents.cs` and `Scripts/Game/GolfGame.Events.cs` as authoritative integration contracts; avoid changing their rules.

**Measure / gate:** Document global ranges/units, one writer, transition and restore ownership. Existing blend times are roughly 3–5 s for atmosphere/precipitation, 8 s wetting and 30 s drying; preserve unless deliberately revised. Use per-material wet masks; no duplicate overlay plus material darkening. Test Clear→each state→Clear and Rain→Storm→Fog on coastal, snow and ash biomes, including hole/replay/scene changes and multiplayer wind updates. Record near/far color, visible precipitation and frame cost. Run existing `RoundEventsPlayTests` after this implementation. GATE: weather behavior and wind remain intact, no leaked globals or pop on restoration.

**Golden proof:** golf07 and golf20 tee/approach in all five states vs r5 (Clear uses r3); add golf17 snowfall/blizzard and golf22 ashfall/eruption. Short clips prove gust direction, lightning/thunder delay and transitions; a still alone cannot pass those checks.

### Phase 6 — VFX and juice library

**Goal:** Turn existing pooled effects and confirmed-event feedback into a consistent library. Improve surface-specific marks, restrained contact rings, readable precipitation and celebrations. Reuse sound and native haptics; preserve live camera, hit holds and game timing.

**Files:** `Scripts/Tennis/TennisFx.cs`, `TennisVenueFx.cs`, `TennisHitFeel.cs`; `Scripts/Game/ShotEffects.cs`, `EventSounds.cs`, `Haptics.cs`; existing particle shaders and `Resources/Tennis/Fx/`. **New** shared recipes/atlas or a small event adapter only if duplication warrants it. Inspect `TennisJuice.cs`, `TennisRules.cs` and gameplay callers as constraints; timing/camera changes require a separate decision.

**Measure / gate:** Event table showing which existing visual/audio/haptic channels actually fire; zero duplicate triggers or per-event instantiate churn. Measure live particle counts and screen coverage under simultaneous rain, impact and celebration. Keep ball/face/landing area readable and support reduced motion. No required package purchase, global freeze or Decal feature. GATE: confirmed events read distinctly and obey the frame budget.

**Golden proof:** Three timed frames plus a short clip for normal/perfect contact, net hit, grass/sand/water/lava/ice landing and point celebration, against the approved r2/r3/r4 look. r1–r5 are still references and cannot establish event timing; annotate that limit rather than inventing a matching REF event.

### Phase 7 — Venue rollout and final device pass

**Goal:** Apply approved systems one venue at a time, finishing each before moving on: resort → rooftop → volcano → Cliffside → Wild Isles → Magma Open → reachable Meadow Run → hub finishing. Preserve layout, collision meshes, obstacle scan names, hazards and camera framing.

**Files:** Venue builders/art/dressing, `GolfCourseLook.cs`, course foliage/fringe/foam/backdrop builders, `HubArt.cs`, and approved materials/presets. Extend the scratch capture harness for missing holes and Meadow entry. `Scripts/Course/Hole.cs` is the roster authority: Cliffside 7/8/9/12/15; Wild Isles 13/14/17/18/19/20; Magma 10/16/21/22/23. Postcards is a retired selection alias/helper, not an additional playable course. Meadow 1–3 needs its own entry path, not `JumpToHole`.

**Measure / gate:** Complete every reachable hole and tennis venue, with tee/approach/green/overview and close/gameplay/surface views. Verify `ObstacleScan`, surface classification and collider/height parity; investigate hole14 support visibility without changing play geometry. Check weather on every biome and Low/High material fallbacks. Run focused `CourseReviewTests`, `RoundEventsPlayTests`, relevant tennis smoke/camera tests and existing visual/physics parity tooling when applicable. Then perform the sustained on-device comparison above. GATE: no uncovered venue, physics/weather regression or unexplained frame-cost increase.

**Golden proof:** Expand the supplied 57-frame set to the complete roster. BEFORE | AFTER | REF uses r1 hub, r2 resort, r3 golf, r4 special venues, r5 weather, with modern detail panels. Each phase report is three lines: what changed; which sheet paths prove it; measurements and remaining failures. Final report lists sheet paths, tested devices/tiers and any failed or unmeasured gate.

## D. Decisions for Adnan

1. **Resolved: always target 60 fps on all tiers; never 30.** Minimum acceptance-device model is still to be named.
2. **Resolved: 2B**, blue acrylic resort court with a muted green surround.
3. **Open:** the generated Neutral/ACES-style board was not distinguishable enough for Adnan to choose. Use a matched actual Unity comparison, with the same lighting, exposure, materials and camera, before choosing one tonemapper for both tiers.
4. **Visual direction chosen: 4B**, subtle far-background blur on High, with all gameplay elements sharp. Low stays off; 60 fps takes priority. The reference choice does not require blur in every scene or during every live-play moment.
5. **Visual direction chosen: 5B**, restrained surface detail: acrylic grain, near-camera grass, layered ice and lava crust. This supports revising overly restrictive material rules; exact shader-family architecture remains an implementation detail for a later authorized pass.

Visual examples requested after the audit are saved in `ArtDir/style/decision-refs-2026-10-14/`: [2 court palette](decision-refs-2026-10-14/02_court_colors.png), [3 grading](decision-refs-2026-10-14/03_color_grading.png), [4 background focus](decision-refs-2026-10-14/04_background_focus.png), [5 material detail](decision-refs-2026-10-14/05_surface_detail.png). These built-in imagegen concepts illustrate appearance choices; they are not game captures, exact tonemapper simulations or performance evidence. Decision 5 compares surface treatment, not invisible shader architecture. The [prompt set and notes](decision-refs-2026-10-14/PROMPTS_AND_NOTES.md) record inputs and limitations. Choices 2B, 4B and 5B are recorded; decision 3 remains open.

Original audit verification: GATE: requested document and independent samples PASS. The 3,363 pre-existing files checked across Unity assets/settings/packages, style inputs and the Git index retained their baseline hashes. Only the audit document was written during that audit pass; the later visual-comparison pass adds reference images and notes. GATE: implementation appearance and on-device FPS NOT TESTED; these remain future work.

## Five-line summary

1. Keep the modern fidelity bar; the current bible is too rigid about saturation, shadows and material detail.
2. Fix the dark courts, saturated wet turf and weak depth using existing systems before adding new ones.
3. Consolidate runtime lighting/post ownership and enforce quality gates for hub, intro and replay effects.
4. Preserve cameras, heroes, physics, event timing and working weather; device performance is still unmeasured.
5. Start with Phase 1 bible decisions, then prove the resort close view against r2 before any wider rollout.
