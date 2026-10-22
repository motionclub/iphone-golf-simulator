# Party Sports onboarding review — incomplete

Owned onboarding implementation and proof reports are staged on `newmapsandmenus`. Nothing is committed or pushed. The final gate is not met.

Implemented: persistent first-run routing, Game Center/guest account flow, character setup, TV/Mac connection instructions and motion primer, Tennis/Golf picker, tutorial routing/controllers, once-only XP/reward persistence, hub routing, replay, and local analytics. White-headband rendering, complete playable lessons, current integrated device export, and complete phone/TV recordings remain blocked or unverified.

## Validation

- Final focused run: 15 passed, zero failed (14 unit tests plus the actual partial phone setup UI flow). FINAL_owned_summary.json.
- Final source and picker-capture rerun: one UI test passed, zero failed; FINAL_capture_summary.json / FINAL_capture_retry.log. The run ends at the genuine missing-Unity error.
- Xcode's optional Simulator diagnostics collector was stopped after the test passed to allow the result bundle to finalize; xcodebuild exited successfully and the exported summary confirms the passing test.
- Full native regression: 422 passed, 9 failed, 3 skipped (434 total); all eight existing native failure names and the existing navigation failure match baseline. P10_native_summary.json and P10_native_comparison.txt.
- Unity EditMode: 257 passed, zero failed versus baseline 253. P10_editmode.xml. Compile helper retains the same 10 pre-existing errors; P10_check_comparison.txt.
- Actual tennis PlayMode: 0/4 full tutorial checks and 0/1 ten-seed Point harness passed. First real contact occurred at 5.686 seconds; later Aim stalls. Ten seeded point attempts produced zero wins; the no-swing attempt did not finish in 90 simulated seconds. P6_PlayMode_final and P6_Points XML/logs.
- All 1,664 baseline staged paths remain staged. Original foreign hunks in all 17 inspected shared paths are preserved; new owned files match their index copies; owned whitespace check passes. FINAL_staging-audit.json and P10_foreign-hunks-preserved.json. Full native tests generated unowned snapshot/video outputs listed in P10_new-unowned-working-paths.txt; these were left unstaged. The literal P10.3 global subset cannot pass while preserving the pre-existing index.

## Every gate

Each proof path below is relative to `work/onboarding/` in the repository. Phase reports give exact commands, raw result paths, and limitations.

| Gate | Result | Proof file |
|---|---|---|
| P0.1 | PASS | P0_RESULT.md |
| P0.2 | PASS | P0_RESULT.md |
| P1.1 | PASS | P1_RESULT.md |
| P1.2 | PASS | P1_RESULT.md |
| P1.3 | FAIL(BLOCKED-OWNER) | P1_RESULT.md |
| P2.1 | PASS | P2_RESULT.md |
| P2.2 | FAIL(BLOCKED-OWNER) | P2_RESULT.md |
| P2.3 | FAIL | P2_RESULT.md |
| P2.4 | PASS | P2_RESULT.md |
| P3.1 | PASS | P3_RESULT.md |
| P3.2 | FAIL(BLOCKED-OWNER) | P3_RESULT.md |
| P3.3 | PASS | P3_RESULT.md |
| P4.1 | PASS | P4_RESULT.md |
| P4.2 | FAIL | P4_RESULT.md |
| P4.3 | FAIL | P4_RESULT.md |
| P4.4 | FAIL(BLOCKED-OWNER) | P4_RESULT.md |
| P4.5 | PASS | P4_RESULT.md |
| P4.6 | N/A | P4_RESULT.md |
| P5.1 | FAIL(BLOCKED-OWNER) | P5_RESULT.md |
| P6.1 | PASS | P6_RESULT.md |
| P6.2 | FAIL | P6_RESULT.md |
| P6.3 | FAIL(BLOCKED-OWNER) | P6_RESULT.md |
| P6.4 | FAIL(BLOCKED-OWNER) | P6_RESULT.md |
| P6.5 | FAIL | P6_RESULT.md |
| P6.6 | FAIL(BLOCKED-OWNER) | P6_RESULT.md |
| P7.1 | FAIL(BLOCKED-OWNER) | P7_RESULT.md |
| P7.2 | PASS | P7_RESULT.md |
| P7.3 | FAIL | P7_RESULT.md |
| P8.1 | PASS | P8_RESULT.md |
| P8.2 | FAIL | P8_RESULT.md |
| P8.3 | FAIL(BLOCKED-OWNER) | P8_RESULT.md |
| P8.4 | FAIL | P8_RESULT.md |
| P9.1 | PASS | P9_RESULT.md |
| P9.2 | PASS | P9_RESULT.md |
| P9.3 | PASS | P9_RESULT.md |
| P9.4 | FAIL | P9_RESULT.md |
| P10.1 | FAIL(BLOCKED-OWNER) | P10_RESULT.md |
| P10.2 | FAIL(BLOCKED-OWNER) | P10_RESULT.md |
| P10.3 | FAIL(BLOCKED-OWNER) | P10_RESULT.md |
| P11.1 | FAIL | P11_RESULT.md |

