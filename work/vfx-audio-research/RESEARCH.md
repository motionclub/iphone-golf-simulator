# Research: how top games built VFX, hit sound, haptics and camera feel (2026-10-17)

For Adnan. This is research only: nothing in the game was changed. The detail, with a URL on every claim, is in three notes files:
- [notes/research_sports.md](notes/research_sports.md): sports games.
- [notes/research_feel.md](notes/research_feel.md): action and "juice" games, plus talks.
- [notes/research_tech.md](notes/research_tech.md): Unity, iOS and AirPlay tech, plus sourcing and licences.

This page is the summary, with the most important source for each claim.

**Tags.** **[S]** means a source says it (the link is given). **[O]** means it is our own observation or inference. **[V]** means it still needs checking against footage.
**Videos.** Every YouTube id below was checked against YouTube's oEmbed endpoint on 2026-10-17 (title and channel match). Nothing was downloaded, and **no clip was played or frame-stepped** (a frame-step pass was stopped, so none is claimed). The only known timestamp is Wii Sports tennis at 0:00:14. For every other clip, [REFERENCE_BOARD.html](REFERENCE_BOARD.html) says what to look for. One id the research agent returned, `MbHumqb00Yg`, turned out to be a different game ("Casual Sport Series: Tennis"), so it was dropped.

**What sources exist.** Studios rarely publish how they built sports-game sound and VFX. The best primary sources are Nintendo's own interviews ("Ask the Developer", Iwata Asks), Apple's WWDC haptics talks, GDC talks, and public code (Celeste). Where there is no primary source, the notes say so instead of guessing.

---

## Part A: Sports games

