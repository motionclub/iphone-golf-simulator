# Party Sports: Art Bible v0.1 (Oct 14, 2026)
This is the single standard every scene, material and effect must match. **Every number here is a starting target to tune by eye in the look-dev scene. None of them are laws.** Once Adnan approves the look-dev scene, the values it ends up with replace these.

Refs: `refs/r1.png` hub at golden hour · `r2` resort tennis with the close cam · `r3` golf tee · `r4` venue grid (rooftop dusk, volcano, ice, magma golf) · `r5` golf weather grid (rain, storm, fog, gusty).
Palette sheet: `ART_BIBLE_palette.png`. Colors were pulled with code (8-color k-means per image plus median samples of hand-picked regions; glows and lines use the 92nd-percentile brightness). The script is `pal.py` and the raw values are in `palette.json`. The refs are AI-made, so copy the *rules*, not the pixels.

## 1. Style DNA (the 6 rules)
1. **Saturated but not neon.** Local colors have saturation of about 50–80%. Only glows and lines go above 90%.
2. **Warm key, cool fill.** The sun is warm (cream to peach), and shadows and ambient light are blue-violet. Shadows are never grey or black.
3. **Layered haze.** Every step back in distance gets lighter, bluer and lower in contrast (see §6).
4. **Big round shapes.** The world is chunky, rounded and toy-like, with no realistic thin detail.
5. **Painted cumulus skies.** Puffy clouds with lit tops and blue-grey bellies. No flat gradients.
6. **Emissive accents pop.** Lamps, windows, lava and neon are the *only* things that bloom.

## 2. Master palette (sampled hex values)
| Role | Hex | Source / note |
|---|---|---|
| Sky top, midday | #58B7FE (golf) / #7FB4F3 (tennis) | r3, r2 |
| Cloud lit | #A8C5ED → paint the tops close to #F4F7FC | r2 (the sample includes the cloud bellies) |
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
| Golden-hour upper sky | #CEB4BC (dusty lilac) | r1 |
| Lamp / window glow | #FDD596 | r1 |
| Rooftop dusk sky / court | #A96A9A / #1A4D9C | r4 |
| Neon / city window | #E46117 | r4 |
| Volcano sky / court | #8B4F79 / #887D80 (grey court) | r4 |
| Lava | #FC9922 core, #E76F34 edge | r4 |
| Magma rock | #421518 | r4 |
| Ice / snow sky | #4CA4C6 / #729BDD | r4 |
| Weather skies | rain #7085A2 · storm #3B567D · fog #E2D2C1 · gusty #83C0F2 | r5 |
| Weather grass | rain #456438 · storm #38563F · fog #5A7A39 · gusty #5D7734 | r5 |
| **Hazard (reserved)** | **#FF5A1F** orange-red. Hazards and warnings only, never decoration. | chosen, not sampled |
| **Ball / hero highlight (reserved)** | ball #FFF36B and the hero's own outfit colors | chosen |