## NEEDS_OWNER.md contents

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

## Exact files staged by this chat

The pre-existing 1,664 staged paths are recorded separately in baseline-staged.txt; they were preserved. This list contains only this chat’s 53 staged paths (33 code files plus proof reports/metadata). No generated projects, build products, xcresult bundles, test-generated foreign assets, or movies are staged.

```text
GolfArcade/Onboarding/Analytics.swift
GolfArcade/Onboarding/GameCenterAccount.swift
GolfArcade/Onboarding/GolfTutorialController.swift
GolfArcade/Onboarding/OnboardingAccountScreen.swift
GolfArcade/Onboarding/OnboardingCharacterScreen.swift
GolfArcade/Onboarding/OnboardingConnectScreen.swift
GolfArcade/Onboarding/OnboardingFlow.swift
GolfArcade/Onboarding/OnboardingGamePicker.swift
GolfArcade/Onboarding/OnboardingMotionPrimer.swift
GolfArcade/Onboarding/OnboardingRewardScreen.swift
GolfArcade/Onboarding/OnboardingRoot.swift
GolfArcade/Onboarding/OnboardingStore.swift
GolfArcade/Unity/HowToCards.swift
GolfArcade/Unity/IslandScreens.swift
GolfArcade/Unity/Progression.swift
GolfArcade/Unity/SportProgress.swift
GolfArcade/Unity/SportsHome.swift
GolfArcade/Unity/SportsSession.swift
GolfArcade/Unity/TennisMenu.swift
GolfArcade/Unity/TennisPlayViews.swift
GolfArcade/Unity/TennisStory.swift
GolfArcadeTests/AnalyticsTests.swift
GolfArcadeTests/OnboardingTests.swift
GolfArcadeUITests/OnboardingUITests.swift
Unity/Assets/Scripts/Game/GolfGame.cs
Unity/Assets/Scripts/Game/GolfTutorial.cs
Unity/Assets/Scripts/Game/GolfTutorial.cs.meta
Unity/Assets/Scripts/Game/NativeSportsSession.cs
Unity/Assets/Scripts/Tennis/TennisTutorial.cs
Unity/Assets/Tests/EditMode/GolfTutorialTests.cs
Unity/Assets/Tests/EditMode/GolfTutorialTests.cs.meta
Unity/Assets/Tests/EditMode/TennisTutorialTests.cs
Unity/Assets/Tests/PlayMode/TennisTutorialPlayTests.cs
work/onboarding/BASELINE.md
work/onboarding/FINAL_RESULT.md
work/onboarding/FINAL_capture_summary.json
work/onboarding/FINAL_gates.json
work/onboarding/FINAL_owned_summary.json
work/onboarding/FINAL_staging-audit.json
work/onboarding/NEEDS_OWNER.md
work/onboarding/P0_RESULT.md
work/onboarding/P10_RESULT.md
work/onboarding/P11_RESULT.md
work/onboarding/P1_RESULT.md
work/onboarding/P2_RESULT.md
work/onboarding/P3_RESULT.md
work/onboarding/P4_RESULT.md
work/onboarding/P5_RESULT.md
work/onboarding/P6_RESULT.md
work/onboarding/P7_RESULT.md
work/onboarding/P8_RESULT.md
work/onboarding/P9_RESULT.md
work/onboarding/staged-onboarding-files.txt
```

## Required walkthrough paths

Neither file exists yet. Both must contain actual completed gameplay and receive Adnan’s approval.

```text
/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/onboarding/WALKTHROUGH_phone.mov
/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/onboarding/WALKTHROUGH_tv.mov
```

Available recording: `SETUP_ONLY_phone.mov` covers setup and stops at the native-only runtime limitation. It is not a P11 walkthrough. Resume screenshots use DEBUG seeded steps and do not prove tutorial completion. No app was removed from or installed on Adnan’s physical iPhone.
