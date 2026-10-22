# A. Mobile benchmarks: frame rate, resolution, "majestic" look, and how they keep frame rate

Research date: 2026-10-17. Method: web search and page fetches only (no browser, no downloads, no video watching).
Labels: **VERIFIED** = I read it on the cited page this session. **SECONDHAND** = only a search snippet or a summary of a summary. **UNVERIFIED** = from memory or a weak source; check it before relying on it.
**No YouTube timestamps were verified.** I could not watch videos. The only timestamps given are chapter marks printed on Apple's WWDC pages.

Our target, for reference: iPhone party tennis/golf in Unity URP, AirPlay to a TV, hard floor of 60 fps at 1920x1080 or more.

---

## 0. Headline numbers (what the ceiling really looks like)

| Game / test | Device | What was measured | Status |
|---|---|---|---|
| Genshin Impact, "very high", 30 min | iPhone 15 Pro Max (A17 Pro) | **59.1 fps average at 4.13 W**. A16 managed ~56.5 fps at 4.32 W. Surface up to **48 °C** (25 °C room, 300 nits). Source: Geekerwan, via Notebookcheck. | SECONDHAND (Notebookcheck returned 403; numbers seen in search snippets from Notebookcheck .net/.it/.org) |
| Resident Evil Village, same review | iPhone 15 Pro Max | Throttles from **~40 to ~30 fps** | SECONDHAND (same source) |
| Genshin, MetalFX on vs off | iPhone 15 Pro Max | Off: 59.4 fps, 4.2 W, 46.3 °C. On: **58.7 fps, about +0.6 W, 48.1 °C**. Sharper image, but more drops. Source: a Weibo tester, via Wccftech. | VERIFIED (wccftech.com/iphone-15-pro-max-running-genshin-impact-metalfx-enabled-results) |
| Genshin at 120 fps | iPhone 15 Pro Max | One user says it held 120 for about 3 s, then fell to 60; MetalFX made no difference. | SECONDHAND, anecdotal (discussions.apple.com/thread/255423151) |
| Assassin's Creed Mirage | iPhone 15 Pro | Locked to a **30 fps** target and often misses it, even on the default Medium. Output is **1278x590** (a quarter of the panel). Internal resolution is lower and temporally upscaled. Traversal stutter. | VERIFIED (GSMArena review) |
| AC Mirage (Digital Foundry) | iPhone 15 Pro | Internal **~680x300 → 720p** via MetalFX. 20–22 fps on High/Medium. 30 fps only on Low, dipping to 25. | SECONDHAND (Russian-language summaries of the DF video, shazoo.ru and ichip.ru; DF video id not found) |
| RE Village | iPhone 15 Pro / Pro Max | Macwelt: never 60, rarely below 30. GSMArena: about 30 or below even on lowest settings with MetalFX Performance. | SECONDHAND |
| RE4 and other AAA ports | iPhone 17 Pro Max (A19 Pro, vapor chamber) | RE4 at **60 fps with no throttling**. "Most AAA titles are still limited to 30 FPS targets." Source: a YouTuber's 10-game test, via Notebookcheck. | SECONDHAND (403 on fetch) |
| iPhone 15 Pro with a vapor-chamber mod | modded | Genshin held a steady 60. Surface temperature about 10 % lower. | SECONDHAND (Wccftech/Notebookcheck snippets) |

**Takeaway for us.** Even A17 Pro cannot hold AAA-style rendering at 60 fps. Genshin-class stylized rendering *can* average about 59 fps over 30 min, but it runs at about 4+ W and 46–48 °C surface temperature, which is the edge of comfort. iPhone 17 Pro's vapor chamber changes this somewhat (RE4 at 60 with no throttle, SECONDHAND). Our 1080p60 floor to a TV is achievable only with a stylized budget that leaves headroom for 20–30 min of heat soak.

---

## 1. Per-game notes

### Genshin Impact (miHoYo/HoYoverse, Unity heavily customized)

