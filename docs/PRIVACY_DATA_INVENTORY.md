# MotionSports: Party Games — privacy data inventory

Written 2026-10-28 from the source on `main` (commit cd4013188a plus the working tree). This is the source of truth for
`site/privacy/`, `site/support/` and `docs/APP_REVIEW_NOTES_v1.0.txt`. If the code changes, update this file first.

App: MotionSports: Party Games, bundle `com.adnanandrew.motionsports`, version 0.1.5. The phone is the controller and the game shows on a
TV or Mac through AirPlay screen mirroring. Golf and bowling can also be played on the phone screen alone.

## Headline facts

- **There is no server of our own.** Release builds never contact the Club Hub service (`ClubHubConfig.serverURL` returns nil
  outside DEBUG, `GolfArcade/Social/FriendsSource.swift:103`). The legacy Node server in `server/` (profiles, rounds, leaderboard) is only
  reachable from Unity's own menu, and that menu never shows inside the app (`GolfGame.cs:317`: `if (NativeSportsSession.Embedded) return;`).
  The legacy server's `BackendClient` is a no-op unless a profile signed up through that hidden menu.
- **Online play is Apple's Game Center.** Presence, party codes and invite notifications use **Apple CloudKit** (public database of
  container `iCloud.com.adnanandrew.motionsports`).
- **No advertising, no ad identifier and no App Tracking Transparency prompt.** The app does not call any analytics service of its own
  (`GolfArcade/Onboarding/Analytics.swift` writes to the local log only).
- **Unity engine caveat (flag).** `Unity/ProjectSettings/ProjectSettings.asset` has `submitAnalytics: 1` (the "Disable HW Statistics" box is
  unticked), so the Unity engine may send anonymous hardware statistics (device model, OS, GPU and similar) to Unity Technologies. The
  `com.unity.analytics` package is also in `Unity/Packages/manifest.json`. It is never initialised: there is no `UnityServices` or `AnalyticsService` call
  in `Unity/Assets`, there is no cloud project ID, and Analytics, Crash, Performance and Ads are all off in `UnityConnectSettings.asset`.
  **Recommendation:** set `submitAnalytics: 0` and remove `com.unity.analytics`. Then this caveat can come out of the policy.

## Feature by feature

