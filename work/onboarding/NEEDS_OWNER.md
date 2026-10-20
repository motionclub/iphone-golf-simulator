# Onboarding owner dependencies

## Unity/Tools/check.sh — URP compiler references
The required baseline helper fails before tests: 10 missing URP/Volume reference errors (see P0_unity-check.log). Smallest change: include the imported core/URP assembly references. This tool is outside the owned list. P0.1 passes because the baseline failure is recorded; the helper remains failing in P10.1. Actual Unity Editor EditMode baseline passes 253/253.

## GolfArcade/Domain/Player.swift, GolfArcade/Unity/LockerCatalog.swift, MatchHero*.swift, Unity/Assets/Scripts/Tennis/TennisRoster.cs — white headband
Add an optional backward-compatible headwear field, a white Sweatband catalog item/headwear slot, and render the equipped item on native preview and match heroes. The current public APIs provide no supported headwear equipment path. Implement reward persistence and requested-equip record in owned onboarding code; P8.3 remains FAIL(BLOCKED-OWNER) until the real hero wears it in both places.

## Unity/Assets/Scripts/Game/GolfGame.cs / course owner — Cliffside tutorial course
The baseline now loads Course.Postcards(), replacing the brief’s assumed Course.Cliffside(). The course setup lines are foreign changes; R3/R5 prohibit modifying them. Need a public tutorial-only hook to select existing Cliffside hole 1 before setup, retaining current course selection for normal play. P7.1 cannot certify the required Cliffside lesson until provided.

## GolfArcade/Unity/SportsMotion.swift — camera analytics
Actual camera request is inside this unowned file. Need a single analytics callback at request/result, guarded by motion tutorial setup. Observation from onboarding can report authorization state, but cannot prove the actual request event. Camera prompt analytics remains unverified without this hook.

## GolfArcadeUITests/SportsNavigationTests.swift — legacy navigation assertions
The unmodified baseline UI test testNativeMenuHasNoScanGateAndExplainsMissingUnity fails at line 61 expecting the obsolete Sports Arcade Form; the current baseline opens the Island title/menu. See P0_navigation_retry.xcresult and original-build log. Smallest owner change: seed -skipOnboarding and assert the current Island menu/real missing-Unity flow. This file is outside §4. P1.3 remains FAIL(BLOCKED-OWNER) because “SportsNavigationTests still pass” is already false before onboarding. Other regressions will still be compared in P10.

## GolfArcade/Unity/SportsRuntime.mm / runtime owner — Simulator gameplay
The documented native-only Simulator project has no Unity runtime. Actual interactive tutorial completion and a full recorded no-TV walkthrough require the integrated physical-device build (or a supported Simulator Unity framework from the runtime owner). Do not fabricate tutorialDone events to pass gates. Simulator setup UI can be tested; P2.2’s full guest-to-done UI run and P11’s complete tutorial walkthrough remain unverified until real gameplay runs.

## GolfArcade/Unity/CharacterModelPreview.swift / MatchHero*.swift and character owner — selected hairstyle visibility
The actual onboarding capture P3_attachments/796643A9-7619-4177-9125-A5298E189BD0.png shows Hair: Bob with a bald hero. Existing public Player hair setters persist the selection; the current match-hero preview does not show that hairstyle. Need owner wiring for separate optional hairstyle meshes/tints in native preview and first tutorial match, preserving locked bald base geometry. P3.2 is FAIL(BLOCKED-OWNER) until a preview/match screenshot pair proves the saved hair/skin/body/name visually match.
# SportsDisplays.swift — on-phone tutorial controls

The Unity preview installs `SportsPreviewControls`, which owns a second set of court-position and power sliders and bypasses the owned TennisRacketController/GolfPhoneController. Smallest requested diff: during tutorial mode render the owned tutorial controls (or expose a public controller-view provider) and hide court-position/power sliders. This file is read-only under §4. P6.3 on-phone controls and P7.1 phone walkthrough remain FAIL(BLOCKED-OWNER) until the preview hook exists.
# NativeSportsSession.cs — tennis success/skip analytics bridge

