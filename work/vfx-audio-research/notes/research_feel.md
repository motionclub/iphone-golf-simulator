# Research: impact feel, VFX, audio, haptics and camera systems in top games

Date: 2026-10-17. Web research only (WebSearch/WebFetch, no browser, no downloads).
Purpose: input for the game-wide event-driven VFX + audio + haptics + camera-feel system (Unity URP, phone = motion controller, game AirPlayed to TV).

Legend: **[S]** = sourced (URL right there). **[S-snippet]** = taken from a search-result summary because the page itself blocked fetching (403 or domain blocked); treat as likely but check before quoting. **[I]** = my own inference or recommendation, not from a source.

Video IDs: I only list IDs that a page I fetched or a search result actually showed. I verified none of them by playing the video, and no timestamps showed up in the results.

---

## 1. Source index (verified links)

| Talk / source | Link | How the ID was verified |
|---|---|---|
| Jonasson & Purho, "Juice it or lose it" (GDC Europe 2012) | https://www.youtube.com/watch?v=Fy0aCDmgnxg | listed on kenney.nl https://kenney.nl/learn/must-see-videos-for-indie-developers |
| Jan Willem Nijman, "The Art of Screenshake" (~40 min) | https://www.youtube.com/watch?v=AJdEqssNZ-U | same kenney.nl page |
| Squirrel Eiserloh, "Math for Game Programmers: Juicing Your Cameras With Math" (GDC 2016) | https://www.youtube.com/watch?v=tu-Qe66AvtY | embedded on https://www.gamedeveloper.com/programming/video-sprucing-up-cameras-with-math |
| Sakurai, "Stop for Big Moments! [Design Specifics]" (hit stop) | https://www.youtube.com/watch?v=OdVkEOzdCPw | search result titled exactly that |
| Sakurai, follow-up on fine-tuning hit stop (8 techniques) | https://www.youtube.com/watch?v=tycbMSjDDLg | linked from https://nintendowire.com/news/2022/12/12/this-week-in-sakurai-12-5-12-11-fine-tuning-hit-stop-and-cheating-the-system/ (I did not confirm the title on YouTube) |
| GDC 2017, "Art Directing VFX for Stylized Games" (Epic/Fortnite, Double Fine, Volition; Kladis, Lindsey, Mitchell, Spurgeon) | https://www.youtube.com/watch?v=x30j-PUN1G4 | embedded on https://gamedeveloper.com/design/video-tips-on-art-directing-vfx-for-stylized-games ; Vault: https://gdcvault.com/play/1024715/Art-Directing-VFX-for-Stylized |
| Lawlor & Neumann, "Overwatch – The Elusive Goal: Play by Sound" (GDC 2016) | https://gdcvault.com/play/1023010/Overwatch-The-Elusive-Goal-Play | Vault page (may need a membership) |
| Overwatch Wwise Tour 2016 (1 of 7) | https://www.audiokinetic.com/learn/videos/fGDOgn2WXLs | Audiokinetic video page |
| John Nesky, "50 Game Camera Mistakes" (Journey) | https://www.youtube.com/watch?v=C7307qRmlMI | kenney.nl page |
| WWDC19 session 810, "Designing Audio-Haptic Experiences" | https://developer.apple.com/videos/play/wwdc2019/810 | Apple page (transcript fetched) |
| Celeste Player.cs (public source) | https://raw.githubusercontent.com/NoelFB/Celeste/master/Source/Player/Player.cs | fetched and read |

---

## 2. Per game / per source findings

### 2.1 Super Smash Bros. (Sakurai): hit-stop tied to damage
- **[S]** "Stop for Big Moments!" explains *hit stop*, the brief freeze when a hit lands, and compares the same attack with and without it. It also introduces "boss stop", a screen freeze when a boss is defeated. Sakurai adds that a short slow-motion that snaps back to normal speed makes the moment even stronger, and that the idea applies to more than hits. Coverage: https://automaton-media.com/en/news/20220824-15208/ , https://upcomer.com/sakurai-starts-new-youtube-channel-sharing-game-development-secrets/ , video https://www.youtube.com/watch?v=OdVkEOzdCPw
- **[S]** Eight ways to improve hit stop (follow-up video, as listed by Nintendo Wire): (1) shake the character who gets hit more; (2) don't move the hitbox; (3) shake horizontally on the ground and vertically in the air; (4) let the shake taper off; (5) control the amount of hit stop; (6) interpolate frames into the damage pose; (7) keep the attacker moving just a little; (8) scale the shake with camera distance. https://nintendowire.com/news/2022/12/12/this-week-in-sakurai-12-5-12-11-fine-tuning-hit-stop-and-cheating-the-system/
- **[S-snippet]** SmashWiki hitlag formulas (d = damage %, h = per-hitbox multiplier, default 1; e = electric; c = crouch-cancel):
  - Melee: `floor(floor(floor(d/3 + 3) * e) * c)`
  - Brawl / Smash 4: `floor(floor((d*0.3846154 + 5) * h * e) * c)`
  - Ultimate: `floor(floor(floor((d*0.65 + 6) * h * e * s) * p) * c)`. A sandbox draft adds a player-count term and caps the result at **30 frames**.
  - Worked example: a 15 % move gives about 8 frames in Melee, 9 in Brawl/Smash 4 and **15 in Ultimate** (60 fps).
  - Hitboxes carry their own multiplier. Example: Marth's tipper has a higher hitlag multiplier on a sweet-spot hit.
  - https://ssbwiki.com/Hitlag (fetch was blocked; facts from search summaries of this page and https://www.ssbwiki.com/User:CanvasK/Sandbox)
