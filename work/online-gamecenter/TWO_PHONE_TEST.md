# Two-phone test: Game Center party (chat I, 2026-10-19)

These gates cannot run on the Simulator: no Game Center sign-in, no invitation delivery, and no Unity in the Simulator.
Run this once on two real iPhones. Write PASS or FAIL on each line and send back the two `SportsDiagnostics.log` files.

## Setup (10 min)
- Two iPhones, A (host) and B (friend), each signed in to a different Game Center account. The two accounts are Game Center friends.
- Install the same build on both, from the same TestFlight number or the same device build of this branch. Bundle id: `com.adnanandrew.motionsports`.
- A has a TV on AirPlay. B can be phone-only or have its own TV.
- On each phone, open the game once, allow Game Center if Apple asks, and allow "friends list" access when asked.
- Note: the game never uses the Club Hub server. `ClubHubServerURL` stays empty. Do not set it.

## Steps
1. **Friends list.** On both phones, open Friends from the Plaza menu. Each phone shows the other player with a lime **Invite** button. FAIL if the list is empty (check Settings › Game Center › friends access for this game).
2. **One-tap invite, app open.** B stays in the Plaza. A taps **Invite** on B once, and nothing else.
   - A's row reads "Sending…", then "Invite sent".
   - Within about 10 s, B shows our banner at the top: "A invites you to their party · Online", with **Join** and **Not now** and a 2-minute bar.
   - B taps **Join**. Expect "Joining A…", then "You joined A's party". Within about 15 s each phone's Plaza shows the other hero, and B's hero walks over to stand beside A's. No Apple matchmaking screen at any point.
3. **One-tap invite, app closed.** A leaves the party (Friends › Leave party). B force-quits the game. A taps **Invite** on B again.
   - B gets Game Center's notification. B taps it once. The game opens and joins A's party with no second tap on our banner (it may show "Joining A…").
   - FAIL if B must tap Join again, or if nothing happens. Note how long the join took.
4. **Rooms together.** A is the leader (the party's host). A walks through the PLAY hall door, then into the Tennis room.
   - Within about 1 s of A's fade, B's screen fades too, and B's hero appears next to A's in the same room. B's phone reads "Following A to Play Hall", then "… to Tennis".
   - B walks alone into the Locker: A must stay put. A walks back out to the Plaza: B follows again.
5. **In-game chat, no sheet.** On B, tap the chat bubble in the top-right dock. A small strip opens at the top: recent lines, quick phrases, and a text field.
   - B types "hi" and sends. On A, the line floats at the top of the phone for about 6 s and appears over B's head on the TV. A never left the controller.
   - A taps a quick phrase ("Let's go!") from the strip. B sees it.
   - Type a swear word: it arrives masked (`****`). Long-press Mute in the full chat (expand button): muted lines stop arriving.
   - During a golf swing or tennis rally, the floating lines must not block the swing button or the stick.
6. **Bench → match → back.** Both sit at the Tennis Online bench. The host picks settings and taps Start. Both phones load the same match. At the end both return to the Plaza and are still in the party.
7. **Leave.** B leaves the party. A's Plaza drops B's hero. Solo modes unlock on both phones.
8. **Third friend (optional, phone C).** While A and B are in the party, A invites C. C joins, and all three follow A through a door.

## If a step fails
Write down the step number, both build numbers, what each screen showed, and the time. Send both phones' `SportsDiagnostics.log`. It is in the app's Documents folder: with the phone plugged in, Xcode › Devices › the app › Download Container. It contains the "Game Center invite inbox" lines.
