# GATE_RESULTS — Majestic weather (chat W)

Round 3 (10-18). Earlier rounds: `proof/GATE_RESULTS_round1.md`, `proof/GATE_RESULTS_round2.md`.
- **Machine:** the Mac M5 GPU in the Editor, 1920×1080, the game's own cameras, muted, through heavy.sh.
- **Final stills and readability:** `proof/final2/` (final code, all 18 slots, one run). Gate table: `proof/final2_gates.md`.
- **Sheets:** `proof/final2/sheets/all.jpg` (target · today · Majestic), `Wnn_sheet.jpg`, `Wnn_pair.jpg`.
- **Off-path proof:** `proof/r10/` (SSAO on) and `proof/r11/` (SSAO off). Table: `proof/offpath_final.md`.
- **Cost:** `proof/cost6/` (all 18), re-confirmed on the keyword build in `proof/r9/` (W01–W05).
- **Videos:** `proof/videos/` (18 clips) + `proof/r10/W03_thunderstorm.mp4` (sun shafts).

> **10-18 evening, phone bug fixes (section at the end):** the ball's dark rim and contact shade are removed, so READABILITY ball contrast is no longer ≥ 3:1 everywhere: W01 2.72, W05 2.48 and X16 2.82 at the iPhone tier. The table below is the round-3 measurement *with* the rim.

**Overall: WEATHER_COST, READABILITY, DETERMINISM, TENNIS_AROUND_PLAY, ASH_FAMILY_10_16 and VIDEOS PASS. TOGGLE_RESTORES: PASS at ≤ 2/255 in every golf view (SSAO off); tennis W12 is 3/255, under the method's own 4/255 floor but over 2/255. REF_MATCH open for Adnan.**

| Gate | Result | Evidence |
|---|---|---|
| WEATHER_COST Δ GPU ≤ 1.0 ms vs clear | **PASS 18/18** | cost6: +0.12…+0.92 ms (hole 16 Ashfall X16 +0.62, was +1.02 in round 1). Keyword build r9: W01 +0.88, W02 +0.23, W03 +0.08, W04 +0.19, W05 +0.27. Today's weather +0.00…+1.83. Method: 5 interleaved A/B rounds, pixel proxy (T2x − T1x)/3. The ball halo + contact shade (2 small quads) came after cost6 and were not timed alone. |
| READABILITY | **PASS** | **Ball ≥ 3:1: 15/15 counted views** (13 golf at address + 2 real tennis balls in play), lowest W02 3.38:1. **Corridor:** 0 px of fall layer and 0 near drops in the ball corridor, 18/18. **URP fog on ball/flag/players** ≤ 0.119, 18/18 (cap 0.15). |
| DETERMINISM | **PASS** | Pure rules; identical published globals on all 6 quality tiers; no `UnityEngine.Random` in the layer. |
| TOGGLE_RESTORES (runtime) | **PASS** | off → on → off returns the frame exactly (golf 0 px; tennis differs only on the animating players). |
| TOGGLE_RESTORES (off path, ≤ 2/255) | **PASS golf · tennis 3/255** | Layer off now compiles the original code (global keyword `MAJESTIC_WEATHER_ON`, off variant = the untouched source). Unpatched vs patched-off twins in one frozen frame, SSAO off: W01 max 1, W09 max 2, X16 max 1, W12 tennis max 3 (its twin-vs-twin swap floor is 4). Table below. |
| TENNIS_AROUND_PLAY (Adnan) | **PASS** | W12 / W14 with a ball in play: rain 0.70 / 1.00 → 0.000, no fall layer, 0 drops; the court stays wet. |
| ASH_FAMILY_10_16 (Adnan) | **PASS** | Hole 10 storm = Eruption, hole 16 rain = Ashfall. |
| MUTED VIDEO per effect | **PASS** | 18 clips + W03 shafts, 1280×720 H.264, no audio. |
| REF_MATCH | **OPEN, for Adnan** | `proof/final2/sheets/all.jpg` |

### READABILITY (proof/final2)

Ball contrast is the ball against the ring of ground around it; "today" is the same view with today's WeatherView. The W12–W16 rows without "ball" measure the far tennis player as a stand-in and are informational, not counted (the real ball rows are W12ball and W14ball).

