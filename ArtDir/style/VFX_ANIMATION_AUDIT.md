# VFX + Animation Audit: Party Sports (Oct 14, 2026)
> **Superseded by `EXPERIENCE_AUDIT.md`.** This file is kept as the inventory only. Findings 2 (Scuba racket), 3 (shake), 4 (hit-stop) and 9 (particle budget) are dropped. The first three are intentional, per Adnan.
**Audit only. Nothing in the project was changed, staged or committed.**

Evidence comes from live captures in a refreshed scratch clone (`~/UnityScratch_depths`, Assets/Packages/ProjectSettings rsynced from the real project tonight), run in foreground batchmode:
- Tennis: resort, `CurrentTennisPointFilm`, a 4-shot point on the live AutoPlay.
- Golf: cliffside hole 12, `CurrentGolfSwingFilm`.
- Emotes: `EmoteFilm` on the current male match hero with current clothing, with front, side and game cameras.

The sheets are in `ArtDir/style/vfx-anim-audit/`. Source reads cover `Unity/Assets/Scripts`. The standard to fix against is `VFX_ANIMATION_STANDARD.md`.

## What exists (inventory)
**How VFX is built:** every effect is code-built at runtime. There are **0 particle prefabs, 0 ParticleSystems saved in scenes, no VFX Graph, and no tween library**. Systems are created once and reused with `Emit()`. That's good: there is no per-hit Instantiate.

| Owner (file) | Effects | Trigger | Max particles | Material / shader | Life |
|---|---|---|---|---|---|
| `Scripts/Tennis/TennisFx.cs` | Impact flash 4, shockwave ring 6, sparkles 60, impact streaks 48, felt fuzz 50, bounce dust 40, footstep dust 60, bounce ripple 8, confetti 240, supercharge stream 160, 6 skid-mark quads, timing-cue ring | `TennisGame` calls: `Contact`, `OpponentContact`, `NetHit`, `Bounce`, `Footstep`, `Slide`, `Celebrate`, `Stream`, `Cue`, `Whiff` | 676 total | `Resources/Tennis/Shaders/TennisFxAdditive`/`TennisFxAlpha`, falling back to `Sprites/Default`. Sprites in `Resources/Tennis/Fx` (impact, ring, sparkle, dust). Confetti is a generated white 4×4 square. | 0.09–2.6 s |
| `Scripts/Game/ShotEffects.cs` (+ `Tracer.cs`, `CometTail.cs`) | Puffs 200, splash 200, clippings 200, ball trail **3000**, tracer line, comet tail | `GolfGame`: `Strike`, `Touchdown`, `Knock`, `Burst`, `LavaBurst`, `IceSpray`, `Splash`, `BeginFlight`/`Land`/`EndFlight` | about 3,800 | `GolfArcade/ParticleSoft`, falling back to `Unlit/Color` | 0.28–1.4 s |
| `Scripts/Game/WeatherView.cs` | Rain **2600**, snow **3200**, ash 1400, embers 200, splashes 300, lightning bolt mesh | Course sky state (`Course.Sky`) | 7,700 pool | `Resources/Golf/WeatherParticle.shader`, `GolfArcade/ParticleAdd` | 0.18–8 s |
| `Scripts/Course/LavaWorld.cs` | Lava fountains 90/120, steam 40, smoke 50/320, embers 300 | Lava course build (always on) | about 920 | `new Material(Shader.Find(...))` | 2.8–20 s |
| `Scripts/Game/MoverView.cs` | Twister debris 400 + dust cloud 120 | Twister mover | 520 | ParticleSoft with **`Texture2D.whiteTexture`** | 2.2–4 s |
| `Scripts/Tennis/HeroTennisDriver.cs` | Racket trail (TrailRenderer) | strokes | n/a | `TennisLook` glow, falling back to `Sprites/Default` | n/a |
| `Scripts/Tennis/TennisGame.cs` | Landing ring (LineRenderer), ball squash on bounce, HUD flash from `fx.Flash` | ball | n/a | `GolfArcade/VertexColorUnlit` | n/a |
| Presentation | `PresentationStinger`, `GolfGame.Presentation.cs`, hole-out card, HUD badges | big moments | n/a | n/a | n/a |

