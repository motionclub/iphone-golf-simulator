# Dead-code removal plan (NOT applied)

Generated 2026-10-03 by a read-only dry run: a top-level Swift declaration is dead when nothing in `GolfArcade/` (app, Objective-C bridge) references it outside its own block; removal is repeated until nothing new turns dead (5 rounds). Nothing was written to disk.

Recoverable snapshot of every tracked-file change taken before any removal: `git show refs/backups/pre-dead-code-20261003` (made with `git stash create`; the working tree was not touched). A Swift-only tarball is in the session scratchpad.

## Menu / UI layer (what the audit called dead) — about 2,700 lines

* **ArcadeScreens.swift** — 837 lines: `TitleScreen`, `MainScreen`, `PartyLobbyScreen`, `QuickPlayScreen`, `PlayerChip`, `StatsStrip`, `GameSelectScreen`, `HubScreen`, `LockedScreen`, `ExhibitionScreen`, `CharacterScreen`, `HowToScreen`, `GolfLessonScreen`, `ConnectScreen`, `ProgressBar`, `ArcadeLogo`, `BrollReel`, `LobbyBackdrop`, `LobbyAction`, `KitPreview`, `CardPager`, `EmptyVenueBackdrop`, `LobbyStyle`, `LobbyButtonStyle`
* **ClubScreens.swift** — 644 lines: `ClubTitleScreen`, `ClubHomeScreen`, `ClubGameSelectScreen`, `ClubHubScreen`, `ClubLadderScreen`, `ClubTrainingScreen`, `ClubSettingsScreen`, `ClubGuideScreen`, `ClubConnectScreen`, `ClubStoryScreen`, `ClubResultsScreen`, `CharacterSizeControl`
* **PlayfulGraphics.swift** — 355 lines: `SunnyBackdrop`, `BouncingBall`, `FloatingConfetti`, `JellyButton`, `SpeechBubble`, `JellyPress`, `Wiggle`, `Triangle`, `ShowroomBackdrop`, `SlabButton`, `BallArt`, `SlabPress`, `Playful`, `BallKind`
* **TennisMenuViews.swift** — 287 lines: `TennisLogo`, `CampaignScreen`, `TrainingScreen`, `ResultsScreen`, `StoryScreen`, `OpponentDetail`, `AirPlayButton`, `Confetti`
* **PostMatchScreen.swift** — 277 lines: `ClubPostMatchScreen`, `LevelUpOverlay`, `LevelBadge`
* **HowToCards.swift** — 133 lines: `HowToCardView`, `LoopingVideo`, `HowToArt`, `LoopingPlayer`
* **ClubDesign.swift** — 81 lines: `ClubWipe`, `ClubPill`, `ClubRow`
* **TennisMapScreen.swift** — 64 lines: `ClubMapScreen`
* **TennisMenu.swift** — 1 lines: `ArcadeMenu`

Total 2679 lines. Files that would end up empty: `PostMatchScreen.swift`. Test-only reference: `LoopingVideo` (2 refs).

## Old golf simulator core — NOT part of the menu cleanup, needs your call

These are unreachable from the current app root but are the original golf simulator's swing / shot logic, and have unit tests:

* **SwingStateMachine.swift** — 169 lines: `SwingStateMachine` (tests: 4)
* **ArcadeView.swift** — 167 lines: `ArcadeView`
* **ShotEngine.swift** — 80 lines: `ArcadeShotEngine` (tests: 1), `ShotResult`, `ShotShape`
* **ArcadeGameSession.swift** — 66 lines: `ArcadeGameSession`
* **SwingFeedbackOverlay.swift** — 56 lines: `SwingFeedbackOverlay`
* **RangeView.swift** — 35 lines: `RangeView`
* **ShotResultCard.swift** — 31 lines: `ShotResultCard`
* **FlightPath.swift** — 21 lines: `FlightPath` (tests: 1)
* **SwingMetrics.swift** — 17 lines: `SwingEvent` (tests: 2), `SwingMetrics` (tests: 4)

Total 642 lines. Recommendation: keep until you decide the old golf simulator is retired.

## Assets (not touched)
* `Club_entrance/loading/terrace` environment JSON + albedo (~62 MB, only tests load them), `PlayerMale*/PlayerFemale*` JSON (~22 MB), `HeroV4.bin` (7.9 MB), `island-*.png` (7.5 MB), `menu-hero-*` + `menu-trophy` (6.9 MB, story/ladder illustrations), `MenuVideo` (39 MB, excluded from the target).
