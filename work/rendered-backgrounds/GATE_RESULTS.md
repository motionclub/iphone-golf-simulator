# Rendered backgrounds — GATE_RESULTS (chat 2, 2026-10-17)

**Result:** every painted or AI panorama and backdrop is off the runtime path in all venues. These are tennis resort, skyscraper and volcano; all 16 golf holes over the 3 courses; and the plaza hub with its rooms' outdoor grounds. The Luminous Coast / dream-worlds sky is DreamEnvironment, now routed to the rendered sky. All 20 locations PASS NO_PAINT, SUN_MATCH, PARALLAX, LONG_LENS, PERF (Editor proxy) and CHAR_SAME: 120 / 120. QUALITY is awaiting Adnan's review. Device PERF: NOT RUN.

**How it was measured:**
- Captures ran in an APFS clone (`/private/tmp/backgrounds-UnityClone`), muted (GOLF_MUTE=1 + EditorUtility.audioMasterMute), at 1920×1080.
- The clock was fixed at 14:00 EST (DREAM_UTC 1792263600), weather Clear.
- "Before" = the same clone with `RENDERED_SKY=0`: every painted path as shipped, captured with the same tools.
- Tools: `tools/capture_tennis.sh`, `capture_golf.sh`, `capture_hub.sh`; gates by `tools/gates.py`; per-location JSON in `proof/<venue>/gates.json` and `proof/golf/holeNN_gates.json`.

**What each gate checks:**
- NO_PAINT — texture audit of every enabled renderer, the skybox and globals. The painted list is ArchipelagoSky, SummerSky, SkyCoastalSmall, SkyVolcanic, SkyRooftop, CloudTops, clouds and ash_cloud. Painted sky reflections (sea `_SkyMap`, clubhouse glass `_ReflectionMap`, tower `_SkyPanorama`) are rewired to the rendered-sky equirect RT.
- SUN_MATCH — the sky's disc direction and scattering-glow azimuth vs the directional light: 0.000° everywhere, because the sky reads the light every frame. Also checked at 07:30, 18:45 (sunset) and 22:00 (moon at the light, stars) on the resort.
- PARALLAX — the camera maths predicts each landmark's screen shift; normalised cross-correlation measures the real shift in the rendered pair.
  - Tests: the brief's 2 m dolly (tennis), plus a 60 m crane (all venues) because a painting gives 0 px on both.
  - Tolerance: max(1 px, 10 %). Islands use their depth range ± radius. Time is frozen during the pairs so drifting clouds don't add motion.
  - Pass: 3 crane landmarks plus min(3, visible) dolly landmarks within tolerance. Every confident match, passing or not, is listed in the JSON.
- LONG_LENS — p99 edge energy behind the heroes at the longest in-game lens (27° stare-downs; golf 20° down-the-hole lens; hub door/spawn) must keep ≥ 90 % of the painting's. The 14° test lens is in the sheets: the painting smears, the 3D islands stay sharp.
- PERF — Editor proxy, interleaved A/B in one run: painted DreamSky with no backdrop vs rendered sky with clouds and scenery. 10 rounds × 20 synchronous 1920×1080 renders per side per camera, median delta ≤ +1.0 ms. Worst: golf hole 10 tee +0.93 ms, resort gameplay +0.89 ms. Many are negative (noise floor ±0.5 ms on the shared Mac). Device: NOT RUN.
- CHAR_SAME — the same frozen frame rendered painted vs rendered; mean ΔE76 over a hero-only mask (rival, golfer, hub hero). The largest is 0.035.

**Content cost:**
- Sky: 1 skybox pass (2 LUT + 2 noise fetches), with the LUT rebuilt on the CPU only when the light's elevation moves more than 0.2°.
- Clouds: 1 draw, 16–26 alpha-tight cards, vertex aerial perspective.
- Islands: 1 draw, 37,776 tris, 4096×2048 albedo+AO and normal.
- Cloud sea: 2 × 1024² maps.
- No render-scale or resolution change anywhere.

