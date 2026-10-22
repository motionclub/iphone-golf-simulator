# Party Sports: A Visual Standard + Juice Plan

For Adnan, written for a founder who isn't an artist. Researched Oct 14, 2026.

## 0. Your reference images (what the target is)
These are the five Codex images you made at 9:07–9:10 PM ET today. They live in `~/.codex/generated_images/01a13c3a-bacc-7912-942b-3c4f38acf507/`, and there are box copies in `/workspace/juice/his_refs/r1–r5.png` plus `sheet.jpg`.
- **r1 Hub (golden hour):** a warm low sun with a peach and lilac cloud sky. Warm stone pavers sit against cream and navy buildings. Lamps and windows glow, and there are lots of round green bushes. The shadows are soft and bluish.
- **r2 Resort tennis (close cam):** a saturated blue court with a green surround and crisp, thick white lines. There are palms, turquoise sea and layered islands that fade into haze, and big puffy cumulus clouds. Bright midday sun throws clear contact shadows under the props.
- **r3 Golf tee:** striped mown grass in two greens, round cartoon trees, a sea bay and misty mountains in the back. The light is warm on top, the shadows are cool, and the yellow ball markers read clearly.
- **r4 Venue grid:** night-city rooftop (purple dusk with neon), volcano court (a red-orange sky, lava falls with emissive glow), frozen ice, and magma golf (glowing cracks, a dark rock rim).
- **r5 Weather grid:** the same golf hole in clear, overcast, storm (dark sky, lightning, desaturated), fog (washed-out distance) and sunny-cloudy versions.

**What they have in common, which is the style DNA:**
1. Saturated but not neon local colors.
2. Warm key light with cool shadows.
3. Strong atmospheric depth, where each layer gets lighter and bluer with distance.
4. Big round "readable" shapes, with nothing fiddly or realistic.
5. Painted cumulus skies.
6. Emissive accents (lamps, lava, neon) that pop.

The existing `ENVIRONMENT_BRIEF_ASTRA.md` already covers the per-area targets: lighting, sky, fog, terrain, courts, hub, post, the golf weather looks, cheap fakes for iPhone, and verification. What it doesn't have is the shared system underneath. This doc is that system.

## 1. Why "copy this image" fails
- A picture is the *result* of maybe 30 separate decisions: sun angle, sun color, shadow color, fog color and distance, sky texture, grass shader, texture painting, tone mapping, bloom, and object shapes. An agent looking at a picture has to guess all 30 at once, and it guesses differently on every venue. That's why each scene drifts.
- AI-made refs also "cheat". The lighting isn't physically consistent, and they have detail no iPhone can render. The goal is to copy the **rules** behind them, not the pixels.
- Studios solve this the same way every time. They turn the picture into **a few shared assets with a few numbers each**, then build every scene from those assets. Consistency comes from *reuse*, not from re-copying.

How real studios describe it:
- **Sea of Thieves (Rare):** "simple rules for a unified look". They simplify shapes, hand-paint textures instead of using photos, add "wonky" wear, and use the light to set the mood.
- **Fortnite (Epic):** painting stylized textures by hand worked better than filtering photos, which came out noisy. They also removed parallel lines, and added nothing smaller than a mailbox that the player has to read.
- **Guilty Gear Xrd (Arc System Works):** every shading decision is *controlled by the artist*, with nothing left to chance. They use 2-tone shading, no normal maps, and hand-placed shadow areas.
- **Hi-Fi Rush (Tango):** one toon renderer for both world and characters, using mostly base color and roughness and no metallic. A *small* input set is what keeps it all consistent.
- **Overwatch (Blizzard):** the art direction pillars ("vibrant, hopeful") are written down early, and every map is checked against them.

