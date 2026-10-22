# Experience-First Audit: Party Sports (Oct 14, 2026)
**Principle: an effect, animation or pause earns its place only if it makes the game more responsive, easier to read, or more rewarding.** This audit is ranked by how much each change improves the player's moment-to-moment experience.

Audit only: no project changes, nothing staged.

Evidence:
- Live captures in the scratch clone, foreground batchmode, in `~/UnityScratch_depths/work/vfxaudit/`:
  - Tennis resort, a full AutoPlay 3-point film at 30 fps, with `trace.csv` per 60 Hz tick.
  - Golf cliffside hole 12, strike to result, with `trace.csv`.
- Sheets in `ArtDir/style/vfx-anim-audit/`.
- Code reads in `Unity/Assets/Scripts`.

Benchmarks marked (≈) are typical values from play experience, not measured.

## The loop as it plays now (measured)
**Tennis (resort, AutoPlay):**
| Step | What happens | Measured |
|---|---|---|
| Point ends → reaction | Feedback text, sting, a full-body emote (Shock, Stomp) | PointOver to emote 0.8 s, emote about 1.4 s |
| Walk back | Hero walks to the baseline (`Male_Walk`) | **1.4–1.9 s** |
| Serve ready → toss | Player-driven (AutoPlay waited about 2.3 s) | n/a |
| Toss → serve contact → "SERVE IN" | toss, then the hit, then text | 0.58 s toss to text |
| Rally contact | Feedback text on the same tick as contact (16.00 → 16.02 s), impact FX on the contact frame | 1 frame |
| **Point end → first chance to serve again** | | **≈ 3.1 s every point** (7.33 → 10.47 s, 18.98 → 22.13 s) |
| Active ball time | 12.2 s of a 27.7 s film | **44% of the time the ball is live** |

**Golf (cliffside 12):**
| Step | Measured |
|---|---|
| Registered impact (film f62) → visible club-ball contact and strike burst | **≈ 8 frames = 0.27 s** (`G1_golf_strike_crop.jpg`) |
| Ball in the air | f62 → about f222 = **5.3 s** (apex 38 m at f153) |
| Ball rolling | f222 → f375 = **5.1 s**. The last 3 s covers about 7 yd at a crawl while the camera holds a static far view with the ball barely visible (`G2`: vf230–355 look identical) |
| Result card, locally | **3.0 s before it can be skipped** (`GolfGame.HoleOut.cs:92 LocalResultSeconds = 3f`, `GolfGame.Results.cs:29`) |
| **Strike → next aim** | **≈ 13.5 s or more per shot**. There is no fast-forward in flight (no skip found in `GolfGame.cs` for `State.Flight`) |

## Top 10 opportunities (ranked by player impact)

### 1. Golf: cut the dead time after the ball lands (biggest win)
- **What the player feels now:** after a great strike, about 5 s of watching a dot creep across a static view, then a 3 s card they can't skip. That's about 8 s of waiting per shot, or about 30 s per hole.
- **Evidence:** golf trace (roll f222–375, 7 yd in the last 3 s), `G2_golf_flight_land_result.jpg`, `GolfGame.HoleOut.cs:92`, `GolfGame.Results.cs:29,97`.
- **Change:**
  - When the ball lands, cut to a low chase cam near the ball for the roll.
  - Once ball speed drops under about 1 m/s, fast-forward 2–3× or snap to rest (the result is already known; the physics is deterministic).
  - Allow tapping the result card after 0.5 s locally. Multiplayer timing stays as is.
- **Why it's better:** Golf Clash and Mario Golf keep the camera on the ball while it rolls and resolve fast. Wii Sports Golf lets you skip almost everything (≈).
- **Success:**
  - On the phone, a shot feels like "hit, watch, next".
  - Median strike → next aim ≤ 8 s, measured in the film trace (now about 13.5 s).

### 2. Golf: visible contact must follow the swing immediately
- **What the player feels now:** the shot is registered while the hero is still at the top of the backswing. The club only reaches the ball about 0.27 s later, so the motion swing feels disconnected.
- **Evidence:** `G1_golf_strike_crop.jpg` (f0 to f+2 at the top, burst at f+8), `CurrentGolfSwingFilm` impactFrame = 62, `GolfGame.cs:2191-2219` (whoosh on the Downswing phase, strike later).
- **Change:**
  - Start the hero's downswing the moment the phone's downswing is detected, so the visible downswing is already moving at impact.
  - Line up the clip's contact frame with gameplay impact, as tennis already does with `contact` slots in `HeroTennisDriver`.
  - The strike sound and burst stay on the visible contact.
  - Check on device, because the film injects `StrikeToward`.