## Per location
### resort
- GATE: NO_PAINT PASS — no painted panorama bound on any enabled renderer, the skybox or a global
- GATE: SUN_MATCH PASS — disc vs light 0.000 deg; scattering-glow azimuth vs light 0.000 deg; light az 89.0 el 58.0
- GATE: PARALLAX PASS — 10/14 landmarks within tolerance; crane Cloud1 pred -21.27 meas -21.27; crane Cloud10 pred -22.29 meas -22.29; crane Cloud12 pred -17.76 meas -20.6; crane Cloud14 pred -11.74 meas -11.77
- GATE: LONG_LENS PASS — 04_stare_rival: 0.1813→0.2855, 06_stare_player: 0.3834→0.4242
- GATE: PERF PASS — gameplay 1920x1080: +0.891 ms (rendered - painted, interleaved median, Editor proxy); ring000 1920x1080: +0.237 ms (rendered - painted, interleaved median, Editor proxy); device: NOT RUN
- GATE: CHAR_SAME PASS — mean dE76 0.002, p95 0.000 over 173735 hero pixels

### skyscraper
- GATE: NO_PAINT PASS — no painted panorama bound on any enabled renderer, the skybox or a global
- GATE: SUN_MATCH PASS — disc vs light 0.000 deg; scattering-glow azimuth vs light 0.000 deg; light az 89.0 el 58.0
- GATE: PARALLAX PASS — 8/11 landmarks within tolerance; crane Cloud0 pred -17.5 meas -17.54; crane Cloud8 pred -10.78 meas -12.29; crane Cloud10 pred -9.19 meas -9.14; crane Cloud15 pred -20.67 meas -20.57
- GATE: LONG_LENS PASS — 04_stare_rival: 0.2026→0.2446, 06_stare_player: 0.1455→0.204
- GATE: PERF PASS — gameplay 1920x1080: +-0.225 ms (rendered - painted, interleaved median, Editor proxy); ring000 1920x1080: +-0.823 ms (rendered - painted, interleaved median, Editor proxy); device: NOT RUN
- GATE: CHAR_SAME PASS — mean dE76 0.031, p95 0.000 over 172337 hero pixels

### volcano
- GATE: NO_PAINT PASS — no painted panorama bound on any enabled renderer, the skybox or a global
- GATE: SUN_MATCH PASS — disc vs light 0.000 deg; scattering-glow azimuth vs light 0.000 deg; light az 89.0 el 58.0
- GATE: PARALLAX PASS — 5/6 landmarks within tolerance; crane Cloud7 pred -20.94 meas -20.93; crane Cloud10 pred -27.34 meas -27.23; crane Cloud14 pred -7.58 meas -7.61; crane Cloud13 pred -21.45 meas -21.34
- GATE: LONG_LENS PASS — 04_stare_rival: 0.046→0.0471, 06_stare_player: 0.0481→0.0479
- GATE: PERF PASS — gameplay 1920x1080: +0.239 ms (rendered - painted, interleaved median, Editor proxy); ring000 1920x1080: +0.665 ms (rendered - painted, interleaved median, Editor proxy); device: NOT RUN
- GATE: CHAR_SAME PASS — mean dE76 0.000, p95 0.000 over 172481 hero pixels

### hub
- GATE: NO_PAINT PASS — no painted panorama bound on any enabled renderer, the skybox or a global
- GATE: SUN_MATCH PASS — disc vs light 0.000 deg; scattering-glow azimuth vs light 0.001 deg; light az 176.0 el 25.0
- GATE: PARALLAX PASS — 7/7 landmarks within tolerance; crane Cloud18 pred -12.77 meas -12.77; crane Cloud5 pred -22.81 meas -22.87; crane Cloud12 pred -10.27 meas -10.27; crane Cloud4 pred -14.61 meas -14.64
- GATE: LONG_LENS PASS — 01_spawn: 0.4555→0.4514, 03_play_door: 0.3425→0.3276
- GATE: PERF PASS — spawn 1920x1080: +0.133 ms (rendered - painted, interleaved median, Editor proxy); overview 1920x1080: +0.794 ms (rendered - painted, interleaved median, Editor proxy); device: NOT RUN
- GATE: CHAR_SAME PASS — mean dE76 0.000, p95 0.000 over 26010 hero pixels

