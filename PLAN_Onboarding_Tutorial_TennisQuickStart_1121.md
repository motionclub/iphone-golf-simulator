# Onboarding tutorial + quick tennis start (2026-11-21)

Branch `onboarding-1121`, worktree `~/onboarding-1121`, cut from `11/20-combined` (b2f539a22) with the
uncommitted `local-setup-1120` tennis-setup work applied on top (patch kept at `~/onboarding-1121-base-local-setup-1120.patch`).
Nothing committed.

## Direction (user, 11-21)
- A short onboarding with menu guidance.
- Going to Play means doing the tutorial: golf (driving, a mid-hole shot, then putting, with emphasis on how sensitive
  putting is), then tennis (explain calibration, calibrate, serve, forehand, backhand), then bowling. After that, all games are open.
- A locked sport, when tapped, asks: play the tutorial or skip it.
- Starting a tennis match must be a lot quicker, with calibration still good.

## What the code does today (investigation 11-21)
- The intro has 7 tips: welcome, open the Locker, pick a look, 3 "how it works" pages, PLAY.
- The first lesson ends the guided part. Each sport then gates only on its own lesson (`needsLesson`). A gated sport goes
  straight to the "How to play X" card, with no skip, only "Not now".
- **Golf lesson:** two 115-yd par 3s with three stations (any swing, 60-yd distance drop, one 8-ft putt). There is no drive and no
  approach, and nothing says putting is sensitive (that text lives only in Settings how-to cards).
- **Tennis lesson:** court setup, then "Hit it back" (forehand + backhand in one step), then the serve. Nothing explains calibration.
  The how-to GIF never plays (`explaining = index == 0`, but tennis reports from index 1).
- **Tennis start:** 45–50 s minimum, 60–75 s realistic.
  - Flashes 9.8 s with no skip, drill 16.5 s, Ready tap, 6 s intro.
  - A saved timing value never shortens the flow.
  - Flash and drill results overwrite one key, and that key is often just "Speaker".
  - `receiveMatchFinish` calls `motion.stop()`, which defeats the rematch skip.
  - Pointing waits for loading to finish.
  - The lag learned during play is never kept.

## Design

### Onboarding (O)
- **O1, short intro (4 tips):** welcome ("swing your phone to play golf, tennis and bowling"), open the Locker, pick a look, PLAY.
  The "how it works" pages are cut. Safety is on the card before each lesson, and "tennis needs a TV" is on the tennis card.
- **O2, PLAY starts the tutorial.** The first PLAY shows a Tutorial card: golf · tennis · bowling, about 5 min, with Start and Not now.
  - Start runs golf. Each finished lesson shows "Golf done. Next: Tennis" with Next and Later. Next goes straight on;
    the last lesson shows "All sports unlocked".
  - Sports stay gated until their lesson is done or skipped.
- **O3, a gated sport asks:** "<Sport> starts with a short lesson (about 1 min)", with **Play the lesson**, **Skip lesson** and Not now.
  - Skip marks that sport skipped: open, no lesson reward. The menu then opens what was tapped.
  - The Tutorial row in Training can still replay any lesson.
- **O4, golf lesson** on one par 4 (two copies, so a holed shot moves to the second):
  1. **Drive:** from the tee. Pass if it carries 100 yd or more.
  2. **Approach:** from 100 yd out. Pass if the carry is within 12 yd of the pin, it stops within 10 yd, or it holes.
  3. **Putting is sensitive:** an explain card (TV and phone) says the putter moves only a few inches, and a full swing
     would send it off the green. Then a 6-ft putt that must be holed. Misses say "Softer, a smaller rock" or "A touch firmer".
  4. **Long putt:** 20 ft. Pass if it stops within 3 ft (or holes). This shows that a putt over three times longer
     needs only a slightly bigger stroke.
