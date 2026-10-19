# B — Nintendo benchmarks + cheap "wow" on Apple TBDR

Research date: 2026-10-17. Method: web search + fetch only (no video watched, no media downloaded).

Labels:
- **VERIFIED-2ND**: number comes from a press write-up of a Digital Foundry (DF) or other analysis (Nintendo Life, GoNintendo, Nintendo Everything). These outlets summarise DF, and the DF video itself was not watched.
- **UNVERIFIED**: claim seen once, from a weak source, or remembered but not confirmed.
- **ESTIMATE**: my own cost estimate for A17/A18-class GPU at 1920x1080. No source gives these numbers.

YouTube ids listed below were copied from the pages that embed or link them. I did not watch the videos, so **no mm:ss timestamps are given for the DF videos**. The only timestamps are third-party chapter markers for the Ghost of Tsushima wind talk, and they are labelled as such.

Our constraints, for reference: 60 fps at 1080p or above on the TV over AirPlay, no dynamic resolution below 1080p, phone acts as the controller.

---

## Part 1 — Nintendo Switch / Switch 2 benchmarks

### 1.1 Measured resolution / frame rate

| Game | Res (docked / handheld) | FPS | Notable tech | Source / video id |
|---|---|---|---|---|
| **Mario Kart World** (S2) | 1440p / 1080p, no DRS | locked 60 (Photo Mode 30) | baked lightmaps + pre-calculated direct light; real-time shadows only on karts + some trackside; real-time cubemaps for water; fully 3D spectators; handheld drops distant LOD + cubemap res; "loose polygon placement" keeps LOD pop-in low; real-time weather | VERIFIED-2ND: [Nintendo Everything](https://nintendoeverything.com/mario-kart-world-tech-analysis-including-frame-rate-and-resolution/), [GoNintendo](https://gonintendo.com/contents/49458-digital-foundry-offers-a-tech-review-of-mario-kart-world), [Nintendo Life preview](https://www.nintendolife.com/news/2025/04/digital-foundry-digs-deep-into-mario-kart-worlds-tech-and-specs). DF preview video `8-P1tKHnWjc` (linked from Nintendo Life). A 120 fps mode was claimed in the preview but was not confirmed after launch (UNVERIFIED). |
| **Mario Kart 8 Deluxe** | 1080p / 720p | locked 60; 3–4P split-screen 30 | no AA, so pixel crawl is visible | VERIFIED-2ND: [Nintendo Wire](https://nintendowire.com/news/2017/04/20/digital-foundry-tackle-mario-kart-8-deluxe-praise-performance/). **"Background animates at half rate"**: I found no source for MK8D. UNVERIFIED for MK8D specifically. The confirmed example of this trick is Mario Strikers (next row). |
| **Mario Strikers: Battle League** | 1080p / 720p | 60 target (cutscenes 30 with uneven pacing) | **crowds fully 3D but updated at half rate**; pitch uses **shell-texture grass**; jumbotrons use render-to-texture; projected shadows; no AA; self-shadowing off in gameplay | VERIFIED-2ND: [GoNintendo](https://gonintendo.com/contents/4619-mario-strikers-battle-league-s-framerate-resolution-and-more-detailed). DF video `wH7gRNh3rNA` |
| **Mario Tennis Aces** | not found | 60 (reviews) | 10 courts; gimmick courts (mirrors, passers-by crossing the court) | No DF/VG Tech numbers found, so resolution is UNVERIFIED. Court list: [Mario Wiki](https://www.mariowiki.com/Mario_Tennis_Aces), [Nintendo Life review](https://nintendolife.com/reviews/nintendo-switch/mario_tennis_aces) |
| **Mario Tennis Fever** (S2 sequel) | "4K via upscaling" (review) | 60, dips to ~40 under heavy racket particles (review) | particle overdraw is the weak point | UNVERIFIED (review, not DF): [Senses.se](https://www.senses.se/en/review-mario-tennis-fever/) |
| **Mario Golf: Super Rush** | not found | steady 60 (reviews) | — | UNVERIFIED (Italian reviews only: [Multiplayer.it](https://multiplayer.it/recensioni/mario-golf-super-rush-recensione.html)) |
| **Nintendo Switch Sports** | not found | 60 (assumed) | Nintendo's licence list includes **AMD FSR**, so upscaling to 1080p is likely | UNVERIFIED: [VideoCardz](https://videocardz.com/newz/nintendo-switch-sports-might-support-amd-fidelityfx-super-resolution). No DF/VG Tech pixel count found. |
| **Super Mario Bros. Wonder** | 1080p native (DRS to 864p on 3D world map) / 720p | near-perfect 60 | many independent parallax layers; eye-tracking on Mario and enemies; shadows from all dynamic objects; cartoony particle system; engine shared with TotK/Splatoon 3 module tools | VERIFIED-2ND: [Nintendo Everything](https://nintendoeverything.com/super-mario-bros-wonder-tech-analysis-frame-rate-resolution/) |
| **Zelda: Tears of the Kingdom** | ~900p dynamic (drops to ~720p **while the camera moves**, restores when still) / 720p max | 30 (dips with Ultrahand, Kakariko) | FSR1 to 1080p output (UNVERIFIED-ish, single summary); praised clouds | VERIFIED-2ND: [Nintendo Life](https://www.nintendolife.com/news/2023/05/video-digital-foundrys-technical-analysis-of-zelda-tears-of-the-kingdom). DF video `BLlZBwN_-C4` |
| **Link's Awakening** (2019) | 720p portable; docked "dynamic but static in traversal" | swings 60↔30 in odd places (just outside the first hut, Mysterious Forest) | tilt-shift DoF at screen edges; DF tests showed the drops are **GPU-bound**: docked clocks in portable mode fixed almost all of them | VERIFIED-2ND: [Nintendo Life 2019](https://www.nintendolife.com/news/2019/09/hold_on_tight_as_digital_foundry_tries_to_nail_down_zelda_links_awakenings_performance_hiccups). Successor *Echoes of Wisdom* (same engine): **double-buffered vsync**, 30/60 bouncing, 720p–1080p, tilt-shift DoF at the edges ([GoNintendo](https://gonintendo.com/contents/40826-digital-foundry-offers-a-tech-analysis-of-zelda-echoes-of-wisdom)). Switch 2 patch: locked 60 at higher res. DF video `0L8GMsUtl9k` ([Nintendo Life](https://www.nintendolife.com/news/2025/06/video-digital-foundry-tests-out-switch-2s-free-switch-game-upgrades)) |
| **Splatoon 3** | DRS 1080p → ~820p + FSR1 / 720p → ~75% | **battles locked 60; hub 30** | no AA; FSR1 adds little | VERIFIED-2ND: [Nintendo Life](https://www.nintendolife.com/news/2022/09/video-digital-foundrys-technical-analysis-of-splatoon-3-on-switch). DF videos `ttfJ0rEDtj0` (analysis), `JDB-Vm4eqTk` (MP preview). S2 patch: 4K docked, 60 everywhere including hub. |
| **Kirby and the Forgotten Land** | original: 30 fps target; S2 Edition: DRS to 1440p / 1080p, SMAA | original 30, S2 60 | original **animated distant enemies/objects at reduced frame rates**; S2 Edition raises it or pushes the cutoff further out | VERIFIED-2ND: [GoNintendo (DF S2 review)](https://gonintendo.com/contents/52574-digital-foundry-offers-a-tech-review-of-kirby-and-the-forgotten-land-switch-2), [GamingBolt](https://gamingbolt.com/kirby-and-the-forgotten-land-switch-2-edition-star-crossed-world-review-delightfully-enhanced) |
| **Captain Toad** | 1080p / 720p (S2: 1440p / 1080p) | 60 | diorama levels, fixed orbit camera | VERIFIED-2ND: [Nintenderos](https://nintenderos.com/2018/06/digital-foundry-somete-a-test-y-compara-captain-toad-treasure-tracker-para-switch-y-3ds/), DF `0L8GMsUtl9k` (S2) |
| **Super Mario Odyssey** | DRS 900p → 810p (sometimes 720p) / 720p | 60 (photo mode 30; cutscenes at reduced res) | VFX deliberately mixed: **realistic** (mist, wind in trees) for the world, **cartoony** (puffs, stars) for Mario's actions | VERIFIED-2ND: [Wccftech](https://wccftech.com/super-mario-odyssey-runs-900p-60-fps-docked-mode-technical-analysis-shared/amp/), [Multiplayer.it](https://multiplayer.it/notizie/190432-super-mario-odyssey-lanalisi-tecnica-completa-di-super-mario-odyssey-da-parte-di-digital-foundry-parla-di-un-gioco-che-spinge-switch-ai-limiti.html); VFX: [GoNintendo / Nintendo recruit interview, Junki Ikeuchi](https://www.gonintendo.com/contents/4438-nintendo-on-mixing-realistic-and-cartoonish-special-effects-in-super-mario-odyssey). S2 patch: ~1800p, locked 60. A **CEDEC Odyssey talk** was not found (UNVERIFIED that one exists). |
| **Animal Crossing: NH** | S2 Edition up to 4K output from ~1440p (sources conflict) | locked 30 on both consoles | "rolling log" curved-horizon world bend (widely known, but no tech source found, so UNVERIFIED) | [Nintendo Wire](https://nintendowire.com/news/2026/01/14/animal-crossing-new-horizons-is-getting-a-sneaky-resolution-upgrade-alongside-the-release-of-the-nintendo-switch-2-edition/) |
| **Pikmin 4** | DRS up to 900p / 720p, with AA | locked 30 | Nintendo's first in-house Unreal game; drops **when a transparent object covers the screen** or when panning busy areas | VERIFIED-2ND: [Nintendo Life](https://nintendolife.com/news/2023/08/video-digital-foundrys-technical-analysis-of-pikmin-4). DF video `6iz5uliQN3M` |
| **Donkey Kong Bananza** (S2) | dynamic ~1080–1200p docked (one summary), FSR1 + SMAA | 60 target, falls to 30 (double-buffered vsync) during heavy destruction and bosses | voxel destruction; **digging camera draws only tunnels and fills empty space with brown fog**; DF called the lighting dated and the shadows noisy | VERIFIED-2ND (mixed sources): [GoNintendo](https://gonintendo.com/comments/17791), [Multiplayer.it](https://multiplayer.it/notizie/donkey-kong-bananza-promosso-da-digital-foundry-ma-con-alcune-riserve.html), [TechRadar (director quote)](https://www.techradar.com/gaming/donkey-kong-bananza-director-acknowledges-the-games-performance-issues-but-says-the-team-prioritized-fun-and-playability-first) |

### 1.2 How Nintendo keeps 60, and lessons for us

1. **Bake everything static, keep real-time light for the hero.** Mario Kart World, Nintendo's flagship 60 fps showcase, uses lightmaps and baked indirect light. Real-time shadows are limited to karts and a few trackside props, and the sun stays in one place whatever the time of day. Lesson: bake the court and course. Real-time shadows go on players, the ball, the racket or club, and perhaps a flag.
2. **Animate the background at half rate.** Strikers updates its fully 3D crowd at half rate. Kirby (original) animated distant enemies at a reduced rate. Lesson: update crowd, mascot and far-NPC Animators every 2nd frame (Unity Animator culling and `AnimatorCullingMode`, or manual `Animator.Update` with half delta). At TV distance nobody sees 30 Hz on a crowd, but everyone sees 30 Hz on the ball.
3. **Prioritise the play loop over the hub.** Splatoon 3 ran battles at 60 and the hub at 30. Our rule is 60 everywhere, but the principle holds: the heavy look-dev should go into the hub and lobby, and the match needs more headroom.
4. **Lower resolution while the camera moves, never mid-rally.** TotK drops to about 720p only while the camera moves. That is not an option for us because of the 1080p floor, but the idea is useful: costly effects (DoF, extra bloom passes) can be turned on only for static flyover or intro shots.
5. **Double-buffered vsync is the trap.** Link's Awakening, Echoes of Wisdom and DK Bananza all fall from 60 to 30 because one late frame costs a whole vsync interval. On iOS this is the same as `CADisplayLink`/`Application.targetFrameRate=60` with no headroom. Lesson: aim for ~11–12 ms of GPU time (ESTIMATE), not 16.6 ms. Link's Awakening's tilt-shift DoF plus effects overloaded a GPU-bound frame, and docked clocks fixed it. Full-screen blur is the first effect to remove when we are over budget.
6. **Transparent full-screen layers kill frames.** Pikmin 4 drops when a transparent object fills the screen, and Mario Tennis Fever drops to about 40 under racket particle storms (UNVERIFIED). This is the same alpha-overdraw lesson as on TBDR (Part 2).
7. **Cull through art direction.** DK Bananza's dig camera draws only tunnels and fills the rest with brown fog. Lesson: fog and fixed camera framing are culling tools. A tennis camera that never sees behind itself does not need anything rendered there.
8. **Clean, simple images over AA tricks.** Several 60 fps Nintendo games ship with **no AA** (MK8D, Strikers, Splatoon 3) and still look clean because of flat, low-frequency textures and big shapes. On Apple TBDR, 4x MSAA is the cheap fix for the shimmer (Part 2).

### 1.3 Nintendo talks on art and environment

- **BotW CEDEC 2017**, five talks, translated by Matt Walker: [Famicast index](https://www.thefamicast.com/2017/12/cedec-talks-translated-making-of-breath.html). Part 5, "The Art and Implementation of 3D Graphics", by Satoru Takizawa (art) and Takuhiro Dohta (programming): [Famicast Part 5](http://www.thefamicast.com/2017/12/part-5-art-and-implementation-of-3d.html). Key points (paraphrased):
  - The world is split into **near / mid / far bands**: particles at far, fog with vertical variation at mid, occlusion-based particles near. Detail is simplified with distance because drawing every plant everywhere looked cluttered.
  - **Distance is exaggerated** to make a Kyoto-sized map feel vast. The reference was mountain ranges and mist seen from a car window.
  - **Light in the air:** particles catch sunlight (moisture after rain, dust), and the team chose what reads well over physical accuracy. Light shafts appear only where there is a window or gap in branches.
  - **Tuning:** artists started with 200+ parameters and the team cut them to about 50.
  - Time × weather × recolour gave about 1,440 variants of Hyrule.
  - Part 3 covers sound design in a "breathing" world ([Famicast Part 3](http://www.thefamicast.com/2017/12/part-3-sound-design-in-massive.html)). Part 1 covers the "triangle rule" for terrain: hills hide what is behind them and draw the player on ([Gigazine](https://gigazine.net/gsc_news/en/20171004-breath-of-the-wild-design-secret)).
  - No official YouTube recording of these talks was found (UNVERIFIED). A separate "making of the ground/weather" talk title was **not found** (UNVERIFIED).
- **Splatoon ink rendering talk:** no CEDEC or GDC source found (UNVERIFIED). Do not cite one.
- **Super Mario Odyssey:** no CEDEC talk found. The VFX philosophy comes from a Nintendo recruitment interview with Junki Ikeuchi (2022), linked in the table above. The art book *The Art of Super Mario Odyssey* exists ([Mario Wiki](https://www.mariowiki.com/The_Art_of_Super_Mario_Odyssey)).
- **Nintendo Switch Sports — "Ask the Developer" Vol. 5** ([Nintendo SG, part 3](https://www.nintendo.com/sg/interview/as8s/03.html)):
  - Art director Junji Morii explains that a **big pro stadium with a large audience was rejected**. So were a college sports ground and an ancient Olympic stadium.
  - Spocco Square is an "imaginary but plausible" sports complex modelled on a renovated port-town warehouse district: a stylish, casual gym players would want nearby.
  - Music seems to come from speakers by each venue and is kept below the motion sound effects.
  - Sportsmates need 650+ motions, against about 30 per Mii in Wii Sports.
  - Yamashita says the team avoided flashy design in favour of continuity.

### 1.4 What Nintendo-style sports games ADD and what they LEAVE OUT

**Added (observed):**
- **Crowds**: Strikers and Mario Kart World use fully 3D crowds. Strikers updates them at half rate. Lesson: low-poly instanced spectators with 2–3 looping cheer clips, plus a reaction burst on a point won.
- **Jumbotron / screens**: Strikers uses render-to-texture. Lesson: a low-res RTT at 15–30 Hz, or a canned flipbook (cheaper).
- **Readable turf**: Strikers' shell-texture grass gives a pitch that is a flat colour from far away with fuzz up close. Line paint is bright and wide, and the court reads as a graphic shape.
- **Themed and gimmick courts** (Aces: mirrors, passers-by). Each venue has one memorable idea, not ten small details.
- **Sky life and weather** (Mario Kart World real-time weather; BotW light-catching particles; TotK clouds).
- **Faces and eyes**: eye tracking in Wonder. At TV distance the eyes and the silhouette carry the charm.
- **Parallax depth** (Wonder: many independent layers). This is our far backdrop rings.

**Left out (observed or inferred):**
- **Big pro-stadium atmosphere** (Switch Sports rejected it on purpose for a casual mood).
- **Real-time GI and time-of-day lighting** during play (MKW keeps the sun fixed).
- **Real-time shadows on scenery.**
- **AA in many titles.**
- **Noisy high-frequency texture detail.** Inferred, as I found no source: Nintendo surfaces read as flat colour areas with soft gradients.
- **Clutter**: BotW's lesson that drawing every plant everywhere looked bad.
- **Complex DoF in the play camera.** The Zelda tilt-shift was the effect that hurt.

**Readability at TV distance (my recommendations, not sourced):**
- Character silhouettes should hold at about 8–12% of screen height.
- Use a value contrast step of 2 or more between court surface, lines and characters.
- Keep saturated colour for the characters, the ball and the interactive props. The world gets lower chroma and lighter values with distance (aerial perspective).
- Crowds should be a texture of colour, not individuals.
- One landmark per venue, visible from the gameplay camera.

---

## Part 2 — Cheap "wow" on Apple TBDR (A17/A18, Metal, Unity 6 URP)

### 2.1 Core TBDR facts (Apple WWDC20 "Harness Apple GPUs with Metal", `wwdc2020-10602`)

URL: https://developer.apple.com/videos/play/wwdc2020/10602/

- **Render passes:** each pass bins geometry, then shades per tile in on-chip tile memory. Load and store actions run once per tile. Clear instead of load, and store only what you need.
- **Hidden surface removal (HSR)** removes opaque overdraw regardless of draw order. **Alpha-blended** geometry forces HSR to flush the pixels under it, and **discard / alpha-test / depth-writing shaders** send work back to HSR. Submit opaque, then alpha-test, then transparent, and do not interleave them.
- **MSAA:** samples live in tile memory and are resolved when the tile is flushed. The MSAA texture can be **memoryless**, and only edge pixels are shaded per sample. This is why 4x MSAA is cheap on Apple.
- **Programmable blending / framebuffer fetch:** a shader can read the current pixel from tile memory, so fog, grading or deferred lighting can be merged into the same pass with no intermediate store or load.
- **Memoryless render targets** use no memory at all.

Unity links for these:
- `RenderTexture.memorylessMode` / `RenderTextureMemoryless.MSAA`: memoryless on iOS/tvOS Metal only ([docs](https://docs.unity3d.com/ScriptReference/RenderTextureMemoryless.MSAA.html)).
- URP Render Graph **native render pass merging** and **`SetInputAttachment` framebuffer fetch** on Metal and Vulkan ([docs](https://docs.unity3d.com/Manual/urp/render-graph-framebuffer-fetch.html)). The Render Graph Viewer shows the merge bar and the reasons a pass broke.

Other Apple sessions:
- **`wwdc2021-10148`** "Optimize high-end games for Apple GPUs" (https://developer.apple.com/videos/play/wwdc2021/10148/): shader permutations instead of branches, **half precision** (cut an AO shader by more than 1 ms, ~30%), lossless compression lost through `ShaderWrite`/`PixelFormatView` flags, fast-math on, avoiding redundant binds.
- **`wwdc2023-10127`** "Optimize GPU renderers with Metal" (https://developer.apple.com/videos/play/wwdc2023/10127/): function constants over uber-branches (demo: material pass 58 → 12.5 ms), async pipeline compilation to avoid hitches.
- **Tech Talk `111373`** "Learn performance best practices for Metal shaders" (https://developer.apple.com/videos/play/tech-talks/111373/): covers **A17 Pro / M3 (Family 9)**. Use `half`, and the `h` literal suffix matters. Float/half conversion is free.
- **`wwdc2019-422`** "Designing for Adverse Network and Temperature Conditions" (https://developer.apple.com/videos/play/wwdc2019/422/): `ProcessInfo.thermalState` and the Xcode **Device Conditions → thermal state** simulation.
- `wwdc2023-10123` "Bring your game to Mac, Part 1" and `wwdc2024-10089` "Port advanced games to Apple platforms" are about porting. They are mostly useful for the Metal Performance HUD and Instruments workflow.

### 2.2 Techniques with costs

GPU numbers are for 1920x1080 on an A17/A18 class GPU. Every ms figure is an **ESTIMATE** unless a source is named; no public source gives per-effect ms at this target. For scale, the full frame at 60 fps is 16.7 ms, and the sustained budget I suggest is about 11 ms of GPU time (ESTIMATE, for thermal headroom).

1. **Baked lighting + light probes / APV.** Wow: very high (soft bounce light and AO is what makes plastic look expensive). Cost: lightmap fetch ≈ free; legacy light probes are per-object SH (free); **APV** samples per pixel (small ALU + 3D texture fetch). Unity lists APV as a mobile feature but gives no numbers ([Unity 6 mobile](https://unity.com/en/resources/mobile-game-optimization-in-unity-6)). A forum thread reports leak issues ([thread](https://discussions.unity.com/t/adaptive-probe-volume-urp-leaks-other-weird-behaviors/1547559)). ESTIMATE: APV +0.2–0.5 ms over SH probes. Recommendation: lightmaps for static objects, SH probes for players. Use APV only if probe density gives a visible gain on characters.
2. **Stylised gradient sky** (3-colour vertical gradient + sun disc + painted cloud layer on a dome). Wow: high. Cost: cheap, ~0.1–0.3 ms (ESTIMATE). Draw it **after opaques** so HSR/early-Z rejects covered pixels, and keep it opaque.
3. **Height / distance fog + aerial perspective.** Wow: very high (BotW's mid-band fog; DK Bananza used fog as culling). Cost: about free when computed in the lit and unlit shaders (a few ALU). A separate full-screen fog pass costs more (ESTIMATE 0.3–0.6 ms) unless it is merged through framebuffer fetch. Gotcha: alpha objects need the same fog function or they glow.
4. **Hero landmarks + silhouette layering** (near court / mid trees + stands / far hills / sky card). Wow: highest for the cost. Cost: cheap, since far layers are a few hundred triangles of unlit tinted cards. Follow BotW's near/mid/far rule and Wonder's parallax layers.
5. **Impostors / billboards (Amplify Impostors, octahedral).** Wow: medium (lets a forest exist). Cost: low vertex cost but **fill and alpha-test cost**. Amplify's own forum has a case where 3,000 plant meshes became octahedral impostors and triangles fell from 1.7M to 375k, yet frame time went *up* from 6.4 to 7.3 ms on a GTX 1060 ([Amplify forum](https://forum.amplify.pt/viewtopic.php?p=4215)). TBDR gotcha: alpha-tested impostors break HSR. Use them only beyond about 60 m, keep them small on screen, use hemi-octahedral for high cameras, and **use alpha-to-coverage with MSAA** rather than many overlapping blended cards.
6. **Vertex-animated foliage / flags / water (sine wind or VAT).** Wow: high (motion makes a scene feel alive). Cost: vertex-only, cheap (ESTIMATE <0.2 ms for a whole venue). VAT costs one texture fetch per vertex plus memory. Wind reference: Ghost of Tsushima uses **one global wind vector with time-varying Perlin noise for gusts**, plus local "vorticle" disturbances, and sampling is opt-in per emitter ([Game Developer](https://gamedeveloper.com/design/using-vorticles-to-simulate-wind-in-i-ghost-of-tsushima-i-)). Talk: Bill Rockenbeck, **"Blowing from the West: Simulating Wind in Ghost of Tsushima"**, GDC 2021 ([GDC Vault 1027124](https://gdcvault.com/play/1027124/Blowing-from-the-West-Simulating)). YouTube `d61_o4CGQd8`, with chapters 00:11 intro, 04:50 particles/foliage, 12:24 grass + cloth, 15:57 GPU cloth (the id and chapters come from the [Podwise index](https://podwise.ai/episodes/1458666), a third party, so UNVERIFIED as the official upload). Grass talk: Eric Wohllaib, **"Procedural Grass in Ghost of Tsushima"**, GDC 2021 Advanced Graphics Summit ([GDC Vault 1027214](https://gdcvault.com/play/1027214/Advanced-Graphics-Summit-Procedural-Grass)). A third-party link points to YouTube `Ibe1JBF5i5Y` (UNVERIFIED as official). Takeaways for us: one shared `_WindDir/_WindStrength/_GustNoise` global drives flags, trees, grass cards and particles together, which is what reads as coherent. GPU blade-per-pixel grass is **too expensive** on mobile, so use shell or card grass at the court edges only.
7. **Cheap stylised water (no planar reflection).** Wow: high at resort and volcano venues. Recipe: depth-faked colour ramp from vertex colour or a baked depth map, a scrolling normal pair, a reflection probe or **static cubemap**, and a foam texture at the shoreline. MKW uses real-time cubemaps for water, but a static one is fine for us. Cost: ~0.3–1 ms depending on screen coverage (ESTIMATE). Gotcha: avoid the `_CameraOpaqueTexture` / depth texture copies. Unity says render-texture copies have "a large impact on mobile" ([URP performance](https://docs.unity3d.com/Manual/urp/understand-performance.html)). Bake the depth instead. Reference project: Unity's open-source BoatAttack URP demo (not re-checked this session).
8. **Cloud shadows (projected scrolling texture).** Wow: medium-high (moving light makes still scenery look alive). Cost: one extra texture sample in the lit shader using world XZ. Cheap, ~0.1–0.2 ms (ESTIMATE). Gotcha: it must also darken baked-lit surfaces, so multiply it in the shared shader, not as a decal.
9. **God rays / fake volumetrics.** Two options:
   - **(a) Light-shaft cards**: additive, soft-edged, camera-faded. Cost scales with **overdraw**, so keep them thin and few. ESTIMATE 0.1–0.4 ms.
   - **(b) Screen-space radial blur**: needs the resolved scene colour, which **ends the tile pass** and adds a store, a load and a full-screen pass. ESTIMATE 0.6–1.2 ms at half resolution.

   On TBDR, prefer (a). BotW used shafts only where there is a gap.
10. **Bloom + colour grading (URP).** Wow: high (soft glow = toy plastic). Unity's advice: High Quality Filtering off, **Downscale = Quarter**, low Max Iterations; "Dual" filter is the faster mobile option and "Kawase" the fastest at low resolution ([URP Bloom docs](https://docs.unity3d.com/Manual/urp/post-processing-bloom.html)). Unity gives no ms numbers. ESTIMATE: quarter-res dual bloom 0.4–0.8 ms; LUT grading + vignette in the uber pass 0.2–0.4 ms. Turn off HDR if it is not needed (Unity's guidance), or use RGB111110 to halve bandwidth.
11. **Wind system:** see 6. Cost: one global constant buffer, effectively free.
12. **GPU instancing / SRP Batcher / GPU Resident Drawer (Unity 6).** SRP Batcher is CPU-side and always on. The **GPU Resident Drawer requires Forward+** and a compute-capable API (Metal qualifies); objects that do not qualify silently fall back ([URP docs](https://docs.unity3d.com/6000.3/Documentation/Manual/urp/gpu-resident-drawer.html)). Wow: indirect (allows dense crowds and props). Cost: saves CPU; Forward+ has a small GPU cost for tiled light lists (ESTIMATE 0.2–0.5 ms). Gotcha: verify in the Frame Debugger on device.
13. **LOD / HLOD.** Cheap and essential. MKW handheld cuts distant LOD and cubemap res, and "loose polygon placement" hides pops. Merge far stands and buildings into one HLOD mesh per venue quadrant.
14. **Occlusion culling.** For fixed sports cameras, the **camera frustum + designed sightlines** do most of the work. Baked Umbra has a CPU cost and little value in an open court. Use it in the hub plaza only.
15. **Texture atlases + ASTC.** Cheap and essential: atlases cut material count (SRP Batcher works per shader variant, and atlases enable merging). ASTC 6x6 for environment, 4x4 for faces, UI and line paint (the project rule says no crunch on face textures). Lossless framebuffer compression is lost when `ShaderWrite` is set (wwdc2021-10148).
16. **Shader LOD tiers.** Medium-cheap. Two tiers keyed off **thermal state**: tier A (cloud shadows, rim, sheen) and tier B (cut those). Use `shader_feature`/function-constant style variants, not runtime branches (WWDC23 demo: 58 → 12.5 ms).
17. **MSAA vs FXAA on TBDR.** **4x MSAA is the default on Apple.** It is resolved in tile, the MSAA buffer is memoryless, and only edges are shaded per sample (wwdc2020-10602). The Vulkan sample measures **about 3% extra bandwidth** for in-tile 4x MSAA ([Khronos sample](https://docs.vulkan.org/samples/latest/samples/performance/msaa/README.html)). ESTIMATE on A17/A18: +0.5–1.5 ms depending on edge density. FXAA/SMAA is a full-screen post pass (ESTIMATE 0.3–0.6 ms) and blurs texture detail. Gotchas: avoid a separate explicit resolve, and make sure any URP pass that needs the depth or opaque texture does not force an MSAA resolve copy mid-frame.
18. **Overdraw / alpha on TBDR.** Opaque overdraw is nearly free because of HSR. **Blended and alpha-tested overdraw is the real cost**: particles, foliage cards, impostors, UI over the 3D view, and full-screen transparent layers (Pikmin 4's drops). Rule: cap full-screen-equivalent transparent layers at about 2–3 (ESTIMATE). Draw order is opaque → alpha-test → blended.
19. **Metal-specific:**
    - memoryless MSAA and depth (iOS-only Unity flag);
    - **framebuffer fetch** to merge fog, grading or decals into the main pass;
    - Render Graph pass merging (check the viewer);
    - avoid the depth texture copy unless soft particles or water really need it;
    - `half` everywhere in fragment shaders;
    - async PSO compilation and warm-up during loading screens (WWDC23).
20. **Thermal management for long sessions.**
    - iOS states are nominal / fair / serious / critical. At serious, Apple recommends cutting GPU work and using lower-quality effects ([wwdc2019-422](https://developer.apple.com/videos/play/wwdc2019/422/)). Test with Xcode Devices → Device Conditions → Thermal State.
    - Unity **Adaptive Performance Apple provider** (`com.unity.adaptiveperformance.apple`, a core package tied to the Unity 6 version) exposes thermal state and performance mode on iOS, tvOS and visionOS ([docs](https://docs.unity3d.com/Packages/com.unity.adaptiveperformance.apple@6.0/manual/index.html)). The Basic provider has **no thermal API**. Unity asks you to turn off "Adjust iOS FPS based on thermal state" when you use AP.
    - Plan: nominal/fair = tier A; serious = tier B (no cloud shadows, bloom iterations −2, crowd anim at 1/3 rate, shadow distance −30%); critical = also drop MSAA to 2x. **Never** drop below 1080p (our rule), so scale effects, not resolution.
    - AirPlay note: the phone screen shows only the controller UI, so render it at a low frame rate, or keep it static, so it costs almost no GPU.
21. **Mobile guides and talks.**
    - Unity e-book "Optimize your game performance for mobile, XR, and the web (Unity 6 edition)", Oct 2024 ([link](https://unity.com/resources/mobile-xr-web-game-performance-optimization-unity-6)); older mobile e-book ([link](https://unity.com/resources/unity-e-book-optimize-your-mobile-game-performance)).
    - Arm Mali best-practices guide ([blog](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/new-developer-guide-arm-mali-application-developer-best-practices)). Its points on tiles, MSAA and load/store also apply to Apple.
    - **Supercell**: "Modernizing Rendering at Supercell", Timo Heinäpurola, GDC 2023 ([GDC Vault 1028820](https://gdcvault.com/play/1028820/Modernizing-Rendering-at)). It covers moving Clash of Clans onto a new renderer behind an API abstraction, driven partly by Metal.
    - **Riot Wild Rift**: the only GDC talk found is pipeline tooling, "The Art of Not Reinventing the Wheel in Wild Rift Asset Pipeline" ([GDC Vault 1027061](https://www.gdcvault.com/play/1027061/)). No Wild Rift rendering talk was found (UNVERIFIED that one exists).
    - **Blizzard / NetEase Diablo Immortal**: no GDC rendering talk found. Only an Android case study on hardware ray-traced reflections ([Android dev](https://developer.android.com/stories/games/diablo-raytracing)), which is not relevant to our budget.
    - Genshin Impact's GDC 2021 talk "Crafting an Anime Style Open World" exists ([GDC news](https://www.gdconf.com/news/learn-about-making-genshin-impacts-open-world-gdc-2021)). The miHoYo rendering deck is a Unity Dojo talk ([Docswell](https://docswell.com/s/UnityJapan/KWRPQ5-210617-unity-dojo20211mihoyozhenzhongyi)).

### 2.3 Suggested frame budget for a "majestic" court at 1080p60 (ESTIMATE)

| Bucket | ms |
|---|---|
| Opaque world (baked, fog in-shader, cloud shadow, VAT wind) | 3.0–4.0 |
| Characters (2–4 heroes, skin/cloth shaders, real-time shadow map 1 cascade) | 2.0–3.0 |
| Crowd (instanced, half-rate anim, no shadows) | 0.5–1.0 |
| Sky + far layers + water | 0.5–1.0 |
| Transparents (particles, shaft cards, ball trail) | 0.5–1.0 |
| MSAA 4x overhead | 0.5–1.5 |
| Post (quarter-res dual bloom + LUT grading) | 0.6–1.2 |
| **Total target** | **≈ 8–12.5 ms**, leaving headroom for thermal throttling |

---

## Summary table

| Technique | Wow | Cost (1080p, A17/A18) | Gotchas on Apple TBDR |
|---|---|---|---|
| Baked lightmaps + SH probes | ★★★★★ | ~free at runtime | Bake time; probes for players; match lightmap and probe exposure |
| APV | ★★★ | +0.2–0.5 ms ESTIMATE | Leaks; cannot hand-place; small gain over SH for small courts |
| Gradient / painted sky dome | ★★★★ | 0.1–0.3 ms ESTIMATE | Draw after opaques; keep opaque |
| In-shader height/distance fog + aerial tint | ★★★★★ | ~free | Every shader (incl. transparents, VAT, crowd) must use the same fog |
| Landmarks + near/mid/far silhouette layers | ★★★★★ | cheap (unlit cards) | Plan it in the camera view; one landmark per venue |
| Octahedral impostors | ★★★ | fill-bound; can be slower (Amplify forum case) | Alpha-test breaks HSR; distance only; A2C with MSAA |
| Vertex wind (one global wind) / VAT | ★★★★ | <0.2 ms ESTIMATE | VAT memory; keep wind coherent across flags, trees, particles |
| GPU blade grass (GoT style) | ★★★★ | expensive on mobile | Use shell grass (Strikers) or edge cards instead |
| Stylised water, no planar | ★★★★ | 0.3–1 ms ESTIMATE | Avoid opaque/depth texture copies; bake depth; static cubemap |
| Projected cloud shadows | ★★★★ | 0.1–0.2 ms ESTIMATE | Must multiply baked light in the shared shader |
| Light-shaft cards | ★★★ | 0.1–0.4 ms ESTIMATE | Additive overdraw; fade near camera |
| Radial-blur god rays | ★★★ | 0.6–1.2 ms ESTIMATE | Ends the tile pass (store, load, full-screen); avoid |
| Bloom (quarter, dual) | ★★★★ | 0.4–0.8 ms ESTIMATE | HQ filtering off; fewer iterations; skip HDR if not needed |
| LUT colour grading | ★★★★ | 0.2–0.4 ms ESTIMATE | Merge into the uber pass; framebuffer fetch where possible |
| Half-rate crowd / distant animation | ★★★★ | saves CPU/GPU | Never on ball, racket or heroes; offset phases to hide sync |
| GPU Resident Drawer / SRP Batcher | ★★ (indirect) | CPU win; Forward+ ~0.2–0.5 ms ESTIMATE | Needs Forward+; silent fallback; verify on device |
| LOD / HLOD | ★★ (indirect) | saves | Loose silhouettes hide pops (MKW) |
| ASTC + atlases | ★★ (indirect) | saves bandwidth | 4x4 for faces, lines, UI; lossless FB compression lost with ShaderWrite |
| 4x MSAA | ★★★★ | +0.5–1.5 ms ESTIMATE (~3% BW, Khronos) | Memoryless; no explicit resolve; avoid mid-frame depth/opaque copies |
| FXAA/SMAA | ★★ | 0.3–0.6 ms ESTIMATE | Blurs detail; MSAA is better on TBDR |
| Alpha / particle overdraw | — | the #1 risk | Cap ~2–3 full-screen layers; sort opaque → alpha-test → blend |
| Memoryless + framebuffer fetch + pass merge | ★ (enabler) | saves bandwidth | Check Render Graph merge bar; Metal-only flags |
| Thermal tiers (AP Apple provider) | ★ (keeps 60) | — | Basic provider has no thermal API; never cut below 1080p; drop effects first |
| Selective DoF / tilt-shift | ★★★ | 0.8–1.5 ms ESTIMATE | Zelda lesson: blur on a GPU-bound frame + double-buffered vsync = 30 fps; intros only |
