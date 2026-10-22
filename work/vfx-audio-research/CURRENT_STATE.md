# Current state: VFX, audio, haptics and camera feel (2026-10-17)

Research only. Nothing in the game was changed. This was read from branch `10/13` in its current working-tree state. The full evidence table (every claim as `path:line`, 455 lines) is in [notes/inventory_raw.md](notes/inventory_raw.md). I spot-checked the riskiest claims myself: `TennisFx.Shake` has no reader, `Celebrate(` and `OverrideCamera(` have no callers, `TennisJuice.Punch` sets 0, `HitStopFor => 0f`, and the pitch reset in `TennisSounds.Hit`.

Script paths are under `Unity/Assets/Scripts/`.

## The one-paragraph version

We have a good set of individually tuned effects, sounds and haptics. They are wired together by hand at each gameplay call site, with no shared system. Tennis contact VFX is pooled and grade-aware. Golf has the only per-surface table, which covers landing colours. The haptics plugin is the most advanced part: layered Core Haptics strikes with a phone-now / TV-later clock. Audio is the weakest part. It has three WAV files, and everything else is synthesised at runtime as a single fixed take. It has no mixer, no variation, no per-surface sound, and a silent announcer. Camera feel is zero by design (Adnan dropped shake and hit-stop). Several finished effects are never called. A new system mostly has to **unify and route** what exists, then **replace the synthesised audio with real layered sounds**.

## Inventory at a glance

