# VFX + Audio + Haptics + Camera-feel inventory (raw, evidence-based)

Date: 2026-10-17. Branch `10/13` (working tree, uncommitted state as found). READ-ONLY survey: nothing in the repo was edited.
All paths relative to repo root `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator`.
Script paths below are under `Unity/Assets/Scripts/` unless a full path is given (written `S/…` for brevity where noted).

---

## 0. Packages / platform facts

| Fact | Evidence |
|---|---|
| URP 17.3.0, no VFX Graph (`com.unity.visualeffectgraph` absent), no Cinemachine, no tween lib, no FMOD/Wwise | `Unity/Packages/manifest.json:2-50` (only `com.unity.render-pipelines.universal` 17.3.0 at :49; `com.unity.modules.particlesystem` :31, `com.unity.modules.audio` :21) |
| The juice doc itself notes "URP 17.3 only, no Cinemachine, VFX Graph or tween library yet" | `ArtDir/style/VISUAL_STANDARD_AND_JUICE.md:84` |
| All particle FX are built-in Shuriken `ParticleSystem`s created **in code** (no FX prefabs found); 18 script files reference ParticleSystem/TrailRenderer/LineRenderer | grep of `Unity/Assets/Scripts` (list in §1) |
| Audio engine settings: DSP buffer 512 (lowered from 1024 for latency), 32 real voices, 512 virtual voices, sample rate default | `Unity/ProjectSettings/AudioManager.asset:11-20`; change recorded in `docs/tennis-feel-pass-2026-10-10.md:47` |

---

## 1A. Tennis VFX — `Tennis/TennisFx.cs` (single owner of court FX)

Built once per match: `TennisGame.cs:300` (`new GameObject("Tennis effects").AddComponent<TennisFx>(); fx.Build()`).
**Pooled**: every system is prebuilt and re-emitted with `ParticleSystem.Emit(EmitParams, n)` (`TennisFx.cs:5-6`, `:133-139`); nothing instantiated per event. Bounce marks are a 6-quad ring buffer (`:23-24`, `:79-91`, `:232-238`).
Shaders: `Unity/Assets/Resources/Tennis/Shaders/TennisFxAdditive.shader` (Blend SrcAlpha One, ZWrite Off, `_Intensity` multiplier, :4-24) and `TennisFxAlpha.shader` (alpha blend, :7-9). Sprites: `Unity/Assets/Resources/Tennis/Fx/{impact,ring,sparkle,dust}.png` (Higgsfield-generated per comment `TennisFx.cs:6`), procedural fallback `TennisLook.Falloff` (`:32-36`, `:48`).
Quality scaling: every burst goes through `EnvironmentFx.ParticleCount(count)` (÷3 when `Reduced`) and velocity × `MotionScale` (.45 when Reduced) (`TennisFx.cs:137-138`; `Environment/EnvironmentFx.cs:12-17`). `Reduced` = `EnvironmentLook.Stage>=6 && PresentationPolicy.Constrained` (`EnvironmentFx.cs:10-13`). `EnvironmentFx.Impact` caps impact alpha .58/.68 when active (`:18-22`).
Warm-up: `TennisWarmup.Run` fires `fx.Contact(Perfect, supercharged)` + `fx.Bounce` into a 64×64 offscreen RT at load to pre-compile PSOs, then `fx.Clear()` (`Tennis/TennisFrameGovernor.cs:47-68`).

### Particle systems (`TennisFx.Build`, `TennisFx.cs:60-77`; generic builder `System()` `:102-131`: world space, sphere r .05, fade alpha 1→.8@.35→0, size-over-life ease .55→`grow`, billboard, no shadows, sortingFudge -5)

| System | Material | max | life s | size m | speed m/s | gravity | grow | line |
|---|---|---|---|---|---|---|---|---|
| Impact flash | additive, impact.png, ×1.8 | 4 | .09–.13 | .9–1.3 | 0 | 0 | 1.5 | :60 |
| Shockwave | additive, ring.png, ×1.8 | 6 | .22–.30 | .35 | 0 | 0 | 5 | :61 |
| Sparkles | additive, sparkle.png, ×2.4, spin | 60 | .25–.5 | .08–.2 | 2–5.5 | .6 | .4 | :62 |
| Impact streaks (stretched, velScale .045, len 1.2) | additive glow | 48 | .09–.16 | .05–.08 | 9–15 | 0 | .3 | :64-65 |
| Felt fuzz | alpha soft | 50 | .22–.5 | .03–.06 | 2.8–6.5 | 3.5 | 1.4 | :66 |
| Bounce dust | alpha dust.png, spin | 40 | .35–.7 | .12–.28 | .4–1.4 | -.3 | 1.8 | :67 |
| Footstep dust | alpha dust.png, spin | 60 | .3–.55 | .1–.2 | .3–.9 | -.2 | 1.9 | :68 |
| Bounce ripple (horizontal billboard) | additive ring | 8 | .3–.4 | .2 | 0 | 0 | 5 | :69-70 |
| Confetti (3D rot, drag 1.6) | alpha 4×4 white square | 240 | 1.6–2.6 | .05–.09 | 3–7 | .9 | 1.4 | :71-75 |
| Supercharge stream (rateOverDistance 22) | additive glow | 160 | .18–.32 | .1–.2 | .1–.5 | 0 | 1.4 | :76-77 |
| Bounce marks: 6 quads, life 2.2 s, colour (.28,.3,.22,a≤.32) | alpha soft | 6 | 2.2 | .13 × (.13+.32·pace) | — | — | — | :79-91, :303-315 |
| Timing cue ring (camera-facing quad, white→yellow→green, size 2.2→.32) | additive ring ×1.4 | 1 | — | — | — | — | — | :93-99, :278-292 |

Total live particle budget for tennis FX ≤ 4+6+60+48+50+40+60+8+240+160 = **676** max particles.

### Public FX API → visuals → triggers

| Method | Looks like | Call sites (trigger) |
|---|---|---|
| `Contact(at, grade, supercharged, smash)` `:153-179` | impact (scale .6/.78/.95/1.2 by grade), shock ×1–2, felt fuzz 6+3·grade, sparkles ≥Great, Perfect adds gold shock + 16 sparkles + Flash .25; Perfect/supercharged → `Heavy()` (12·amount radial streaks + flat ripple, `:193-202`); smash = biggest gold set + Flash .6. Colour = `TennisRules.ContactColor` (blue <Great, cream Great/Excellent, gold Perfect; `Tennis/TennisRules.cs:84-87`), cyan if supercharged | `TennisGame.ContactPresentation.cs:25` (player) via `FlushContactPresentation()` called from `TennisContactPresentation.LateUpdate` at `[DefaultExecutionOrder(1100)]` (`Tennis/TennisContactPresentation.cs:8-12`) — i.e. on the **displayed** contact frame after the rig is finalised; online view `TennisGame.Network.cs:62`; warm-up `TennisFrameGovernor.cs:64` |
| `OpponentContact(at, heavy)` `:214-224` | smaller cream impact + shock + 6 fuzz; heavy = cyan streak set | `TennisGame.ContactPresentation.cs:26`; Versus `TennisGame.Versus.cs:338` |
| `Whiff(feet, racket)` `:183-190` | white shock ring at racket, ground ripple, 7 dust, 6 blue sparkles | `TennisGame.cs:2073` (`WhiffJuice`, called from `:741` toss miss and `:1379` no-contact), `:1678` (opponent whiff), `TennisGame.Versus.cs:255` |
| `NetHit(at)` `:205-211` | 2 shocks, 12 fuzz, 8 white sparkles | `TennisGame.cs:1549` |
| `Bounce(at, vel, court)` `:227-239` | 3–9 dust (pace-scaled), ripple, skid mark | `TennisGame.cs:1566` (only when `overDeck`); warm-up. **`court` colour parameter is ignored** (dust is always `(1,.97,.92,.55)`; caller passes constant `CourtDust` `TennisGame.cs:230`) → no per-surface/per-venue tennis bounce |
| `Footstep(at, speed)` `:242-246` | 2–3 footDust puffs if speed ≥3 m/s | `TennisGame.cs:326` (`actor.FootPlanted` from `TennisActor.cs:1321`, rally only) |
| `Slide(at)` `:248` | 8 dust | `TennisGame.cs:327` (`actor.DiveLanded`, `TennisActor.cs:827`) |
| `Celebrate(at, amount)` `:251-260` | 40–200 confetti in 5 palette colours | **no call site** (grep `Celebrate(` finds only the definition) → tennis confetti for winners/match is dead code |
| `Stream(ball, on)` `:269-274` | supercharge glow stream behind ball | `TennisGame.cs:1714` (per sim step, on if supercharged & outgoing), off `:1392` |
| `Cue(show, ball, cam, closing)` `:278-292` | timing ring closing on ball | `TennisGame.cs:2358`, `:2366` |
| `LavaOut(at)` `:142-147` | orange impact + 18 sparks + dark dust | `Tennis/TennisConditions.cs:49` (volcano venue ball out) |
| `Shake` property `:27`, set by Contact/Whiff/NetHit (`:163,177,189,210`), decays 3.5/s (`:305`) | camera punch request | **never read** (grep `.Shake` → no consumer). Dead channel. |
| `Flash` property `:29`, decays 5/s (`:306`) | full-screen white lift | read once: `TennisGame.cs:2461-2462` → HUD flash image alpha = `Flash*.25` ("a lift, never a white-out") |

