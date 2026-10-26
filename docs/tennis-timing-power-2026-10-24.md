# Tennis: timing = power, swing = direction — 2026-10-24

Ask (Adnan): players must be made to aim and time their shots. Timing decides how hard the ball is hit, where
you swing decides where it goes. It should feel as intuitive as golf, players should almost always hit the ball
(easy to pick up, hard to master), and the pace should reference Wii Sports Tennis.

**Nothing here has been played on a phone and TV yet.** Verified in Unity (EditMode suite + PlayMode sweep through
the real `TennisGame`), see "Verification".

## The rule

| | Before (10-10 feel pass) | Now |
|---|---|---|
| Side (left / straight / right) | swing **timing**: early left, late right | **where you swing**: racket face (phone) at contact. Square to the TV is straight (±8° band), about 30° turned is the corner. Touch: aim pad. Keyboard: arrows |
| Pace | string-bed centre (spacing) | **timing**: on the ball fastest, further off slower (`TennisRules.TimingPace`) |
| Depth | swing power | **timing**: clean lands deep (≈10.4 m), mistimed sits up short (≈6.2 m) |
| Swing effort | depth | a ±5% nudge only |
| Early swing | > 0.10 s early whiffed | up to ~0.3 s early: the player **holds the backswing** and lets go as the ball arrives; graded on the real (early) timing, so it is slow and short |
| Rally ball out | never | never (still clamped inside the lines) |

Why the face and not timing for direction: Wii Sports uses timing for direction, and the 10-10 pass copied it. The
playtest ask is the reverse, and it separates the two skills the way golf does (choose where, then execute).
The face reading is shaped in Unity (`SideFromSwing`: dead band 0.15, full at 0.75 of the phone's aim value), which
is much less twitchy than the pre-10-10 mapping the feel pass removed (~10 cm per degree).

Easy to pick up: a normal swing goes straight, nearly every swing connects, every rally ball lands in.
Hard to master: pace and depth only come from timing, and the corners are only near the lines on a clean hit.

## Wii Sports Tennis reference (measured)

No published numbers exist, so they were timed from gameplay video (audio onsets, checked against frame sheets):

| Clip | Level | Hit to hit |
|---|---|---|
| youtube `iWvsmX7nI2U` (0:09-0:16 rally) | casual | ~1.55-1.6 s (hit to bounce ~0.9 s) |
| youtube `LYK3xHGUqh8` (0:19-0:25, 0:52-0:56) | Pro | ~0.9-1.0 s (doubles net player volleys shorten it) |

Other Wii facts (community wikis): movement is automatic; timing picks direction; hitting the serve at the top of
the toss is a fastball. Ball speed in km/h is never shown.

## Our pace, before and after (hit to the other baseline's contact plane, real seconds, GameSpeed 1.1)

| Shot | Before | After |
|---|---|---|
| Player PERFECT | 0.87 s | 0.95 s (Wii Pro) |
| Player GOOD | ~0.85 s | 1.19 s |
| Player mistimed (≈0.3 s off) | ~1.0 s | 1.4-1.5 s (Wii casual) |
| CPU club | 0.94-1.05 s | ~1.25-1.4 s |
| CPU pro / boss | 0.77-0.94 s | ~0.95-1.2 s |
| CPU serve return | unchanged | unchanged (scaled, the moonballer's topspin returns ballooned over 3.3 m) |

CPU: `TennisOpponent.WiiPace` = 0.72 on every profile's rally pace (relative character and campaign balance kept),
floored at 14 m/s (`MinRallyPace`) so deep balls don't loop like lobs. Player: `SlowRallyPace / RallyPace /
FastRallyPace` = 11.5 / 14.5 / 20.5. The measurement test is in "Verification".

## Files

- `TennisRules.cs` — `SideFromSwing`, `TimingPace` (`ShotSpeed` now calls it), `SwingPlacement`, `SwingHold`,
  `EarlySwingHold`, `ContactQuality` (timing × small spacing/balance trims), frame-ring cap on real string contacts.
  Removed: `AimFromTiming`, `AimWindow`, `AimCentreBand`, `DepthFromPower`, `TimingPlacement`, `TimingAimWord`.
- `TennisActor.cs` — `HoldSwing`, `HeldTotal`; `TimeToContact` includes the hold; `PaceToContact` re-plans a hold.
- `TennisGame.cs` — `HoldEarlySwing` + `BallDueAtRacket` at swing start; lateness graded minus the hold;
  `SwingPlacement` with the aim locked at swing confirmation; `TimingAims` → `SwingAims`; aim ring for touch/keyboard.
- `NetworkTennisMatch.cs` — online uses the same rule; the far seat's aim is turned back into its own frame
  (`SportsMultiplayer.Submit` flips it into the host's).
- `TennisOpponent.cs` — `WiiPace`, `MinRallyPace`.
- Copy: `TennisTutorial.cs` (AIM LEFT now "swing toward the left"), `TennisCoach.cs`, `HowToCards.swift`,
  `docs/tennis-playtest.md`.
- Tests updated to the new rule: `TennisMatchTests`, `TennisSpatialContactTests`, `TennisTimingBalanceTests`,
  `TennisRallyBalanceTests`, `TennisRulesTests`, PlayMode `TennisTimingBalancePlayTests`.

## Verification

Unity 6000.3.24f1, batch mode, in an APFS clone (harnesses and CSVs in `work/tennis-timing-power/`).

PlayMode sweep through the real `TennisGame` (ball fed from 6 m, swing time stepped by 20 ms, aims −0.8/0/+0.8,
three ball sides, confirmed-swing and onset+confirm paths):

| | Before (10-13 audit) | Now |
|---|---|---|
| Swings that connect | −0.10 … +0.12 s | **−0.30 … +0.18 s**, same on the onset path |
| Rally balls in | all | all |
| Aim −0.8 / 0 / +0.8 → landing x | always the middle (±1 m) | −3.3 / +0.1 / +3.2 m mean (range −3.7…−2.1, −0.3…+0.5, +2.1…+3.7) |

| Grade | n | pace | hit to hit (real) | depth |
|---|---|---|---|---|
| OK | 124 | 13.6 | 1.39 s | 7.8 m |
| GOOD | 64 | 15.7 | 1.19 s | 9.9 m |
| GREAT | 40 | 18.1 | 1.03 s | 10.4 m |
| EXCELLENT | 28 | 20.6 | 0.97 s | 10.5 m |
| PERFECT | 40 | 20.5 | 0.95 s | 10.5 m |

Tests: EditMode 637/639 pass. The 2 failures are path tests that look for `../GolfArcade` and `../proof` and only fail
because the clone lives outside the repo. Tennis PlayMode, compared with a baseline clone without these changes:
nothing that passed there fails here. 15 tennis PlayMode tests already fail on the current tree (missing arms /
custom bodies, batch-mode `WaitForEndOfFrame`, the tutorial's lesson tests, a `HeroFaceReferenceFit` error log that
fails whichever test loads the scene first). They are not caused by this change and are not fixed by it.

Not run: Xcode build / Swift tests (only `HowToCards.swift` copy changed), netsim (`dotnet` is not installed here), device.

## Not done / for the device

- Face-angle mapping (±8° straight, ~30° corner) is a guess at comfort: check left/straight/right on a phone and
  tune `SwingAimDeadBand` / `SwingAimFull`.
- The retired aim-calibration lesson (`TennisAimLesson`) is not brought back; the default profile is used.
- Late side of the window is still physical (ball passes the body): about +0.18 s.
