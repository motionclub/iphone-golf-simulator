# Playtest fixes — 2026-11-21

Source: Adnan's playtest notes (11-21). Audit = read-only code read of `~/local-setup-1120` (newest code, branch `local-setup-1120`). Nothing changed yet. Paths are relative to that tree; `S/` = `Unity/Assets/Scripts/`.

## Root causes (one line each, verified)

| Note | Cause |
|---|---|
| Golf "falls super short" | `S/Shot/GolfClub.cs:97 ForDistance` picks the shortest club that reaches **at full power**; a relaxed swing reads ~0.6–0.7 power (`S/Swing/MotionSwingDetector.cs:105`, 100% ≈ 149° phone turn), so every relaxed shot lands ~30% short. Forced carries (Needle tee, Temple Falls tee, Crater approach, Island 12) go in the water/lava. Per-player swing calibration exists (`MotionSwingDetector.cs:86`) but nothing calls it. 80% of holes have 5–20 mph wind at ~1.2%/mph. |
| Golf stale / needs par 2–3 | 16 holes: 4 par 3, 8 par 4 (~390 yd avg), 4 par 5, 0 par 2. At a relaxed swing par 4 = 3 shots to the green, par 5 = 4; bogey is normal, birdies rare. XP only at the end of a finished **solo** round. |
| "Completing a game feels impossible" | Golf solo/same-phone has **no stroke cap** (online stops at par+5). Golf 9/18 run on into other courses (~14/28 min solo, ~55/110 min for 4). Wild Isles unlock needs **par or better** on Cliffside (`S/Profile/Unlocks.cs:38`). Tennis campaign rounds 6–10 are best-of-3/5 full sets (45–75 min); online tennis forced to 1 set. Bowling always 10 frames (~4 min solo, 16–20 min for 4). No save/resume — a jetsam kill (tennis ~3.2 GB of ~3.4 GB) loses the match. Host away 180 s ends online games for everyone. |
| Onboarding a hassle | First golf shot ≈ 16 taps / 3–4 min after install (8 intro-tip taps, safety card, forced lesson, unlock card, menus, flyover). Safety card (`GolfArcade/Onboarding/PlaySafe.swift:24`) is **in-memory only** → returns on every cold launch for every sport. |
| Tennis setup a hassle | START → first serve ≈ 8 taps + hold + ~10 s flashes + ~17 s timing drill + 6 s intro (60–75 s). Repeats **every match** unless Rematch within 90 s; Main Menu forgets it; the tennis lesson *is* the setup and doesn't keep the result, so a new player does full setup twice in minutes. |
| Bowling random / no skill | Speed is nearly flat (`S/Bowling/BowlingSwingDetector.cs:194`: lazy 16.5 mph → hard 21.1). Any non-Perfect release adds 5–14 boards of random scatter vs a ~±2-board pocket. The "let go" buzz fires after the arm's bottom → likely grades Late. Unintended wrist roll → unplanned hook; speed silently changes hook ~10 boards. Pin carry tuned at one speed; fast balls don't help (flatter entry). Phone shows only mph + grade; hook/rpm received but never shown. |
| Bowling atmosphere | No bowling music (fallback `game_light` at 0.22; **Magma silent**), no announcer, recycled tennis/golf crowd. 12–15 s dead time per ball, 75–90 s wait between turns for 4 players. No high score, no ball choice, no unlocks. |
| Retention weak | Levels unlock nothing (`Progression.swift:4` "reward list is empty"). No daily challenge for tennis/bowling, no achievements, no quests, no quick modes. Rematch is 4 taps away. |

## Direction from Adnan (11-21, second message): replaces the first plan below