### Other tennis visuals tied to events
| Item | Evidence |
|---|---|
| Ball `TrailRenderer` (time .2, width .12→0, minVertexDistance .04, additive glow, falloff tex) built once | `TennisGame.cs:342-347` |
| Trail colour per frame = contact tier colour (gold/cream/blue) or cyan if supercharged; alpha .45–.8 and time .14–.26 s by speed (×1.6 supercharged) | `TennisGame.cs:2324-2330` |
| Trail widened to .45 + orange (player ultimate) / cyan (rival ultimate), reset at point end | `TennisGame.cs:2052-2054`, `:1697`, `:1704`, `:887` |
| Ball squash & stretch on contact/bounce (squash 1 → 0 over .09 s, stretch up to 1.35 at pace) | `TennisGame.cs:2313-2322`; set at `:1994` (contact), `:1567` (bounce) |
| Racket `TrailRenderer` on string centre, lit only after confirmed contact / whiff (.2 s white or .32 s gold for Perfect/super; .4 s blue on whiff; .2 s for rival) | `Tennis/HeroTennisDriver.cs:481-500` |
| Body "kick" (chest recoil + root squash) on Great+/heavy contact, net slump, whiff — **disabled for match heroes** (`!Match`, `Match => matchLook != null`) | `HeroTennisDriver.cs:61`, `:470-480`, `:499` |
| Contact frame hold: `QueueContactPresentation` → `HeroTennisDriver.HoldContactFrame()` pins the rendered pose to the contact time for the frame | `TennisGame.ContactPresentation.cs:12-17`; `HeroTennisDriver.cs:626-656` |
| Landing / aim `LineRenderer` rings, markers | `TennisGame.cs:129`, `:2215-2290` |

---

## 1C. UI FX (popups, banners, flashes)

| Element | Behaviour | Trigger | Evidence |
|---|---|---|---|
| Tennis grade badge (lower-left panel: GOOD/GREAT/…/"SUPER SHOT" + "EARLY · LEFT · FOREHAND · 120 km/h") | static text panel, no tween found | every player contact `TennisGame.cs:2018`; serve `:766` | `Tennis/TennisHud.cs:374-381` |
| Tennis cause text ("NO CONTACT", timing word) .6 s | — | `TennisGame.cs:2019`, `:1379` | `TennisHud.cs:365-371` |
| Tennis call queue (GAME / SET, max 3 queued) and point result "X SCORED" 3 s | — | `TennisGame.cs:900-904` | `TennisHud.cs:384-411` |
| Tennis UI spark bursts (pooled `sparks` list of Images) | 8 sparks when timing cue hits "now", 14 on timing-check OK, 10 gold on perfect toss | `TennisHud.cs:53`, `:240`, `:413-…`, `:479`, `:591`, `:646` |
| Tennis HUD flash image (alpha = fx.Flash × .25) | white lift on Perfect (.25→.06), smash (.6→.15), supercharge (1→.25) | `TennisGame.cs:2461-2462` |
| `TennisJuice` spectacle overlay (ScreenSpace canvas, sort 50): vignette, speed-lines, flash RawImages, 80 pt title + 32 pt subtitle with double outline, ultimate meters, rival-cam inset (320² RT) | Titles: "PERFECT!"/"SUPERCHARGED!" (`:72`), "SMASH!" + flash .1 (`:85`), "WHIFF!" (`:89`), "PERFECT SERVE!" + flash .12 (`:109`), "NET!" (`:113`, called `TennisGame.cs:1550`), "POINT <name>" (`:116-122`, called `TennisGame.cs:885`), ultimate name + flash .22 (`:142`) | `Tennis/TennisJuice.cs:296-340` |
| Golf strike popup (`StrikeHud`): word punches in with EaseOutBack overshoot to 1.25 + -9°→-3° twist, Pop .28 s / Hold 1.5 s / Fade .45 s, rises 60 px | `GolfGame.AnnounceStrike` `Game/GolfGame.cs:2685-2692` (from strike `:2224`, not for putter) | `UI/StrikeHud.cs:17`, `:38-80` |
| Golf callouts / events / landing badge / banner / unlock toast / scorecard / HoleOutCard / swing card | e.g. "Boing!", "Twister!", "Birdie!", "Beep beep!" callouts on round events; "Incinerated · shot + 1 penalty" | `Game/GolfGame.Events.cs:227-244`, `GolfGame.cs:2368`; `UI/Hud.cs:1100-1191`; `UI/LandingBadge.cs:80`; `UI/HoleOutCard.cs:84`; `UI/UnlockToast.cs` |
| Club-select card punch (60 px slide + scale, exp decay 14/s) | phone controller sheet | `UI/ControllerSheet.cs:445`, `:503-530` |
| Locked-course padlock head-shake | locked course SELECT (+ `sounds.PlayGroan(.3)`) | `UI/HomeScreen.cs:182`, `:248`, `:266-267`; `GolfGame.cs:486` |

---

## 5. Event / timing plumbing

### 5.1 No central event bus
There is no shared VFX/audio/haptics/camera dispatcher. Every gameplay site calls each channel directly. The few `static event`s exist for the **phone/native bridge, recorder, tutorial and hero animation**, not for presentation:

| Event | Declared | Fired | Subscribers |
|---|---|---|---|
| `TennisGame.ContactMade(Vector2 face, Timing, bool super)` | `TennisGame.cs:221` | `:2024` | `NativeSportsSession.cs:123` (emit "contact" to phone), `HeroTennisDriver.cs:211` (racket trail, torso kick) |
| `Landed(byPlayer, in, pos, serve)` | `:206` | `:818`, `:1578` | `NativeSportsSession.cs:130`, `TennisTutorial.cs:77` |
| `Netted(bool)` | `:220` | `:1550` | `HeroTennisDriver.cs:213` |
| `Whiffed` | `:218` | `:741`, `:1379` | `HeroTennisDriver.cs:211` |
| `OpponentStruck` | `:1860` | `:1707`, `:2192`, `Versus.cs:338` | `HeroTennisDriver.cs:212` |
| `ScoreChanged`, `PhaseChanged`, `MatchFinished`, `MatchStatsReady`, `RallyEnded`, `RecordingPointStarted/Ended`, `DrillPoint`, `TimingChecked` | `:190-221`, `:420`, `:494` | `:843-919`, `:1143` | `NativeSportsSession.cs:114-130` (phone + point recorder), `TennisTutorial.cs:77` |
| `GolfGame.ShotStruck` | `Game/GolfGame.Native.cs:8` | `GolfGame.cs:1981` (input-time, before flight) | `GolfTutorial.cs:49` |
| `GolfGame.RoundSummary` | `GolfGame.Challenges.cs:41` | — | `NativeSportsSession.cs:128` |
| `PresentationPolicy.Trace` / `Event(beat,state,seq,detail)` — a log/trace line for presentation beats (Point/Game/Set/MatchEnd begin) | `Game/PresentationPolicy.cs:9`, `:19-22` | `TennisGame.cs:882` | (trace only) |
| `ExperienceTrace.Mark(sport, stage)` — latency stamps "contact" / "contact-channels-requested" | `Game/ExperienceTrace.cs:36-42` | tennis `TennisGame.cs:2023`, `:2064`; golf `GolfGame.cs:2222`, `:2226` | telemetry file |

### 5.2 Tennis player contact — fan-out (all inside `TennisGame.ReturnBall`, `TennisGame.cs:1983-2066`, run in the 120 Hz sim step)
1. grade: `LastGrade = TennisRules.Grade(hit.Quality)` (`:2004`); streak → supercharge after 3 Great+ (`:2007-2008`; `TennisRules.cs:19-21`).
2. HUD grade + cause (`:2017-2020`).
3. `ContactMade` event (`:2024`) → hero racket trail/torso kick; phone.
4. Ball trail width/colour (`:2052-2054`).
5. VFX **queued**: `QueueContactPresentation(Player, grade, super||ult, smash)` (`:2055`) → drawn at the displayed frame by `FlushContactPresentation` in LateUpdate order 1100 (`TennisContactPresentation.cs:8-12`).
6. Spectacle: `juice.UltimateHit` or `juice.Trigger(Smash|Perfect)` (`:2057-2058`).
7. Face expression (`:2060-2061`).
8. Audio **immediate**: `sounds.Hit(LastGrade, Player.Power, smash)` (`:2062`).
9. Haptics **immediate** (arm clock, no `Lag`): `Haptics.Hit(TennisHitFeel.Rally(grade, faceOffset, lateness, kind, power, streak, super, rallyShots))` (`:2063`).
Serve contact has its own copy of this fan-out: `TennisGame.cs:766-775` (`hud.ShowGrade`, `QueueContactPresentation`, `sounds.Hit`, `juice.PerfectServe`/`Punch(.5)`, `Haptics.Hit(TennisHitFeel.Serve(verdict))`).
Opponent contact copies: `TennisGame.cs:1707`, `:2192`, `Versus.cs:338` (sound `RivalHit` + VFX; no haptic).
Online (non-host phone) copy: `TennisGame.Network.cs:53-69` (sound + `fx.Contact` + haptic to striker on contact counter change; bounce → **sound only**, no `fx.Bounce`).

So sound + haptics fire on the **sim** step while particles fire on the **render** frame (≤1 frame apart at 60 fps); no single timestamp is shared.