| slot | ball contrast (today) | fall layer in corridor (px hit / px) | near drops in corridor | max drops | URP fog ball / flag | result |
|---|---:|---:|---:|---:|---:|---|
| W01 rain | 5.05:1 (1.29:1) | 0 / 21406 | 0 | 280 | 0.000 / 0.111 | PASS |
| W02 clearing | 3.38:1 (1.15:1) | 0 / 0 | 0 | 0 | 0.000 / 0.108 | PASS |
| W03 thunderstorm | 6.71:1 (1.60:1) | 0 / 44348 | 0 | 400 | 0.000 / 0.023 | PASS |
| W04 sea fog | 4.84:1 (1.48:1) | 0 / 0 | 0 | 0 | 0.000 / 0.118 | PASS |
| W05 gusty | 5.48:1 (1.01:1) | 0 / 0 | 0 | 338 | 0.000 / 0.110 | PASS |
| W06 snow | 8.33:1 (1.02:1) | 0 / 22016 | 0 | 100 | 0.000 / 0.113 | PASS |
| W07 blizzard | 7.33:1 (1.37:1) | 0 / 22016 | 0 | 172 | 0.000 / 0.113 | PASS |
| W08 freezing fog | 7.85:1 (1.07:1) | 0 / 0 | 0 | 0 | 0.000 / 0.119 | PASS |
| W09 ashfall | 9.56:1 (1.10:1) | 0 / 24871 | 0 | 59 | 0.000 / 0.109 | PASS |
| W10 eruption | n/a (ball off screen) | 0 / 4057 | 0 | 75 | 0.000 / 0.027 | PASS |
| W11 smoke | 6.55:1 (1.29:1) | 0 / 0 | 0 | 0 | 0.000 / 0.118 | PASS |
| W12ball tennis rain | 4.94:1 (1.18:1) | 0 / 0 | 0 | 0 | 0.000 / 0.000 | PASS |
| W14ball tennis storm | 6.40:1 (3.12:1) | 0 / 0 | 0 | 0 | 0.000 / 0.000 | PASS |
| X10 h10 eruption | 9.62:1 (1.20:1) | 0 / 27686 | 0 | 76 | 0.000 / 0.107 | PASS |
| X16 h16 ashfall | 11.01:1 (1.02:1) | 0 / 21111 | 0 | 65 | 0.000 / 0.111 | PASS |

Informational far-player rows (corridor and fog all clear): W12 1.16, W13 1.13, W14 2.34, W15 2.06, W16 1.02 (today 1.05–1.98).

### TOGGLE_RESTORES off path (proof/r10 SSAO on, proof/r11 SSAO off)

Three frames in one frozen frame: original-twin shaders, patched-twin shaders, live patched shaders, all with the layer off. "Swap floor" is what swapping materials changes on its own (draw order, coplanar edges).

| slot | SSAO | original vs patched twin (px / max) | swap floor: live vs patched twin | live patched vs original | result (≤ 2/255) |
|---|---|---:|---:|---:|---|
| W01 | off | 25 / 2 | 35 / 2 | 14 / 1 | PASS |
| W09 | off | 7 / 2 | 6 / 1 | 5 / 2 | PASS |
| X16 | off | 21 / 2 | 17 / 2 | 6 / 1 | PASS |
| W12 tennis | off | 53 / 4 | 219 / 4 | 204 / 3 | 3/255: under the 4/255 floor, over 2/255 |
| W04 | on | 0 / 0 | 1 / 1 | 1 / 1 | PASS |
| X16 | on | 22 / 3 | 31 / 3 | 17 / 3 | at floor |
| W01 | on | 210 / 78 | 67 / 2 | 198 / 78 | SSAO speckle |
| W09 | on | 32 / 6 | 31 / 2 | 16 / 6 | SSAO speckle |

With SSAO on, the outliers sit on objects no patch touches. SSAO samples depth in screen space, so a material swap changes its noise there; with SSAO off the same views are ≤ 2/255. The runtime toggle (no swap) is exact.

## What changed in round 3
- **Off path compiles the original code:** the shared patch adds `#pragma multi_compile_fragment _ MAJESTIC_WEATHER_ON` to 11 world shaders. MajesticWeather.hlsl is wrapped in `#if defined(MAJESTIC_WEATHER_ON)` with pass-through macros, so the off variant is the original source. The layer sets the global keyword only while it is active. Cost: double fragment variants for those 11 shaders.
- **Readability:**
  - the glow has a floor whenever weather is up;
  - a soft dark rim disc sits behind the ball, facing the camera (`MajesticWeatherHalo`);
  - a flat contact shade lies under the ball;
  - the flag glow is stronger.
- **Ref gaps:**
  - W03: storm sun shafts now read (golden rays, ZTest Always, hung at 85 / 45 m);
  - W04/W13: tree haze lifted above the bank;
  - W05: petals visible in a still.