## 2. The layered system (build it bottom-up, in this order)
| # | Layer | What it is | The Party Sports version |
|---|---|---|---|
| 1 | **Art bible (1–3 pages)** | Written rules plus the golden images. | The style DNA list above, a **master palette** (about 24 swatches: grass ×3, sand, water ×2, stone ×2, wood, foliage ×3, sky top/horizon per time of day, shadow tint, emissive accents), **value rules** (the hero and ball are always the brightest or most contrasted thing; the background is lighter and lower in contrast), and **shape rules** (round, chunky, no thin details under about 10 cm at play distance). |
| 2 | **Look-dev scene ("beauty corner")** | One small Unity scene where the look gets approved *once*. | `LookDev_Golf` and `LookDev_Tennis`: one tee box or court, a hero, a ball, one of each prop and tree, a sky. Dial it in until it matches r2 and r3 *from the game camera*. Every other venue copies its settings. |
| 3 | **Master shaders + material library** | 4–6 Shader Graph masters with a few exposed sliders. Every material is an *instance* of one of them. | `M_Ground` (grass, sand, court, with stripe/noise/tint and wetness), `M_Foliage` (wind sway, translucency, top-down tint gradient), `M_Prop` (toon-ish ramp, AO tint, rim), `M_Water` (depth color, foam, scrolling normals), `M_Emissive` (lava, neon, lamps, with pulse), `M_Sky`. Agents are **not allowed to create new shaders**, only instances. |
| 4 | **Lighting + post presets** | A saved profile per time of day and per venue mood. | A `LightingPreset` ScriptableObject holding sun angle, sun color and intensity, ambient top/equator/ground colors, shadow strength, fog color and distance, and sky material. That gets paired with a URP **Volume Profile** (tone mapping, color adjustments, white balance, bloom, vignette, LUT). Presets: Morning, Midday, Golden, Dusk-Neon, Volcano, Snow. |
| 5 | **Environment kit** | Modular, reusable pieces built to a shared scale and texel density. | Trees (3 sizes × 3 variants), bushes, rocks, flower clumps, fences, court surrounds, lamp posts, backdrop hills and islands as **layered cards**, and cloud cards. Every course is assembled from the kit. |
| 6 | **VFX library** | Prefabs with one naming scheme and a shared particle material and atlas. | Dust puff, grass spray, sand splash, water splash, sparkle burst, ball trail, confetti, lava ember, rain, snow, lightning flash, fog wisps, wind leaves. |
| 7 | **Juice / feedback library** | Reusable "feedback" components triggered by events. | `Juice.Play("BallHitPerfect", pos, strength)` runs particles, sound, camera shake, hit-stop, haptic and a UI pop together. |
| 8 | **Weather as global parameters** | Weather is a handful of numbers that *every* shader reads. | `_Wetness`, `_WindStrength`, `_WindDir`, `_Snow`, `_StormDarkness`, `_FogDensity`, set with `Shader.SetGlobalFloat/Vector` by one `WeatherDirector`. Each state blends a lighting preset and a Volume, and spawns its VFX and audio bed. |
| 9 | **Golden screenshots** | Fixed cameras that capture each venue and weather and compare it with the approved image. | You already have `tools/EnvBriefCaptureTests` and `build_sheets.py`. Add approved "golden" shots and a simple diff check: average color, brightness histogram, and a perceptual diff. Then any change that drifts a scene more than X gets flagged. |

## 3. Step order for Party Sports
1. **Lock the bible.** Pull the palette from r1–r5 automatically (k-means swatches), write the value and shape rules, and save them to `ArtDir/style/ART_BIBLE.md` with the 5 refs.
2. **Build the look-dev scene** on the resort tennis court with the close cam (r2), then on the golf tee (r3). Approve it by eye. This becomes the *standard*.
3. **Master shaders.** Convert the court, grass, foliage, water and lava to the 5 masters. Delete one-off materials.
4. **Lighting presets + Volumes.** Midday (resort and golf), Golden (hub), Dusk-Neon (rooftop), Volcano, Snow. Each venue just *references* a preset.
5. **Sky + depth kit.** A painted cumulus skybox per preset, 3 layers of backdrop hill and island cards that fade into fog, and a height and distance fog color matched to the sky horizon.
6. **Environment kit pass.** Round trees, bushes, rocks, flowers. Re-dress golf holes and court surrounds from the kit.
7. **Weather director (global params)** driving the shaders, Volumes, VFX and audio. Match r5.
8. **VFX + juice library**, then wire it into gameplay events (see the catalog below).
9. **Golden shots + perf gates** on every venue and weather combination. Run them after every agent pass.

## 4. Juice catalog for Party Sports
Juice means maximum output for minimum input. It's many small layered feedbacks: tweening, squash and stretch, particles, sound, shake and hit-stop ("Juice It or Lose It", "Art of Screenshake"). The rule is that **every important event gets at least 3 channels** (visual + sound + motion/haptic), scaled by how important it is.