### 5.3 Tennis other events (direct calls)
| Event | VFX | Audio | Haptic | UI/Camera | Evidence |
|---|---|---|---|---|---|
| Bounce (on deck) | `fx.Bounce` | `sounds.Bounce(|vy|/8)` | `Cue.Bounce` delayed by `Lag`, only rival ball landing IN on player side | — | `TennisGame.cs:1566-1580` |
| Net tape | `fx.NetHit` | `sounds.Net()` | none | `juice.Call("NET!")` | `:1547-1550` |
| Whiff | `fx.Whiff` | `sounds.Whiff()` | `Cue.Whiff` | `juice.Trigger(Whiff)` title | `:2071-2077` |
| Point/game/set/match | none (confetti dead) | crowd `crowd.Cheer`, `stands.Cheer`, `audio.OnPointOver(...)` or fallback `sounds.Applaud`; umpire `umpire.Call()` | `PointLost/PointWon/GameWon/MatchWon` delayed by `Lag` | `juice.PointReaction` title, `hud.ShowPointResult/ShowCall` | `:862`, `:885-918` |
| Swing confirmed by phone | — | — | `Haptics.SwingFelt()` | — | `:593`, `:607` |
| Footstep / dive landing | `fx.Footstep` / `fx.Slide` | `audio.OnFootstep(speed, isPlayer)` (footstep only) | none | — | `:326-327` |
| Supercharge flight | `fx.Stream` | — | — | trail ×1.6 | `:1714`, `:2330` |
| Ultimate charge | — | synthesized rising sine cue (`AudioClip.Create` per use, 22.05 kHz, 2.2 s, `Destroy(cue, 3.2)`) | — | world freeze `Time.timeScale=0` for 2.2 s, titles, canvases hidden | `TennisJuice.cs:129-157`; triggered `TennisGame.cs:1155-1161` |

### 5.4 Golf strike fan-out (`GolfGame.cs:2219-2227`, `State.Flight`, first frame with `flightTime ≥ 0`)
`sounds.PlayStrike(club, power)` → `Haptics.Putt(power)` or `Haptics.Strike(grade, power)` + `AnnounceStrike()` (StrikeHud popup, applause if Perfect & power>.8) → `effects.Strike(origin, aim, lie, power, putter)` — all in one frame, same order, no Lag scheduling. Input-time feedback earlier: `Haptics.Tension(load)` + `sounds.SetTension(load)` during backswing (`:1916`, `:1942`), `sounds.PlayWhoosh` + `Haptics.Top` at downswing (`:2196`), `ShotStruck` event `:1981`.
Golf landing/flight: `effects.Touchdown(pos, lie, strength)` + `PlayIceSkid`/`PlayThud` + first-down `Haptics.Tick` + `effects.WetLanding` (`:2309-2314`); obstacle knock `effects.Knock` + `PlayKnock`/`PlayLeaves` + `Haptics.Tick` (`:2325-2327`); ice spray (`:2335-2339`); lip-out groan (`:2348`); **cup**: `effects.Cup` + `sounds.PlayCup` + `Haptics.Roar` (`:2351`); lava `effects.LavaBurst` + `PlayLavaHiss` + `Haptics.Failure` (`:2367`, `:2376`); water `effects.Splash` + `PlaySplash` + `PlayGasp(.55)` + `Haptics.Failure` (`:2377-2378`); crowd reactions by lie in `React()` (`:2696-2711`). Round events (`GolfGame.Events.cs:227-244`) and challenge rings (`GolfGame.Challenges.cs:128-164`) also call `effects.Burst` + sound + haptic + callout inline.
Golf replay re-fires strike/land/cup/splash sounds and effects (`GolfGame.cs:2774-2809`) with no haptics.

### 5.5 Grade tiers / surface tables (what exists)
| Table | Values | Evidence |
|---|---|---|
| Tennis `Timing` | Missed, Ok, Good, Great, Excellent, Perfect (+ "supercharged" after 3-in-a-row ≥Great, + smash, + ultimate) | `Tennis/TennisRules.cs:13`, `:19-21` |
| Tennis grade labels | "PERFECT!", "EXCELLENT", "GREAT", "GOOD", "OK", "MISS" | `TennisRules.cs:70-78` |
| Tennis contact colours (3 tiers) | gold ≥Perfect (1,.82,.32), cream ≥Great (1,.97,.86), muted blue (.64,.76,.86) | `TennisRules.cs:84-87` |
| Tennis shake tiers (unused) | super 1, Perfect .7, Excellent .32, Great .18, else .06 | `TennisFx.cs:177` |
| Tennis hit-stop | `HitStopFor(...) => 0f`, `HeavyHitStop = 0f` (disabled; "rewards never add timed simulation holds") — contradicts ART_BIBLE "Preserve tennis holds of 14/30/45 ms by grade" | `TennisRules.cs:80-82`; `TennisGame.cs:1099`, `:2012`, `:2056-2057`; `ArtDir/style/ART_BIBLE.md:124` |
| Golf `StrikeGrade` | Perfect, Great, Good, Thin; `ShotShape` Straight/Draw/Fade/Hook/Slice | `Swing/StrikeGrade.cs:6`, `:10` |
| Golf clubs | Driver, Iron, Wedge, Putter, Hybrid, Iron5, Iron9, PitchingWedge, LobWedge, Chipper | `Shot/GolfClub.cs:7` |
| Golf `CourseLie` | Tee, Fairway, Rough, Bunker, Green, Water, OutOfBounds, Fringe, Ice | `Course/Hole.cs:23` |
| Golf visual surfaces (materials) | 27 values incl. Sand, Lava, Snow, Ice, Ash, Water, Shallow, Surf… | `Course/GolfCourseLook.cs:17` |
| Landing-puff palette per lie (Green / Rough+OOB / Bunker / Ice / default) | colours a/b | `Environment/EnvironmentFx.cs:23-33` |
| Weather skies | Rain, Snow, Ash | `Course/RoundEvents.cs:17` |
| Tennis per-surface bounce | **none** (single `CourtDust`, ignored inside Bounce) | `TennisGame.cs:230`, `TennisFx.cs:227-231` |

---

## 6. Camera feel

| Feature | State | Evidence |
|---|---|---|
| Tennis camera | `TennisShoulderCamera.Frame` + exp lerp (rate 9/s); FOV set directly; no shake/punch/kick term anywhere in the path | `TennisGame.cs:2389-2408`; `Tennis/TennisShoulderCamera.cs:24` |
| `TennisFx.Shake` | written, **never consumed** | `TennisFx.cs:26-27`, `:163-210`, `:305` |
| `TennisJuice.Punch(amount)` | **no-op** (`punch = 0`) | `TennisJuice.cs:159`, `:195` |
| `TennisJuice.Apply(ref pos, ref look, ref fov, …)` rally FOV breath | **empty body**, never called; comments say "Gameplay framing owns a constant FOV; contacts never move or zoom the camera" | `TennisJuice.cs:286-293` |
| `TennisJuice.OverrideCamera` (Perfect low Dutch, Smash side, Whiff crash-zoom, Toss cam, Reaction, Ultimate 3-shot orbit) | fully implemented but **never called** (grep `OverrideCamera(` finds only the definition) → cinematic cuts are inert; Trigger(Perfect) returns early before `Begin(Shot.Cut)` anyway (`:70-74`) | `TennisJuice.cs:205-280` |
| Tennis slow-mo | `Slow(.14, .4)` only reachable in the Perfect case that is short-circuited (`:70-74` vs `:80-81`) → effectively dead; Ultimate charge **freezes** `Time.timeScale=0` for 2.2 s | `TennisJuice.cs:81`, `:137-138`, `:169-171`, `:185` |
| Tennis hit-stop | 0 (see §5.5) | `TennisRules.cs:80-82` |
| Tennis instant replay | `InstantReplayEnabled = false` ("off until it replays the visible characters truthfully") | `TennisGame.cs:1840`, `:922-925`; `Tennis/TennisReplay.cs` |
| Tennis DOF for replays | `TennisLook` DOF helper for slow-mo replays (`RequestDepthOfField`) | `Tennis/TennisLook.cs:259-264` |
| Golf `CameraRig` | SmoothDamp position/look, roll, zoom (FOV from zoom factor), POV ball framing; **no shake/punch** | `Game/CameraRig.cs:550-640` |
| Golf replay slow-mo | `Time.timeScale = 0.4` for replayClock ∈ (-0.3, 0.35) around the strike; `rig.Zoom(clamp(dist/26,1,8))` on the ball; landing cut | `GolfGame.cs:2762-2766`, `:2847-2850` |
| Golf pause | `Time.timeScale = 0` via native pause | `Game/NativeSportsSession.cs:403` |
| Hero torso kick (body-level "camera-less punch") | disabled for match heroes | `HeroTennisDriver.cs:476` |
| ART_BIBLE rule | "Preserve animations, live cameras … no disabled camera punch restoration" | `ArtDir/style/ART_BIBLE.md:126` |

---

## 7. Perf-relevant facts

