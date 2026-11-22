# PLAN — Phone Casting: one phone is the screen (golf + bowling)

**Status (2026-11-21):** Phases 1–5 built on branch `phone-casting-1120`, uncommitted. Everything that can run without phones passes. The device gates (G3–G7 on real phones, and the lag over mobile data) are still to run. Results are in `work/phone-casting/GATE_RESULTS.md`.
**Asked for:** two phones, where one is the "TV" and the other is the controller. More controller phones mean more players.
**Scope:** golf and bowling only. **Tennis is out:** Adnan, 11-20: "tennis can only be played on bigger screens". It works when the phones are side by side (no Wi-Fi network needed) and over mobile data.

## 1. What the player sees

```
 SCREEN PHONE (landscape, propped up)        CONTROLLER PHONE(S) (in hand, portrait)
 ┌──────────────────────────────────┐        ┌──────────────┐
 │  the game, full screen, TV HUD   │ ◀───── │ golf sheet / │  swing, aim, club, release
 │  sound + music play here         │  link  │ bowling deck │  haptics play here
 └──────────────────────────────────┘        └──────────────┘
```

1. One phone picks **Play → Use this phone as the screen**, then **Golf** or **Bowling**.
2. Phones nearby get the existing join banner: "Play golf on Sam's screen?" Friends far away, or people with no shared Wi-Fi, can also come in with the Game Center party invite.
3. Every controller phone is a player. The screen phone holds no player.
4. Player limits: **golf 1–3, bowling 1–3**. The lobby holds 4 people, and the screen takes one place (`MultiplayerModels.swift`, `.full` error). Raising this is a default in §6.

## 2. Why this is small: the parts already exist

| Need | Already in the code |
|---|---|
| A phone that runs the match for the others | Golf: the host is the authority (`NetworkGolfRound`). Guests are already controller-only (`MultiplayerLobby.controllerOnly`: golf `localID != hostID`) and watch the host's screen. |
| Bowling across phones | `BowlingGame.Network.cs`: every phone runs the game. The bowler's phone sends the throw and its pinfall, and seat −1 is already "a spectator". |
| A phone with no seat in a match | The lobby already allows seat −1 (`assign(_, seat: -1)`, the spectator swap). |
| Phones side by side, no Wi-Fi network | `LocalMultiplayerTransport` with `includePeerToPeer = true` (direct Wi-Fi). It uses no mobile data. |
| Phones over mobile data | `GameCenterTransport` (GKMatch). Apple relays the traffic when the phones can't reach each other directly. |
| Nearby hosting + join banner | `HubSession.useNearbyBench()` / `nearbyTick` / `joinNearby()`. Today it only hosts with `quick: .tennis`. |
| Unity drawing on the phone's own screen | `SportsDisplays.phonePlayWindow()` (handheld play) and `multiplayerControllerWindow()` |
| Screen stays awake during play | `SportsSession.active` already sets `isIdleTimerDisabled` |

**The new piece is the "screen" role.** It's a host phone with no seat whose Unity view fills its own display like a TV.

## 3. Phases

### Phase 1 — The screen role in the lobby (Swift)
- `MultiplayerParticipant` gets `castScreen: Bool?`. When it's set, the participant is at seat −1, is the owner/host, and there is at most one per lobby. It's valid for golf and bowling only; `valid` refuses it for tennis.
- `createLobby(owner:)` seats the owner at 0 today. A screen host is created at −1 instead.
- The re-seat pass (`participants[i].seat = i < capacity ? i : -1`, `MultiplayerModels.swift:149`) must skip the screen. Otherwise a sport change puts the screen in seat 0.
- `start` needs at least 1 seated player, not 2, when a screen is present. That allows a solo round on two phones.
- `MultiplayerService.hostLocal(quick:)` gets a `screen:` argument. `HubSession` gets a menu route `bay-cast-screen` → `useCastScreen(sport:)`, modelled on `useNearbyBench`.
- The join banner copy says "Play golf on Sam's screen?". Joining is unchanged.
- **Party / Game Center:** the party lobby gets a "This phone is the screen" toggle for the leader, using the same field. The toggle is shown only when the party's sport is golf or bowling.
- The tennis entry points don't show the option. If tennis is picked while a screen is set, the copy is "Tennis needs a TV or Mac".

### Phase 2 — The screen phone shows the game (Swift + Unity)
- `SportsDisplays.castScreenWindow()` is a full-screen window on the phone's own scene, like `phonePlayWindow()`. `SportsSession.launch` picks it when `castScreen` is set and no TV is connected. If a TV is connected, the TV is used as today.
- **Orientation:** landscape, either way up, locked for the match. It reuses the menu's rotation gate (`phoneMenuRotates`) and forces upright again on leaving.
- **Unity:** a `castScreen` start flag in `NativeSportsSession`:
  - camera rect full (0, 0, 1, 1), not the handheld (0, .25, 1, .75);
  - the TV HUD layout (`Hud.ReservedBottom = 0`; golf map and club card shown);
  - no local player, no controller sheet;
  - sound on; 60 fps; `presentationConstrained` rules on heat.
- **On screen:** a small "Leave" and pause control only. There is no gameplay touch, because touch play stays removed.
- **Battery hint** in the lobby: "Plug in the screen phone for long rounds".

