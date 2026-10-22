# Majestic Party: art and tech direction for maps and weather

Research chat 9, 2026-10-17. This is a proposal only; nothing in the game was changed.

It builds on [RESEARCH.md](RESEARCH.md) (what the best-looking 60 fps games do) and [FEASIBILITY.md](FEASIBILITY.md) (our measured baseline and the verdict per ambition). Every recommendation keeps the floor: **60 fps at ≥1920×1080 on the phone, on the AirPlay TV and in the lobby**.

---

## 1. The direction in one paragraph

Every venue is **a postcard place you'd want to visit**, seen at **its signature hour**, with **one landmark you'll remember**, a world that **moves** (one wind through flags, palms, grass, crowd and clouds), and weather that arrives as **an event with a payoff** (the storm rolls in, the thunder lands, the court drips, the rainbow comes out).

The world is calm, warm and believable, built like a toy diorama with soft plastic surfaces. The **spectacle belongs to the players**: hits, celebrations and confetti (chat 8).

Think Wii Sports Resort's island, Mario Kart World's light, Sky's weather moods and Switch Sports' "a place you'd want to be". Not a pro stadium, and not a simulation.

## 2. Six pillars

| Pillar | What the player feels | How we build it (cheap) | Reference |
|---|---|---|---|
| **Place** | "Where is this? I want to go there." | One hero landmark per venue in the play camera's view. Near (court) / mid (stands, palms, buildings) / far (landmark, coast) / sky layers, with aerial-perspective fog toward the sky colour between them. | BotW near/mid/far; Wii Sports Resort volcano |
| **Light** | Golden, warm, never muddy | A signature hour per venue from one time-and-weather controller. Chat 2's rendered sky LUT supplies the sky, fog and ambient colour. Key light angle held steady. Light floor on foliage; tinted shadows; one LUT grade. | Mario Kart World fixed key light; Genshin light floor |
| **Life** | "It's alive" | One global wind. Crowd as an instanced motion texture driven by an excitement value. Birds, boats, balloons, blimp, flags. Ball kids, umpire head turns. Far life animated at half rate. | Ghost of Tsushima wind; Strikers half-rate crowd |
| **Weather as event** | Drama, then relief | Golf plays through weather. Tennis weather wraps around play: arrival, between games, after the match. A material wetness value, one rain layer, lightning pulse plus thunder, clearing plus rainbow. Audio from the same values. | Sky's rain arc; Lagarde wetness; Mario Golf Wildweather |
| **Craft at reading distance** | "So detailed", without noise | Big value bands that tell the match story: mow stripes, baseline wear, clay scuffs swept between sets, crisp lines, a bright net band. No micro-grain. | Top Spin 2K25; acuity maths in note C §3.1 |
| **Party on the players** | Excitement | Contact bursts, trails, confetti, a crowd wave on a big point. Chat 8's event bus and budgets. | Odyssey: realistic world, cartoony actions |

## 3. First make room where the budget is tight

FEASIBILITY.md measured every venue. On an **iPhone 17 Pro** today's venues appear to leave 5–8 ms of GPU headroom (estimate, ±40 %), enough for the majestic layer. There are two exceptions:
- **Golf weather** roughly triples a golf frame's per-pixel cost (+3 ms on the M5, ~+5 ms on a 17 Pro at peak).
- **Hole 12** submits 5.5 M triangles per frame.

On the **iPhone 15/16** and in **two-player split screen** (the scene drawn twice) the budget is tight to over. Golf weather on an iPhone 15 is estimated at ~15 ms before any majestic layer.

