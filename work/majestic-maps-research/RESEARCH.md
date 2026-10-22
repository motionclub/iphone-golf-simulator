# Majestic maps at 60 fps: what the best-looking games actually do

Research chat 9, 2026-10-17. Research only; nothing in the game was changed.

**Question (Adnan):** can our tennis courts and golf holes feel majestic (immersive weather, gorgeous backdrops, exquisite courts/courses) in a Wii / Fall Guys / Mario way, while holding **60 fps at ≥1920×1080** on iPhone and the AirPlay TV?

**Method.** Web research only: talks, dev blogs, Digital Foundry write-ups and Apple sessions. No media was downloaded and no video was watched. Every number has a status:
- **V**: read on the cited page.
- **2nd**: comes from a press summary of the original.
- **U**: unverified.
- **EST**: our own estimate.

The full evidence, with every URL, is in three notes:
- [notes/A_mobile_benchmarks.md](notes/A_mobile_benchmarks.md): mobile games, Apple sources.
- [notes/B_switch_and_techniques.md](notes/B_switch_and_techniques.md): Nintendo games, cheap "wow" techniques on Apple tile GPUs.
- [notes/C_weather_and_court_detail.md](notes/C_weather_and_court_detail.md): weather as feeling, court and course detail at phone and TV distance.

The clickable reference board is [reference-board.html](reference-board.html). Our own measurements are in [FEASIBILITY.md](FEASIBILITY.md).

---

## 1. The short answer

The games that feel majestic **and** hold 60 on phones and Switch never get there with polygons or simulation. They get there with five cheap things:
1. **Authored light and sky.** A painted or gradient sky, one time-of-day/weather controller, and baked or faked light.
2. **Layered depth.** A near court, mid trees and stands, a far landmark, and atmosphere between the layers.
3. **Motion everywhere.** One wind moves flags, grass, crowd, clouds and particles together.
4. **Bold, simple shapes with confident colour.**
5. **Discipline about pixels.** Little alpha overdraw, expensive effects at reduced resolution, and real-time shadows only on the heroes.