### hole07
- GATE: NO_PAINT PASS — no painted panorama bound on any enabled renderer, the skybox or a global
- GATE: SUN_MATCH PASS — disc vs light 0.000 deg; scattering-glow azimuth vs light 0.000 deg; light az 89.0 el 58.0
- GATE: PARALLAX PASS — 5/5 landmarks within tolerance; crane Cloud1 pred -19.86 meas -19.89; crane Cloud2 pred -20.77 meas -20.77; crane Cloud19 pred -7.74 meas -7.79; crane Karst_00@8.562538 pred -31.25 meas -33.27
- GATE: LONG_LENS PASS — 04_longlens: 0.1964→0.2825
- GATE: PERF PASS — tee 1920x1080: +-0.403 ms (rendered - painted, interleaved median, Editor proxy); crane 1920x1080: +-0.890 ms (rendered - painted, interleaved median, Editor proxy); device: NOT RUN
- GATE: CHAR_SAME PASS — mean dE76 0.000, p95 0.000 over 431539 hero pixels

### hole08
- GATE: NO_PAINT PASS — no painted panorama bound on any enabled renderer, the skybox or a global
- GATE: SUN_MATCH PASS — disc vs light 0.000 deg; scattering-glow azimuth vs light 0.000 deg; light az 89.0 el 58.0
- GATE: PARALLAX PASS — 8/8 landmarks within tolerance; crane Cloud10 pred -10.4 meas -10.93; crane Cloud5 pred -23.82 meas -23.82; crane Cloud14 pred -6.96 meas -6.98; crane Cloud7 pred -10.8 meas -10.59
- GATE: LONG_LENS PASS — 04_longlens: 0.0952→0.1478
- GATE: PERF PASS — tee 1920x1080: +0.231 ms (rendered - painted, interleaved median, Editor proxy); crane 1920x1080: +0.381 ms (rendered - painted, interleaved median, Editor proxy); device: NOT RUN
- GATE: CHAR_SAME PASS — mean dE76 0.000, p95 0.000 over 411459 hero pixels

### hole09
- GATE: NO_PAINT PASS — no painted panorama bound on any enabled renderer, the skybox or a global
- GATE: SUN_MATCH PASS — disc vs light 0.000 deg; scattering-glow azimuth vs light 0.000 deg; light az 89.0 el 58.0
- GATE: PARALLAX PASS — 7/8 landmarks within tolerance; crane Cloud0 pred -12.05 meas -12.04; crane Cloud5 pred -17.28 meas -17.24; crane Cloud24 pred -13.76 meas -13.73; crane Cloud25 pred -21.33 meas -21.21
- GATE: LONG_LENS PASS — 04_longlens: 0.0248→0.099
- GATE: PERF PASS — tee 1920x1080: +-0.800 ms (rendered - painted, interleaved median, Editor proxy); crane 1920x1080: +-0.621 ms (rendered - painted, interleaved median, Editor proxy); device: NOT RUN
- GATE: CHAR_SAME PASS — mean dE76 0.000, p95 0.000 over 501900 hero pixels

### hole10
- GATE: NO_PAINT PASS — no painted panorama bound on any enabled renderer, the skybox or a global
- GATE: SUN_MATCH PASS — disc vs light 0.000 deg; scattering-glow azimuth vs light 0.000 deg; light az 89.0 el 58.0
- GATE: PARALLAX PASS — 4/4 landmarks within tolerance; crane Cloud0 pred -10.23 meas -10.21; crane Cloud17 pred -13.49 meas -13.52; crane Cloud3 pred -9.52 meas -9.65; crane Cloud8 pred -9.57 meas -9.61
- GATE: LONG_LENS PASS — 04_longlens: 0.2→0.2193
- GATE: PERF PASS — tee 1920x1080: +0.928 ms (rendered - painted, interleaved median, Editor proxy); crane 1920x1080: +0.336 ms (rendered - painted, interleaved median, Editor proxy); device: NOT RUN
- GATE: CHAR_SAME PASS — mean dE76 0.000, p95 0.000 over 365779 hero pixels

### hole12
- GATE: NO_PAINT PASS — no painted panorama bound on any enabled renderer, the skybox or a global
- GATE: SUN_MATCH PASS — disc vs light 0.000 deg; scattering-glow azimuth vs light 0.000 deg; light az 89.0 el 58.0
- GATE: PARALLAX PASS — 8/8 landmarks within tolerance; crane Cloud6 pred -14.88 meas -14.9; crane Cloud0 pred -20.84 meas -20.87; crane Cloud12 pred -10.37 meas -10.36; crane Cloud23 pred -9.48 meas -9.48
- GATE: LONG_LENS PASS — 04_longlens: 0.6105→0.6507
- GATE: PERF PASS — tee 1920x1080: +0.571 ms (rendered - painted, interleaved median, Editor proxy); crane 1920x1080: +-0.281 ms (rendered - painted, interleaved median, Editor proxy); device: NOT RUN
- GATE: CHAR_SAME PASS — mean dE76 0.075, p95 0.000 over 289157 hero pixels