| Fact | Evidence |
|---|---|
| Active pipeline asset `Unity/Assets/Resources/Tennis/Rendering/TennisURP.asset` (guid 826b40…) used by GraphicsSettings and all 6 quality levels | `Unity/ProjectSettings/GraphicsSettings.asset:91`; `QualitySettings.asset:51…316` |
| Asset as authored: HDR on (precision 0 = 32-bit), MSAA 4, renderScale 1, depth texture on, opaque texture off, main-light shadows 4096, 1 cascade, distance 60, soft shadows (quality 2), SRP batcher on, colour grading HDR (mode 1) LUT 32, GPU Resident Drawer off | `TennisURP.asset:19-86` |
| Runtime tiers by `SystemInfo.deviceModel`: High (iPhone16,x+ = A17Pro+) MSAA4/4096/60 m; Standard (iPhone15,x) MSAA4/2048/38 m; Low MSAA2/hard/1024/32 m. HDR always on, renderScale 1, SSAO only on High | `Tennis/TennisQuality.cs:27-35`, `:46-51`, `:77-102`, `:127-132` |
| Frame governor (2 s windows, 10% late frames → step down: MSAA→2, drop SSAO/High, cascades→1, renderScale .85, MSAA→1; never steps up) | `Tennis/TennisFrameGovernor.cs:9-41`; `TennisQuality.cs:136-148` |
| Golf shadows: 320/260/180 m, 4 (High) or 2 cascades | `TennisQuality.cs:108-122` |
| Target 60 fps: `Application.targetFrameRate = 60` (golf) / 60 when external display, else `FrameRate.Target` | `Game/GolfGame.cs:152`; `NativeSportsSession.cs:243`; `NativeSportsSession.Hub.cs:49` |
| 30 fps fallback removed (2026-10-16); thermal cap Serious 30→60, Critical 15→30 | `work/frame-rate-60/README.md:5-8` |
| No `work/frame-rate-60b/BUDGET.md` exists (folder holds only `logs/ proof/ scripts/`; proof empty) | `ls work/frame-rate-60b` |
| Budget rules: "60 rendered fps on every tier (16.7 ms)… Built-in pooled particles; measure live counts and screen coverage per effect/tier. Existing rain/snow maxima exceed 300"; 150 draws/150k tris are "investigation prompts" | `ArtDir/style/ART_BIBLE.md:128-133` |
| Tennis post: ACES, bloom threshold 1.05 intensity .28 maxIterations 4, vignette .12; Low tier drops bloom (+ DOF) | `Tennis/TennisLook.cs:225-254`; `Tennis/SportsPostProcessing.cs:13-32` |
| Hub post: Neutral tonemap, bloom .7 thr 1.05 scatter .62 tint FFE2B8 maxIter 5, vignette .2, Gaussian DOF 55–220 m high-quality sampling | `Hub/HubArt.cs:162-176` |
| Golf post: comment says "post-processing renders nowhere in this project (no PostProcessData…)" but `PostcardRefreshProofRunner` gates require ACES + bloom on the golf camera → status ambiguous, golf bloom likely present on postcard holes | `Course/GolfLook.cs:148`; `Course/PostcardRefreshProofRunner.cs:68-82`; `Environment/EnvironmentLook.cs:88-93` |
| Art bible bloom target: threshold 1.1, intensity .35, scatter .6; "only emissives (lamps, lava, neon, perfect-hit FX) should go over the threshold" | `ArtDir/style/ART_BIBLE.md:66`, `:100-103` |
| Shader PSO warm-up for tennis FX at load | `TennisFrameGovernor.cs:44-68` |

---

## 2. Audio (Unity side)

### 2.1 Assets, engine, packages
| Fact | Evidence |
|---|---|
| Only **3 audio files** in the whole Unity project: `Unity/Assets/Resources/Club/Sounds/{pop,tick,whoosh}.wav` (16-bit PCM mono 44.1 kHz, 60 KB total). 0 `.ogg/.mp3/.aif/.m4a/.caf`, 0 `.mixer` | `find Unity/Assets` |
| Import settings (all three identical): loadType 0 Decompress On Load, compressionFormat 1 (Vorbis), quality 1, preload 0, normalize 1, forceToMono 0, no iOS override | `Unity/Assets/Resources/Club/Sounds/pop.wav.meta:8-20` |
| Everything else (golf, tennis, weather, crowd, music, stingers) is **synthesised at runtime** with `AudioClip.Create` | §2.2 |
| No AudioMixer, no `outputAudioMixerGroup`, no snapshots; all sources `spatialBlend = 0` (2D); no FMOD/Wwise | manifest; grep |
| No AudioSource/AudioListener in any scene/prefab; listeners added in code | `Game/CameraRig.cs:40`, `Tennis/TennisGame.cs:287`, `Hub/HubWorld.cs:490` |
| AudioManager: DSP 512, 32 real / 512 virtual voices, stereo, no spatializer | `Unity/ProjectSettings/AudioManager.asset:11-20` |

### 2.2 Sound scripts
| Script | Sources (voices) | Clips / synthesis | Notes |
|---|---|---|---|
| `Game/GolfSounds.cs` | 3 x 2D: shared one-shot `source` (prio 128), `strikeSource` **prio 0** ("never stolen", `:16`, `:32`), looping `tensionSource` (`:21-40`) | 22 clips synthesised synchronously at startup in `Synthesize()` (`:109-226`), created from `GolfGame.cs:211`. Renderers `Clip()` (1-pole LP, normalise, 5 ms fade, `:388-408`), `Applause()` (`:233-271`), `Crowd()` formant voices (`:306-372`), `Whistles()` (`:276-300`) | Strike by club family (`:44-49`, mapping `Shot/GolfClub.cs:25-29`): Driver/Hybrid 0.34 s knock 520→250 Hz + rings 2350/3650/5200, tanh 2.2 (`:126-128`); Iron .22 s 700→330 rings 1550/3100 (`:129-131`); Wedge .22 s ring 950 (`:132-134`); Putter .16 s 900→640 ring 700 (`:135-136`). Also Whoosh (`:51`), Cup 4 liner knocks @1150 Hz (`:52`, `:144-155`), Splash (`:53`), LavaHiss (`:55`), IceSkid (`:57`), **one Thud for every lie** (`:58`, `:158-160`), Leaves/Knock wood/stone (`:60-62`), Ready/Fanfare/Tick (`:63-65`), Applause 3.4 s 16 clappers (`:67`), Gasp/Groan 18 voices (`:71-72`), HoleOut ovation 6 s 28 people + whistles by score vs par (`:76-87`), Tension loop 88/132 Hz + 14 Hz ratchet, vol→load×.75, pitch .8+.7·load (`:91-107`). **No randomisation, single take each** |
| `Game/EventSounds.cs` | 3 x 2D: `once`, looping `rain`, `wind` (`:39-41`) | lazy `??=` clip properties (`:18-32`), `Prepare()` prewarms rain/thunder/rumble (`:47-51`), `Render()` (`:194-217`) | Rain → level×.42, wind ×.32, ease .35/s (`:56-68`); Thunder near/far (`:71`), volcano Rumble .9 (`:73`), Gust .75, Boing .9, Squawk .8, Horn .7 (`:74-77`), Ratchet .35 / Stamp .85 (`:78-79`), ring Chime 2 or 4 notes (`:81`), Jingle (`:83`), Foghorn (`:85`). **Instantiated separately** (each re-synthesises its own clips) by `GolfGame.Events.cs:57`, `Tennis/TennisConditions.cs:33`, `Environment/DreamHazardView.cs:15` (one per hazard root) |
| `Game/PresentationStinger.cs` | 1 source | 0.18 s chirp at 22.05 kHz on first `Lead()` (`:7-16`) | `MusicDuck` = .5 for .5 s after a cue (`:6`) — the only cross-system duck, read by `TennisAudioDirector.cs:111`; called `GolfGame.Presentation.cs:95`, `:201` |
| `Tennis/TennisSounds.cs` | 2 x 2D: shared one-shot `source` (**default prio 128**), looping `crowd` (`:21-22`) | 15 clips synthesised on main thread (`:67-105`) | `Hit(grade,power,smash)` `:31-40`: "Pop" or "Pop sweet" (≥Great) + "Body thump" + "Smash crack" or "Perfect sting" (G6-C7-E7). **Bug**: `source.pitch = Lerp(.94,1.08,power)` then `source.pitch = 1` right after `PlayOneShot` (`:34-36`) — pitch is live per-source, so the variation is cancelled. `RivalHit` (`:42`), `Whiff` swish + slide whistle (`:45`, `:96-103`), **single `Bounce` clip, no surface variation** (`:46`), `Net` (`:47`), `Whoosh` (**never called**, `:48`), `Call(good)` (only `Call(false)` used, `:49`), `Gasp` (`:50`), `Applaud` (`:53-65`, unreachable because the director always exists, `TennisGame.cs:906-907`) |
| `Tennis/TennisSynth.cs` | — | pure C# DSP: RBJ biquad (`:11-48`), SteelPan/Marimba/Bass/Pad/Kick/Clave (`:93-142`), formant crowd voice (`:145-161`) | shared synthesis kit |
| `Tennis/TennisAudioDirector.cs` | owns none; creates Music, Ambience, Announcer (`:19-28`) | — | `OnPointStarting` announcer queue (`:31-49`); `OnFault` (`:51-55`); `OnPointOver` crowd cheer/ooh/groan + music stings + announcer hype & score (`:59-90`); `OnFootstep` → Ambience.Step (`:93`); `Update` long-rally ooh (`:100`, **uncommitted** threshold change ≥8 & %4==0), stem mix by phase, duck music to .45 while announcer speaks or stinger (`:95-114`) |
| `Tennis/TennisMusic.cs` | 4 sources prio 32: beat/keys/lead loops + stings (`:45-50`) | 16-bar calypso in F, 112 BPM, 32 kHz, rendered **off main thread** `Task.Run(RenderStems)` (`:51`, `:109-174`), sample-locked `PlayScheduled(dspTime+.1)` (`:79-80`) | Stings Point/Winner/Game/MatchWon/MatchLost (`:17`) rendered lazily **on main thread** at first play (`:60-68`, `:232-270`); `Master` .55 never set externally (`:34-38`). **Only music in the game — none for golf or hub** |
| `Tennis/TennisAmbience.cs` | 4 sources: beach loop (64), murmur loop (64), crowd one-shots (40), feet (96) (`:26-31`) | 10 clips rendered on worker thread (`:32`, `:96-100`); calls before ready are skipped (`:40-67`) | Ooh/Groan 26 voices (`:40-42`), Cheer 24 voices or Roar 40 voices > .7 + whistles/claps (`:44-48`), Hush (`:37`); `Step` (`:52-64`): speed>4.5 → 45% chance shoe squeak (3 variants 2.1–3.6 kHz), random **source-wide** pitch .92–1.1, speed>1.5 → soft land; far player ×.45. `Land(weight)` **never called** (`:67`). Beach 18 s surf+breeze+gulls (`:103-135`), murmur 22 voices (`:138-165`) |
| `Tennis/TennisAnnouncer.cs` | 1 voice source prio 8 (`:51`) | `Resources.LoadAll<AudioClip>("Tennis/Announcer")` (`:52-59`), 43 line keys (`:14-35`) | Queue with delay/expiry (`:67-72`), Clear on new point (`:75`), 0.12 s gap (`:77-92`), take rotation (`:94-102`). **Folder `Unity/Assets/Resources/Tennis/Announcer` does not exist → announcer and all calls are silent** (`Say` returns early `:69`) |
| `Tennis/TennisJuice.cs` | lazily-added source (`:146`) | **new `AudioClip.Create` per ultimate** (2.2 s rising sine, 22.05 kHz), `Destroy(cue, +1 s)` (`:144-157`) | per-event allocation |
| `UI/Club.cs` `ClubSound` | 1 static DontDestroyOnLoad source (`:488-506`) | loads the 3 WAVs, vol .5 (`:503`) | buttons pop/tick (`UI/Hud.cs:23`; `UI/Club.cs:175,378,427`; `UI/HomeScreen.cs:284`), screen-wipe whoosh (`UI/Club.cs:535`), unlock pop (`UI/UnlockToast.cs:63`) |
| `Tennis/TennisUmpire.cs`, `TennisResortCrowd.cs`, `TennisStandsCrowd.cs` | — | — | **visual only** (umpire nod `:55`; crowd animation `Cheer`) |
| `Game/PointClipAudioTap.cs`, `Game/CaptureAudioTapKeeper.cs` | listener `OnAudioFilterRead` tap → native `SportsRecorderAudio` with dspTime stamps (`PointClipAudioTap.cs:13-24`); re-attached every .5 s while capturing (`CaptureAudioTapKeeper.cs:15-28`); added `NativeSportsSession.cs:107`, `:378-379` | — | game audio is recorded into point clips / session video |
| `Game/MuteWhenAutomated.cs` | — | — | `Muted` if batchmode or `GOLF_MUTE=1` (`:10`); `BeforeSceneLoad` sets `AudioListener.volume = 0` (`:12-16`); `Volume(on)` used by `NativeSportsSession.cs:193`, `:237`, `NativeSportsSession.Hub.cs:46` |
| Global volume | `AudioListener.volume` on/off only; `AudioListener.pause` during hub loads | `NativeSportsSession.Hub.cs:283`, `:337`, `:340` |