| Event | Juice layers | How to build it in Unity (URP, iPhone) |
|---|---|---|
| Swing windup | Anticipation squash on the club or racket, a faint swoosh trail, a sound pitch that rises with power | Animation curve on the root scale (unless animations are off limits, so use a VFX trail only), a `TrailRenderer` on the club tip, and an AudioSource pitch tied to power |
| Ball hit, normal | Impact spark, a "thock" sound, a tiny camera kick, a light haptic | Shuriken burst (8–12 particles), a pooled AudioSource, a Cinemachine Impulse or simple shake script (0.05 s), iOS haptic light |
| Ball hit, perfect/sweet spot | **Hit-stop** of 50–80 ms, a white flash ring, a bigger shake, a "PERFECT" text pop, a chime layer | `Time.timeScale=0` for 3–5 frames (unscaled UI), a ring particle on an additive material, a scale-punch tween on the text, haptic medium |
| Ball flight | A trail colored by shot type, a soft shadow blob always on the ground | `TrailRenderer` with a width curve, a projected shadow quad or decal under the ball (depth reads at the close cam) |
| Ball land (grass/sand/water/court) | A per-surface puff (grass blades, sand spray, splash ring), a per-surface sound, a landing mark | A surface lookup from the physics material, giving a VFX library prefab, plus a URP Decal (Screen Space) mark that fades out |
| Putt drop | Slow-mo for the last 0.3 s, a cup "clunk", a confetti pop, a crowd "ooh", a score count-up | timeScale 0.4 tween, a confetti burst, a UI number tween with easing (OutBack) |
| Ace / winner | A camera push-in, a crowd roar, light streaks, a short freeze-frame with a stinger | Cinemachine or camera tween, the PresentationStinger script, a full-screen flash via Volume weight tween |
| Net cord | Net wobble, a "tick" sound, the ball briefly highlighted | Vertex wobble on the net material driven by a hit position property, plus an outline flash |
| Wind | Foliage, flags and grass sway, drifting leaves, a whoosh bed scaled by strength, a wind arrow in the HUD | A global `_WindStrength/_WindDir` read by `M_Foliage` (vertex offset with sine and noise), a leaf particle stream, an audio loop volume on wind |
| Rain | Rain sheets near the camera, splash rings on the ground, **wet look** (darker albedo, glossier, puddle reflections), a darker sky, a rain audio bed | Camera-attached rain particles (not world-wide), a global `_Wetness` lerping smoothness up and albedo down on `M_Ground/M_Prop`, puddle mask decals, Volume: cooler white balance and lower saturation |
| Storm | Lightning flash plus a delayed thunder sound, swaying trees, a dark sky | A flash script spikes the ambient and a Volume exposure for 0.1 s, then thunder plays 0.5–2 s later. Wind at max. |
| Fog | Distance hidden in color, wisps near the ground | URP fog (exponential) with a color matched to the sky horizon, plus alpha cards for wisps near the camera |
| Snow / ice | Falling flakes, a snow mask on top surfaces, ice reflections, breath puffs | Global `_Snow` adds a white top-facing blend in the master shaders, plus a particle snowfall |
| Lava / magma hazard | Glowing cracks that pulse, embers, a heat-shimmer card, a sizzle when the ball falls in | `M_Emissive` pulse plus bloom, an ember particle, and a hazard-in event triggering a splash, a sound and a UI "LAVA!" |
| Water hazard | Foam edge, a splash plus rings, "plunk" | `M_Water` depth-fade foam, a splash prefab |
| Moving obstacles (windmill, bumpers) | **Idle motion** so it reads as live, a clear warning color (one hazard color everywhere), a rim/outline, an anticipation wind-up before it moves into the path, a bonk on hit | A simple rotator or tween, a consistent hazard accent from the palette, a rim term in `M_Prop`, a sound cue 0.5 s before the danger window |
| UI wins / scores | Pop-in with overshoot, count-up numbers, star bursts, button press squish | Tweens (scale 0→1.15→1), easing curves, a sparkle particle in a UI canvas |

Readability rules for obstacles and hazards: one shared **hazard color** (for example orange-red) that is never used for decoration. Hazards always move or glow a little. Players get warned before damage (telegraphing).