Where the frame goes today:
- 1–2.5 M triangles per frame (golf median 2.2 M, hole 12 5.5 M);
- **two tennis characters ≈ 1.06 M of that** (~0.53 M each including their shadow pass, against AGENTS.md's 35–50 k per base);
- 180–380 draw calls;
- a 4096 shadow map with 25–134 casters;
- full-screen weather volumes on top.

The majestic look is affordable everywhere only if we **spend less on what doesn't read and more on what does**. The changes are ordered by expected gain per effort. The ms figures are estimates scaled from the Mac to an iPhone 17 Pro at peak, roughly ×1.5 on the iPhone 15/16 and in split screen.

| # | Make-room change | Why (measured) | Expected saving |
|---|---|---|---|
| R1 | **Character triangle budget + distance LOD.** Garments, hair and heads get LOD1/LOD2 for the far player and a light shadow-pass mesh. | Two tennis characters ≈ 1.06 M submitted triangles per frame (79–83 % of Skyscraper and Volcano frames); a golfer ≈ 0.54 M. | 0.5–1.5 ms; doubles in split screen |
| R2 | **Shadow casters: heroes, ball, racket/club, net and a few props only.** Bake the rest (lightmaps or baked AO); shadow map 2048 with tight distance. | Shadow pass 0.35–0.5 M triangles (1.9 M on hole 12), 25–134 casters; ~1.5 ms CPU+GPU on the Mac (median). Mario Kart World does the same. | 0.5–1.5 ms, plus render-thread time |
| R3 | **Golf hole triangle diet**, starting with hole 12 (5.5 M submitted triangles) and the 2.5–3.3 M holes (13, 17, 19). Course-wide LOD/HLOD, distant terrain decimated, foliage instanced. | Golf median 2.2 M; hole 12 is 2.5× the median and ~1.1 ms more than hole 8 on the Mac for geometry. | 1–2.5 ms on heavy holes |
| R4 | **Weather drawn inside the materials**, not as full-screen volumes. Wetness, snow and ash cover become a global value in turf, court and stone shaders, and fog lives in-shader. Only the rain layer and particles stay as overlays. | Measured: the golf weather view adds **~+3 ms pixel GPU on the M5** (repeated in all 6 golf weather slots across two runs) from three blended full-screen depth-reading passes. Pikmin 4 and Mario Tennis Fever drop on exactly this. | **3–4 ms in golf weather** (the biggest single item) |
| R5 | **Depth texture only where needed.** The pipeline asset requests `_CameraDepthTexture` every frame; keep it only on cameras or passes that read it. | Unity: depth/opaque copies have "a large impact on mobile". | 0.3–1 ms |
| R6 | **HDR format check.** Use RGB111110 or LDR plus a LUT if bloom allows. Keep 4× MSAA (cheap on-chip). | Halves colour bandwidth. | 0.3–0.8 ms |
| R7 | **Device measurement harness.** Metal HUD plus an `xctrace` GPU trace on an iPhone 17 Pro and an iPhone 15, a 20-minute heat soak per venue, and thermal tiers via Adaptive Performance's Apple provider. | No device frame time has ever been recorded for this project. | Turns the estimates into facts |

## 4. Frame budget for the majestic version

Target: **11 ms GPU at room temperature on the iPhone 17 Pro (A19 Pro)** for a heaviest-case match frame, so a heat-soaked phone still makes 16.6 ms. Older Pro phones get the thermal/older tier (§7).

| Bucket | Budget (ms, A19 Pro) | Contents |
|---|---:|---|
| Characters (2–4 visible) + shadow map | 3.0 | LOD'd heroes; shadow casters per R2 |
| Court / course ground + near props | 2.0 | Baked light, in-shader fog, cloud shadows, wetness, wind sway |
| Mid + far scenery + landmark + sky + clouds | 1.5 | Chat 2's sky LUT, impostor rings, distant scenery shader, cloud cards |
| Life (crowd, critters, flags, water) | 1.0 | Instanced, half-rate far animation |
| Transparents (weather layer, VFX, trails) | 1.5 | Weather ≤ 1.0 ms; contact VFX bursts |
| MSAA 4× + post (bloom ¼-res, LUT grade) | 1.5 | One post pass |
| Headroom (spikes, AirPlay encode, UI) | 0.5 | |
| **Total** | **11.0** | Two-player split screen uses the same total (see §7) |

Triangle budget: **≤ 1.5 M submitted per frame**, including the shadow pass (≤ 300 k for two characters). Draw calls **≤ 300**, SetPass **≤ 120**. Today: tennis 1.3–2.5 M, golf 1.4–5.5 M, 180–380 draws.

## 5. Technique list with cost

Costs are for an A19 Pro at 1080p. **EST** = estimate from the research, not measured on our device.

| Technique | Where | Cost (EST) | Notes |
|---|---|---|---|
| Global wind (`_WindDir`, `_WindStrength`, `_Gust` world noise) | All venues; = golf gameplay wind | <0.2 ms | Grass, palms, flags, bunting, net sag, crowd sway, cloud drift, leaf/petal particles. Extends `GolfWindSway`/`_HubWind` into one shared global. |
| One time-and-weather controller (0–1 hour curve plus weather state) driving sun colour, ambient, fog, grade, wetness, wind and audio | Everywhere | ~0 | Feeds chat 2's `RenderedSky` LUT and chat 8's audio mixer. Skips the dull hours. |
| In-shader height/distance fog + aerial perspective toward the sky LUT | Every world shader | ~0 | Replaces full-screen fog volumes. The ball, players and lines are excluded or capped at ≤15 %. |
| Hero landmark + impostor/distant-scenery rings | Each venue | 0.3–0.6 ms | Chat 2 builds `DistantScenery`; this proposal names the landmark per venue (§6). |
| Projected cloud shadows (world-XZ scroll) | Ground shaders | 0.1–0.2 ms | Must multiply baked light too. Follows chat 2's cloud cards. |
| Material wetness (porosity darkening, gloss up, puddle mask + ripple flipbook near camera) | Court, turf, stone | 0.2–0.4 ms | Replaces `WeatherGround` overlay. Dry-out: the worn line dries first, puddles last. |
| Rain: one camera-attached cylinder/cone layer + ≤ 400 near streaks outside the ball corridor + 20/40/60 splashes | Golf in rain; tennis between games | 0.4–0.8 ms | Instead of 2,600 particles. Video gate, since rain can't be judged in stills. |
| Lightning: sun pulse + direction swing + sky flash + 2–4-frame bolt + thunder at d/343 s | Storms | ~0 | Clamp exposure; ≤ 3 flashes per second. Existing `LightningBolt` kept. |
| Snow/ash cover: up-facing mask in materials | Frostbite Fjord, Magma Open | ~0.1 ms | Lines stay clear. |
| Mow stripes (view-dependent), baseline/approach wear by match progress, clay scuff trail map (256–512² RT), swept between sets | Courts, fairways, greens | 0.1–0.3 ms | Tells the match story at TV distance. |
| Instanced crowd: 2–4 baked VAT loops, per-instance colour/phase, `_CrowdExcitement`, half-rate update; umbrellas/towels in rain | Tennis stands, golf gallery at greens | 0.5–1.0 ms | Extends `TennisStandsCrowd`'s instanced submission. |
| Critters and vehicles: gull flocks, boats, hot-air balloons, blimp, kites | Per venue | 0.1–0.3 ms | 1–2 draw calls each, vertex-animated. |
| Stylised water: baked depth ramp, scrolling normals, sky-LUT reflection, shore foam | Resort, golf coasts, lava | 0.3–0.8 ms | No opaque or depth texture copy. |
| Light-shaft cards | Storm breaks, temple, volcano | 0.1–0.3 ms | Not radial blur. |
| Bloom ¼-res Dual + one LUT grade | Global | 0.6–1.0 ms | Already in TennisPost; tune it, don't add passes. |
| Tilt-shift DoF | Intros, flyovers, replays only | 0.8–1.5 ms | Never on the play camera. |
| Thermal tiers (Adaptive Performance, Apple provider) | Global | — | Serious: cloud shadows off, crowd at ⅓ rate, bloom −2 iterations, rain layer only. Critical: MSAA 2×. **Never** below 1080p or 60. |

## 6. Per-venue ideas

Each venue gets one signature hour, one landmark, one living thing and one weather moment. Chat 2 owns how the sky and far scenery are rendered; these are art-direction asks for it and for the venue passes.

**Tennis**
- **Resort (Archipelago):**
  - *Hour:* late-afternoon gold.
  - *Landmark:* the karst towers (chat 2 is building them) plus a lighthouse on the headland.
  - *Life:* sailboats crossing, gulls, palm fronds and pennants on the wind, a crowd wave on set point.
  - *Weather:* a tropical shower between games. The court darkens and shines, awnings drip, umbrellas pop up in the stands, the next game opens on a drying court and a rainbow over the bay.
- **Skyscraper (rooftop):**
  - *Hour:* blue hour as the city lights come on.
  - *Landmark:* the Saucer Tower.
  - *Life:* a blimp with the score, searchlights, window lights flickering on, helicopters.
  - *Weather:* wind gusts in the flags and cloud sea, and a lightning storm across the distant towers. Lightning stays out of the court.
- **Volcano:**
  - *Hour:* dusk with lava glow.
  - *Landmark:* the cone erupting on match point.
  - *Life:* ember drift, steam vents, lava falls (already there, now on the global wind).
  - *Weather:* ash fall between games and a post-match eruption. Embers keep their colour rule (green < 0.4 × red) so they never read as a second ball.

**Golf**
- **Cliffside** (Cliffside, Needle, Split, Island Carry, The Steps):
  - *Hour:* morning sea light.
  - *Landmark:* one lighthouse visible from every tee (the Wii Sports Resort rule).
  - *Life:* whales or dolphins breaching off Island Carry, kites, boats.
  - *Weather:* sea fog that fills the low ground (already there), wind told through whitecaps.
- **Wild Isles** (The Spiral, Witch's Lair, Frostbite Fjord, Mesa Canyon, Temple Falls, Windmill Links):
  - *Hour:* varied by hole, with mist at Temple Falls.
  - *Landmark:* a tall waterfall or temple seen across the course.
  - *Life:* windmill sails turning with the real wind, birds in flocks, falling-leaf particles.
  - *Weather:* snow settling on Frostbite Fjord, a rain storm that clears to a rainbow ring.
- **Magma Open** (Crater, Volcano Rim, Obsidian Slab, Ember Causeway, Caldera Crown):
  - *Hour:* night-into-dawn glow.
  - *Landmark:* the caldera.
  - *Life:* lava bubbles, ember wind.
  - *Weather:* ash and eruption flashes as the "lightning" of this course.
- **Plaza hub:**
  - Golden hour.
  - Fix the sun-disc cheat (disc at az 21° vs light at az 176°) with chat 2's sky.
  - Fountains and flags on the global wind; the clubhouse clock tower as the landmark.

## 7. Online, split-screen and AirPlay notes

- **Weather that changes visibility must be identical on every client and every quality tier.** It is seeded from the session, which `DreamConditions.WeatherFor(seed, epoch)` already does. Thermal tiers may drop decoration, never fog density or rain over the play area.
- **Split screen draws the scene twice** (`TennisGame.SetSplitDisplay`). Each half has half the pixels, but the triangle and draw-call cost doubles, so the R1–R3 savings matter twice there. Split screen gets the far-layer impostors and half-rate life as defaults.
- **AirPlay:** the phone renders the 1080p TV frame and the controller UI. Keep the controller UI static or low-rate (note B §2.2 item 20). AirPlay adds ~100–200 ms of A/V latency (chat 8), so weather audio cues are timed to the TV picture, not the phone.

## 8. How this fits chat 2 (backgrounds) and chat 8 (VFX/audio)

- **Chat 2 (rendered backgrounds) owns the sky, clouds, distant scenery and reflections.** This proposal **consumes** its outputs:
  - its sky-view LUT becomes the single source of fog, ambient and aerial-perspective colour;
  - its cloud cards drift on the global wind and darken the ground through the projected cloud-shadow texture;
  - its `DistantScenery` carries each venue's landmark.
  - **Ask:** keep cloud cards within the transparent budget (≤ 0.5 ms; they are alpha-blended), and expose the LUT and sun as globals the world shaders can read.
- **Chat 8 (VFX/audio) owns the event bus, VFX budgets and the audio mixer.** Weather audio (rain layers, gusts, thunder delay, wet bounce, clearing sting) is driven by the time-and-weather controller's values through chat 8's mixer and snapshots. Crowd reactions come from chat 8's events (`ContactMade`, `ScoreChanged`) through `_CrowdExcitement`. Contact VFX stays on chat 8's side of the transparent budget.
- **Chat 1 (60 fps) owns the frame budget and quality tiers.** §4 is a proposal for `work/frame-rate-60b/BUDGET.md`, which did not exist when this was written.

## 9. Phased plan with binary gates

Every gate is measured at ≥1920×1080. "Device" means an iPhone 17 Pro (and an iPhone 15 for the older tier) with the Metal HUD and an `xctrace` capture.

| Phase | Work | Gates (PASS/FAIL) |
|---|---|---|
| **P0 Measure for real** | Device build of the current game; GPU ms per venue on the phone and over AirPlay; 20-min heat soak on Resort and the heaviest golf hole (12); thermal-state log. | `DEVICE_BASELINE`: GPU ms and fps recorded for all 3 venues and 3 golf holes, on 2 phones. `SOAK_20MIN`: fps p1 and thermal state logged. |
| **P1 Make room** | R1–R6 from §3, R4 (weather in materials) first. | `TRIS ≤ 1.5 M` and `DRAWS ≤ 300` on every venue slot (MajesticCost harness). `DEVICE_GPU ≤ 11 ms` on the iPhone 17 Pro, and ≤ 16.6 ms sustained on the older phone, on every venue including golf weather and split screen. `LOOK_UNCHANGED`: before/after stills side by side, signed off by Adnan. |
| **P2 Shared systems** | Global wind, time-and-weather controller, in-shader fog, material wetness/snow, thermal tiers. | `WIND_COHERENT`: one video per venue where flags, grass, crowd and clouds lean the same way and the golf HUD wind matches. `WEATHER_IN_MATERIALS`: the full-screen weather volumes are gone, with Δ GPU in rain ≤ 1.0 ms on device. `TIERS`: Serious/Critical forced in Xcode keeps 60 fps and 1080p. |
| **P3 Pilot venue: Resort tennis** | Signature hour, landmark, life, crowd excitement, court story (stripes, wear), shower-between-games event + rainbow, with chat 2's sky/clouds/scenery. | `MAJESTIC_LOOK`: Adnan approves a 20 s video against the target concept video. `BALL_READ`: ball contrast ≥ 2.0:1 against every background in every weather, measured. `DEVICE_60`: GPU ≤ 11 ms, 20-min soak holds 60. `FLASH_SAFE`: ≤ 3 flashes/s. |
| **P4 Roll out** | Skyscraper, Volcano, the three golf courses, the hub; one chat per venue group. | Same gates as P3, per venue. `SPLIT_60`: two-player split screen holds 60 on device. `ONLINE_SAME`: two clients show the same weather state. |
| **P5 Weather events** | Golf full weather by course (fog, rain to rainbow, snow, ash/eruption); tennis between-games and arrival/after events; audio coupling with chat 8. | `WEATHER_VIDEO`: a 5 s clip per weather per venue where the ball is never lost for > 2 frames. `AUDIO_SYNC`: thunder after flash by d/343 s; rain loops follow intensity. |

## 10. Suggested parallel-chat split (after the 10-17 chats are integrated by chat 6)

| Chat | Owns | Depends on |
|---|---|---|
| **M0 Device perf harness** | Device build, Metal HUD/`xctrace` capture scripts, soak runs, `BUDGET.md` numbers (with chat 1) | — |
| **M1 Characters diet** | Hero/garment/hair LODs and the shadow-pass mesh (with the garment-pipeline owner) | M0 |
| **M2 World diet** | Shadow casters, baking, golf course LOD/HLOD (hole 12 first), depth-texture and HDR settings | M0 |
| **M3 Shared world systems** | Global wind, time-and-weather controller, in-shader fog, wetness/snow, thermal tiers | chat 2's LUT globals |
| **M4 Pilot venue (Resort)** | Landmark, life, crowd excitement, court story, shower event | M1–M3 |
| **M5 / M6 / M7 Roll-out** | Tennis venues; golf courses; hub | M4 approved |

M1, M2 and M3 touch different files and can run at the same time. M4 waits for them. Chat 8's event bus and chat 2's sky are prerequisites for M3 and M4, not part of this split.