### 2.3 2026-10-15 "gameplay audio" themes (Clubhouse Pop / Stadium Snap / Toybox Rally)
- Plan only: `work/gameplay-audio/PLAN.md:7-11` (themes), `:16-20` (theme banks, reserved contact voices, bounded overlap, non-repeating takes, announcer queue, brake/slide/landing audio, audition surface), `:24-30` (acceptance: contact sound synchronous on the existing contact event, no per-hit allocation, contact voices never stolen; GATE_RESULTS in proof/).
- **Nothing installed**: names appear nowhere in `Unity/Assets` or `GolfArcade/` (grep); `work/gameplay-audio/` holds only `PLAN.md` (+ `PLAN_HitFeel_Haptics.md` copy is at repo root, see §4); no proof folder. No theme type, selector or bank exists.

### 2.4 Event → sound map
Tennis:
| Event | Sound | Call site |
|---|---|---|
| Player rally contact | `TennisSounds.Hit(grade, power, smash)` | `TennisGame.cs:2062` |
| Player serve contact | `Hit(Perfect/Great, servePower)` | `:773` |
| Online mirrored contact / bounce | `Hit` / `Bounce` | `TennisGame.Network.cs:61`, `:68` |
| Rival hit / rival serve / Versus remote | `RivalHit(.6/.9)`, `RivalHit(.8)`, `RivalHit(...)` | `:1707`, `:2192`, `TennisGame.Versus.cs:338` |
| Bounce (all venues identical) | `Bounce(|vy|/8)` | `:1568` (calibration beat `:529`) |
| Net | `Net()` | `:1547` |
| Out / fault / double fault | `Call(false)` + `audio.OnFault` | `:1600`, `:815-816` |
| Whiff / remote whiff / rival miss | `Whiff()` / `Gasp()` / `Gasp()` | `:2074`, `Versus.cs:256`, `:1651`, `:1679` |
| Point start | `audio.OnPointStarting` (announcer — silent) | `:2117` |
| Point/game/set/match | `audio.OnPointOver` (crowd, stings, announcer) | `:906` |
| Footsteps | `audio.OnFootstep` → `Ambience.Step` | `:326` (from `TennisActor.cs:1321`) |
| Ultimate | synth cue | `TennisJuice.cs:135` |
| Weather | EventSounds | `TennisConditions.cs:33` |
| No sound: dive landing (`:327`), brake/slide/direction change (anim only `TennisActor.cs:827`, `:853-855`), umpire, racket swing whoosh |
Golf:
| Event | Sound | Call site |
|---|---|---|
| Address / ready | `PlayReady` | `GolfGame.cs:2200` (+ `:2465`, `:2514`, `:2610`, `GolfGame.Network.cs:467`) |
| Backswing / release | `SetTension(load)` / `Release` | `:1942` / `:240`, `:1954`, `:1980`, `:1991` |
| Downswing | `PlayWhoosh(load)` | `:2196` |
| Strike | `PlayStrike(club, power)` | `:2223`, replay `:2774`, network `GolfGame.Network.cs:200`, signature shot `:1449` (Iron .9) |
| Landing (fairway/rough/sand/green/OOB) | **one `PlayThud`** | `:2310`, `:1469`, `:2794` |
| Ice | `PlayIceSkid` | `:2310`, `:2335` |
| Water | `PlaySplash` + `PlayGasp(.55)` | `:2377-2378`, `:2806` |
| Lava | `PlayLavaHiss` | `:2367`, `:2376`, `:2805`, `GolfGame.Network.cs:247` |
| Tree/rock/wall | `PlayKnock(stone)` / `PlayLeaves` | `:2326` |
| Movers balloon/twister/gull/cart | Boing / Gust / Squawk / knock+Horn | `GolfGame.Events.cs:228-243` |
| Gust event / twist reveal | Gust / Ratchet+Stamp | `GolfGame.Events.cs:163`, `:287`, `:134-135` |
| Rings / bounty | Chime(big) / Jingle | `GolfGame.Challenges.cs:131`, `:162` |
| Lip-out | `PlayGroan(.6)` | `:2348`, `:2701` |
| Cup / hole out | `PlayCup`; `PlayFanfare` + `PlayHoleOut(strokes,par)` | `:2351`, `:2802`, `:2927`; `:2928-2930` |
| Gallery | Applause(.3) on Perfect>.8; Gasp+Applause near pin; Applause(.25) on green; Groan close miss/OOB/bunker | `:2691`, `:2710`, `:2711`, `:2702-2708` |
| Unlocks / locked course / UI ticks | Fanfare / Groan(.3) / Tick | `:2555`, `:486`, `:666`, `:690`, `:805` |
| Weather | thunder/rumble/foghorn/ambience | `Game/WeatherView.cs:208`, `:253`, `:280`, `:287`, `:441` |
| Presentation | `PresentationStinger.Lead/Stop` | `GolfGame.Presentation.cs:95`, `:201` |
| No sound: golfer footsteps, golf music, per-lie landing, divot/sand-blast |
Hub/menus: only `ClubSound` pop/tick/whoosh; no hub music/ambience; `Hub/HubBayScreen.cs:46` video `audioOutputMode = None`.

---

## 3. TV vs phone audio split

| Source | API | Where it plays | Evidence |
|---|---|---|---|
| All Unity game audio (SFX, crowd, music, stinger) | Unity/FMOD on the shared `AVAudioSession` | the app's current route → **the TV when AirPlay is active**. No repo code sets Unity's category; `muteOtherAudioSources: 0` | `Unity/ProjectSettings/ProjectSettings.asset:90`; export trampoline `work/gameplay-regression/ios-export-before/Classes/UnityAppController.mm:193-199` |
| Racket "phone knock" (Tok/Ting/Clunk/Click/Tock WAVs synthesised in the plugin) | `AudioServicesPlaySystemSoundWithCompletion` (System Sound Services ignores the AirPlay route) | **phone speaker only** — the only second route. Default **OFF**. Not verified on device | `Unity/Assets/Plugins/iOS/GolfHaptics.mm:5-6`, `:144-169`, `:175`; `GolfHitFeel.h:27`, `:212-254`; default `GolfArcade/Unity/SportsSession.swift:137-140`; `proof/hit-feel/GATE_RESULTS.md:38` |
| SwiftUI menu sounds (tick/pop/whoosh) | `AVAudioPlayer` `ClubSound` | same route (TV under AirPlay) | `GolfArcade/Unity/ClubDesign.swift:76-88`; calls `TennisMenu.swift:235`, `:290`, `:319`; `SportsDisplays.swift:166`, `:442` |
| Lobby SceneKit | none (no `SCNAudioSource/SCNAudioPlayer`) | — | grep |
| Party voice chat | `AVAudioEngine` source node → main mixer | same session route; with `.allowAirPlay` plausibly the TV — unverified | `GolfArcade/.../PartyVoiceEngine.swift:763-787`, `:17`; `proof/party/PARTY_VOICE_NOTES.md:36`, `:77` |