TennisTutorial now publishes StepResolved(index, misses, skipped), and Swift accepts tutorialSuccess/tutorialSkip. §4 limits this shared bridge to tutorialStart reads and golf tutorial event emission. Its owner needs to subscribe to TennisTutorial.StepResolved and emit those two messages (one additive line). Until that hook is authorized/provided, actual tennis success/skip analytics cannot be certified. No forbidden shared bridge line was changed.
# GolfGame / NativeSportsSession owners — tutorial hole reset and skip

The new golf component isolates practice → changed aim → six-stroke hole logic, but GolfGame exposes no public restart/current-course selector. Need a tutorial-only `BeginTutorialHole(Cliffside, 0)` hook after the aim exercise so practice strokes do not alter the playable hole, and NativeSportsSession’s tutorialNext command must route to GolfTutorial.SkipStep. Those behavior/command regions are outside §4’s additive read-only GolfGame hooks and limited bridge regions. P7.1 stays FAIL(BLOCKED-OWNER). The new logic is not proof that the required Cliffside hole runs.
# SportsSession.swift — touch with an attached display

The brief’s required `onPhone: !displayConnected || touch` launch formula reaches `start(preview: true)` when a player chooses touch with a TV connected; the existing start guard rejects that combination. The start/preview window region is outside the owned launchExtras/event regions. Requested owner hook: allow on-phone touch preview while an external display exists, or define the supported touch-on-TV launch API. P4.4/P6.4 cannot certify that path until resolved.

# Unity export / build script owners — locked asset regeneration

BuildMenu.BuildIOS calls TropicalArenaImporter.Prepare, which writes shared material/kit resources; build-integrated-ios.sh and install-phone.sh regenerate shared GolfArcadeUnity.xcodeproj outside §4. R5 prohibits regenerating those locked assets and R4 restricts new files. Need an owner-produced current Unity export (including GolfTutorial and new tennis lesson) and an isolated output option for the existing build/install scripts. An isolated native project can compile without touching shared projects, but installing the stale existing Unity export would not verify this work. P10.2 remains FAIL(BLOCKED-OWNER) until a current export is available.
# Tennis gameplay / character owners — real tutorial returns

P6_PlayMode/playmode.xml records three real failures: the unchanged generic good-timing left-target test fails, the revised full lesson gets stuck at Aim after actual Forehand/Backhand returns, and the unchanged customized-character test cannot find Curls. Need gameplay/rig owners to restore reliable good-timing returns to the left target and visible hair. Do not weaken physics assertions or simulate success. P6.2/P6.3/P6.4 and P10.1 cannot pass without the complete real lesson and device proof.
# TennisGame / serve owner — tutorial Point remains unfriendly

P6_Points/playmode.log records all 10 seeded on-time harness attempts: 0/10 wins (every point went to the opponent). The no-swing run also remained unfinished after 90 simulated seconds. This is an actual failing test, not completion proof. Need an owner fix to the normal tutorial-guarded serve/point behavior or an approved public test driver for on-time serving; TennisServeRoutine/actor/driver and gameplay physics are locked. P6.6 is FAIL(BLOCKED-OWNER).
# Regression proof outputs / index ownership

The required full native baseline/regression suites regenerate their existing screenshot/video outputs in unowned ArtDir folders. These paths are listed in P10_new-unowned-working-paths.txt; they were not staged, overwritten back, or deleted by this chat. Snapshot-test owners should expose an output-directory override so later runs can write under work/onboarding. Also 1,664 foreign paths were already staged before this chat; R2 prohibits removing them, so the literal global cached-path subset in P10.3 cannot pass. Own added code staging uses a patch mapped to the initial index, and all foreign shared-file hunks are preserved (P10_foreign-hunks-preserved.json).
