# Joining a friend's party: one tap, reliably (2026-10-26)

Build 0.1.5 (11). On 10-26 two phones joined once at 20:35. After that, with both friends inviting each other, the party looped connect → drop. In the 21:46–21:54 host log the peer connects, says hello and drops 1–2 s later, whichever phone hosts. The cause was several join handshakes running at once on one phone, each one tearing the others down.

Swift only (`GolfArcade/`). Staged in the bowling integration tree, not committed. The 10-25 handshake design is unchanged: a turn-based record goes invited → accepted → go, then `waitForPlayers` on a private `playerGroup` match.

## Cause → fix

| # | Cause (verified) | Fix | Where |
|---|---|---|---|
| 1 | Up to five handshakes ran at once on one phone: GC host `bringIn`, GC guest join, CloudKit `letIn`, CloudKit knock join, auto rejoin. Each tore down the others. | **`PartyJoinCoordinator`**: one handshake per phone. Every path asks it first. Rules: (a) the same handshake twice is refused; (b) only one host handshake at a time, and the next refresh or tick retries; (c) no host role while joining; (d) a join the player asked for supersedes whatever runs, and the old one's search is cancelled; (e) an automatic join never cancels anything. | `Multiplayer/PartyJoinCoordinator.swift`, used throughout `GameCenterTransport.swift` |
| 1a | `canAcceptParty` always ran `cancelSearch()` + `leave()`. | It takes `automatic`. An automatic join returns false while the phone is in a lobby with other phones connected. It only leaves when there is a lobby or search to leave. | `MultiplayerService.ensureGameCenter` |
| 1b | `attachParty` disconnected any previous match. | A guest only reaches it after choosing to leave. Hosts with a match use `addPlayers`. Guards stop a superseded handshake from ever starting a search. | `GameCenterTransport.attachParty`, `bringIn`, real-time invite |
| 1c | `hostAvailable` allowed hosting while the phone was itself joining. | Returns *later* (false) while a guest handshake runs, while a CloudKit knock waits, or while a quick-match search runs. | `MultiplayerService.ensureGameCenter` |
| 1d | `letIn` bumped the shared `generation`, which aborted an in-flight `bringIn`. | `generation` is gone. Each handshake has its own token. A let-in while a bring-in runs is refused, and the knock is answered on a later tick. | `GameCenterTransport.letIn` |
| 1e | The global `GKMatchmaker.cancel()` killed the next search. | Searches are owned by a token (`searchOwner`). A handshake or its deadline cancels only its own search, and only while that search runs. Quick match has its own token. | `matchmake(_:_:)`, `cancelMatchmaking(_:)`, `deadline` |
| 2 | Crossed invites: both friends invited each other, both joined, and there was no tie-break. | **`PartyTieBreak`**, computed the same way on both phones from the records both can read. The record that stays is (1) one somebody already said Join to, else (2) the bigger party's, else (3) the one whose host has the lower gamePlayerID. The other record is retired. The phone whose invitation lost joins the winner by itself (automatic). If the friend's phone already retired the other half, a missing outgoing record plus their incoming invitation counts as crossed too. CloudKit knocks on each other: the lower gamePlayerID answers, and the other keeps knocking. | `PartyTieBreak`, `GameCenterTransport.readInbox`, `ClubCloud.answer` |
| 3 | The auto rejoin re-invited after 4 s, under Apple's own reconnect. It was not cancelled on reconnect, so it killed live parties. | Rejoin waits **12 s** (`rejoinAfter`). When the member reconnects, the leader **takes the rejoin record back** (`cancelInvite`). Leaving the party takes back any still out. On the member's phone a rejoin is *automatic*: refused, and its record retired, the moment the phone is in a connected party again, including while the join loop is waiting. A rejoin card from someone this phone is connected to is declined, not joined. | `MultiplayerService.peersChanged/leave/inviteDroppedMembersBack`, `acceptStoredInvitation`, `ClubHub.accept` |
| 4 | `partyGroup` leaked after a failed join. The friend then published the host's group as their own Party. | A guest's group and allowed list are set **only once connected**. A failed guest attach clears both. `cloudHostParty` offers nothing while joining. | `attachParty(…, guest:)`, `connect`, `joinGroup`, `cloudHostParty` |
| 5 | Invite records were not retired on several failure exits. A relaunch resumed a join with no tap (`resumed` lived in memory only). | Every guest failure exit (load, ended, host left, accept, 4 failed rounds, automatic abort) **retires the record**. One that couldn't be read is retired when the inbox next lists it. The host retires after `maxRounds` (4) failed go's (row: "Couldn't connect"). A relaunch resumes **only a Join tapped < 120 s ago** (`JoinMemory`, UserDefaults). Anything older is a banner that needs a tap. | `acceptStoredInvitation.giveUp`, `bringIn`, `JoinMemory` |
| 6a | CloudKit knocks outlived the joiner's wait (180 s vs 90 s) and the joiner never deleted them. | Each knock **expires with its round's wait**. The joiner deletes its own knock when the wait ends: answer, time-out, cancel or next round. | `ClubCloud.join` |
| 6b | A joiner timeout came back as a silent `CancellationError`. | Deadlines mark the token, and the search fails with words ("Couldn't connect. Try again."), so the knock goes round again. | `deadline`, `searchFailed` |
| 6c | The tick loop awaited a let-in (up to 80 s), stalling presence. | The let-in runs beside the tick (`letInTask`). One at a time. | `ClubCloud.answer` |
| 6d | `available()` was checked once. | Asked again every 30 s until CloudKit is there. | `ClubCloud.start` |
| 6e | Invite records and notifications were never cleaned up. | The recipient deletes Invite notes addressed to it on each tick, plus expired Answers. Delivered invite notifications for invites that are over are removed from Notification Center. | `ClubCloud.tick`, `ClubPush.removeDelivered` |
| 7a | No TV meant `OnboardingConnectScreen` with no skip. `canJoinNow` was false during onboarding, so an invite could never be joined. | The invite banner **shows over onboarding**. Join (or a notification tap) **puts onboarding off until the party is over**: `OnboardingFlow.holdsMenu` is false while joining or in a party. With a TV the Plaza takes the TV. With no TV, the phone shows its own Plaza. Onboarding comes back at the same step afterwards. | `OnboardingFlow.partyWaits`, `ClubHub.updateBanner/accept` |
| 7b | A cold start from an invite raced Game Center sign-in. | The join waits up to 30 s for sign-in (`untilSignedIn`) before reading the record. | `MultiplayerService.acceptGameCenterInvitation` |
| 7c | Notification permission was only asked in Friends. | Asked on onboarding's account step once signed in, after sign-in for returning players, on the first invite sent and after the first join. iOS shows its prompt only once. | `OnboardingFlow.next`, `ClubSignIn.start`, `ClubHub` |
| 8 | The host had to be in the foreground and in the Plaza (inbox refresh only while active). | The guest's Join sets a Game Center turn message, so the host's phone is **notified even with the game closed**: "Bea is ready to join your party. Open Motion Club to let them in!" (`PARTY_READY`). Coming back to the app refreshes the inbox at once. A turn event during a refresh triggers a re-read instead of being dropped. The joiner's 2 s wait ends early on a turn event. The host still lets people in only outside a match. | `acceptStoredInvitation`, `MultiplayerService.prepare`, `refreshInvitations`, `nap` |