Session/routing controls:
- `PartyVoiceEngine.beginSession`: `.playAndRecord`, mode `.default`, `[.allowAirPlay, .allowBluetoothHFP, .allowBluetoothA2DP, .defaultToSpeaker, .mixWithOthers]`, `setAllowHapticsAndSystemSoundsDuringRecording(true)` (`PartyVoiceEngine.swift:731-751`); `endSession` restores category only (`:753-759`); VPIO other-audio ducking set to minimum (`:768-769`); **no game ducking under speech** (`PARTY_VOICE_NOTES.md:76`); route-change/interruption observers (`:657-662`, `:713-720`).
- AirPlay picker: hidden `AVRoutePickerView` in `Unity/Assets/Plugins/iOS/GolfAirPlay.mm:1-36`; picture via Screen Mirroring / second scene (`Game/BigScreen.cs:45-47`; `SportsUnityAppController.mm:16-98`, TV renderer capped 1080p).
- Controller-only multiplayer phones get Unity sound off (`GolfArcade/Unity/SportsSession.swift:446`).
- Recording: `SportsAudioMixer.h` wait-free 3-source mixer (game, remote voice, mic) at 48 kHz (`:1-12`, `:29`); `SportsSessionRecorder.mm:298-300`, `:537-542`; the knock and haptics are **not** recorded.
- Sounds are **not** scheduled against `TennisGame.Lag`; the plan deliberately keeps contact sounds immediate (`work/gameplay-audio/PLAN.md:26`), so they reach the TV with the AirPlay A/V delay.

---

## 4. Haptics

### 4.1 Native plugin files (`Unity/Assets/Plugins/iOS/`)
| File | Purpose |
|---|---|
| `GolfHitFeel.h` | header-only Core Haptics pattern "synth": strike layers, cues, knock WAV renderer, 22-entry feel-test list (`:1-12`, `:256-285`) |
| `GolfHaptics.mm` | CHHapticEngine lifecycle (auto restart after interruption `:33-58`), `playsHapticsOnly = YES` (`:44`), delayed scheduling `engine.currentTime + delay` (`:94`), 35 ms swing-cue hold/cancel (`:18-22`, `:120-124`, `:183-185`), UIKit fallbacks (`:176-177`, `:186`, `:230-246`), system-sound knock (`:144-169`), tension buzz |
| `GolfAirPlay.mm`, `SportsBridge.mm`, `SportsPointCapture.mm`, `SportsPointRecorder.h/.mm`, `SportsSessionCapture.mm`, `SportsSessionRecorder.h/.mm`, `SportsAudioMixer.h`, `SportsUnityAppController.mm` | AirPlay picker; JSON bridge + `SportsClock` (`SportsBridge.mm:46-81`); recorders/mixer; dual-display controller |

### 4.2 C# API `Game/Haptics.cs`
P/Invokes `GolfHaptics_Warm/Hit/Cue/Selection/Notification/TensionStart/Set/Stop` (`:12-19`), no-ops off iOS (`:22-30`); gate `On => Enabled && !Suppressed` (`:35-38`); `Hit(in HitFeel)` fields Style, Grade 0-5, Pips, Supercharged, Power, Center, Mistime, Heat (`:47-58`, `:67-72`); `Play(Cue, intensity=1, delay=0)` delay clamped 0..1 s (`:76-79`); helpers `SwingFelt` (`:83`), `Putt` (`:86`), `Top` (`:90-96`), `Strike(StrikeGrade, power)` (`:100-111`), `Roar` (`:114`), `Tick/Success/Warning/Failure` → UIKit generators (`:117-121`), `Tension/Release` (`:125-146`), `Warm` (`:63`).

### 4.3 Cues (`Haptics.cs:44` mirrors `GolfHitFeel.h:25`; shapes `GolfHitFeel.h:161-209`; intensity × k × strength, floor .2 `:50-54`)
| Cue | Pattern | Triggered at |
|---|---|---|
| Swing | continuous 0–50 ms, I .3k, S .15 (`:167-168`); held 35 ms, cancelled if a hit lands | `TennisGame.cs:607` (`SwingConfirmedTick`, from `:593`, `:669`) |
| Whiff | continuous 160 ms, I .4k, S .1 (`:170-171`) | `TennisGame.cs:2076` |
| Bounce | 1 transient I .32k S .45 (`:173-174`) | `TennisGame.cs:1580` (delay `Lag`); **reused for golf movers** `GolfGame.Events.cs:228` (.6), `:233` (.8), `:243` (.5) |
| PointWon | rising transients 0/90/180 ms (`:176-177`) | `TennisGame.cs:918` (delay `Lag`) |
| PointLost | falling 0/140 ms (`:179-180`) | `:918` (Lag) |
| GameWon | 3 rising taps + .5 s crowd rumble (`:182-193`) | `:918` (Lag) |
| MatchWon | 6 taps + 1.0 s rumble (`:185-192`) | `:918` (Lag) |
| Top | 1 transient I Mix(.55,1,k) S 1 (`:195-196`) | golf downswing `GolfGame.cs:2196` (not putter) |
| Roar | 9 decaying transients 85 ms apart over .8 s continuous (`:198-204`) | golf cup `GolfGame.cs:2351`, `:2927` (guarded by `cupFeedback`) |

Strike pattern `BuildHit` (`GolfHitFeel.h:84-159`): contact crack + decaying body (`:93-101`); sting 40 Hz tremolo 70–160 ms on unclean contact (`:104-117`); reward: supercharged 2nd crack @70 ms + 220 ms surge (`:120-127`), PERFECT ring + sparkle @140 ms (`:128-135`), EXCELLENT 60 ms ring (`:136-142`); smash shock @80 ms (`:145-146`); streak pips up to 4 taps from 220 ms (`:149-155`); weight by style (`:57-69`); cleanliness pulled 50% toward grade table .1/.3/.55/.75/.9/1 (`:73-79`).

### 4.4 Mappings
- Tennis (`Tennis/TennisHitFeel.cs`): style Smash→Heavy, Serve→Serve, Volley/Lob/Slice/LowPickup→Touch, Dive→Scramble, else Drive (`:12-19`); `Rally` grade = TV grade, pips = streak 0..2, center = 1−faceError, **Mistime hard-coded 0** (`:33`, so timing lateness is ignored), heat = (rally−2)/10 (`:23-35`); `Serve` (`:38-46`); online `Graded` (`:49-56`).
- Golf (`Haptics.cs:100-111`): Perfect→grade 5 center 1; Great→3/.85/mistime .2; Good→2/.7/.35; Thin→1/.25/.45; putter `Putt` grade 3 center 1 (`:86`); backswing tension I .15+.85·l², S .2+.7·l (`:132`), `Top` stops tension and mutes it 1.5 s (`:90-96`, `:129`).

### 4.5 All `Haptics.*` call sites
Tennis: `TennisGame.cs:607` SwingFelt; `:775` Hit(Serve); `:918` Point/Game/Match cues (Lag); `:1580` Bounce (Lag); `:2063` Hit(Rally); `:2076` Whiff; `TennisGame.Network.cs:64` Hit(Graded).
Golf: `GolfGame.cs:1916` Tension; `:1953`, `:1980`, `:1990`, `:240`, `:756` Release; `:2196` Top; `:2200` Tick (address); `:2224` Putt/Strike; `:2311` Tick (first touchdown); `:2327` Tick (tree/rock); `:2351`, `:2927` Roar; `:2367`, `:2378`, `:2934` Failure (lava/water/OOB); `:666`, `:690`, `:805` Tick (UI/aim); `GolfGame.Events.cs:135` Tick, `:228/:233/:243` Bounce cue, `:238` Tick; `GolfGame.Challenges.cs:132` Tick, `:163` Success; `GolfGame.Network.cs:129`, `:194` Suppressed, `:278` Release; `Game/WeatherView.cs:288` Tick (near thunder); `UI/Lobby.cs:212`, `:519`, `:561`, `:570` Tick; `Game/NativeSportsSession.cs:194`, `:237`, `:403`, `NativeSportsSession.Hub.cs:46` enable/warm/release.
Swift-side UIKit haptics independent of the plugin: `GolfArcade/Unity/SportsSession.swift:297`, `:737`; `TennisMenu.swift:268`, `:290`, `:318`; `HubSession.swift:451`, `:604`, `:611`; TOSS button rigid impact `TennisPlayViews.swift:470`. Dead second engine: `GolfArcade/Feedback/SwingFeedbackController.swift` (compiled, unreferenced).

