# C: Weather as feeling, and court/course detail that reads

Research notes, 2026-10-17. Scope: iPhone party tennis and golf (Unity URP 17, Metal). The phone is the controller and the game is AirPlayed to a TV. Hard floor: 60 fps at 1920x1080 or above.

**Method.** Web search and page fetches only. No video was watched and no media was downloaded.

**Labels.**
- **VERIFIED** means I read the claim on the cited page, or confirmed the video title through YouTube oEmbed.
- **UNVERIFIED** means it comes from memory or a secondary summary that I could not check.
- **Recommendation** marks a design proposal of mine. These are not sourced facts.
- **Timestamps.** I watched no talk, so I give no timestamps of my own. The only mm:ss values here are Podwise's auto-generated chapters, and they are labelled that way.

---

## 0. Ten things to take away

1. **Rain cannot be seen in a still frame.** ToyShop's notes cite the computer-vision finding that rainfall cannot easily be recognized in a single static frame but is obvious in motion (Tatarchuk, SIGGRAPH 2006, VERIFIED). So weather proof must be video, and weather must be designed in motion.
2. **The cheapest falling rain is one full-screen composite pass, not thousands of particles.** ToyShop renders several parallax layers of rain in one pass with one texture fetch. All drops share a single direction vector (VERIFIED). Particles are then kept for splashes near the camera.
3. **Wetness is a parameter, not a simulation.** Lagarde's model darkens albedo by porosity, pushes gloss toward water, and flattens normals where water collects. Puddles dry slower than the surfaces around them (VERIFIED). One global `_Wetness` value drives all of it.
4. **Lightning is a shadowed directional pulse plus a delayed thunder sound.** ToyShop pre-baked two lightning directions into an 8-bit lightmap channel that modulates the normal lighting (VERIFIED). CryEngine exposes the thunder delay and sky-flash parameters as named settings (VERIFIED).
5. **One global wind vector drives everything.** Ghost of Tsushima's Guiding Wind is essentially one vector from the hero to the goal. Its direction is constant and its strength is modulated by Perlin noise to make gusts across grass (GDC 2021, VERIFIED).
6. **Pick the flattering moments.** Mario Kart World runs a day in about 24 minutes and does not advance time evenly. The team shortened the dull evening-to-night stretch and tuned the clearest racing line per weather and time (Nintendo Ask the Developer, VERIFIED). They nearly gave up on it because of the cost of checking every variation.
7. **Use Shuriken on iOS, not VFX Graph.** Unity's VFX Graph documentation says the package is not out of preview for URP or mobile, and that it needs compute shaders and SSBOs (VERIFIED).
8. **The phone and the TV subtend almost the same angle.** A 6.1-inch phone at 40 cm spans about 20° horizontally. A 55-inch TV spans about 27° at 2.5 m and 23° at 3 m (derived). Both exceed 60 pixels per degree at 1080p, so single-pixel detail is wasted on both. What reads is broad value bands, silhouettes and motion.
9. **Surfaces should tell the story of the match.** Top Spin 2K25 leaves dust and scuffs where players slide on clay and resets the court each set. On grass, the area behind the baseline turns to dirt over a tournament (2K, VERIFIED). These are large, low-frequency marks that read at both distances.
10. **Real tennis is not played in rain.** For tennis, design weather as before, after or around play: the arrival, rain on a roof, a drying court with a rainbow, wind in flags. Golf can be played in full weather.

---

## 1. Project context (read from the repo, not changed)

The golf side already ships a weather system, from commit 7f003e1190:

- `Unity/Assets/Scripts/Game/WeatherView.cs`
- `Unity/Assets/Resources/Golf/WeatherCommon.hlsl`, `WeatherGround.shader`, `WeatherFog.shader`, `WeatherParticle.shader`

The tennis side reads it through `Scripts/Environment/WeatherDirector.cs` and `Scripts/Tennis/TennisConditions.cs`.

**What it does today:**
- **Full-screen volumes.** Three camera-centred inverted spheres (cloud dome, ground fog, wet ground). Each reconstructs world position from depth and evaluates value-noise FBM.
- **Shuriken particle caps.** Rain 2,600 (stretched), snow 3,200, ash 1,400, embers 200, splashes 300.
- **Lightning.** A LineRenderer bolt, a global `_GolfWeatherFlash` value, and thunder scheduled after the strike.
- **Wetness approach.** Wet ground is drawn over the finished picture, so course materials are never touched.

**Implications against the findings below (Recommendation):**
- **Fill rate is the likely cost.** At 1080p on a tile-based GPU, the three blended full-screen passes with depth reads are probably the main expense, more than the particle count. I have not profiled this. Measure GPU time per pass in Xcode before adding more weather.
- **Overlay wetness cannot touch the materials underneath.** It can approximate darkening and gloss, but it cannot apply Lagarde's porosity rule (metal and plastic stay bright while porous ground darkens). An optional global `_Wetness` read inside the court and terrain shaders is the cheaper and more correct long-term route.

---

## 2. Part 1: Weather as feeling

### 2.1 How shipped games use weather

**Sky: Children of the Light (thatgamecompany, mobile first)**
- **Weather as an emotional arc.** The art talk by Yuichiro Tanabe (GDC Summer 2020, GDC Vault 1026812) maps the six realms onto times and weathers: morning, day, rain, sunset, dusk, night. The progression follows a hero's journey and a human lifespan (Pocket Tactics write-up, VERIFIED).
- **Hidden Forest.** This is the rain realm. It is described as having more complex level design and emotionally complex moments that stand for adolescence (VERIFIED).
- **Rain as a pressure mechanic.** Rain steadily drains the player's light, and light blooms act as shelter that recharges it. Repairing the bridge and freeing the jellyfish stops the rain in the area (fan wiki and walkthrough, VERIFIED as fan-reported).
- **Eye of Eden storm visuals** (dark storm, falling hazards, red light): UNVERIFIED.
- **Possible tech talk.** A 2026 GDC talk, "Dynamic Environment Lighting in Sky" by Oliver Castaneda, appears in a GameDev.net listing. The page returned 403, so its content is UNVERIFIED.
- **Lesson.** Weather is a chapter of a mood arc, it has a shelter mechanic, and it ends with a reward when it clears.

