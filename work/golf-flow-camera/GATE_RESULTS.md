# GATE_RESULTS — chat A golf flow + broadcast camera (2026-10-19, cliffside h1, phone flow in Unity clone, proof/ + traces)
- GATE FIRST_DRIVE_FACING: PASS — model yaw stays at the swing stance (−90°) from flyover cut to contact (after3 trace); before: Idle +90° side-on through the address beat (before_firstdrive #156/#165).
- GATE NO_CHARACTER_INTRO: PASS — beats go 0 → 2 (flyover → address cut), no "ON THE TEE" plate, no intro emote window (after3 trace, after_firstdrive).
- GATE NO_OBSTACLE_TAGS: PASS — flyover shows the hole plate only, no hazard tags (after_firstdrive #60/#85 vs before #80).
- GATE NO_EMOTE_AFTER_HIT: PASS — non-holed results: no Idle/emote performed, panel shows no emote buttons, PlayResultEmote refuses; hole-out reaction still plays (Emote_FistPump in trace).
- GATE BROADCAST_FULL_SHOT: PASS — hold behind golfer (tilt up) → cut to follow → cut to static landing camera → post-shot hold on the ball (after_drive_final). Landing framing is my reading, rough-flower foreground still busy.
- GATE PUTT_FADE_NO_FOLLOW: PASS — camera position identical from putt address to result; golfer opacity 1→0 in 0.45 s from 0.3 s after contact; post-putt holds on the ball (after_putts, after_drive_final #308–322).
- GATE HOLEOUT_FROM_BEHIND: PASS — holed putt: same camera, golfer fades back in (0.35 s), faces the cup and reacts back-to-camera (after_putts #408–#445).
- NOT RUN: device/phone build, online 2-phone, chip-in/ace hole-out capture, PlayMode/EditMode suites (GolfPresentationTests, GolfBroadcastTests, IntroRulesPlayTests, HoleFlowTests, GolfAnimationFlowTests, PresentationFilmTests assert the old intro/result framing).
