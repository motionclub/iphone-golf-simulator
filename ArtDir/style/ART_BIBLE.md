# Party Sports: Art Bible v0.2 (Oct 15, 2026)
This is the single standard every scene, material and effect must match. **Every number here is a starting target to tune by eye in the look-dev scene. None of them are laws.** Once Adnan approves the look-dev scene, the values it ends up with replace these.

Refs: `refs/r1.png` hub at golden hour · `r2` resort tennis with the close cam · `r3` golf tee · `r4` venue grid (rooftop dusk, volcano, ice, magma golf) · `r5` golf weather grid (rain, storm, fog, gusty).
Palette sheet: `ART_BIBLE_palette.png`. Colors were pulled with code (8-color k-means per image plus median samples of hand-picked regions; glows and lines use the 92nd-percentile brightness). The script is `pal.py` and the raw values are in `palette.json`. The refs are AI-made, so copy the *rules*, not the pixels.

## 1. Style DNA (the 6 rules)
1. **Purposeful color.** Use role-specific displayed sRGB samples: clear r3 sky can reach HSL S98; r4 stone can be S5. Palette relationships and readability take precedence over a universal saturation band.
2. **Warm key, cool fill.** The sun is warm (cream to peach), and shadows and ambient light are blue-violet. Shadows are never grey or black.
3. **Layered haze.** Distance moves toward the local horizon color and lower contrast (see §6); golden and desert haze can be warm.
4. **Big round shapes.** The world is chunky, rounded and toy-like, with stable, readable detail. Net strings, lines and grass blades are permitted; reject phone-scale shimmer.
5. **Painted cumulus skies.** Puffy clouds with lit tops and blue-grey bellies. Gradients support the painted clouds; they do not replace cloud form.
6. **Emissive accents pop.** Strong bloom belongs to lamps, windows, lava and neon. Restrained sky/highlight bloom is allowed; threshold selects brightness, not material names.

## 2. Master palette (sampled hex values)
| Role | Hex | Source / note |
|---|---|---|
| Clear blue zenith | #4AB1FD (golf) / #46A0F1 (tennis) | r3 (.38,.03,.46,.08), r2 (.47,.03,.53,.09) |
| Cloud lit / belly | #F3EAE4 / #A8C5ED | r2 top (.585,.19,.615,.21); belly family retained |
| Haze / far islands | #8CB2CB (tennis), #75A3B0 (golf mountains) | r2, r3 |
| Water near / far | #63AFE8 / #339FE5 | r3, r2 |
| Grass, lit stripe | #86AB29 | r3 |
| Grass, far / bright stripe | #A1C33E | r3 |
| Grass, in shadow | #5C7F27 | r3 |
| Foliage, dark mass | #235321 (golf), #484E28 (hub) | r3, r1 |
| Court, resort hard court | #2089D8 | r2 |
| Court surround | #367A86 (teal-green) | r2 |
| Lines | #FFFDF2 (warm white, never pure #FFFFFF) | r2 |
| Stone deck (cool) | #BDB7BB | r2 |
| Hub pavers (warm) | #D4A784 | r1 |
| Hub roof navy | #494F6B | r1 |
| Golden-hour horizon glow | #FEE89B | r1 |
| Golden-hour upper sky | #A8B5D4 blue / #CEB4BC lilac cloud | r1 blue (.30,.04,.40,.11) |
| Lamp / window glow | #FDD596 | r1 |
| Rooftop dusk sky / court | #A96A9A / #1A4D9C | r4 |
| Neon / city window | #E46117 | r4 |
| Volcano sky / court | #8B4F79 / #887D80 (grey court) | r4 |
| Lava | #FC9922 core, #E76F34 edge | r4 |
| Magma rock | #2A202D charcoal-violet / #421518 warm face | r4 charcoal (.88,.75,.91,.79) |
| Ice / snow sky | #4CA4C6 / #729BDD | r4 |
| Weather skies | rain #7085A2 · storm #3B567D · fog #E2D2C1 · gusty #83C0F2 | r5 |
| Weather grass | rain #456438 · storm #38563F · fog #5A7A39 · gusty #5D7734 | r5 |
| **Hazard (reserved)** | **#FF5A1F** orange-red. Hazards and warnings only, never decoration. | chosen, not sampled |
| **Ball / hero highlight (reserved)** | ball #FFF36B and the hero's own outfit colors | chosen |

