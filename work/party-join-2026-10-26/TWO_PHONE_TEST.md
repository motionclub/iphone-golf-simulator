# Two-phone test: joining a friend's party (2026-10-26 fix)

**Phones.** A = Adnan's iPhone, B = the second TestFlight phone.
- Both phones need **this build**.
- Both need to be signed in to Game Center, and to be Game Center friends.
- Pull each phone's `Documents/SportsDiagnostics.log` after every test that fails.
- Useful log lines:
  - `party handshake … refused` / `… cancelled for …`
  - `Game Center invite: crossed with …`
  - `party match found / connected after … s / never connected`
  - `game center player … connected/disconnected`
  - `multiplayer hello from …`
  - `multiplayer lobby from host …`

**Pass bar (Fortnite).**
- One tap on Join, and both phones show each other in the party within ~10 s.
- No connect → drop loop. No error text.
- Each test **must stay together for 60 s** after joining. That catches the old drop 1–2 s after connecting.

---

## 1. Both invite each other (the 10-26 failure)
1. A and B are both in the Plaza, each alone.
2. Within 2 seconds of each other: A invites B, and B invites A (Friends → Invite).
3. Expected, without anyone tapping Join:
   - Exactly one phone hosts: the one whose invite somebody already said Join to. Otherwise the lower Game Center id hosts. Either phone can host, but only one does.
   - The other phone says "*X invited you too. Joining X…*". Its own invite row goes back to **Invite**.
   - Both phones end up in **one** party, and the log shows one `party match connected`. They stay together for 60 s.
4. Repeat with taps on both sides: A invites B and B invites A. Each taps **Join** on the other's banner as fast as possible. Same result: one party, no loop.
5. Repeat 3 times, so each phone has a chance to win the tie-break.

**FAIL if:**
- either phone shows two `party match found` lines in a row;
- you see "disconnected" within 5 s of "connected";
- both phones end up leaders of separate parties.

## 2. A stale notification tap
1. A invites B. B has the game closed and gets the notification ("*A wants to play with you!*"). **Don't tap it yet.**
2. On A: cancel the invite (Friends → Cancel), then invite B again.
3. On B: tap the **old** notification. Expected:
   - The game opens and B joins A's **current** invite, one tap in all.
   - Otherwise: "*That invite has ended. Ask A to invite you again.*", with A's current invite on the banner. One tap on it joins.
4. Variant: get A and B into a party first. Then tap an old notification from A on B. Expected:
   - "*You're already in A's party.*"
   - Nothing leaves, nothing reconnects, and the party stays for 60 s.
5. Variant, cold start: force-quit B. A invites B. Tap the notification on B's lock screen. Expected:
   - B opens.
   - The join waits for Game Center sign-in. It no longer fails at once with "*That invite has ended*".
   - B is in A's party.
6. After joining, B's Notification Center should no longer hold the old invite notifications.

## 3. Host backgrounded
1. A invites B. Then on A: press Home, so the game is in the background.
2. On B: tap **Join**. Expected:
   - B shows "*Waiting for A…*".
   - A gets a Game Center notification: "*B is ready to join your party. Open Motion Club to let them in!*"
3. On A: open the game, from the notification or from the icon. Expected:
   - B joins within a few seconds of A coming back.
   - A doesn't wait for a poll, and doesn't need a second tap on either phone.
4. Variant: A is in the **middle of a match** when B taps Join. Expected:
   - B waits ("*Waiting for A…*").
   - A's row says *Joining…*.
   - When A's match ends and A is back in the Plaza, B comes in by itself.
5. Rejoin check (cause 3): with A and B in a party, turn B's Wi-Fi off for ~5 s, then on. Expected:
   - B reconnects by itself, either through Apple's reconnect or through the 12 s rejoin.
   - The party is **not** torn down afterwards.
   - No second "connected/disconnected" pair appears after it settled.
   - On A, any rejoin invite is taken back: no "B joined" toast twice.

## 4. Fresh install, no TV
1. Delete the app on B and install this build. **No TV or AirPlay** on B.
2. B opens on the onboarding screen "*Let's get you on the TV*". (On a phone that was signed in before, Game Center signs in silently.) If B isn't signed in, use a phone that is: invites need Game Center.
3. A invites B. Expected:
   - B shows the invite **banner over the onboarding screen**.
   - The notification permission prompt may also appear: B already passed the account step, or B was signed in at launch.
4. B taps **Join**. Expected:
   - Onboarding steps aside.
   - B shows its phone-only Plaza (top of the screen) with the controller.
   - B joins A's party.
   - Both see each other, and the party stays for 60 s.
5. On A: leave the party (or remove B). Expected:
   - B returns to the onboarding screen **at the same step**. It isn't skipped and doesn't start over.
6. Variant: B is on the TV onboarding (AirPlay connected, mid-steps). A invites B; B taps Join. Expected:
   - The TV switches to the Plaza with A's party.
   - Onboarding comes back after the party.

---

**Report back:**
- PASS/FAIL per numbered step.
- For any FAIL: both phones' `SportsDiagnostics.log` and the time it happened.
