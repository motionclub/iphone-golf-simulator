# GATE_RESULTS — Majestic weather (chat W)

Round 2 (10-18). Round 1 (10-17) is kept in `proof/GATE_RESULTS_round1.md`.
- **Machine:** the Mac M5 GPU in the Editor, 1920×1080, the game's own cameras, muted, through heavy.sh.
- **Cost run** (`proof/cost6/`, 06:00–06:30): the machine never went idle overnight, so this run queued after 90 minutes. While it ran, no other Unity job ran, though a character chat's Blender job may have (`proof/cost6.condition`).
- **Off-path proof:** `proof/r7/`.
- **Stills and sheets:** `proof/r8/`.
- **Videos:** `proof/videos/` (rounds 5–8).

**Overall: 6 PASS · 1 FAIL (READABILITY contrast, 9/15 views) · REF_MATCH open for Adnan.**

| Gate | Result | Evidence |
|---|---|---|
| WEATHER_COST Δ GPU ≤ 1.0 ms vs clear | **PASS 18/18** | Majestic adds +0.12…+0.92 ms over clear; hole 16 ashfall +0.62 (was +1.02). Today's weather: +0.02…+1.83 ms. Method: 5 interleaved A/B rounds, pixel proxy (T2x − T1x)/3. Table below. |
| READABILITY | **FAIL** (contrast only) | **Corridor:** 18/18 views; 0 near drops in the ball corridor and the fall layer never draws there. **Fog on ball/flag/players:** ≤ 0.119 in 18/18 (cap 0.15). **Ball contrast ≥ 3:1: 9/15 views**, details below. |
| DETERMINISM | **PASS** | Pure rules, plus identical published globals on all 6 quality tiers in every slot checked. No `UnityEngine.Random` in the layer. |
| TOGGLE_RESTORES | **PASS** | **Runtime:** off → on → off gives back the frame exactly (golf 0 px; tennis differs only on the animating players). **Shaders:** with the layer off, the patched shaders equal the originals in 18/18 views (method and tolerance below). |
| TENNIS_AROUND_PLAY (Adnan) | **PASS** | W12 and W14: a ball in play takes rain 0.70/1.00 → 0.000, with no fall layer and no drops; the court stays wet. |
| ASH_FAMILY_10_16 (Adnan) | **PASS** | Hole 10 storm = "Eruption", hole 16 rain = "Ashfall". |
| MUTED VIDEO per effect | **PASS** | `proof/videos/`: 18 clips (round 5) + 5 newer (W03, W04, W05, W10, W12), 1280×720 H.264, no audio. |
| REF_MATCH | **OPEN, for Adnan** | `proof/r8/sheets/all.jpg` (target · today · Majestic), `Wnn_pair.jpg` |

**Ball contrast ≥ 3:1, the 15 views counted:**
- **Counted:** 13 golf views (the golf ball at address) + 2 tennis views (the real tennis ball, in play).
- **PASS (9):** W03, W06, W07, W09, W10, W11, X10, X16 and the W14 tennis ball.
- **FAIL (6):** W01 2.87, W02 1.93, W04 2.79, W05 2.39, W08 2.90, W12 tennis ball 1.64.
- **Today's weather at the same views:** 1.0–1.6 (tennis ball 1.2–3.3).
- **Not counted:** the far tennis player rows in the table are informational only.

**Off-path method:**
- Every patched world shader has an unpatched twin compiled beside it (`tools/make_orig.py`).
- The harness switches materials to the twins inside one frozen frame: no reimport and no second run.
- Pixels that change between two renders of the patched frame are excluded as noise.
- Every view stays within compiler rounding: ≤ 0.31 % of pixels differ, and ≤ 0.002 % by more than 8/255 (tolerance 0.05 %).
- Diff images: `proof/r7/*_offpath_diff.png` (×20).

### WEATHER_COST (pixel GPU at 1080p, interleaved A/B, ms)

