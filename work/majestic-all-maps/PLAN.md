# PLAN: the Majestic look on every map, every view, every weather (chat 10, 2026-10-17)

**Status: APPROVED by Adnan, 10-17 ("Go ahead with PLAN.md"). Building has started.**

Adnan's decisions (§4.5), 10-17:
1. Holes 10 and 16 switch to the **ash weather family**: ashfall, eruption and volcanic smoke.
2. **One signature hour per course:** Cliffside morning, Wild Isles golden afternoon, Magma pre-dawn.
3. **Tennis weather goes around play:** arrival, between games and after the match.

Inputs:
- `AUDIT.md`: places, weather, cameras, costs.
- `design/HOLE_BRIEFS.md`: the design per course and hole.
- `research/WHOLE_HOLE_BEST_PRACTICE.md`: how good golf and open-world games make every view work, with sources.
- `refs/`: the AI targets, listed in `refs/MANIFEST.md` and shown on the board.
- Chat 9's Majestic layer and chat 2's rendered skies, which this plan extends.

Floor: **60 fps at ≥ 1920×1080** everywhere (`work/frame-rate-60b/BUDGET.md`).
- GPU ≤ 11 ms on the TV view; the environment gets ≤ 5 ms of that.
- ≤ 1.0 M visible triangles per view.
- Weather gets ≤ 1.0 ms.
- Resolution and frame rate are never lowered to fit.

---

## 1. What "done" means

1. **All 16 golf holes, the 3 tennis venues and the plaza** match their refs from **every camera a player sees**, not just the tee:
   - tee, mid-fairway and approach;
   - off-line lies left and right;
   - putts from three sides;
   - the green looking back;
   - the intro flyover;
   - the replay and landing cameras.

   Every one of those views has a subject. No void, flat empty plate or bare island bevel shows anywhere.
2. **Each of the 13 weather looks** reads as top quality at phone and TV distance and stays readable (ball, flag, lines), with a weather *event* where the ref shows one: rain clearing to a rainbow, lightning, an eruption. The 13 are:
   - Rain, Thunderstorm and Sea Fog;
   - Snow, Blizzard and Freezing Fog;
   - Ashfall, Eruption and Volcanic Smoke;
   - Gusty, in three families;
   - and the tennis versions.
3. All of it inside the frame budget, measured at the **worst view** of every hole and in the heaviest weather. That rules out the golf weather layer's +3–4 ms of today.

### The targets
Board: https://claude.ai/artifact/3fXZZrnQ9pwjA7NrM1C4Z5 (private; Adnan shares it if others need it). Files: `refs/` (`MANIFEST.md` has source frame, model, quality, credits and job id for every image).

- **Golf:** 16 holes × 5 views = 80 targets, all repainted from real frames of `MajesticHoleViews`. Every hole's views were generated from its `design/HOLE_BRIEFS.md` entry, and every non-tee view was anchored to the hole's approved tee target, so landmarks agree between views.
  - Tee and intro flyover: high quality.
  - Approach or mid-fairway, green looking back, one off-line lie: medium quality.
  - Today-vs-target sheets: `refs/holes/sheets/hNN_today_vs_ref.jpg`.
