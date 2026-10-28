# Party link: one way in, and parties that heal (2026-10-27)

Base: Adnan's main `3ff23b2a` (build 0.1.5 (14)). Shipped as TestFlight **0.1.5 (15)**, uploaded 2026-10-28. Swift, plus two build fixes:

- `CFBundleDisplayName = MotionSports` in `GolfArcade/Unity/SportsInfo.plist`. The icon used to read "GolfArcade".
- `MajesticMesh.Sag` is `NoInlining`. Xcode 26.2's clang segfaults compiling `Bunting` with it inlined (`GolfArcade__27.cpp`, IL2CPP -O3).

## The error

What players saw: **"The operation couldn't be completed. (GameCenterFoundation.FastSyncTransportError error 4.)"**

`FastSyncTransportError` is the error enum of iOS 26's GKMatch transport, inside Apple's private GameCenterFoundation framework. It
is not documented. Its cases were read from the Swift field metadata of the iOS 26.3.1 and 26.6 binaries (Xcode's iOS DeviceSupport
copies). Both versions list them in the same order:

| code | case |
|---|---|
| 0 | internalError |
| 1 | illegalState (nilChannel, nilLocalParticipant, unknownBestHostHandle) |
| 2 | failedToElectLeader |
| 3 | failedToSendData |
| **4** | **groupSessionInvalidated** |

**Error 4 means Apple ended the match's session under the game.** It happens when a phone goes to the background or loses Wi-Fi, or
when one phone hangs up a match the other phone is still in. Build 14 logged `match(_:didFailWithError:)` and passed the raw error to
the screen. It also kept the dead GKMatch as the party's match, so every later send failed with the same text and the party never came
back.

## The fix: the party link

- **One place to meet.** A party meets in one private Game Center group, worked out from the leader's gamePlayerID:
  `PartyGroup.of(leader)`. It is FNV-1a, so it is the same number on every phone, on every launch and in every build. Every way in
  searches that group until the leader is there: an invite card, Game Center's notification, a CloudKit knock or code, Apple's own
  invite, a relaunch, coming back from the background. Nothing has to pass between the phones first. The old invited → accepted → go
  turn handshake is gone. The record is now only a mailbox: the friend's card, plus PARTY_READY so the host's phone is notified. So an
  invite that got stuck, crossed or answered twice still leads to the right place.
- **The leader** searches its own group whenever it expects someone: a friend it invited, someone who tapped Join or knocked, or a
  member whose phone dropped. A member who dropped is brought back at any time, even mid-match. A new friend comes in only in the Plaza.
  With friends still connected, the leader adds the newcomer to the live match (`addPlayers`). Otherwise it finds a new match.
- **A dead match heals.** These all count as a dead match: error 4 from didFail, a send that throws error 4 or 1, everyone
  disconnecting, or 12 s with nobody heard. The link pings every 4 s. The match is dropped quietly and the party, the lobby and any
  match in progress stay. Both phones meet again in the leader's group, and the lobby, the Plaza and a running round carry on. The
  player sees "Lost the connection to X's party. Reconnecting…" and then "Back together!", never Apple's text.
- **No second leader.** A guest whose leader dropped, rather than left, waits for that leader instead of taking the party over. Taking
  over is what made two leaders when the old one came back.
- **Leaving is not dropping.** A phone that leaves on purpose sends a `bye` on the match, so nobody waits for it.
- **Relaunch.** The party (leader, members, last time together) is kept in UserDefaults (`party.link.v1.<id>`). For 10 minutes a
  reopened app goes back into it by itself, once it is in the Plaza. A relaunched leader's new lobby replaces its old one on the
  guests' phones.
- **Packet numbers.** A phone that is back numbers its packets from 1 again. Its packets used to be dropped as old, so a relaunched
  leader's lobby was never taken. Now `seen` is cleared for a peer when it reconnects.
- **Waiting.** A party now waits 10 minutes for a dropped phone (`MultiplayerTuning.partyPatienceSeconds`, also AwayPolicy's party
  limit). A match still waits 3 minutes.
- **Gone.** The leader's rejoin invitation and Apple's `shouldReinviteDisconnectedPlayer` (now false): each was a second path into
  the same party. PartyJoinCoordinator is gone too: the link is the only thing that searches for a party. The file keeps its name so
  both Xcode projects still compile it, and now holds PartyGroup, PartyMemory, PartyLinkPlan and PartyTieBreak.

Where: `GolfArcade/Multiplayer/GameCenterTransport.swift` (the link: `runLink`, `planLink`, `meet`, `bringMore`, `adopt`, `matchDied`,
`joinParty`) and `PartyJoinCoordinator.swift` (the pure pieces). In `MultiplayerService.swift`: the heal path in `onPartyConnected`,
no hand-over while `waitingFor(owner)`, the restarted-leader lobby, `connectedPeers`, and `syncPartyLeader`.

## Tests

`PartyJoinHarnessTests.swift` was never in `GolfArcade.xcodeproj`, so its 240 orderings and 63 evenings did not run. It is added now,
and passes on this code. It also holds a new `PartyLinkHarnessTests` class: each phone is the real GameCenterTransport and
MultiplayerService, and only Game Center's matchmaking is faked in memory. The cases:

- a Join that meets in the leader's group;
- Apple ending the match under both phones (error 4): the same lobby on both, nobody leaves, the guest never takes over;
- one phone's match dying;
- the guest's app closed and reopened;
- the leader's app closed and reopened, with the guest waiting;
- a Join that starts before the leader knows about it;
- leaving on purpose;
- a third player dropping and coming back into the same match;
- error 4 mid-way through a golf round: the round goes on.

`PartyJoinTests` covers the planner, the group, the memory, and error-4 classification.

## Two-phone check (both phones on this build)

1. **Invite → Join.** A invites B, B taps Join. Both are in one party within ~10 s and stay there for 60 s.
2. **Background.** In a party, B swipes home for 30 s, then comes back. B shows "Reconnecting…", then "Back together!". A's lobby
   still lists B, and nobody becomes leader. Then do the same on A.
3. **Kill the app.** In a party, force-quit B and reopen it within a minute. B goes back into A's party by itself once it is in the
   Plaza. Then do the same on A: B waits, and does not become leader.
4. **Mid-round.** During online golf, B swipes home for 20 s. The round goes on, and B's turns come back.
5. **Stale invite.** A invites B. B taps the Game Center notification much later (or the card while A is in a match). B joins as soon
   as A is in the Plaza.
6. **Leave.** B leaves the party. A's row shows B gone at once, and A does not keep searching.

For any FAIL, send both phones' `Documents/SportsDiagnostics.log` (Settings › Voice & chat › Send diagnostics). Lines to look for
start with `party link:`, `party match`, `game center hangs up`, and `multiplayer: party back together`.