| slot | clear | Majestic | Δ Majestic | today (legacy) | Δ today | FTM Δ Majestic | result |
|---|---:|---:|---:|---:|---:|---:|---|
| W01 | 3.24 | 3.71 | **+0.47** | 4.50 | +1.26 | +0.70 | PASS |
| W02 | 2.88 | 3.00 | **+0.12** | 3.45 | +0.56 | +0.62 | PASS |
| W03 | 3.32 | 3.57 | **+0.26** | 3.83 | +0.52 | +1.10 | PASS |
| W04 | 2.98 | 3.30 | **+0.32** | 4.82 | +1.83 | -0.28 | PASS |
| W05 | 3.74 | 4.23 | **+0.49** | 3.96 | +0.23 | +1.23 | PASS |
| W06 | 3.88 | 4.68 | **+0.80** | 5.10 | +1.22 | +0.72 | PASS |
| W07 | 3.82 | 4.43 | **+0.61** | 4.95 | +1.13 | +0.85 | PASS |
| W08 | 3.73 | 4.42 | **+0.68** | 4.41 | +0.68 | +1.56 | PASS |
| W09 | 3.57 | 4.42 | **+0.85** | 5.13 | +1.55 | -0.09 | PASS |
| W10 | 3.59 | 4.51 | **+0.92** | 5.01 | +1.42 | +0.86 | PASS |
| W11 | 3.69 | 4.47 | **+0.78** | 4.35 | +0.66 | +1.89 | PASS |
| W12 | 2.90 | 3.45 | **+0.55** | 4.10 | +1.20 | +1.88 | PASS |
| W13 | 2.85 | 3.67 | **+0.81** | 4.00 | +1.15 | +0.57 | PASS |
| W14 | 2.82 | 3.43 | **+0.61** | 4.36 | +1.53 | -0.48 | PASS |
| W15 | 3.21 | 3.75 | **+0.55** | 3.23 | +0.02 | +2.63 | PASS |
| W16 | 3.12 | 3.61 | **+0.49** | 3.58 | +0.46 | -0.22 | PASS |
| X10 | 3.58 | 4.44 | **+0.86** | 4.88 | +1.30 | +0.11 | PASS |
| X16 | 3.64 | 4.25 | **+0.62** | 4.93 | +1.30 | +0.92 | PASS |

WEATHER_COST: PASS (18/18)

### READABILITY (proof/cost6, final glow)

| slot | ball contrast (today) | flag contrast (today) | fall layer in corridor (px hit / px) | near drops in corridor | max drops | URP fog ball / flag | result |
|---|---:|---:|---:|---:|---:|---:|---|
| W01 | 2.87:1 (1.29:1) | n/a (n/a) | 0 / 21406 | 0 | 280 | 0.000 / 0.111 | FAIL |
| W02 | 1.93:1 (1.13:1) | n/a (n/a) | 0 / 0 | 0 | 0 | 0.000 / 0.108 | FAIL |
| W03 | 4.19:1 (1.60:1) | n/a (n/a) | 0 / 44348 | 0 | 397 | 0.000 / 0.023 | PASS |
| W04 | 2.79:1 (1.47:1) | n/a (n/a) | 0 / 0 | 0 | 0 | 0.000 / 0.118 | FAIL |
| W05 | 2.39:1 (1.00:1) | n/a (n/a) | 0 / 0 | 0 | 294 | 0.000 / 0.110 | FAIL |
| W06 | 3.15:1 (1.01:1) | n/a (n/a) | 0 / 22016 | 0 | 97 | 0.000 / 0.113 | PASS |
| W07 | 3.29:1 (1.37:1) | n/a (n/a) | 0 / 22016 | 0 | 169 | 0.000 / 0.113 | PASS |
| W08 | 2.90:1 (1.07:1) | n/a (n/a) | 0 / 0 | 0 | 0 | 0.000 / 0.119 | FAIL |
| W09 | 4.87:1 (1.09:1) | n/a (n/a) | 0 / 24871 | 0 | 55 | 0.000 / 0.109 | PASS |
| W10 | n/a (n/a) | n/a (n/a) | 0 / 4057 | 0 | 67 | 0.000 / 0.027 | PASS |
| W11 | 3.61:1 (1.30:1) | n/a (n/a) | 0 / 0 | 0 | 0 | 0.000 / 0.118 | PASS |
| W12 | 1.25:1 (1.19:1) | 1.18:1 (1.01:1) | 0 / 0 | 0 | 280 | 0.000 / 0.000 | FAIL |
| W12ball | 1.64:1 (1.18:1) | n/a (n/a) | 0 / 0 | 0 | 0 | 0.000 / 0.000 | FAIL |
| W13 | 1.06:1 (1.06:1) | 1.11:1 (1.11:1) | 0 / 0 | 0 | 0 | 0.000 / 0.000 | FAIL |
| W14 | 2.39:1 (1.73:1) | 1.15:1 (1.19:1) | 0 / 0 | 0 | 400 | 0.000 / 0.000 | FAIL |
| W14ball | 4.82:1 (3.25:1) | n/a (n/a) | 0 / 0 | 0 | 0 | 0.000 / 0.000 | PASS |
| W15 | 1.97:1 (1.94:1) | 1.17:1 (1.08:1) | 0 / 0 | 0 | 199 | 0.000 / 0.000 | FAIL |
| W16 | 1.04:1 (1.56:1) | 1.77:1 (1.51:1) | 0 / 0 | 0 | 0 | 0.000 / 0.000 | FAIL |
| X10 | 6.15:1 (1.20:1) | n/a (n/a) | 0 / 27686 | 0 | 68 | 0.000 / 0.107 | PASS |
| X16 | 4.31:1 (1.01:1) | n/a (n/a) | 0 / 21111 | 0 | 54 | 0.000 / 0.111 | PASS |