| # | Feature | What it reads or creates | Leaves the phone? | Where it goes | Kept for | Code |
|---|---|---|---|---|---|---|
| 1 | Motion sensors | Gyroscope, accelerometer and attitude via `CMMotionManager` device motion | Raw samples: no. Swing results and game actions go to the TV picture and, in multiplayer, to the other phones in the match | On-device; other players' phones | Not stored (live only) | `GolfArcade/Unity/SportsMotion.swift`, `Mock/MotionSwing.swift` |
| 2 | Camera / ARKit (tennis) | Rear-camera frames and ARKit world tracking for the court scan (screen flashes) and side-to-side steering | No. Processed live on the phone, not recorded or uploaded | — | Not stored | `SportsMotion.swift:189` (`AVCaptureDevice.requestAccess`), `Tracking/` |
| 3 | Local network (nearby party) | Bonjour `_motionparty._tcp` + UDP on the same Wi-Fi | Yes, to phones on the same network only | Nearby phones in your lobby: display name, character look, game state, chat, voice | Not stored | `Multiplayer/LocalMultiplayerTransport.swift` |
| 4 | AirPlay display | The game's picture and sound | Yes, to the TV/Mac you pick in Screen Mirroring | Your own TV or Mac via Apple AirPlay | Not stored by us | iOS screen mirroring, `SportsDisplays.swift` |
| 5 | Game Center | Game Center sign-in; teamPlayerID, gamePlayerID, display name; parental flags (`isUnderage`, communication and multiplayer restrictions) | Yes | Apple Game Center (sign-in, invites, matchmaking, peer-to-peer match data) | Apple's policy | `Multiplayer/GameCenterTransport.swift`, `Party/PartySafety.swift:62` |
| 6 | Game Center friends | Your Game Center friends list (only after the system "Friends" permission, `NSGKFriendListUsageDescription`) | Friend IDs are used to look up their presence records in CloudKit | Apple (Game Center, CloudKit) | Not stored by the app | `Social/FriendsSource.swift:46-55` |
| 7 | Online play / Quick Match | Game Center real-time match (up to 4). Quick Match uses Game Center auto-match and can pair you with players you don't know | Yes | Apple Game Center | Match lifetime | `GameCenterTransport.swift:908-917` |
| 8 | Presence + party codes + invites (CloudKit) | `Player` record: record name = Game Center teamPlayerID, gamePlayerID, display name, online state, last-seen time, party info (unless "invisible"). `Party` record: code, host IDs and name, size, open flag. `Invite`/`Knock`/`Answer` notes: from/to IDs, sender name, code, expiry | Yes | Apple CloudKit public database of our container. Written under your iCloud account. Developer-readable | **Player and Party records have no automatic deletion** (the Player record is refreshed about every 45 s while the game is open). Notes are deleted by the recipient or on expiry (120 s to a few minutes) | `Social/ClubCloud.swift:362-411` |
| 9 | Push notifications | Notification permission, asked after the player's first invite (never at launch). CloudKit subscription `to == <your id>` | APNs token goes to Apple only | Apple (APNs/CloudKit) | Apple | `Social/ClubHubLive.swift:156-179` |
| 10 | Invite by text ("phone-number invite") | The app builds a message with your display name, a party code and a link, then opens Apple's **Messages compose sheet** (or the share sheet) | Only when **you** pick recipients and tap Send in Apple's sheet | The people you choose, via Messages/SMS | Not stored by the app | `Social/ClubHubView.swift:288-364`, `ClubCloud.swift:215`, `FriendsSource.swift:137` |
| | | **The app never reads contacts or phone numbers.** There is no Contacts permission and no `CNContact` use. The number is typed or picked inside Apple's sheet, which the app cannot see. Nothing is uploaded or hashed | | | | |
| 11 | In-game chat | Typed messages (140 chars max), quick phrases | Yes, to party members only | Other phones in your party, via the Game Center match or the local network | **Memory only, this session only, last 100 messages.** Never saved or uploaded | `Party/PartyChat.swift:37-38,178` |
| 12 | Chat safety | Birth year (asked once; an under-13 answer is locked for 7 days), accepted rules version, block list (Game Center IDs), profanity filter setting | No | On-device (`UserDefaults`) | Until the app is deleted | `Party/PartySafety.swift` |
| | | Rules: under 13, no age given, or Game Center limits → quick phrases only (no typing, no voice). Teens always filtered. A filter masks profanity and slurs and hides links, emails and phone numbers. Report, Mute and Block sit next to every message | | | | |
| 13 | Reports | Reported player's name and ID, reason, their last few typed lines, your name, time | Only when **you** send it: the app opens a **text message** to the support number (`PartyContact.smsNumber`), or email if `ClubSupportEmail` is set. Currently empty, so it uses SMS | Developer (Adnan), by SMS | As long as the message is kept | `Party/PartySafety.swift:212-254` |
| 14 | Party voice chat | Microphone, only after you tap the mic (`NSMicrophoneUsageDescription`). Voice-activity gated, encoded on the phone | Yes, to party members only | Party phones (Game Center match or local network) | Not recorded or stored, **except** that your voice can be in a TV recording you or a friend makes | `Party/PartyVoiceEngine.swift:700`, `PartyVoiceCoordinator.swift` |
| 15 | TV recording / clips | The TV picture and game audio (plus party voice if on), MP4 in the app's temp folder | Only if **you** share or save it (share sheet; "Save Video" needs `NSPhotoLibraryAddUsageDescription`, add-only, never reads Photos) | Wherever you send it | Temp files are pruned by the app and by iOS | `Unity/Assets/Plugins/iOS/SportsSessionRecorder.mm:257-330`, `Unity/PointClips.swift:109` |
| 16 | Onboarding + lessons | Step reached, lesson station, install time, rewards claimed | No | On-device | Until the app is deleted | `Onboarding/OnboardingStore.swift` |
| 17 | Bowling (in build 9) | Same motion + optional pass-the-phone. No new data types | As #1 / #7 | — | — | `Unity/BowlingController.swift` |
| 18 | Progress, looks, settings | XP, unlocks, character look, audio/voice settings | No (except name + look shown to other players in a match, and the CloudKit Player record) | On-device | Until the app is deleted | `UserDefaults` |
| 19 | Diagnostics log | `SportsDiagnostics.log` in Documents: game events, local `Analytics.track` events (time since install, screen and step names), audio route, memory use. No identity or camera content (`Analytics.swift:3`). Also `NSLog` to the device's system log | Only if **you** tap Settings › Send diagnostics (share sheet) | Wherever you send it | Capped at **1 MB** (keeps the newest half when full) | `Unity/SportsMotion.swift:7-33`, `Party/PartySettingsView.swift:47` |
| 20 | Apple crash reports | Standard iOS crash and energy reports | Only if the user turned on "Share with App Developers" | Apple → us through App Store Connect / TestFlight | Apple's policy | iOS |
| 21 | Unity engine | Possibly anonymous hardware statistics (see the caveat above) | Possibly | Unity Technologies | Unity's policy | `ProjectSettings.asset:96` |
| 22 | Web pages | GitHub Pages may log visitors' IP addresses | — | GitHub | GitHub's policy | `.github/workflows/static.yml` |