**Mario Kart World (Nintendo, 2025)**
- **Time of day.** A full day passes in about 24 minutes. Time does not move evenly, so the team concentrated on the most appealing times and shortened transitions. They did not want players crossing a featured place, such as the desert, in the dull stretch between evening and night (Ask the Developer Vol. 18 Part 2, VERIFIED).
- **Weather.** It can rain or snow, and a Lightning item can trigger a sudden change. The team picked weather that would be fun to drive through (VERIFIED).
- **Readability.** Fixed time and weather made it easier to design the clearest path. Each change in brightness or light angle needed its own checks, and the team was at one point on the verge of giving up on time and weather changes (VERIFIED).
- **Music.** The jukebox switches to more relaxed arrangements in the evening and at night (VERIFIED).
- **Climate by region.** The west is drier, and a snowy mountain in the northeast serves as a landmark (VERIFIED).
- **Digital Foundry** ("Mario Kart World on Switch 2: Is This Really A Generational Leap?", YouTube `8-P1tKHnWjc`, title VERIFIED). Per Nintendo Life's summary: lighting is still largely baked, and the key light stays in the same place whatever the time of day (VERIFIED as a summary; video not watched, no timestamp).
- **Lesson.** Fake the sun. A static key light plus a grade, sky and ambient change keeps baked lighting and shadow cost fixed.

**Alto's Odyssey (Team Alto / Snowman, mobile)**
- **What sources say.** Time of day and weather change constantly, for example sunrise one moment and a sandstorm the next (iDownloadBlog review). The App Store lists dynamic lighting and weather such as sandstorms and shooting stars (VERIFIED). Ryan Cash told Red Bull the team packed surprises into weather, lighting and wildlife (VERIFIED, snippet).
- **Art analysis.** A fan analysis of Harry Nesbitt's style describes a pure-colour foreground over a tinted background, single-hue palettes per area and dark fading gradients for glare (secondary, VERIFIED as a description only).
- **Lightning specifics:** UNVERIFIED.
- **Lesson.** On mobile, weather can be mostly palette, gradient and fog changes plus a few cheap particles.

**Zelda: Breath of the Wild / Tears of the Kingdom**
- **Gameplay (fan wikis, VERIFIED as reported).** Rain makes Link slip while climbing and puts out fires. Lightning seeks out metal gear. Weather in an area changes every four in-game hours. Puddles grow with rainfall and then evaporate.
- **Design intent.** Fujibayashi said the team considered letting players control the weather and rejected it (Game Informer, via GoNintendo, VERIFIED).
- **GDC 2017 talk.** "Breaking Conventions with The Legend of Zelda: Breath of the Wild" (YouTube `QyMsF31NdNc`, title VERIFIED) covers the chemistry engine. That engine computes interactions between objects and elements such as fire, electricity and wind (Denfaminicogamer recap of CEDEC 2017, VERIFIED).
- **CEDEC 2017 sessions.** Famitsu lists reports on level design ("gravity" and "terrain"), UI, and the engineering behind the art workflow. I found no CEDEC 2017 report on rendering rain, lightning or wind on grass, so any specific technique attributed to it is UNVERIFIED.

**Ghost of Tsushima: wind as guidance**
- **The talk.** "Blowing from the West: Simulating Wind in 'Ghost of Tsushima'" by Bill Rockenbeck, GDC 2021. YouTube `d61_o4CGQd8` (title VERIFIED). Podwise auto-chapters (not watched):

  | Time | Chapter |
  |---|---|
  | 00:11 | Intro |
  | 04:50 | Particles and foliage |
  | 12:24 | Grass and cloth |
  | 15:57 | GPU cloth |
  | 21:24 | Cloth stability hacks |
  | 25:50 | Collision |

- **Wind model (Game Developer write-up, VERIFIED).**
  - Guiding Wind is a single vector from the hero to the goal. Cutscenes use one authored vector that changes with the weather.
  - Direction stays constant, and strength varies with time-varying Perlin noise. This produces gusts that sweep across grass fields.
  - Invisible "vorticles" add local swirls, gusts and blasts. Hundreds of them are summed by brute force.
  - Particles rise over terrain by sampling the height map ahead of them, with no fluid simulation.
  - The whole system costs a small fraction of PS4 compute.
- **Companion talk.** "Procedural Grass in 'Ghost of Tsushima'" by Eric Wohllaib, YouTube `Ibe1JBF5i5Y` (title VERIFIED).
- **Sound.** The ambience talk "Big World, Small Team: Designing a Scalable Ambience System for 'Ghost of Tsushima'" (Bansal and Meyer, GDC Vault 1026976/1027222) describes ambience that adapts to time, weather and region (VERIFIED, description only).
- **Lesson.** One `_WindDir` value plus a scrolling noise for strength is enough to drive grass, flags, the crowd's hair and clothes, rope, leaves and the cloud dome. If they all agree, the wind feels real.

