# Chat I: Online made simple, Game Center only (2026-10-19)

## Step 0: what existed and what works
- Branch `codex/game-center-lobby-invites` (f24cfcb0fe) is fully superseded on 10/19. Its auth waiters, `canAcceptParty`, `onPartyConnected`, `nativeParty`, the host bench settings and the solo lock are all here in a later form. Its real-time `GKMatchRequest.recipients` invite was replaced on 10-15 by the stored-invitation inbox (a GKTurnBasedMatch record plus a private playerGroup GKMatch). Nothing needed hand-applying. Its project.yml bundle-id hunk is now `$(APP_BUNDLE_ID)`.
- Real: GC sign-in, friends list, the inbox banner, accept/decline/expiry, party presence over the match, Call Party, and chat over the match. All of it is unit-tested only (gate files 10-11, 10-15 ×2).
- Unproven: every Game Center networking step on devices. All three earlier gate files list TWO_PHONES as FAIL / NOT RUN.

## Why invites "don't work as intended" (from the code)
1. Two invite systems were stacked: the Club Hub relay (invite, Join, share codes, presence) and Game Center. `ClubHubServerURL` is empty, so the relay half was dead or hidden, and the UI still mixed the two.
2. Tapping Game Center's invite notification only opened the app. The friend then had to find our banner and tap Join again. Fixed: the notification tap is now the Join.
3. Nothing followed the party: after joining, each phone walked alone and entered rooms alone. Fixed: the party follows its leader.
4. Chat was a full-screen sheet that hid the game, and every Game Center card said "invites you to Tennis". Fixed: inline strip, and the card now says "their party".
5. Still open (device-only): the inviter's phone waits on Game Center auto-matching for up to 120 s with one invite at a time, and Apple only lists friends who both allowed friends access. Neither has ever been tried on two phones.

## Follow-ups (not done in this pass)
- Inviting several friends at once (today it is one pending invite at a time, a GKMatchmaker limit of the current design).
- Delete the dormant relay code (`HubRoomTransport`, ClubHub relay paths, `club-hub/`) once the two-phone test passes.
- The checked-in `GolfArcade.xcodeproj` / `GolfArcadeUnity.xcodeproj` miss `AwayPolicy.swift`. Regenerate them with xcodegen at integration.