**FPS / resolution**
- 120 fps option added on iOS in **v2.2 (Oct 2021)**, first for iPhone 13 Pro and iPad Pro. It was the first platform above 60; the other platforms were at 60 and PS4 at 30. Patch note wording: "120 FPS option for some devices". VERIFIED (GSMArena 2021-10-14; Automaton).
- Extended to iPhone 14 Pro in v3.1. SECONDHAND (search snippet).
- MetalFX support on A17 Pro. Reported as coming in 4.1. SECONDHAND (Creative Bloq snippet).
- Sustained-load numbers are in section 0. In practice, 120 does not hold on a 15 Pro Max, and 60 holds at about 4.1–4.8 W.

**Why it feels majestic** (GDC 2021, Haoyu Cai, "'Genshin Impact': Crafting an Anime-Style Open World", https://www.youtube.com/watch?v=-JFyAdI_rO8, video id `-JFyAdI_rO8`; no timestamp verified). Points below are from the Famitsu write-up (famitsu.com/news/202107/23228135.html). VERIFIED.
- The world uses an **NPR pipeline with stylized rules**, not physical realism. The **characters are the reference** and the environments are tuned to match them.
- **There is no fixed light.** A 24 h cycle drives everything, and streetlamps at night add direct and indirect light. Characters receive ambient light and tree shadows in real time.
- **Faces** use custom light maps plus shadow masks that react to light direction, giving a bold anime face shadow. Characters and scenes use **separate render paths**. Shadow darkness and tint follow the environment colour.
- **Clouds**: artists draw cloud silhouettes and growth keyframes. A tool converts them to **gradient maps** and drives them with **two light maps (base light plus rim highlight)**. Clouds change size and colour with weather and time.
- **Terrain** blends up to 8 layers. A custom colour-tone function adds variation without extra layers. Rocks and cliffs blend 3 textures with near/mid/far looks. **Trees get a minimum light floor** so they never go too dark, plus specular tweaks for anime-style leaf shadow.
- **Mobile trick**: each grass model stores **only one colour**, and artists tint it. Grass sets are randomized to avoid repeating colour patterns.

**Rendering techniques** (Unity Dojo 2021, Zhenzhong Yi, console pipeline, docswell.com/s/UnityJapan/KWRPQ5-210617-unity-dojo20211mihoyozhenzhongyi). VERIFIED.
- There are **two pipelines**: console/PC and **mobile (the primary dev platform)**, on a heavily customized Unity. The deck says the mobile-specific optimizations are not public (low-level details under NDA).
- Console-side ideas that transfer as concepts:
  - **CSM with up to 8 cascades.** The first 4 update every frame and the rest interleave, at least once per 8 frames.
  - **Penumbra-only soft-shadow mask at 1/4 resolution**, which cut the pass from 2–2.6 ms to 1.3–1.7 ms.
  - **AO at half resolution** with bilateral upsample, plus **capsule AO for characters**.
  - **Volumetric fog under 1 ms** with temporal filtering, and god rays at half resolution.
  - Reflection probes relit at runtime from an offline mini G-buffer, **one probe per frame**, to follow time of day.
  - Colour grading in one LUT (<0.05 ms). **ACES was rejected** as off-style.

### Honkai Impact 3rd (miHoYo's mobile-first precursor; best public miHoYo *mobile* deck)
- Unite Tokyo 2018, Jack He: "From mobile to high-end PC: high-quality anime-style rendering on Unity" (docswell.com/s/UnityJapan/KWLQP5-unite-tokyo-20183rd). VERIFIED.
- **Mobile features**:
  - Planar reflection at **1/3 resolution or lower** with optional blur and Fresnel.
  - Bloom chain at **1/4, 1/8, 1/16, 1/32**.
  - Full-screen distortion as a post pass.
  - **24 h dynamic lighting with 8 cloud templates.** Cloud textures pack RGBA as shadow 1, shadow 2 and rim, with noon/afternoon/dusk/night variants.
  - **Billboard particle clouds** plus a time-of-day editor that also drives fog, skybox colour and character lighting.
  - DoF with dynamic resolution by blur size.
- **Characters**: multi-channel 2D ramps (up to 3), rim light, a vertex-colour mask that reduces face shading, and eye refraction faked by a view-dependent UV offset.
- **Outlines**: geometry/backface outlines with vertex-colour width and perspective correction; image-space outlines for scenery at constant cost.

### Honkai: Star Rail (HoYoverse, Unity)
- **MetalFX** quietly added in v2.0 (Feb 2024). SECONDHAND (TouchArcade snippet; 403 on fetch).
- Runs at Highest at 120 fps on the iPhone 15 Pro, but may thermally throttle to the mid-40s at 60. SECONDHAND (MacDirectory snippet, weak).
- GDC 2025 talk "'Honkai: Star Rail': Reimagining RPGs for Mass Audiences" (Chengnan An, gdcvault.com/play/1035480) is design-only. No HSR rendering talk found.
- Turn-based framing means small arenas and a fixed camera. That is a key reason it can afford a high per-pixel character look. (Inference, not sourced.)

### Zenless Zone Zero (HoYoverse)
- iPhone 15 Pro was **capped at 60 fps at launch (Jul 2024)**, and TouchArcade hoped for a 120 option in 1.1. SECONDHAND.
- A Brazilian iPhone 16 review saw a 120 option in settings and averaged 60 fps at 95 % stability. The phone ran very hot, but performance held. SECONDHAND.
- Engine (Unity) is UNVERIFIED this session. No rendering talk found.
- Look: urban, "trendy" style chosen to suit fast action (Tom's Hardware Italia interview, SECONDHAND).

### Sky: Children of the Light (thatgamecompany, custom Metal engine)
- **Engine**: custom engine, originally built for **Metal** first. It won the **2020 Apple Design Award** for its custom Metal engine, haptics, Game Center and spatial audio. Apple's Behind the Design article (developer.apple.com/news/?id=zm47it7t, VERIFIED) says the team built "a custom Metal engine to render Sky's ethereal scenes" while "making sure the game would perform well and preserve battery life". Development took 7 years and began in 2012 on the hardware of that era. The game ran down to iPhone 5S at launch (9to5Mac).
- **FPS**: in-game choice of **30 or 60 fps** on mobile. Official patch notes mention bugs "when graphics were set to 60 FPS on Android" (0.29.0) and boat jitter "at 30FPS" (31.5). VERIFIED via thatgamecompany help-center snippets.
- 120 fps is not on iPhone/iPad per community posts ("120fps is exclusive to PC and Macs"). UNVERIFIED.
- PC has 30/60/120 modes (Steam users say the locks are 31/61/121, with frame-pacing complaints). SECONDHAND.
- **Majestic factors** (GDC Summer 2020, "Art of Sky: Children of the Light", Yuichiro Tanabe, gdcvault.com/play/1026903, members-only):
  - **Light is the theme**, both visually and narratively.
  - Each realm is a **different time of day and weather, from morning to night**, mapped to life stages. The Valley of Triumph is the "dramatic, magic hour" sunset.
  - Architecture follows a "progression of civilisation".
  - Characters are small, masked and white-haired with a signature cape. The figures are deliberately simple so the world carries the drama.
  - Source: Pocket Tactics. VERIFIED.
- **Talks with video ids**:
  - "Dynamic Environment Lighting in Sky: Children of the Light", Oliver Castaneda. GDC 2025 or 2026; the year conflicts between pages. GDCRewind short: https://www.youtube.com/watch?v=Jm0mh5rr7Gg (`Jm0mh5rr7Gg`). The technical content was **not verified**; gamedev.net returned 403.
  - Castaneda also gave a GDC 2025 talk on applying wind forces to fur in Sky. SECONDHAND.
  - "Designing Social Play for Sky", John Hughes, GDC Summer 2020: `lZE7Vv2Opuw`.
  - "Evolving Emotional Storytelling in thatgamecompany's Sky", Jennie Kong, GDC 2019: `wQP9spsb_IQ`.
  - No public Sky cloud-rendering talk was found. Treat any claim of one as UNVERIFIED.

### Alto's Odyssey (Team Alto / Snowman, Unity)
- Built with **Unity**, because a small team without CS backgrounds needed an off-the-shelf engine. Source: Harry Nesbitt in Game Developer's "Road to the IGF". VERIFIED.
- **Majestic factors**:
  - "Dynamic lighting and weather effects like sandstorms and shooting stars", plus wind vortexes and rushing water. VERIFIED (App Store listing and official press kit).
  - "Gradually shifting lunar cycles" to suggest a living world. VERIFIED (Game Developer).
  - A minimalism/surrealism ethos: "how far can you simplify a form until you're left only with its essence". Odyssey makes "brighter, more confident use of colour".
- **How it's built**: a 2D side-scroller with layered parallax, flat colour shapes and full-screen gradient skies. Per-frame cost is mostly fill rate, not geometry. This is inferred from the look, and no technical talk was found.
- Frame rate on current iPhones: UNVERIFIED (likely display-rate).
- Interviews with ids: AppStories Ep. 45 (Nesbitt and Cash), https://www.youtube.com/watch?v=8IkQwIbvyV4 (`8IkQwIbvyV4`); "The Alto Collection" episode `71CRhxAhW3s`.

### Monument Valley 1–3 (ustwo games, Unity)
- **Technique** (MCV/Develop "Unity Focus", VERIFIED):
  - "We ended up writing all our own shaders": a **custom directional lighting model** instead of Unity surface shaders.
  - Unity lightmapping used **only for static AO**.
  - "Some hefty overdraw for **vignetting and faked volumetric glows**".
  - In effect, the faces are lit by direction-based flat colours, the soft depth comes from baked AO, and the atmosphere comes from cheap transparent cards. Almost no real-time lighting.
- MV3 launched as a Netflix exclusive on 2024-12-10 and was later removed from Netflix (Jun 2025, per Wikipedia snippet). SECONDHAND. FPS/resolution: UNVERIFIED.
- Talks/videos:
  - ustwo at Nordic Game 2014, "Making of Monument Valley in Unity": `mCCC9hQm6MM`.
  - GDC 2014 showcase: `v2T2IG5Jye8`.
  - "Building The Impossible: The Making of Monument Valley 3": `pjsLWH0mCVk`.
  - "Monument Valley 3: Blurring art and design": `5fVdC5hzaHU`.
  - The Ken Wong GDC 2015 art talk exists per snippet; its video id is not confirmed.

### Mario Kart Tour (Nintendo/DeNA)
- **v2.12.0 changed the menu screens to a max of 60 fps**. Races were "adjusted" for processing, draw distance and handling; the article does not state the race frame rate. VERIFIED (LevelUp).
- DeNA warned that phone features which raise refresh rate (Pixel/Aquos) are unsupported.
- A user-toggle 60 fps mode for races: **UNVERIFIED** (the only claim found is a 2019 beta-era French article).
- New content ended in Oct 2023. From my own knowledge; not re-verified.
- Look: a bright Nintendo palette, short city/landmark tracks, a camera-locked portrait view. No technical talk found.

### Fall Guys (Mediatonic/Epic, Unity) — mobile
- Mobile launched with the **Epic Games Store mobile debut (Aug 2024)**. **iOS is EU-only** under the DMA; Android is worldwide. Cross-play and cross-progression supported. SECONDHAND.
- iPhone FPS/resolution: **UNVERIFIED**. The only 60 fps claim is a low-quality Android blog.
- Engine: Unity, per the Unity case study "Supporting the meteoric rise of Fall Guys" (unity.com/resources/games/…, page 404 on fetch). Fall Guys also won Best Multiplayer at the Unity Awards 2020. VERIFIED (unity.com/awards/2020).
- Art intent: beans are "unathletic but ambitious", inspired by Kidrobot "Yetiguy" figures. Characters are built to be impractical for their tasks. Source: Gfinity/GGRecon. SECONDHAND.
- No shader or rendering talk found.

### Stumble Guys (Kitka Games → Scopely, Unity)
- Unity Developer Summit at GDC: "Stumbling into…" (gdcvault.com/play/1035403, members-only). It covers the console expansion while keeping the mobile cadence.
- A team of ≤7 made the original. 32 players per match, with rounds of about 1 min. Over 320 M mobile downloads (Appmagic via MobileGamer.biz). SECONDHAND.
- iPhone FPS options: **UNVERIFIED**. Player-review analysis asked for lower graphics settings, which suggests few controls existed in 2023.

### Brawl Stars / Clash Royale (Supercell)
- Brawl Stars GDC session "Making of a Brawler: Character Creation for Brawl Stars" (Fernanda Oliveira; GDC Vault). The 5 pillars are humour, nostalgia, diversity, **iconic simplicity (one clear idea, no prop pile-up)** and timeless "Saturday-morning cartoon" energy. VERIFIED (PocketGamer.biz).
- FPS: on Android it follows the device refresh rate (ROG Phone reports a constant 120). iPhone behaviour is **UNVERIFIED**.
- Clash Royale: no 60/120 fps statement found. UNVERIFIED.
- Supercell's in-house engine: UNVERIFIED this session.
- Readability lesson: top-down/three-quarter camera, chunky silhouettes, saturated team colours, very short draw distance.

### Golf Clash (Playdemic → EA) / Tennis Clash (Wildlife Studios)
- No engine, FPS or rendering source found. Engine and FPS are UNVERIFIED.
- Golf Clash: "compellingly cute turn-based" with "simple trajectory-based gameplay". EA bought Playdemic for $1.4 B. SECONDHAND.
- Both are the **direct genre comparables** for us. They hold readability through a fixed broadcast-style camera, simple turf shaders and small venue dioramas. This is an inference to check with captures.

### What the Golf? (Triband) / Sneaky Sasquatch (RAC7) / Hello Kitty Island Adventure (Sunblink)
- **What the Golf**: Apple Arcade launch title, 19 Sep 2019; crowdfunded on Fig. Physics-comedy with flat pastel shading and few lights. Engine (Unity) UNVERIFIED. Video: Utomik Developer Spotlight `hjCOuMwdSQc`.
- **Sneaky Sasquatch**: named Apple Arcade Game of the Year (CTV News; year not shown in snippet). SECONDHAND. No tech source found.
- **Hello Kitty Island Adventure**:
  - Apple Arcade Game of the Year 2023 and **ADA finalist 2024**. Made by a team of 6. Runs on iPhone, iPad, Mac and **Apple TV**.
  - The dev quote "It's stunning on Apple TV… the best place to experience it" is relevant for our AirPlay-to-TV goal.
  - The touch-first UI had to be rethought for controller and TV.
  - No engine, FPS or resolution details. VERIFIED (developer.apple.com/articles/hello-kitty-island-adventure).

### Infinity Nikki (Infold, Unreal Engine 5)
- UE5 open world. Epic's developer interview exists ("Behind the scenes of Infinity Nikki: tracing a glamorous turn to an Unreal open world"; 403 on fetch, so contents UNVERIFIED).
- Beta 3 was capped at **30 fps**, and Infold listed a **60 fps mobile option** among planned patches. Whether it shipped is UNVERIFIED.
- Minimum is iPhone 11; on Android, 8 GB RAM plus a Snapdragon 888-class chip. SECONDHAND.
- GDC 2026 (Qualcomm-presented) talk "Faster Frames, Lower Power: How Infinity Nikki Leverages Adreno High Performance Memory" (gdcvault.com/play/1036051) is Android/Vulkan only. It shows that even UE5 mobile titles live on bandwidth/tile-memory tricks.

### Wuthering Waves (Kuro, Unreal Engine 4)
- 120 fps was in the closed beta and **removed at launch (May 2024)**. Mobile options are 30/45/60. Kuro later said 120 would return "for PCs who can handle that" (1.2). **No iOS 120 confirmed.** SECONDHAND (Sportskeeda, Twinfinite, Mein-MMO).
- SI.com guide: iPad can push more frames, "but then you'll run into the ever-so-familiar stuttering found in Unreal Engine games". Shader/PSO hitches are the UE mobile risk.

### Pokémon UNITE (TiMi / The Pokémon Company)
- Switch has a 60 fps "Frame Rate: High" option. A mobile "High" frame-rate option is claimed by one guide; **UNVERIFIED**.
- Engine: UNVERIFIED.

### Ceiling and other references
- **AC Mirage / RE Village / RE4 on iPhone**: see section 0. The lesson is that the **AAA port path ends at 30 fps with MetalFX from a sub-720p internal resolution** on A17 Pro. Even A19 Pro only reaches 60 in lighter titles like RE4. These are the anti-model for a 60 fps party game.
- **Apex Legends Mobile** (shut down 2023, from memory): an "Extreme" **80 fps** mode existed only on iPhone 13 Pro/Pro Max. No 120. SECONDHAND.
- **Diablo Immortal**: 30/60 fps options. 120 fps only on Android with Pixelworks IRX hardware (vendor press release). iPhone 120 is **UNVERIFIED**.
- **Sonic Dream Team** (Apple Arcade, SEGA HARDLight): TouchArcade ran device/resolution/FPS coverage, and a 120 fps discussion appears in its HARDLight interview, but numbers were not retrieved. A reviewer saw poor fps on iPhone 13 even at 0.5x resolution. SECONDHAND.
- **Eggy Party** (NetEase, May 2022, UGC party game): engine and FPS **UNVERIFIED**. It is the closest "party" comparable in East Asia and worth capturing ourselves.
- **Not researched**: Arena of Valor, Snufkin and Grindstone (no usable sources returned).
- **Wild Rift** (bonus): Riot's job posting lists "frame time, memory, startup time, crash rate, **thermal behavior**, and device-tier quality" as the client quality bar. This is a good checklist for us.

---

## 2. Apple platform sources (primary, for the "keep 60" toolbox)

- **WWDC22 10103 "Boost performance with MetalFX Upscaling"** (developer.apple.com/videos/play/wwdc2022/10103):
  - **Spatial** upscaling gives "substantial performance gains".
  - **Temporal AA plus upscaling** gives the highest quality.
- **WWDC25 211 "Go further with Metal 4 games"** (developer.apple.com/videos/play/wwdc2025/211). Chapters as printed on the page: Upscale **2:13**, **Interpolate frames 7:17**, Ray tracing 13:50, Denoise-while-upscaling 19:25, Next steps 26:08.
  - MetalFX **frame interpolation** generates in-between frames from motion vectors and depth.
  - **Caution for us**: interpolation adds latency, and it does not satisfy a "real 60" gameplay floor. That caution is my inference.
- **Tech Talk 111372 "Bring your high-end game to iPhone 15 Pro"** (developer.apple.com/videos/play/tech-talks/111372). VERIFIED.
  - Use the **Metal Performance HUD** to see frame interval, GPU time and memory.
  - The page describes a **sustained-performance execution capability/entitlement** for steady-state rather than burst performance. Confirm the exact API name in the docs.
  - **Precompile shaders AOT** with no on-device compilation, because it is "not power efficient and can cause hitches".
  - **Render lower, then MetalFX upscale.** Spatial works on all iOS 17 devices; temporal needs A14+.
  - Scale features by GPU family (Apple9 = mesh shaders and RT), choose ASTC/BC textures, use the increased-memory-limit entitlement, and size resources with `os_proc_available_memory`.
- **WWDC21 10147 "Optimize for variable refresh rate displays"** and the doc "Optimizing iPhone and iPad apps to support ProMotion displays":
  - iPhone ProMotion runs **10–120 Hz**.
  - Apps must **opt in** (Info.plist key `CADisableMinimumFrameDurationOnPhone`, plus `preferredFrameRateRange`) to exceed 60.
  - Since iOS 15, games get **priority for 30/60 Hz**.
  - Drive animation from `targetTimestamp`, and never assume the requested rate is honoured.
- **WWDC20 ADA**: Sky won for its custom Metal engine. This shows Apple rewards an engine built for battery as well as beauty.

---

## 3. What "majestic" seems to be made of (from the sources above)

1. **Time-of-day and weather as the main art lever, not polygon count.** Genshin (24 h cycle, weather-driven clouds), Honkai 3rd (24 h, 8 cloud templates), Sky (each realm is a time of day), Alto (lighting/weather/lunar cycles).
2. **Hand-authored stylized skies and clouds.** Genshin's artist-drawn silhouettes are converted to gradient maps with base and rim light maps. Honkai's packed RGBA cloud textures and billboard particle clouds are another example. None of this uses raymarched volumetrics on mobile.
3. **Characters are the style anchor.** Genshin tunes environments to the characters. Sky, Brawl Stars and Fall Guys keep characters simple and iconic so they read at small size.
4. **Controlled darkness.** Genshin's tree light floor and ACES rejection, plus HoYo's "dirty/dark vs vivid/bright" tuning axis. Shadows get tinted by the environment and are never black.
5. **Atmosphere from cheap layers.** MV uses overdraw vignettes and fake glows plus baked AO. Alto uses parallax gradient layers. Honkai uses fog/skybox colour driven by one time-of-day editor.

---

## 4. Cross-game patterns (what majestic-and-60 fps games do and avoid)

1. **They pick a stylized lighting model and fake the expensive parts.** MV writes its own directional model with baked AO. Genshin and Honkai use NPR ramps and face light-maps. Sky uses a custom Metal engine. None ship physically-correct real-time GI on mobile.
2. **Sky and clouds are authored art, not simulation.** Gradient maps, packed RGBA cloud cards and billboard clouds give a "majestic" horizon at almost zero per-pixel cost. Volumetrics stay on console (Genshin's console fog is <1 ms on PS4, never on phone).
3. **One time-of-day/weather controller drives everything.** Fog, skybox colour, character light and cloud tint all come from it (Honkai 3rd editor, Genshin). Mood changes are cheap parameter lerps, not new lighting bakes.
4. **Expensive effects run at reduced resolution.** Reflections at ≤1/3, bloom at 1/4–1/32, AO at 1/2, penumbra masks at 1/4, DoF with dynamic resolution. Full-resolution passes are reserved for the characters and UI.
5. **Expensive updates are amortized over frames.** Interleaved shadow cascades and one reflection probe per frame. A small diorama court can update its shadow once and cache it.
6. **The cost is pushed into authoring data.** Single-colour grass tinted per instance, texture-layer count capped (8) with a colour-tone function for variation, and distance-band material swaps (near/mid/far).
7. **Characters stay iconic and simple, the world carries the beauty.** Sky's masked kids, Brawl Stars' "one clear idea", Fall Guys beans. Readability at phone distance beats per-strand detail.
8. **They offer a 30/60 choice and only add 120 on known-good devices, often later.** Genshin added 120 in 2.2 for named devices. ZZZ and Wuthering Waves launched capped at 60, and WuWa removed its beta 120. Sky stays at 30/60 on mobile. Sustained 120 does not hold even on a 15 Pro Max.
9. **They treat thermals as the real budget.** Genshin at 60 costs about 4.1–4.8 W and 46–48 °C on a 15 Pro Max after 30 min. MetalFX added +0.6 W and about 2 °C, at a slight fps loss. Steady state, not burst, is the spec (Apple's sustained-performance guidance; Wild Rift's quality bar includes "thermal behavior").
10. **They upscale instead of rendering native.** MetalFX spatial or temporal from a lower internal resolution is Apple's own advice. The HoYo titles adopted it (HSR 2.0, Genshin on A17 Pro). But the AAA ports show that upscaling cannot rescue a console-weight frame. **Avoid** that path: AC Mirage was ~680x300 internal, 30 fps target, missed.
11. **They avoid runtime shader compilation and UE-style hitching.** Apple says to compile AOT. The WuWa and iPad guides cite UE stutter. In Unity URP that means shader variant stripping plus prewarming and PSO-style tracing before the match.
12. **They avoid open-ended draw distance in the gameplay view.** HSR's turn-based arenas, Clash/Brawl top-down boards, MV/Alto dioramas and 2D layers. The "majestic" depth comes from painted far layers and a sky dome, not geometry.
13. **They design for the big screen when one exists.** Hello Kitty Island Adventure calls Apple TV "the best place to experience it". TV output deserves its own UI/controls pass, not just a mirrored phone frame.
14. **They lean on colour confidence and value control rather than post-process stacks.** Alto's "brighter, more confident use of colour", Genshin's custom LUT with ACES rejected, and shadows tinted by the environment. One LUT pass (<0.05 ms on PS4) does the grade.
15. **They profile on the device at steady state.** Metal HUD, 20–30 min heat-soak runs (Geekerwan-style), device-tier quality presets and GPU-family feature gates (Apple9 for mesh/RT) instead of one global setting.

---

## 5. Gaps / to-do if more certainty is needed
- Frame rate and resolution on the iPhone 16 Pro / 17 Pro for Fall Guys, Stumble Guys, Brawl Stars, Clash Royale, Golf Clash, Tennis Clash, MKT, What the Golf, Sneaky Sasquatch, Eggy Party and Pokémon UNITE. All UNVERIFIED. Best fixed by capturing them ourselves with Metal HUD / Xcode GPU capture on a 15 Pro and a 17 Pro.
- The Digital Foundry video ids for AC Mirage and RE Village on iPhone were not found.
- The technical content of the Sky GDC lighting talk (`Jm0mh5rr7Gg` short; full talk on GDC Vault) is unread.
- No timestamps inside any YouTube talk were verified.