All palette values above describe displayed sRGB pixels, never shader albedo or HDR energy. Normalized sample boxes and independent HSL measurements are in AUDIT_AND_PLAN.md §A. Hub lit pavers #DDAC83 and shaded pavers #957D79 replace the mislabeled #D2A281 shadow. Golf far hills may use #8AAFB4. Fog ambient is cool #ACB4C5; the localized sunlight is warm #FBE5C5. Rain/storm turf samples are #486540/#3C5C42. Hazard/ball colors are authored conventions, not sampled targets.

## 3. Value structure (L = HSL lightness 0–100, measured from the refs)
- **Sky is lighter than ground** in every daytime state: clear blue sky L61–64, lit cloud L92, grass L33–50, foliage masses L 22–25.
- **Shadow vs lit:** use about 10–18 HSL L separation as a starting relationship, with one cool ambient tint (grass lit L42 → shadow L33).
- **Distance:** far objects get +10–25 L and lose 30–50% saturation (court L49 → haze L67 at S38).
- **Darkest darks** are foliage cores and magma rock (L17–25). Small occlusion cores can be darker; do not erase form by lifting every shadow.
- **Brightest** are lines, glows and highlights (L79–97), which should stay under 10% of the frame.
- **Hero and ball must be the highest-contrast thing** at their screen position. Test it by squinting or blurring the screenshot.

## 4. Lighting targets per preset (URP; starting values)
| Preset | Sun elevation / color / intensity | Ambient (gradient) sky · equator · ground | Shadow strength | Fog color · start–end (linear) or density | Grading |
|---|---|---|---|---|---|
| Midday (resort, golf clear, gusty) | 50° · #FFF1D8 · 1.4 | #9CC7F5 · #B7CFD9 · #6E7F4A | 0.75 | #A9C8DE · 60–260 m | ACES tonemap, post-exposure +0.1, contrast +10, saturation +8, white-balance temp +5 |
| Golden (hub) | 12° · #FFC98A · 1.2 | #C8B1C8 · #E6C7A8 · #6A5A48 | 0.7 | #E8C9B0 · 40–200 m | temp +15, saturation +10, lift shadows toward #4A4A6E |
| Dusk-Neon (rooftop) | 6° · #FF9E7A · 0.6 + a cool moonlight fill | #6E5A9A · #A96A9A · #2A2A44 | 0.6 | #8E6C9E · 50–220 m | temp −5, saturation +12, bloom up |
| Volcano | 20° · #FF8A5A · 0.9 | #6B3F6A · #A05A4E · #2B1418 | 0.7 | #7A4660 · 30–180 m | temp +10, contrast +15 |
| Snow / ice | 25° · #FFE6CC · 1.3 | #9FBDF0 · #D6E4F5 · #C8D8EC | 0.65 | #C9DAF0 · 50–240 m | temp −10, saturation −5, post-exposure +0.2 |
- **Shadow tint:** comes from ambient sky/equator/ground once. No fixed 35% blue overlay on top of already cool ambient.
- **Hero fill/rim/ambient:** each lighting preset owns the §15 analytic hero values alongside the world values. Keep the existing hero-only rendering layer; no new realtime light or shadow map.
- **Bloom:** threshold 1.1 (HDR), intensity 0.35, scatter 0.6. Only emissives (lamps, lava, neon, perfect-hit FX) should go over the threshold.
- **Tonemapping:** ACES on every tier. Adnan selected ACES on 2026-10-15 from `proof/phase_02/actual_unity_neutral_aces.jpg`, a matched actual Unity comparison. Diagnostic Neutral overrides do not change that decision.
- Runtime-built scenery starts with existing vertex/painted AO, bounce and trilight ambient. No baked-lightmap claim without authored lightmap evidence. Keep one shadowed main light; inventory existing unshadowed fills separately.
- Table values are prototype inputs, not measured results: light intensity is Unity linear light energy, angles are degrees, colors are authored sRGB; post contrast/saturation are Unity parameter units. Fog ranges are physical meters. Golf uses yards (meters / 0.9144); tennis/hub use meters. Calibrate to venue extent, never crop a whole course at 260 m.

## 5. Shape language
- Rounded silhouettes, toy-like proportions, slightly oversized props (benches, lamps and umpire chair at about 1.2× real size).
- Trees are clustered round blobs (3 sizes × 3 variants), palms have thick fronds, and conifers in snow are stacked cones.
- Nothing player-relevant thinner than about 10 cm at play distance. No straight parallel edges on organic shapes ("wonky" slightly).
- Hazards and obstacles are chunky and obvious, outlined by the hazard color or a rim.