- **[I]** Takeaway: hit-stop should be a **linear function of hit strength with a floor and a cap**, applied to both participants, with an optional per-event multiplier for sweet spots.

### 2.2 Celeste (Thorson & Berry): actual shipped values from public source
From https://raw.githubusercontent.com/NoelFB/Celeste/master/Source/Player/Player.cs **[S]**:
- **Freeze (hit-stop):** `Celeste.Freeze(.05f)` on dash start (50 ms, about 3 frames at 60 fps), skipped when time is already slowed (`Engine.TimeRate > 0.25f`). `Freeze(.1f)` on an explode-launch (bigger event, 100 ms). `Freeze(0.01f)` when a crystal is smashed during a fall.
- **Directional shake:** `level.DirectionalShake(DashDir, .2f)` on dash, so the shake points in the motion direction for 0.2 s. `DirectionalShake(±axis, .1f)` on spring bounces. An undirected `level.Shake()` plays on death.
- **Rumble is a small enum vocabulary, Strength {Light, Medium, Strong} × Length {Short, Medium}**, picked per event:
  - dash: Strong/Medium
  - landing: Light/Short
  - throw: Strong/Short
  - drop: Light/Short
  - bounce: Light/Medium
  - super-bounce: Medium/Medium
  - red-dash wall hit: Medium/Short
  - tired: Light/Short every frame
- **Squash & stretch:**
  - jump start: Scale (0.6, 1.4)
  - super-bounce: (0.5, 1.5)
  - side bounce: (1.5, 0.5)
  - landing: X lerps 1 → 1.6 and Y lerps 1 → 0.4 by `squish = min(fallSpeed / maxFall, 1)`, so squash depth scales with impact speed
  - recovery toward 1 at `1.75 * dt` per frame
- **One dash event fans out to every channel in one function:**
  - freeze 0.05 s
  - rumble Strong/Medium
  - displacement burst (screen-space distortion ring, 0.4 s, radius 8 → 64)
  - directional shake 0.2 s
  - `SlashFx.Burst`
  - trail sprites
  - particles every 0.02 s
  - direction- and colour-specific SFX (`char_mad_dash_pink_right`, etc.)
- **[S]** Thorson's 2020 game-feel thread covers coyote time, jump buffering and half gravity at the jump apex: https://www.gamespot.com/articles/celeste-dev-explains-how-they-made-their-game-feel/1100-6474775/

### 2.3 Vlambeer / Nijman, "The Art of Screenshake"
Numbers below are from the write-up at https://infovore.org/?p=5275 (talk: https://www.youtube.com/watch?v=AJdEqssNZ-U). All are for one Nuclear Throne pistol shot at 30 fps and 320×240 **[S]**:
- **Firing:** shell ejected at 2–4 px/frame, offset 100–150° from the aim direction.
- **Bullet:** 16 px/frame with 0–4° random spread. The first frame is a circle and later frames are bullet-shaped, which fakes a muzzle flash.
- **Camera:** kicks back 6 px away from the aim direction. Screenshake goes up by **+4** (max px in any direction) and decays quickly.
- **Weapon kick:** set to 2 px, then the gun slides back fast. A reverse kick plays on shotgun reload.
- **Enemy hit:**
  - material sound (meat, plant, rock or metal) mixed with the character's own hurt sound
  - knockback 3 px/frame
  - one white frame, then two "big eyes" frames
  - **10–20 ms hitpause on every hit**
- **Permanence:** props such as cacti keep lasting marks of the fight.
- **[I]** The pattern here is additive shake. Every event adds a fixed amount to one shared value that decays, and nothing sets the shake to a value directly.

### 2.4 Eiserloh, "Juicing Your Cameras With Math" (GDC 2016): trauma shake
- **[S]** The talk covers kinds of camera shake, smoothed follow, framing and split screen. Free video: https://www.youtube.com/watch?v=tu-Qe66AvtY (via https://www.gamedeveloper.com/programming/video-sprucing-up-cameras-with-math).
- **[S-snippet]** A personal account of the talk says to use rotational and translational shake in 2D but **only rotational shake in 3D**, because a translational jitter can push the camera into walls. https://blogs.jccc.edu/dpatter/tag/mathematics
- **[S-snippet]** Implementations that credit the talk agree on these points:
  - Trauma is a 0–1 value. Events add to it and it decays linearly.
  - Shake = trauma² (some use trauma³).
  - Offset and angle = max × shake × noise(t). Perlin/simplex noise gives a smooth signal. One noise channel per axis, each with its own seed.
  - The npm `screen-shake` package defaults to maxAngle 10°, maxOffset 30 px and decay 0.02 per update.
  - Sources: https://www.npmjs.com/package/screen-shake , https://github.com/baratgabor/Unity3D-PerlinCameraShake (coroutine-driven with no polling; skips axes that are not used) , https://bevy.org/examples/camera/2d-screen-shake/
  - These are derived implementations, not quotes of the slides.