### 4.6 The two clocks
- Rule: arm-caused (strike, swish, whiff) **now**; TV-seen (bounce, point, game, match) **`TennisGame.Lag` later** (`PLAN_HitFeel_Haptics.md:50`; `GolfHitFeel.h:23-24`).
- `Lag => lag.Estimate` (`TennisGame.cs:481`) from `TennisLagLearner` (median of ≤9 raw-lateness samples + camera prior ×2, clamp 0..1 s, ±.3 s outlier reject `TennisLagLearner.cs:20-54`) — by definition TV delay **plus the player's habit** (`:6-7`); learns only without a camera prior (`TennisGame.cs:483`); saved per point (`:484-488`, `:920`); per-TV prior keyed by AirPlay port (`GolfArcade/Unity/SportsSession.swift:1201-1213`). Lag also advances swing/serve timing (`TennisGame.cs:393`, `:442`, `:565`, `:584`) and multiplayer screen credit (`Multiplayer/SportsMultiplayer.cs:226`).
- Applied on the haptic engine clock (`GolfHaptics.mm:94`), clamped to 1 s twice (`Haptics.cs:78`, `GolfHaptics.mm:182`); delayed cues get no UIKit fallback (`:186`).
- **Golf has no TV clock**: landing/knock/cup/failure/mover haptics fire at game time.
- **Audio and VFX never use Lag** (only haptics do).

### 4.7 Docs/gates
- `PLAN_HitFeel_Haptics.md` (repo root; not in work/gameplay-audio): 7 fixes (`:9-17`), known latencies unchanged — assisted contacts 45–180 ms late, serve haptic 200–450 ms after swing, detector confirm 10–50 ms after peak, online a round trip late (`:19-23`); knock opt-in (`:52`, `:75`); next: device tuning, predictive crack, serve haptic at judgement (`:88-94`).
- `proof/hit-feel/gates.txt:1-16`: 15 off-device gates PASS. `proof/hit-feel/GATE_RESULTS.md`: EditMode 8/8 (`:24`), iOS compile/device build (`:25-28`); **install on iPhone NOT RUN (`:29`); all 6 device feel gates NOT RUN (`:35-40`)**; responsiveness device gate NOT RUN (`:55`).

---

## 1B. Golf / environment VFX — quick facts (full detail in §1D at the end)

| Item | Evidence |
|---|---|
| `Game/ShotEffects.cs` builds all golf shot FX once under a "Shot effects" GameObject (`:76`) via `BuildParticles(name, size, life, gravity)` (maxParticles 200, world space, emission disabled, alpha .9→.6→0, size .5→1→1.3, `GolfArcade/ParticleSoft` shader) (`:305-333`), then re-emits with `EmitParams`, so it is **pooled** (no per-event Instantiate; grep of `Instantiate(` in Game/Course/Environment finds only models/props) | `ShotEffects.cs:76`, `:300-333` |
| API: `Strike(at, fwd, lie, power, putt)` `:217`; `Knock(at, leaves, stone)` `:245`; generic `Burst(at, a, b, count, speed, size, life, lift)` `:280` (used by round events/rings `GolfGame.Events.cs:227-242`, `GolfGame.Challenges.cs:128`); `BeginFlight/Land/EndFlight/ClearTracer` `:343-360` (tracer `Game/Tracer.cs`, comet `Game/CometTail.cs`, trail style from Gear `:71`); `Cup` ring `:410`; `WetLanding` ring `:411`; `Touchdown` `:414`; `LavaBurst` `:445`; `IceSpray` `:476`; `Splash` `:495`; `SetQuality(Quality)` `:336` | `ShotEffects.cs` |
| **Per-lie landing table** (the only per-surface VFX table in the game): Water→Splash; Ice, Bunker, Green, Rough/OOB, default (fairway) colour pairs; 10+14·strength puffs, size .35–.75, life .3–.6; overridden by `EnvironmentFx.Landing` when Stage≥6 | `ShotEffects.cs:414-443`; `Environment/EnvironmentFx.cs:23-33` |
| Weather precipitation: looping pooled systems (`main.loop = true`, `rateOverTime = rate * level`) | `Game/WeatherView.cs:132-136`, `:565-570`; art bible notes rain/snow maxima >300 (`ArtDir/style/ART_BIBLE.md:132`) |
| Not covered in depth here (inspect before designing): `Game/Tracer.cs`, `CometTail.cs`, `MoverView.cs`, `RingView.cs`, `LandingZone.cs`, `SignatureShot.cs`, `Course/LavaWorld.cs`, `WaterMotion.cs`, `GolfCourseFoam.cs`, `Environment/DreamWorldArt.cs`, `DreamHazardView.cs`, `WeatherDirector.cs`, `Tennis/TennisVenueFx.cs`, `TennisVenueBuilder.Volcano.cs`, Hub FX; `Unity/Assets/Resources/Effects/{dust,flash,ring,splash,grass}.png` sprites | file list from grep §0 |

---

## 8. Gaps (consolidated)

**Architecture**
1. No event bus: each gameplay site hand-calls fx / sounds / Haptics / juice / hud (tennis `TennisGame.cs:2017-2063`, serve `:766-775`, opponent `:1707`, `:2192`, online `Network.cs:53-69`; golf `GolfGame.cs:2219-2227`, `:2309-2378`, `Events.cs:227-244`). Fan-out is copy-pasted 4-5 times per sport, and the copies have drifted: online bounce has no VFX, opponent contacts have no haptic, replay has no haptic.
2. Three different clocks: VFX on the rendered contact frame (LateUpdate order 1100), audio and haptic on the 120 Hz sim step, and TV-seen haptics delayed by `Lag` (tennis only). Golf has no TV clock at all. No shared timestamp.
3. `Lag` mixes the TV delay with the player's habit (`TennisLagLearner.cs:6-7`).

**VFX**
4. Dead or inert channels: `TennisFx.Shake` is never read; `TennisJuice.Punch` and `Apply` do nothing; `TennisJuice.OverrideCamera` is never called (all cinematic cuts inert); hit-stop is 0, against the ART_BIBLE's "14/30/45 ms holds"; `TennisFx.Celebrate` confetti has no caller (no tennis winner or match confetti); the hero torso kick is off for match heroes; tennis instant replay is off.
5. Tennis has no per-surface/venue bounce (the `court` colour is ignored). Golf has a per-lie colour table but **one** thud sound for every lie and no divot/sand-blast/grass-blade FX found.
6. Inconsistent styles: tennis uses Higgsfield sprites plus its own additive/alpha shaders; golf uses `GolfArcade/ParticleSoft` with procedural soft textures; `Resources/Effects/*.png` is a third set. UI FX are split across TennisHud sparks, the TennisJuice overlay, golf StrikeHud, and Hud callouts.
7. Pooling is good: TennisFx and ShotEffects are prebuilt and re-emitted, weather loops are prebuilt, and Reduced mode thins the counts (`EnvironmentFx`).

**Audio**
8. Only 3 WAV files; everything else is synthesised at runtime with single fixed takes. Tennis hit pitch variation is cancelled (`TennisSounds.cs:34-36`); footstep pitch is source-wide.
9. Announcer is silent (`Resources/Tennis/Announcer` missing). Umpire is silent. The 3-theme plan (Clubhouse Pop / Stadium Snap / Toybox Rally) was **never installed**.
10. No mixer, buses, snapshots, or 3D audio. Tennis contact plays on a priority-128 shared source and can be culled before feet/crowd/music (32 real voices). Golf strike is priority 0.
11. Per-event allocation and main-thread synthesis: the ultimate cue makes a new clip each time; music stings and EventSounds clips render on the main thread at first use; EventSounds is re-synthesised per instance (golf, tennis weather, each dream hazard).
12. Missing sounds: tennis dive landing, brake/slide, racket swing whoosh (method exists but is unused), `Ambience.Land` unused; golfer footsteps; music for golf and hub; hub ambience; per-surface golf landings.

**TV vs phone / haptics**
13. All Unity, menu and likely voice audio goes to the AirPlay TV. The only phone-local sound is the opt-in system-sound knock (default OFF, untested on device). Sounds are never compensated for the AirPlay delay.
14. Haptics: all 6 device feel gates are NOT RUN. Rally `Mistime` is fixed at 0 by design ("early/late is an aim choice"). The golf `Bounce` cue is reused for movers. UIKit Tick/Success/Failure ignore the strength setting. Swift-side UIKit haptics bypass the plugin. `SwingFeedbackController.swift` is a dead second engine. No haptic for: opponent contact, own ball landing in, out/fault calls, supercharge or ultimate arming, golf lip-out, online bounce.

**Perf**
15. There is no `work/frame-rate-60b/BUDGET.md`. The budget rules live in `ART_BIBLE.md:128-133` (60 fps on every tier, measure particle counts per effect per tier). Max tennis FX particles are 676. The pipeline runs HDR + MSAA 4 + 4096 shadows on High, with a governor step-down that never steps back up.

---

## 1D. Golf / environment / venue VFX — full pass (paths relative to `Unity/Assets/`)

### ShotEffects (`Scripts/Game/ShotEffects.cs`), built once in `Create` (`:74-111`) from `Game/GolfGame.cs:221`; all re-emitted, only build-time `Destroy` of colliders (`:174`)
| System | Line | Size | Life | Gravity | Texture |
|---|---|---|---|---|---|
| Puffs | :84 | .7–1.1 | .22–.5 | -2.2 | `Resources/Effects/dust.png` (:87-88) |
| Splash | :85 | .9–1.4 | .28–.9 | -3.5 | soft disc |
| Clippings | :89 | .28–.5 | .55–.95 | -9 | `Effects/grass.png` 2×2 sheet, spin ±6 (:92-106) |
| Trail | :90-91 | .3–.5 | .5–.9 | 0 | soft disc, **max 3000** |
| Flares (pooled quads on layer 31, SetActive; ease-out cubic grow, fade after 25%, `Step` :192-206): Strike flash (flash.png), Strike ring (ring.png, flat), Splash crown (splash.png) | :107-109 | quad | — | — | — |