**How animation is built:**
- `HeroTennisDriver.cs` (2,073 lines) runs a hand-built **PlayableGraph**: a full-body mixer, an upper-body mixer, an AvatarMask layer mixer, foot IK off on the clips, its own foot lock and ground lift, a "contact assist" that nudges the arm by up to 0.5 m and lunges the body by 0.3 m so the racket meets the ball, and left-hand grip release times.
- Root motion is off for the match heroes.
- There are no AnimatorControllers in the project.
- Clips:
  - `Resources/Tennis/Performance/*.anim`: 20 clips (forehand/backhand corrected and polished, HitPerfect, Idle, CelebratePoint, MatchWin/Lose, MissWhiff, SadPointLost, ×2 sexes).
  - `Resources/HeroMoves/{Male,Female}/*.fbx`: 7 emotes plus Walk and Run, solved in Blender by the emote-standard pipeline.
  - The old taunts (Scuba, Spike, Thrust) and intros (Wave, BringIt, Pushups).
- Golf: `GolferView.cs`/`HeroGolfer.cs`. Hub: `HubHeroAnimator.cs`.
- Wind sway is a global shader value (`GolfWindSway.cs` → `_GolfWind`).
- Haptics are rich and native (`Haptics.cs`, `TennisHitFeel.cs`).

## Findings, worst first
| # | Severity | Finding | Evidence | Where |
|---|---|---|---|---|
| 1 | **High** | **Emote clipping is still there.** The Oct 12 audit found **309 problems (152 very obvious)**: hands inside thighs and hips on Walk/Run every stride, racket in the leg, shirt tears at the armpit, shoes 17 mm under the ground. Its gates G1–G13 all "PASS" because **no gate checks clipping**. | `vfx-anim-audit/A_prior_clipping_top12.jpg`, `work/emote-standard/CLIPPING_AUDIT.md` | `Resources/HeroMoves/*`, `work/emote-standard/GATE_RESULTS.md` |
| 2 | **High** | **The racket leaves the hand in the old Scuba taunt.** The racket hangs at ground level under the hero from f17 to f107 while the hands are at his face. | `vfx-anim-audit/A_Emote_Scuba_front.jpg` | `HeroTennisDriver.PlayTaunt`, grip / `leftRelease` |
| 3 | **High** | **Camera shake is dead code.** `TennisFx.Shake` is set on every contact, net hit and whiff, but nothing in the project reads it. Golf has no shake at all. Only the HUD reads `Flash` (×0.25). | code search: no `.Shake` reader | `Scripts/Tennis/TennisFx.cs:27,155,169`, `TennisShoulderCamera.cs` |
| 4 | **High** | **No hit-stop anywhere.** Tennis and golf contacts never freeze time; the only `timeScale` change is the 0.4× replay slow-mo. A perfect hit doesn't feel heavier than a normal one, apart from particles and haptics. | code search | `TennisGame.cs:2037`, `GolfGame.cs:2217` |
| 5 | Med-High | **Putt drop has no visual payoff.** The ball is hidden (`SetActive(false)`) and the game plays cup and fanfare sounds, a roar haptic and a HUD badge. There's no burst at the cup, no flag pop, no slow-mo on the last roll. Only 2 channels happen where you're looking. | `G2_golf_flight_land_result.jpg` | `GolfGame.cs:2897-2905, 2776` |
| 6 | Medium | **The shockwave ring is oversized.** It grows to about a quarter of the screen and passes through the hero for about 6 frames after contact (f+2 to f+8), covering the player and ball at the moment you want to read the shot. | `T2_tennis_contact_crop.jpg` | `TennisFx.cs:63` (grow 5, size .35) |
| 7 | Medium | **Grey smoke dust in the Spike taunt** sits mid-court as a grey cloud for the whole emote, about 2 s. It's grey, not the bible palette, and it's the opposite of a punchy cartoon puff. | `A_Emote_Spike_side.jpg` | `TennisFx.dust` (life .35–.7 but re-emitted), taunt code |
| 8 | Medium | **Golf strike timing needs checking.** The film's recorded impact (f0) arrives while the hero is still at the top of the backswing. The club only reaches the ball and the strike burst fires about **8 frames (0.27 s) later**. The effect matches the visible contact, but there's a gap between input and visible hit. Measure it on device. | `G1_golf_strike_crop.jpg` | `GolfGame.cs:2191-2219`, `CurrentGolfSwingFilm` |
| 9 | Medium | **The particle budget is far above an iPhone budget.** Weather pools are 2,600 rain / 3,200 snow, plus a 3,000-particle ball trail and about 920 always-on lava particles with smoke 38–85 m wide (heavy overdraw). The standard targets ≤ 300 live gameplay particles plus ≤ 600 weather. | code | `WeatherView.cs:88-99`, `ShotEffects.cs:91`, `LavaWorld.cs:440-520` |
| 10 | Medium | **White-texture and fallback risk.** Twister dust uses `Texture2D.whiteTexture`, so it shows as square-edged particles. Six effect builders fall back to `Sprites/Default` or `Unlit/Color` when a shader is missing from the build (white or flat squares on device). Confetti is a white square on purpose. Add a missing-shader scan to the build. | code | `MoverView.cs:300`, `TennisFx.cs:40`, `ShotEffects.cs:301`, `HeroTennisDriver.cs:486` |
| 11 | Medium | **Four parallel effect systems** (TennisFx, ShotEffects, WeatherView, LavaWorld) each build their own materials, textures and colors in code (about 40 hard-coded `new Color(...)`). There is no shared palette, master particle shader set or naming. That's why styles drift between sports. | code | files above |
| 12 | Low-Med | **Event color clash with the bible.** Golf shot quality uses green, yellow and red trails (`ShotEffects.PureColor`, etc.). Red/orange is now the bible's reserved hazard color. Tennis felt fuzz is #DBFF47 lime. | code | `ShotEffects.cs:45-48` |
| 13 | Low | **No emote film for the 7 new emotes.** `EmoteFilm` only knows the old taunt and intro names (ArgumentException on `Emote_JumpJoy`), so the new set can't be re-filmed in the game scene with the current tool. | `scratch work/vfxaudit/emote2.log` | `Editor/EmoteFilm.cs` |
| 14 | Low | **Audio sync can't be checked from captures.** Batchmode records silence (automated mute), so audio/visual sync was checked in code only. Hit sound, haptic and FX fire in the same call for tennis contact, bounce, golf strike, touchdown and water. That's good. | `tennis_resort/audio.wav` (all zero) | `MuteWhenAutomated` |

