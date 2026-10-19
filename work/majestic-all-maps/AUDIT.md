# Majestic look on every map + weather: audit (chat 10, 2026-10-17)

Baseline: chat 9's Majestic layer (`work/majestic-maps-research/build`) and chat 2's rendered skies (`work/rendered-backgrounds`). Read-only audit: nothing in `Unity/` was changed.

Code facts come from a read of `Unity/Assets/Scripts` (file:line refs below). Cost numbers come from chat 9's sweep (`work/majestic-maps-research/proof/baseline.md`: Mac M5 Editor, 1920×1080, 4× MSAA, single-render counts). They are **not** phone numbers; no device frame time exists yet.

Contact sheets in `audit/`:
- `golf_tee_chat2.jpg`, `golf_aerial_chat2.jpg`: all 16 holes, 10-17, rendered sky, clear.
- `weather_current.jpg`: weather states (10-15 dream-worlds frames + chat 9 run 2).
- `weather_now_chat9.jpg`: 10-17 frames with Majestic + rendered sky (chat 9's run for this audit): h08 clear/rain/storm/fog/gusty, h17 blizzard, h21 eruption, resort rain/fog.
- `views_clear/`: every player view per hole (my capture run, see §5). Pending until the run lands.
- `sheet_hNN.jpg`: one sheet per hole from those views.

## 1. Every place in the game

| Place | Where it lives | Majestic layer (chat 9) | Rendered sky (chat 2) |
|---|---|---|---|
| Tennis **Resort** (TROPICAL) | `TennisVenueKind.Resort` | ✅ late-afternoon gold + `MajesticResort` | ✅ |
| Tennis **Skyscraper** (SKY) | `.Skyscraper` | ✅ blue hour + `MajesticSkyscraper` | ✅ |
| Tennis **Volcano** (MAGMA OPEN) | `.Volcano` | ✅ dusk storm + `MajesticVolcano` | ✅ |
| **Plaza hub** (plaza, locker, clubhouse, play hall, tennis room, golf room) | `Hub.unity`, `HubLayout.cs:48-64` | ✅ golden hour + `MajesticHub` (plaza only) | ✅ `HubDome` |
| Golf **Cliffside**: 7, 8, 9, 12, 15 | `Hole.cs:335` | ⚠️ light + grade, plus balloons, gulls, boats and whale (`MajesticLook.cs:111-113`) | ✅ coastal + karst |
| Golf **Wild Isles**: 13, 14, 17, 18, 19, 20 | `Hole.cs:339` | ❌ **nothing** (`look.Active=false`: no light, grade or dressing) | ✅ coastal + karst |
| Golf **Magma Open**: 10, 16, 21, 22, 23 | `Hole.cs:343` | ❌ **nothing** | ✅ magma profile (ash clouds) |
| Meadow Run 1–3 | tests only | n/a | n/a |

**11 of 16 golf holes get no Majestic layer at all.** On the five Cliffside holes the layer adds light, grade and sky life only. No hole has a set-piece pass toward a target the way the tennis venues do.

### Golf holes

| # | Course | Name | Par | Biome | Signature today | Dressing code | Tris/frame (M) | Draws | Pixel ms (M5) |
|---|---|---|---|---|---|---|---:|---:|---:|
| 7 | Cliffside | Cliffside | 4 | coastal | clifftop dogleg, green above the sea | standard look | 2.39 | 265 | 2.56 |
| 8 | Cliffside | Needle | 4 | coastal | knife-edge clifftop, sea-stack green, stone path, arch | standard + postcard | 2.02 | 268 | 3.36 |
| 9 | Cliffside | Split | 5 | coastal | ridge split by a lagoon | standard + postcard + composition swap | 2.46 | 276 | 3.29 |
| 12 | Cliffside | Island Carry | 3 | coastal | island green, arches, floating isles, lighthouse | coastal pilot (`GolfCoastalCliff12`, LuminousCoast) | **5.54** | 226 | 4.27 |
| 15 | Cliffside | The Steps | 3 | coastal | water carry, three-tier green | standard | 2.26 | 208 | 3.05 |
| 13 | Wild Isles | The Spiral | 5 | temperate | road round a pine hill, summit green | standard | 3.28 | 253 | 3.76 |
| 14 | Wild Isles | The Witch's Lair | 4 | woodland crater | green sunk in a crater, canopy | standard | 1.76 | 227 | 4.48 |
| 17 | Wild Isles | Frostbite Fjord | 5 | alpine / snow | frozen lake (Ice hazards), pines | standard | 2.75 | 244 | 3.75 |
| 18 | Wild Isles | Mesa Canyon | 3 | desert | two red mesas, water canyon, cacti | standard | 1.41 | 185 | 3.41 |
| 19 | Wild Isles | Temple Falls | 4 | jungle lagoon | waterfall pool, temple, stone step | standard + temple canopy | 2.51 | 270 | 3.89 |
| 20 | Wild Isles | Windmill Links | 4 | windmill links | tulip fields, canals, spinning sails | standard | 1.71 | 271 | 2.45 |
| 10 | Magma | Crater | 4 | volcanic | crater rim, lava inlet | standard + postcard (sea `Backdrop`) | 1.81 | 246 | 3.43 |
| 16 | Magma | Volcano Rim | 4 | volcanic | smoking volcano, lava river | standard (sea `Backdrop`) | 2.32 | 263 | 4.04 |
| 21 | Magma | Obsidian Slab | 3 | magma | slab over the lava lake | `LavaWorld` + geysers | 1.73 | 224 | 3.56 |
| 22 | Magma | Ember Causeway | 4 | magma | winding black-rock causeway | `LavaWorld` | 2.12 | 283 | 4.28 |
| 23 | Magma | Caldera Crown | 5 | magma | rock horseshoe round a lava lagoon | `LavaWorld` | 1.75 | 180 | 3.46 |

BUDGET.md allows ≤ 1.0 M visible triangles per view. Every hole is over that today (median 2.2 M, hole 12 5.5 M); chat 9's FEASIBILITY R3 already flags it. The Majestic rollout has to **pay for itself** on golf (LOD, impostors, shadow casters) before it adds anything.

### What the frames show (clear, 10-17, `golf_tee_chat2.jpg` / `golf_aerial_chat2.jpg`)
- **Same look everywhere.** Saturated flat lime turf with identical mow stripes on all 16 holes. One noon light, no signature hour, little aerial perspective. Wild Isles and Cliffside read as one course.
- **Islands floating on an empty sea.** Every non-magma hole is an island plate on a flat teal sea plane. Its edges are hard cliffs or plain bevels with no surf, shallows or foam band. From the crane/flyover the hole reads as a game board, not a place.
- **Few focal points.** Most tee views end in a horizon of identical karst islands (chat 2's) and cumulus. Landmarks the names promise are missing or tiny: no lighthouse on 12, no temple on 19 in the tee view, no windmill in 20's tee view, no erupting cone on 16.
- **Generic dressing.** Low-poly cone pines and lollipop trees repeat across temperate, alpine and windmill holes; the desert hole has scattered cacti; magma holes are black ground with a few palms. No density gradient: the play corridor and the far edge get the same scatter, so off-line views look empty.
- **Gameplay labels in world.** "Needle aperture", "Stairway current", "Canyon lift", "COOLING 3.1s" and "Spiral cut" float in the scene. They are gameplay text, so the refs leave them out, but the plan must keep them readable.
- **Hazard rocks.** Dark floating boulders (RockGate sockets, `DreamCourseLayout.cs:56-62`) hang in most skies. They are gameplay and stay. Today they read as dark blobs, so the refs give them a designed look (mossy stone, lava rock, ice).
- **Magma course is two things.** Holes 10 and 16 sit on the sea Backdrop with a magma sky. Holes 21–23 are a lava-lake disc whose rim is visible from the aerial. The flyover of 21–23 shows a hard-edged lava disc with spokes of lava falls: a flagrant seam.
- **Hole 17 snow** is a flat white plate with a blue ice-lake mesh; no snow on the trees, no frozen texture, no mountains.

## 2. Weather

How it's chosen: golf draws `Clear 25 / Gusty 25 / Rain 25 / Storm 15 / Fog 10` per hole from the round seed (`DreamConditions.cs:29-37`). There are **no per-hole restrictions**, except that no Storm comes within 2 holes of another. Tennis draws the same five per game boundary. Weather never changes mid-hole. Each biome renames the effect (`Weathers.SkyOf`, `RoundEvents.cs:90-94`):

| Weather | Coastal/temperate (7–9, 12–15, 18–20, **10, 16**) | Snow (17) | Ash (21–23) | Tennis Resort / Skyscraper | Tennis Volcano |
|---|---|---|---|---|---|
| Clear | clear | clear | clear | clear | clear |
| Gusty | wind | wind | wind | wind (+air drag) | wind |
| Rain | **Rain** | **Snow** | **Ashfall** | Rain (lower bounce) | Ashfall |
| Storm | **Thunderstorm** | **Blizzard** (no lightning) | **Eruption** (orange flash + rumble) | Thunderstorm | Eruption |
| Fog | **Sea Fog** | **Freezing Fog** | **Volcanic Smoke** | Sea Fog | Volcanic Smoke |

So there are **13 distinct weather looks** including gusty, plus the real-clock time of day: night 21–05, dawn 05–07, sunset 16:30–20:30 EST. Majestic overrides the clock with each place's signature hour (Adnan, 10-17). Overcast is not a state of its own; it's `_Cloud` 0.08–0.65 per weather.

Odd ones: holes 10 and 16 are Magma Open but get **rain and thunderstorm**, not ash. That's a design bug to decide (§ PLAN).

### How weather is drawn today (`Game/WeatherView.cs`)
- Three **full-screen volume spheres**:
  - `Golf/StormSky` dome (shafts, lightning glow, rainbow);
  - `Golf/WeatherFog`;
  - `Golf/WeatherGround` (wet, puddles, snow, ash).
- **Particles:**
  - rain 2,600 max at 1,500/s;
  - snow 3,200 at 1,100/s;
  - ash 1,400 at 450/s;
  - embers 200;
  - splashes 300.
- **Lightning:** `Golf/LightningBolt`, every 2.5–6 s in storms.
- **Globals:** `WeatherDirector` publishes `_EnvironmentWetness`, `_EnvironmentSnow` and `_EnvironmentStorm`. `EnvironmentSurface.hlsl` reads them, and so do 10 world shaders.
- **Wind:** `_GolfWind` sways plants only.

### Cost (chat 9 sweep, same place clear → weather)
| Slot | Δ pixel GPU (M5) | Δ sync 1080p |
|---|---:|---:|
| golf h08 fog | **+3.29 ms** | +4.56 |
| golf h08 rain | **+4.14 ms** | +4.73 |
| golf h08 storm | **+4.01 ms** | +5.74 |
| golf h13 storm | +3.56 ms | +2.69 |
| golf h21 storm (eruption) | +3.05 ms | +1.72 |
| tennis resort fog/rain/storm | +1.4–1.5 ms | ±2 |
| tennis skyscraper / volcano | −0.6 to +0.95 ms | +0.7–2.5 |

Golf weather roughly **triples** a golf frame's per-pixel cost. That comes from three blended full-screen depth-reading passes. It is the biggest single cost in the game and leaves no room for any Majestic layer below the iPhone 17 Pro (FEASIBILITY §4).

### What the weather frames show (`weather_current.jpg`)
- **Storm/rain golf (h08, 10-17):** the whole frame washes to a flat **pink-grey veil**. The sky panorama turns pink, the far islands vanish into a beige box, and the turf gets a dense grain "wet" noise that reads as dirty, not wet. No darkening of the sky toward the storm, no cloud mass, no lit wet path, no puddle reflections. Rain streaks are thin and sparse at TV distance.
- **Fog (h08/h17/resort, 10-15):** a uniform white-pink overlay with no depth layering. Near and far fog at once, so the frame loses contrast without "mystery". On tennis the far court disappears into a flat wash.
- **Snow / blizzard (h17):** the same grain noise in white over the turf, white-out sky. Trees don't gather snow. Reads like a broken texture.
- **Eruption / ash (h21):** purple-grey dim, a few ember dots. No eruption event visible in a still.
- **Tennis storm (resort/skyscraper):** a light rain layer and a slight blue cast. The serve ring stays readable. The skyscraper has a flat purple sky, with the rendered sky and lightning not doing much. The volcano storm has no plume.
- **Gusty:** shows only as plant sway and particle drift. There is no visual of wind in sky, flags, sea or grass waves; nothing reads in a still. Pending chat 9's 10-17 frames: `proof/now/golf_h08_gusty.png`.

**10-17 frames with Majestic and the rendered sky** (chat 9's run, `audit/weather_now_chat9.jpg`) confirm all of the above on the current build:
- **h08 Gusty is pixel-for-pixel the clear frame.** Wind has no visual at all in a still.
- **h08 Rain / Storm** are a flat grey veil over the whole frame. The turf turns into white speckle noise and the far islands and sea wash out; there is no dark storm mass, wet gloss or reflection. Storm differs from rain only by denser streaks.
- **h08 Fog:** a uniform yellow-green wash with no layering; the sky is still blue above it.
- **h17 Blizzard:** a carpet of white speckles on the turf, big flat flakes and a grey sky. The trees carry a little snow.
- **h21 Eruption:** a dark flat frame with one plume card. The golfer is lit flatly and the floating label "Quiet plume" is in the scene.
- **Tennis resort Rain / Fog:** a whole-frame grey or yellow veil. The court stays readable, but the place loses all its colour, with no wet court, umbrellas or depth.

## 3. Cameras the player actually sees on a hole (`Game/CameraRig.cs`, base FOV 60)

| Camera | Code | Pose |
|---|---|---|
| Address (tee, fairway, rough, bunker, every non-putt lie) | `FrameAddress` :46 via `GolfGame.FrameAim` :1850 | behind the ball 3.85 yd, 0.55 right, 2.05 up; looks 3 yd ahead. Joystick tilts up/down. Extra lift on 9/12. |
| Putt / green read | `FrameGreen` :104 | behind the ball 3.8, 0.65 right, 2.5 up. **One side only**: the green from any approach direction. |
| Ball flight follow | `BeginShot` :195 / `FollowShot` :207 | holds the launch view 1.5 s, then chases 30 yd behind and 6 up |
| Landing | `FollowShot` | 11 yd behind the ball, 4.2 up, as it lands and rolls |
| Hole intro flyover | `HoleIntro.Pose` | opening: high glide down the hole (46→34 yd up, 26 yd seaward, fov 44). Then 2 highlights (carry, windmill, greenside, edge/vista, bunkers/rocks) and the green (fov 28). |
| Tee introduction | `GolfGame.cs:1364-1392` | over the shoulder, then full body; the hole behind the golfer |
| Replay | `GolfGame.cs:2827-2856` | launch from 8 yd behind and 2.2 to the side, then **a cut to a landing camera looking back toward the tee** |
| Hole-out / result | `FrameHoleOut` :155, `FrameCharacterResult` :138 | golfer on the green, the hole behind |
| Multiplayer | `FrameGolfParty` :117 | the party ±10 yd back, 3.4 up |
| Course select | `Orbit` :505 | circles the hole |

**Lie-specific cameras do not exist.** Bunker, rough and trees all use the address camera. Every off-line ball therefore shows the player a **ground-level view from wherever the ball stops**, facing the pin. That includes the back sides of tree lines, cliff edges and the sea plane: the views that look emptiest today.

The **reverse views** (replay landing camera, hole-out, putts from the far side of the green) look back up the hole, toward the tee and the far side of the island. There, today, is mostly sea plane and the same karst ring.

## 4. Majestic coverage gaps (vs chat 9's targets)

Chat 9's targets (`work/majestic-maps-research/concepts/after`) set the bar:
- a signature hour;
- a living 3D sky;
- one landmark;
- layered far landforms in aerial haze;
- life (boats, gulls, balloons, whale);
- one wind;
- crisp readable gameplay;
- weather as an event (rain clearing to a rainbow, lit wet path).

| Gap | Where | Note |
|---|---|---|
| No Majestic layer at all | 11 holes (Wild Isles + Magma) | first thing to fix; profiles per course |
| One camera only | all golf | targets and chat 9's proofs are tee-camera only; Adnan: "the entire hole" |
| No per-hole landmark per direction | all golf | reverse and off-line views have no subject |
| Island edges and sea | 13 sea holes | no shore band, foam, shallows or surf; hard bevels |
| Magma rim seam | 21–23 | lava disc edge + spokes visible from the flyover |
| Course identity | Cliffside vs Wild Isles | same turf, trees, sky and light |
| Weather looks | all | flat veils, grain-noise wetness, no weather event, no payoff (rainbow, clearing), +3–4 ms |
| Weather payoff only on h08 target | — | chat 9 made one weather target (h08 clearing); none for snow, ash, fog, gusty or tennis rain |
| Triangle budget | every hole | 1.4–5.5 M vs ≤ 1.0 M; R1–R3 make-room work comes first |
| 10/16 weather family | Magma Open | rain/thunder on a volcano course; should be ash |

## 5. Per-hole camera set (capture)
`unity/Assets/Editor/MajesticHoleViews.cs` (in my clone only) shoots, per hole, 1920×1080:

| Kind | Views |
|---|---|
| Game-framed (the ball is dropped there; the game's own aim camera, putter on the green) | `tee`; `mid` and `approach` (par 4/5) or `approach` (par 3); `offL` and `offR` (fairway edge + 14–18 yd, nudged off water); `puttFront`, `puttLeft`, `puttRight` |
| Flyover (the real `HoleIntro.Pose`) | `flyOpen`, `flyH1`–`flyH3` |
| Reverse | `greenBack` (from behind the pin back down the hole), `reverseMid` (mid-fairway back to the tee) |
| 360° at mid-fairway | `pan0/90/180/270` (backdrop per direction, for the design sheets) |
| Overview | `crane` (high behind the tee), `map` (top-down) |
| Live drives, the game's follow + landing cameras | `driveGood_*` (to the fairway or green), `driveBad_*` (deliberately 30 yd off line). Real rest spots and lies are logged. |

`hNN_cameras.json` stores position, forward, FOV, ball spot and lie for every view. The same set is re-shot for the gates in PLAN.md.

### Capture results (10-17)
- The run took 18:00–18:40 through `heavy.sh unity` and was booked on SCHEDULE.md (line removed when done). It used `~/majestic-all-maps-UnityClone`, was muted, ran in clear weather with Majestic and the rendered sky on, and shot 16 holes × 26–28 views (≈ 450 frames).
- Per-hole sheets: `audit/sheet_hNN.jpg`.
- Camera sets: `audit/views_clear/hNN_cameras.json`.
- Design sheets: `design/sheets/hNN_design.jpg` (map + line of play + density zones + 360° strip + brief).

Where the live drives finished (real ball rest spots, used for the off-line views and the gates):

| Hole | Good drive → | Bad drive (30 yd off line) → |
|---|---|---|
| 7 | fairway | rough (left tree line) |
| 8 | fairway | rough |
| 9 | fairway | rough |
| 10 | rough | **water/lava** |
| 12 | fringe | rough |
| 13 | rough (the dogleg target cut the corner) | rough |
| 14 | fairway | rough |
| 15 | green | green (wide side) |
| 16 | fairway | **water/lava** |
| 17 | fairway | rough (snow) |
| 18 | green | rough (sand) |
| 19 | fairway | rough |
| 20 | fairway | rough |
| 21 | fairway | **lava** |
| 22 | fairway | rough |
| 23 | **lava** | **lava** |

So off-line balls on every hole come to rest in the rough, among trees, on sand and snow, at cliff edges and at lava banks. The **address camera then looks from there toward the pin**, and that view is in the gate set.

### New problems the multi-view capture found
1. **The mid/approach spot is in the water on carry holes** (8, 9, 12, 18 and lava on 10, 21). The harness put the golfer in the sea. Fixed in the harness (`InPlay()` walks to the nearest dry point) for future gate runs; these refs used mid/green-back/off-line views instead.
2. **Camera inside geometry:** on 16 the mid-fairway address camera sits inside the basalt gate (`h16_mid.jpg` is black with a red seam). A lie next to a gate hazard gives the player a blocked view, so the plan needs a camera collision/pull-in rule for gate hazards.
3. **`[GolfLandmarkFinish] LIGHTHOUSE skipped: local bounds do not match source`**: the Cliffside lighthouse finish silently does not apply. Every Cliffside ref leans on the lighthouse as the course landmark.
4. **Floating gameplay labels** ("Needle aperture", "COOLING 6.2s", "ACTIVE 1.0s", "Stairway current", "Root window", "Temple aperture", "Petal current") are drawn in the world and show in every view, including flyovers. Gameplay must keep them, but they need a styled sticker treatment (chat 8 UI vocabulary) rather than plain floating text.
5. **360° pans:** at mid-fairway on 7, 9, 13, 15 and 20 the side and back directions show a flat lime plane with a few cone trees and the same karst ring. That is the strongest evidence for the "every direction has a subject" rule.
6. **Magma 21–23 from the green-back and off-line views:** the lava disc's flat procedural texture fills most of the frame; the rim and caldera walls do not exist.

### Objective baseline (tools/ref_match.py, 10-17)
- **NO_EMPTY_VIEW** fails on **203 of 332** of today's player views (`audit/no_empty_view_today.jsonl`). The check is the widest flat, featureless run at coarse scale, ≤ 0.25 of the frame width; for putts only the backdrop band beyond the green counts.
- The views that fail on every hole:
  - the green looking back;
  - the intro flyover's green shot;
  - mid-fairway 360° views;
  - the reverse view to the tee;
  - the ball-at-rest result views.
- All 80 targets pass. Calibration: today 0.35–1.0, targets 0.05–0.22.
- **REF_MATCH (objective half):** every sampled today frame fails against its target. The main gaps are `detail_ratio` 0.39–0.83 (today is flatter than the target) and `sky_dist` 12–39 (the target's signature hour is missing).