| Effect | Look | Trigger |
|---|---|---|
| `Strike` :217-241 | putt: soft ring .4 s; full: flash .22 s (.25→.9+1.1·power) + ring .45 s (.3→2.2+2.5·power) + clippings 8+22·power (×2 in rough); bunker → `Touchdown(Bunker, 1.2+power)` sand spray; water → no clippings. **Ice/green non-putt strikes still throw grass** | `GolfGame.cs:2225` (first Flight frame), replay `:2775` |
| `Knock` :245-276 | leaves 44 green clippings 1.0–1.7 s; stone/wood 12 grey/brown puffs | `GolfGame.cs:2325` (windmill sails count as Tree → wood chips, `Course/CourseShot.cs:268`) |
| `Burst` :280-294 | generic puff | movers via `MoverKnock` `GolfGame.Events.cs:208-247` (balloon 26 white/pink :227; twister 46 dirt 1.6 s :232; gull 34 feathers :237; cart 14 dust :242), called `GolfGame.cs:2323`; rings 40 gold/turquoise/pink `GolfGame.Challenges.cs:128` |
| `EmitTrail` :372-406 | reward trail every .14 yd, ≤80/frame: Sparkle / Fire / Rainbow | `LateUpdate` :362-367; style `GolfGame.cs:978` |
| `Touchdown` :414-442 | 10+14·strength puffs, per-lie colours (:419-426) overridden by `EnvironmentFx.Landing` (Stage defaults 7, `Environment/EnvironmentLook.cs:21-25`) | `GolfGame.cs:2309` (every landing/bounce), `:1468` (signature shot, always Green), `ShotEffects.cs:226` |
| `WetLanding` :411 | blue ring .35 s | `GolfGame.cs:2312` when `WetLandingRules` (`GolfGame.Experience.cs:43-46`) |
| `Splash` :495-526 | crown .7 s .6→2.6, 46 drops, 24-particle ripple **drawn with the dust sprite** | `GolfGame.cs:2377`, replay `:2806` |
| `LavaBurst` :445-472 | orange flash .4 s, 70 sparks, 16 smoke | `GolfGame.cs:2367`, `:2376`, `:2805`, `GolfGame.Network.cs:247` |
| `IceSpray` :476-493 | 3–10 chips every .06 s while skidding | `GolfGame.cs:2337-2341` |
| `Cup` :410 | one gold ring .4 s | `GolfGame.cs:2351`, `:2927` |
| Hole-out confetti | **UI mesh** confetti 90–110 pieces | `UI/HoleGraphics.cs:70-91`, thrown `UI/HoleOutCard.cs:140` |
| Tracer / comet | `Game/Tracer.cs` LineRenderer, point every .6 yd (:13), ≈.42% view height (:62-67), 2.5 s fade; `Game/CometTail.cs` POV tube .333 s, from `Resources/Course/swing_trail.json`. **New Gradient/AnimationCurve/ToArray every frame** (`Tracer.cs:78-92`, `CometTail.cs:67-75`) | `GolfGame.cs:2295`, `:2314`, `:2379`, `:2909`, `:2921`, `:1127`, `:1411`, `:2748`, `GolfGame.Results.cs:47` |
Single shared ring flare (`ShotEffects.cs:183-190`): Strike/Cup/WetLanding restart each other (WetLanding fires every bounce).

### EnvironmentFx coverage
`ParticleCount` and `MotionScale` used only by TennisFx (`TennisFx.cs:137-138`); `ParticleAt` used in `ShotEffects.cs:440,458,470,491,511,524` + TennisFx. **Not reduced**: strike clippings/flares, Knock, Burst (movers/rings), EmitTrail, all weather/twister/lava/pollen. `Constrained` comes from native `presentationConstrained` (`Game/NativeSportsSession.cs:246`).

### Other golf/course/environment systems
| System | Details | Evidence |
|---|---|---|
| MoverView twister | 2 funnel meshes (`Golf/Twister` shader), dust skirt, Debris loop max 400 @110/s, Dust cloud max 120 @30/s | `Game/MoverView.cs:324-392`; built `GolfGame.Events.cs:95` |
| Mover reactions | balloon wobble :111, cart bump :124, gull tumble :152-157; none for RockGate/WindLift (:104-105); balloon burner Perlin sphere :113-114 | `MoverView.cs` |
| RingView | torus + spinning coin, pulse; `Take` scale + coin fly .45 s | `Game/RingView.cs:120-157`; `Challenges.cs:65`, `:125`, `:192` |
| LandingZone | amber breathing ellipse; **mesh rebuilt every frame** | `Game/LandingZone.cs:43-76` |
| AimDots | 40 pooled dot quads + halos + load mark | `Game/AimDots.cs:34-45` |
| BallLook | halo + shadow quads, min screen size, fog-brighter halo | `Game/BallLook.cs:42-45`, `:111-121` |
| CinematicRig | baked trail tubes (SkinnedMeshRenderer) | `Game/CinematicRig.cs:55-68`, `:105-125` |
| WeatherView | `Particles()` loop/world/box (`:125-142`): Rain max 2600 rate 1500·precip 1.4 s stretched v.y -24 (:88, :513-521); Snow max 3200 rate 1100 8 s (:92, :522-529); Ash max 1400 rate 450 9 s (:94, :530-537); Embers max 200 (:97, :538-545); Splashes max 300 manual (:99, :547-557). **Snow/ash steady-state demand ≈8800/4000 > caps → silently clipped**. Lightning: 2 LineRenderers `Golf/LightningBolt` .32 s + global `_GolfWeatherFlash` + sun boost (:294-373), every 5–12 s in storm (:279), ash biome = orange flash + 40 embers (:298-307). Domes: StormSky (:395-431), WeatherFog (:446-472), WeatherGround (:475-493). `Fall()` allocates closures per frame (:513-545) | `Game/WeatherView.cs`; created `GolfGame.Events.cs:55-58` |
| WeatherDirector | publishes `_EnvironmentWetness/_Snow/_Storm` globals | `Environment/WeatherDirector.cs:23-38` |
| LavaWorld (magma holes) | 10 steam vents (max 50), plume max 320, 3 fountains max 120, embers max 300, geysers per `GEYSER_` marker; prewarmed loops; **no quality tier** | `Course/LavaWorld.cs:426-528`; `HoleView.cs:337-339` |
| DreamWorldArt pollen | 4 systems max 24 (holes 19/20) | `Environment/DreamWorldArt.cs:88-102` |
| DreamHazardView | warning discs, plume cylinder toggle, countdown, rumble; no particles/eruption burst | `Environment/DreamHazardView.cs:12-57` |
| WaterMotion / GolfCourseFoam / SpinningSails | blend-shape sea + flags / static shore feather / physics only | `Course/WaterMotion.cs:49-58`; `GolfCourseFoam.cs:13-45` |
| Tennis volcano venue | steam 3/7 vents, plume 320/700, fountains 2/4, embers 90/200 — **tier-scaled** by TennisQuality | `Tennis/TennisVenueBuilder.Volcano.cs:410-665` |
| TennisVenueFx | scenery behaviours (FollowCamera, FaceCamera, Drift, Blink [material instance], Pulse, LavaFlow, FallFlow, Sway, Flicker) | `Tennis/TennisVenueFx.cs:13-125` |
| Tennis actor stroke trail | disabled when a hero is attached | `Tennis/TennisActor.cs:285-293`; `TennisHeroSetup.cs:51` |
| Hub | no ParticleSystems; HubBayScreen `_Flash` burst, HubLife wind/birds/flags | `Hub/HubBayScreen.cs:56-73`; `Hub/HubLife.cs:9-58` |
| Golf camera | no shake/punch/hit-stop; only replay 0.4× | `GolfGame.cs:2766` |

### Effect/weather shaders
`Shaders/ParticleSoft.shader` (alpha; golf puffs, tracer, halo, aim dots, twister) and `Shaders/ParticleAdd.shader` (additive; embers, fountains, pollen) are outside Resources and are found with `Shader.Find`, so they depend on Always Included (`ShotEffects.cs:300`). `Resources/Tennis/Shaders/TennisFx{Additive,Alpha}.shader`; `Resources/Golf/LightningBolt.shader`, `Golf/Twister.shader`, `Environment/DreamLavaPlume.shader`. Weather: `Resources/Golf/WeatherParticle.shader` (lens/depth fade, flash-reactive), `WeatherFog.shader`, `WeatherGround.shader`, `StormSky.shader`, `WeatherCommon.hlsl`, plus `GolfGround.shader` and `Environment/Shaders/EnvironmentSurface.hlsl` consuming `_Environment*`.

### Golf VFX gaps
- The replay has no Touchdown, Knock, Burst, IceSpray, WetLanding or Cup effects; a holed ball in the replay gets sounds only (`GolfGame.cs:2759-2812`).
- Multiplayer `FollowHostPath` shows only LavaBurst (`GolfGame.Network.cs:239-260`).
- No visual effect on: lip-out (`:2347-2349`), OOB (`:2934`), or the dream vent eruption.
- WindLift maps to Twister, so it shows dirt and a "Twister!" callout (`Course/CourseMovers.cs:396`).
- The tracer comment says green/yellow/red, but the colours in the data are gold/cream/blue (`ShotEffects.cs:6-9`).