- **Why it's better:** the core of Wii Sports Golf is that the club follows your arm 1:1.
- **Success:**
  - On the phone, the hit lands when your arm does.
  - Visible contact within 3 frames (≤ 100 ms) of registered impact, from a 240 fps phone video or a trace.

### 3. Tennis: get back to serving faster
- **What the player feels now:** about 3.1 s after every point before you can serve again, mostly the hero walking back. Only 44% of the time is live play.
- **Evidence:** tennis trace (PointOver 7.33 → serve stance 10.47 s; Walk 9.53 → 10.35 s; 20.12 → 22.00 s), `TennisGame.cs:872` (`pointSkipAfter`), `HeroTennisDriver.cs:522` (`HoldNextPoint` for emotes).
- **Change:**
  - Overlap the reaction with the reset: the emote plays while the hero glides back.
  - Snap or fast-walk to the baseline, or allow the toss input during the walk and snap on toss.
  - Keep the full reaction only for big points (winner, ace, 8+ rally, game or set).
- **Why it's better:** Wii Sports Tennis and Mario Tennis get you to the next point in about 2 s (≈), which keeps the "one more point" loop tight.
- **Success:**
  - On the phone, you never wait to serve.
  - Point end → serve-ready ≤ 1.5 s on normal points; live-ball share ≥ 60% in the film.

### 4. Tennis: make shot quality readable at the ball, not in text
- **What the player feels now:** there are 6 timing grades (`TennisRules.cs:13`: Missed, Ok, Good, Great, Excellent, Perfect), but the at-ball visual only changes for Perfect and supercharge (`TennisFx.cs:166-170`). The rest is a text line ("PERFECT! · forehand · SWEET SPOT · 110 km/h"), which you can't read mid-rally.
- **Evidence:** `T2_tennis_contact_crop.jpg`, `TennisFx.cs:145-172`, the feedback string in the trace.
- **Change:** 3 clearly different tiers at the contact point:
  - Ok/Good: a small dull puff and a soft "pok".
  - Great/Excellent: a white flash and a crisper "thwack".
  - Perfect: a gold star, a pitch-up chime, and a gold ball trail for the shot.
  
  The ball trail color carries the grade while the ball travels, which is where the eye already is. Shrink the text to one word.
- **Why it's better:** Mario Tennis uses a distinct sound and flash per shot quality, and Wii Sports uses the pitch of the hit (≈). Players learn timing by ear and eye, not by reading.
- **Success:**
  - Feel test: friends can call "good / great / perfect" without the text, ≥ 80% right.
  - Each tier has a distinct sound and color in the code.

### 5. Tell the player WHY a shot went wrong
- **What the player feels now:** "MISSED IT" or "OUT", but not whether they were early or late, or hit off-center.
- **Evidence:** the game already computes `hitLateness` and `faceOffset` (`TennisGame.cs:2045`, passed to haptics only). Golf has `Timing`, `Center`, `ErrorDegrees` (`TennisRules.cs:8`), and the golf shot rating shows only as a color.
- **Change:**
  - Tennis: a tiny EARLY ◀ or ▶ LATE tick on the timing ring for 0.6 s after any shot below Great.
  - Golf: one word on the result ("Late, pushed right" or "Thin, low"), and the shot-quality trail colors per the standard (gold, white, grey-blue). Red is reserved for hazards.
- **Why it's better:** Golf Clash's perfect-shot ring and Mario Golf's impact meter teach you instantly. A party game needs new players to improve within 3 shots.
- **Success:**
  - New players improve their average grade between their first and fifth rally.
  - Players can say why a shot missed.

### 6. Near misses and putt drops: pay off the emotion
- **What the player feels now:**
  - Holing out hides the ball and plays sounds (`GolfGame.cs:2897-2905`, `ball.SetActive(false)`), with nothing at the cup.
  - A lip-out gets a text and a groan (`GolfGame.cs:2676, 2976`).
  - "So close!" at under 4 ft gets text only.
- **Evidence:** code lines above; `G2` result frames.
- **Change:**
  - Hold the camera on the cup for the drop with a rattle sound, a flag wobble and a small bible-palette burst. Show the score after.
  - Lip-out: an instant 1.5 s slow replay of the lip plus a big "NOOO" crowd and hero reaction. Near misses are the funniest moments in a party game.
  - Scale the payoff to rarity: tap-in small < long putt < chip-in < hole-in-one. A hole-in-one already gets 4 s (`PresentationDirector.cs:59`).