### OFF PATH (proof/r7)

| slot | materials / patched shaders | stable px | differing px (any) | > 8/255 px | max | result |
|---|---:|---:|---:|---:|---:|---|
| W01 | 20 / 4 | 2073600 | 4274 (0.21%) | 0 | 5 | PASS |
| W02 | 17 / 3 | 2073600 | 2338 (0.11%) | 23 | 70 | PASS |
| W03 | 17 / 4 | 2073583 | 6371 (0.31%) | 0 | 7 | PASS |
| W04 | 20 / 4 | 2073583 | 6402 (0.31%) | 1 | 52 | PASS |
| W05 | 32 / 4 | 2073509 | 5799 (0.28%) | 0 | 8 | PASS |
| W06 | 19 / 4 | 2073559 | 1204 (0.06%) | 0 | 3 | PASS |
| W07 | 19 / 4 | 2073482 | 669 (0.03%) | 0 | 2 | PASS |
| W08 | 19 / 4 | 2073575 | 6503 (0.31%) | 0 | 5 | PASS |
| W09 | 18 / 4 | 2073548 | 3456 (0.17%) | 24 | 18 | PASS |
| W10 | 18 / 4 | 2073574 | 1042 (0.05%) | 0 | 5 | PASS |
| W11 | 18 / 4 | 2073585 | 4048 (0.20%) | 0 | 4 | PASS |
| W12 | 44 / 4 | 2058968 | 512 (0.02%) | 2 | 129 | PASS |
| W13 | 44 / 4 | 2073400 | 129 (0.01%) | 8 | 34 | PASS |
| W14 | 17 / 3 | 2073343 | 112 (0.01%) | 9 | 34 | PASS |
| W15 | 17 / 3 | 2073597 | 254 (0.01%) | 9 | 74 | PASS |
| W16 | 20 / 2 | 2071630 | 167 (0.01%) | 6 | 44 | PASS |
| X10 | 13 / 4 | 2073586 | 3910 (0.19%) | 34 | 23 | PASS |
| X16 | 21 / 5 | 2073570 | 1985 (0.10%) | 0 | 8 | PASS |

OFF_PATH: 18/18 PASS (tolerance: ≤ 0.05 % of pixels off by more than 8/255 — shader-compiler rounding; diff images `proof/r7/*_offpath_diff.png`, ×20 amplified)

## What changed in round 2 (10-18)
**Cost (hole 16 under 1.0 ms):**
- ash falls as one procedural layer;
- near ash: about half the flakes, larger;
- lava puddles only within ~60 m of the camera;
- lighter cover noise;
- no storm deck in ashfall;
- the tennis mirror marches 10 steps (was 16) with 3 colour taps (was 5).

**Readability (`MajesticWeatherGlow`):**
- a soft additive self-light on the ball (golf and tennis) and the flag, drawn on their own meshes;
- strength follows how much the weather takes away (cloud, fog, darker sky, falling precipitation, cover), with a floor;
- nothing in clear weather.

**Ref gaps:**
- **W04/W13:** the sea-fog bank thins within ~8 m of the ground, so trees and landmarks stand clear.
- **W05:** petals are bigger and more numerous, with stronger grass gust waves and cloud shadows. They read in a still; the video shows them racing.
- **W03:** a golden storm sun, and sun shafts hung in front of the near hills. These read only weakly at this camera, which sees little sky.
- **W10/W11 lava rivers:** not attempted (set dressing).

## Open items
1. **REF_MATCH:** Adnan's eye.
2. **Ball contrast below 3:1 in 6 views:**
   - W02 rain clearing and W05 gusty are sunny scenes, so the glow is light;
   - W01, W04 and W08 sit at 2.8–2.9 against bright wet turf;
   - W12's tennis ball is seen against the bright sea and sky.

   Next step if wanted: a light dark rim under the ball (contact shade), or game-wide ball lighting at address. Today's clear weather is also below 3:1 at the address camera.
3. **Shaders not covered by the in-material weather:**
   - GolfPlants tee grass;
   - URP Lit props;
   - MajesticDressing.

   They get only the capped URP fog.
4. **Device timing:** NOT RUN (Editor proxy only).