What is already good (keep it):
- The effects are pooled, which is efficient.
- Tennis contact FX fire on the exact contact frame (impact star at f0 in T2).
- The driver anchors clip contact to gameplay contact.
- The ball squashes on bounce.
- Haptics are rich.
- Wind sway is already a global shader value.
- Golf per-surface landings exist (puff, clippings, splash, lava, ice).

## Feedback-channel matrix (≥ 3 channels where the player is looking)
| Event | Visual | Sound | Motion: shake, hit-stop, slow-mo | Haptic | Verdict |
|---|---|---|---|---|---|
| Tennis contact | ✔ | ✔ | ✘ (shake dead, no hit-stop) | ✔ | 3, but missing the weight layer |
| Tennis perfect / supercharge | ✔ + HUD flash | ✔ | ✘ | ✔ | needs hit-stop + shake |
| Bounce | ✔ dust, ripple, mark, squash | ✔ | n/a | ✘ | OK |
| Net cord | ✔ | ? (not found in fx path) | ✘ | ✘ | **< 3** |
| Tennis winner / match | ✔ confetti | ✔ crowd, stinger | camera presentation | ✔ | OK |
| Golf strike | ✔ puff + trail | ✔ | ✘ | ✘ in `GolfGame` (Haptics.Hit is tennis only) | **< 3** |
| Golf landing | ✔ | ✔ | ✘ | ✔ first touch | OK |
| Putt drop | ✘ at cup (HUD badge only) | ✔ | ✘ | ✔ roar | **weak** |
| Water / lava | ✔ | ✔ | ✘ | lava ✔ / water at result only | borderline |
| Wind / gusty | foliage sway | ? | n/a | n/a | needs leaves + audio bed |
| Rain / storm | ✔ rain, splashes, bolt | ? | ✘ flash | ✘ | check audio + flash |

## Evidence sheets (`ArtDir/style/vfx-anim-audit/`)
- `T0_tennis_point_overview.jpg`: the whole point, every 1.5 s.
- `T1/T2/T3_tennis_contact_*.jpg` and `_crop.jpg`: contact strips f−8 to f+12.
- `G1_golf_strike(_crop).jpg`: golf swing and strike, f−22 to f+16.
- `G2_golf_flight_land_result.jpg`: flight, landing and the result card.
- `A_Emote_{Spike,Scuba}_{front,side}.jpg`, `A_Intro_Pushups_*.jpg`: current hero with current clothes.
- `A_prior_clipping_top12.jpg`: the worst 12 from the Oct 12 clipping audit.
- Raw frames and traces are in the scratch clone: `~/UnityScratch_depths/work/vfxaudit/`.

Not captured: the female hero, weather particle states, lava, the twister, the putt drop up close, the 7 new emotes in game, and the hub. The next pass should add them (the tools to change are listed in the standard).
