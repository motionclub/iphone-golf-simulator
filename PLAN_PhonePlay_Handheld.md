# PLAN — Handheld play (phone-only golf + bowling)

2026-10-28. Approved mock: https://claude.ai/artifact/39jeVfT34vDA59xj7zbPRE.
This replaces the "landscape game view ⇄ portrait controller" loop of `PLAN_PhonePlay_NoTV_GolfBowling.md` §1–2 for phones with no TV.

## Rule
- A phone with **no TV of its own** plays **golf or bowling** handheld. This covers solo, pass-the-phone, a party's host, and a party's guest, whether or not anyone else in the party has a TV.
- A phone with a TV plays as before: the game on the TV and the controller on the phone.
- Tennis still needs a TV.

## Layout (the Game Boy split)
- **Top 75 %: the game.** Unity's gameplay camera `rect = (0, .25, 1, .75)`. The HUDs bound to that camera fit inside it (GolfShotHud, ShotResultPanel, HoleOutCard, BowlingHud). The legacy golf `Hud` overlay keeps above the deck (`Hud.ReservedBottom`).
- **Bottom 25 %: the deck** (`HandheldFrame.swift`, opaque, `SportsSession.handheldDeck` = Unity `NativeSportsSession.HandheldDeck` = 0.25).
  - Golf: club card + arrows (left), aim pad + aim reading (middle), TAP TO SWING / READY (right), pause.
  - Bowling: where to stand (lane strip + chevrons), the ball (hold, swing, let go), last throw (mph + grade), pause.
- **Golf map:** Unity's HUD drops its own map and club card (`GolfShotHud.Handheld`). The app draws the hole map in the game view's lower right corner, and a tap opens it full screen with par/yards/wind (BACK TO SHOT closes it; it also closes when the shot is struck). The map picture is 512 px wide in handheld play.
- Result, round-end and party-turn cards sit at the foot of the game view. Skip-intro, intro emotes and tips are lifted above the deck. No feedback bar and no top bar.

## Code
- Swift:
  - `SportsSession.start` sets `phoneGame` for golf+bowling with no TV and sends `phonePlay`. The runtime lends its view to the phone window (`controllerReplica || phonePlay`). Unity's own controller sheet never comes forward in handheld play.
  - `TennisMenu.begin` / pass-the-phone no longer ask for a TV for golf/bowling (`Sport.playsOnPhone`).
  - `GolfController` handheld layout, `BowlingController` handheld deck, `SportsHome` lifts/hides.
- Unity:
  - `NativeSportsSession.Handheld.cs` (`phonePlay` → `handheld`): camera rect/aspect, portrait orientation, `GolfGuestController` off (a guest's own camera draws), statics reset on `end`.
- Fix on the way: phone-only bowling loaded Unity with `controllerReplica:false`, which the native loader refuses away from a TV ("Connect an external TV…").

## Gates
See `work/handheld-1028/GATE_RESULTS.md`.
