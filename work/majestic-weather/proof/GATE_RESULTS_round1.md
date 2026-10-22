# GATE_RESULTS — Majestic weather (chat W, 2026-10-17)

Run: `proof/final/` (21:50, `~/majestic-weather-UnityClone`, muted, Editor on the Mac M5 GPU, 1920×1080, pipeline MSAA). Every
slot is the game's own address / shoulder camera at the ref's hole or venue. Videos are from round 5 (`proof/videos/`, the look
before the last eruption/gust tweaks). The machine was shared with other chats' Unity/Blender jobs throughout, so the timings
carry noise of about ±0.3 ms; the gate uses chat 9's pixel proxy (interleaved A/B, (T2x − T1x)/3), with the FTM column for
reference.

**Overall: FAIL.** 4 of 7 gates PASS. WEATHER_COST fails on one view by 0.02 ms (17/18). READABILITY fails only its ball/flag
contrast line, which today's weather fails too. TOGGLE_RESTORES fails because the shader off-path proof is not valid.
REF_MATCH is Adnan's call.

| Gate | Result | Evidence |
|---|---|---|
| REF_MATCH (16 refs + holes 10/16) | **OPEN — for Adnan** | `proof/final/sheets/all.jpg` (target · today · Majestic), per ref `Wnn_sheet.jpg` and `Wnn_pair.jpg` (target next to the 1080p frame); stills `proof/final/Wnn_majestic.jpg` / `_legacy.jpg` / `_clear.jpg` |
| WEATHER_COST Δ GPU ≤ 1.0 ms vs clear | **FAIL 17/18** (X16 hole-16 ashfall +1.02 ms) | table below; every other view +0.09…+0.94 ms (three tennis views read below clear: noise). Today's weather: +0.11…+1.80 ms at the same cameras |
| READABILITY | **FAIL** (contrast line only) | corridor PASS 18/18 (no near drop in the ball corridor over 60 frames, fall layer 0 px changed inside it); ball/flag/player URP fog ≤ 0.119 everywhere (cap 0.15) PASS 18/18; **ball/flag contrast ≥ 3:1 FAIL in 17/18 views. It fails for today's weather too** (Majestic ≥ today in 14 of 17). The golf ball at address reads L ≈ 0.07–0.23, a lit-ball/hero-lighting matter, not the weather |
| DETERMINISM | **PASS** | pure rules (13 looks × 3 families × golf/tennis, gusts from seed + shared clock, tennis play-window truth table, visibility = `DreamConditions.Visibility`, `WeatherFor` per seed) + every slot's published globals identical across all 6 quality tiers (round 5: 17/17 slots, 1 distinct each); no `UnityEngine.Random` in the layer |
| TOGGLE_RESTORES | **FAIL (unproven off-path)** | runtime: layer off → on → off gives back **exactly** the frame (golf W01: 0 px; tennis W12: only the two animating players differ, time frozen). The off-path proof (patched shaders with the layer off vs the original shaders) is **not valid as run**: reimporting shaders in Play mode broke unrelated runtime materials (yellow trees, golf). The tennis venue reads 690 px, inside its 1,206 px player-animation noise floor. By code: every hook is `if(_MajWeatherOn>.5h)` or `== MixFog` when off, and `MAJESTIC=0` never sets the global. A clean proof is a separate unpatched-clone render |
| TENNIS_AROUND_PLAY (Adnan's decision) | **PASS** | W12 + W14: ball put in play → rain 0.70/1.00 → 0.000, fall layer off, 0 drops, court stays wet; frames `proof/final/W12_rally_hold.jpg`, video `proof/videos/W12_rain.mp4` |
| ASH_FAMILY_10_16 (Adnan's decision) | **PASS** | X10: hole 10 storm = "Eruption", X16: hole 16 rain = "Ashfall" (`proof/final/run.log`) |
| MUTED VIDEO per effect | **PASS** | `proof/videos/`: 18 clips, 5–7 s, 1280×720 H.264, no audio track |

### WEATHER_COST (pixel GPU at 1080p, interleaved A/B, ms)

| slot | clear | Majestic | Δ Majestic | today (legacy) | Δ today | FTM Δ Majestic | result |
|---|---:|---:|---:|---:|---:|---:|---|
| W01 | 3.00 | 3.88 | **+0.88** | 4.80 | +1.80 | +1.11 | PASS |
| W02 | 3.17 | 3.12 | **-0.04** | 4.14 | +0.97 | +1.29 | PASS |
| W03 | 3.47 | 4.36 | **+0.89** | 4.51 | +1.04 | +2.11 | PASS |
| W04 | 3.43 | 4.08 | **+0.65** | 4.67 | +1.24 | +0.41 | PASS |
| W05 | 3.53 | 4.07 | **+0.54** | 3.78 | +0.25 | +2.68 | PASS |
| W06 | 3.63 | 4.33 | **+0.70** | 4.81 | +1.18 | +1.49 | PASS |
| W07 | 3.64 | 4.45 | **+0.80** | 4.77 | +1.13 | +1.94 | PASS |
| W08 | 3.48 | 4.38 | **+0.89** | 4.21 | +0.72 | +1.53 | PASS |
| W09 | 3.64 | 4.57 | **+0.94** | 4.87 | +1.23 | +1.35 | PASS |
| W10 | 3.63 | 4.53 | **+0.89** | 4.90 | +1.26 | +1.79 | PASS |
| W11 | 3.65 | 4.41 | **+0.77** | 4.38 | +0.73 | +0.89 | PASS |
| W12 | 3.00 | 2.92 | **-0.07** | 4.05 | +1.05 | +2.15 | PASS |
| W13 | 2.93 | 3.32 | **+0.39** | 4.33 | +1.40 | +4.18 | PASS |
| W14 | 3.13 | 2.44 | **-0.70** | 4.36 | +1.23 | +6.96 | PASS |
| W15 | 3.18 | 3.27 | **+0.09** | 2.47 | -0.72 | +1.74 | PASS |
| W16 | 3.36 | 4.01 | **+0.65** | 3.47 | +0.11 | +3.63 | PASS |
| X10 | 3.44 | 4.34 | **+0.90** | 4.76 | +1.32 | +0.85 | PASS |
| X16 | 3.49 | 4.51 | **+1.02** | 4.76 | +1.27 | +1.11 | FAIL |

WEATHER_COST: FAIL (17/18)

### READABILITY


## What the layer does now (vs today, see sheets)
- **No more full-screen veils.** WeatherView's 3 volumes and 5 particle systems are off while the layer is on; weather lives in the world materials.
- **Rain / storm:**
  - wet turf, deeper colour, a sky sheen;
  - puddles mirror the rendered sky (treeline band, muddy bottom, damp rims, raindrop rings near the camera, sharp sun glints);
  - darker overcast deck, storm wall on the horizon, lightning light;
  - 2-layer camera rain plus ≤ 400 near streaks, never in the ball corridor.
- **Tennis wet court:**
  - a screen-space mirror of players, net, lamps and city lights (only while the court is wet);
  - weather runs on arrival, between games and after the match, never during a rally.
- **Rain clearing:** rainbow + secondary bow, sunbeams, last drops; the ground dries edges first, puddles last.
- **Sea fog / freezing fog:**
  - the bank lies on the ground; trees and landmarks rise out of it (gameplay visibility of the ground unchanged);
  - frost sparkle and ice puddles in freezing fog.
- **Snow / blizzard:** snow settles on up-facing ground, pines and rocks (lightly on the line of play); flakes; ice puddles.
- **Ash family:**
  - ash on rock, not turf; glowing lava puddles with cracking crust off the line of play;
  - warm smoky sky with lava underglow;
  - eruption flash and lava bombs;
  - holes 10 and 16 included.
- **Gusty:** cloud shadows racing (~50 m patches), grass gust waves, petals/leaves (embers on ash holes), stronger sway on grass, trees, flags, bunting and sails (`_GolfWind` scaled; `_WindDir/_WindStrength/_Gust` published).

## Open items
1. **REF_MATCH (Adnan).** Closest refs: W01, W02, W06, W07, W09, W12, W14.
   - **Still behind:**
     - W03: the ref's warm sun shafts;
     - W04/W13: tall trees still slightly hazed;
     - W05: gusts read in motion, little in a still;
     - W10/W11: no glowing lava rivers / orange sky like the AI images.
   - **Owned by other chats:** lava rivers, landmarks and umbrellas are set dressing.
   - Lightning bolt shape is WeatherView's.
2. **X16 cost +1.02 ms.** Re-measure on a quiet machine before cutting further. Next cut if needed: ash fall layer 1 layer near the green.
3. **Ball contrast.** The game-wide ball/hero lighting at address is below 3:1 even in today's weather. Not weather-owned.
4. **TOGGLE off-path.** Prove with two clones (patched vs unpatched, layer off) in Edit-mode renders, not by reimporting in Play mode.
5. **Not covered by the in-material weather:**
   - URP Lit props;
   - GolfPlants tee grass cards;
   - MajesticDressing.

   They get only the capped URP fog. Wet/snow on them needs their shaders hooked (chat 9 / golf track).
6. **Tennis lightning timing** comes from WeatherView's own random clock (cosmetic, not seeded). It is held during rallies.
7. **Device numbers NOT RUN** (Editor proxy only).