## Open items
1. **REF_MATCH:** Adnan's eye.
2. **W10/W11 lava rivers:** not attempted (set dressing, chat 10's area).
3. **Tennis off path at 3/255:** the method's own floor in that view is 4/255, so ≤ 2/255 cannot be shown there with material swaps.
4. **Not covered by the in-material weather:** GolfPlants tee grass, URP Lit props and MajesticDressing get the capped URP fog only.
5. **Device timing:** NOT RUN (Editor proxy only).

## Ready for integration (chat 6)
- **New files** (installed in `Unity/`, untracked, hashes verified against `INSTALLED.sha1`; dormant until the patch is applied):
  `Scripts/Majestic/MajesticWeather.cs`, `MajesticWeatherRules.cs`, `MajesticWeatherFx.cs`, `MajesticWeatherGlow.cs` (+ .meta);
  `Resources/Majestic/MajesticWeather.hlsl`, `MajesticWeatherFall.shader`, `MajesticWeatherDrop.shader`, `MajesticWeatherSky.shader`,
  `MajesticWeatherReflect.shader`, `MajesticWeatherGlow.shader`, `MajesticWeatherHalo.shader` (+ .meta).
  Not installed on purpose: `Editor/MajesticWeatherShots.cs` (proof harness, clone-only).
- **Turn it on:** `python3 -I work/majestic-weather/tools/patch_shared.py apply Unity` (or `tools/install.sh --patch`).
  It edits EnvironmentSurface.hlsl, GolfRock, GolfBotanical, CoastalPine and GolfOcean. It adds the `MAJESTIC_WEATHER_ON` pragma to 11 world shaders, sends holes 10/16 to the ash family in `Weathers.SkyOf`, and writes the `MajesticWeatherHook.txt` marker.
  `check` exits 0 when fully applied, 1 when not applied, 2 when half-applied.
- **Rollback:** `patch_shared.py remove Unity` (byte-exact) and/or `tools/install.sh --remove` (removes the patch + exactly the files above).
- **Dry run 10-18 on today's `Unity/` sources:** apply → check all True → remove → 0 files differ from the originals.
- **Runtime off switch:** env `MAJESTIC=0` or `MAJESTIC_WEATHER=0`.
- **After apply:** Unity must recompile the 11 shaders (twice the fragment variants). Expect the first Editor/iOS build to take longer.
- **With chat 10's maps layer** (`tools/install_majestic.sh`):
  - **Files:** no file overlap. Chat 10 patches MajesticLook.cs, MajesticVenue.cs and GolfCoastalInstances.cs; this patch doesn't touch them.
  - **Sky:** chat 10 overrides `RenderedSky.Current.Look`. Weather only scales the `_RSky*` globals after RenderedSky writes them (LateUpdate, order 10003), and reads `_EnvironmentDepthLayers` without writing it. Depth-haze amount is kept by max(); its colour becomes the weather fog colour while weather is on.
  - **Not tested together yet:** weather was tuned without chat 10's round 1–15 layer. Check holes 22 and 16 (W09, X16) for double darkening from AshOvercast plus the ash weather.

## Phone bug fixes (10-18 evening, from Adnan's phone build)
Repro and proof were captured in a copy of the integration project (weather patch + maps layer) at the iPhone quality level ("Medium": 1 shadow cascade, 20 m) with `MW_QUALITY=2`. Before: `proof/bug_before/`. After: `proof/bug_after/`. Sheets: `ball_before_after.jpg` and `gusty_before_after.jpg`.

1. **"Ball has a weird shadow around it."**
   - **Root cause:** `MajesticWeatherHalo`, the round-3 readability aid. It drew a soft dark disc behind the ball facing the camera, plus a second one lying under the ball; they showed in every weather, and as a reddish smear on the ash holes.
   - **Fix:** both are removed (`MajesticWeatherGlow.cs`), and `MajesticWeatherHalo.shader` is deleted. The ball keeps only its own additive glow.
   - **After:** no smudge in W01, W05 or X16.
   - **Cost:** ball contrast at the iPhone tier is now 2.72 (W01), 2.48 (W05) and 2.82 (X16), against 1.30, 1.31 and 1.18 with today's weather. The 3:1 gate fails in these views. Adnan's eye wins over the metric; a bright rim would need his OK.
2. **"Flowers going through the air … insane shadows going everywhere"** (gusty, hole 20).
   - **Not real shadows:** no weather or maps renderer casts shadows. All weather renderers have shadow casting off and no ShadowCaster pass, and chat 10's scatter is `ShadowCastingMode.Off`.
   - **Root cause:** the gusty look's in-material wind effects.
     - Cloud shadows were hard-edged (smoothstep .50–.56), about 50 m across, at strength .55, racing at up to 20 m/s.
     - Grass waves darkened and brightened the turf by up to +100 %, in stripes 12 m apart moving at about 12 m/s.
     - Since the round-2 strengthening for W05, this happened exactly while the petals fly.
   - **Fix** (`MajesticWeather.hlsl` and the gusty values in `MajesticWeatherRules.cs`):
     - cloud shadows are now about 110 m soft patches at 2–8 m/s, strength .28;
     - grass waves are a sheen only (+35 % max, never darker than −5 %), about 18 m apart at 4–9 m/s, strength 1.2.
   - **Gate** (`tools/flicker.py`, fairway region, golfer masked):

     | clip | fairway pixels changing > 12/255 per 0.1 s |
     |---|---|
     | before | 10.3 % (peak 24.4 %) |
     | after | 0.5 % (peak 2.2 %) |
     | rain reference | 2.1 % |
     | gusty in round 1 | 1.8 % |

     **PASS.**

Installed in `Unity/`, dormant (`INSTALLED.sha1` refreshed). The integration project needs the same three files re-copied and the Halo shader deleted.

## Ball outline (10-18 night, Adnan's direction)
Adnan asked for "an extremely subtle outlining, maybe more so a happy outlining ... like a heat seeking missile outline / asteroid outline like flames". The new `MajesticWeatherComet` (shader + C#) is additive warm light only, never dark:
- a hair-thin hot line round the ball's silhouette, with a soft flame glow licking outward (away from the motion; upward at rest);
- a flame trail that only appears above ~5 m/s and is full at 14 m/s;
- strength runs from barely there in clear sun up to its full value in rain, fog and ash (MajesticWeatherGlow.Darkness);
- cost: 2 tiny meshes per ball (16x10 shell + 4-vertex ribbon).

Three variants went to Adnan (`proof/rim3/`: `rim_variants.jpg`, `rim_moving_zoom.jpg`, `W01_rim{A,B,C}_move.mp4`). **Adnan picked A (ember)**, now the default. B and C stay in code; set them with env `MAJESTIC_BALL_RIM`.

Ball contrast at the iPhone tier (Medium) with A:

| view | with A | no rim | gate |
|---|---:|---:|---|
| X16 ash | 4.16:1 | — | **PASS**, no smear |
| W01 rain | 2.60:1 | 2.72:1 | below 3:1 |
| W05 gusty | 2.01:1 | 2.48:1 | below 3:1 |

**The rain and gusty values are a known, accepted limit (coordinator, relaying Adnan).** The metric averages the whole ball patch, and an outline adds edge pixels dimmer than the white ball. Reaching 3:1 there would need a brighter ball glow, which Adnan did not ask for. The ball glow is unchanged.

**Combined build (chat 12, 10-18 night, `work/integration-1018/weather*/`):** ball contrast was golf W01 2.51, W03 3.63, W09 2.84, X16 2.72; tennis W12ball 1.54 (round 3 with the dark rim: 4.94), W14ball 2.88 (6.40). Corridor and fog PASS everywhere.

**Weak spot:** the tennis ball in resort rain (W12), a yellow ball on a bright wet court and sea. The dark rim was what had carried it to 4.9:1. The ember outline also shows at rest (only the trail needs speed), but at the default strength it's too faint to lift that view.

**Possible follow-up, needs Adnan's OK:** a tennis-only stronger ember floor (warm, not dark). Not done tonight.

## Tennis ball: stronger warm ring (10-18 night, Adnan: "strengthen the tennis ball's warm outline for rain")
This applies to the tennis ball only. Golf and the ball glow are unchanged.
- **Settings:** `MajesticWeatherComet` puts a strength floor on the tennis ball (2.2 in weather, 0.45 in clear sun) and draws a crisp ring in deeper gold (1, .82, .45), starting at 0.8 radii. It is still additive light, never dark.
- **Choice:** this was ring 3 of six settings filmed at the iPhone tier (`proof/tennis_boost2/`, `proof/tennis_boost3/tennis_ring_compare.jpg`). The variants that filled the ball itself white washed out the ring.
- **Proof:** clip `proof/tennis_boost3/W12_rim_tennis.mp4`.
- **Off switch for A/B tests:** `MAJESTIC_TENNIS_EMBER=0`.

Ball contrast, ball plus outline vs what's behind it:

| view | before | ring 3 | gate |
|---|---:|---:|---|
| W12 resort rain | 1.65:1 | 1.64:1 | **target ≥ 2.0 not met** |
| W14 storm | 4.62:1 | 4.64:1 | PASS |

The integration chat's measure (the ball's own renderers only, so the outline counts as background) gives W12 1.53.

**Why W12 can't reach 2.0 with warm light:** the ball is already near-white (linear L ≈ 0.60) in front of a pale stone wall (L ≈ 0.35). An all-white ball patch would top out around 2.6:1, and the anti-aliased edge pixels pull the average down. Gold sits at about the wall's luminance, so the ring separates the ball by colour, which this luminance metric does not see. Getting 2:1 in luminance would need a darker edge (rejected by Adnan) or a darker wall behind the ball (map, not weather).