1. **Golf ball physics:** balls don't roll enough, bounces are wrong, and some shots bounce and soar into the sky (bug). Find the sky-launch bug with a repro first. Background: gameplay-audit-1111 found rebound 0.30-0.46 on every full shot, no descent-angle term, a flat y=0 bounce, and the 10-28 "livelier turf".
2. **Power must be easy to gauge** while swinging. Pairs with the club-choice fix (a relaxed swing is about 0.6-0.7 power).
3. **Remove some golf maps** (golf only). DONE 11-21 on branch `playtest-1121` (uncommitted): Adnan picked hole 7 "Cliffside" and hole 13 "The Spiral". Both are retired from the courses; their data is kept. Cliffside is now 4 holes, par 15; Wild Isles 5 holes, par 20. Stills: `work/map-stills-1121/golf_after_14_holes.jpg`.
4. **Save/resume for local play.**
5. **Swiping out of the app must not kill it.** Suspects: jetsam from the ~3.2 GB footprint, or a background-snapshot crash. Needs a device repro and crash logs.
6. **Onboarding:** keep everything before the tutorial (the intro tips). Replace the forced per-sport lessons with **one combined tutorial that plays between games** and **can be opted out of**.
7. **Tennis setup:** already fixed in local-setup-1120. No work.
8. **Bowling mechanics:** like real bowling, simple input with a huge skill gap. Speed and spin must clearly matter, with less hidden randomness.
9. **Bowling atmosphere:** audio (music, announcer, real crowd), and venues that look way cooler.
10. **Replayability (main goal).** Research DONE 11-21: `work/replayability-1121/REPLAYABILITY.md`. Build order R1–R7: rounds measured in minutes plus one-swing Play Again; same motion gives the same result; a Skill Level that moves after every game; readable power/spin; scored drills; built for the room; a daily reason. Original note: find out why Wii Sports kept people playing round after round, then apply it. XP and progression come later.

Still valid from the first plan: golf club choice for relaxed swings, an offline stroke cap, short formats, the Wild Isles unlock, and par 2/3 holes.

## First plan (11-21, before Adnan's direction)

### Phase 1 — "a game you can finish in 5 minutes" (small code, biggest win)
1. **Golf club choice for real swings.** `ForDistance` targets ~75% power (or the player's calibrated comfortable swing; wire up `MotionSwingDetector` calibration from the lesson's first swings). Gate: relaxed 0.7 swing carries every forced hazard on all 16 holes (sim sweep).
2. **Golf stroke cap offline = par+3** (pick up, score "X"), matching online's idea. Gate: no hole can exceed cap.
3. **Short formats everywhere:** golf "3 holes" (default) / course / 9; tennis "1 game"/"3 games" default, campaign rounds max 1 set; bowling "5 frames" (Wii-style quick) / 10. Online tennis default 3 games.
4. **Unlock Wild Isles on finishing Cliffside** (not par).
5. **Persist the safety card** (UserDefaults, per sport, once ever).
6. **Remember tennis setup** across matches/menu (keep court direction + timing offset; re-run only on "Recalibrate" or a TV/route change). Tennis lesson writes the result so setup runs once.

### Phase 2 — golf holes + quick reward
7. **Par 2/3 content:** add 4–6 short holes (60–150 yd, one feature each) and a "Short Course" playlist of par 3s; mix ≥2 par 3s into every course. Shorten the longest par 4s ~10–15%.
8. **Wind bands calmer by default** (most holes 0–9 mph; 15–20 only on "windy" days).
9. **Per-hole reward:** XP/coins pop on each hole (birdie/par/closest-to-pin), not only at round end; pay XP for partial rounds.

### Phase 3 — bowling skill
10. **Speed matters:** widen speed range (e.g. 13–24 mph) and give carry a speed/entry sweet spot; a fast pocket hit should strike more.
11. **Deterministic, readable release:** shrink Good/Early/Late scatter (e.g. 0.15/0.5/0.45°), move the buzz to the true bottom, deadzone accidental wrist roll (hook only from an intentional twist, e.g. >20°).
12. **Show the throw:** phone + TV show speed, hook, board at the arrows/pins, pocket/entry angle; aim line stays visible as a ghost after release.

### Phase 4 — bowling atmosphere + session flow
13. Bowling music per venue (Magma included), announcer stingers for strike/spare/turkey, bowling-specific crowd.
14. Cut dead time: sweep 1.5→0.8 s, auto-skip walk back, next bowler steps up during the sweep → target ≤8 s per ball.
15. Personal best per lane, ball picker (look only), turkey/clean-game badges.

### Phase 5 — retention
16. Level rewards (colours, balls, caps from the existing locker items) every level 2–20.
17. Daily challenge for each sport (tennis: win a 1-game match; bowling: spare challenge) + 3 daily quests.
18. One-tap **Play again** on the post-game screen (default focus), and save/resume for solo golf/bowling between holes/frames.

## Open questions for Adnan
- "Maps fall super short" = shots land short (fixed by 1) **or** some maps feel underwhelming? If the latter, which ones.
- "Unless the game is in the background" — does a game die when the app goes to the background (jetsam), or do sessions only last when it's played casually in the background of a hangout?
