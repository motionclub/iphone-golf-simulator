# Lobby invitations — 2026-10-15

Scope: keep the Friends screen in the app, use Game Center for invitations and party networking without its matchmaking controller, enter the shared walkable Plaza, sit at an online bench, let the host choose settings and Start. Lock solo play while friends are in the party.

GATE: NATIVE_BUILD PASS — final Xcode simulator test build succeeded, Swift 6 / iOS 26.5. Production bundle identity `com.adnanandrew.motionsports` is now also kept in the native project and XcodeGen source; the integrated production project already used it. The Game Center entitlement is retained.

GATE: APP_REGRESSIONS PASS — 149/149, 0 skipped. Suites: ClubHubTests, HubPartyTests, HubSessionTests, MultiplayerTests, MenuFlowRegressionTests. See `proof/ios-test-result.json` for the final build log and xcresult locations. The existing protocol-v5 changes had left one v4 expectation and a shared configuration fixture without environment fields; those test artifacts now match the existing v5 schema.

GATE: SERVICE_REGRESSIONS PASS — 92/92 in `proof/service-tests.log`. After the open-lobby reconnect and successor-host corrections, the changed room suite passes 10/10 again in `proof/room-tests-final.log`.

GATE: IN_APP_INVITE_PATH PASS — the friend row invokes programmatic `GKMatchRequest.recipients`, using the cached GKPlayer (not a team ID passed as a game ID). It no longer requires a Club Hub URL. Pending invites can be cancelled; duplicate taps do not replace a pending native request. No Game Center matchmaking controller is presented. Game Center accepted invitations now attach a party instead of being ignored. The inviter stays host, and peers use the existing lobby/Plaza protocol. This is implementation/build proof, not live Apple-delivery proof.

GATE: BENCH_SETTINGS PASS — sitting readies players without auto-start. Host-only Map / Sets / Games / golf course-events controls and explicit Start; a guest cannot start and a walking friend cannot be pulled into play. Existing TV requirements are preserved. Proof: `proof/host-bench-settings.png`, `proof/host-bench-small-phone.png`. These are running native views with an in-memory party on Simulator, not a two-device Unity match.

GATE: SOLO_LOCK PASS — solo stations refuse entry while a friend is in the party, with a visible reason; the menu launch and runtime entry also refuse solo launches. Leaving the party unlocks solo. The party tests exercise refusal/unlock and shared match launch; MultiplayerTests also covers solo menu/map-entry refusal on an ordinary remote-player transport.

GATE: FRIENDS_SCREEN PASS — `proof/game-center-friends-no-service.png`: enabled in-app Invite without a presence URL. Unknown presence is not labelled Offline; unavailable service-only controls are hidden. Host settings reviewed at 402×874 and 375×667 points; labels and Start fit.

GATE: FRIEND_OPEN_JOIN_IMPLEMENTATION PASS — with a service connection, an idle lobby advertises an open door, online friend rows offer Join, and the server independently checks friendship, visibility, availability and blocks. Previously admitted friends may reconnect during a match. Closed/busy/away/hidden hosts and strangers are refused. The service suite proves the actual WebSocket path; client tests prove the join action.

GATE: LIVE_FRIEND_OPEN_JOIN FAIL — `ClubHubServerURL` remains empty. Game Center supplies the friend graph and invitations but no app-readable friend online/lobby-presence directory. The optional service implementation is local; it has not been deployed or activated in production. No fake online badges or guaranteed join-without-invite are claimed.

GATE: GAME_CENTER_TWO_PHONES FAIL — NOT RUN. No pair of signed-in physical devices was exercised. Automatic account authentication, Game Center permission screens, offline notification delivery, cold-launch acceptance, Unity Plaza pose replication, and bench-to-match play still need a same-build two-account TestFlight/device check. Apple may require its sign-in/consent screen when the account needs attention; credentials cannot be supplied silently. No full-motion real-device pass is claimed.

No TestFlight upload, deployment, commit, or push was made. Existing unrelated workspace changes were preserved.