| Area | What exists | Quality | Biggest gap |
|---|---|---|---|
| Packages | URP 17.3 only. No VFX Graph, Cinemachine, tween library, FMOD/Wwise or Feel | — | — |
| Tennis VFX | `Tennis/TennisFx.cs`: 10 Shuriken systems built once and re-emitted, plus 6 bounce-mark quads. Max 676 particles. Additive and alpha shaders, 4 Higgsfield sprites | Good. Pooled, grade-aware (impact size .6→1.2, 3 colour tiers), with a Reduced mode | No per-court bounce (the `court` colour argument is ignored). Confetti `Celebrate` is never called. Grades below Perfect look nearly the same at the ball (EXPERIENCE_AUDIT #4) |
| Golf VFX | `Game/ShotEffects.cs`: puffs, splash, grass clippings, 3,000-particle trail, flare quads (flash, ring, crown). Strike, Knock, Burst, Touchdown, Splash, LavaBurst, IceSpray, Cup, reward trails (Sparkle/Fire/Rainbow). Tracer and comet | Good coverage, pooled | One shared ring flare (Strike, Cup and WetLanding restart each other). Ice and green strikes still throw grass. Replay and multiplayer follow show almost no landing or cup effects. No effect for lip-out or OOB |
| World / weather VFX | `Game/WeatherView.cs` rain 2,600 / snow 3,200 / ash 1,400 / embers / splashes, lightning, domes. `Course/LavaWorld.cs`. Tennis volcano (tier-scaled). Twister, rings, pollen | Rich | Snow and ash demand exceeds their caps, so they are silently clipped. LavaWorld has no quality tier. Tracer, CometTail and LandingZone allocate every frame |
| UI FX | Tennis HUD sparks, `TennisJuice` overlay titles (PERFECT!, SMASH!, NET!), golf `StrikeHud` (EaseOutBack pop), hole-out mesh confetti, callouts | Works, but split across 4 systems with different motion | No shared pop/tween vocabulary |
| Audio assets | **3 WAV files** (menu pop/tick/whoosh, 60 KB). Everything else is `AudioClip.Create` synthesis (`GolfSounds` 22 clips, `TennisSounds` 15, `EventSounds`, `TennisAmbience`, `TennisMusic` calypso stems) | Clever, but sounds synthetic. Single take per sound | No real recorded layers, no round-robin. Tennis hit pitch variation is cancelled by a bug (`TennisSounds.cs:34-36`) |
| Audio engine | 2D AudioSources only. 32 real / 512 virtual voices, DSP 512 | — | **No AudioMixer, buses, snapshots or ducking** (apart from one ad-hoc `MusicDuck`). Tennis contact plays on a shared priority-128 source and can be culled. Golf strike is protected (priority 0) |
| Missing audio | Announcer (`Resources/Tennis/Announcer` doesn't exist, so all 43 lines are silent). Umpire. Golf landing per lie (one thud for every lie). Dive / slide / brake. Racket whoosh (method exists, never called). Golfer footsteps. Golf and hub music. Hub ambience | — | The 10-15 three-theme plan (Clubhouse Pop / Stadium Snap / Toybox Rally) was **never installed**. It exists only as `work/gameplay-audio/PLAN.md` |
| Haptics | `Plugins/iOS/GolfHitFeel.h` + `GolfHaptics.mm`: layered strike (crack, body, sting, reward ring, supercharge surge, smash shock, streak pips). 9 cues. Two clocks (arm-caused now, TV-seen `+Lag`). Swing/whiff flam fix. Engine warm-up | **Best part of the stack.** Mac gates PASS | All 6 device feel gates NOT RUN. No haptic for opponent contact, own ball landing in, out/fault, ultimate arming, golf lip-out or online bounce. Golf movers reuse the tennis Bounce cue. Swift UI haptics bypass the plugin |
| Phone vs TV | All Unity audio, SwiftUI menu sounds and probably voice chat follow the AirPlay route to the TV. The only phone-speaker sound is the system-sound "knock", which is OFF by default and untested on a device | — | No phone-side sound identity. Sounds are never compensated for AirPlay delay. Golf has no TV clock at all |
| Camera feel | Tennis: none. `TennisFx.Shake` has no reader, `TennisJuice.Punch` is a no-op, `OverrideCamera` cinematic cuts are never called, hit-stop is 0, instant replay is off. Golf: replay 0.4× slow-mo only | **Intentional:** "no camera shake and no hit-stop are intentional" per Adnan (`ArtDir/style/EXPERIENCE_AUDIT.md:166-167`) | The art bible still says "preserve tennis holds of 14/30/45 ms" (`ART_BIBLE.md:124`), but the code has 0. The docs disagree, so Adnan needs to confirm |

## How events reach the channels today

There is **no event bus**. Each gameplay site calls `hud`, `fx`, `sounds`, `Haptics`, `juice` and the face expression one by one:

```
TennisGame.ReturnBall (120 Hz sim step)          TennisContactPresentation.LateUpdate (order 1100)
 ├─ grade + streak                                 └─ fx.Contact(...)   ← VFX on the DISPLAYED contact frame
 ├─ hud.ShowGrade / cause
 ├─ ContactMade event → phone bridge, racket trail
 ├─ ball trail colour/width
 ├─ QueueContactPresentation ────────────────────────┘
 ├─ juice.Trigger(Perfect|Smash) titles
 ├─ face expression
 ├─ sounds.Hit(grade, power, smash)  ← audio on the SIM step
 └─ Haptics.Hit(TennisHitFeel.Rally(...)) ← haptic NOW (arm clock)
Bounce / point / game / match haptics ← + TennisGame.Lag (TV clock, tennis only)
```

- The contact fan-out is **copied 4–5 times** per sport: player rally, serve (`TennisGame.cs:766-775`), opponent (`:1707`, `:2192`), Versus (`TennisGame.Versus.cs:338`), online (`TennisGame.Network.cs:53-69`), and golf replay and network. The copies have drifted:
  - online bounce has no VFX;
  - opponent contact has no haptic;
  - golf replay has no landing, cup or haptic.
- There are **three clocks**:
  - VFX runs on the render frame;
  - audio and strike haptics run on the 120 Hz sim step;
  - TV-seen haptics run on `TennisGame.Lag`, which mixes TV delay with the player's timing habit (`TennisLagLearner.cs:6-7`).
- The existing static events (`ContactMade`, `Landed`, `Netted`, `ShotStruck`, `ScoreChanged`…) feed the phone, recorder, tutorial and hero animation, **not** presentation. They are the natural hook points for a bus.

## Strength tiers and surfaces that already exist

| Table | Values |
|---|---|
| Tennis `Timing` | Missed, Ok, Good, Great, Excellent, Perfect, plus supercharged (3 in a row at Great or better), smash and ultimate (`Tennis/TennisRules.cs:13`, `:19-21`) |
| Tennis contact colours | gold for Perfect, cream for Great/Excellent, muted blue below (`TennisRules.cs:84-87`) |
| Tennis shake tiers (unused) | super 1, Perfect .7, Excellent .32, Great .18, else .06 (`TennisFx.cs:177`) |
| Golf `StrikeGrade` | Perfect, Great, Good, Thin; shapes Straight/Draw/Fade/Hook/Slice (`Swing/StrikeGrade.cs`) |
| Golf clubs | 10 clubs, grouped into 4 sound families (Driver/Hybrid, Iron, Wedge, Putter) (`Shot/GolfClub.cs:7`, `:25-29`) |
| Golf `CourseLie` | Tee, Fairway, Rough, Bunker, Green, Water, OutOfBounds, Fringe, Ice (`Course/Hole.cs:23`) |
| Golf visual surfaces | 27 material surfaces including Sand, Lava, Snow, Ice, Ash, Water, Shallow and Surf (`Course/GolfCourseLook.cs:17`) |
| Per-surface **VFX** | golf landing colours only (`ShotEffects.cs:414-443`, `EnvironmentFx.cs:23-33`) |
| Per-surface **audio** | none (ice skid, splash and lava hiss are hazard-specific) |

## Performance facts that bound the design

- **60 fps at ≥1920×1080 everywhere** is the floor (delegation README). `work/frame-rate-60b/BUDGET.md` **does not exist yet**; chat 1 owns it. The budget rules live in `ArtDir/style/ART_BIBLE.md:128-133`:
  - pooled built-in particles;
  - live counts and screen coverage measured per effect and per tier;
  - no unmeasured universal cap.
- Pipeline (`TennisURP.asset`): HDR on, MSAA 4, render scale 1, depth texture on, opaque texture off, 4096 shadows on High.
- Device tiers come from the model. The frame governor only steps down.
- Bloom: tennis .28, hub .7. Golf post-processing status is ambiguous.
- Tennis FX PSOs are warmed into an offscreen RT at load (`TennisFrameGovernor.cs:47-68`). Golf FX and weather are not warmed.

## Rules and decisions from earlier work that the new system must respect

1. **No camera shake, no hit-stop**: intentional per Adnan (`EXPERIENCE_AUDIT.md:166-167`). Also "no disabled camera punch restoration" (`ART_BIBLE.md:126`). The proposal treats these as OFF unless Adnan reopens them.
2. **Every important event gets ≥3 channels** (visual + sound + motion/haptic), scaled by importance (`ART_BIBLE.md:123`).
3. **Contact sounds play synchronously on the existing contact event.** No per-hit allocation, and contact voices are never stolen (`work/gameplay-audio/PLAN.md:26-28`).
4. **Haptic strikes stay on the truthful contact frame.** Arm-caused feedback plays now; TV-seen feedback is delayed (`PLAN_HitFeel_Haptics.md`).
5. **Colours stay in the palette.** Hazard orange `#FF5A1F` is reserved and ball yellow `#FFF36B` is reserved (`ART_BIBLE.md` §10). Glow EmissionHDR ≤ 1.5 in daylight.
6. **No full-body celebration while the ball is live** (EXPERIENCE_AUDIT #7). Failure beats ≤ 1.5 s and skippable (#10). Golf dead time should shrink, not grow (#1).
7. **Gameplay camera framing is fixed** (tennis comment: "contacts never move or zoom the camera").
8. **Unity runs are always muted** (GOLF_MUTE=1 plus Editor mute).

## Gap list ranked by player impact

1. **Hits sound synthetic and identical.** There are no recorded layers, no round-robin, and the pitch variation is cancelled. This is the biggest gap in the "does it feel good" sense.
2. **Shot quality isn't readable at the ball by ear or eye below Perfect** (EXPERIENCE_AUDIT #4). The tiers exist in data but not in feedback.
3. **No mixer.** Contact can be culled, the crowd and music never duck for the hit, and the announcer is silent.
4. **No per-surface audio**, and tennis has no per-court VFX. Golf thuds the same on sand, green and fairway.
5. **The phone has no sound identity** beyond haptics. The opt-in knock is untested on a device.
6. **Dead payoffs:** tennis winner/match confetti, the cinematic cut library and tennis instant replay are all off.
7. **Copy-pasted fan-out** causes drift between solo, online, Versus and replay.
8. **Three clocks** with no shared contact timestamp. The audio/VFX skew is at most one frame today, but nothing enforces it.
9. **Missing sounds:** dive, slide, brake, swing whoosh, golfer feet, lip-out VFX, OOB VFX, music outside tennis.
10. **Small perf debts:** per-frame allocations (Tracer, CometTail, LandingZone, weather `Fall()` closures), the per-use ultimate `AudioClip`, main-thread synthesis on first use, `EventSounds` re-synthesised per instance, and LavaWorld without a tier.