### Phase 3 — Golf on the screen
- The screen phone is the golf host at seat −1. `NetworkGolfRound` already takes the shot inputs from seated senders (`SportsMultiplayer` "input"). The host check is `IsHost`, not "has a seat". The work is checking every `LocalSeat`/`Seat(localID)` use for a host at −1: turn clock, emote prompt, `golfResultDone` (shooter's phone ends its result), skip votes, intro "golfer up".
- **Skip votes:** the screen doesn't vote. "Everyone skipped" counts seated golfers only.
- **Controller phones:** unchanged. The `GolfController` native sheet, with the Unity replica underneath and its camera off.
- **Pass-the-phone guests:** a controller phone can still add local guests (`controllerID`), so one controller plus one screen can still be a 2-player round.

### Phase 4 — Bowling on the screen
- The screen phone joins `BowlingGame.ConfigureNetwork` as `localIndex = -1`, the spectator path that already exists. It rolls every throw from the bowler's packet and draws the lane full screen.
- **Host duties stay with the screen phone:** bowling for a dropped player (`NetworkDrop`) and the heartbeat. Check that `HostPhone` with no local player still does both.
- **Controller phones:** show only `BowlingController` (full controller, not the handheld deck). Their lane camera is off, which saves heat and battery. Their Unity copy still runs the throw: the bowler's phone is the one that settles pinfall.
- **Timing:** bowling is self-timed from the phone's own swing (no `DisplayLatency`). The screen phone's lag doesn't affect the throw.

### Phase 5 — Mobile data and the link
- Game Center is already on the party path, so there's no new transport. The work is checking that the screen role works over it.
- **Data use:** the golf aim stream is 30 Hz (small), plus one shot packet per swing. Bowling sends one packet per ball plus a 1 s heartbeat. Measure bytes per round on device and put the number in the lobby help text.
- **Lag:** a golf guest's swing waits one round trip before launching. Measure it over LTE/5G. Gate below: ≤ 400 ms extra from swing to the ball leaving on screen.
- **Screen phone drops** (call, app closed, dead battery): the screen is the host, so the match can't go on. Use the existing away rules (`AwayPolicy`, 180 s): controllers show "Waiting for the screen", and the round resumes if it comes back. **Host migration is out of scope.**

## 4. Gates (binary, proof in `work/phone-casting/`)
- **G1 LOBBY:**
  - a screen phone hosts golf and bowling with 1, 2 and 3 players;
  - tennis refuses the screen role at every entry point;
  - re-seating never seats the screen;
  - unit tests on `MultiplayerLobby.valid`.
- **G2 SCREEN VIEW:**
  - full screen landscape both ways, TV HUD, no handheld deck, sound on the screen and not on the controllers;
  - screenshots on 2 phone sizes.
- **G3 GOLF:** on 2 phones, side by side, Wi-Fi off the network:
  - a 3-hole round with 0 stuck states;
  - intros, skips, results and hole-out all play on the screen;
  - the final card matches on both phones.
- **G4 BOWLING:** on 2 phones, a 10-frame game; the score sheets match on both phones.
- **G5 THREE PHONES:** 1 screen + 2 controllers, golf and bowling, turns pass correctly.
- **G6 MOBILE DATA:** 2 phones, Wi-Fi off, Game Center party:
  - golf 3 holes + bowling 10 frames;
  - measured data per round and swing-to-launch lag written down;
  - lag ≤ 400 ms extra.
- **G7 DROP:** the screen leaves for 30 s and comes back, and the round resumes. A controller leaves past the limit, and the existing rules apply (golf turns pass; bowling host bowls for them).
- **G8 PARITY:** with a TV, golf, bowling and tennis behave exactly as before. Existing iOS + Unity EditMode tests pass.

## 5. Order and size
1. Phase 1 + 2: lobby role + screen view. Testable in the simulator with the `--lobby-mock` lobby and an editor seat.
2. Phase 3 golf: proves the whole idea on 2 phones.
3. Phase 4 bowling: mostly checking, since the network game exists.
4. Phase 5 data/drop: device-only.

Device runs need Adnan's phones (`phone-build-recipe`). G3–G7 can't pass in the simulator.

## 6. Defaults (change any)
1. **Name in the menu:** "Use this phone as the screen".
2. **Max 3 players** with a screen (the lobby limit stays 4). Raising it to 5 is a one-line capacity change plus a load test.
3. **The screen phone plays no one.** Pass-the-phone guests ride on a player's phone instead: the screen's golf lobby has "+ Guest" on each player's row. Built.
4. **Landscape locked** during a match, either way up.
5. **iPad works as the screen** with the same code (same role, bigger picture). It isn't a separate target.
6. **Tennis is not offered** on a phone screen. Whether an iPad counts as "a bigger screen" for tennis is Adnan's call, and it's not in this pass.

## 7. What was built (2026-11-21)
- **Phase 1:** the `castScreen` role, lobby rules, menu rows (`bay-golf-cast`, `bay-bowling-cast`), the screen's lobby and the "Play golf on X's screen?" banner. The party leader gets a "This phone is the screen" switch.
- **Phase 2:** the screen phone draws the game full screen, sideways, with the TV HUD and only an End game button over it. Players' phones are controller-only and draw no picture.
- **Phase 3:** golf with a seatless host. One golfer is a round, and each new hole waits for the screen's own build. Guests can ride on a player's phone.
- **Phase 4:** bowling, with a live setup mirror, the throw sent at release, then the pinfall; the screen holds its score for the bowler's pinfall.
- **Phase 5:**
  - Players see "Waiting for the screen phone" while it is away.
  - Golf data to players' phones is cut from 3.3–4.3 to 0.6–0.7 MB a minute: 6 updates a second, plus one at once on each change.
  - A screen phone that is gone past the away limit ends the game with a screen-specific message.
- **Found and changed beyond this plan:**
  - The bowling throw used to travel only after the pins settled.
  - The first-launch lesson rule blocked the screen.
  - The hub closed the screen's panel as it opened.
  - The menu's 5-row lists now use the Play screen's row size.