- **Weather:** 16 targets in `refs/weather/`.
  - Golf: W01–W11 (W02 is chat 9's rain-clearing image).
  - Tennis: W12–W16.
- **Cost:** 180.0 credits, as approved.

## 2. Best practice we follow (sources in `research/WHOLE_HOLE_BEST_PRACTICE.md`)

| Rule | Where it comes from | How we apply it |
|---|---|---|
| Compose for the cameras the player really has | Destiny 2 backgrounds (80.lv); PGA 2K authored camera sequences | the per-hole camera set (`audit/views_clear/hNN_cameras.json`) is the art spec and the gate |
| Every view has a subject; landmarks pull the eye | BotW triangle rule (CEDEC 2017); Mario Golf: Super Rush pin beam; Ghost of Tsushima | one landmark per **quadrant** per hole (`HOLE_BRIEFS.md` FWD/BACK/L/R); one course landmark visible from every hole |
| Near / mid / far / sky layers that recede | 80.lv backgrounds and skyboxes; Unreal aerial perspective | chat 2's sky + karst far layer; new **mid ring** of landforms and impostors per course; height fog matched to the sky colour |
| Few species, strong values, clustered scatter | Ghost of Tsushima; Horizon ZD; Far Cry 5 ecology | 4–6 species per course, clusters of 3–7, density by distance from the corridor (§4.3) |
| Hide the world's edge | 80.lv; BotW rectangular masses | shore band + shallows + foam on every island; caldera walls on 21–23; no camera can see the sea plane's edge |
| Detail costs LOD, not frames | Unity LOD/HLOD/impostor docs; Hot Shots pop-in reviews | LOD crossfade, impostor rings, per-layer cull distances; flyovers checked for pop-in frame by frame |
| Stable frame time beats detail | Hot Shots Switch reviews; Golf Rival vs Clash (Naavik) | the make-room work (§3) lands before any new dressing |

## 3. Make room first (golf)

Every hole is over the 1.0 M triangle cap today: median 2.2 M, hole 12 is 5.5 M. Golf weather adds +3–4 ms of pixel cost. The Majestic dressing has to be paid for first. These are chat 9's FEASIBILITY items R2–R4, scoped to golf:

| # | Change | Expected (EST, A19 Pro) | Gate |
|---|---|---|---|
| M1 | Shadow casters: golfer, ball, club, flag and hero props only; scenery gets baked AO or blob shadows | 0.5–1.5 ms | casters ≤ 12 per view |
| M2 | Per-hole triangle diet: LOD groups with crossfade on trees, rocks and landmarks; HLOD/impostor ring beyond ~120 yd; hole 12 cut first, then 13, 17, 19, 9, 7 | 1–2.5 ms on heavy holes | **TRIS ≤ 1.0 M per view at every sampled camera** |
| M3 | **Weather inside the materials**: drop `WeatherView`'s three full-screen volume spheres; wetness, snow, ash and fog become globals read by the world shaders (`EnvironmentSurface.hlsl` already reads `_EnvironmentWetness` etc.) | 3–4 ms in weather | weather Δ GPU ≤ 1.0 ms |
| M4 | Particle diet: one camera-attached rain/snow/ash layer + ≤ 400 near streaks outside the ball corridor (today rain is 2,600, snow 3,200) | 0.3–0.6 ms | particle count ≤ 600, corridor clear |

## 4. What gets built

### 4.1 Architecture: extend chat 9's layer
- **New files only**, under `Scripts/Majestic/` and `Resources/Majestic/`. They self-attach as chat 9's do and switch off with `MAJESTIC=0`.
  - `MajesticLook.Golf(n)` grows from 5 holes to all 16, with one profile per **course**: signature hour, grade, fog, palette.
  - Per-hole tables say where each landmark, set piece and density zone sits.
- New pieces:

| File (new) | Does |
|---|---|
| `MajesticCourse.cs` | course profiles A/B/C (hour, light, grade LUT, fog, palette, species list) |
| `MajesticHoleKit.cs` | per-hole data from `HOLE_BRIEFS.md`: landmark per quadrant, set pieces, density zones, hazard-rock skin |
| `MajesticScatter.cs` | instanced clustered scatter by distance from the corridor and green; grounded base patches; LOD and cull distances |
| `MajesticShore.cs` + `MajesticShore.shader` | island shore band, shallows gradient, foam rings, surf at cliffs; replaces bare bevels on 13 sea holes |
| `MajesticRing.cs` | mid-distance impostor ring of landforms per course (outside chat 2's far karst), so no direction is empty |
| `MajesticCaldera.cs` | caldera walls with lava falls around 21–23 (hides the lava-disc rim seam) |
| `MajesticLife.cs` | extends `MajesticGolf`'s balloons, gulls, boats and whale to every course: birds, butterflies, petals, embers, windmill sails, ducks |
| `MajesticWeather.cs` + shader includes | §4.4 |

- Landmark meshes (lighthouse, windmill, temple and twin falls, chalet, witch's cottage, mesa arch, caldera volcano) are built in **Blender** (headless, through `heavy.sh blender`) as low-poly LOD0/LOD1 + impostor, in the house soft-plastic style.
- **Shared-file edits** go to chat 6 as patches, as chat 9 did with its hook:
  - `WeatherView` (switch the volumes off when Majestic weather is on);
  - `EnvironmentSurface.hlsl` (fog, snow, ash and puddle terms);
  - `HoleView` (Backdrop for 10/16).

### 4.2 Per course and per hole
Each hole gets the brief's FWD/BACK/L/R landmarks, set pieces and edge treatment. Its refs are its target from 5 views:
- tee;
- flyover;
- mid-fairway (approach on par 3s);
- green looking back;
- one off-line view.

| Course | Holes | Biggest jobs | Est. effort (builder-days) |
|---|---|---|---|
| A Cliffside | 7, 8, 9, 12, 15 | shore + foam on all edges; lighthouse visible from every tee; hole 12 diet (5.5 M → ≤ 1 M); morning light | 4–5 |
| B Wild Isles | 13, 14, 17, 18, 19, 20 | six biomes, six landmark kits (tower, cottage, chalet + falls, mesa arch, temple + twin falls, windmill); 17's snow on branches; golden afternoon | 7–9 |
| C Magma Open | 10, 16, 21, 22, 23 | caldera volcano landmark; caldera walls (21–23 seam); basalt shore with glowing tide line (10, 16); pre-dawn light; ember life | 4–6 |
| Plaza + tennis | — | chat 9's open items (skyscraper and volcano behind target, café guests, embers); weather looks W12–W16 | 2–3 |

Fixes the multi-view capture found (AUDIT §5), owned by the golf chat:
- **Camera pull-in at gate hazards.** On hole 16 the address camera sits inside the basalt gate. Add a sphere-cast pull-in to `FrameAddress`; this is a shared file, so it goes to chat 6 as a patch.
- **`GolfLandmarkFinish` skips the lighthouse** ("local bounds do not match source"). Fix it or replace it with the new lighthouse landmark, because Cliffside's course landmark depends on it.
- **Floating gameplay labels** ("Needle aperture", "COOLING 6.2s"…) get a sticker treatment in chat 8's UI vocabulary instead of plain floating text, and stay out of the flyover's hero frames.
- **On 21–23**, add caldera walls so the lava disc's edge never shows from the green-back, off-line or flyover views.

### 4.3 Dressing density rule (every hole)
| Zone | Distance from the play corridor or green | Content | Budget |
|---|---|---|---|
| Z0 corridor | 0–8 yd | turf only: mow stripes, crisp edges, fringe, a few wildflower tufts in the rough | ~0 |
| Z1 near | 8–25 yd | dense clusters of 3–7 (shrubs, rocks, flowers, trees at LOD0), grounded patches, the hole's set pieces | ≤ 250 k tris |
| Z2 mid | 25–80 yd | tree lines and groves in clusters, LOD1, gaps framing views of the landmarks | ≤ 200 k |
| Z3 shore/edge | the island's rim | shore band, foam, surf, cliff skirts | ≤ 50 k |
| Z4 far | 80 yd + | impostor ring, landmark impostors, chat 2's karst and sky | ≤ 50 k |

The gate is **NO_EMPTY_VIEW**: in every sampled camera, no flat, featureless ground area wider than 25 % of the frame width, and the named subject is on screen.

### 4.4 Weather (one system, golf and tennis)
`MajesticWeather` drives everything from one state: weather + intensity 0..1 + event phase. It replaces the volumes with:

| Piece | Implementation | Cost (EST) |
|---|---|---|
| Wetness | `_EnvironmentWetness` (exists) → darker albedo by porosity, gloss up, puddle mask in turf/court/stone shaders; drying order: edges first, puddles last | 0.2–0.4 ms |
| Puddles + ripples | world-space puddle mask; ripple flipbook only within 30 yd of the camera | in the above |
| Rain | camera-attached cylinder with scrolling streak texture + ≤ 400 lit streak particles outside the ball corridor + splash rings on puddles | 0.4–0.6 ms |
| Snow / ash cover | up-facing mask in world shaders (`_EnvironmentSnow`, new `_EnvironmentAsh`); lines, green and ball kept clear | ~0.1 ms |
| Snow / ash / ember fall | the same camera layer with a flake or ash texture + ≤ 300 near flakes | 0.3–0.5 ms |
| Fog | in-shader height + distance fog toward chat 2's sky colour; "fog bank" shape (low over water, thin over the green); **ball, flag and players capped at ≤ 15 % fog** | ~0 |
| Sky | chat 2's `RenderedSky` `_Cloud`/`_Sunset` driven by weather; storm cloud wall cards (≤ 0.3 ms); sun shafts as cards | 0.2–0.4 ms |
| Lightning | sun pulse + sky flash + `LightningBolt` 2–4 frames, ≤ 3 flashes/s, exposure clamped; thunder at distance/343 s (chat 8 audio bus) | ~0 |
| Eruption | caldera flash on cloud undersides, lava bombs as 6–10 arcing meshes, ember burst, rumble | 0.1–0.2 ms |
| Wind | one global `_WindDir/_WindStrength/_Gust` (extends `_GolfWind`): grass waves, trees, palms, flags, bunting, net, sails, cloud speed, whitecaps, particles | < 0.2 ms |
| Events | rain → **clearing + rainbow** (h08 ref) between holes / games; storm rolls in on hole start; eruption on Magma storms | ~0 |
| Audio hooks | rain bed, wind bed and gust swells, thunder, rumble on chat 8's `Ambience` bus, driven by the same state | — |

| Effect | Ref | Must show |
|---|---|---|
| Rain | W01 (golf h07), W12 (tennis resort) | dark sky over the sea, glossy turf/court, puddles with reflections, umbrellas, lit streaks against dark backgrounds |
| Rain clearing | W02 (chat 9 h08) | sunbeams, rainbow, wet path, last drops |
| Thunderstorm | W03 (h13), W14 (skyscraper) | storm wall, forked lightning far off, wind-bent trees, wet reflections |
| Sea Fog | W04 (h15), W13 (resort) | fog bank in low ground and water, green and players clear above it, lighthouse beam |
| Gusty | W05 (h20), W15 (skyscraper) | sails racing, petals, grass waves, flags snapping, fast cloud shadows (debris never on the court/green) |
| Snow / Blizzard / Freezing Fog | W06–W08 (h17) | flakes, snow on branches, warm windows; sideways snow; ice-crystal sparkle |
| Ashfall / Eruption / Volcanic Smoke | W09–W11 (h22, h23, h21), W16 (tennis volcano) | grey flakes with lava glowing brighter; caldera erupting; sulphur smoke banks lit from below |

### 4.5 Decisions for Adnan
1. **Holes 10 and 16** are on Magma Open but draw sea weather (rain, thunderstorm). Switch them to the ash family, so they get ashfall, eruption and smoke? *(Recommended: yes. The refs show them that way.)*
2. **Signature hour per golf course:** A morning, B golden afternoon, C pre-dawn. Chat 9's rule keeps the signature hour all day.
3. **Tennis weather timing:** keep weather during play (today), or wrap it around play (arrival, between games, after the match) as chat 9 proposed?

## 5. Gates (binary; replaces the single-frame check)
The camera set per hole: tee, mid, approach, offL, offR, puttFront, puttLeft, puttRight, flyOpen, flyH1–3, greenBack, reverseMid, pan0–270, crane, driveGood_*, driveBad_*. That is about 26–28 views per hole. They are re-shot by `MajesticHoleViews` in every weather that hole can draw, with one contact sheet per hole and weather.
- The harness lives in `unity/Assets/Editor/MajesticHoleViews.cs`; run it with `tools/capture.sh <out>` through `heavy.sh`, with env `MAM_HOLES` and `DREAM_WEATHER`.
- It writes `hNN_cameras.json` (pose, FOV, ball spot and lie) so the same set can be re-shot.
- Since the first run, `InPlay()` keeps mid/approach spots out of the water.

| Gate | PASS when |
|---|---|
| **REF_MATCH** | for the 5 ref views of each hole and each weather ref, the in-game frame next to the ref shows the same landmarks, set pieces, sky mood and light direction, with value and palette histograms within tolerance; Adnan signs the side-by-side sheet (his eye is final) |
| **NO_EMPTY_VIEW** | every sampled camera (all ~24) has its named subject on screen and no flat featureless area > 25 % of the frame width (automatic: low-gradient non-sky area mask) |
| **NO_VOID** | rendering with a magenta clear colour and the sea plane flagged gives 0 void pixels and no visible sea-plane or lava-disc edge in any sampled camera |
| **POP_IN** | the flyover rendered at 60 fps: no object appears or vanishes between consecutive frames (frame-diff blobs > 0.2 % of the frame) |
| **READABILITY** | ball and flag luminance contrast ≥ 3:1 against their background in every view and weather; no weather particle inside the ball corridor; fog on ball, flag and players ≤ 15 % |
| **PERF_WORST_VIEW** | at the most expensive sampled camera of each hole, in its heaviest weather: visible triangles ≤ 1.0 M, draws ≤ 250, Editor proxy median ≥ 58 fps at 1920×1080 (`FrameRate60bTests`), and on device (iPhone 17 Pro and one older phone) GPU ≤ 11 ms |
| **WEATHER_COST** | Δ GPU of each weather vs clear ≤ 1.0 ms at the same camera (interleaved A/B, chat 9's method) |
| **DETERMINISM** | the same seed gives the same weather, wind and visibility on every client and every quality tier (online) |
| **TOGGLE_RESTORES** | `MAJESTIC=0` gives back today's frame exactly (chat 9's rule) |

## 6. Order of work and the parallel split
The machine allows **1 Unity + 2 Blender** jobs at once (`heavy.sh`), so at most **two heavy builders** run at a time, plus light chats.

| Phase | Chat | Work | Heavy use |
|---|---|---|---|
| 0 | **G0 golf make-room** | M1–M2 golf (shadow casters, LOD/HLOD/impostors, hole 12 diet) + `MajesticHoleViews` gates baseline | Unity |
| 0 | **L landmark kit** (Blender) | lighthouse, windmill, temple + twin falls, chalet, witch's cottage, mesa arch, caldera volcano + walls, shore/foam meshes; LOD0/1 + impostors | Blender ×1 |
| 1 | **W weather** | M3–M4 + §4.4 `MajesticWeather` on golf h07/h13/h15/h17/h20/h21–23 and the 3 tennis venues; patches for chat 6 | Unity (alternates with G) |
| 1 | **G1 Cliffside** | course A: shore, ring, scatter, set pieces, life, light; REF_MATCH on 7, 8, 9, 12, 15 | Unity (alternates with W) |
| 2 | **G2 Wild Isles** | course B | Unity |
| 3 | **G3 Magma Open** | course C, caldera walls | Unity |
| 4 | **chat 6 integration** | shared-file patches, lobby re-export, whole-game sweep, device perf | Unity + device |

G0 → G1 → G2 → G3 run in sequence in one golf chat, so they never share files. W runs in parallel and owns only the weather files and the shader-include patch. L feeds G1–G3. Each chat books `SCHEDULE.md`, batches its captures and pushes images every 15–20 min.

Rough total: about 20–28 builder-days. G0 + W first (~5–6 days), then courses A, B and C at about 4, 8 and 5 days.