**Racing games: puddles and drying**
- **Forza Horizon 2.** Puddles form and evaporate, filling crevices and low areas first, and they affect traction (Jalopnik preview, VERIFIED).
- **Gran Turismo 7.** Puddle positions are mapped per track. A dry line appears on the racing line while shaded and puddled areas stay wet longer, and only some tracks get rain (press coverage, VERIFIED as reported).
- **Shader parameters** for Forza or GT wet tarmac: UNVERIFIED (none found).
- **Lesson.** Dry-out is a story. The worn path (the tennis baseline, the golf green's approach) should dry first, and puddles should dry last.

**Others**
- **Animal Crossing: New Horizons.** Snow settles on grass, buildings and trees. Villagers wear rain gear. Thunderstorms are purely cosmetic (fan wikis, VERIFIED as reported). **Lesson:** characters reacting to weather is the cheapest feeling of all.
- **Fortnite.** The January 2022 update added tornadoes you can ride and lightning that gives a speed boost (press, VERIFIED). Weather became a toy, not just an obstacle. A later PC "performance mode" reduced storm visibility and angered players on console (TheGamer, VERIFIED). **Lesson for online play:** weather that changes visibility must look the same on every client.
- **Genshin Impact.** No first-party talk on its rain or wetness was found. A Habr teardown says it uses a custom Scriptable Render Pipeline, with some effects cut on mobile (VERIFIED as a third-party inference). Rain ripples and wet-ground specifics: UNVERIFIED.
- **Red Dead Redemption 2** (reference only). "Creating the Atmospheric World of Red Dead Redemption 2" by Fabian Bauer, SIGGRAPH 2019 Advances course: an integrated sky, cloud, fog and storm pipeline (existence VERIFIED, content not read). Too expensive for us; use it only for colour ideas.

### 2.2 Techniques and what they cost

**Falling rain: three options**

1. **Full-screen composite (ToyShop).**
   - Rain is a post-process pass before the final post stack, using one 8-bit rainfall texture.
   - Several depth layers fall at different speeds in a single pass with a single projective texture fetch. A "rain parallax" parameter sets the depth range of the layers.
   - All drops share one direction vector, which the notes call crucial for a consistent rainfall.
   - Drops are lit as bright refracting lenses, and the pass receives lightning brightness and direction.
   - Downsides: every pixel pays, and plain scrolling repeats visibly. ToyShop avoids repetition with per-drop randomization (Tatarchuk 2006, VERIFIED).
   - **Mobile cost:** one cheap full-screen ALU pass. On a tile-based GPU, the cost is the blend over every pixel.
2. **Camera-attached cylinder or cone of scrolling textures** (King Kong, per forum reports).
   - It is cheap. It breaks when the camera pitches up or down, because rain then appears to fall sideways or forward. Closing the top with a cone helps (gamedev.net and Panda3D threads, VERIFIED as forum reports).
   - **Fit for us:** our gameplay cameras are nearly level, so this works.
3. **Particles (current golf approach).**
   - Stretched billboards look correct from any angle and catch light, but fill rate grows with streak length and count.
   - Unity's mobile guidance: reduce particle overdraw, use the simplest shaders, prefer alpha-blend over alpha-test (legacy Unity mobile optimisation docs, VERIFIED).
   - Discard and clip stall mobile GPUs (Unity forum, VERIFIED as forum).

**Recommendation for falling rain:**
- **Hybrid.** Use one composite or cylinder layer for distant rain, plus at most a few hundred near-camera streaks that sit outside the court or ball corridor.
- **Fade near the camera.** Fade streaks within about 4 m of the lens, which the current code already does with `_Near = 4`.

**Splashes and ripples (Lagarde, "Water drop 2b", Remember Me; VERIFIED)**
- **Splash counts.** 20, 40 and 60 for light, moderate and heavy rain. Heavy splashes cost about 0.3 ms on PS3 or Xbox 360. A 256x256 depth map from the rain's direction suppresses splashes under cover.
- **Ripples.** One shared, tiling 256x256 ripple normal map, generated procedurally at about 0.15 ms. Four layers fade in, one per quarter of rain intensity. Ripples show only where water has accumulated.
- **Full rain suite.** Raindrops, splashes, ripples and camera drops cost about 2.8 ms of a 33 ms frame at 720p on PS3 or 360.
- **Comparison points.** S.T.A.L.K.E.R. used a ripple volume texture that visibly repeated, BioShock used a screen-space ripple buffer, and ToyShop used a GPU water simulation.
- **Recommendation for us:** a pre-baked ripple flipbook normal (for example 8 frames at 128²) is enough at our viewing distances. Sample it only in puddle and wet areas and only near the camera.

**Wetness model (Lagarde, "Water drop 3b", VERIFIED)**
- **Albedo darkening.** `factor = lerp(1, 0.2, (1 - metalness) * porosity)`, then `diffuse *= lerp(1, factor, wet)`.
- **Gloss.** `gloss = lerp(1, gloss, lerp(1, factor, 0.5 * wet))`. The 0.5 weight is empirical, and the change in index of refraction is ignored as too subtle.
- **Porosity without a texture.** Derive it from roughness, for example `saturate(-2.5 * gloss + 1.25)` in his engine's units. The known flaw is that rough non-porous materials also darken.
- **Thin water to puddle.** Blend toward flat vertex normals and water-like specular as accumulated water rises.
- **Drying.** Use a sigmoid or lerp over about a minute with a noise mask, and dry puddles more slowly.

**Puddle reflections without screen-space reflections (Recommendation)**
- **Reflection.** Sample the sky reflection probe or cubemap at the reflected vector. The golf WeatherGround shader already reflects a `_SkyColor`.
- **Planar reflections.** If one hero puddle needs a real reflection, render it at a quarter resolution and only in cinematics.
- **Fontainebleau.** Unity's Fontainebleau demo uses puddle decals (`DC_Puddle01_wet`) on HDRP's LayeredLit, not URP (repo listing, VERIFIED).
- **URP samples.** The URP 3D Sample's Terminal, Garden, Oasis and Cockpit scenes show night, fog, sand and water but list no rain. The Boat Attack repo is a water package. I found no rain system in either (VERIFIED by absence in the listings).
- **Apple Metal rain demo:** UNVERIFIED (none found).

**Camera droplets (Shawn Hargreaves, MotoGP, VERIFIED)**
- **Technique.** Droplet sprites hold refraction offsets in their red and green channels and sample the scene at shifted coordinates.
- **The cost trap.** About 100 droplets each sampling the full-resolution scene dropped the game far below 60 fps because of texture-cache misses. The fix was to sample a 128x64 downsampled copy instead, which restored 60 fps.
- **Per-camera tuning.** TV replay cameras get stationary drops scaled to the field of view. Bike cameras get larger, faster and more opaque drops.
- **Naughty Dog's lens drops** (Uncharted, The Last of Us Part II): no breakdown found, UNVERIFIED.
- **Recommendation:** use camera drops only on broadcast-style cutaway cameras (intros, replays, celebrations), never on the gameplay camera, where they would hide the ball.

**Lightning (ToyShop and CryEngine, VERIFIED)**
- **ToyShop.**
  - Lightning is a strong directional light that affects every object, with uniformly aligned shadows that sell a real strike.
  - Separate shadow maps per flash were too expensive. Instead the team pre-rendered the scene lit from two lightning directions into a two-channel 8-bit "lightning lightmap" that multiplies normal lighting.
  - The notes stress the sudden flash followed by the inevitable thunder, and that the flash also reveals detail that darkness would hide.
- **CryEngine 5.** The lightning entity exposes a thunder delay, sky highlight colour, multiplier and vertical offset.
- **Recommendation for our recipe:**
  1. Ramp the sun intensity up and swing its direction toward the strike for about 0.1 s, then decay over about 0.5–1 s. Shadows come free from the existing sun.
  2. Add an ambient lift and brighten the sky dome where the strike is.
  3. Show a bolt mesh for 2–4 frames.
  4. Schedule thunder at distance ÷ 343 m/s, so about 3 s per km. A close strike should crack, a far one should roll.
  5. Clamp exposure so the ball never blows out. Cap at 3 flashes in any 1-second window, the WCAG 2.3.1 photosensitivity threshold.

**Wind (Ghost of Tsushima model)**
- **Recommendation.** One global `_WindDir` (xz) and `_WindStrength`, plus a world-space scrolling noise for gusts, sampled by:
  - grass (vertex sway weighted by height)
  - flags and banners (vertex sine plus flutter)
  - net cord sag wobble
  - crowd hair, flags and scarves
  - rope and bunting
  - trees
  - cloud-dome scroll
  - leaf and petal particles (Shuriken external forces or velocity over lifetime)
- **Golf gameplay.** Gameplay wind should equal the visual wind vector, so players read wind from the world, not only from the HUD. PGA Tour 2K23 bases its wind on the Beaufort scale (2K official page, VERIFIED). A Beaufort-like ladder of visual tells (smoke, flags, leaves, whitecaps) works as a readable language.

**Fog**
- **Recommendation.** Use height fog with distance fog, applied in material code or one full-screen pass, never several stacked passes.
- **Keep the play volume clear.** Fog should start beyond the far baseline, or beyond about 60–80 % of the shot distance in golf.
- **Fog banks.** Use them for drama on approach and flyover cameras, then thin them on the gameplay camera.
- **Halos.** ToyShop got misty halos around lights with a Kawase blur post-process (VERIFIED). URP Bloom with a higher scatter in rain gives the same effect at almost no extra cost.

**Snow accumulation (Recommendation)**
- **Mask.** `snow = saturate((dot(N_world, up) - k) * s) * _SnowAmount * noise`, blended to white with raised roughness. The golf `WeatherGround` already settles snow on up-facing surfaces.
- **Tennis.** Keep the lines unsnowed, or swept as a gameplay prop.

**Time of day and sunset (Recommendation, with URP facts)**
- **URP Color Lookup** applies a LUT with a Contribution blend (Unity 6 docs, VERIFIED).
- **Blending LUTs between volumes.** Whether URP blends LUT textures smoothly between overlapping volumes is UNVERIFIED. Texture parameters may switch instead of interpolating.
- **Safer route.** Blend numeric grading (White Balance, Color Adjustments, Split Toning, Shadows/Midtones/Highlights) by volume weight. Lerp the sun colour and intensity, ambient gradient, fog colour and sky-dome gradient from one 0–1 "time" curve.
- **Mario Kart World's lesson.** Fix the key light direction, skip the dull minutes, and check every state for ball contrast.

**Particles on iOS**
- **VFX Graph.** Unity's 17.x docs say VFX Graph needs compute shaders and SSBOs, does not support OpenGL ES, and is not out of preview for URP or mobile (VERIFIED). Older forum threads report Metal compile failures with curve-based blocks on iOS 12 (VERIFIED as forum).
- **Recommendation:** use Shuriken with GPU-instanced mesh particles where possible, or one `RenderMeshInstanced` call for rain and snow quads.
- **Fill rate.** A 100x100 px particle costs four times a 50x50 one (bugnet guide, secondary). Keep particles small, short-lived and low-overlap.
- **Tile-based GPUs.** Hidden-surface removal works for opaque geometry. Blended and discard geometry loses it, so all weather overdraw is paid in full. This is general TBDR guidance; Apple's "Tailor your apps for Apple GPUs and tile-based deferred rendering" page did not render for me.
- **Starting budget (Recommendation, measure on device):** no more than 1.5 ms of GPU time for the whole weather layer at 1080p. Lagarde's 2.8 ms of a 33 ms console frame is 8.5 % of the frame. The same share at 60 fps is about 1.4 ms.

### 2.3 Coupling audio to weather

- **Lightning with thunder.** ToyShop's emotional payoff is the sudden flash followed by the inevitable thunder (VERIFIED). CryEngine ships a thunder-delay parameter (VERIFIED). Ghost of Tsushima's ambience adapts to weather, time and region (VERIFIED, description only).
- **Breath of the Wild.** Sound teams recorded more than 10,000 sounds. A sound-studies analysis notes footsteps change from a wet wooden bridge to wet grass in rain (VERIFIED as reported). Specific CEDEC sound-session details are UNVERIFIED.
- **Mario Kart World.** Music arrangements change with the time of day (VERIFIED).
- **Recommendation: drive audio from the same scalar values as the visuals.**
  - **Rain intensity.** Three rain loops (light patter, steady, downpour), crossfaded by intensity. Add rain-on-surface layers near the listener: canvas awning, stand roof, umbrellas, the golf cart roof.
  - **Wind strength.** A wind bed, plus gust one-shots triggered when the noise-driven gust value crosses a threshold. This is the same value that bends the grass, so sound and visuals line up.
  - **Wet surfaces.** Wetness switches footstep and ball-bounce sounds to wet variants. A wet bounce is a satisfying, cheap tell.
  - **Lightning.** The flash timestamp schedules the thunder. Duck crowd and music volume for about 1 s on a close crack.
  - **Clearing.** Birdsong and a musical sting when the rain clears, with a rainbow. This mirrors Sky's light-after-rain reward.

### 2.4 Gameplay readability

- **Sports precedents.**
  - **Mario Golf: Super Rush.** Wind speed and direction are always shown. Rain shortens roll. Lightning appears only on Wildweather Woods and heavy rain only on the Wildweather course (guides, VERIFIED as reported). One review noted the image going blurry while characters jump around in the rain (Stripes, VERIFIED). Avoid motion blur and rain post-processing on the gameplay camera.
  - **Golf Clash.** Wind is shown as speed and direction, and players convert it into target-ring offsets using community charts (low-quality sources; the mechanic is VERIFIED, ratios UNVERIFIED).
  - **PGA Tour 2K23.** Wind modelled on the Beaufort scale (VERIFIED).
  - **Mario Tennis Aces and Switch Sports weather:** none found, UNVERIFIED.
- **Online fairness.** Because of the Fortnite precedent, visibility-changing weather must be the same on every client and every quality tier.
- **Contrast rules (Recommendation):**
  1. **The ball always beats the background on luminance.** Keep a ball floor in its shader (an emissive minimum or rim) that does not scale down with weather dimming. Exclude the ball, players and court lines from fog, or clamp fog on them to 15 % or less.
  2. **Particles stay out of the ball corridor.** Rain streaks and snow should be thin in the volume between the players and the ball's path, and denser outside the court or fairway.
  3. **Weather never hides trajectory information.** In golf fog, the landing marker and the aiming arc stay crisp. In tennis wind, show the ball's drift with its trail, not by hiding it.
  4. **Lightning is clamped.** No full-white frames, and no more than 3 flashes per second (WCAG 2.3.1).
  5. **Gate it on video.** Capture 5 s clips per weather on both the phone and the TV output. Fail the clip if the ball is lost for more than 2 frames (Recommendation, consistent with the still-frame finding).

---

## 3. Part 2: Court and course detail that reads at phone and TV distance

### 3.1 Viewing geometry (derived; inputs stated)

**Inputs:**
- **Phone:** 6.1-inch, 19.5:9, about 460 ppi, 2556x1179. Long side about 14.1 cm, short side about 6.5 cm.
- **TV:** 55-inch, 16:9, 121.8 x 68.5 cm, at 1920x1080.

| Display | Horizontal angle | Pixels per degree | 1 px |
|---|---|---|---|
| Phone at 40 cm | ≈ 19.9° | ≈ 128 (native) | ≈ 0.47 arcmin |
| TV at 2.5 m | ≈ 27.4° | ≈ 70 | ≈ 0.87 arcmin |
| TV at 3 m | ≈ 22.9° | ≈ 84 | ≈ 0.73 arcmin |

- **Acuity.** Normal 20/20 acuity is about 1 arcmin, or 60 pixels per degree. Every case above is at or past it, so **single-pixel detail is invisible on both**. Fine normal-map grain, 1 px line wear and sub-pixel specks are spent for nothing.
- **Example (assumed camera).** A tennis ball (6.7 cm) seen from 15 m with a 40° vertical field of view covers about 0.64 % of frame height, or about 7 px at 1080p.
  - On the TV at 2.5 m: about 6 arcmin.
  - On the phone in landscape: about 3.6 arcmin.

  That is small on both, and **about 40 % smaller on the phone**. This explains why the ball needs a trail, a rim and a shadow blob. The camera values are illustrative, not the game's actual numbers.
- **Text.** Comfortable reading needs characters of roughly 20 arcmin or more. A field study implies a recommended lower limit near 22 arcmin (secondary; the exact ANSI/HFES 100 values are UNVERIFIED). On the TV at 2.5 m, 20 arcmin is about 23 px of cap height at 1080p.

### 3.2 Surfaces

**Grass: mowing stripes**
- **Why stripes exist.** Light reflects differently off blades bent toward or away from the viewer (lawn-care sources, VERIFIED).
- **Shader (Recommendation).** `stripe = step(0.5, frac(worldZ / stripeWidth))`. Shift value by ±4–8 % and roughness slightly, and flip the sign with view direction for the real "flip when you walk around" effect.
- **Reads?** Stripes are 1–2 m bands, many pixels wide, so they read on both devices.
- **Wear.** Top Spin 2K25's grass behind the baseline progressively turns to dirt over a tournament (VERIFIED). A world-space wear mask (a baseline ellipse plus the service-box T) lerps to a dirt colour. Drive it from match progress.

**Clay**
- **Scuffs.** Top Spin 2K25 kicks up dust and leaves scuff marks wherever players slide, then sweeps the court at each new set (VERIFIED).
- **Recommendation.**
  - A render-texture "trail map" covering the court, at 256–512², where slides stamp elongated scuffs. Dust puffs are a few particles.
  - Ball marks: small oval stamps on clay only. They also serve gameplay, to show where the ball landed for line calls.
  - Sweeping between sets is a lovely ritual beat (a ball kid with a drag mat).

**Hard court**
- **Paint.** Line-paint wear and rubber-scuff patches are low-contrast and fine-grained, so they mostly do not read.
- **What does read.**
  - The two-tone colour of the court surface against the surrounding area.
  - Crisp, bright lines with soft anti-aliasing.
  - A broad sheen gradient toward the sun.
  - Darker rubbery skid zones behind the baseline, as broad blotches.
- Lines must stay the highest-contrast element. Never let wetness or snow dim them.

**Ball marks on grass and hard court**
- Real marks are not visible on these surfaces.
- Use a short-lived gameplay mark (a small dust puff on clay, a faint flattened ring on grass) only where it helps line calls.

### 3.3 Net, posts and court furniture

- **Silhouette first.** The net band (white top tape) and the posts are a readable silhouette line that frames the court. Keep the band bright and slightly thick, at 1.5–2× real width.
- **Mesh.** The net mesh itself should be a low-alpha texture with mip bias. At distance it must not shimmer (moiré) on the TV. Use mipmapped alpha-blended or alpha-to-coverage grids, never a 1-px grid.
- **Wind.** The net sags and wobbles slightly with wind and on ball impact (vertex offset). This is cheap, and players notice motion.

### 3.4 Crowds and stands

**Techniques with sources**
- **Classic stadium impostors.** A crowd mesh of cards with streams for billboard UVs, ambient-occlusion UVs and per-instance colour (book chapter on stadium crowds, Taylor & Francis; abstract VERIFIED, page returned 403).
- **Polypostors** (Kavan et al., I3D 2008). 2D polygonal characters animated by displacing vertices from textures. Much less memory than image impostors (VERIFIED).
- **Geopostors** (Dobbyn et al., 2005). Switch between geometry and impostors based on the pixel-to-texel ratio, with minimal popping (VERIFIED).
- **EA's FIFA.** A Polycount thread speculated FIFA 10 used instanced low-polygon characters, not billboards. This is UNVERIFIED and not developer-sourced.
- **GPU-instanced baked animation.** Unity's "Animation Instancing" blog targets mobile by baking skinning into textures. The blog targets OpenGL ES 3.0+, and Metal support should be checked. Open-source vertex-animation-texture bakers exist, such as sugi-cho's Animation-Texture-Baker and GPUSkinning-Unity (VERIFIED). The Stadium Crowd Generator asset claims 1,300+ seated spectators in real time (vendor marketing, UNVERIFIED).

**Recommendation for our scale**
- **Seating.** 100–400 low-poly (300–600 triangle) chibi spectators, GPU-instanced.
- **Animation.** Two to four baked vertex-animation-texture loops (idle sway, clap, cheer-jump, "ooh"), with per-instance phase and colour.
- **Excitement signal.** Drive animation from one global `_CrowdExcitement` value set by game events (rally length, ace, match point).
- **Far stands.** Use cards or a painted backdrop with a scrolling "wave" shader. The crowd is mostly a **motion texture**: a reaction wave after a point reads on both screens even when no single face does.
- **Mario Tennis Aces and Switch Sports crowd tech:** UNVERIFIED (no source found). Switch Sports' Ask the Developer describes Spocco Square as a sports complex that could not exist but would be appealing if it did. The Sportsmates characters needed more than 650 separate motions (VERIFIED).

### 3.5 Props and life

- **Motion beats detail.** Recommendation, consistent with the acuity math: a few large moving things read better than many small static ones. In rough priority:
  1. Flags and bunting on the global wind
  2. A blimp or hot-air balloons drifting across the sky (Alto's Odyssey uses balloons and wildlife as recurring flourishes, VERIFIED as described)
  3. Birds crossing in flocks, or as a single gull in golf seaside holes
  4. Boats sliding along the horizon
  5. Confetti and streamers on match point or hole-out
  6. Ball kids running, and an umpire turning their head
  7. Water sparkle
- **Cost.** Each item is one or two draw calls of vertex-animated meshes, plus small particle bursts on events.
- **Human figures.** Ball kids and umpires are characters with silhouettes. Give them a few baked loops and event-triggered gestures (catch the ball, point to call). They sell "a real match" more than any texture.

### 3.6 The diorama feel

- **Link's Awakening (2019).** Aonuma described the look as a "diorama" re-creation, with a tilt-shift effect to emphasize the miniature feel. It fits the small but deep world and its comical characters (Hollywood Reporter via GoNintendo and Nintendo Everything, VERIFIED).
- **Captain Toad.** The levels are "garden-in-a-box" dioramas built around turning the camera to see the whole stage (Hayashida and Hiratake interviews, VERIFIED).
- **Astro Bot.** Art rebuilt the blocked-out platforms in high quality and made them reusable at different angles, like toy blocks (PlayStation Blog, VERIFIED).
- **Recommendation for us:**
  - **Tilt-shift** on intro, flyover and replay cameras only. Use a cheap Gaussian depth of field with a horizontal focus band, not Bokeh. It is still a full-screen blur at 1080p, so budget it.
  - **Saturated, slightly lifted palettes** with soft plastic speculars.
  - **Bounded worlds.** Courts and holes that sit as islands with visible edges.
  - **Toy-block modular props** reused at angles.
  - **Gameplay camera stays sharp.** Diorama blur on the gameplay camera hurts ball reading.

### 3.7 Golf course presentation

- **Wii Sports Resort.** The golf course was planned as 9 holes like Wii Sports and grew to 18 late in 2008. The island got a central volcano so the whole archipelago has one landmark (Iwata Asks, VERIFIED). **Lesson:** one landmark visible from every hole gives orientation and a sense of place.
- **Golf Story.** The developers' main art goal was legibility, so players can tell objects apart and plan shots (Nintendo Everything interview, VERIFIED as reported). One review noted the pixel art sometimes hid slopes (Oberlin Review, VERIFIED). **Lesson:** slope and lie must read through value and lines, not only through shape.
- **Mario Golf: Super Rush.** Weather is used per course (Wildweather), wind is always shown, rain shortens roll (VERIFIED). Presentation was described as "adorably pretty" (Gaming Trend), while EGM found the course design boring (VERIFIED). **Lesson:** beauty does not replace hole identity.
- **What the Golf?** No art-direction interview found. The design is joke-per-hole parody (GamesBeat, VERIFIED).
- **PGA Tour 2K23.** Flyover specifics: UNVERIFIED.
- **Hole intro beats (Recommendation; matches the project's intro-flyover work):** landmark, then tee-to-pin path, then the hazard, then the weather tell (flags, rain shafts), then the hand-off to the player.

### 3.8 What reads and what is wasted at our distances (Recommendation, from §3.1)

**Reads:**
- Value bands of at least about 3 arcmin: mow stripes, wear patches, court colour against its surround.
- Silhouettes: net, posts, players, umpire chair, trees, landmark.
- Motion: crowd wave, flags, birds, ball trail.
- Strong local contrast at the ball.
- Specular sheen changes when wet.

**Wasted:**
- Normal-map micro-grain.
- 1–2 px paint chips.
- Per-blade grass detail beyond the near ground.
- Crowd faces.
- High-resolution texel density on surfaces beyond about 20 m.
- Lens dirt on gameplay cameras.

**Texel density.** Above about 1–2 texels per screen pixel is wasted on both devices. Spend memory on the court surface near the camera and on hero props shown in intros.

---

## 4. Summary tables

### Weather features

| Weather feature | Technique | Mobile cost (iPhone, 1080p, 60 fps) | Readability risk |
|---|---|---|---|
| Falling rain (far) | Full-screen composite with parallax layers (ToyShop), or a camera cylinder or cone | Low: one ALU pass, one fetch; the blend fills every pixel | Low if alpha is capped; breaks at steep camera pitch |
| Falling rain (near) | A few hundred Shuriken stretched billboards, faded within 4 m | Medium: overdraw from streak length | Medium: streaks crossing the ball corridor |
| Splashes | 20/40/60 particles by intensity, masked from cover | Low | Low |
| Ripples | Tiling flipbook normal, 4 intensity layers, only where water collects | Low | Low |
| Wet surfaces | Global `_Wetness`: porosity-based darkening, gloss up, flat normals in puddles, slow drying | Very low in material; medium as a full-screen overlay | Low; never dim court lines |
| Puddle reflections | Sky probe or cubemap at the reflected vector; no SSR | Very low | Low |
| Camera droplets | Refraction sprites sampling a 128x64 downsample (MotoGP) | Low with the downsample; very high without it | High on gameplay camera; cutaways only |
| Lightning | Sun pulse and direction swing, sky-dome flash, 2–4-frame bolt, thunder at distance ÷ 343 m/s | Very low | Medium: exposure clamp and WCAG 3-flash cap |
| Wind | One global vector plus noise gusts into grass, flags, net, crowd, trees, particles; = gameplay wind in golf | Very low (vertex math) | Positive: makes golf wind readable in the world |
| Fog and fog banks | Height and distance fog in material or one pass; banks on flyover cameras only | Low (one pass) | High if it covers the play volume: start beyond the far baseline |
| Snow | Up-facing mask on surfaces; Shuriken flakes; lines kept clear | Low to medium (flake overdraw) | Medium: white ball on white ground; ball needs a coloured rim |
| Sunset and time of day | Numeric grading, sun, ambient, fog and sky lerped from one time curve; fixed key light; skip the dull minutes | Very low | Medium: check every state for ball contrast |
| Weather audio | Rain, wind and wet-footstep layers driven by the same scalars as the visuals; thunder delay | CPU or audio only | None |

### Court and course detail

| Court/course detail | Reads on phone (40 cm)? | Reads on TV (2.5–3 m)? | Cost |
|---|---|---|---|
| Mowing stripes (1–2 m bands) | Yes | Yes | Very low (world-space shader) |
| Baseline grass wear to dirt (tournament) | Yes | Yes | Low (mask lerp) |
| Clay slide scuffs and dust | Yes, as broad strokes | Yes | Low to medium (trail render texture plus a few particles) |
| Clay ball marks | Barely: about 2–4 px | Yes, if contrast is enhanced | Low |
| Hard-court paint chips and micro-scuffs | No | No | Wasted |
| Court lines (crisp, bright) | Yes, critical | Yes, critical | Very low |
| Net band and posts silhouette | Yes | Yes | Very low |
| Net mesh grid | Only as a tone; aliasing risk | Only as a tone; moiré risk | Low if mipmapped |
| Crowd as a motion wave or reaction | Yes | Yes | Low to medium (instanced vertex-animation textures) |
| Individual crowd faces | No | No | Wasted |
| Flags, bunting, balloons, blimp, boats, birds | Yes (motion) | Yes | Low |
| Confetti burst on big moments | Yes | Yes | Low (event-only) |
| Ball kids and umpire gestures | Partly (silhouette) | Yes | Medium (characters plus loops) |
| Tilt-shift diorama blur | Yes on cutaways | Yes on cutaways | Medium (full-screen DoF): cutaways only |
| One landmark visible from every hole or court | Yes | Yes | Medium (one hero asset) |
| Normal-map micro-grain or blade detail beyond about 20 m | No | No | Wasted |

---

## 5. Sources (all fetched or seen in search results, 2026-10-17)

**Weather and rendering**
- Tatarchuk, "Artist-Directable Real-Time Rain Rendering in City Environments", SIGGRAPH 2006 course notes: https://advances.realtimerendering.com/s2006/Chapter3-Artist-Directable_Real-Time_Rain_Rendering_in_City_Environments.pdf (text extracted and read). Slides: https://advances.realtimerendering.com/s2006/Tatarchuk-Rain.pdf
- Lagarde, "Water drop 2b: Dynamic rain and its effects": https://seblagarde.wordpress.com/2013/01/03/water-drop-2b-dynamic-rain-and-its-effects/
- Lagarde, "Water drop 3b: Physically based wet surfaces": https://seblagarde.wordpress.com/2013/04/14/water-drop-3b-physically-based-wet-surfaces/
- Hargreaves, "MotoGP: raindrops keep falling on my lens": https://www.shawnhargreaves.com/blog/motogp-raindrops-keep-falling-on-my-lens.html
- Rain-method forum threads:
  - https://gamedev.net/forums/topic/654661-methods-for-drawing-rain/5141877/
  - https://discourse.panda3d.org/t/rain-and-snow/14782
  - https://discourse.panda3d.org/t/rain-effect/8373
- CryEngine lightning entity: https://www.cryengine.com/docs/static/engines/cryengine-5/categories/23756816/pages/29796945

**Ghost of Tsushima**
- Wind write-up: https://gamedeveloper.com/design/using-vorticles-to-simulate-wind-in-i-ghost-of-tsushima-i-
- Wind talk: GDC Vault https://gdcvault.com/play/1027124/Blowing-from-the-West-Simulating ; YouTube d61_o4CGQd8 ; Podwise chapters https://podwise.ai/episodes/1458666
- Grass talk: GDC Vault https://gdcvault.com/play/1027214/Advanced-Graphics-Summit-Procedural-Grass ; YouTube Ibe1JBF5i5Y
- Ambience talk: https://gdcvault.com/play/1026976/Big-World-Small-Team-Designing

**Sky: Children of the Light**
- Art talk: https://gdcvault.com/play/1026812/Art-of-Sky-Children-of
- Write-up: https://www.pockettactics.com/sky-children-of-the-light/art
- Rain mechanics (fan wiki): https://sky-children-of-the-light.fandom.com/wiki/Flora,_Minerals_and_Elements_of_Sky
- Walkthrough: https://www.appunwrapper.com/2019/07/18/sky-children-of-the-light-walkthrough-guide/
- Lighting talk listing (403): https://gamedev.net/news/994-dynamic-environment-lighting-in-sky-children-of-the-light-gdcrewind-gdc2026/

**Mario Kart World**
- Ask the Developer Vol. 18 Part 2: https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-18-mario-kart-world-part-2
- Digital Foundry summary: https://www.nintendolife.com/news/2025/04/digital-foundry-digs-deep-into-mario-kart-worlds-tech-and-specs ; Digital Foundry video 8-P1tKHnWjc

**Zelda: Breath of the Wild and Tears of the Kingdom**
- GDC 2017 talk: YouTube QyMsF31NdNc
- Denfaminicogamer CEDEC 2017 recap: https://news.denfaminicogamer.jp/kikakuthetower/171016
- Famitsu CEDEC 2017 index: https://www.famitsu.com/matome/cedec2017
- Weather (fan wiki): https://zelda.fandom.com/wiki/Weather
- Rain and puddles: https://zeldauniverse.net/2017/04/03/the-rain-in-breath-of-the-wild-does-more-than-hinder-your-climb/
- Weather-control interview: https://gonintendo.com/stories/302341-nintendo-considered-letting-players-control-the-weather-in-zelda

**Alto's Odyssey**
- https://www.idownloadblog.com/2018/02/21/review-altos-odyssey/
- https://www.redbull.com/ca-en/altos-odyssey-ios-launch-interview
- https://blogs.ulster.ac.uk/cormacmccann/?p=794

**Racing games**
- Forza Horizon 2 puddles: https://jalopnik.com/forza-horizon-2-developer-says-manufacturer-provided-da-1588344255
- Gran Turismo 7 rain: https://racinggames.gg/article/kazunori-yamauchi-confirms-not-every-track-in-gt7-has-dynamic-weather

**Other games**
- Animal Crossing rain: https://nookipedia.com/wiki/Rain
- Fortnite tornadoes and lightning: https://www.pcgamer.com/uk/fortnite-update-tornado-lightning-flare-gun
- Fortnite performance-mode storm visibility: https://www.thegamer.com/fortnite-performance-mode-issues/
- Genshin custom render pipeline (Habr): https://habr.com/en/articles/874866
- Red Dead Redemption 2 SIGGRAPH 2019: https://history.siggraph.org/?p=76936

**Unity and mobile performance**
- VFX Graph system requirements: https://docs.unity3d.com/Packages/com.unity.visualeffectgraph@17.0/manual/System-Requirements.html
- VFX Graph iOS forum report: https://discussions.unity.com/t/ios-and-android-support/857886
- Legacy mobile optimisation: https://docs.unity.cn/540/Documentation/Manual/MobileOptimisation.html
- Particle fill-rate guide: https://bugnet.io/blog/debugging-particle-system-performance-issues
- URP Color Lookup: https://docs.unity3d.com/Manual/urp/post-processing-color-lookup.html
- URP 3D Sample: https://unity.com/demos/urp-3d-sample
- Boat Attack water: https://openupm.com/packages/com.unity.urp-water-system/
- Fontainebleau: https://GitHub.com/Unity-Technologies/FontainebleauDemo
- Apple TBDR guide (page did not render): https://developer.apple.com/documentation/metal/tailor-your-apps-for-apple-gpus-and-tile-based-deferred-rendering

**Sports-game weather and wind**
- Mario Golf: Super Rush weather: https://www.thegamer.com/mario-golf-super-rush-guide-weather-conditions/
- Rain blur review: https://www.stripes.com/living/entertainment/video_games/2021-07-01/mario-golf-super-rush-video-game-review-1882620.html
- Reviews: https://gamingtrend.com/feature/reviews/im-an-albatross-mario-golf-super-rush-review/ ; https://egmnow.com/mario-golf-super-rush-review/
- PGA Tour 2K23 physics and wind: https://pgatour.2k.com/2k23/up-your-game/physics/

**Courts, crowds and presentation**
- Top Spin 2K25 Centre Court Report: https://2k.com/games/topspin-2k/topspin-2k25/centre-court-report/gameplay/
- Lawn-stripe physics: https://www.onlineturf.co.uk/knowledge-base/blog/creating-stripes-on-your-lawn
- Crowds:
  - Polypostors: https://dcgi.fel.cvut.cz/home/zara/papers/KavanEtAll-I3D08.pdf
  - Geopostors: https://ics-websites.science.uu.nl/docs/vakken/mcrws/papers_new/Dobbyn%20et%20al%20-%202005%20-%20Geopostors.pdf
  - Unity animation instancing: https://blog.unity.com/engine-platform/animation-instancing-for-skinnedmeshrenderer
  - Unity forum on stadium fans: https://discussions.unity.com/t/what-is-the-best-way-to-make-fans-cheering-in-a-stadium-for-a-mobile-game/883782
  - Stadium crowd book chapter: https://www.taylorfrancis.com/books/9780203705179/chapters/10.1201/b22483-9
- Switch Sports Ask the Developer: https://www.nintendo.com/sg/interview/as8s/03.html
- Link's Awakening tilt-shift: https://nintendoeverything.com/aonuma-on-how-the-art-style-came-to-be-for-zelda-links-awakening-on-switch/
- Captain Toad: https://www.gameinformer.com/b/features/archive/2014/11/17/captain-toad-treasure-tracker-was-almost-a-zelda-game.aspx
- Astro Bot: https://blog.playstation.com/2024/09/09/astro-bot-how-team-asobi-created-a-unified-vision-for-fun/
- Wii Sports Resort Iwata Asks: https://iwataasks.nintendo.com/interviews/wii/wiisportsresort/0/5
- Golf Story: https://nintendoeverything.com/interview-golf-story-dev-on-wii-u-origins-cut-ideas-and-more/ ; https://oberlinreview.org/14678/arts/sidebar-releases-realistic-new-take-on-golf-games/
- What the Golf?: https://gamesbeat.com/what-the-golf-putts-around-with-physics/
- Display-size field study (ANSI/HFES 100 values UNVERIFIED): https://researchgate.net/profile/Oliver-Kolbe/publication/345496261

**UNVERIFIED or not found** (do not cite as fact):
- Any CEDEC 2017 rain, grass or wind technique
- Genshin rain and wetness shading
- Forza and GT wet-tarmac shader parameters
- Naughty Dog lens drops
- Mario Tennis Aces and Switch Sports crowd tech
- PGA 2K flyover details
- Apple Metal rain demo
- Sky Eye of Eden storm visuals
- Alto's Odyssey lightning
- Smooth blending of LUT textures between URP volumes
- Exact ANSI/HFES 100 character sizes
