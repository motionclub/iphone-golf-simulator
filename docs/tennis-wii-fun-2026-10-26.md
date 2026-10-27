# Tennis: Wii Sports rules, aim by swing lanes (2026-10-26)

Adnan: "everytime i make contact, the computer misses, and also half the time i make a good swing it misses ... easy
contact, and quality of contact depending on timing and aim ... steal all of [Wii Sports'] gameplay principles except
when it comes to aim, i want direction of where you swing the racket to aim ... FUN IS ALL THAT MATTERS". He picked
three snapped lanes for aim.

**Nothing here has been played on a phone and TV yet.** Verified in Unity (EditMode + PlayMode self-play through the
real `TennisGame`), see "Verification".

## Why it felt bad (root causes, before this change)

- **Your swing had about six separate tests to pass.** Failing any one was a whiff:
  1. The phone wrote the swing off as a step.
  2. Confirmation took longer than 0.14 s.
  3. The character was limited by its legs and didn't get to the ball.
  4. The animated strings were more than 22 cm from the ball ("honest contact").
  5. The swing was outside the timing window.
  6. The TV-delay guess was off.
- **The CPU also had the honest-contact test** (26 cm, "RIVAL WHIFFED IT"). In the real game its animated racket is
  further than that on about 80% of its shots (self-play: 331 of about 400 at its original speed). Every one of those
  was a free point for the player, which is why the computer "missed" almost everything.
- **The CPU had coin-flip errors.** Every ball, easy or not, carried a 4-7% unforced error chance. On top of that, its
  miss chance grew with how cleanly the player hit, so a clean ball down the middle could win the point.
- **Serves faulted** on off-peak timing, a loose toss, or the strings missing the toss.

## The rules now

| | Before | Now |
|---|---|---|
| Contact | the visible strings had to be within 22 cm, or it was a whiff | a swing in the window always hits; the ball is put on the strings (the gap is counted in `HonestMisses` for animation tuning) |
| Phone confirmation | 0.14 s grace | 0.2 s |
| Getting to the ball | limited legs (about 79% reachable without a lean) | always gets there: a ball the sprint can't reach gets a dash (`TennisRules.DashSpeed` 11 m/s, no reading pause, no stamina slowdown) |
| Aim | racket face, smooth (dead band 0.15, corner at 0.75) | three lanes: \|aim\| ≤ 0.3 straight, beyond it left / right |
| Side lane on a clean hit | deep corner (x 3.67, z 10.4) | an angle: x 3.95, z 8 (keeps travelling wide). Straight still goes deep |
| CPU contact | "RIVAL WHIFFED IT" if its strings were more than 26 cm away | a ball it decided to play is played |
| CPU errors | forced + flat unforced 4-7% on every ball; clean hits weighed 0.3 | forced only (quality weighs 0.12); no unforced errors before 10 shots, then "worn down" +1.2%/shot to 12% (Wii's rivals tire) |
| CPU legs in a rally | profile speed and reaction | 0.9× speed, +0.04 s read (`TennisOpponent.RallyLegs`, `RallyReadDelay`); serve returns unchanged |
| Club rival threshold | 0.25 | 0.3 (it shanked perfect balls at the body) |
| Serve | faults for far-off timing, loose toss and string gap | a struck serve goes in; timing sets the pace (rocket at the top), a loose toss wanders inside the box |
| Rally ball out | never | a swing more than `TennisRules.OutTiming` (0.17 s) off the ball sails out: wide of the sideline on a side lane, long down the middle (Wii: "too early or too late ... out of bounds"). GOOD or better (≤ 0.14 s) always lands in. Overheads and dives excepted. Online versus uses the same rule (`NetworkTennisMatch.Return`) |

## Files

- `TennisRules.cs`: `OutTiming`, `MistimedOut`, `MistimedLanding`, `SideFromSwing` (lanes), `SwingPlacement` (`SideLaneWidth`/`SideLaneDepth`), `JudgeServeStrike`
  (always legal, in the box), `DashSpeed`.
- `TennisOpponent.cs`: `Fatigue`, `QualityBite`, `RallyLegs`/`RallyReadDelay`, no unforced error term, serve-return spin cap.
- `TennisOpponentProfile.cs`: Club `Threshold` 0.3.
- `TennisGame.cs`: no honest-contact rejection (rally, serve, rival), `ConfirmGrace` 0.2, `AutoReachEverything` dash,
  rally legs, fatigue passed to the rival. `honestRejected` removed (also from `TennisAbilities.cs`, `TennisOverheads.cs`).
- `NetworkTennisMatch.cs`: the same out rule online.
- `TennisOverheads.cs`: a queued smash whose lob came down short plays as a groundstroke instead of being dropped.
- Copy: `HowToCards.swift` (serve, "Just swing", "Work the corners"), `TennisTutorial.cs` (lanes).
- Tests:
  - New `TennisFunTests`.
  - Updated `TennisMatchTests` (lanes, serves in, comfortable balls) and `TennisGameplayImprovementTests` (toss wander, stays in).

## Verification

Unity 6000.3.24f1, batch mode, in an APFS clone. The harness and results are in `work/tennis-fun-1026/` (main checkout).

- **EditMode, every tennis test:** 181 of 182 pass. The one failure is `TennisLatencyTests.ProvenThresholds…`, which
  reads `../GolfArcade/…SteeringFilter.swift` and fails only because the clone has no `GolfArcade` beside it.
- **New `TennisFunTests`:**
  - Aim takes only three values.
  - On a comfortable ball (stretch ≤ .35, pace ≤ .3, any quality, any roll), every rival on the ladder never errs.
  - A long rally wears the rival down.
  - A mistimed ball (0.25 s off) never wins a point.
  - A ball down the middle never wins one.
  - A clean angle beats a centred club rival 63% of the time.
  - The ladder gets harder: club 63% > standard 8% > pro 0% = boss 0%.
  - These figures come from the pure model, with the rival starting each ball in the middle. The real game is below.
- **PlayMode, through the real `TennisGame`** (`ZTennisFunPlay`, standard rival):

| Run | Points | Player won | Mean rally | Player whiffs | How points ended |
|---|---|---|---|---|---|
| Wide balls, every in-court feed | 87 | 87 returned | | **0** | |
| Self-play, sharp timing | 100 | 100 | 9.5 | **0** | 60 winners past the rival, 40 rival errors (19 out, 21 net) |
| Self-play, casual (8% of balls missed) | 100 | 76 | 6.8 | **0** | 41 winners, 35 rival errors, 24 player misses |
| With the out rule: sharp / casual | 100 / 100 | 100 / 71 | 10.4 / 7.5 | **0** / **0** | |
| With the out rule: sloppy (timing σ 0.12 s, its own driver) | 100 | 70 | 9.4 | 1 (outside the window) | 40 winners, 29 rival errors, **27 player shots out**, 2 misses |

  - No "RIVAL WHIFFED IT" in any run.
  - Of the rival's contacts, 370 of about 470 (sharp) had its strings more than 26 cm from the ball. Under the old rule
    each of those was a free point; now the ball is put on the strings.
  - At the old full legs, the same measure was 331 of about 400.
- **Rival legs sweep** (60 points each, sharp bot, before the lob fix in the bot):

| Legs / read delay | Player won | Mean rally | Winners |
|---|---|---|---|
| 1.0 / 0 | 36* | 13.2 | 3 |
| .9 / .04 | 55 | 7.2 | 32 |
| .85 / .06 | 49 | 6.5 | 38 |
| .8 / .08 | 54 | 5.0 | 46 |
| .75 / .1 | 57 | 4.5 | 52 |

  (*every lost point was a lob the bot never swung at.) We picked .9 / .04.
- **The overhead bug this turned up:** a swing made early at a lob that then bounced short was queued as a smash and
  silently dropped, and the ball went by. It now plays as a groundstroke (`FireQueuedOverhead`). In the wide-ball feed,
  misses went from 4 to 0. `ReachableLobsKeepTheirOverheadContact` and `TennisAbilitiesPlayTests` pass.
- **Out rule tests:**
  - New `TennisFunTests.BadlyTimedShotsGoOut` passes.
  - `TennisSpatialContactPlayTests` now checks ±0.14 s (in, aimed side) and ±0.24 s (out, wide on the aimed side), and passes.
  - The online `TennisTimingBalanceTests` checks a way-off swing goes out long or wide.
  - EditMode: 182 of 183 pass (the same clone-path failure as before).
- **Not run:** Xcode / Swift tests (only `HowToCards.swift` copy changed), netsim, and the device.

## Not done / for the device

- **Play it on a phone and TV.** The self-play bot is a near-perfect player; how often a real person misses the
  window with TV lag sets how often the CPU wins points.
- **The CPU's animation drift is now visible as a short ball snap.** Its strings miss the ball by more than 26 cm on
  most shots. The fix is in the rival's contact guidance (`PlanContact`, `GuideContact`, positioning beside the
  ball), not in the rules.
- **Player errors (added on Adnan's OK):** badly timed shots now go out, so the CPU wins points from your mistakes too.
  A person's timing scatter on a TV is unknown: tune `OutTiming` after a device session.
- **Online versus** uses `SideFromSwing` (lanes) and the serve rule; its contact and whiff rules weren't changed.

## Second pass, same day: quiet grade, hang time, replays (Adnan)

> "a less emphasized hit grading maybe in the bottom corner, as well as a bit more hang time on tennis balls. yes to replays
> after long rallies and aces" · "also making sure sound is on time, and haptics are on time and not delayed"

- **Quiet grade in the corner.** In a match the TV showed no hit grade at all (score-only HUD), and the phone's big
  "PERFECT!" pop-up (`TennisPlayViews.swift` `LastHit`) is never used. The lower-left feedback panel now shows in matches
  too, at 70% opacity (`TennisHud.MatchGradeAlpha`), for 1.8 s. It reads the grade, then timing · lane · stroke · speed,
  for example "GREAT / EARLY · RIGHT · BACKHAND · 59 km/h".
- **Hang time.** Flight time is set almost entirely by pace: the arc solver already lofts slow balls (measured: net clearance
  changes only the fastest balls).
  - Player paces 11.5 / 14.5 / 20.5 → **10 / 13 / 17.5 m/s**, and clean-shot net clearance 0.7 → 1.1 m.
  - CPU `WiiPace` 0.72 → 0.66, `MinRallyPace` 14 → 13, clearance 0.45 → 0.9.
  - A clean hit now takes about 1.1 s hit to hit (was 0.95 s). A clean strike stays at least 1.4× faster than a mistimed
    one: the pace tests pass unchanged.
  - Slower balls gave the rival time to reach everything (self-play rallies of 25 shots). Rally legs were re-swept:
    `RallyLegs` 0.9 → **0.76**, `RallyReadDelay` 0.04 → 0.085.
- **Replays.** After an ace, a rally of 8+ shots (whoever won it) or the match point: never two in a row, a swing skips
  one, and not in versus or online play.
  - The recorder used to capture in `TennisGame.Update`, before the heroes were posed (`HeroTennisDriver`, order 1000). In
    playback the driver re-posed them over the replay, which is why replays were off.
  - `TennisReplay` now captures and applies in its own LateUpdate at order 31000, with the camera applied there too.
- **Sound and haptic timing.** Audit only, no change: the timing chain is the 10-24 latency work.
  - The strike haptic waits for the phone's own swing peak (`GolfHaptics_HitOnSwing` / `SwingContact`), so it lands with
    the arm rather than with the TV picture.
  - The phone-speaker knock plays with it (on by default). The haptic engine is kept running (no auto-shutdown,
    haptics-only for the lowest start latency). The DSP buffer is 512.
  - The TV's own audio is in sync with the TV picture, so both are behind the arm by the AirPlay delay. That can't be
    removed; the phone haptic and knock are the on-time channel.
  - The phone build from 10-22 predates all of this: it needs a new build, then a device check.

| Check (real `TennisGame`) | Result |
|---|---|
| Self-play sharp / casual / sloppy | won 100 / 74 / 67 %, mean rally 9.4 / 7.9 / 8.8, player whiffs 0 / 0 / 2 (sloppy swings outside the window) |
| Wide balls | 86 / 86 returned, 0 whiffs |
| Replay pose (hero hand vs recording, every playback frame) | PASS: worst 0.0 cm over 306 frames; 2 of 460 transforms drift (forearms of the "Permanent male tennis player" rig, re-solved by the arm refresh, up to 20 cm), not visible in the near-camera frames (results/pass2/replay_near_*.png) |
| EditMode tennis | 182 / 183 (the clone-path test only) |