- **O5, tennis lesson:**
  - An explain card first: "Calibrate once. Your TV shows the picture a moment late, so we time it and remember it for this TV."
  - Then the full setup (point and hold, flashes, timing drill). This is the one place the drill always runs, and its result is saved.
  - Then **Serve** (land 1), **Forehand** (return 2), **Backhand** (return 2).
  - The motion sensors stay alive after the lesson, so the next match needs no setup.
- **O6, bowling:** the current 3 stations stay.
- **O7, a shared "explain" station field.** A station may carry `explain` {title, body}. The lesson HUD shows it as a card for 6 s,
  or until the first swing, on the TV and on the phone. It is used by golf putting, and the tennis calibration card uses the same view.
  The opening GIF shows on the first *reported* station, not index 0, which fixes the tennis GIF.

### Quick tennis start (T)
- **T1, keep the court direction between matches.** No `motion.stop()` at match finish when the direction is kept. The keep-alive
  covers Main Menu too, for 10 min instead of 90 s, and the lesson ends with the keep-alive.
- **T2, two stores and a real TV key.** Picture delay (flashes) and whole-chain timing (drill or learned in play) get separate keys.
  The key is the output route's `portType` + `uid` + `portName`, plus the external screen size.
- **T3, a known TV skips the flashes and drill.** With a stored whole-chain timing for this route, setup is just point and hold, then
  the match starts automatically.
  - "Recheck timing" stays in the pause menu and Settings.
  - A new TV runs the flashes with the get-ready cut from 1.5 to 0.8 s, then the drill with a 3 s countdown instead of 5 s.
    The drill ends early once 4 scored swings agree.
- **T4, point while it loads.** Point and hold works during loading, because it is motion only.
- **T5, no Ready tap.** The steering reset happens on its own when setup ends.
- **T6, keep the learned lag.** At match end the app saves the in-play learned lag as the whole-chain timing for this TV, so
  each match starts better calibrated than the last.
- **T7, shorter intro.** A rematch, or a match on a known TV, uses the short intro cut. A swing still skips it.
- **T8, safety card.** It is remembered per sport for 24 h, instead of coming back on every cold launch.

Target: a known TV goes from START to the first serve in load + about 2 s hold + short intro, about 12–15 s. A new TV takes about 30 s
(it was 45–50). A rematch takes load + under 1 s.

## Gates (binary)
- G1: the intro has 4 tips or fewer before PLAY (unit test on `coach(tv:)` sequence). PASS/FAIL
- G2: PLAY in `.goPlay` offers the tutorial card, and Start launches golf station 0 (unit test). PASS/FAIL
- G3: finishing golf offers tennis next, and finishing tennis offers bowling. Finishing all three leaves no gated sport (unit test). PASS/FAIL
- G4: a gated sport station offers lesson/skip. Skip opens it without a lesson and marks it skipped, not done. Play starts that lesson (unit test). PASS/FAIL
- G5: the golf lesson has stations drive, approach, putt (with explain), long putt, in that order. The pass rules match O4 (Unity EditMode). PASS/FAIL
- G6: the tennis lesson steps are serve, forehand, backhand. Forehand feeds go to the forehand and backhand feeds to the backhand (Unity EditMode). PASS/FAIL
- G7: with a stored whole-chain timing for the current route, setup after point and hold reaches `.playing` with no flashes,
  no drill and no Ready tap (unit test). PASS/FAIL
- G8: a match finish that keeps the direction leaves `hasUsableCourtDirection` true, and the next load skips setup (unit test). PASS/FAIL
- G9: flash and timing results land in different keys, and the route key includes `uid` (unit test). PASS/FAIL
- G10: everything compiles (iOS build for the simulator, and Unity batch compile). PASS/FAIL
- Device run: NOT possible from here. It is listed as open.

Proof: `proof/onboarding-1121/` (test logs, snapshot PNGs of the new cards). Results go in `proof/onboarding-1121/GATE_RESULTS.md`.