## 6. Depth and haze layers (every outdoor venue has all 4)
1. **Play space:** full color.
2. **Near dressing (to about 40 m):** full color, slightly darker than the play space so the court or fairway pops.
3. **Mid backdrop (hills, islands, buildings; about 80–200 m):** +12 L, −30% saturation, tinted toward the fog color.
4. **Far backdrop (mountains, skyline; cards past 200 m):** +25 L, −50% saturation, nearly the fog color. One silhouette edge only.
Fog approaches the relevant horizon region for that preset. Layer ranges are illustrative physical meters, not universal cutoffs. Preserve full near-play color and three distinguishable backdrop layers; warm haze is valid. Measure HSL L/S per fixed ROI and also linear luminance for readability.

## 7. Sky rules
- One painted skybox per preset (cumulus for midday, warm streaks for golden, purple-orange for dusk and volcano). Clouds have lit tops and #8FA6C8-ish bellies.
- The sun disc is visible in golden and dusk only. Slow cloud UV scroll (or cloud-shadow cookie on the ground) at about 0.005 per second.
- Clear sky HSL L61–64 and lit cloud near L92 are distinct daytime roles. Storm skies drop to about L36 but stay blue, never grey.

## 8. Six material families (initial refactoring allowed; preserve specialist variants)
| Master | Used for | Core inputs (detail and specialist inputs allowed) |
|---|---|---|
| `M_Ground` | grass, fairway, rough, sand, court, ice | BaseColor, StripeColor, StripeWidth, NoiseScale/Amount, ShadowTint, Smoothness, reads globals `_Wetness`, `_Snow` |
| `M_Foliage` | trees, bushes, palms, flowers | TopColor, BottomColor (gradient), Translucency, WindWeight, reads `_WindStrength`, `_WindDir`, `_Snow` |
| `M_Prop` | buildings, benches, fences, rocks, net posts | BaseColor/Texture, AOTint, ShadowTint, RimStrength, reads `_Wetness`, `_Snow` |
| `M_Water` | sea, ponds, puddles | ShallowColor, DeepColor, FoamColor, FoamWidth, WaveSpeed |
| `M_Emissive` | lava, lamps, neon, windows | EmissionColor, EmissionHDR (≤ 3), PulseSpeed, PulseAmount |
| `M_Sky` | skyboxes, backdrop cards | Texture, Tint, FogBlend, ScrollSpeed |
Preserve quiet mipmapped normals, roughness masks, acrylic grain, water depth/foam, ice layering and lava flow/cooling. HLSL is valid; Shader Graph is optional. Family materials may use existing specialist shaders; retain instancing, SRP batching and all shadow/depth passes before switching assignments. Hero shaders are outside this migration. Texture density starts at 256 px/physical m near play, 64 px/m in backdrops; verify on phone and convert golf yards. No blanket shader deletion.

## 9. Glow rules
- Reserve strong glow for emissives/FX; small sky/highlight contributions may cross the luminance threshold.
- Glow color stays inside the palette: lamp #FDD596, lava #FC9922, neon #E46117 or cool accents.
- In daylight, glows are subtle (EmissionHDR ≤ 1.5). In golden, dusk and volcano they are strong (up to 3).

## 10. Readability rules
- The hero and ball always contrast with the ground behind them (blur test). Reserve the ball yellow #FFF36B.
- **Hazard color #FF5A1F is reserved.** It appears only on hazards, warnings and danger telegraphs. Lava and magma use their own palette and must still get a hazard edge or rim where play can touch it.
- Lines are warm white, thick enough to read at the close cam (measure the existing width and phone-size stability before changing).
- HUD sits over the image without hiding the landing area. No decoration may out-contrast the hero.