- **Why it's better:** in Golf Clash and Mario Golf, lip-outs and long putts are the shareable moments. Wii Sports' crowd "ooooh" on near misses (≈).
- **Success:**
  - Friends react out loud.
  - Every lip-out shows its replay within 0.3 s.
  - Drop moment ≤ 0.2 s after the ball reaches the cup.

### 7. No full-body celebration while the ball is live
- **What the player feels now:** after a perfect hit, the hero stands and fist-pumps for about 0.75 s while the opponent returns the ball (trace 16.52–17.25 s, playerX frozen at 0.00). It looks like you're not ready, and it hides the real stance.
- **Evidence:** trace rows 16.4–17.3 s, `HeroTennisDriver.cs:632` (HitPerfect juice mid-rally), `:657` (it only cancels once moving > .9).
- **Change:** while the ball is live, show perfect-hit pride as an upper-body or face-only beat (a quick fist, a smile) that never stops the ready stance. Save the full-body emote for point end.
- **Why it's better:** Wii Sports and Mario Tennis characters always return to ready immediately. Readiness is part of how you read the rally.
- **Success:**
  - The hero always looks ready.
  - Zero full-body emote ticks during `Phase.Rally` in the trace.

### 8. Make wind and weather change decisions, visibly
- **What the player feels now:** wind exists in the physics and as a global sway (`GolfWindSway.cs:92` `_GolfWind`). The environment audit found Gusty looks the same as Clear, and rain is just grey. Weather doesn't visibly ask you to play differently.
- **Evidence:** `ArtDir/environment/targets-2026-10-14/sheets/13_golf_gusty.jpg`, `15_golf_weather_all_states_current.jpg`, `WeatherView.cs`.
- **Change:**
  - Wind gets a strong world read: flags, leaf streams across the fairway, and the ball's flight visibly drifting. Keep the HUD arrow with numbers. Rain shortens roll, and a wet green gets a splash on landing so you can see why the ball stopped.
  - Per Adnan's earlier direction, no aim guide line; the read comes from the world.
- **Why it's better:** in Golf Clash, wind is the skill. Reading it is the game.
- **Success:**
  - Players adjust their aim on gusty holes (aim offset vs wind, from the trace).
  - Feel test: "I could see the wind."

### 9. Make long rallies and streaks feel like they're building
- **What the player feels now:** there's lots of hype logic (crowd at 5+, music and announcer at 8+, `TennisAudioDirector.cs:63-100`, `TennisGame.cs:853-937`), but the rally count only appears as text *after* the point ("N-SHOT RALLY"). There's no build-up you can see while playing, and nothing for comebacks or match-point tension.
- **Change:**
  - A small live rally counter that pops at 4, 8 and 12, with the crowd swelling as it climbs (sound first).
  - "MATCH POINT" and "BREAK POINT" banners with a quieter crowd before the serve.
  - A comeback line from the announcer when the scores level.
- **Why it's better:** Wii Sports Tennis rallies get louder as they go (≈). Tension before big points is what friends remember.
- **Success:**
  - Rallies past 8 shots get cheers in the room.
  - The counter is visible from shot 4.

### 10. Make failures funny, not flat
- **What the player feels now:**
  - Water: a splash and a gasp.
  - Out of bounds: a groan and "+1".
  - Tennis: "MISSED IT", or a Stomp or Slump at point end.
  - No announcer audio exists yet (the audio plan has 42 lines, with no files).
- **Evidence:** `GolfGame.cs:2352-2354, 2682-2683`, `GolfGame.cs:2907-2908`, `TennisGame.cs` feedback strings, `/workspace/audio/AUDIO_PLAN.md`.
- **Change:**
  - Short comic beats tied to the failure: the ball skips once on the water before sinking, a duck quacks, the announcer gets a sarcastic line, and the hero does a quick comedic reaction.
  - Each lasts ≤ 1.5 s and is skippable, so it never adds dead time (see #1 and #3).
- **Why it's better:** party games such as Wii Sports, Mario Party and Golf With Your Friends make losing entertaining, so the losing player stays happy.
- **Success:**
  - The losing player laughs.
  - Failure beats ≤ 1.5 s.

## Pace summary
- Tennis: about 9 s per point now, of which 3.1 s is reset. Target about 7 s, with reset ≤ 1.5 s.
- Golf: about 13.5 s per shot now. Target about 8 s. A 4-shot hole drops from about 55 s to about 32 s, plus its intro.

## Dropped from the earlier VFX audit (per Adnan)
- The Scuba racket drop, no camera shake and no hit-stop are intentional. The particle-budget point is removed as not relevant to the experience.