Also:
- An old notification for a replaced invite joins that friend's open invite, if the inbox has one.
- Quick match refuses to start while a party handshake runs.

## Tests

A scratch xcodegen project with symlinked `GolfArcade*/` dirs, run on the iPhone 17 Pro simulator. The checked-in xcodeproj is stale; `PartyJoinCoordinator.swift` and `PartyJoinTests.swift` are new files that xcodegen picks up.

- `PartyJoinTests` (new, 8):
  - the coordinator's rules table;
  - its tokens, supersede and cancel;
  - the tie-break gives the same answer on both phones over every step × party-size combination, plus the rule order;
  - `JoinMemory`;
  - crossed CloudKit knocks;
  - knock expiry and cleanup, and a let-in that does not stall the tick;
  - CloudKit availability retry and note cleanup;
  - onboarding stepping aside.
- `ClubHubTests`:
  - the onboarding test was rewritten to the new behaviour;
  - new: automatic joins give way;
  - new: an old notification finds the open invite;
  - new: already in the party;
  - new: crossed/failed rows;
  - the CloudKit drop-in test now awaits the background let-in.

Game Center itself cannot run in the simulator: that needs two phones (TWO_PHONE_TEST.md).

## Not changed / follow-ups
- The host still brings people in only outside a match. Mid-match admission would need the match itself to accept a late spectator.
- A guest whose leader drops elects itself leader of a 1-person lobby (`handOver`). If Apple then reconnects the old leader into the same GKMatch, there are two owners. This is pre-existing; the rejoin no longer makes it worse.
- A stale-notification join that fails with "ended" does not jump to a newer invite from the same friend that arrived after the tap. The banner shows the newer one.
- The checked-in `GolfArcade.xcodeproj` / `GolfArcadeUnity.xcodeproj` do not list `PartyJoinCoordinator.swift`. The device recipe runs xcodegen, which picks it up.