## 11. Weather presentation (one adapter around authoritative WeatherView)
| State | `_Wetness` | `_WindStrength` | `_Snow` | `_StormDarkness` | Fog density / color | Sky / grade | VFX + audio |
|---|---|---|---|---|---|---|---|
| Clear | 0 | 0.2 | 0 | 0 | preset default | preset | birds or ambience |
| Gusty | 0 | 0.9 | 0 | 0 | default | #83C0F2 sky, contrast +5 | leaf streams, flag snaps, whoosh bed |
| Rain | 0.8 | 0.4 | 0 | 0.3 | +40%, #8C9AAE | #7085A2 sky, saturation −20, temp −10 | camera-local rain, splash rings, puddle decals, rain bed |
| Storm | 1.0 | 0.8 | 0 | 0.7 | +60%, #5A6E8C | #3B567D sky, exposure −0.4 | rain plus lightning flash (ambient spike 0.1 s), thunder 0.5–2 s later |
| Fog | 0.2 | 0.1 | 0 | 0 | ×3, #E2D2C1, far end about 120 m | low contrast −15 | ground wisp cards, muffled ambience |
| Snow | 0 | 0.3 | 1.0 | 0 | +20%, #C9DAF0 | snow preset | snowfall, breath puffs |
The table is a visual direction, not a second weather simulation. Keep the existing five game states: snow and ash interpret rain/storm by biome. WeatherView owns transition amounts; WeatherDirector publishes visual globals and hero clamp from those same amounts. Read authoritative wind; never alter rules. `_Wetness` is currently material-local: use distinct environment globals and one consumer per response to avoid double darkening. Wet grass stays rough, stone/metal can gloss; tune masks per family. Preserve 3–5 s atmosphere/precipitation, 8 s wetting and 30 s drying. Clear and scene/hole/replay transitions restore the preset and reset globals. The fog target is cool ambient #ACB4C5 plus localized warm sunlight; do not turn the entire foreground beige.

## 12. Juice principles
- Every important event gets **at least 3 channels**: visual, sound, and motion or haptic. Scale it by importance (normal hit < perfect < ace or putt drop).
- Audit actual existing event bindings against `VISUAL_STANDARD_AND_JUICE.md` §4. Preserve tennis holds of 14/30/45 ms by grade and live input. No global time freeze, duplicate trigger or speculative hit.
- Hazards always telegraph: idle motion, hazard color, and a warning about 0.5 s before danger.
- Preserve animations, live cameras, time, gameplay and physics. Work within confirmed FX/audio/haptic bindings only; no disabled camera punch restoration.

## 13. iPhone budget (starting targets; tune on device)
- **60 rendered fps on every tier (16.7 ms/frame), never a 30 fps target or fallback.** Measure sustained on-device runs; reduce visual cost to meet it.
- One realtime shadowed main light. Record batches/SetPass, visible/shadow triangles, fragment/transparent cost, texture memory, CPU/GPU mean/p95/p99. Allocate environment budget after fixed hero cost; 150 draws/150k triangles are investigation prompts, not verified universal budgets.
- Same mapper across tiers; Low bloom and DOF off. High may use subtle far-background blur only when players/ball/net/court stay sharp and 60 fps survives. Gate all hub/intro/replay entry points and restoration.
- Built-in pooled particles; measure live counts and screen coverage per effect/tier. Existing rain/snow maxima exceed 300; do not impose an unmeasured universal cap or remove weather.
- ASTC appropriate to content; preserve face quality and existing sky detail. Texture limits require memory/phone-scale evidence, not a universal 1024 cap. Minimum acceptance device is still to be named; editor renders do not prove fps.

## 14. Golden shots (the acceptance test)
Fixed cameras per venue and weather (reuse `tools/EnvBriefCaptureTests`). Each phase delivers BEFORE | AFTER | REF sheets plus measured average sky and ground L, compared with §3, plus FPS. Adnan's eye gives final approval.

## 15. Character lighting