Known sampling quirks: the hub "shadow" sample (#D2A281) is almost the same as the lit one, because the refs keep paver shadows soft. Target shadows about 15–20 lightness points darker.

## 3. Value structure (L = HSL lightness 0–100, measured from the refs)
- **Sky is lighter than ground** in every daytime state: sky L 67–80, grass L 33–50, foliage masses L 22–25.
- **Shadow vs lit:** a shadow is about 10–18 L darker and *shifted blue* (grass lit L42 → shadow L33).
- **Distance:** far objects get +10–25 L and lose 30–50% saturation (court L49 → haze L67 at S38).
- **Darkest darks** are foliage cores and magma rock (L17–25). Never use pure black.
- **Brightest** are lines, glows and highlights (L79–97), which should stay under 10% of the frame.
- **Hero and ball must be the highest-contrast thing** at their screen position. Test it by squinting or blurring the screenshot.

## 4. Lighting targets per preset (URP; starting values)
| Preset | Sun elevation / color / intensity | Ambient (gradient) sky · equator · ground | Shadow strength | Fog color · start–end (linear) or density | Grading |
|---|---|---|---|---|---|
| Midday (resort, golf clear, gusty) | 50° · #FFF1D8 · 1.4 | #9CC7F5 · #B7CFD9 · #6E7F4A | 0.75 | #A9C8DE · 60–260 m | Neutral tonemap, post-exposure +0.1, contrast +10, saturation +8, white-balance temp +5 |
| Golden (hub) | 12° · #FFC98A · 1.2 | #C8B1C8 · #E6C7A8 · #6A5A48 | 0.7 | #E8C9B0 · 40–200 m | temp +15, saturation +10, lift shadows toward #4A4A6E |
| Dusk-Neon (rooftop) | 6° · #FF9E7A · 0.6 + a cool moonlight fill | #6E5A9A · #A96A9A · #2A2A44 | 0.6 | #8E6C9E · 50–220 m | temp −5, saturation +12, bloom up |
| Volcano | 20° · #FF8A5A · 0.9 | #6B3F6A · #A05A4E · #2B1418 | 0.7 | #7A4660 · 30–180 m | temp +10, contrast +15 |
| Snow / ice | 25° · #FFE6CC · 1.3 | #9FBDF0 · #D6E4F5 · #C8D8EC | 0.65 | #C9DAF0 · 50–240 m | temp −10, saturation −5, post-exposure +0.2 |
- **Shadow tint:** via the ambient ground and equator plus the master-shader `ShadowTint` (#5A6FA8 at about 35%).
- **Rim light:** only in the hero shader, warm-white, about 0.25 strength, facing the camera.
- **Bloom:** threshold 1.1 (HDR), intensity 0.35, scatter 0.6. Only emissives (lamps, lava, neon, perfect-hit FX) should go over the threshold.
- **Tonemapping:** Neutral for everything. ACES is optional on High only, if Adnan prefers more contrast.
- Static scenery is baked (lightmaps + light probes), with one realtime sun for hero and ball shadows.

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
Fog color always equals the sky's horizon color for that preset.

## 7. Sky rules
- One painted skybox per preset (cumulus for midday, warm streaks for golden, purple-orange for dusk and volcano). Clouds have lit tops and #8FA6C8-ish bellies.
- The sun disc is visible in golden and dusk only. Slow cloud UV scroll (or cloud-shadow cookie on the ground) at about 0.005 per second.
- Sky value is L 67–80 by day. Storm skies drop to about L36 but stay blue, never grey.

## 8. Material rules (only these masters; agents may not create new shaders)
| Master | Used for | Allowed params (nothing else) |
|---|---|---|
| `M_Ground` | grass, fairway, rough, sand, court, ice | BaseColor, StripeColor, StripeWidth, NoiseScale/Amount, ShadowTint, Smoothness, reads globals `_Wetness`, `_Snow` |
| `M_Foliage` | trees, bushes, palms, flowers | TopColor, BottomColor (gradient), Translucency, WindWeight, reads `_WindStrength`, `_WindDir`, `_Snow` |
| `M_Prop` | buildings, benches, fences, rocks, net posts | BaseColor/Texture, AOTint, ShadowTint, RimStrength, reads `_Wetness`, `_Snow` |
| `M_Water` | sea, ponds, puddles | ShallowColor, DeepColor, FoamColor, FoamWidth, WaveSpeed |
| `M_Emissive` | lava, lamps, neon, windows | EmissionColor, EmissionHDR (≤ 3), PulseSpeed, PulseAmount |
| `M_Sky` | skyboxes, backdrop cards | Texture, Tint, FogBlend, ScrollSpeed |
Textures are simple and hand-painted-style, with no photo textures and no noisy normal maps. Keep texel density consistent (about 256 px/m near the play space, about 64 px/m on the backdrop).

## 9. Glow rules
- Only `M_Emissive` and FX particles may exceed bloom threshold.
- Glow color stays inside the palette: lamp #FDD596, lava #FC9922, neon #E46117 or cool accents.
- In daylight, glows are subtle (EmissionHDR ≤ 1.5). In golden, dusk and volcano they are strong (up to 3).

## 10. Readability rules
- The hero and ball always contrast with the ground behind them (blur test). Reserve the ball yellow #FFF36B.
- **Hazard color #FF5A1F is reserved.** It appears only on hazards, warnings and danger telegraphs. Lava and magma use their own palette and must still get a hazard edge or rim where play can touch it.
- Lines are warm white, thick enough to read at the close cam (resort lines about 2× current width; tune by eye).
- HUD sits over the image without hiding the landing area. No decoration may out-contrast the hero.

## 11. Weather as global parameters (one `WeatherDirector` sets them; shaders read them)
| State | `_Wetness` | `_WindStrength` | `_Snow` | `_StormDarkness` | Fog density / color | Sky / grade | VFX + audio |
|---|---|---|---|---|---|---|---|
| Clear | 0 | 0.2 | 0 | 0 | preset default | preset | birds or ambience |
| Gusty | 0 | 0.9 | 0 | 0 | default | #83C0F2 sky, contrast +5 | leaf streams, flag snaps, whoosh bed |
| Rain | 0.8 | 0.4 | 0 | 0.3 | +40%, #8C9AAE | #7085A2 sky, saturation −20, temp −10 | camera-local rain, splash rings, puddle decals, rain bed |
| Storm | 1.0 | 0.8 | 0 | 0.7 | +60%, #5A6E8C | #3B567D sky, exposure −0.4 | rain plus lightning flash (ambient spike 0.1 s), thunder 0.5–2 s later |
| Fog | 0.2 | 0.1 | 0 | 0 | ×3, #E2D2C1, far end about 120 m | low contrast −15 | ground wisp cards, muffled ambience |
| Snow | 0 | 0.3 | 1.0 | 0 | +20%, #C9DAF0 | snow preset | snowfall, breath puffs |
Wet look: `_Wetness` lowers albedo by about 25% and raises smoothness to about 0.75 on M_Ground and M_Prop, matching rain grass L31 vs clear L34–42. Transitions blend over 3–5 s.

## 12. Juice principles
- Every important event gets **at least 3 channels**: visual, sound, and motion or haptic. Scale it by importance (normal hit < perfect < ace or putt drop).
- Use the event table in `VISUAL_STANDARD_AND_JUICE.md` §4 (swing, hit, perfect hit with 50–80 ms hit-stop, flight trail, per-surface landing, putt drop, ace, net cord, weather, hazards, UI wins).
- Hazards always telegraph: idle motion, hazard color, and a warning about 0.5 s before danger.
- Don't touch hero animations for juice; use FX, camera, time, UI, audio and haptics.

## 13. iPhone budget (starting targets; tune on device)
- 60 fps High tier / 30 fps Low tier, measured on device.
- Under about 150 draw calls, under about 150k triangles on screen, 1 realtime shadowed light.
- Post: tonemapping, color adjustments/LUT and bloom on High. Low drops bloom to half resolution or turns it off. Depth of field is on High only, and only in replays.
- Particles: built-in Particle System, at most about 300 live particles on screen, small transparent quads, one shared atlas.
- Textures in ASTC, with most at 1024 or below.

## 14. Golden shots (the acceptance test)
Fixed cameras per venue and weather (reuse `tools/EnvBriefCaptureTests`). Each phase delivers BEFORE | AFTER | REF sheets plus measured average sky and ground L, compared with §3, plus FPS. Adnan's eye gives final approval.

## 15. Character lighting

**Why:** the heroes are the game. Today they take whatever light the venue gives them (tennis uses raw scene lights + `SampleSH` ambient; golf swaps in the sun as key). Result (Oct 14 captures, `character-lighting/`): Volcano tennis body sinks into a near-black court (mask L6, but re-check: the shirt reads in the image), silhouette lost at Resort (female dL 3.7), Skyscraper (dL 4.0), golf 16 Volcano Rim (dL 2.7) and 17 Frostbite (dL 3.7–6.4); golf faces L14–19 under the cap; fog greys skin (#A9ACAE). The lobby (SceneKit) uses a proper 3-point rig, so heroes look better in the lobby than in play.

**Rules (starting targets, tune by eye):**
1. **Character light layer.** Heroes get their own key/fill/rim that only touches the hero (URP rendering layer, or the existing `HeroPresentationLight` path in `HeroLighting.hlsl`, which costs no light slot). Key follows the venue sun's direction and hue; fill comes from the camera side; rim from behind the hero relative to the camera.
2. **Ambient clamp.** Hero ambient = `SampleSH` clamped to luminance 0.25–0.60 (linear) and saturation ≤ 0.35, so dark venues can't black the hero and fog can't grey it.
3. **Skin target.** Face skin, any venue or weather, from the gameplay cam: Lab **L 45–65**, **a 10–20**, **b 18–30** (hub/lobby reads L42–50, a≈15, b≈27). Never L < 35.
4. **Max venue tint.** Venue light may shift skin hue by at most **Δhue 10°** and Δb ±8 from the hub reference. Lava orange and dusk purple tint the rim, not the face.
5. **Shadow strength.** Self-shadow on the hero at most **0.6**; contact shadow on the ground stays full. Cap/brim shadow on the face lifted by fill so the face stays ≥ L35.
6. **Rim per preset** (colour, strength, fresnel power ~3): Resort warm white (1,.96,.88) 0.35 · Skyscraper cool cyan-white (.85,.93,1) 0.5 · Volcano warm orange (1,.7,.45) 0.55 · Golf Clear 0.35 · Rain/Storm cool (.8,.88,1) 0.5 · Fog 0.25 (fog already separates) · Dusk holes (16) 0.55.
7. **Silhouette contrast.** Median hero edge vs surrounding ring: **dL ≥ 15** in every gameplay shot (hub is ~30). If the background is bright (snow, fog), the hero goes darker with a strong rim; if dark (volcano, night), the hero goes brighter.
8. **Clothing readability.** Shirt keeps its palette hue (Δhue ≤ 12°) and L ≥ 25; dark kits (navy, black trousers) get rim before they get brighter.
9. **Lobby parity.** In-game hero under the Resort preset should match the lobby (key 1050 warm @40° camera-left, fill 35% cool, rim 50% from behind, ambient 210 cool) within dL 8 on face and shirt. Side-by-side check in the look-dev scene.
10. **iPhone cost.** No extra realtime lights or shadow maps. Fill and rim are analytic in the hero shaders (≈10 ALU); globals set per preset; budget +0.2 ms GPU on iPhone 13 at most.

**Check:** run `character-lighting/tools/CharLightCaptureTests.cs.txt` (copy into a scratch clone as a PlayMode test); the metrics JSON must pass rules 3, 4, 7 and 8 on every shot.
