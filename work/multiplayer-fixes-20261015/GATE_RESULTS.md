# Multiplayer repairs — October 15, 2026

Scope: Game Center-only in-app invitations and joining, lobby movement/emotes/visibility, free-text composing and overhead Plaza chat, background/resume, and automatic Call Party seating. Character assets, maps, cameras and game rules were not edited. No commits or upload.

GATE: NATIVE_REGRESSIONS PASS — 187/187, zero failures/skips, on iPhone 17 Pro Simulator / iOS 26.5. ClubHubTests, HubPartyTests, HubSessionTests, MultiplayerTests, PartyChatTests, FriendsLobbyProofTests, MenuFlowRegressionTests. `proof/native-final-results.json` contains the selected tests, result bundle and build-log paths. After clearing stale gather state on party changes, the affected HubPartyTests/HubSessionTests passed 23/23 again (`proof/native-reset-results.json`). The final startup guards also passed the eight HubSessionTests and two focused inactive/lifecycle checks (`proof/native-boot-results.json`, `proof/native-last-results.json`).

GATE: GAME_CENTER_INBOX_IMPLEMENTATION PASS — tagged, expiring `GKTurnBasedMatch` records supply the inbox; turn events and foreground polling refresh the existing Friends cards and banner. Join uses a private real-time playerGroup and preserves the invited host. Decline/cancel/expiry retire the temporary records. The invitation validates recipient, membership, group, expiry and Game Center participant identity; block checks handle both game and team IDs. Native invitations take precedence over the optional relay. Legacy real-time accepted invitations remain supported. `proof/game-center-inbox.png` is the running native view with injected Game Center-shaped cards, not live Apple delivery.

GATE: NATIVE_LIFECYCLE PASS — regression tests cover repeated resign/background/foreground/active notifications, three background cycles and transient inactive interruptions. Unity receives each real UIKit boundary once. Background never synthesizes a late resign callback (which can render); repeated inactive events cannot overwrite Unity's external-pause bookkeeping. The Plaza drops held input while inactive and defers Unity startup if UIKit becomes inactive before the scheduled boot. Actual Metal/iPhone resume remains a hardware gate below.

GATE: LOBBY_JOIN_IMPLEMENTATION PASS — joining clears Unity's station lock as well as the native station/panel, including deferred completion while inactive/booting. Meeting the host waits for a usable presence update. Tests exercise the native commands and both sides' lobby/presence paths.

GATE: CALL_PARTY_IMPLEMENTATION PASS — the call sends a real gather/seat command, queues across doorway travel or inactive state, and works for a party controller without its own TV. The host waits for every called connected member's actual seating presence, including friends in the locker. A remaining unseated friend keeps Call Party available. The existing host map/settings/Start action and display requirements remain.

GATE: CHAT_IMPLEMENTATION PASS — custom text can be drafted directly; Send opens existing setup if required and keeps the draft. Emoji joining characters and non-Latin text survive sanitizing. Existing filtering, parental restrictions, mute/block and rate limits remain. Only visible post-filter messages reach Unity; literal text appears over its speaker for eight seconds. System messages and muted/restricted messages are not forwarded. Bubbles follow walking/seated heroes and are bounded for close bench cameras.

GATE: UNITY_RENDERED_RUNTIME PASS — 6/6 in the actual Unity 6000.3.24f1 editor, including local/remote walking, both emotes, literal chat, eight-second expiry, automatic seating, delayed doorway gathering, controller-only gathering and the pre-existing phone/TV lobby tests. The final run also asserts projected chat width at a close bench camera. `proof/playmode.xml`, `proof/unity-runtime-run.log`, `proof/friends-chat-and-emote.png`, `proof/call-party-seated.png`.

GATE: IOS_EXPORT PASS — final export succeeded in 61 seconds with zero errors (Unity 6000.3.24f1); see `proof/ios-export.log`.

GATE: INTEGRATED_IPHONE_BUILD PASS — the final Unity export and native source built successfully for Release/arm64 iphoneos, unsigned. The app contains UnityFramework and metadata matching the final export byte-for-byte. `proof/integrated-final-build.log`, `proof/integrated-native-final-build.log`, `proof/integrated-final-package-check.json`. To fit the disk, the full build discarded its temporary C++ object cache and archive debug symbols after successful compilation; the last native increment reused that same verified archive. The generated project was restored and task-only DerivedData was removed after inspection. No source/build-system workaround remains.

GATE: LIVE_GAME_CENTER_DELIVERY_AND_JOIN FAIL — NOT RUN. Two signed iPhones and two Game Center accounts are needed to prove foreground invitation delivery, private-group matchmaking in both directions, and adding further party members. Local fakes do not pass this gate. No new service, hosting account or APNs setup is required by this implementation.

GATE: DEVICE_BACKGROUND_CRASH_AND_RESUME FAIL — NOT RUN. No device crash trace was available and Simulator does not embed Unity. The duplicate-pause/late-background-render defects are corrected and locally tested, but the user's actual iPhone crash must be checked on a signed device, including external displays.

Acceptance steps: [DEVICE_CHECK.md](DEVICE_CHECK.md).

## Verification limits and build notes

The first native test call used an unsupported suite-filter argument, so it ran unrelated art/locker fixtures; that broad run produced failures and was stopped. Only the correctly filtered 187-test final run is reported as passing. The standalone C# reflection runner compiled runtime and test assemblies, but its broad test execution reported 46 failures, including Unity native ECall methods unavailable outside the editor. The rendered Unity editor run is the runtime gate.

Screenshots use the real current Unity heroes and world. Remote presence is injected at the native bridge in the Unity tests; screenshots do not establish two-device networking or on-device performance. Native inbox/chat screenshots use in-memory fixtures. The temporary unsigned app is inspected and its manifest retained; large DerivedData/test-product packages created by this task may be removed to recover disk space.

## API references

- [Apple: programmatic stored invitations, loading matches and passing the first turn](https://developer.apple.com/documentation/gamekit/starting-turn-based-matches-and-passing-turns-between-players)
- [Apple: programmatically accepting an invitation](https://developer.apple.com/documentation/gamekit/gkturnbasedmatch/acceptinvite(completionhandler:))
- [Apple: real-time invitation events report acceptance](https://developer.apple.com/documentation/gamekit/gkinviteeventlistener)
- [Apple: resign-active notifications are posted with scene-based apps too](https://developer.apple.com/documentation/uikit/uiapplicationdelegate/applicationwillresignactive(_:))