**Why:** the heroes are the game. Today they take whatever light the venue gives them (tennis uses raw scene lights + `SampleSH` ambient; golf swaps in the sun as key). Result (Oct 14 captures, `character-lighting/`): Volcano tennis body sinks into a near-black court (mask L6, but re-check: the shirt reads in the image), silhouette lost at Resort (female dL 3.7), Skyscraper (dL 4.0), golf 16 Volcano Rim (dL 2.7) and 17 Frostbite (dL 3.7–6.4); golf faces L14–19 under the cap; fog greys skin (#A9ACAE). The lobby (SceneKit) uses a proper 3-point rig, so heroes look better in the lobby than in play.

**Rules (starting targets, tune by eye):**
1. **Character light layer.** Heroes get their own key/fill/rim that only touches the hero (URP rendering layer, or the existing `HeroPresentationLight` path in `HeroLighting.hlsl`, which costs no light slot). Key follows the venue sun's direction and hue; fill comes from the camera side; rim from behind the hero relative to the camera.
2. **Ambient clamp.** Hero ambient = `SampleSH` clamped to luminance 0.12–0.60 (linear) and HSV saturation ≤ 0.60, so dark venues can't black the hero and fog can't grey it.
3. **Skin target.** Face skin, any venue or weather, from the gameplay cam: Lab **L 45–65**, **a 10–20**, **b 18–30** (hub/lobby reads L42–50, a≈15, b≈27). Never L < 35.
4. **Max venue tint.** Venue light may shift skin hue by at most **Δhue 10°** and Δb ±8 from the hub reference. Lava orange and dusk purple tint the rim, not the face.
5. **Form shadows.** Hero light shadow attenuation floor **0.15**. Fill **0.35**, direction normalize(view*.80 + up*.60 − right*.30); nominal key:fill about 3:1. Face-only brim lift ≤0.20. Skin shoulder knee/ceiling **0.60/0.95 linear RGB**. Ground contact shadows stay full.
6. **Rim per preset** (authored sRGB color; linear strength capped **0.35**, cubic grazing lobe): Midday (1,.96,.88), Golden (1,.85,.65), Dusk-Neon (.85,.93,1), Volcano (1,.7,.45), Snow (.85,.93,1); Rain/Storm (.8,.88,1), Fog .25 strength. Multiply by saturate(dot(normal,keyDirection)*.7+.3). On bright backgrounds the hero can read darker; never wrap every edge in light.
7. **Silhouette contrast.** Median hero edge vs surrounding ring: **dL ≥ 15** in every gameplay shot (hub is ~30). If the background is bright (snow, fog), the hero goes darker with a strong rim; if dark (volcano, night), the hero goes brighter.
8. **Clothing readability.** Shirt keeps its palette hue (Δhue ≤ 12°) and L ≥ 25; dark kits (navy, black trousers) get rim before they get brighter.
9. **Lobby parity.** In-game hero under the Resort preset should match the lobby (key 1050 warm @40° camera-left, fill 35% cool, rim 50% from behind, ambient 210 cool) within dL 8 on face and shirt. Side-by-side check in the look-dev scene.
10. **iPhone cost.** No extra realtime lights or shadow maps. Fill and rim are analytic in the hero shaders (≈10 ALU); globals set per preset; budget +0.2 ms GPU on iPhone 13 at most.

**Check:** run `character-lighting/tools/CharLightCaptureTests.cs.txt` (copy into a scratch clone as a PlayMode test); the metrics JSON must pass rules 3, 4, 7 and 8 on every shot.

## 16. Combined implementation proof (2026-10-15)
The user authorized COMBINED_PLAN_PROMPT.md implementation, starting with FIX_PROMPT.md, then environment phases 1–7. Stage only; no commit/push/stash/checkout. Scratch-only foreground captures. Preserve meshes, rig/animation, physics/gameplay and production camera framing. Phase status lives in proof/EXECUTION.md. Unmeasured or failed gates stay explicit; no blanket pass from screenshots.

Hero fix additional targets: whole-hero HSV saturation ≥.62; gameplay detail ≥6.8; darkest 5% CIELAB L3–12; silhouette dL≥15 in at least 110/168 gameplay captures. The combined rollout target remains every gameplay shot. Saturation/detail aggregation was not defined in the prompt: measurement reports must state the estimator and cannot silently reinterpret it to obtain PASS. Current measured matching-color lobby faces are L58.80/66.97 tennis and L66.69/67.01 golf (after/GATE_RESULTS.md), superseding the earlier L42–50 estimate. Lobby parity and face L45–65 gates remain separately reported.

Implementation note: the compact hub uses layered scenery haze with linear fog disabled, preserving its existing painted Unlit sky dome. Golf and tennis retain calibrated linear fog plus layered depth; golf distances are converted from metres to yards. Rain reaches fully overcast hero compensation at its existing precipitation amount .62; this does not change the weather timer or precipitation output.

## 2026-10-15 — character-lighting reversal

Adnan rejected the combined pass’s character lighting and requested reversing that part only. Restore the five pre-pass hero shader/profile files and remove preset-owned hero fill/rim/ambient integration. Environment lighting, ACES, distance haze, world weather, materials and FX remain. The character-lighting targets and earlier combined proof are historical guidance, not permission to reapply the rejected look.