The games that try the console/AAA path on iPhone (Assassin's Creed Mirage, Resident Evil Village) end up at **30 fps from a sub-720p internal image**. That is the path to avoid.

Our style (soft plastic party sports, small bounded venues, a fixed sports camera) is exactly the kind that can hold 60 with a rich look. Mario Kart World, Mario Strikers, Captain Toad, Sky and Genshin are the evidence.

---

## 2. Benchmarks: who looks majestic and how they hold frame rate

### 2.1 Mobile

| Game | Frame rate / resolution (status) | What makes it feel majestic | How it keeps frame rate | Source |
|---|---|---|---|---|
| **Genshin Impact** (Unity, heavily customised) | 60; a 120 option since v2.2 on Pro iPhones. **Sustained 30 min on iPhone 15 Pro Max: 59.1 fps average at 4.13 W, surface 48 °C** (2nd, Geekerwan via Notebookcheck). 120 does not hold. | 24 h cycle drives everything. Artist-drawn clouds turned into gradient maps lit by 2 light maps. Characters are the style anchor and the world is tuned to them. Trees have a minimum light floor so the image never goes muddy. | NPR rules instead of physics. Each grass model stores one colour that artists tint. Terrain is capped at 8 layers with a colour-tone function for variation. Colour grade is one LUT; ACES was rejected as off-style. | GDC 2021 `-JFyAdI_rO8` (Famitsu write-up, V); Unity Dojo 2021 deck (V) |
| **Honkai Impact 3rd** (miHoYo mobile deck) | mobile 60 (U) | Time of day with 8 cloud templates; billboard particle clouds. | **Reflections at ≤1/3 resolution, bloom chain at 1/4 to 1/32.** One time-of-day editor drives fog, sky and character light. | Unite Tokyo 2018 deck (V) |
| **Sky: Children of the Light** (custom Metal engine) | 30 or 60 user choice on mobile (V). No 120 on iPhone (U). | **Light is the theme.** Each realm is a time of day and a weather (morning → rain → sunset → night) mapped to an emotional arc. Tiny, simple characters so the world carries the drama. | Engine built for Metal and for battery life (Apple Design Award 2020, V). | GDC 2020 art talk (Pocket Tactics write-up, V); lighting talk short `Jm0mh5rr7Gg` (content U) |
| **Alto's Odyssey** (Unity) | display rate (U) | Sandstorms, lightning, shooting stars, lunar cycles. "How far can you simplify a form until you're left only with its essence." | 2D parallax gradient layers; the cost is fill rate, not geometry. | Game Developer "Road to the IGF" (V); `8IkQwIbvyV4` |
| **Monument Valley 1–3** (Unity) | (U) | Diorama; soft depth. | Custom direction-based flat lighting plus baked AO only. Glows and vignettes are cheap transparent cards. | MCV interview (V); `mCCC9hQm6MM` |
| **Honkai Star Rail / ZZZ / Wuthering Waves** | ZZZ and WuWa launched capped at 60. WuWa removed its beta 120 mode. | Anime spectacle in small arenas. | Fixed small arenas; MetalFX upscaling (HSR 2.0). | 2nd (see note A) |
| **AC Mirage / RE Village** (ceiling reference) | **30 fps target, often missed. ~680×300 internal → 720p** on iPhone 15 Pro (2nd, DF via summaries). RE4 reaches 60 on iPhone 17 Pro Max (2nd). | — | The anti-model: console-weight frame plus upscaling. | GSMArena (V) |
| **Brawl Stars / Clash** (Supercell) | follows device refresh on Android (U) | "Iconic simplicity": one clear idea per character, Saturday-morning-cartoon energy. | Top-down camera, chunky silhouettes, very short draw distance. | GDC "Making of a Brawler" (2nd); GDC 2023 "Modernizing Rendering at Supercell" (Vault 1028820) |
| **Fall Guys / Stumble Guys / Golf Clash / Tennis Clash / Mario Kart Tour / Eggy Party** | **No verified iPhone frame-rate data** (U) | Bright palettes, bounded arenas, broadcast camera. | Unknown; worth our own capture with the Metal HUD. | note A §5 |
| **Hello Kitty Island Adventure** | — | Team of 6. Says Apple TV is "the best place to experience it". | TV gets its own UI and controls pass. | Apple developer article (V) |

### 2.2 Switch / Switch 2 (Nintendo is the real reference for "fun majestic")

| Game | Res / fps (status) | Lesson | Source |
|---|---|---|---|
| **Mario Kart World** | 1440p docked / 1080p handheld, **locked 60, no dynamic resolution** (2nd, DF) | **Baked lightmaps. Real-time shadows only on karts and a few props. The key light never moves** even though time of day changes. Real-time cubemaps for water. Fully 3D spectators. Loose polygon placement hides LOD pop. A full day passes in ~24 min, with the dull evening-to-night stretch skipped. The team nearly cut weather because every state had to be checked for readability. | DF `8-P1tKHnWjc`; Ask the Developer Vol.18 (V) |
| **Mario Strikers: Battle League** | 1080p/60 (2nd) | **Crowd fully 3D but animated at half rate.** Pitch uses shell-texture grass. Jumbotrons use render-to-texture. No AA. | DF `wH7gRNh3rNA` |
| **Kirby and the Forgotten Land** | 30 (original) | Distant enemies animated at reduced rate. | DF via GoNintendo (2nd) |
| **Splatoon 3** | battles 60, hub 30 (2nd) | Play gets the headroom. | DF `ttfJ0rEDtj0` |
| **Link's Awakening / Echoes / DK Bananza** | fall from 60 to 30 (2nd) | **Double-buffered vsync: one late frame costs a whole interval.** Full-screen tilt-shift blur on a GPU-bound frame did it. Aim for about 11–12 ms GPU, not 16.6. | DF via Nintendo Life (2nd) |
| **Pikmin 4** | 30, drops (2nd) | Drops **when a transparent object fills the screen**. | DF `6iz5uliQN3M` |
| **Zelda BotW** (CEDEC 2017) | — | **Near/mid/far bands:** particles far, fog with vertical variation mid, occlusion particles near. Distance exaggerated. Light shafts only where there is a gap. 200+ art parameters cut to ~50. Time × weather × recolour gives ~1,440 looks from one world. | Famicast translation of CEDEC Part 5 (V) |
| **Nintendo Switch Sports** | 60 (U) | **Rejected a big pro stadium with a huge crowd** for a stylish, casual, plausible venue. Music sits under the motion sound effects. | Ask the Developer Vol.5 (V) |
| **Mario Tennis Aces** | 60 (reviews) | One gimmick per court (mirrors, passers-by), not ten small details. | Mario Wiki / reviews |
| **Super Mario Odyssey** | DRS 900p/60 (2nd) | VFX deliberately mixed: **realistic for the world** (mist, wind in trees), **cartoony for the hero's actions** (puffs, stars). | Nintendo recruit interview (2nd) |
| **Super Mario Bros. Wonder** | 1080p/60 (2nd) | Many independent parallax layers; eye-tracking characters. | DF via Nintendo Everything |
| **Wii Sports Resort** | — | **A central volcano gives the whole island one landmark seen from every hole.** | Iwata Asks (V) |

---

## 3. Cross-game patterns (the rules that come out of all of this)

**Look**
1. **Light and sky are authored, not simulated.** Gradient or painted skies, artist cloud shapes, one time-of-day/weather controller, and a fixed or faked key light (MKW, Genshin, Honkai, Sky). Mood changes are parameter lerps, not new bakes.
2. **Depth comes from layers plus atmosphere.** Near (court) / mid (stands, trees) / far (landmark) / sky, with aerial-perspective fog between them (BotW, Wonder, Alto). **One hero landmark per venue** that is visible from the play camera (Wii Sports Resort's volcano).
3. **Motion beats detail.** Flags, bunting, grass, crowd waves, birds, boats and balloons all on one wind. On a 6-inch phone at 40 cm and a 55-inch TV at 2.5–3 m, both screens are past 60 px per degree, so **single-pixel detail is invisible**. Broad value bands, silhouettes and motion read; micro-normals and paint chips are wasted (note C §3.1).
4. **Characters are the style anchor**, and the world is tuned to them (Genshin). The world is realistic-ish and calm. The hero's actions get the cartoony spectacle (Odyssey).
5. **Controlled darkness and confident colour.** Light floors so nothing goes muddy; shadows tinted, never black; one LUT grade (Genshin, Alto).
6. **Weather is a feeling and a story.** A mood arc (Sky), a reward when it clears (rainbow, birdsong), the flattering moments only (MKW skips dull minutes). Weather that changes visibility must look the same on every client (the Fortnite lesson).

**Performance**

7. **Bake static light; real-time shadows only on the heroes** (MKW).
8. **Expensive effects at reduced resolution** (bloom ¼–1/32, reflections ≤⅓, AO ½) **or amortised** (shadow cascades in rotation, one probe per frame).
9. **Background animation at reduced rate:** crowds at half rate (Strikers), distant things slower (Kirby). Never the ball, racket or heroes.
10. **Alpha overdraw is the #1 killer on tile GPUs.** Full-screen transparent layers and particle storms cause the drops (Pikmin 4, Mario Tennis Fever's racket particles U). Opaque overdraw is nearly free on Apple GPUs because of hidden-surface removal.
11. **4× MSAA is cheap on Apple tile GPUs** (resolved on-chip, memoryless) and is the right AA. FXAA blurs and costs a full pass (WWDC20 10602; Khronos sample ~3 % bandwidth).
12. **Headroom, not 16.6 ms.** One late frame on a vsynced 60 becomes a 30 fps hitch (Link's Awakening). Heat is the real budget: Genshin at 60 costs 4+ W and 48 °C after 30 min. **Plan about 11 ms GPU at room temperature** so a heat-soaked phone still makes 16.6 (EST, consistent with note B §2.3).
13. **No runtime shader compilation:** compile ahead and prewarm (Apple tech talk 111372, WWDC23 10127).
14. **Fixed camera = free culling.** A sports camera never sees behind itself (DK Bananza's dig camera fills the void with fog). Use fog and framing as culling tools.
15. **Scale effects, never resolution, under heat.** Thermal tiers cut cloud shadows, bloom iterations, crowd rate and shadow distance. Our floor forbids going below 1080p. The Unity Adaptive Performance **Apple provider** exposes thermal state; the Basic provider has no thermal API.

---

## 4. Cheap "wow" techniques ranked for our game

Costs are for 1920×1080 on an A18/A19-class GPU. All costs are **EST** unless sourced (note B §2.2 has the detail).

| Technique | Wow | Cost | Apple tile-GPU gotcha |
|---|---|---|---|
| In-shader height/distance fog + aerial tint toward the sky colour | ★★★★★ | ~free (ALU) | Every shader, including transparents and crowd, must share the same fog |
| Hero landmark + near/mid/far silhouette layers (unlit far cards, impostor rings) | ★★★★★ | cheap | Plan in the play camera; one landmark per venue |
| Baked lightmaps / AO + SH probes for heroes | ★★★★★ | ~free at runtime | Bake time; match probe and lightmap exposure |
| One global wind (`_WindDir/_WindStrength/_Gust`) → grass, flags, net, crowd, trees, clouds, particles; = gameplay wind in golf | ★★★★ | <0.2 ms | Keep it coherent (Ghost of Tsushima `d61_o4CGQd8`) |
| Projected scrolling cloud shadows | ★★★★ | 0.1–0.2 ms | Must multiply baked light in the shared shader |
| Stylised water, no planar reflection (baked depth ramp, scrolling normals, sky cubemap, shore foam) | ★★★★ | 0.3–1 ms | Avoid `_CameraOpaqueTexture` and depth copies |
| Bloom quarter-res Dual + LUT grade | ★★★★ | 0.6–1.2 ms | High-quality filtering off; skip HDR if not needed |
| Vertex-animated life (birds, boats, balloons, blimp, flags) | ★★★★ | 1–2 draw calls each | Animate offscreen-cheap; half rate far away |
| Instanced crowd with baked vertex-animation-texture loops + one `_CrowdExcitement` value | ★★★★ | 0.5–1 ms | Half-rate update; no shadows |
| Light-shaft cards (not radial blur) | ★★★ | 0.1–0.4 ms | Additive overdraw; fade near camera |
| Octahedral impostors for far trees | ★★★ | fill-bound; **can be slower than meshes** (Amplify forum: 6.4→7.3 ms) | Alpha-test breaks hidden-surface removal; distance only; alpha-to-coverage |
| Shell or card grass at court edges (Strikers) | ★★★★ | 0.3–0.8 ms | Never full-screen blade grass (Ghost-style is too expensive) |
| Tilt-shift / DoF | ★★★ | 0.8–1.5 ms | **Intro, flyover and replay cameras only** (Zelda lesson) |
| Radial-blur god rays | ★★★ | 0.6–1.2 ms | Breaks the tile pass; avoid |

---

## 5. Immersive weather on mobile (note C §2)

- **Rain cannot be seen in a still frame**; it is obvious in motion (ToyShop, SIGGRAPH 2006, V). **Weather proof must be video.**
- **Falling rain:** the cheapest is one composite layer, either a full-screen pass with several parallax depths sharing one fall direction (ToyShop) or a camera-attached cylinder/cone, which is fine for our near-level cameras. Add only a few hundred near streaks outside the ball corridor. Thousands of stretched particles are the expensive option.
- **Wetness is a parameter, not a simulation** (Lagarde, Remember Me, V): darken albedo by porosity, raise gloss, flatten normals in puddles, and dry puddles last. One global `_Wetness`, read inside the materials, is cheaper and more correct than an overlay drawn on top. **Dry-out tells a story:** the worn baseline and the approach dry first (Gran Turismo 7).
- **Splashes** 20/40/60 by intensity. **Ripples** from one tiling flipbook normal, only where water collects (Lagarde budget: the whole rain suite was ~2.8 ms of a 33 ms console frame, about 8.5 % of the frame).
- **Lightning:** a sun pulse plus a direction swing toward the strike (shadows come free), a sky flash where it strikes, a 2–4-frame bolt, then thunder at distance ÷ 343 m/s. Clamp exposure so the ball never blows out; **no more than 3 flashes per second** (WCAG 2.3.1).
- **Wind:** one vector plus noise gusts (Ghost of Tsushima). Make the golf gameplay wind visible in the world through a Beaufort-like ladder: leaves → flags → whitecaps → bent palms.
- **Fog:** height plus distance in material code or in **one** pass; fog banks on flyover cameras, thinned on the play camera; keep the play volume clear.
- **Time of day:** lerp numeric grading, sun, ambient, fog and sky from one 0–1 curve. Keep the key light nearly fixed and skip the dull minutes (MKW).
- **Characters reacting to weather** is the cheapest feeling of all (Animal Crossing rain gear). Add umbrellas in the crowd, towels on heads, shielding eyes in wind.
- **Audio from the same values as the visuals.** Three rain loops crossfaded by intensity; rain-on-surface layers (awning, stand roof, umbrellas); gust one-shots when the gust value crosses a threshold; wet bounce and footstep variants; thunder delay; birdsong and a sting when it clears. Chat 8 found the audio stack has **no mixer and only synthesised single-take sounds**, so weather audio depends on chat 8's mixer and real-layer plan.
- **Tennis is not played in rain.** Weather goes *around* play: arrival under clouds, rain on the roof between games, a drying court, a rainbow, wind in the flags, sunset. Golf can be played through full weather (Mario Golf Super Rush's Wildweather course is the precedent).
- **Readability rules:**
  - The ball always beats the background on luminance, with a ball brightness floor that ignores weather dimming.
  - Exclude the ball, players and lines from fog, or cap fog on them at ≤15 %.
  - No particles in the ball corridor.
  - No camera droplets on the play camera; they belong on cutaways only (MotoGP lesson: sample a 128×64 downsample, never the full frame).
- **Particles on iOS:** use Shuriken or instanced quads. VFX Graph needs compute and is still not out of preview for URP on mobile (Unity 17.x docs, V).

---

## 6. Court and course detail that reads (note C §3)

- **Phone and TV subtend about the same angle:** the phone ≈ 20° at 40 cm, the TV ≈ 23–27° at 2.5–3 m. Both are past 60 px/deg. The ball is ~7 px at 1080p from 15 m and about 40 % smaller on the phone, which is why it needs its trail, rim and shadow blob.
- **What reads:**
  - mow stripes (1–2 m bands, flipping with view direction);
  - wear to dirt behind the baseline, growing over the match (Top Spin 2K25);
  - clay slide scuffs and dust, swept between sets as a ritual beat;
  - crisp, bright, slightly thick lines;
  - a broad sheen toward the sun;
  - a bright net band and post silhouettes;
  - a crowd **wave** as a motion texture;
  - flags, birds, balloons, confetti;
  - ball kids running, an umpire turning their head.
- **What is wasted:** normal micro-grain, 1–2 px paint chips, per-blade grass past the near ground, crowd faces, more than 1–2 texels per screen pixel beyond ~20 m.
- **Diorama feel:**
  - courts and holes as islands with visible edges;
  - toy-block props reused at angles (Astro Bot, Captain Toad);
  - saturated, slightly lifted palettes;
  - tilt-shift only on intros and replays.
- **Nintendo adds:** one gimmick per court, readable turf, jumbotrons, life in the sky, eyes on characters, parallax depth.
- **Nintendo leaves out:** the pro-stadium mega-crowd, real-time GI, real-time scenery shadows, high-frequency texture noise, clutter, and blur on the play camera.
- **Golf:**
  - one landmark visible from every hole (Wii Sports Resort volcano);
  - slope and lie must read through value and lines (Golf Story's legibility lesson);
  - beauty doesn't replace hole identity (Super Rush review);
  - a hole intro that goes landmark → path → hazard → weather tell → hand-off.

---

## 7. Gaps

- **No verified iPhone frame-rate data** for the most direct comparables: Fall Guys, Stumble Guys, Golf Clash, Tennis Clash, Mario Kart Tour, Eggy Party. The fix is to capture them ourselves with the Metal Performance HUD on a 17 Pro.
- **No mm:ss timestamps were verified** inside any talk (no video was watched). The reference board links each video by id and gives timestamps only where a page printed chapter marks.
- **Device numbers.** Our own measurements are Mac-GPU Editor numbers scaled to iPhone; see FEASIBILITY.md. A device run (Xcode GPU capture plus a 20-minute heat soak) is the decisive next measurement.