### 2.5 Jonasson & Purho, "Juice it or lose it" (GDC Europe 2012)
- **[S]** A Breakout clone is made "juicy" live on stage with tweening, stretch and squeeze. Jonasson says juicy things "wobble, squirt, bounce around, and make little cute noises", and that juice means "maximum output for minimum input". Purho says a lack of interactivity hurts more than poor graphics. https://www.gamedeveloper.com/design/video-is-your-game-juicy-enough- , video https://www.youtube.com/watch?v=Fy0aCDmgnxg
- **[I]** As I remember the talk (not verified this session): tweened entry of objects, colour, particles on impact, screen shake, sound per hit with pitch variation, eyes on the paddle, and music. Check this against the video before quoting it.

### 2.6 Overwatch (Blizzard): "Play by Sound", priority mixing, VFX colour vs shape
- **[S-snippet]** The audio team (Scott Lawlor, Project Audio Director; Tomas Neumann, Senior Software Engineer) worked to **five pillars**: Hero VO, clear mix, gameplay information, **pinpoint accuracy**, and **Pavlovian response**. The headline goal was "Play by Sound", using audio to direct gameplay and not only decorate it. Middleware: **Wwise**. https://www.audiokinetic.com/en/blog/overwatch-game-audio-using-wwise-1/ (403 on fetch)
- **[S-snippet]** They tried Wwise HDR audio and replaced it with their own system that always "hears" what matters most to the player. Inputs: the player's biggest threat, who the player is looking at, who is looking at the player, and who is shooting nearby. The approach draws on Walter Murch's "dense clarity, clear density". The Wwise Tour talk shows the RTPC curves. Same source.
- **[S]** Each other player gets an "importance" value in the mix based on **how large *the listener* appears on that enemy's screen**. An enemy close by who is not aiming at you earns fewer "threat points" than a farther enemy who is aiming at you, so the first sits lower in the mix. A path-length term was added because an enemy in the room above with no quick route was over-rated. Footsteps and combat get muffled when the player is in hiding spots. Every hero has a unique footstep. https://pcgamesn.com/overwatch/overwatch-devs-on-creating-a-game-you-can-play-by-sound-and-announcing-dolby-atmos-support
- **[S-snippet]** VFX (senior effects artist Rachel Day, BlizzCon 2017 coverage): players are trained to read red as fire or enemy and blue as ice. When World Cup skins recoloured effects to country colours, colour cues were lost, so the team **changed the shape language** of some abilities. https://vfxvoice.com/?p=624080 (search summary)
- **[S]** Day calls VFX "the visual telling of gameplay". Projectile impacts must read instantly. The stylised, hand-painted system aims for "instantly identifiable", not realistic. Workflow: designers set projectile speed, VFX sets the look, and the team pushes intensity to an extreme then dials it back. Timing follows animation principles. https://vfxvoice.com/rachel-day-the-game-changing-gamemaker-behind-overwatch/

### 2.7 League of Legends / Riot: VFX style guide (readability)
- **[S-snippet]** The official 2017 /dev post (the URL now redirects) sets four goals: visual clarity for gameplay, minimal clutter, promote the champion's theme, and surprise and delight. The guide works across five areas: **gameplay, value, color, shape, timing**. It was written because effects were inconsistent across many teams. https://nexus.leagueoflegends.com/en-us/2017/10/dev-leagues-vfx-style-guide/
- **[S]** Ten tips (guide by Art Director Jin Ho Yang), summarised at https://www.vfxapprentice.com/blog/10-league-of-legends-vfx-design-tips :
  1. One clear primary shape shows the effect's purpose. Secondary elements support it through value and saturation.
  2. Scale size and intensity to the ability's importance. A basic attack must not look like an ultimate.
  3. Keep values mostly in the mid range and avoid 0 % and 100 %. A wider value range pulls focus.
  4. Use glow to show power, direction and duration.
  5. Avoid 0 % and 100 % saturation. Higher saturation draws attention.
  6. Use one dominant colour plus a secondary one, desaturate competing colours, and keep genre conventions (heal = green, frost = blue, gunpowder = orange-red).
  7. Hand-drawn shapes that mix soft and hard edges. Don't stack contradictory shapes.
  8. Add motion blur and smear in the direction of travel.
  9. Timing: "lead the brain with anticipation", then the payoff, then time for the viewer to process it.
  10. **Keep effects short.** Long effects clutter the screen, signal the wrong importance and hide other effects.
- **[S-snippet]** Riot's later VFX update post ranks gameplay readability above theme and says spells should be neither too bright nor too hard to see. https://leagueoflegends.com/en-au/news/dev/dev-behind-the-scenes-of-vfx-updates
- **[S-snippet]** VALORANT separates hit-registration **correctness** from **clarity**. Most "bad hit reg" complaints turned out to be clarity problems in impact presentation, and only a few real registration bugs were found. https://www.thespike.gg/valorant/news/riot-games-on-the-state-of-hit-registration-and-future-improvements/347