### Wii Sports / Wii Sports Resort / Wii Sports Club (Nintendo)
- **The controller played the hit.** At the 2006 reveal, the Wii Remote speaker played the tennis ball "pop" on every hit, and the rumble motor fired on contact **[S]** ([NWR](https://www.nintendoworldreport.com/news/11434), [Hexus E3 hands-on](https://hexus.net/gaming/news/wii/5607-e3-2006-live-massive-wii-games-hands-on/?page=2)). The speaker was very low-fi (4-bit ADPCM / 8-bit PCM) and the rumble was on/off only **[S]** ([WiiBrew](https://wiibrew.org/wiki/Wiimote)).
- **Nintendo's rule for the controller speaker:** never copy the TV. The Super Mario Galaxy sound team found that doubling the TV sound in the hand "lost all meaning". They used the speaker only for the player's own physical actions, sometimes as a slightly delayed echo, so the sound "lands in your hand" **[S]** ([Iwata Asks, Super Mario Galaxy, sound team](https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-Super-Mario-Galaxy/Volume-3-The-Sound-Team/4-Sound-Effects-You-Can-Feel/4-Sound-Effects-You-Can-Feel-205134.html)).
- **Players turned the speaker off** because the same hit sound played every time **[S, forum]** ([Dolphin forum](https://forums.dolphin-emu.org/Thread-wiimote-sound)). Lesson: vary the hand-side sound by hit quality.
- **Slower balls hide input lag.** Kenta Sato said tennis's slower rallies hid input delay, and table tennis needed MotionPlus **[S]** ([Iwata Asks, Wii Sports Resort](https://www.nintendo.com/fr-fr/Iwata-demande/Iwata-demande-Wii-Sports-Resort/Iwata-Asks-Wii-Sports-Resort/5-Le-tennis-passe-a-table/5-Le-tennis-passe-a-table-220402.html)). Our AirPlay delay works the same way: the phone carries the "now".
- **Crowd as feedback.** There are two cheer types (applause, and a whole-crowd "wow" on comebacks), and the crowd grows with skill rating **[S, guide]**. In Wii Sports Club, opponent Miis stomp in frustration after a corner smash, and the developers were "always grinning" while testing it **[S]** ([Iwata Asks, Wii Sports Club](https://www.nintendo.com/en-gb/Iwata-Asks/Iwata-Asks-in-Motion-Wii-Sports-Club/Wii-Sports-Club/3-When-Mii-Characters-Get-Frustrated/3-When-Mii-Characters-Get-Frustrated-823820.html)).
- **Second screen shows the lie.** In Wii Sports Club golf, the GamePad shows the ball at your feet, so you can tell rough from bunker at a glance **[S]**. Our phone could do the same.
- Footage: `OsnNlg_Sask` (tennis from 0:00:14), `bMnN3m_5X-A`, `1hEVZTld8u4` (hole-in-one celebrations).

### Nintendo Switch Sports (2022, golf added Nov 2022)
Primary source: [Ask the Developer Vol. 5](https://www.nintendo.com/sg/interview/as8s/).
- **Motion sounds come first in the mix.** Earlier entries had no music in matches. Switch Sports added music but placed it as if it plays from speakers in the venue, mixed under the swing and hit sounds. Each venue's reverb was tuned **[S]** ([part 3](https://www.nintendo.com/sg/interview/as8s/03.html)).
- **Sound shaped the art.** A robot-athlete concept was dropped partly because mechanical clunks would compete with the motion sounds **[S]**.
- **Latency vs accuracy.** Waiting for the full swing felt "one step behind". Early detection was right only 80–90% of the time, and they pushed it past 90% **[S]** ([part 2](https://www.nintendo.com/sg/interview/as8s/02.html)).
- **Perfect serve:** a hit at the top of the toss turns the ball trail red and gives a faster ball **[S, guide]**.
- Footage: `T9MhqWwhsIA` (official gameplay trailer), `LivrZI3_TPc` / `NDLfV1dhiok` (golf update).

### Mario Tennis Aces (2018) and Mario Tennis Fever (Feb 2026), by Camelot
- **The clearest hit-strength ladder in the genre:** normal → charge → Trick → Zone → Special. Each step adds a channel:
  - a stronger trail
  - time slowdown (Zone Speed / Zone Shot)
  - a camera change to first person
  - a short pose cutscene (Special)
  - a consequence: racket damage on badly blocked Zone or Special shots **[S]** ([Mario Wiki](https://www.mariowiki.com/Mario_Tennis_Aces))
- **Trail colour means shot type:** red topspin, blue slice, purple flat, orange lob, white drop **[S]**.
- **Tension haptics:** the Joy-Con pulsed like a heartbeat before match-point serves **[S]** ([Nintendo Wire](https://nintendowire.com/features/impressions-mario-tennis-aces-set-to-serve-up-some-fun-this-summer/)).
- **Rarity matters (Fever, 2026).** Reviewers found top-tier Fever Shots tiresome because both sides fire them every point **[S]** ([Dexerto](https://www.dexerto.com/gaming/mario-tennis-fever-review-3315802/)). Big effects must stay rare.
- Footage: `0lPJCJqpcK8` (Direct trailer), `J7NG82-2iXs` (all Zone Shots), `A5BUIycx8iE` (all Special Shots), `0qlPHM5wQyY` / `iP5MGnurtLQ` (Fever).

### Mario Golf: Super Rush (2021)
- **Special shots make shockwaves that push other players' balls**, because golf is otherwise solo. The team rejected a tennis-style Zone Shot as against the spirit of golf **[S]** ([Nintendo Everything interview](https://nintendoeverything.com/mario-golf-super-rush-interview-opening-swing-mode-more/)).
- **They removed the impact timing click.** The shot gauge **bends to show slope**, and the game tries to show *why* a shot missed **[S]**.
- **Celebrations are gated by outcome.** Confetti plays on a Nice Shot. Across the series, no "Nice Shot" is called if the ball is heading for a hazard **[S]** ([Mario Wiki: Nice Shot](https://www.mariowiki.com/Nice_Shot)).
- Footage: `g__umJvdlh4` (all 16 special shots), `ds-0l01i2hs`.

### Everybody's Golf / Hot Shots Golf (Clap Hanz, founded by ex-Camelot staff)
- A perfect shot or chip-in eagle gets "plenty of visual effects", and a complete miscue gets its own comic effect, the series' charm. One reviewer found it "a little busy" **[S]** ([Press Start](https://press-start.com.au/reviews/playstation4-reviews/2017/08/29/everybodys-golf-review-old-friend-returns/)).
- The perfect-impact window changes size with club and lie **[S]**.
- Footage: `bwMnPKKf5uo`, `_K5R5fkh6po`.

### Golf Story / Sports Story (Sidebar Games)
- The designer's aim was golf's "vibe: the sounds, sights and characters" **[S]**. No hit-SFX or VFX breakdown exists. Footage: `YyjTzc7EH4I`, `geq1XrcqgHM`.

### TopSpin 2K25 (Hangar 13 / 2K)
- **The post-shot label explains the outcome** (perfect / good / too soon / too late), so timing never feels unfair **[S]** ([Shacknews](https://shacknews.com/article/139582/topspin-2k25-review-top-spin)).
- **Surfaces leave lasting marks.** On clay, slides kick up dust and leave scuffs, and the court is swept between sets. On grass, the baseline wears to dirt over a tournament **[S]** ([2K Centre Court Report](https://2k.com/games/topspin-2k/topspin-2k25/centre-court-report/gameplay/)).
- There is no commentary, only a PA announcer, and reviewers called the crowd lacklustre **[S]**.
- Footage: `7eNj6n6WUmQ` (gameplay showcase), `3a3Er6BhL24` (timing-feedback UI).

### PGA Tour 2K21/2K23/2K25 (HB Studios), EA Sports PGA Tour
- **You can hear strike quality at contact.** Reviewers say a pure strike and a poor strike sound clearly different **[S]** ([SGO review](https://www.sportsgamersonline.com/games/pga-tour-2k23-review/)).
- **Commentary talks to you, not about you.** The in-house audio designer voices it. It began as placeholder lines, because a computer voice couldn't give the right tone **[S]** ([PocketGamer.biz interview](https://www.pocketgamer.biz/interview/73766/pga-tour-2k21-john-mccarthy-interview/)). That makes a cheap in-house announcer a proven route.
- EA PGA Tour drives shots from ShotLink and TrackMan data. Its audio and VFX are not documented **[S]**.
- Footage: `9okRdqlh3_Q` (2K25), `0ZCOFsKQuGI`, `VUGvJ3WPDUk` (EA).

### Golf Clash (Playdemic/EA) and Tennis Clash (Wildlife), mobile
- **Golf Clash:** a slingshot pull, graded Great / Perfect / Sliced. A perfect release still loses to bad wind or a bad lie. Both players watch the same camera, so watching the opponent teaches you **[S]** ([Game Developer UX review](https://www.gamedeveloper.com/design/ux-review-golfclash-s-swing-to-success-)). Players who lose feel they could have played better **[S]**.
- **Tennis Clash:** swipe length sets power and direction sets aim. The satisfaction comes from placing the ball where you meant to **[S]** ([GameAnalytics](https://www.gameanalytics.com/blog/how-tennis-clash-scored-a-golden-set)).
- Footage: `CeOY62p0Tmo` (Perfect shot tutorial), `5JvngTcVAVo` (Tennis Clash gameplay).

### AO Tennis 2, Matchpoint Tennis Championships
- **A crowd that ignores a long rally reads as broken** **[S]** (AO Tennis 2 reviews).
- **Shot power changes the strike sound itself**, not just its volume **[S]** ([Matchpoint review](https://www.theouterhaven.net/2022/07/matchpoint-tennis-championships-solid-fundamentals-lots-to-learn/)).

### Sports-science evidence for hit sound
- In Loughborough golf studies, golfers' sense of "feel" tracked **impact-sound loudness and sharpness** more strongly than hand vibration. In putting, a louder and sharper sound (peaks around 2–4 kHz) was judged "harder, faster" **[S]** ([Loughborough repository](https://repository.lboro.ac.uk/articles/journal_contribution/Assessment_of_the_impact_sound_in_golf_putting/9564332)).
- A tennis racket impact is an **initial impulsive crack plus a quieter, longer ring** **[S]** ([Banwell thesis](https://dspace.lboro.ac.uk/dspace-jspui/handle/2134/13678)). That is a natural transient + body + tail.

---

## Part B: Action and "juice" games, and talks

### Super Smash Bros. (Sakurai): hit-stop as a strength function
- Hit-stop (hitlag) grows **linearly with damage, with a floor and a cap**. Ultimate is about `0.65·damage + 6` frames, capped at 30. A 15% hit freezes about 8 frames in Melee, 9 in Brawl/Smash 4 and 15 in Ultimate **[S, wiki]** ([SmashWiki: Hitlag](https://ssbwiki.com/Hitlag)).
- **The sweet spot freezes longer than the edge** (Marth's tip). Hit-stop is **kept short in multiplayer** because a freeze opens a window for third parties **[S]** ([Source Gaming, Famitsu column](https://sourcegaming.info/2015/11/11/thoughts-on-hitstop-sakurais-famitsu-column-vol-490-1/)).
- **Eight techniques** (`tycbMSjDDLg`):
  1. Shake the victim more.
  2. Keep the hitbox still.
  3. Shake horizontally on the ground and vertically in the air.
  4. Decay the shake.
  5. Control the amount.
  6. Interpolate into the damage pose.
  7. Let the attacker keep moving a little.
  8. Scale the shake with camera distance.
- "Stop for Big Moments" (`OdVkEOzdCPw`) covers a short freeze plus a slow-motion snap-back for KOs and boss defeats.

### Celeste: shipped values from the public source
- **Every channel fires from one place.** One dash event triggers:
  - freeze 0.05 s
  - rumble Strong/Medium
  - a distortion ring
  - directional shake 0.2 s
  - burst particles
  - trail sprites
  - a direction-specific sound **[S]** ([Player.cs](https://raw.githubusercontent.com/NoelFB/Celeste/master/Source/Player/Player.cs))
- **Rumble is a fixed vocabulary of 3 strengths × 2 lengths**, picked per event.
- **Landing squash scales with fall speed:** up to (1.6, 0.4), recovering at 1.75 per second.

### Vlambeer, "The Art of Screenshake" (`AJdEqssNZ-U`)
- A 10–20 ms hit-pause on every hit, plus a white flash frame.
- Shake is **additive and decays**: +4 px per shot, and a 6 px camera kick.
- Hits play a material sound (meat / plant / rock / metal) mixed with the hurt sound.
- Props keep **permanent marks** **[S]** ([infovore write-up](https://infovore.org/?p=5275)).

### "Juice it or lose it" (Jonasson & Purho, `Fy0aCDmgnxg`) and Swink, *Game Feel*
- Juice is "maximum output for minimum input": tweening, squash, particles, sound per hit **[S]**.
- A correction cycle under about 100 ms feels like real-time control **[S, review]**.

### Eiserloh, "Juicing Your Cameras With Math" (GDC 2016, `tu-Qe66AvtY`)
- **The trauma model:** events add to a 0–1 trauma value that decays. Shake equals trauma² × max × Perlin noise. **In 3D, prefer rotation-only shake** so the camera can't clip into walls **[S + derived implementations]**.

### Overwatch (Blizzard)
- **"Play by Sound"** has five audio pillars: hero VO, clear mix, gameplay information, pinpoint accuracy, Pavlovian response **[S, snippet]**.
- **The mix ranks threat, not loudness.** An enemy aiming at you outranks a closer enemy who isn't. They replaced Wwise HDR with their own priority system **[S]** ([PCGamesN](https://pcgamesn.com/overwatch/overwatch-devs-on-creating-a-game-you-can-play-by-sound-and-announcing-dolby-atmos-support)).
- **When skins recoloured effects, colour stopped carrying meaning**, so the team changed the *shape language* of some abilities **[S, snippet]**. This applies directly to us: player colours are customisable.

### League of Legends VFX style guide (Riot)
Ten rules ([VFX Apprentice summary](https://www.vfxapprentice.com/blog/10-league-of-legends-vfx-design-tips)):
1. One primary shape.
2. Size and intensity match importance.
3. Mid-range values.
4. Glow shows power and direction.
5. Avoid 0% and 100% saturation.
6. One dominant colour plus a secondary.
7. Mixed hard and soft edges.
8. Smear in the direction of travel.
9. Anticipation, then impact, then time to read.
10. **Keep effects short.**

The guide was written because many teams were making inconsistent effects **[S]**.

### Rocket League and Frostbite: HDR mixing
- **Rocket League's HDR "makes other sounds quieter"** so the important sounds stand out. 20–30 sounds stack at once. It was remixed for headphones, and it ships a dynamic-range setting (Low / Medium / Theater) **[S]** ([Psyonix via devtrackers](https://devtrackers.gg/rocket-league/p/d0e83f63-under-the-hood-an-inside-look-at-hdr-audio-coming-to-rocket-league)).
- Frostbite HDR culls sounds by loudness, used as a stand-in for importance **[S, slides]**.

### Fortnite, Fall Guys, Splatoon, Hades
- **Fortnite:**
  - The GDC 2017 stylised-VFX panel (`x30j-PUN1G4`) covered **VFX art-direction pillars** **[S]**.
  - Epic's Quartz clock syncs music to effects and lighting **[S, snippet]**.
  - "Visualize Sound Effects" draws on-screen rings for important sounds, which helps players who play muted **[S, snippet]**.
- **Fall Guys** (Unity): the soundtrack was built around a **balloon-inflation recording plus kids' toy samples** **[S]** ([Bandcamp interview](https://daily.bandcamp.com/features/jukio-kallio-daniel-hagstrom-fall-guys-soundtrack-interview)). This is the closest sourced pointer to our soft-plastic sound. No VFX breakdown exists.
- **Splatoon:** ink sounds came from Foley tests with water, slime, foam beads, pellets and finally iron beads **[S, snippet]**.
- **Hades:** each god has its own effect family (shapes and colour) **[S]** ([80.lv](https://80.lv/articles/a-behind-the-scenes-look-at-the-effects-in-hades/)). It moved from XACT to FMOD **[S]**.

### Apple, "Designing Audio-Haptic Experiences" (WWDC19 810) and Core Haptics (520, 223; WWDC21 10278)
- **Three principles:** Causality (obvious cause), Harmony (feels the way it looks and sounds), Utility (use it sparingly) **[S]** ([WWDC19 810](https://developer.apple.com/videos/play/wwdc2019/810)).
- **Sound and haptic are "two instruments, same tempo."** Any delay between them breaks the illusion. Scale both by impact velocity. Transient haptics are for impacts, continuous ones for texture or tension **[S]**.
- A light priming tap can "wake up the skin" before an important burst **[S]**.

### Mobile VFX budgets (Azur Games, PocketGamer.biz, Aug 2026)
- **Budget by simultaneous copies.** Crowded scenes may need 3–10 particles per effect. One effect went from 200 to 50 particles **[S]** ([PocketGamer.biz](https://www.pocketgamer.biz/vfx-optimisation-in-midcore-games-commonly-overlooked-techniques-and-advanced-methods/)).
- Use a shared atlas plus the Custom Data module, so per-effect colour batches under one material. Use trimmed meshes for large flashes, because overdraw is the real limit **[S]**.

---

## Part C: Tech facts that decide our choices (detail in [notes/research_tech.md](notes/research_tech.md))

| Question | Finding | Source |
|---|---|---|
| VFX Graph on iPhone? | VFX Graph 17.3 is **still preview for URP and for mobile**. On 2025-12-01 Unity staff said it is "not officially supported on mobile". | [VFX Graph requirements](https://docs.unity3d.com/Packages/com.unity.visualeffectgraph@17.3/manual/System-Requirements.html), [Unity Discussions](https://discussions.unity.com/t/vfx-graph-not-visible-on-android-and-ios-after-upgrading-from-2022-3-50-to-6000-2/1697740) |
| Particle instancing on 6000.3 | Shuriken mesh particles instance with the URP particle shaders or a hand-written HLSL shader. **Shader Graph particle instancing only arrives in 6.6.** | [Unity manual](https://docs.unity3d.com/6000.3/Documentation/Manual/PartSysInstancing.html), [Discussions 2026-06](https://discussions.unity.com/t/shuriken-particles-shader-graph/1669355/11) |
| Fill-rate on Apple GPUs | Hidden-surface removal is free for **opaque**. Translucency costs overdraw. Draw opaque first, then alpha-test, then blend. | [WWDC20 10602/10632](https://developer.apple.com/videos/play/wwdc2020/10632) |
| Soft particles | Need the depth texture (CopyDepth or prepass). We have depth on, but should not *depend* on it for VFX. | [URP Particles Lit](https://docs.unity3d.com/6000.3/Documentation/Manual/urp/particles-lit-shader.html) |
| Unity audio vs FMOD/Wwise | Unity 6 has the **Audio Random Container** (since 2023.2: random, shuffle, avoid-repeat, pitch/volume ranges), AudioMixer snapshots and ducking, `PlayScheduled`, and 6.3 scriptable processors. FMOD Indie is probably free for us (sources conflict on the threshold). Wwise Indie is free under a $250K budget. Both would be a second audio engine next to voice chat and Core Haptics. | [ARC](https://docs.unity3d.com/Manual/AudioRandomContainer-UI.html), [FMOD Unity](https://www.fmod.com/docs/unity), [Wwise pricing](https://www.audiokinetic.com/en/wwise/pricing/for-games/) |
| AirPlay route change | Unity's Classic audio foundation (≤ 6.6, which includes us) **resets the whole audio engine** on a device change when the format differs. The fix (Enhanced Audio Foundation) arrives in 6.7. | [Unity 6.7 audio foundations](https://docs.unity.com/en-us/engine/6000.7/manual/audio/foundations.md) |
| Phone-speaker sound during AirPlay | **System Sound Services only.** It "plays locally on the device speakers; it does not use audio routing". It plays one sound at a time, PCM/IMA4 only, has no volume control, and obeys the silent switch. | [Apple docs](https://developer.apple.com/documentation/audiotoolbox/audioservicesplaysystemsound(_:)), [Apple DTS 2024-12](https://developer.apple.com/forums/thread/770154) |
| Voice chat + AirPlay | PlayAndRecord allows **mirrored AirPlay only**, `.voiceChat` mode blocks AirPlay, and multiRoute excludes AirPlay. | [Apple QA1803](https://developer.apple.com/library/archive/qa/qa1803/_index.html) |
| AirPlay mirroring delay | Video and audio arrive together, roughly 100–200 ms late (community and vendor figures; Apple publishes none). | [AirServer](https://support.airserver.com/support/solutions/articles/43000531769-what-is-the-airplay-screen-mirroring-protocol-) |
| Audio formats | ADPCM + Decompress On Load for short hits. Vorbis Compressed-In-Memory for ambience. Vorbis Streaming for music. | [Unity AudioClip](https://docs.unity3d.com/6000.0/Documentation/Manual/class-AudioClip.html) |
| Feel toolkit | Feel (MoreMountains, about $50, needs 6000.0.23+) is a good model to copy (`MMF_Player`: intensity, cooldown, chance, range, channels), but its haptics path would duplicate `GolfHaptics.mm`. | [Feel docs](https://feel-docs.moremountains.com/mmf-player.html) |
| Sound libraries and AI | Sonniss GDC bundles: free, no attribution, **no AI training**. Freesound: only CC0 and CC-BY are usable. ElevenLabs SFX: the free plan needs attribution. Stable Audio: free under $1M revenue (verify). | see notes §7 |

---

## Part D: Cross-game patterns (what every good one does)

Ranked by how much each matters for **our** game. Each pattern lists the games that show it.

1. **One contact event fans out to every channel from one place,** sharing one timestamp: VFX, sound, haptic, UI and camera (Celeste dash, Feel `MMF_Player`). *We do this by hand in 5 copies.*
2. **Hit quality changes the timbre, not just the volume.** The sweet spot is louder, crisper and brighter (Matchpoint, PGA 2K, Loughborough, Sakurai tip vs edge). *Our tiers exist in data, but you can't hear them.*
3. **The hand (controller) plays only your own contact; the TV carries the world** (Wii speaker, Super Mario Galaxy rule, Apple Causality). *The phone is our "now" channel, because the TV is about 100–200 ms late.*
4. **Haptic and sound share a tempo,** scaled by impact strength (Apple 810, Celeste's fixed rumble vocabulary).
5. **A tier ladder adds one channel per step** (Aces normal → charge → Trick → Zone → Special; Super Rush specials). The **top tier stays rare** (Fever criticism, Everybody's Golf "busy", Sakurai keeping multiplayer hit-stop short).
6. **Trail colour or style carries the shot's grade or type while the ball is in the air,** where the eye already is (Aces, Switch Sports red serve, Wii power serve, Mario Golf gold streak).
7. **Every shot gets a short, named grade that explains the result** (TopSpin, Golf Clash, Mario Golf Nice Shot, Super Rush "why it missed").
8. **Celebrations are gated by outcome, not input** (Mario Golf: no "Nice Shot" into a hazard).
9. **Failure gets its own funny beat** (Everybody's Golf miscue, frustrated Miis, Aces racket-break).
10. **Duck the bed, don't boost the hero sound** (Rocket League HDR, Switch Sports music under swings, Overwatch priority mix).
11. **Crowds track rally length and tension.** A flat crowd reads as broken (AO Tennis 2 negative example, Wii comeback "wow").
12. **Music never masks hits**: none at all, or diegetic venue music ducked under SFX (Wii Sports, Switch Sports).
13. **Surfaces have their own sound and leave lasting marks** (TopSpin clay scuffs and grass wear, Vlambeer prop marks, Wii Sports Club lie view).
14. **Effects come in families keyed to their source** (Hades god families, Overwatch hero footsteps). **When colour is customisable, shape carries the meaning** (Overwatch World Cup skins).
15. **Readability: one primary shape, mid-range values, size scaled to importance, keep it short** (Riot).
16. **Timing curve: anticipation → impact → short dissipation** (Riot, LoL, Overwatch "animation principles").
17. **Weight without stopping time** is possible: squash and stretch (Celeste), a white flash frame and big-eyes frames (Vlambeer), opponent reaction (Wii Sports Club), shake on the *hit object* not the camera (Sakurai #1). *This matters because Adnan has ruled out camera shake and hit-stop.*
18. **If hit-stop is used, it's linear in strength with a floor and cap, and short in multiplayer** (Smash, KOF 7/11 f, Celeste 3 f, Vlambeer 1 f).
19. **Respond on the earliest confident sample.** Waiting feels "one step behind" (Switch Sports at 80–90%+, Wii Resort).
20. **Tension haptics are separate from hit haptics** (Aces match-point heartbeat).
21. **Budget particles by simultaneous copies; overdraw is the real mobile limit** (Azur, Unity, Apple TBDR).
22. **Presets plus live play-mode tuning plus a fixed vocabulary** is how small teams stay consistent (Feel, Celeste's rumble enum, Riot style guide).
23. **A visual stand-in for key sounds** helps players who play muted (Fortnite Visualize Sound).
24. **Personal, second-person commentary from a cheap in-house voice works** (PGA 2K placeholder lines, Fever's Talking Flower).

## Part E: Numbers worth stealing

| What | Value | Source |
|---|---|---|
| Hit-stop | 1 f (Vlambeer), 3 f (Celeste dash), 6 f (Celeste big launch), 7/11 f (KOF light/heavy), `0.65·d + 6` capped at 30 f (Smash Ultimate) | notes/research_feel.md §5 |
| Shake | trauma 0–1, shake = trauma², rotation-only in 3D; Celeste directional 0.2 s dash / 0.1 s bounce; Vlambeer +4 px per shot | §2.2–2.4 |
| Squash | Celeste land (1.6, 0.4) scaled by speed / max speed, recovery 1.75/s | §2.2 |
| Haptic vocabulary | 3 strengths × 2 lengths (Celeste); intensity = power, sharpness = cleanness (Apple) | §2.2, §2.15 |
| Voices | 20–30 stacked (Rocket League); Unity default 32 real / 512 virtual | §2.8, §3.3 |
| Mobile particles | 3–10 per effect in crowded scenes; budget = per-effect × simultaneous copies | §2.16 |
| Golf impact sound | perceived "solid" tracks loudness and sharpness; putt peaks about 2–4 kHz | Loughborough |
| Feels real-time | under about 100 ms correction cycle | Swink |
| AirPlay mirroring | about 100–200 ms A/V together | community and vendor |

## What we could not find (honest gaps)
- How Nintendo, Camelot, Playdemic or EA actually **recorded and layered** their hit sounds (sweet-spot layers, mic setups). No public source exists.
- Switch Sports HD Rumble on hit: no source, and footage can't show it.
- Fall Guys VFX and audio architecture; Rocket League ball-hit strength mapping; Hades hit-stop values.
- A sourced pitch-randomisation range. Our ±1–2 semitone figure is industry habit, not cited.
- One unconfirmed claim: PGA 2K's audio lead field-recording swings on real courses.