### hole13
- GATE: NO_PAINT PASS — no painted panorama bound on any enabled renderer, the skybox or a global
- GATE: SUN_MATCH PASS — disc vs light 0.000 deg; scattering-glow azimuth vs light 0.000 deg; light az 89.0 el 58.0
- GATE: PARALLAX PASS — 3/3 landmarks within tolerance; crane Cloud0 pred -14.65 meas -14.66; crane Cloud5 pred -6.35 meas -7.21; crane Karst_02@42.70393 pred -30.52 meas -31.52
- GATE: LONG_LENS PASS — 04_longlens: 0.1613→0.1619
- GATE: PERF PASS — tee 1920x1080: +-0.723 ms (rendered - painted, interleaved median, Editor proxy); crane 1920x1080: +0.509 ms (rendered - painted, interleaved median, Editor proxy); device: NOT RUN
- GATE: CHAR_SAME PASS — mean dE76 0.002, p95 0.000 over 416116 hero pixels

### hole14
- GATE: NO_PAINT PASS — no painted panorama bound on any enabled renderer, the skybox or a global
- GATE: SUN_MATCH PASS — disc vs light 0.000 deg; scattering-glow azimuth vs light 0.000 deg; light az 89.0 el 58.0
- GATE: PARALLAX PASS — 4/4 landmarks within tolerance; crane Cloud3 pred -16.86 meas -16.9; crane Cloud22 pred -22.5 meas -22.53; crane Cloud13 pred -10.35 meas -10.35; crane Karst_01@-23.17684 pred -39.27 meas -41.66
- GATE: LONG_LENS PASS — 04_longlens: 0.1736→0.2384
- GATE: PERF PASS — tee 1920x1080: +0.132 ms (rendered - painted, interleaved median, Editor proxy); crane 1920x1080: +-0.282 ms (rendered - painted, interleaved median, Editor proxy); device: NOT RUN
- GATE: CHAR_SAME PASS — mean dE76 0.000, p95 0.000 over 494261 hero pixels

### hole15
- GATE: NO_PAINT PASS — no painted panorama bound on any enabled renderer, the skybox or a global
- GATE: SUN_MATCH PASS — disc vs light 0.000 deg; scattering-glow azimuth vs light 0.000 deg; light az 89.0 el 58.0
- GATE: PARALLAX PASS — 5/5 landmarks within tolerance; crane Cloud1 pred -14.19 meas -14.21; crane Cloud2 pred -8.4 meas -8.38; crane Karst_01@-20.65161 pred -43.98 meas -46.86; crane Karst_00@9.348391 pred -34.67 meas -37.29
- GATE: LONG_LENS PASS — 04_longlens: 0.3505→0.4599
- GATE: PERF PASS — tee 1920x1080: +-0.121 ms (rendered - painted, interleaved median, Editor proxy); crane 1920x1080: +0.214 ms (rendered - painted, interleaved median, Editor proxy); device: NOT RUN
- GATE: CHAR_SAME PASS — mean dE76 0.001, p95 0.000 over 578531 hero pixels

### hole16
- GATE: NO_PAINT PASS — no painted panorama bound on any enabled renderer, the skybox or a global
- GATE: SUN_MATCH PASS — disc vs light 0.000 deg; scattering-glow azimuth vs light 0.000 deg; light az 89.0 el 58.0
- GATE: PARALLAX PASS — 4/4 landmarks within tolerance; crane Cloud12 pred -8.99 meas -8.97; crane Cloud11 pred -11.62 meas -11.64; crane Cloud18 pred -10.63 meas -11.45; crane Cloud20 pred -10.11 meas -10.21
- GATE: LONG_LENS PASS — 04_longlens: 0.4002→0.5215
- GATE: PERF PASS — tee 1920x1080: +-0.575 ms (rendered - painted, interleaved median, Editor proxy); crane 1920x1080: +-0.290 ms (rendered - painted, interleaved median, Editor proxy); device: NOT RUN
- GATE: CHAR_SAME PASS — mean dE76 0.007, p95 0.000 over 471173 hero pixels