## 5. Tool recommendations (what the repo has now: URP 17.3 only, no Cinemachine, VFX Graph or tween library yet)
- **Particles:** use the **built-in Particle System (Shuriken)**. Unity's own guidance is that it runs everywhere and talks to physics. VFX Graph needs compute shaders and is for millions of particles, which is overkill on iPhone.
- **Shaders:** **Shader Graph** masters (URP Lit or Unlit with a custom ramp). Keep the number of exposed sliders small.
- **Post/lighting:** **URP Volume Profiles** (one Global per venue, Local for zones), the LUT/Color Adjustments, Bloom (low threshold only on emissives), and Tone mapping (Neutral/ACES). Use **baked lightmaps + light probes** for static scenery and keep one realtime sun.
- **Decals:** URP Decal Renderer Feature in **Screen Space** mode. Unity recommends it for tile-based mobile GPUs. Use it for ball marks, puddles and scorch.
- **Camera shake:** **Cinemachine Impulse** (free package; supports Recoil/Bump/Explosion shapes), or a 30-line shake script if you're not adopting Cinemachine.
- **Juice framework:** **Feel by MoreMountains** ($50, Unity 6 compatible, 150+ feedbacks, includes Nice Vibrations haptics). It's the fastest way to get hit-stop, shake, tween and haptic in one "feedback player". The alternative is free DOTween or PrimeTween plus your own `Juice` script.
- **Weather:** your own `WeatherDirector` that sets globals plus blends presets. No asset needed.

## 6. How to brief agents (Claude / Astra) so it stays consistent
1. **One system per prompt.** For example "build M_Foliage + global wind", not "make golf look like r3".
2. **Give numbers, not adjectives.** For example "sun 35° elevation, color #FFE2B8, shadow tint #6B7FB8, fog start 40 m and end 220 m, color = sky horizon".
3. **Name the asset it must reuse**, and forbid new shaders and one-off materials.
4. **Golden shots are the acceptance test.** Ask for BEFORE | AFTER | REF sheets from fixed cameras, plus a perf number (FPS and draw calls on the Low tier).
5. **Your eye approves the look-dev scene first.** After that, agents only *propagate* it.
6. **Perf budget** (a starting point for iPhone, to tune on device): 60 fps High / 30 fps Low, fewer than about 150 draw calls, under 150k tris on screen, at most 2 full-screen post passes plus bloom, overdraw kept low (small, few transparent particles).

## Sources (Links gathered from search results; most not individually opened Oct 14, 2026)
- Juice It or Lose It, Jonasson & Purho (GDC Vault): https://www.gdcvault.com/play/1016487/juice-it-or-lose · video: https://www.youtube.com/watch?v=Fy0aCDmgnxg
- The Art of Screenshake, Jan Willem Nijman / Vlambeer: https://www.youtube.com/watch?v=SkgkIXZ_13Y · summary: https://gamedesign.gg/watch/art-of-screenshake/
- Developing the Art of Fortnite (GDC): https://www.gdcvault.com/play/1024936/Developing-the-Art-of-Fortnite · video: https://www.youtube.com/watch?v=498KToofNf8
- Visual Adventures on Sea of Thieves (GDC): https://www.gdcvault.com/play/1025015/Visual-Adventures-on-Sea-of · 80.lv recap: https://80.lv/articles/gdc18-visual-adventures-on-sea-of-thieves
- Summary of both stylized talks (Habrador): https://blog.habrador.com/2018/08/stylized-graphics-fortnite-sea-of-thieves.html
- The Art of Overwatch: Evolving a Legacy (GDC): https://www.gdcvault.com/play/1024268/The-Art-of-Overwatch-Evolving
- Guilty Gear Xrd GDC talk recap (Sketchfab): https://sketchfab.com/blogs/community/art-spotlight-here-at-last/
- 3D Toon Rendering in Hi-Fi RUSH (GDC): https://gdcvault.com/play/1034251/3D-Toon-Rendering-in-Hi · video: https://www.youtube.com/watch?v=gdBACyIOCtc
- Breath of the Wild, "Change and Constant" (GDC): https://www.gdcvault.com/play/1024562/Change-and-Constant-Breaking-Conventions
- Rendering Tiny Glade (Pounce Light): https://www.youtube.com/watch?v=jusWW2pPnA0
- Unity: Volumes in URP: https://docs.unity3d.com/6000.0/Documentation/Manual/urp/volumes-landing-page.html
- Unity: Choosing your particle system: https://docs.unity.com/en-us/engine/6000.0/manual/visual-effects/particle-systems/choosing-your-particle-system
- Unity: Decal Renderer Feature (Screen Space for mobile): https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal%4014.0/manual/renderer-feature-decal.html
- Cinemachine Impulse Source: https://docs.unity3d.com/Packages/com.unity.cinemachine@6.6/manual/CinemachineImpulseSource.html
- Feel (MoreMountains): https://assetstore.unity.com/packages/tools/particles-effects/feel-183370

Not covered by a source I could open: Genshin/Zenless toon pipeline, Mario Kart World and Astro Bot tech talks (no official talks found), and Reddit/X dev threads (not searched in this pass). The perf budget numbers are common starting points, not a sourced spec.