## Not collected (checked)

Real name, email, phone number, contacts (no Contacts permission), precise or coarse location (no location permission), reading Photos,
advertising identifier, purchase data (no in-app purchases; `UnityPurchasingSettings` is off), health data. No payments, prizes or gambling.

## Permissions in the plist vs what the code asks for

| Key | Prompt appears when | Note |
|---|---|---|
| Game Center sign-in (not a permission) | Onboarding "account" step: Sign in, or Later | Guests can play |
| `NSLocalNetworkUsageDescription` | First nearby-party browse or host | |
| `NSCameraUsageDescription` | First tennis match (court scan) | Denied → "Physical steering needs the rear camera". There is no touch fallback any more |
| `NSGKFriendListUsageDescription` | Opening Friends | |
| Notifications | After your first invite | |
| `NSMicrophoneUsageDescription` | First tap on the party mic | |
| `NSPhotoLibraryAddUsageDescription` | "Save Video" from the share sheet | |
| `NSMotionUsageDescription` | **Probably never.** The code uses only `CMMotionManager` device motion, which needs no permission. There is no `CMMotionActivityManager`/`CMPedometer`/`CMAltimeter` | Verify on device. The review notes no longer promise this prompt |

## Old names still visible in the app (out of scope here; flagged)

- Permission strings say "Motion Club": microphone, Photos, Game Center friends and local network (`project.yml:31-32`, `GolfArcade/Unity/SportsInfo.plist`).
- Invite texts say "Motion Club" (`FriendsSource.swift:140`, `ClubCloud.swift:217`). **These go to people outside the app.**
- The report text and subject say "Motion Club report" (`PartySafety.swift:206,245`).
- The URL scheme is `motionclub://`, and the recording folder is `MotionClubRecordings`. These are internal and not shown to users.
- `ClubSupportEmail`, `ClubSupportURL` and `ClubPrivacyPolicyURL` are empty in `SportsInfo.plist`, so the in-app privacy link is missing and reports go by
  SMS to a personal phone number.

## Build 9 note

Build 0.1.5 (9) was archived before CloudKit was switched on (`ClubCloudContainer` was empty then). In that build, features #8–#9 stay
dormant and text invites fall back to the share sheet. The current tree has CloudKit on. The policy describes the current tree,
because that is what will ship.

## Decisions (Adnan, 2026-10-28)

- No business address yet, and no EU/UK representative. The policy shows a contact email only.
- iCloud Player/Party records are kept indefinitely, with no automatic expiry, until the player asks for deletion by email.
- US state privacy laws are not thought to apply. The policy keeps a short, plain rights section (access, correction, deletion; no sale or
  sharing) instead of a CCPA/CPRA breakdown. The GDPR section was removed.
- The demo video stays as it was.
- **Policy follows Adnan, not the code (2026-10-28):** the public pages say there is no voice chat and typing is 18+ only. **The code still differs.**
  Party voice is reachable: the mic button shows whenever the player is in a party (`PartySettingsView.swift:134,148`, `PartyChatView.swift:62`).
  13–17-year-olds can type: `PartySafety.access` gives `.teen` `.full` (`PartySafety.swift:93-99`). Rows #12 and #14 above describe the code. Change the
  code before release, or the policy is inaccurate.

## App Store Connect: App Privacy answers

Basis: Apple's definition of "collect" is data transmitted off the device that we or a third-party partner can access for longer than real-time servicing.

| Data type | Collected? | Linked to user | Tracking | Purpose | Why |
|---|---|---|---|---|---|
| Identifiers › User ID | Yes | Yes | No | App Functionality | Game Center player IDs and display name in the CloudKit `Player`/`Party`/note records (#8) |
| Usage Data › Other Usage Data | Yes | Yes | No | App Functionality | Online state, last-seen time and party size in the `Player` record (#8) |
| Diagnostics › Other Diagnostic Data | Yes | No | No | Analytics | Unity engine hardware statistics (#21). Remove this row if `submitAnalytics` is set to 0 |
| Everything else (contact info, location, contacts, user content, audio, photos, browsing, purchases, health, financial, sensitive) | No | | | | Chat and voice are real-time only. Camera and motion stay on the device. Reports and diagnostics are optional and user-initiated (sent from Messages, Mail or the share sheet) |