### 2.8 Rocket League (Psyonix): HDR audio, ball sound
- **[S]** The 2019 HDR Audio update (Stephen Lichota, Miles Flanagan, Mike Ault):
  - HDR "doesn't make sound louder"; it makes "other sounds quieter so there's an emphasis on specific sounds".
  - Other cars and positional cues, such as where the ball is, get priority. Crowd and ambience are pushed out of the way.
  - **20–30 sounds can stack at once.**
  - It was the first mix designed for headphones. Earlier mixes were made on loud high-end speakers.
  - Reference game: Rainbow Six Siege. Rocket League differs because the car is almost always boosting.
  - https://devtrackers.gg/rocket-league/p/d0e83f63-under-the-hood-an-inside-look-at-hdr-audio-coming-to-rocket-league
- **[S]** A Dynamic Range preset now ships: Low, Medium (default), and High ("Theater"). https://www.epicgames.com/help/c-202300000001622/c-202300000001682/what-are-dynamic-range-presets-in-rocket-league-a202300000012407
- **[S]** Founder Dave Hagewood on the ball-impact sound: it should feel "a little bit soft" but "future-tech". https://gameinformer.com/b/features/archive/2015/08/09/the-surprisingly-guarded-lore-of-rocket-league
- **Gap:** I found no source on how hit strength maps to the ball sound, on the middleware, or on how goal explosions are built (only community guesses at https://realtimevfx.com/t/blending-an-animated-mesh-into-particles/8890).

### 2.9 DICE / Frostbite HDR audio (reference for the HDR idea)
- **[S-snippet]** GDC 2009 (Anders Clerwall), and the "Adaptive mixing in Frostbite" slides:
  - Loudness is measured at the listener and a **sliding window** follows the loudest sounds, covering roughly the quietest audible level up to ~130 dB.
  - It is not compression. It works on logical loudness values, not the waveform.
  - It acts as **culling by loudness**, with loudness as the stand-in for importance.
  - Because quiet sounds are culled, 16-bit output (96 dB) is enough.
  - Sources: https://www.slideshare.net/slideshow/adaptive-mixing-in-frostbite/3128152 , https://www.frostbite.com/frostbite/news/how-hdr-audio-makes-battlefield-bad-company-go-boom
- **[S]** Wwise HDR concepts:
  - Threshold and ratio set on the master-mixer bus.
  - With an infinite ratio, any two sounds above threshold come out equally loud. A finite ratio is the compromise.
  - Envelope tracking avoids an unnatural lull after impacts.
  - Shaping an explosion's envelope can create a pre-blast silence.
  - No numeric presets are given.
  - https://designingsound.org/2013/06/21/finding-your-way-with-high-dynamic-range-audio-in-wwise/
- **[S-snippet]** Early Wwise guidance: put HDR sounds on their own bus at about **−12 to −18 dB**, and keep UI and critical VO outside HDR. https://www.gamedeveloper.com/audio/hdr-audio-in-wwise-best-practices-so-far-

### 2.10 Fortnite (Epic)
- **[S]** The GDC 2017 stylised-VFX panel included Epic. Its theme was setting **artistic pillars** for VFX and turning art direction into stylised effects. https://www.youtube.com/watch?v=x30j-PUN1G4
- **[S-snippet]** Audio: GameSoundCon talks by Zak Belica and Seth Weedin on keeping up with the live update cycle. Weedin later covered how content and gameplay audio integrate, plus a "Rave Cave" system built on **bus routing and spatial submixes**. Adam Block covered **Quartz**, UE's sample-accurate music clock, which syncs music to effects and lighting. https://www.unrealengine.com/en-US/blog/get-game-audio-tips-from-our-favorite-talks-at-gamesoundcon (403 on fetch)
- **[S-snippet]** **Visualize Sound Effects** (accessibility option, off by default) draws on-screen ring icons for footsteps, gunfire, chests and gliders. It shows direction but makes above vs below hard to tell. https://www.esports.net/news/fortnite/visual-sound-effects-fortnite/ , https://primagames.com/gaming/how-to-turn-on-visual-footsteps-in-fortnite
- **[S-snippet]** "3D Headphones" option: better spatialisation of tactically important sounds, so footsteps can be read as above or below. https://gamesbeat.com/fortnite-spatial-audio/
- **[I]** For us: a visual sound indicator is a cheap way to cover deaf or muted players, and a lot of mobile and party audiences play muted.

### 2.11 Fall Guys (Mediatonic, Unity)
- **[S]** Built in Unity. https://en.wikipedia.org/wiki/Fall_Guys
- **[S]** Mediatonic said they spent a lot of time on movement so characters felt "clumsy and human" (ragdoll physics). https://www.businessinsider.nl/the-maker-of-fortnite-is-buying-the-british-studio-behind-fall-guys-heres-how-it-went-from-near-disaster-to-launching-one-of-the-biggest-gaming-hits-of-all-time/
- **[S]** Music: the composers used a balloon-inflation recording as a core sound. Mediatonic sent them samples of kids' toys and instruments, with a high-energy synth brief. https://daily.bandcamp.com/features/jukio-kallio-daniel-hagstrom-fall-guys-soundtrack-interview
- **[S-snippet]** A Mediatonic audio-designer job ad asks for FMOD or Wwise. https://stratos-ad.com/index.php?job=49892
- **Gap:** no public VFX or audio system breakdown found. **[I]** The toy-sample palette (balloons, squeaks, plastic) is the closest sourced pointer for our soft-plastic sound identity.

### 2.12 Splatoon (Nintendo)
- **[S-snippet]** The Side Order sound designer built ink sounds from Foley tests: water and slime as a base, then foam beads, pellets, sequins and glass beads, finally **iron beads**, while also changing hand movement and tools. https://gonintendo.com/contents/56997-splatoon-3-sound-designer-explains-the-painstaking-process-of-creating-the-game-s
- **[S]** Toru Minegishi leads Splatoon sound direction. https://www.nintendo.com/us/whatsnew/ask-the-developer-vol-7-splatoon-3-part-1/
- **Gap:** no ink-VFX system details found.

### 2.13 Hades (Supergiant)
- **[S]** Audio middleware went from XACT (Bastion) to FMOD (Transistor onward), later FMOD Studio. Darren Korb does sound design, implementation and VO direction. https://www.gamedeveloper.com/blogs/composer-darren-korb-talks-audio-middleware-and-its-importance-to-game-developers
- **[S]** VFX and UI were by Josh Barnett. Each Olympian god's boon has its own effect family (Zeus thunder, Poseidon waves, Artemis arrows). https://80.lv/articles/a-behind-the-scenes-look-at-the-effects-in-hades/
- **Gap:** no sourced hit-stop or shake numbers for Hades. **[I]** The colour-coding by god is a family-of-effects pattern (one palette and shape set per source) that maps well onto a per-player colour.

### 2.14 Wii Sports / Nintendo (closest analog to our phone-as-controller)
- **[S]** At the 2006 reveal, the Wii Remote speaker played the tennis-ball "pop" each time a player hit the ball. https://www.nintendoworldreport.com/news/11434 , https://nintendoworldreport.com/editorial/11815
- **[S-snippet]** Iwata Asks (Super Mario Galaxy): when the controller speaker played exactly the same sound as the TV, "it lost all meaning", so controller audio should be distinct from TV audio. https://iwataasks.nintendo.com/interviews/wii/super_mario_galaxy/2/3
- **[S-snippet]** Forum view: Wii tennis plays the exact same hit sound every time, and many players turned the remote speaker off. https://forums.dolphin-emu.org/Thread-wiimote-sound
- **[I]** For us: the phone should play a short, tactile, *different* layer (a haptic transient, maybe a tiny click), not a copy of the TV mix. Vary it with hit quality so it avoids the Wii's one-sample problem.

### 2.15 Apple, "Designing Audio-Haptic Experiences" (WWDC19 810): phone haptics
- **[S]** Three principles, from https://developer.apple.com/videos/play/wwdc2019/810 :
  - **Causality:** it must be obvious what caused the feedback. Design sound and haptics as if the objects were physical (material, "hard kick or soft kick", environment).
  - **Harmony:** "things should feel the way they look, the way they sound." Bouncing-ball example: a short precise sound plus a high-sharpness transient, **both scaled by impact velocity**.
  - **Utility:** use moderation and put feedback only on the core interaction.
- **[S]** Haptics and audio are "two instruments" that need not play the same notes "but they do have to play in the same tempo". Adding deliberate latency between visuals and feedback made the illusion "completely not there". The talk gives no millisecond threshold.
- **[S]** Parameters are intensity (amplitude) and sharpness (round/soft → crisp/mechanical). Transients feel like an impact or tap; continuous events give rumble or texture.
- **[S]** Techniques:
  - The first tap of a burst can be missed ("four taps perceived as three"), so a light priming tap can "wake up the skin".
  - Anticipation: ramp a continuous haptic, then cut it right before the sound.
- **[S]** Core Haptics AHAP files can contain `AudioCustom` events (a waveform path in the bundle, with volume and pitch) alongside haptic events, so one pattern carries both in sync. https://developer.apple.com/documentation/corehaptics/representing-haptic-patterns-in-ahap-files

### 2.16 Supercell / mobile VFX budgets
- **[S]** A Brawl Stars Senior VFX job ad says much of the VFX work is outsourced because of content volume, so the in-house role directs outside artists and pushes "quality and performance". https://supercell.com/en/careers/senior-vfx-artist-brawl/2019291
- **[S]** Brawl Stars GDC 2019 (Antti Summala) focused on making it simple and well suited to mobile touchscreens. https://gdconf.com/news/go-inside-design-supercells-new-hit-game-brawl-stars-gdc-2019
- **[S]** Mobile VFX budgets (Stanislav Stabrov, lead VFX at Azur Games, PocketGamer.biz, Aug 2026). https://www.pocketgamer.biz/vfx-optimisation-in-midcore-games-commonly-overlooked-techniques-and-advanced-methods/
  - **Budget by simultaneous copies.** Ten copies × 30 particles = 300; at 2 particles each it drops to 20. Crowded battles may need **3–10 particles per effect**. One effect went from 200 to 50 particles by trimming smoke and sparks.
  - Bake small, frequent, secondary effects into a flipbook texture. Use separate layers only for large, slow or rare effects.
  - Overdraw: doubling quad width and height quadruples screen area. Fill the quad with the image and use trimmed custom meshes for large flashes and shockwaves.
  - Use a shared atlas so particle systems batch under one material. Pass per-effect colour, brightness and scroll values through the **Custom Data** module rather than making new materials.
  - Enable Collision, Noise and Trails only when essential. Fake ground hits with Limit Velocity over Lifetime.
  - Keep shader maths cheap. Avoid GrabPass on mobile. Move uniform work such as UV panning into the vertex shader.
- **[S]** Unity mobile guide: fill rate is the main mobile limit. Reduce particle overdraw, use the simplest shaders, keep alpha-blended screen coverage small, and test by lowering resolution (if it speeds up, you are fill-bound). https://docs.unity3d.com/2019.1/Documentation/Manual/MobileOptimisation.html
- **Gap:** no Supercell-published particle numbers found.
- **[I]** We render on the phone and stream to the TV, so the TV's size makes overdraw *readable* but the phone GPU still pays for it. Budget for the phone.

### 2.17 Fighting-game reference values
- **[S-snippet]** The King of Fighters XIII lists hitstop at **7 frames (light) and 11 frames (heavy)**. https://srk.shib.live/w/The_King_of_Fighters_XIII/Character_States/Hitstun_Blockstun_state
- **[S-snippet]** Street Fighter 6: heavier attacks get longer hitstop, and some Punish Counters get extra-long hitstop. No numbers given. https://srk.shib.live/w/Street_Fighter_6/Game_Data

### 2.18 Game feel theory (Swink)
- **[S]** Steve Swink defines game feel as "real-time control of virtual objects in a simulated space, with interactions emphasised by polish". https://arxiv.org/pdf/2011.09201
- **[S-snippet]** He describes a correction cycle under ~100 ms as feeling like real-time response. https://lizengland.com/blog/review-game-feel-by-steve-swink/
- **[I]** AirPlay adds TV latency. Feedback on the phone (haptic plus a phone-side click) can land under 100 ms even when TV video lags. That makes the phone channel the "truth" for contact timing.

---

## 3. Tooling / process (Unity-specific)

### 3.1 Feel / MMFeedbacks (More Mountains)
**[S]** https://feel-docs.moremountains.com/mmf-player.html , https://feel-docs.moremountains.com/list_mmfeedbacks.html
- An `MMF_Player` is an ordered list of feedbacks played by `PlayFeedbacks(position, intensity)`.
- **Global intensity** scales most feedbacks (1 normal, 0.5 half, 0 off).
- Each feedback has its own Timing (delay, repeat) and a Chance (0–100 %).
- Player-level controls:
  - initial delay
  - **cooldown**
  - duration multiplier and randomised duration
  - `CanPlayWhileAlreadyPlaying`
  - scaled or unscaled timescale, which matters because hit-stop freezes timescale
  - **range gating with distance falloff curve**
- Channels: `MMF_PlayerEvent` broadcasts play and stop to every player on a channel.
- Feedback types include:
  - Freeze Frame and Time Modifier (both need an MMTimeManager)
  - Camera Shake (duration, amplitude, frequency)
  - Cinemachine Impulse
  - Flash
  - Squash & Stretch (mass-conserving) and Squash & Stretch Spring
  - Particles Instantiation (on demand or from a cache) and Particles Play
  - Sound (event, cached or pooled; random pitch and volume; mixer group)
  - **Nice Vibrations** haptics (iOS Core Haptics transients with amplitude and frequency, continuous, `.haptic` clips, presets)
- Authoring workflow: tweak in play mode with "Keep Playmode Changes", or use Copy All / Replace All. Store presets as prefabs. Feedbacks can be added and removed at runtime. A context dictionary passes event data in.
- **[I]** Its architecture (event → preset with an intensity input → timed multi-channel fan-out, plus cooldown, chance and range) is the right model even if we write our own.

### 3.2 Cinemachine Impulse
**[S]** https://docs.unity3d.com/Packages/com.unity.cinemachine@2.8/manual/CinemachineImpulseSource.html , https://docs.unity3d.com/Packages/com.unity.cinemachine@3.1/manual/CinemachineImpulseListener.html
- An Impulse Source emits a signal shaped by an **attack / sustain / decay** envelope.
- **"Scale With Impact"** makes stronger impacts last longer.
- An Impulse Listener on the camera applies it, with Gain and channel masks.
- Distance-based with an impact radius.

### 3.3 Unity audio scheduling, voices and ducking
- **[S]** `AudioSource.PlayScheduled(dspTime)` gives sample-accurate starts. Schedule **~100–200 ms ahead**. If the time is already past, playback starts as soon as possible. https://docs.unity3d.com/6000.6/Documentation/ScriptReference/AudioSource.PlayScheduled.html
- **[S]** Real voices are the maximum audible at once. Virtual voices are the maximum managed; past that limit, sounds stop. Default project values are **32 real / 512 virtual**, seen in a default AudioManager.asset. https://docs.unity3d.com/ScriptReference/AudioConfiguration.html
- **[S]** The Audio Mixer **Duck Volume** effect gives sidechain ducking driven by a Send from another group. Snapshots hold mixer states. https://docs.unity.com/en-us/engine/6000.5/manual/audio/mixer/inspectors.md
- **[S]** The Audio Random Container (Unity 6) randomises clip, pitch and volume for footsteps, impacts and similar sounds. https://docs.unity.com/en-us/engine/6000.0/manual/audio/random-container/create-randomized-playlist.md

### 3.4 Sound layering
- **[S]** Common practice is attack/transient + body + tail (plus sub and mechanical layers or "sweeteners"). Transients must line up. A body without a transient feels muffled, and a transient without a body feels "thin and toy-like". Long tails muddy fast action. https://violetrecording.com/how-to-make-impact-sounds/ , https://violetrecording.com/how-to-design-weapon-sounds/ , https://www.wayline.io/learn/game-audio/1
- **[I]** "Toy-like" is half our brief. Soft-plastic hits want a crisp transient (plastic tick), a short rounded body (rubber thump) and a very short tail, plus a sweetener layer by hit quality, for example a bright chime for a perfect timing hit.

---

## 4. Cross-game patterns

1. **One contact event fans out to every channel in one place.** Celeste's dash runs freeze, rumble, shake, distortion, particles, trail and SFX from one function. Feel's MMF_Player formalises the same idea. **[S]**
2. **Strength drives everything.** Smash hitlag rises linearly with damage, Celeste's landing squash scales with fall speed, Cinemachine's Scale With Impact lengthens the envelope, and Apple scales haptic intensity and sound amplitude by impact velocity. **[S]**
3. **Hit-stop has a floor and a cap.** Values run from roughly 1 frame (Vlambeer, 10–20 ms) through 3 frames (Celeste dash) and 7–11 frames (KOF) to 15+ frames, capped at 30 (Smash Ultimate). **[S]**
4. **Freeze both parties, but let the attacker drift a little and shake the victim more.** From Sakurai's list. **[S]**
5. **Shake is additive and decays, and it never accumulates without limit.** Vlambeer adds 4; trauma models clamp at 1 and square the value. **[S]**
6. **Directional beats random.** Celeste shakes along the dash direction; Sakurai shakes horizontally on the ground and vertically in the air. **[S]**
7. **In 3D, prefer rotational shake** so the camera never clips into geometry. This is Eiserloh's advice per a secondary source. **[S-snippet]**
8. **Scale shake by camera distance or range,** with Sakurai's distance-based shake and Feel/Cinemachine range falloff. **[S]**
9. **Haptics use a small fixed vocabulary.** Celeste uses 3 strengths × 2 lengths, the Feel/Nice Vibrations presets work the same way, and Apple's transients are tuned with intensity and sharpness. **[S]**
10. **Haptics and audio share a tempo, not a waveform.** Latency between them kills the illusion. **[S]** (Apple)
11. **The controller channel must differ from the TV channel.** Iwata: identical sound on both "lost all meaning". **[S-snippet]**
12. **Audio priority means importance, not raw loudness.** Overwatch ranks threat; Frostbite HDR culls by loudness as a stand-in for importance; Rocket League ducks crowd and ambience under cars and the ball. **[S]**
13. **Duck the bed, don't boost the hero sound.** Rocket League HDR makes "other sounds quieter". **[S]**
14. **Mix for the real listening device.** Rocket League remixed for headphones after mixing on loud speakers. Our case is TV speakers plus the phone speaker. **[S]** / **[I]**
15. **Give the player a dynamic-range setting.** Rocket League ships Low, Medium and Theater. **[S]**
16. **Sounds and VFX belong to families keyed to their source.** Hades uses one effect family per god; Overwatch has a unique footstep per hero; LoL ties colour to type (heal green, frost blue). **[S]**
17. **When colour is taken (team or customisable colours), shape carries the meaning.** Overwatch World Cup skins forced shape-language changes. This matters directly to us because player colours are customisable. **[S-snippet]**
18. **Readability: one primary shape, mid-range values, saturation reserved for focus, and size scaled to importance.** **[S]** (LoL)
19. **Timing: anticipation → impact → short dissipation, and keep effects short** because long effects clutter the screen. **[S]** (LoL)
20. **Fake detail cheaply:** a first-frame circle as a muzzle flash, a white flash frame, "big eyes" reaction frames. **[S]** (Vlambeer)
21. **Permanence sells impact:** marks and props that stay after the hit (Vlambeer). **[S]** **[I]** For us: ball scuffs on clay, divots, a lingering chalk puff.
22. **Budget particles by simultaneous instances, not per effect.** Overdraw is the real mobile limit, so use atlases plus Custom Data to batch. **[S]**
23. **Presets plus play-mode tuning plus copying values back** is how small teams author feel quickly (Feel). **[S]**
24. **Clarity is separate from correctness.** VALORANT's "bad hit reg" was mostly a presentation problem, so fix feel before blaming physics. **[S-snippet]**
25. **Add a visual stand-in for audio cues** (Fortnite Visualize Sound Effects), since many party and mobile players play muted. **[S-snippet]** / **[I]**

---

## 5. Numbers we can steal

At 60 fps, 1 frame = 16.7 ms. Every row is tagged sourced or inference.

### Hit-stop / freeze
| Value | Context | Tag |
|---|---|---|
| 10–20 ms (about 1 frame) | every bullet hit, Nuclear Throne | [S] infovore |
| 50 ms (3 f) | Celeste dash start | [S] Player.cs |
| 100 ms (6 f) | Celeste explode-launch (big event) | [S] Player.cs |
| 7 f light / 11 f heavy | KOF XIII | [S-snippet] |
| about 8 / 9 / 15 f for a 15 % hit | Melee / Brawl-Smash 4 / Ultimate | [S-snippet] SmashWiki |
| Ultimate: `0.65·d + 6` frames, cap 30 f | formula | [S-snippet] SmashWiki |
| **Proposal:** `hitstopFrames = clamp(round(2 + 6·q), 2, 8)` for tennis and golf contact, where q ∈ [0,1] is hit quality or power. Perfect smash about 8 f, weak tap about 2 f. Game point / match point "boss stop": 12–20 f plus a short slow-mo ramp back to normal (Sakurai). | | [I] |

### Screen shake / camera
| Value | Context | Tag |
|---|---|---|
| +4 px per shot, fast decay, at 240 px height (about 1.7 % of screen height) | Vlambeer | [S] |
| camera kick 6 px opposite the aim (about 2.5 % of height) | Vlambeer | [S] |
| directional shake 0.2 s on dash, 0.1 s on bounce | Celeste | [S] |
| trauma 0–1, shake = trauma² (or ³), maxAngle 10°, maxOffset 30 px, decay 0.02 per update | npm screen-shake, built on Eiserloh's talk | [S-snippet] |
| 3D: rotation-only shake | Eiserloh via secondary source | [S-snippet] |
| **Proposal:** TV camera max roll/yaw 1.5–3° at trauma 1. Perlin noise at about 15–25 Hz. Trauma decay of about 1.5 per second. Contact adds 0.15–0.5 trauma by quality. Use Cinemachine Impulse with attack about 0.02 s, sustain 0, decay 0.15–0.35 s, Scale With Impact on. Add an "AirPlay comfort" multiplier of 0.5–0.7, because a big TV makes shake look larger. | | [I] |

### Squash & stretch
| Value | Context | Tag |
|---|---|---|
| jump (0.6, 1.4); super (0.5, 1.5); land up to (1.6, 0.4) scaled by speed / max speed; recover at 1.75 per second | Celeste | [S] |
| **Proposal:** ball squash on contact (1.3, 0.75) at full power, 2–3 frames, mass-conserving | | [I] |

### Haptics (phone)
| Value | Context | Tag |
|---|---|---|
| 3 strengths × 2 lengths vocabulary | Celeste | [S] |
| Core Haptics transient: intensity 0–1 and sharpness 0–1. Scale intensity with impact velocity. Use a priming tap for important alerts. | Apple | [S] |
| **Proposal:** contact = transient with intensity 0.4 + 0.6·q and sharpness 0.5 + 0.4·q, fired on the phone in the same frame as the contact is detected (never routed back via TV time). Perfect hit = transient plus a 60–80 ms continuous tail at about 0.3. | | [I] |

### Audio
| Value | Context | Tag |
|---|---|---|
| 20–30 sounds stack at once in a match | Rocket League | [S] |
| 32 real / 512 virtual voices | Unity defaults | [S] |
| HDR bus at −12 to −18 dB, UI and critical VO outside HDR | Wwise early guidance | [S-snippet] |
| HDR window ~130 dB logical range, 16-bit output OK | DICE | [S-snippet] |
| PlayScheduled lead of 100–200 ms (for music and stingers, not for contact SFX) | Unity | [S] |
| Pitch randomisation ±1–2 semitones (about ±6–12 % pitch), volume ±1–2 dB, 3–5 round-robin variants per impact. I found **no** source for this. | | [I] |
| **Proposal:** voice caps per category: contact SFX 4, footsteps 4 per hero, crowd/ambience 2 beds, UI 4, VO 1–2 with priority. Duck crowd and music 3–6 dB for 300–500 ms on every contact, and 8–12 dB on point won (Rocket League "make others quieter"). | | [I] |

### Particles / overdraw (mobile)
| Value | Context | Tag |
|---|---|---|
| 3–10 particles per effect in crowded scenes; budget = per effect × simultaneous copies; one effect cut from 200 to 50 particles | Azur Games | [S] |
| Doubling quad width and height = 4× overdraw cost; trimmed meshes for big flashes | Azur Games | [S] |
| **Proposal:** contact burst ≤ 24 particles plus 1 mesh ring (shockwave). Total live particles ≤ 300. Alpha-blended screen coverage ≤ 25 % of the frame at peak. One shared VFX atlas and material, with per-event colour through Custom Data. | | [I] |

### Latency
| Value | Context | Tag |
|---|---|---|
| < ~100 ms correction cycle feels like real-time response | Swink, via a review | [S-snippet] |
| **Proposal:** phone haptic and click within one frame of contact detection on the phone. The TV-side shake, freeze and SFX are driven by the same `ContactEvent` id and timestamp, so all channels in the TV process happen in one frame. | | [I] |

---

## 6. Gaps / not found
- Fall Guys VFX and audio system architecture (no public talk found).
- Rocket League ball-hit strength mapping and middleware; how goal explosions are built.
- Hades hit-stop and shake values.
- Splatoon ink VFX system.
- Supercell's published particle or audio budgets.
- Exact slide formulas from Eiserloh; the Overwatch threat-mix RTPC values (they are in the Wwise Tour video, which I did not watch).
- Riot VFX style guide PDF itself (the /dev URL now redirects to the LoL home page).
- A sourced pitch-randomisation range.
