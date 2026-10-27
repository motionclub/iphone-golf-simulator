# PLAN — Phone Play: golf + bowling with no TV

2026-10-25, rev 2 (Adnan's answers folded in).

**Rules**
- **Golf and bowling never need a TV.** A TV is optional: when one is connected it shows the game, as today.
- **Tennis is not part of this.** It can only be played with an external display, and nothing about it changes.
- **Every player uses their own display**: their phone's screen, or their own TV if they have one. This holds solo, pass-the-phone, and with several phones locally or online.

## 1. The loop

```
 ┌──────── GAME VIEW (landscape) ───────┐        ┌─ CONTROLLER (portrait) ─┐
 │  course / lane, HUD, intro, flight,  │  tap   │  golf: today's sheet    │
 │  result, replay, other players       │ Ready  │  bowling: board + ball  │
 │                          [ Ready ]   │ ─────► │                         │
 │ [II]                                 │        │                         │
 └──────────────────────────────────────┘ ◄───── └─────────────────────────┘
        shot detected (golf impact / bowling release) → back to the game view
```

1. **Game view.** The round plays full screen on the phone, sideways. A small **Ready** button sits bottom-right (thumb reach) and Pause sits top-left. Ready shows only when it is this phone's player's shot.
2. **Ready → controller.** The phone shows the controller exactly as it does when a TV is connected.
3. **Swing / bowl → game view.** As soon as the shot is read, the phone goes back to the game view and the camera follows the ball. Golf switches on `Aim → Flight`, bowling on `Approach → Rolling`.
4. **Next turn:** repeat. Shot result / Next Hole / bowling frame cards are small overlays on the game view. A **View** button on the controller goes back to the game view without swinging.

## 2. How it works

### With a TV (today)
Unity, the game engine, draws **two pictures at the same time**:
- display 1, the **TV**: the course camera and the game's HUD;
- display 0, the **phone**: the controller sheet (golf), or the app's native controller on top (bowling).

Nothing ever switches. Both pictures are always there.

### Without a TV
There is only **one screen**, so the two pictures **take turns** on it:

| | Course camera (3D) | Game HUD | Controller |
|---|---|---|---|
| **Game view** | on | on | hidden |
| **Controller** | **off**: no 3D drawn, which saves battery and heat while you swing | hidden | on |

The switch is the same kind of thing golf already does today when it brings its controller sheet forward for a shot (`SportsRuntime.showUnity(onPhone:)`). We only add the other half: turning the course camera onto the phone for the game view. So it really is just **switching between the display and the controller**, as you said.

### Why "landscape" isn't an iOS rotation
The phone's interface **never rotates**. The game view is drawn landscape-sized (e.g. 2556×1179) and placed on the portrait screen **turned 90°**. Going back to the controller just puts the portrait controller in front again. This:
- makes the swap instant (an iOS rotation animates ~0.3 s and re-lays-out every screen);
- avoids Unity's portrait-only setting entirely;
- can't be confused by the phone tilting mid-swing.

The game view's side follows how the player is holding the phone (motion is already running), so it is never upside down.

### What has to adapt for a phone screen
- **HUD layout.** The game HUD was laid out for a 16:9 TV. A phone sideways is wider (~19.5:9), with rounded corners and the Dynamic Island on one end. HUD elements get anchored inside the phone's safe area, and TV-only text ("look at the TV") is hidden.
- **No display delay.** A TV over AirPlay shows the picture ~100–200 ms late, which is why tennis calibrates timing. On the phone screen that delay is ~0. Golf doesn't depend on it, and bowling won't after §5.
- **Sound** comes out of the phone speaker.

### Several phones
Each phone in a multiplayer golf round **already runs its own copy of the round**. The host sends every shot ("where it was struck from, along which line, and the swing itself: every phone flies this same shot", `NetworkGolfRound`), and each phone flies it itself. Today a guest's copy has its camera turned off because the guest was expected to look at the host's TV. Turning it on gives every player **their own view** of every shot on their own phone (or their own TV).

## 3. Phases

### Phase 1 — Golf and bowling never need a TV
- One rule in one place: `Sport.requiresExternalDisplay` is true for tennis only (unit tested).
- Replace every blanket `guard session.displayConnected` with it:
  - `TennisMenu.begin`, `beginLesson`, `launchFailed`;
  - `SportsSession.start / resume / readyToPlay`;
  - `GolfController` (resume disabled without a TV, the "TV OFF" pill → "PHONE");
  - Plaza PLAY hall (`HubControllerView.playOnly`, `bayForLaunch`). Golf and bowling bays open on the phone, and tennis bays say "Tennis needs a TV";
  - onboarding connect screen: golf lesson on the phone, tennis lesson still asks for a TV. ⚠ `GolfArcade/Onboarding/*` has uncommitted 10-24/25 work; build on top of it once that lands.
- Lobby copy: golf/bowling lobbies never mention a TV. Tennis is unchanged.
- Recording stays TV-only. It already refuses without one.

### Phase 2 — Game view ⇄ controller (Swift + Unity)
- **Swift:** `SportsDisplays.phoneGameWindow()`, built from the existing landscape preview window that the benchmark uses. Unity's view sits inside it at landscape size with a 90° transform. Add `SportsSession.phonePlay` and `phoneView: .game | .controller`. One `setPhoneView(_:)` brings the right window forward and sends `command("phoneView", …)` to Unity.
- **State machine:** a pure struct, unit tested.

| From | Event | To |
|---|---|---|
| game | Ready (my shot: golf `Aim` + shot ready, bowling `Setup`) | controller |
| controller | golf `Flight` · bowling `Rolling` | game |
| controller | View button · Pause | game |
| game | intro, other players' shots, Result, Replay, HoleDone, pins/sweep | game |

- **Unity** (`NativeSportsSession`, `GolfGame.Native`): a `phonePlay` launch flag (`touch` stays false, since touch gameplay is still removed). `phoneView` turns the course camera + HUD canvases on and the `PhoneScreenOnly` sheet off, or the reverse. Safe-area anchoring is added to `Hud`, `GolfShotHud`, `HoleOutCard`, `ShotResultPanel` and `BowlingHud`. Phone-play cameras get a 60 fps cap and the `presentationConstrained` rules.
- **Overlay:** restyle `SportsPreviewControls` into the small landscape Ready / Pause / result / Next Hole overlay.

### Phase 3 — TV connects or disconnects mid-round (golf + bowling)
**A round started with a TV loses it:**
- **Solo / pass-the-phone:** pause right away and ask:
  > TV disconnected — **Continue on this phone** · Reconnect TV · Exit

  If the TV comes back while the question is up, it closes and the round resumes on the TV.
- **Several phones (local or online):** nothing stops mid-shot. The disconnected phone's controller keeps working. At the **next stoppage** (golf: the ball comes to rest and the result shows, or between players; bowling: pins settled / sweep done), the match **auto-pauses for everyone** ("Waiting for Sam — TV disconnected") and Sam's phone asks the question above. Network rounds already carry a `paused` state (`NetworkGolfRound.State.paused`).
  - Recommended: if Sam doesn't answer within 60 s, Sam's phone switches to phone play so the party isn't held.

**A TV connects during phone play:** same pattern, offered rather than forced. "Move the game to your TV?" Yes reuses `routeGameToExternalDisplay()`. In multiplayer the move happens at the next stoppage.

**Tennis:** unchanged (pause, reconnect the TV).

### Phase 4 — Golf phone loop
Golf needs almost nothing beyond Phase 2. Aim, club and swing stay on today's controller sheet. Intro flyovers, flight, replay and results play in the game view, and tap-to-skip uses the existing `NativeContinue()`. Pass-the-phone shows "Sam's turn" + Ready in the game view.

### Phase 5 — Bowling V2: your own swing is the clock (golf-style)
**Problem with the current design:** the bowler walks a fixed approach on screen and you let go "when the slide foot lands". You're timing against the **picture**, which you can't see on a phone in your hand. On a TV it is also late (hence `DisplayLatency` + `BowlingLagLearner`).

**Golf doesn't have that problem.** You swing at your own pace, the golfer follows your phone (`PaceDownswing`), and impact is wherever **your** club bottoms out. Bowling V2 copies that:

1. **Setup (controller):** pick the board with ◀ ▶, then press and hold the ball = Ready (captures your stance, as today).
2. **Swing at your own tempo:** push away, swing back, swing forward, let go. `BowlingSwingDetector` already measures the swing angle, backswing height and forward speed from the phone.
3. **The bowler follows you.** The approach walk starts with your backswing. The steps are time-stretched so the slide foot plants exactly as **your** arm passes the bottom. The arm is already scrubbed by your phone's swing angle. This is golf's `PaceDownswing` applied to the walk. No new clips: the existing `Bowl_Shot` approach gets played back time-warped per step.
4. **The release is judged against your own arm, not the screen.** A swinging arm is a pendulum, and it is fastest at the bottom, so the detector knows the moment your arm passes the bottom (the peak of forward swing speed). Your thumb lift is graded relative to that moment:

| Thumb lifts | Result |
|---|---|
| well before the bottom | dropped early: slow, short, sprays |
| just after the bottom (window ~0–120 ms, to tune) | **clean release** |
| late, arm rising | lofted: bounces, loses line |
| held through the follow-through | **foul** (fouls stay on, as decided) |

5. **Speed** = forward-swing speed and **hook** = wrist turn at release, both unchanged from PLAN_Bowling §4.
6. **Haptics confirm, they don't cue:** a tick at the top of the backswing and a short buzz inside the release window. You feel it, but you're never waiting on it.
7. **One model for TV and phone.** Nothing depends on what's on screen, so `DisplayLatency` and the bowling lag learner are removed. The TV just shows it.

In phone play the controller is up during the approach. The view switches to the lane at release, so you see the ball, the hook, the pins, and a foul replay if you foul.

PLAN_Bowling.md §4 (fixed-walk release window, "phone never shows the game") is superseded by this section.

### Phase 6 — Several phones, each with its own display
- **Golf (local + online):** turn on each phone's own camera for its copy of the round (today `GolfGuestController` turns it off). Each phone runs the Phase 2 loop, and Ready shows only on the phone whose player is up. Everyone else watches the shot live on their own screen. A phone with its own TV uses its TV.
- **Bowling (local + online): new work.** No network bowling round exists yet. Build `NetworkBowlingRound` on the `NetworkGolfRound` model: host authority, one lane, turns. The bowler's phone sends the throw (board, speed, hook, revs, release grade, foul). Every phone rolls the same throw on its own copy of the lane (deterministic pins from the host's seed, plus the host's final pinfall).
- Lobbies: golf/bowling need no screen. The tennis rule (`hasScreenForSport`) stays.

## 4. Gates
- **G1 NO TV NEEDED:** golf and bowling start from the menu, a Plaza bay, retry/replay, onboarding and every lobby with no TV. Tennis is refused with the TV message at each of those (unit + UI tests).
- **G2 LOOP:** on device, with no TV, a full 3-hole golf round and a 10-frame bowling game. Every shot goes game → Ready → controller → shot → game, with 0 stuck states.
- **G3 SWITCH:** controller → game view ≤ **150 ms** after impact/release (logged). The swap is never slower than a frame on Ready.
- **G4 HUD:** game-view screenshots at iPhone 16 Pro and SE sizes, in both landscape directions. Nothing under the Dynamic Island, corners or home indicator.
- **G5 TV LOSS:** solo asks right away. A 2-phone round pauses only at the next stoppage. "Continue on this phone" resumes in phone play with no restart, and a reconnect while asking resumes on the TV. Tennis still pauses.
- **G6 BOWLING SELF-TIMED:** 20 recorded throws at slow, normal and fast tempos each land in the clean window when released just past the bottom. The bowler's slide meets the arm's bottom within 1 frame. Identical results with and without a TV for the same recorded motion.
- **G7 MULTI-PHONE:** 2 phones, no TVs: golf and bowling, local + online. Both phones show every shot. Only the player up gets Ready. The final scores match.
- **G8 THERMAL:** 15 min of phone-play golf on device without reaching `.serious`, ≥ 55 fps in the game view.
- **G9 PARITY:** with a TV connected, golf, bowling and tennis behave as before (bowling with V2 controls). Existing iOS and Unity EditMode tests pass.
- Proof goes in `proof/phone-play/`, and results in `GATE_RESULTS.md`.

## 5. Defaults (change any)
1. The game view follows whichever way the phone is held sideways.
2. Golf aiming stays on the controller sheet.
3. A one-time "Play on a TV for the big picture" tip on the first phone-play round.
4. 60 s answer timeout on the multiplayer TV-loss question, then phone play.
5. A TV appearing mid-round is offered ("Move the game to your TV?"), not forced.