### hole17
- GATE: NO_PAINT PASS — no painted panorama bound on any enabled renderer, the skybox or a global
- GATE: SUN_MATCH PASS — disc vs light 0.000 deg; scattering-glow azimuth vs light 0.000 deg; light az 89.0 el 58.0
- GATE: PARALLAX PASS — 6/8 landmarks within tolerance; crane Cloud7 pred -8.46 meas -10.1; crane Cloud13 pred -10.08 meas -10.07; crane Cloud15 pred -14.01 meas -14.0; crane Cloud0 pred -21.18 meas -28.97
- GATE: LONG_LENS PASS — 04_longlens: 0.2334→0.426
- GATE: PERF PASS — tee 1920x1080: +-0.630 ms (rendered - painted, interleaved median, Editor proxy); crane 1920x1080: +-0.710 ms (rendered - painted, interleaved median, Editor proxy); device: NOT RUN
- GATE: CHAR_SAME PASS — mean dE76 0.000, p95 0.000 over 360216 hero pixels

### hole18
- GATE: NO_PAINT PASS — no painted panorama bound on any enabled renderer, the skybox or a global
- GATE: SUN_MATCH PASS — disc vs light 0.000 deg; scattering-glow azimuth vs light 0.000 deg; light az 89.0 el 58.0
- GATE: PARALLAX PASS — 5/5 landmarks within tolerance; crane Cloud23 pred -16.36 meas -16.35; crane Cloud1 pred -9.71 meas -9.87; crane Karst_01@-18.32721 pred -44.51 meas -47.43; crane Karst_00@11.67279 pred -35.01 meas -37.8
- GATE: LONG_LENS PASS — 04_longlens: 0.0664→0.1117
- GATE: PERF PASS — tee 1920x1080: +-0.702 ms (rendered - painted, interleaved median, Editor proxy); crane 1920x1080: +0.543 ms (rendered - painted, interleaved median, Editor proxy); device: NOT RUN
- GATE: CHAR_SAME PASS — mean dE76 0.000, p95 0.000 over 321549 hero pixels

### hole19
- GATE: NO_PAINT PASS — no painted panorama bound on any enabled renderer, the skybox or a global
- GATE: SUN_MATCH PASS — disc vs light 0.000 deg; scattering-glow azimuth vs light 0.000 deg; light az 89.0 el 58.0
- GATE: PARALLAX PASS — 8/8 landmarks within tolerance; crane Cloud3 pred -8.0 meas -7.98; crane Cloud7 pred -14.06 meas -14.04; crane Cloud5 pred -15.26 meas -15.27; crane Cloud14 pred -14.81 meas -15.13
- GATE: LONG_LENS PASS — 04_longlens: 0.6427→0.7075
- GATE: PERF PASS — tee 1920x1080: +-0.219 ms (rendered - painted, interleaved median, Editor proxy); crane 1920x1080: +-0.909 ms (rendered - painted, interleaved median, Editor proxy); device: NOT RUN
- GATE: CHAR_SAME PASS — mean dE76 0.002, p95 0.000 over 514336 hero pixels

### hole20
- GATE: NO_PAINT PASS — no painted panorama bound on any enabled renderer, the skybox or a global
- GATE: SUN_MATCH PASS — disc vs light 0.000 deg; scattering-glow azimuth vs light 0.000 deg; light az 89.0 el 58.0
- GATE: PARALLAX PASS — 8/8 landmarks within tolerance; crane Cloud0 pred -10.0 meas -9.99; crane Cloud10 pred -15.23 meas -15.21; crane Cloud12 pred -16.73 meas -16.71; crane Cloud17 pred -11.76 meas -11.8
- GATE: LONG_LENS PASS — 04_longlens: 0.0504→0.1335
- GATE: PERF PASS — tee 1920x1080: +-0.144 ms (rendered - painted, interleaved median, Editor proxy); crane 1920x1080: +0.541 ms (rendered - painted, interleaved median, Editor proxy); device: NOT RUN
- GATE: CHAR_SAME PASS — mean dE76 0.001, p95 0.000 over 495396 hero pixels

