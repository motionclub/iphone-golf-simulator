# Two-phone check

Use the same production-bundle build on two phones with different Game Center accounts. Both players must be mutual Game Center friends and allow this game's friends access.

1. Open each app. A returning account authenticates automatically; complete Apple's login/consent if requested. Open Friends: both friends should appear with enabled Invite.
2. Close the second app. Tap Invite once on the first phone. Accept the Game Center notification on the second phone. It must open into the inviter's Plaza, with no Game Center matchmaking window. Walk on each phone and confirm the other player moves.
3. Try Campaign, Training, Exhibition, golf Round and pass-the-phone while together: each must refuse solo entry. Locker and Settings remain usable.
4. Connect the required TV(s). Sit at the same Tennis Online bench. No match should start yet. Host chooses a map, sets and games; guest cannot change settings or start. Host taps Start: both phones load the same chosen match.
5. Exit back to the Plaza. Both players remain in the party. Leave the party: solo modes unlock.
6. Invite an offline friend, cancel, and resend; no stuck Sending/Cancel state or unwanted match should remain.
7. Optional, only once a presence endpoint is deployed/configured: opening the game publishes an idle open lobby. Friend taps Join without an invitation and enters the same Plaza. Test a blocked stranger, full lobby, host in match, and reconnect during play.

Failure evidence: record which step failed, the two build numbers, Game Center sign-in state, and each phone's SportsDiagnostics.log. Real invitation and presence gates stay FAIL until these steps have device evidence.