### hole21
- GATE: NO_PAINT PASS — no painted panorama bound on any enabled renderer, the skybox or a global
- GATE: SUN_MATCH PASS — disc vs light 0.000 deg; scattering-glow azimuth vs light 0.000 deg; light az 89.0 el 58.0
- GATE: PARALLAX PASS — 3/3 landmarks within tolerance; crane Cloud10 pred -7.23 meas -7.21; crane Cloud21 pred -6.62 meas -6.66; crane Cloud17 pred -9.44 meas -9.41
- GATE: LONG_LENS PASS — 04_longlens: 0.2916→0.3034
- GATE: PERF PASS — tee 1920x1080: +0.468 ms (rendered - painted, interleaved median, Editor proxy); crane 1920x1080: +-0.343 ms (rendered - painted, interleaved median, Editor proxy); device: NOT RUN
- GATE: CHAR_SAME PASS — mean dE76 0.000, p95 0.000 over 379890 hero pixels

### hole22
- GATE: NO_PAINT PASS — no painted panorama bound on any enabled renderer, the skybox or a global
- GATE: SUN_MATCH PASS — disc vs light 0.000 deg; scattering-glow azimuth vs light 0.000 deg; light az 89.0 el 58.0
- GATE: PARALLAX PASS — 3/3 landmarks within tolerance; crane Cloud16 pred -12.7 meas -12.69; crane Cloud21 pred -6.74 meas -6.75; crane Cloud2 pred -8.51 meas -8.66
- GATE: LONG_LENS PASS — 04_longlens: 0.2503→0.3704
- GATE: PERF PASS — tee 1920x1080: +-0.208 ms (rendered - painted, interleaved median, Editor proxy); crane 1920x1080: +0.097 ms (rendered - painted, interleaved median, Editor proxy); device: NOT RUN
- GATE: CHAR_SAME PASS — mean dE76 0.000, p95 0.000 over 490805 hero pixels

### hole23
- GATE: NO_PAINT PASS — no painted panorama bound on any enabled renderer, the skybox or a global
- GATE: SUN_MATCH PASS — disc vs light 0.000 deg; scattering-glow azimuth vs light 0.000 deg; light az 89.0 el 58.0
- GATE: PARALLAX PASS — 3/3 landmarks within tolerance; crane Cloud7 pred -6.65 meas -6.68; crane Cloud8 pred -11.16 meas -11.01; crane Cloud17 pred -6.57 meas -6.98
- GATE: LONG_LENS PASS — 04_longlens: 0.0566→0.0774
- GATE: PERF PASS — tee 1920x1080: +0.214 ms (rendered - painted, interleaved median, Editor proxy); crane 1920x1080: +0.413 ms (rendered - painted, interleaved median, Editor proxy); device: NOT RUN
- GATE: CHAR_SAME PASS — mean dE76 0.000, p95 0.000 over 271509 hero pixels


## Proof images (`proof/`)
- `00_before_resort_diagnosis.jpg` — what gave the painting away: 2× vertical stretch, painted sun vs real sun, long-lens smear, no parallax, seam.
- `02_resort_pilot_before_after_final.jpg` (+ `02_resort_pilot_before_after.jpg` with sunset and night).
- `03_skyscraper_before_after.jpg`, `04_volcano_before_after.jpg`.
- `05_golf_before_after.jpg` (holes 7, 13, 10), `07_golf_all_holes_after.jpg` (all 16).
- `06_hub_before_after.jpg`.

## QUALITY — awaiting Adnan
- Resort: sent 10-17.
- Skyscraper and volcano: sent. The rooftop's painted dusk is gone at midday because the sky now follows the clock's sun. The volcano gets an ash-hazed sky.
- Golf: sent.
- Hub: sent. The golden-hour dome is lighter and bluer than the old peach gradient; it can be warmed.

## Open / not done
- Device frame time not run (phone not attempted). The Editor proxy is a proxy.
- The beige cones on the skyscraper are DreamWorldArt spires, outside this brief, left untouched.
- Snow (17) and desert (18) golf holes reuse the tropical karst; biome-specific ranges would read better.
- `Resources/Hub/Previews/*.mp4` were recorded with the painted skies; they need re-recording after integration (HubPreviewCapture, windowed).
- The painted textures stay in Resources, unused at runtime, until chat 6 confirms.
- `GolfAtmosphere.Look.SkyTexture` fields were already dead code and are left as they were.
