# Gate results — PLAN_FinalLook_Gameplay_2026-11-11.md

Last updated 2026-11-11 23:15. Everything below is in `Unity/`, uncommitted. `ROLLBACK.sh` in this folder puts every file back as it was before Phase 0 started.

**How it was checked.** Two copies of the project in `~/unity-clones/`: `final-plan` (the project as it stood at the start, plus the one skirt fix) and `final-plan-dev` (with the Phase 1 changes). Nothing ran in the shared project. Nothing has run on a phone or a TV.

## Phase 0 — Baseline and budget

| Gate | Result |
|---|---|
| Test suites green, or each failure listed with its cause | **PARTLY.** EditMode PASS (758 of 758 at the start, after one fix). PlayMode: six of seven batches listed below (39 failures, two with causes); the seventh is running again |
| A table of measured frame times per sport and device | **FAIL — not measured.** Needs the phone and TV, and the minimum devices named (decision 9). Mac-editor frame times are in (below): they show no change from Phase 1 and are not a device budget |

### EditMode at the start: 758 tests

First run: 754 passed, 4 failed.

| Failure | Cause | Outcome |
|---|---|---|
| `FemaleDeformationTests.NeutralSkirtAndUnderShortsKeepTheirOriginalBinding` | Real defect from the 11-11 build install. The arm-shaping field also moved 1,507 of her skirt's 10,185 vertices by up to 18 mm (and his shorts), where the hands hang beside the hips at rest | Fixed in `HeroBuild.cs`: a garment with no arm weights takes no arm shape |
| `HeroAssetRegistryTests.NoCodeOutsideTheRegistryNamesAnOlderHero` | The project copy had no sibling `GolfArcade/` folder for the test to read | Copy re-arranged; passes |
| `NetworkViewTests.TheOneTVFixtureWrittenBySwiftParsesAndIsValid` | Same: no sibling `proof/` folder | Passes |
| `TennisLatencyTests.ProvenThresholdsMatchThePhonesPeakConfirmation` | Same | Passes |

Second run: 758 of 758.

### PlayMode at the start

A single run of all 94 files grew to 16 GB of memory in one Unity and had to be stopped. It now runs in seven batches, one Unity each, with capture and film tools left out (31 classes; they are listed in `playmode_chunks.sh`).

| Batch | Result at the start (before Phase 1) |
|---|---|
| tennis1 (5 classes, 32 tests) | 28 passed, 4 failed |
| tennis2, heroes, golf1, golf3, hub | finished: see the complete table below |
| golf2 (8 classes, 20 tests) | 18 passed, 2 failed (run 22:39 with the filter fixed; see below) |

Failures in tennis1, all present before any Phase 1 change:

| Failure | Cause |
|---|---|
| `TennisGameplayTests.ApprovedArenaAndBothStandardsRunTennisPhysics` | Stale test: it looks for a renderer named "V4 Higgs body", a hero that was replaced |
| `TennisGameplayTests.RallyStartsWithVisibleServeThenPlayableBall` | The player moved 0.86 m toward a wide ball where the test wants 1 m. Cause not found yet |
| `TennisGameplayTests.StrengthAndPhonePositionChooseReadableStrokes` | Expected a backhand, got a forehand. Cause not found yet |
| `TennisPolishPlayTests.CaptureOpponents` | "Milo should wear their own body". Cause not found yet |

### PlayMode at the start, complete (run finished 2026-11-11 19:58)

Code as it stood before Phase 1 (the baseline copy). Six of seven batches reported: **189 tests, 147 passed, 39 failed, 3 skipped.** The seventh (golf2: NewHoles, Playthrough, RoundEvents, RoundSmoke, SolidProps, SwingSmoothness, Replay, ArcadeCards) was stopped by the machine's memory brake at 16:55, and again at 21:32 on the changed code. **Cause found 22:10: my mistake in the batch list.** It named `ClassicConditionsForTests`, which is not a test class but the suite-wide set-up fixture; naming it made Unity run every PlayMode test (capture tools included) in one process, the very thing the batches exist to avoid. The name is removed; the batch then ran in about 16 minutes on each copy (below).

| Batch | Tests | Passed | Failed | Skipped |
|---|---|---|---|---|
| tennis1 | 32 | 28 | 4 | 0 |
| tennis2 | 34 | 26 | 8 | 0 |
| heroes | 20 | 14 | 6 | 0 |
| golf1 | 25 | 15 | 10 | 0 |
| golf3 | 17 | 12 | 5 | 0 |
| hub | 61 | 52 | 6 | 3 |

Every failure below was present before any Phase 1 change. Causes are filled in only where the message makes them plain; the rest are **not investigated yet**.

| Batch | Test | What it reported |
|---|---|---|
| tennis1 | `TennisGameplayTests.ApprovedArenaAndBothStandardsRunTennisPhysics` | tennis characters should have visible arms |
| tennis1 | `TennisGameplayTests.RallyStartsWithVisibleServeThenPlayableBall` | auto-positioning must chase a wide ball (flow=PointOver predicted=-100.00 ball=(4.00, 0.29, -12.63) x=3.21 start=2.35) |
| tennis1 | `TennisGameplayTests.StrengthAndPhonePositionChooseReadableStrokes` | Expected: String containing "backhand" |
| tennis1 | `TennisPolishPlayTests.CaptureOpponents` | Milo should wear their own body |
| tennis2 | `NativeTennisSetupTests.PointWinnerStaysVisibleAndCelebrationsHoldTheNextServe` | Point stays open for at least five real seconds |
| tennis2 | `TennisGameplayImprovementPlayTests.LiveCourtUsesScoreOnlyAndSteadyShoulderCamera` | Label:SET 1 / Label:COACH / Label:0 / Label:SUPER SHOT / Label:GAMES / Label:0 / Label:TRAINING  ·  FREE RALLY / Label:0 / Label:0 / Label:YOU / Label |
| tennis2 | `TennisGameplayImprovementPlayTests.NativePracticeCommandsCanPauseRetryAndSwitchToTouch` | Expected: False |
| tennis2 | `TennisTutorialPlayTests.CompleteTheWholeLessonWithRealShotsAndNoSkipping` | net faults retry with coaching |
| tennis2 | `TennisTutorialPlayTests.CustomizedCharacterKeepsRigAndRacket` | Expected: not null |
| tennis2 | `TennisTutorialPlayTests.TenSeededPointsWinWithOnTimeSwingAndNoSwingStillFinishes` | seed=10 did not finish |
| tennis2 | `TennisVenueTests.SkyscraperBallPastTheEdgeFallsAndIsCalledOut` | it should keep falling |
| tennis2 | `TennisVenueTests.VolcanoBallPastTheEdgeFalls` | Expected: less than -5.0f |
| heroes | `GolferSelectTests.MakingAGolfer` | no Segment Shorts on the screen |
| heroes | `HeroGarmentRuntimeOrderTests.LiveDriverGarmentsUseThisFramesFinalPose` | Expected: not null |
| heroes | `HeroGolferTests.EveryClubSwings` | wedge-half: the club starts at the ball (0.56 yd) |
| heroes | `HeroGolferTests.EveryLookBuilds` | Face is in the build |
| heroes | `MatchHeroClipMapTests.EveryStrokePlaysItsOwnMatchClipOnBothSexes` | ready / idle is ReadyIdle |
| heroes | `NativeLaunchHeroTests.HeroSurvivesTheNativeLaunchPath` | System.IO.DirectoryNotFoundException : Could not find a part of the path "/Users/adnanyonathan/unity-clones/final-plan/ArtDir/score80/native_launch_ru |
| golf1 | `GolfAnimationFlowTests.RoutineResultsAdvancePromptlyButChosenEmotesFinish` | Expected: True |
| golf1 | `GolfBroadcastTests.AFullSwingIsReplayedFromTheTeeBoxThenWatchedLanding` | the result waits for the replay |
| golf1 | `GolfBroadcastTests.FlightCutsOnceAtLandingThenBothGolfersCanEmoteAndContinue` | shot heading reversed |
| golf1 | `GolfBroadcastTests.OffCourseProjectionsAndAllClubChangesStayVisible` | Expected: True |
| golf1 | `GolfCourseStandardPlayTests.UpgradePreservesGroundObstaclesAndHazardsAcrossTheCatalog` | Expected: 22 |
| golf1 | `GolfPolishTests.DetailedBodiesAndEveryClubClearTheHead` | Expected string length 26 but was 23. Strings differ at index 11. |
| golf1 | `GolfPolishTests.LandingMarkersMatchPowerAndCameraHoldsTheGolfer` | map marker must be the club's still-air carry from this lie |
| golf1 | `GolfPresentationTests.LiveShotsHoldThenFollowWithoutReversingOrRolling` | hole 7 camera reversed at 4.35s |
| golf1 | `GolfPresentationTests.SwingToResultShowsStatsAndLetsBothGolfersEmoteUntilContinue` | result must face the character |
| golf1 | `NativeGolfFlowTests.PhoneCommandsAimChangeClubsPauseAndLaunchWithoutCalibration` | Expected: Flight |
| golf3 | `DreamGolfPilotTests.DressingPreservesPhysicsAndBallReadabilityAndLeavesWithTheHole` | System.ArgumentException : An item with the same key has already been added. Key: COLLIDER_CHALK_FACES |
| golf3 | `IntroRulesPlayTests.GolfSkipLandsOnTheGolferWhoEmotesOnlyWhenTheirPlayerPicks` | skip lands on the golfer's introduction, not past it |
| golf3 | `MagmaOpenTests.TheHolesFloatInTheCrater` | hole 21: the fire's sky |
| golf3 | `PresentationFlowTests.GolfOverviewSkipConsumesMotionUntilAQuietPose` | Follow-through must not become a new ready pose |
| golf3 | `WildIslesPlayTests.EarningThings` | beaten Cliffside: open |
| hub | `BigScreenFlowTests.TheRoundStartsFromThePhoneWithTheCourseOnTheTv` | the tournament title is up over the flyover |
| hub | `ErrorHandlingTests.OnlineAtHomeCopes` (skipped) | no game server running on this Mac |
| hub | `ExperienceFlowTests.OrdinaryResultsSkipAtHalfSecondAndAutoAdvanceAtThree` | automatic reading window stays three seconds |
| hub | `HubPartyTests.FourHeroesStaySmoothAndFriendsAreDrawnWhereTheyWere` | four heroes keep the frame rate (editor) |
| hub | `HubPartyTests.FriendsCanWalkEmoteChatAndGather` | remote movement is rendered |
| hub | `HubPartyTests.OnlineTennisWearsTheLobbyLooks` | your shirt colour |
| hub | `HubPartyTests.PartyStills` (skipped) | HUB_LOOK_DIR not set |
| hub | `HubPlazaTests.SoakHoldsFrameRate` | the plaza holds 60 fps in the editor soak |
| hub | `MenuPointerTests.FilmEveryScreen` (skipped) | ML_OUT not set |

Plain from the message: `ApprovedArenaAndBothStandardsRunTennisPhysics` looks for a renderer of a hero that was replaced (stale test); `NativeLaunchHeroTests.HeroSurvivesTheNativeLaunchPath` wants an `ArtDir/score80` folder the project copy does not have (set-up, not the game); the three skips need a game server or an output folder; the two frame-rate failures (`HubPartyTests.FourHeroesStaySmooth…`, `HubPlazaTests.SoakHoldsFrameRate`) come from a batch that waited about 2.6 hours at the memory gate before it could start, so the Mac was short of memory around it and I do not trust them either way.

### PlayMode after Phase 1, against the start (run finished 2026-11-11 21:58)

The same six batches on the changed code (`pm_compare.py pm-base pm-new` prints this): **189 tests, 146 passed, 40 failed, 3 skipped**, against 147 / 39 / 3 at the start. golf2 follows in its own table.

| Change | Test | What happened |
|---|---|---|
| Passed before, fails now | `HubBayTests.StandingUpMidLoadLeavesNothingLoaded` | Fails on `TennisGame.SliceInit` still being set two frames after the phone stands up 0.4 s into a load. The code on that path (`NativeSportsSession.Hub.cs`, `HubWorld.cs`) is identical in both copies, and the check depends on how far the load got in 0.4 s; that run was also slow (35.9 fps where the baseline had 48.1). **Settled 22:55: the test is unsteady on both copies, not broken by Phase 1.** Run alone it passed once and failed once on the changed code, and failed on the baseline, each time on the same line. It checks the flag two frames after standing up, while the cancel first waits for the scene load to finish; whether that fits in two frames varies. Whether the test or the cancel should change is not decided |
| Failed before, passes now | none | |
| Replaced | `IntroRulesPlayTests.TennisIntroductionsWaitForAPickAndVersusNeedsBothPhonesToSkip` → `TennisShowRunsSixSecondsAndOnePlayersSkipEndsIt` | The old rule's test is gone with the rule; the new one passes in the game |
| Fail on both sides | 38 tests | Same assertion on each. Numbers moved a little in 9 of them (for example the wide-ball chase 3.21 → 3.05 m against a 3.35 m limit; the map marker error 0.68 → 0.20 yd against 0.001), none across its limit |

**golf2, both copies (finished 22:39):** NewHoles, Playthrough, RoundEvents, RoundSmoke, SolidProps, SwingSmoothness, Replay, ArcadeCards: **20 tests, 18 passed, 2 failed on each side.** With it the whole suite is 209 tests: 165 passed, 41 failed, 3 skipped at the start; 164 / 42 / 3 after Phase 1.

| Test | At the start | After Phase 1 |
|---|---|---|
| `ArcadeCardsTests.TheCardsThroughARound` | Fails: "the landing is stamped" | Fails the same way. Cause not looked for |
| `ReplayTests.APureApproachAndAHoledPuttAreReplayed` | Fails late: timed out waiting for the approach's replay | **Fails earlier, and this one is Phase 1's doing:** its set-up asks for a tee shot that pitches at least 8 yd from the pin and still finishes within 3.9 yd. With the old landing a ball ran that far on a green; now it stops. Set-up changed 22:45 (`GolfGame.GreenTarget` also tries landings at the pin; the test falls back to one). Run again 23:10: it now gets past the set-up and fails exactly as at the start (timed out waiting for the approach's replay). That time-out predates Phase 1; its cause is not found |

So Phase 1 broke no PlayMode test that passed before: the one that flipped is unsteady on the baseline too. It also fixed none: the 38 standing failures are still there and still without causes, apart from the two named above.

### Frame times on the Mac editor (2026-11-11 22:00)

`FrameRate60bTests.RuntimeHoldsSixty`, 1920 x 1080, 60 fps target, one quiet Unity, before and after Phase 1. This is the Mac in the editor, not a phone or a TV, so it shows change, not the budget.

| Scene | Before: median fps | Before: slowest 5 % | After: median fps | After: slowest 5 % |
|---|---|---|---|---|
| Tennis intro | 50.7 | 23.8 | 50.7 | 20.2 |
| Tennis match | 56.1 | 44.1 | 58.5 | 45.5 |
| Golf intro | 59.9 | 50.8 | 60.3 | 47.6 |
| Golf hole | 60.3 | 42.6 | 59.9 | 45.3 |
| Plaza | 59.9 | 40.9 | 59.9 | 51.0 |

No change from Phase 1 beyond run-to-run noise (one run each side). Two things stand out on both sides: the tennis intro sits at 51 fps with dips to the low 20s, and the tennis match does not hold 60 even here. Bowling is not in this test, and load times are not measured. Stills: `phase0/frames-base/res1080/`, `phase0/frames-new/res1080/`.

## Phase 1 — Ball and pace

EditMode with all of Phase 1 in: **778 of 778** (20 new tests in `TennisFlightTests.cs` and `GolfLandingTests.cs`). PlayMode on the changed code is running.

### Tennis: a flatter, faster ball

| Measure | Before | Target | Now | Gate |
|---|---|---|---|---|
| Perfect drive peak | 2.54 m | 1.8 m or less | 1.80 m | PASS |
| Average shot peak | 3.3 m | 2.2 m or less | 2.1 m (1.8 m on the ball to 2.4 m for the worst-timed) | PASS |
| CPU drive peak, mean per rival | 2.1–4.2 m | 2.2 m or less | 1.75–1.99 m for nine rivals; Tama 2.29 m | **FAIL for one rival** |
| Second arc after the bounce | 1.7–2.4 m | 1.3 m or less | 0.9–1.2 m (player); 0.66–0.96 m mean per rival, Tama 1.33 m | PASS for nine, **FAIL for Tama** |
| CPU lob | 4.4 m, up to 1 in 4 | 3.5 m or less, at most 1 in 12 | 3.5 m, at most 1 in 12 for every rival | PASS |
| Time from the rival's hit to your contact | fastest 1.15 s | no shorter than that | fastest 1.17 s | PASS |
| A test pins rally peak height | none | exists | `TennisFlightTests` (9 tests) | PASS |

Tama is the "moonballer": every ball it hits carries heavy topspin, which pulls the ball down harder, so the same second in the air takes it higher. I left it at 2.3 m as its character and gave it its own limit (2.45 m) in the test. Say if it should be flattened too.

**What the time gate does not show.** The fastest ball is no faster, but the typical one is: in real-game self-play the median time from the rival's hit to the player's contact went from 1.48 s to 1.31 s. The easier rivals lost the most (Tama 1.72 to 1.28 s, Lina 1.55 to 1.32 s). A ball that peaks at 2 m cannot stay in the air longer than about a second.

**Real game, self-play, standard rival, 100 points per bot:**

| | Before | Now |
|---|---|---|
| Player's rally ball, median top of flight | 2.49 m | 1.62 m |
| Rival's rally ball, median top of flight | 2.65 m | 1.93 m |
| Sharp bot: points won, mean rally | 99, 8.5 shots | 100, 8.3 shots |
| Casual bot: points won, mean rally | 76, 7.5 shots | 81, 6.6 shots |
| Sloppy bot: points won, mean rally | 71, 8.3 shots | 75, 7.7 shots |
| Wide balls returned | 85 of 85 | 90 of 90 |

Proof: `phase1/proof_tennis_before_after.jpg` (ball paths from the real game and frames at the top of each ball's flight).

What changed, all in `TennisFlight` (bottom of `TennisBall.cs`): pace 14 / 18.5 / 21.5 m/s (10 / 13 / 17.5 before); net clearance 0.40 m (1.1 for the player, 0.9 for rivals); the court keeps 54 % of a rally ball's pace and 64 % of its height (94 % and 75 %); a clean ball lands at 9.4 m (10.4); rival pace compressed into 17.5–21.5 m/s; rival legs 0.97 of profile speed (0.76), swept so clean angles win as often as before. Serves are untouched. `TENNIS_CLASSIC=1` in the Editor flies the old ball.

Found on the way and fixed: the swing cue, the player's timing grade, the rival's swing start and the self-play bot all estimated the ball's arrival as distance over present speed. That reads early now that the ball slows at the bounce (the bot's shots went out 1 in 6). They now use one estimate that includes the bounce (`TennisGame.TimeToPlane`).

Older tests changed (8): the pace ratio between a clean and a poor contact is 1.2–1.4× now, not 1.4–1.6× (a flat ball cannot also be a slow one), and "deep" is 9.4 m.

### Golf: a landing that depends on the shot

| Shot | Target | Now | Gate |
|---|---|---|---|
| Full wedge onto a green | First hop 0.5 m or less; stops within 3 yd, or spins back | PW 0.18 m and +1.5 yd; SW +0.4 yd; LW −0.3 yd (figures from the numeric copy; the game's tests hold the limits) | PASS |
| 7 iron onto fairway | One or two hops; 5–10 yd of run | Two hops, 6.2 yd | PASS |
| Driver onto fairway | Skips forward; 15–30 yd of run | Two low skips (0.67 m), 19 yd | PASS |
| Any shot into a bunker | No hop | No hop, 0 yd | PASS |
| Any shot into rough | One dead hop | One hop, 0.1–0.2 m | PASS |
| Upslope against downslope | Upslope clearly shorter | 7 iron and driver: upslope under 75 % of the downslope run (6 % slopes) | PASS |
| The old 2–3 hop test is replaced | — | `GolfLandingTests` (11 tests) | PASS |

Also in: a table per surface (tee, fairway, fringe, green, rough, bunker, out of bounds, ice all differ); each hop judged on the ground it lands on (a 5 iron that pitches on the back of a small green and hops into the rough now dies there); bounce off the real slope; backspin that checks and draws back; landing variation taken from the strike's existing shared scatter, so every phone sees the same bounce. Roll and putting are unchanged.

Proof: `phase1/proof_golf_landing_before_after.jpg`. That chart is drawn from the numeric copy of the code (`phase1/golf_model.py`).

**Filmed in the game (2026-11-11 23:00): `phase1/proof_golf_landing_film.jpg`.** Clone-only harness `phase1/ZGolfLandingFilm.cs.txt`, first hole of the Postcards course, the game's own camera, full swings, wind pinned to still air, old code then new. One shot per club per side.

| Shot (filmed) | Before | After | Against the gate |
|---|---|---|---|
| Lob wedge, 51 yd, onto the green | Highest hop 1.08 m, hopping for 1.28 s, ran 1.9 yd | Highest hop 0.18 m, hopping for 0.42 s, ran 0.2 yd | PASS (hop 0.5 m or less, stops within 3 yd) |
| Pitching wedge, about 102 yd, onto the green | 1.30 m, 1.40 s, ran 3.9 yd | 0.17 m, 0.40 s, ran 1.2 yd | PASS |
| Driver, about 250 yd, onto the fairway | 2.00 m, 1.80 s, ran 20.5 yd | 0.56 m, 0.92 s, ran 12.9 yd | **Under the 15–30 yd target on this one drive.** The tests hold 19 yd on flat fairway; the slope where this drive pitched was not measured, so this is not explained |
| 7 iron, about 135 yd | Pitched in rough: 0.09 m, ran 0.6 yd | Pitched in rough: 0.11 m, ran 0.5 yd | Not a fairway sample (the spot I chose left it short of the fairway): the 5–10 yd fairway gate is **not filmed** |

Carries differ by up to 3 yd between the two sides in still air (driver 250.1 against 253.2); cause not checked. A first take with the hole's random wind left on (6 mph into the wind on one side) is kept in `phase1/golf-film/windy-run1/` and is not a fair comparison.

**Not checked:** the aim preview and shot map on screen. They use the same flight code, so they should agree, but nobody has looked.

**Side effect to know:** the chipper is rated by where it finishes, so its swing was re-calibrated by the new landing: it now carries about 7 yd and runs 18 (it was about 14 and 10).

### Pace: cut the waits

| Wait | Before | Target | Now | Gate |
|---|---|---|---|---|
| Tennis intro | 12.9 s | 6 s or less; any one player can skip | 6.0 s; one swing skips to the call of play, and in versus either phone's skip ends it on both | PASS in code, EditMode and the PlayMode test in the game (`TennisShowRunsSixSecondsAndOnePlayersSkipEndsIt`); **not watched by eye** |
| Tennis pre-serve routine | 2.2 s | 1.2 s | 1.2 s (one bounce of the ball, not two) | PASS in code; **not seen in game** |
| Golf hole flyover | 7.9 s | 4 s, skippable | 4.0 s (short cut 2.1 s); skip rule unchanged | PASS in code; **not seen in game** |
| Golf after holing out | about 5.5 s | 3 s | 1.8 s result + 1.2 s score beat | PASS in code; **not seen in game** |
| Bowling pin sweep | 3.1 s, cannot be skipped | 1.5 s or skippable | 1.5 s | PASS in code; **not seen in game** |
| Bowling strike replay | up to 8 s | 4 s | at most 4 s | PASS in code; **not seen in game** |
| Bowling walk back | about 3 s | covered by the next player's setup | The machine starts 1 s after the result (2 s with a reaction shot); it was 1.9 and 2.8 s | **PARTLY**: shorter, not yet overlapped with the next player's walk-up |

Each highlight in the golf flyover is now 0.8 s (1.7 s before). That may be too quick to read; it is the first thing to look at in game.

## Still open from Phase 0 and 1

- PlayMode: 41 standing failures at the start, two with causes.
- Frame times on the phone and TV (needs you); load times anywhere; bowling frame times.
- Golf: a filmed 7 iron onto fairway, and why the one filmed drive ran 12.9 yd where the target is 15–30. A look at each shortened wait in game.
- The three baseline tennis failures without a cause.

## Phase 2 — Bodies: arms as muscles (step 1 only, awaiting approval)

Built 2026-11-11 in `work/final-plan-1111/phase2/`. **Nothing is installed**: the only change in `Unity/` is an Editor switch (`HERO_BUILD_ARM=0`) that drops the arm term of the 11-11 build so the two can be compared.

- `armfield.py`: the arm's surface as a radius around each bone. A bony core plus one belly per muscle (deltoid outer, front and back heads; biceps; triceps long and lateral heads; brachialis; brachioradialis; forearm flexors and extensors; the point of the elbow), joined so neighbours keep a groove between them. The difference from the current body is a displacement field in the arm's own coordinates, so skin and sleeve move together.
- `render_arm.py`, `arm_gates.py`: Blender renders and the measurements below. Proof: `phase2/proof_arm_muscles_v3.jpg`.

| Gate | Base body | Installed 11-11 build | Muscle model | Result |
|---|---|---|---|---|
| Upper arm clearly thicker than forearm (girth) | 37.5 : 36.5 cm (1.03) | 44.3 : 44.8 cm (0.99) | 41.8 : 34.8 cm (1.20) | PASS |
| Narrow elbow and wrist | elbow 32.9, wrist 22.5 cm | 39.1, 22.7 cm | 33.4, 22.0 cm (elbow 80 % of the upper arm; it was 88 %) | PASS |
| Arm oval in cross-section, not round (deep : wide) | 1.09 | 1.13 | 1.23 | PASS |
| Biceps and triceps separation visible in a rally frame at gameplay distance | | | | **NOT CHECKED**: studio renders only |
| No skin through any garment across the tennis, golf and bowling kits | | | | **NOT CHECKED**: the tennis polo follows in the studio; golf and bowling kits not tried |
| Adnan approves the male arm | | | | **WAITING** |

Known flaws in this version: the grooves also press into the sleeve (a dimple on the front of the polo's shoulder); the edge where the deltoid meets the top of the shoulder is a little sharp; against the tier 1 target the arm is leaner and more cut.

### Second version, 2026-11-12 (the first was rejected)

Adnan on the first version: "you didn't make the bicep bigger or the shoulders corresponding with the forearm ... it needs to be proportional". Measured with the arms hanging, he was right: seen from the front the first version's forearm (12.4 cm) was wider than its upper arm (11.7 cm), and the shoulders had grown 1.5 cm. The bulk it added only showed from the side. The girth gate above passed and still missed this, so the gates below are read from the front and the side, arms hanging.

What changed: the forearm is held at the tier 1 target's fullness (which is the base body's), the upper arm is widened across as well as front to back, and the shoulder cap is grown with its fullest point low so the shoulder line still slopes. Proof: `phase2/proof_arm_muscles_v5.jpg` (`board.py`), numbers from `posed.py`.

| Arms hanging, cm | Base body | In the game today | First version | Second version | Tier 1 target (read off the picture) |
|---|---|---|---|---|---|
| Shoulders, bare | 54.8 | 55.3 | 56.3 | 57.9 | |
| Shoulders, in the polo | 61.9 | 63.7 | 63.1 | 66.1 | 58–59 |
| Upper arm, from the front | 11.7 | 13.0 | 11.7 | 13.4 | 11.3 (at the cuff) |
| Elbow, from the front | 10.7 | 12.1 | 11.7 | 10.8 | 11.3 |
| Forearm, from the front | 12.4 | 14.9 | 12.4 | 12.1 | 11.6 |
| Wrist, from the front | 6.6 | 6.6 | 6.6 | 6.7 | 7.0 |
| Upper arm, from the side | 12.6 | 14.9 | 14.5 | 14.9 | 12.8 (above the elbow) |
| Forearm, from the side | 11.5 | 14.0 | 10.2 | 11.3 | 11.5 |
| Upper arm ÷ forearm, from the front | 0.94 | 0.88 | 0.94 | 1.11 | 0.97 |
| Girth: upper arm, forearm | 37.5, 36.5 | 44.3, 44.8 | 41.8, 34.9 | 45.8, 35.7 | |

| Gate | Result |
|---|---|
| Steps down shoulder > upper arm > forearm > wrist, from the front and from the side | PASS on the mesh (13.4 > 12.1 > 6.7 front; 14.9 > 11.3 side; shoulder cap stands 2.2 cm proud of the base) |
| Forearm at the target's fullness | PASS within 0.5 cm (12.1 × 11.3 against 11.6 × 11.5) |
| Shoulders in the polo no wider than the target | **FAIL**: 66.1 cm against 58–59. The base body in the polo is already 61.9; the sleeve stands about 3.5 cm off the skin each side |
| Seen in a rally frame; no skin through golf and bowling kits | **NOT CHECKED** |
| Adnan approves the male arm | **WAITING** |

Open point for Adnan: the tier 1 target's own arm is close to a tube (upper arm and forearm the same width from the front). A biceps clearly bigger than the forearm is what he asked for and is a step away from that picture (plan decision 3).

Known flaws: small lumps where the shoulder meets the chest and on the cap; a shallow dent on the polo where the cap begins.

### Polo over the second version, 2026-11-12 (shoulder pads)

Adnan on the second version: "the shirt makes it look like he's wearing shoulder pads ... mainly on the sides". Cause, measured: the polo sleeve already stands 2.4 to 3.9 cm off the base skin on the outer side of the arm, and the field moved the sleeve by the muscle's whole growth (up to 3.1 cm there) on top of that slack. Fix (`armfield.CLOTH`, `apply(..., cloth=True)`): the muscle fills the slack first, and the cloth moves out only where it would come nearer the skin than 1.1 cm, or nearer than it already was where it is tight. The body is unchanged. Proof: `phase2/proof_arm_muscles_v6.jpg`.

| Gate | Result |
|---|---|
| Polo shoulders, arms hanging | 62.2 cm (it was 66.1; the base body's polo is 61.9, in the game today 63.7, the target picture 58–59) |
| Polo no nearer the skin than before (`clearance.py`, rest pose) | PASS: least −0.49 cm (one vertex, −0.48 before), 1 % at 0.48 cm (0.51 before); median clearance 1.95 cm (2.74 before) |
| Polo no wider than the target | **FAIL** by about 3.5 cm, all of it in the garment's own cut: the base body's polo is 61.9 |
| No skin through the polo in motion; golf and bowling kits | **NOT CHECKED** |
| Adnan approves | **WAITING** |

This replaces the 11-11 rule "cloth takes the identical field" for growth under slack cloth; where the cloth is tight it still takes the whole field.

### Chest, 2026-11-12

Adnan after the polo fix: "now work on the chest, it's not proportional to the shoulders and arms". He did not say the arm is approved; the arm and the chest are both still studio work. Measured before: the chest was 37.7 cm wide under 57.9 cm shoulders, with small pectorals set high and narrow and no width under the armpits.

Built in `phase2/torsofield.py`, the same way as the arm, about the trunk's upright axis: a pectoral slab from the breastbone to the armpit fold (fullest high on the chest, a clear lower border, its outer corner running into the front of the shoulder), and width under the armpits fading into the waist. The body's own chest came to a point low on each side; the slab is built over the chest with that point levelled (`flatten`). `armfield.armness` keeps the chest field off the upper arm. Proof: `phase2/proof_chest_v1.jpg` (`board_chest.py`), numbers from `torso_measure.py`.

| cm | Base body | In the game today | New arms, old chest | New arms + chest |
|---|---|---|---|---|
| Shoulders, bare | 54.8 | 55.3 | 57.9 | 57.9 |
| Chest width (arms left out) | 35.0 | 36.2 | 37.7 | 40.0 |
| Chest depth | 28.8 | 31.4 | 31.4 | 32.0 |
| Chest girth (approximate) | 107 | 115 | 116 | 121 |
| Waist girth (approximate) | 89 | 80 | 80 | 80 |
| Chest width ÷ shoulders | 0.64 | 0.65 | 0.65 | 0.69 |
| Polo shoulders | 61.9 | 63.7 | 62.2 | 62.2 |

| Gate | Result |
|---|---|
| Pectorals reach the shoulder (no notch between chest and deltoid), from the front | PASS in the studio render, by eye |
| Chest wider in step with the shoulders | 0.65 to 0.69 of the shoulder width; no target number was set, so this is a measurement, not a pass |
| Arm unchanged by the chest field | PASS: 70 vertices at the front of the shoulder move (the tie-in, up to 7 mm); arm widths and girth identical |
| Polo does not print the pectorals | PASS by eye: the polo tents over the chest (`torsofield.cloth_table`: moves only where it lacks the slack, spread 4 cm and hung downward); largest polo move 1.7 cm |
| Polo no nearer the skin than 1.1 cm where it had room | by construction; not re-measured on the final version |
| Side view | **OPEN**: the chest still stands forward of a flat stomach as a rounded mass; less pointed than before, not flat |
| In a rally frame; golf and bowling kits; any motion | **NOT CHECKED** |
| Adnan approves | **WAITING** |

Not done: back, traps, stomach, legs (the 11-11 build's terms are still what the body carries there).

### Tops that hug the body: tennis, golf, bowling, 2026-11-12

Adnan after the chest: "the polo should be hugging the arm, especially with how muscular our frame is. this should be the case for all clothes, golf tennis bowling. should make our character look super fit and muscular". This reverses the direction of the polo fix above (which kept the tailored looseness): the top is now pulled in to the body.

Built in `phase2/fit.py`. For the arms and the trunk, in the coordinates the muscles are built in: the body after the muscle fields, a tent over it (cloth bridges the grooves between muscles and hangs from the chest), a few millimetres of ease (4 mm on the sleeve, 5 mm on the chest, 11 mm at the waist), and every layer of the garment at one place moved by the same amount so hems, cuffs and plackets keep their thickness. Left as tailored: the collar, the hem (the cloth runs from it in a straight line up to the fitted chest), anything tucked into a waistband (the golf polo), and the armpit hollow. One function for all three kits. Proof: `phase2/proof_fit_v1.jpg` (`board_fit.py`), numbers from `fitcheck.py`.

| Cloth to skin, middle value, cm | Sleeve | Chest | Upper back | Nearest point after | Cloth under the skin after |
|---|---|---|---|---|---|
| Tennis polo | 1.6 to 1.0 | 2.4 to 1.7 | 1.7 to 0.9 | 0.07 | 0 |
| Golf polo | 1.0 to 0.9 | 2.3 to 1.4 | 1.5 to 0.9 | 0.09 | 0 |
| Bowling shirt | 1.1 to 0.9 | 2.4 to 2.2 | 1.6 to 0.9 | 0.05 | 0 |

(Nearest point and the under-the-skin count leave out the collar and the armpit hollow. The sleeve's middle value hides the main change: on the outer side of the arm the tennis sleeve stood 2.4 to 3.9 cm off the skin and now sits at the 4 mm ease.)

| Gate | Result |
|---|---|
| Sleeve hugs the arm on all three tops | PASS in the studio renders, by eye |
| No cloth under the skin outside the collar and armpit, rest pose | PASS, 0 vertices on all three |
| Golf belt still visible (tucked hem untouched) | PASS: nothing below the waistband moves |
| No skin through the cloth in motion (swings, serves, the bowling delivery) | **NOT CHECKED**, and the risk is higher than before: the cloth now sits millimetres from the skin |
| Shorts, trousers, socks, shoes; her kits | **NOT DONE** |
| Adnan approves | **WAITING** |

Known flaws: fold lines across the upper chest under the collar on both polos; the bowling shirt's collar points crease and its hem is slightly wavy; in the armpit hollow, with the arms out, the sleeve's underside and the grown side of the chest overlap (hidden when worn, not checked in motion).

Exports added: `export/male_golfkit`, `export/male_bowlingkit` (ZHeroArmExport with `ARM_HERO=GolfKit|BowlingKit`). Render variants: `tennisloose|tennisfit|golfloose|golffit|bowlloose|bowlfit`, 5th argument `dressed`.

### Whole body rebuilt as one, 2026-11-12 (the arm, chest and tight-fit versions above are superseded)

Adnan on the fitted tops: "there's clearly something wrong ... he just looks extremely weirdly built ... make everything proportional, back, abdomen, etc ... also the clothes look terrible now". Diagnosis, measured with `phase2/figure.py` (neck to ankle):

| cm | Base body | In the game today | Last version | Whole body |
|---|---|---|---|---|
| Waist, girth | 89 | 80 | 80 | 90 |
| Chest ÷ waist | 1.21 | 1.45 | 1.52 | 1.28 |
| Hips ÷ waist | 1.22 | 1.37 | 1.37 | 1.21 |
| Shoulders ÷ waist, width | 1.73 | 1.93 | 2.01 | 1.73 |
| Upper arm, girth | 37.5 | 44.3 | 45.8 | 41.9 |
| Upper arm ÷ forearm | 1.03 | 0.99 | 1.28 | 1.18 |
| Chest, girth | 107 | 116 | 122 | 115 |

Causes:
1. **The waist.** The 11-11 build pulled it in to 80 cm and left the hips at 109; my arm and chest were then added above it. Chest 122, waist 80, hips 109 is an hourglass.
2. **Built part by part.** Arm, then chest, each tuned to its own number, on a trunk with no matching back, stomach or neck.
3. **The arm was too big for its bone.** His upper arm bone is 23.8 cm long (the forearm is 27.0); at 46 cm round it read as a ball.
4. **The base body's stomach stands as far forward as its chest** (18.6 against 18.1 cm), so any added chest sat on a paunch or, in the old build, over a pinch.
5. **The clothes.** 4 to 5 mm of ease made the polo a compression shirt: it printed every lump of the body above, with fold lines where the fit's rules met (under the collar, at the hem).

What was built instead: everything on the plain base body (`HERO_BUILD=0`), one set. `torsofield.P`: pectorals as a plane, width under the arms, the upper back and the hollow of the lower back filled, the stomach's front wall and the low pouch held in, the waist left at the base's 89 to 90, neck fuller at the sides and back (throat and jaw untouched). `armfield.P`: the arm one size down (41.9 cm), shallower grooves. `fit.FIT`: ease 7 mm on the sleeve, 10 mm on the chest, 14 mm at the waist, wider tents, the envelope smoothed. Proof: `phase2/proof_whole_v1.jpg` (`board_whole.py`); tune with `whole.py`.

| Gate | Result |
|---|---|
| One build from neck to hips: chest ÷ waist about 1.3, waist not under the base's | PASS on the mesh (1.28; waist 90) |
| Stomach behind the chest in profile | PASS on the mesh (chest 19.8, stomach 17.4 to 16.7 cm forward of the axis; the base had 18.1 and 18.6) |
| Tops on the three kits: no cloth under the skin, rest pose | PASS: 0 vertices outside collar and armpit on tennis, golf, bowling; nearest 0.2 to 0.4 cm |
| Legs in proportion | **NOT DONE**: thighs are 73 cm round each and, side by side, 40.8 cm across, wider than the chest (38.4). This set does not touch the legs |
| Skin surface clean | **OPEN**: small lumps on the bare chest near the breastbone |
| In the game, in motion, her body and kits, shorts and trousers | **NOT DONE** |
| Adnan approves | **WAITING** |

Kept for reference: `armfield.V5` / `armfield_v5.py`, `torsofield.CHEST_ON_BUILD` / `torsofield_chestonly.py`. Exports on the base body: `export/male_build0`, `male_golfkit_base`, `male_bowlingkit_base`.

### Chest rebuilt, 2026-11-12 (the whole-body version's chest was rejected)

Adnan on the whole-body version: "the chest is fucked up, almost look like female breasts from side angle, and there's some disfiguration on the chest/pecs". Causes, seen in close-ups (`renders/r19`) and in the field itself:
1. Each pectoral was its own 3.3 cm mound, fullest low, with the breastbone left at zero between them: two mounds and a deep cleft.
2. Under the mounds the chest fell back 1.8 cm in 6 cm, an undercut.
3. The cleft's walls were steeper than the mesh could carry, which tore them.
4. The base body itself has small sculpt dents along the pectorals' edges and a low point on each side (visible on the plain base, `renders/r19/base_*`); the shapes sat on top of them.

Rebuilt in `torsofield.py`: one broad dome over the whole upper chest, breastbone included, fullest just under the collarbone and running on down over the ribs; the pectorals are 6 mm plates on it with a shallow line between them and a soft lower border; the front of the chest is laid onto the smoothed surface so the base's dents are gone (`resurface`); the field is smoothed so nothing in it is sharper than the mesh. Proof: `phase2/proof_chest_v2.jpg` (`board_chest2.py`). The rejected set is kept as `torsofield_mounds.py`.

| Front of the chest, cm forward of the axis, by height | 1.33 | 1.30 | 1.27 | 1.24 | 1.21 | 1.18 | 1.15 | 1.10 |
|---|---|---|---|---|---|---|---|---|
| Base body | 12.1 | 15.0 | 16.8 | 17.9 | 18.1 | 18.2 | 18.5 | 18.6 |
| Rejected | 13.8 | 17.9 | 19.7 | 19.8 | 19.4 | 18.0 | 17.9 | 17.4 |
| New | 14.8 | 17.2 | 18.6 | 19.3 | 19.4 | 18.9 | 18.9 | 18.3 |

| Gate | Result |
|---|---|
| No cleft between the pectorals; no undercut beneath them | PASS in the close-ups, by eye; the profile loses 1.1 cm over 11 cm where the rejected one lost 1.8 in 6 |
| Chest skin clean | PASS by eye in the close-ups; two faint marks remain near the lower border |
| Tops over it, rest pose | PASS: 0 vertices under the skin on tennis, golf, bowling; nearest 0.2 to 0.3 cm |
| Pectorals read as muscle | **OPEN**: definition is now low (a broad smooth chest); the plate thickness (`pec`) can raise it without bringing the mounds back |
| Legs, her body, bottoms, motion, the game | **NOT DONE** |
| Adnan approves | **WAITING** |

### Shoes, and the first look in the game, 2026-11-12

Adnan on the outfits board: "why are the shoes pointy? fix that pls, and then show me what our characters look like in game now".

**Shoes.** The point is in the game's own shoe meshes (it shows in the game-shader turnaround of 11-11 too): each men's shoe is 37 to 39 cm long on a 31 cm foot and narrows from 18 cm to under 4 cm over its last third. `phase2/shoefield.py` redraws the toe box as a blunt rounded end (superellipse) and draws the tip back 2.2 cm; laces, heel and height are untouched. Tennis, golf and bowling shoes.

| Shoe width, cm, by station (heel 0, toe 1) | 0.70 | 0.80 | 0.85 | 0.90 | 0.95 | 0.98 | Length |
|---|---|---|---|---|---|---|---|
| Tennis, before | 17.7 | 15.2 | 12.9 | 10.0 | 6.3 | 3.7 | 39.4 |
| Tennis, after | 18.1 | 17.9 | 17.3 | 16.0 | 12.6 | 9.6 | 37.2 |
| Golf and bowling, before | 17.0 | 14.0 | 12.0 | 9.0 | 5.5 | 3.4 | 37.5 |
| Golf and bowling, after | 17.4 | 17.1 | 16.4 | 14.8 | 11.8 | 7.7 | 35.3 |

**In the game.** Still nothing in the shared project. A preview hook that exists only in the project copy `~/unity-clones/final-plan-dev` (`phase2/install_clone_preview.sh`, `HeroStudio.cs.txt`; `... off` removes it) loads the studio's vertex positions (`phase2/make_game_data.py` -> `phase2/game_data/`, `HERO_STUDIO=<dir>`) for the male body, tops, shoes and the garments that follow, in place of the 11-11 build; normals and tangents turn with the surface. Captured with `CHARACTER_LOD=0`: game-shader turnarounds of all six heroes (`look/turnaround_new`, the golfer in `look/turnaround_new_golf`) and scenes (`ingame_new.sh` -> `look/ingame_new`: tennis court and close shots, golf, bowling, plaza and locker room). Board: `look/characters_in_game_1112.jpg` (`look/board_ingame.py`).

| Gate | Result |
|---|---|
| Every male mesh with a file loads in the game | PASS: body, top, bottom, shoes (and golf belt) on all three kits, per the Unity logs. The golfer's body renderer is named `Body`, not `Body_M`; the first turnaround missed it and was retaken |
| Renders in the game's shaders without broken shading | PASS by eye on the turnarounds and scenes |
| In motion, at speed, on a device | **NOT CHECKED**: stills from a few poses only (ready stance, one rally frame, golf address, bowling stance) |
| Distance versions of the garments | **NOT DONE**: the preview forces full detail; the game's distance garments have no new shape yet |
| Her | unchanged; her shoes were not looked at |
| Adnan approves | **WAITING** |

Seen in the game renders: the tennis polo reads glossy and a little lumpy across the stomach in the ready stance; the bowling shirt's front wrinkles in the reaction shot; the back of the tennis shoe (heel counter) still looks boxy.

### Her: walk, arms, hands, 2026-11-12

Adnan on her board: "the female has good proportions, main issue are the fit of the clothes, her fingers and hands, and the arms having extremely weird anatomy/animations. when she walks she looks like a bug not a human".

Method: `HandsWristFilm` (the plaza's own walk, every kit, hand close-ups) in the project copy, once as the game is and once with each suspect switched off (`her/toggle_body.jpg`, `her/toggle_handL.jpg`).

| Cause | Evidence | Fix (project copy only: `her/install_clone_her.sh`) |
|---|---|---|
| **Bug walk**: the baked hand-clearance tracks carry every hand clear of the tennis skirt's flared hem, and the plaza plays them for every kit; both arms are held out with bent elbows through the whole walk, in trousers too | `HUB_SAFETY=0` gives a normal arm swing (hands then pass through the skirt); wrist angles are identical across her three kits, so the correction is baked, not solved per kit | `HeroClearanceTracks.FreeArmShare` = 0.40: an arm whose hand is empty takes 40 % of its baked correction. Racket and club hands unchanged. `CLEARANCE_FreeArmShare=1` restores the old walk |
| **Arm anatomy**: the 11-11 build's arm term at `HERO_ARM_GAIN` 2 swells her forearm by up to a third on a slim frame | `HERO_ARM_GAIN=0` gives even, slim arms | default 2 -> 0.6 |
| **Hands**: walking, her empty hands keep the clip's fingers, straight and spread | hand close-ups | a relaxed curl while she walks and runs (`CurlFingers` with an even per-finger set, amount 0.8 in the film; `FEMALE_WALK_CURL`) |

Proof: `her/her_walk_before_after.jpg` and `.gif` (frames in `her/walk_before`, `her/f3`).

| Gate | Result |
|---|---|
| Arms hang by her sides and swing, in all three kits | PASS by eye in the film |
| Forearm no thicker than her frame carries | PASS by eye |
| Hands read as relaxed human hands | **PARTLY**: fingers now fall together with a curl; the hand itself is still long-fingered and flat, the thumb is a dark stub, and fingertips carry dark and orange smudges (skin texture). Mesh and texture not touched |
| Hands clear of the skirt | **NOT MEASURED**: at 40 % the hand passes close in front of the pleats; no clipping in the sampled frames, not checked frame by frame |
| Tennis and golf clips (her free left hand takes the same 40 %) | **NOT CHECKED**: only the plaza walk was filmed |
| Clothes fit | **NOT STARTED** at this point |
| In the shared project | **NO**: project copy only |

### Her: clothes' fit, first pass, 2026-11-12

Measured first (`phase2/herfit_measure.py`, exports `export/female_tennis|female_golfkit|female_bowlingkit`): the golf polo's sleeves stand up to 5.5 cm off her arm and the polo is 3 cm loose at the waist; the tennis tank is 0.5 cm off the chest and 2 cm at the waist; the bowling shirt 1 to 2 cm all over; the bowling trousers 0.7 to 1.9 cm (they follow her legs; the wide look is her own hip and thigh).

Refit: the same `fit.dress` as his tops with `grow=False` (her body is not touched), `phase2/herfit.py`. Three things had to change for her and now hold for both: an armhole edge is not a sleeve (her tank, her bowling shirt), a top's hem that meets a waistband is left as tailored (pushing it clear widened her hems by 4 cm), and the shift a garment takes is smoothed as a whole. His three tops re-checked after those changes: still 0 vertices under the skin, nearest 0.23 to 0.26 cm.

Loaded in the project copy through the same preview hook (her tops only, after her own build) and rendered by the game: `her/her_today_vs_new.jpg` (`her/board_her_after.py`; turnarounds `her/turnaround_fit`, walk `her/f4`).

| Gate | Result |
|---|---|
| Golf polo sleeves close to the arm | PARTLY: 95 % clearance 5.5 -> 2.4 cm, polo 6 cm narrower across the sleeves; in the game's render the sleeves and sides now show soft lumps. Closer, not cleaner |
| Tennis tank, bowling shirt | little change (they were already close): largest move 1.3 and 1.4 cm |
| Skirt, skort, bowling trousers, shoes | **NOT TOUCHED** |
| Her body unchanged by the refit | PASS: 0.00 mm |
| In motion, in the shared project | **NO** |

Honest read: the walk and the forearm are clear improvements; the hands are better posed but the hand itself is still wrong; the clothes' fit moved a little and the golf polo needs re-tailoring (its sleeves are built puffed, on a coarse mesh) more than a refit.

### Her arm against his in the same walk, 2026-11-12

Adnan: "look at her arms, there's a clear break where her arm is bending downwards. pull up the same walking from the male and compare them". Filmed with a project-copy tool, `her/ArmWalkFilm.cs.txt` (`her/armfilm.sh <name> [ENV=..]`: front, side, each arm close up, and `arms.csv` with the elbow bend and where the upper arm and forearm point), tennis kits, three ways.

| Elbow bend through the walk, degrees: average (least to most) | Her | Him |
|---|---|---|
| The walk clip alone (clearance off) | 52 (47 to 61) | 52 (47 to 61) |
| As in the game | 51 (14 to 71) | 31 (18 to 42) |
| Now | 21 (10 to 30) | 16 (10 to 22) |

Cause: the Walk clip carries the arms like a jogger's, the elbow bent about 52 degrees the whole way round, for both heroes. His baked clearance track happens to straighten his elbow to about 31; hers leaves it near 51 and swings it between 14 and 71. On her slim arm a 50 degree elbow with the upper arm back and the forearm forward reads as a break; his bulk and straighter elbow hide it.

Fix (project copy, `her/install_clone_her.sh`, both heroes): in the plaza a free arm's elbow is eased into a walking range by turning the forearm about the elbow's own hinge (`want = 12 + 0.7 x (bend - 35)`, never under 10), weighted out by the relaxed stand, actions and sitting. `PLAZA_ELBOW=0` restores the clips' elbows. Proof: `her/her_arm_vs_his.jpg` and `.gif`.

| Gate | Result |
|---|---|
| Her elbow in a walking range, close to his | PASS: 21 against 16 degrees on average; it was 51 against 31 |
| No break at the elbow in the close-ups | PASS by eye in the sampled frames |
| Hands clear of the skirt with the straighter arm | **NOT MEASURED**: the hand now hangs lower, beside the skirt's hem; no cut-through in the sampled frames |
| Running, emotes, tennis, golf, bowling | **NOT CHECKED**: only the plaza walk was filmed. The elbow change applies to plaza walking and running only |
| In the shared project | **NO** |

### Her forearm and wrist, 2026-11-12

Adnan: "it's also her forearm/wrist, it doesn't function like a normal one in the animation, it's like her wrist is permanently broken. first we need to fix that, then rework the animations".

**What was measured.**
- Rest pose (exported bones): her hand is built 22.8 degrees off her forearm's line, toward the thumb; his 1.3. Her forearm is 20.9 cm, his 27.0; her knuckle span 5.3 cm, his 9.4.
- The walk (`ArmWalkFilm`, now on the film's own clock; before this fix each filmed frame skipped about 0.09 s, so the earlier animations played roughly three times too fast): the hand leaves the forearm's line by 8 degrees at the back of the swing and 37 at the front, every stride (his 10 to 33). It is in the Walk clip itself: the same with the clearance off.
- Every clip as authored (`her/ZClipArmSurvey.cs.txt` -> `her/clip_arm_survey.csv`, 107 clips per hero, sampled raw at 30 Hz, no grip polish or clearance): the largest wrist bend has a middle value of 81 degrees for her and 80 for him; 91 of her 107 clips and 89 of his pass 60 degrees. Tennis ready stance 68 (her right wrist 60 degrees sideways, held), plaza run 101, forehand 111, backhand 129, return 154. A real wrist manages about 70 forward or back and 20 to 35 sideways.

So the wrist is not broken in one place: nearly every animation drives it past what a wrist can do, for both heroes; on her thin wrist, built off-line at rest, it shows.

**Fixed now (project copy, `her/install_clone_her.sh`, both heroes, plaza walking and running):** a free hand keeps to the forearm's line: up to 8 degrees as the clip has it, a fifth of anything beyond. `PLAZA_WRIST=0` restores the clips' wrist. Proof: `her/her_wrist_vs_his.jpg` and `.gif` (frames `her/b_game`, `her/b_fix`).

| Gate | Result |
|---|---|
| Walking wrist within a normal range, hers like his | PASS: hers 10 degrees on average (8 to 14), his 10 (8 to 13); it was 19 (8 to 37) and 18 (10 to 33) |
| Elbow still in the walking range with it | PASS: hers 24 on average (17 to 29), his 15 (12 to 19) |
| The wrist in every other animation | **NOT FIXED**: the survey above is the work list |
| The wrist's skin where it does bend (the crease in the ready stance), the hand's built-in 23 degrees, the hand's shape | **NOT TOUCHED** |
| In the shared project | **NO** |

**Animation rework, proposed order** (not started): 1. anatomical wrist limits in the pose pass every hero pipeline already calls, free hands first (no racket or club to keep in place); 2. for a hand on a racket or club, the elbow is re-chosen so the wrist comes inside its limits while the racket stays where the clip put it; 3. re-key by hand only the clips still outside after that, worst first (`clip_arm_survey.csv`).

### Her arm brought to his, 2026-11-12

Adnan on the wrist version: "closer but still needs more work. the male arm looks perfect but girl's still lacking". Compared at full size (`her/arm_now_big.jpg`) and measured from forearm to knuckles on both rest bodies:

| Wide x deep, cm | Her before | Her now | His |
|---|---|---|---|
| Forearm, 13 cm above the wrist | 8.5 x 7.8 | 8.1 x 7.8 | 10.5 x 10.4 |
| Forearm, 4 cm above | 7.9 x 5.7 | 6.1 x 5.1 | 8.2 x 7.1 |
| Wrist | 7.1 x 4.9 | 5.9 x 4.3 | 7.3 x 4.3 |
| Palm, 6 cm in | 8.3 x 5.1 | 8.5 x 5.0 | 12.7 x 7.4 |
| Wrist as a share of the palm | 0.85 | 0.69 | 0.57 |

Cause: the 10-27 hand reshape (`HeroHandShape.Wrist`) widened her wrist by 22 %, to 7.1 cm: as wide as his on a forearm two thirds the size. Her forearm never narrowed into a wrist, so the hand read as stuck on the end of a rod. And her elbow was still about 10 degrees more bent than his.

Fix (project copy, `her/install_clone_her.sh`): new section profile in `HeroHandShape.Wrist` (width 0.97 / 0.89 / 0.88 at 10 cm above, 3 cm above and at the wrist, 1.14 just inside the palm; depth 0.93 / 0.76 / 0.72); `FEMALE_WRIST_TAPER=0` restores the 10-27 numbers. Her elbow's walking range is set to his (`12 + 0.45 x (bend - 44)`). Proof: `her/her_arm_now.jpg` and `.gif` (frames `her/c_fix`), shape from `export/female_tennis_taper`.

| Gate | Result |
|---|---|
| Elbow in the walk equal to his | PASS: 15 degrees on average (11 to 19) against his 15 (12 to 19) |
| Wrist in the walk equal to his | PASS: 10 (8 to 14) against 10 (8 to 13) |
| Forearm tapers into a wrist narrower than the palm | PASS on the mesh: wrist 0.69 of the palm (it was 0.85; his 0.57) |
| Her golf glove and anything else worn at the wrist | **NOT CHECKED** against the narrower wrist |
| Fingers (thin, dark ragged tips), thumb | **NOT TOUCHED** |
| Other animations; the shared project | **NO** |

### INSTALLED in the game project, 2026-11-12

Adnan: "implement changes to the game now to her arms, as well as the male model and clothes and what we've worked on". Installed in `Unity/`, **uncommitted**. Every changed file was saved first (`keep.sh` -> `install_backup/`); `ROLLBACK.sh` puts everything back.

| What | Where | Switch (environment) |
|---|---|---|
| His whole-body rebuild, his three tops refitted, the garments that follow, rounded shoe toes; her three tops refitted | new `Unity/Assets/Scripts/Tennis/HeroStudio.cs` + data `Unity/Assets/Resources/HeroStudio/*.bytes` (17 files, 1.6 MB: per-vertex offsets, written by `phase2/make_game_data.py`); called from `HeroBuild.Prepare` (him, in place of the 11-11 build) and `MatchHeroLook` (his shoes; her tops after her own build) | `HERO_STUDIO=0`: all of it off, he gets the 11-11 build again |
| Her forearm build toned down | `HeroBuild.cs`: her arm gain 2 -> 0.6 | `HERO_ARM_GAIN=2` |
| Her forearm tapering into a wrist | `HeroHandShape.cs`: new section profile | `FEMALE_WRIST_TAPER=0` |
| Plaza walk and run, both heroes: free arms take 40 % of the baked clearance | `HeroClearanceTracks.cs` (`FreeArmShare`, `Player.freeArmShare`), handed over in `HubHeroAnimator.cs`. Plaza only: tennis and golf keep the full track | `CLEARANCE_FreeArmShare=1` |
| Plaza walk and run: elbow eased into a walking range, hand kept to the forearm's line, her fingers curled | `HubHeroAnimator.cs` | `PLAZA_ELBOW=0`, `PLAZA_WRIST=0`, `FEMALE_WALK_CURL=0` |

A mesh of his with no data file of its own (a distance garment, a sock) follows the body's offsets underneath it, as the 11-11 build's garments did; the preview's forced full detail is gone.

| Gate | Result |
|---|---|
| EditMode suite on a project copy synced from the installed project | PASS 778 / 778 (`logs/install-editmode.*`) |
| Every data file loads in the game | PASS: his body (both renderer names), 3 tops, 3 bottoms, belt, shoes, her 3 tops, per the Unity logs of the turnaround and the scene captures |
| The installed game renders what was approved in the preview | PASS by eye: `look/installed_1112.jpg` (turnarounds `look/turnaround_installed`, scenes `look/ingame_installed`), normal level of detail, no preview switches |
| Her walk on the installed code | PASS: wrist 10 degrees on average (8 to 14), elbow 15 (11 to 19); his 10 and 16 (`her/d_installed/arms.csv`) |
| PlayMode suite | **NOT RUN** after the install |
| His distance garments (the game's far-away versions of the tops) | **NOT VERIFIED**: no capture showed one in use; they have no data file and follow the body |
| The iOS menus and locker (their heroes are exported files, `GolfArcade/Unity/CharacterAssets`) | UPDATED later on 11-12: see "Menu, locker and lobby heroes re-exported" below |
| On a phone | **NOT BUILT** |
| In motion beyond the plaza walk (tennis, golf, bowling) | **NOT CHECKED** |
| Committed | **NO** |

### Menu, locker and lobby heroes re-exported, 2026-11-12

Adnan: "fix the menu characters as well". The app's menu, locker and lobby heroes are exported copies of the game's heroes (`GolfArcade/Unity/CharacterAssets`), so they still showed the bodies and clothes from before the install. Re-exported from the installed game with `work/final-plan-1111/sync_menus.sh` (= `work/hero-sync/sync_heroes.sh` on the plan's project copy through the job gate, then `MatchHeroLockerExport.RunBowling`, which that script does not cover). **Uncommitted.**

- Changed: 66 files for tennis, tennis far-away and golf (mesh, skeleton with its animations, loading-screen swing frames), 6 for the bowling heroes, and the 6 Unity reference files + `provenance.json` in `GolfArcadeTests/VisualGolden`. No textures changed.
- `work/hero-sync/look_sources.txt` now also guards `HeroBuild.cs`, `HeroStudio.cs` and the 17 `Resources/HeroStudio/*.bytes` (253 guarded sources), so the native freshness test fails if the body or clothes data change without a re-export.
- Before: `install_backup_menus/` (`CharacterAssets`, `VisualGolden`, `sheets_before`). Undo: `work/final-plan-1111/ROLLBACK_MENUS.sh` (menus only; the game project is `ROLLBACK.sh`).

| Gate | Result |
|---|---|
| Every export used the new shapes | PASS: the Unity logs of all four exports show the studio meshes loading (his body, tops, bottoms, shoes; her tops), none falling back |
| Menu hero = game hero, same pose, cameras and lights (`work/hero-sync/sheets`, `PARITY.md`) | PASS: 58 shots, brightness ratio 0.949 to 1.052, largest mean difference 10.6 of 255 (his head, palette 5), the same range as before the install |
| The menu heroes show the new work, by eye | PASS: `look/menu_characters_1112.jpg`, before and after in the app's own renderer, tennis, golf and bowling, both heroes |
| Bowling menu heroes draw correctly | PASS by eye in a copy of the lobby renderer with a bowling switch (the sync has no bowling sheet; no game-side picture to compare against) |
| The app's own hero tests on the simulator (`VisualOverhaulNativeTests`, `LockerMirrorTests`; `logs/menus_native_tests*.log`) | PASS for what the export can affect. Freshness test (menu export older than the game's look sources): failed before, passes now. The app's skinning against Unity's reference vertices, all six heroes: passes, after two hard-coded bone counts in `GolfArcadeTests/VisualOverhaulNativeTests.swift` were raised by six (the forearm twist bones of 11-11, new to the export). **14 other tests in these two files fail, identically on the old files and the new** (stale expectations: face shapes list, cloth weave numbers, old fixtures under `work/`); not touched |
| Bowling heroes against Unity reference vertices | **NOT CHECKED**: the tests have no bowling reference |
| Whole native test suite | **NOT RUN** (only the two hero files) |
| Menus, locker and lobby looked at in the app (simulator or phone) | **NOT DONE** |
| Committed | **NO** |

### Animation rework, step 1: wrist and elbow limits in every sport (project copy only), 2026-11-12

Adnan: "Start animations" (after: "it's like her wrist is permanently broken. first we need to fix that, then rework the animations"). **Built and measured in the project copy `~/unity-clones/final-plan-dev`; NOT in the shared `Unity/`.** Another chat ("Emotes and sports animations", `work/anim-review-1112`) is editing `GolferView.cs`, `HubHeroAnimator.cs` and a new `HeroHands.cs` in the shared project (empty hands after emotes), so this step is one new file and one hook in a file that chat has not touched.

- `anim/HeroArmLimits.cs.txt` (new `Assets/Scripts/Tennis/HeroArmLimits.cs`): one anatomical rule as the last step of the shared pose pass (`HeroPoseSafety.Apply`: tennis, golf, plaza, bowling). The wrist's bend is split into flexion, extension and deviation to either side, each with its own limit and a soft knee. An **empty hand** turns back about the wrist. A **hand that carries the racket or club** keeps its place and rotation; its elbow swivels about the shoulder-wrist line (26 degrees at most, never into the trunk, held down from climbing), and outside a stroke the hand may turn part of the rest, eased. A **hand that only steadies the grip** (the tennis ready cradle, the top hand in golf) turns about the middle of what it grasps and its arm is solved again; eased in and out so the arm never jumps when the grip changes.
- `anim/install_clone_anim.sh` installs it in a project copy (sync from the shared project, the file, the hook in `HeroPoseSafety.cs`). `ARM_LIMITS=0` switches it off; `ARM_LIMIT_<Name>` overrides a number.
- Measuring: `anim/ZArmProbe.cs.txt` (copy only, `ARM_PROBE_OUT`) rides on the real films (`anim/probe.sh <round>`: `CurrentTennisPointFilm` for each hero, `CurrentGolfSwingFilm`, `BowlingFilm`), writes every hero arm every frame before and after the limits, and photographs the worst wrists twice in the same frame. `anim/stats.py`, `pops.py`, `board.py`, `strip.py`, `proof.py`. Final round `anim/r6` (+ `r7`), proof `anim/proof_wrist_limits_v1.jpg`.

Degrees the hand is off the forearm's line, real play (mean / 95th percentile / worst):

| Where | Before | After |
|---|---|---|
| Tennis, her hand steadying the racket (ready stance, about half of a point) | 60 / 69 / 69 | 13 / 21 / 29 |
| Tennis, her empty left hand | 33 / 50 / 57 | 17 / 21 / 25 by the limits; on screen 20 / 38 / 91, because the serve's ball hand is posed afterwards by `HeroTossHold` |
| Tennis, her racket hand | 42 / 54 / 72 | 38 / 48 / 62 |
| Tennis, his racket hand | 49 / 79 / 95 | 43 / 71 / 82 |
| Golf, her hand steadying the club (address) | 54 / 61 / 61 | 24 / 25 / 48 |
| Golf, her hand carrying the club | 52 / 105 / 105 | 51 / 106 / 106 |
| Bowling, his empty hands | 15 / 71 / 97 and 13 / 50 / 85 | 11 / 41 / 42 and 10 / 37 / 38 |
| Bowling, her empty hands | 6 / 5 / 37 | 6 / 10 / 36 |

| Gate | Result |
|---|---|
| Empty and steadying hands stay inside a human range in real play | PASS in the films measured: no frame past 45 degrees for a steadying hand or a bowling hand (before: 80 % of her ready stance past 60) |
| No jump caused by the limits | PASS: no frame where the limits' own result moves more than 8 degrees further than the clip did, except the first frame after a hero appears (`anim/r6/pops.txt`, `r7`) |
| EditMode suite on the copy with the limits on | PASS 778 / 778 (`logs/anim-editmode2.*`) |
| The hand that carries the racket or club | **FAIL / not solved**: strokes keep the hand where the clip has it (the strings must meet the ball), so his racket wrist still reaches 82 and the putting grip 106. Needs the clips or the grip pose changed |
| Serve toss hand (91 degrees with the ball) | **NOT COVERED**: `HeroTossHold` poses it after the pass |
| Golf address looked at closely by a person | **NOT DONE**: the gloved hand turns on the club by the pivot; from the game camera it reads the same, closer it needs Adnan's eye |
| His tennis player in golf, both heroes in every sport, emotes, the plaza | **NOT MEASURED** (films used: her and him in tennis, her in golf, both in bowling) |
| PlayMode suite; frame cost of the pass | **NOT RUN / NOT MEASURED** |
| Menus and locker | **NOT COVERED**: `MatchHeroLockerExport` samples the clips without the pose pass, so the menu heroes' ready stance keeps the 68 degree wrist until the export applies the limits and is run again |
| Installed in the shared project | **NO** |

Found on the way: in his tennis follow-through the fitted polo breaks up at the shoulder (ragged red pieces around the sleeve, `anim/r6/strip_b.jpg` last row, before and after alike). The fitted tops were only checked at rest; this is the first look at one in a stroke.

### Working beside the "Emotes and sports animations" chat, 2026-11-12 22:30

Adnan: "figure out what the other chat is working on specifically and make sure u guys dont interfere". Read from its transcript and files: it was asked for emotes, tennis and bowling animations; it installed the empty-hands rule (`HeroHands.cs`, calls in `GolferView.cs` and `HubHeroAnimator.cs`, 21:33) and is now on the racket fingers (`HeroGripPolish.cs`, `HeroRacketSeat.cs`, in its copy `~/unity-clones/anim-review`). Ownership, pass order and rules: `work/COORDINATION_animation_2026-11-12.md`; the same sent to that chat as a note (queued, not confirmed).

| Check | Result |
|---|---|
| Same files edited by both | ONE: `Hub/HubHeroAnimator.cs` (its EMPTY HANDS call; this plan's elbow / wrist / curl blocks). Both sets of lines are in the live file |
| This plan's `ROLLBACK.sh` would have deleted the other chat's lines there | FIXED: guarded (restores a file only if it is exactly as this plan left it, `install_patches/MANIFEST.sha256`; takes only this plan's 46 changed lines out of `HubHeroAnimator.cs`, `install_patches/HubHeroAnimator.mine.patch`, dry run clean). Old script: `install_patches/ROLLBACK_before_guard.sh` |
| The other chat's rollback deletes this plan's lines | NO: it removes its own lines by pattern (run on a copy: both files "clean", this plan's blocks intact) |
| The two wrist rules fight | NO: its `KeepWristInLine` (empty hands, golf without a club and plaza emotes) and `HeroArmLimits` both only bring the hand toward the forearm's line; its finger wrap runs after the pose pass (order 1160) and sees the final hand |
| Menu export still current | **NO since 21:33**: `HubHeroAnimator.cs` is a guarded look source, so `testNativeHeroesMatchTheCurrentUnityHeroLook` fails again. Its racket work will change two more guarded files. One export (`sync_menus.sh`) after that work is installed |
| Unity copies and the job gate | Separate copies; both chats use `heavy.sh` |
| Left to the other chat | fingers, grip, racket seat, emote clips. Unowned until its racket work lands: the racket-carrying hand's wrist in strokes |

### After the other chat's racket-grip install, 2026-11-12 22:53 to 23:25

It installed `HeroGripPolish.cs` (finger wrap, marked RACKET GRIP 2026-11-12) and `HeroRacketSeat.cs` (her racket 12 mm along the palm; no rotation; his unchanged) and handed the menu export to this chat.

| Gate | Result |
|---|---|
| This plan's installed work untouched by that install | PASS (HeroStudio hooks, the plaza blocks, the data files all present; its diff is those two files only) |
| Menu, locker and lobby heroes exported once more from the current game | DONE 23:10: 60 + 6 files; previous export kept in `menus_new/`; menu against game sheets in the same range as before (58 shots, largest mean difference 10.6 of 255) |
| Native hero tests on the new export | PASS: freshness and golden vertices (6 heroes). The stale face-shapes test still fails, as before |
| `HeroArmLimits` on the new grip (project copy, round `anim/r8`) | PASS: her ready-stance wrist 61 to 13, golf address 54 to 24, as before the grip change; EditMode 778 / 778 with both chats' work |
| A jump when a golf hand changes from carrying to steadying | **1 frame of 16 degrees** at the putt (`anim/r8/pops.txt`): the ease-in covers empty-to-steadying, not carrying-to-steadying. Not fixed |
| Re-bake of the tennis arm corrections | NOT NEEDED for the racket (no rotation). Whether the men's new body needs one is **not measured** |
| `HeroArmLimits` in the shared project | **NO**: waits for Adnan's word; the menu export runs once more after it |

### Wrist and elbow limits INSTALLED in the game project, 2026-11-13 13:42

Adnan: "install the changes and show me what all of the animations look like now". **Uncommitted.** `anim/install_game_anim.sh`:
new `Unity/Assets/Scripts/Tennis/HeroArmLimits.cs`; `HeroPoseSafety.cs` ends `Apply` with the public `ArmLimits()`; `Editor/MatchHeroLockerExport.cs` applies the same rule to every clip frame it exports (marked `ARM LIMITS 2026-11-13`). Switch `ARM_LIMITS=0`. Backups by `keep.sh`, guarded `ROLLBACK.sh` manifest updated; `HeroArmLimits.cs` and `HeroPoseSafety.cs` added to the guarded look sources.

Changed since the copy-only version above:
- A hand moving between carrying and steadying the racket or club now eases (the one-frame 16 degree jump at the putt).
- Editor samples (tools, tests, the menu export) are each their own pose (no carry-over between samples taken in one frame).
- The top hand of a two-handed backhand stays exactly where the clip has it near contact (`FemaleDeformationTests.BackhandAndServeContactTransformsStayExact` failed with it moving 7.3 cm); it settles away from contact, as do the ready cradle and the golf top hand.

| Gate | Result |
|---|---|
| EditMode on a copy identical to the installed files | PASS 778 / 778 (`logs/anim-editmode5.*`; the 3 files compared byte for byte) |
| Measured again after these changes (round `anim/r9`, her tennis point, his golf) | her ready cradle 60 -> 12, his golf top hand 50 -> 23; no new jumps except at a point's first frames (frame 2-5 and 38, where the game places the heroes) |
| PlayMode | **NOT RUN** |
| Menu, locker and lobby heroes | DONE 13-11 15:20: exported with the limits (50 + 4 files; the export now applies them to every clip frame); no guarded source differs; native freshness and golden-vertex tests pass (the stale face-shapes test still fails, as before) |
| On a phone | **NOT BUILT** |

### Every animation filmed on the installed game, 2026-11-13

`anim/films.sh films_1113` (9 Unity runs, about 20 minutes; the golf swing film needed a copy-only fix: `GolfMotionFilm` could not find a 100-yard spot on hole 12 and now takes the nearest playable one), `anim/encode.py` (one video per sport: `films_1113/<sport>.mp4`, lighter `<sport>_view.mp4`, overview `<sport>_sheet.jpg`), and for review `anim/clips.py`: **101 numbered clips, one per animation** in `films_1113/clips/` with a page `clips/index.html` (served by the `anim-clips` entry in `.claude/launch.json`, port 8771): tennis 48 (each hero's animations cut from a real point, then the 7 emotes and 6 reactions per hero), golf 28 (5 clubs, 7 emotes, walk, run per hero), bowling 5 (deliveries and reactions; the film's camera follows the ball, so a reaction may not show the bowler), plaza 20 (walk, run, sprint, 7 emotes per hero).

Wrist numbers across these films (probe without pictures, `films_1113/*_probe`, `anim/stats.py films_1113`): steadying hands now 12-30 degrees on average (were 50-82); empty hands 9-22 (were 11-32); **the racket- or club-carrying hand is still 35-67 on average and up to 101-123 in golf emotes and putting**: not solved. The plaza probe recorded zeros (it did not read the plaza heroes); the plaza's own numbers are the 11-12 walk measurements.

Tools added: the export now writes the whole skin (`<name>.skin`, `export/male_skin/`), `armio.swing` poses the arms down with the game's own weights (helper bones `ArmBlend_a_b_n` included), `armio.membership` says what belongs to the arm (the four named bones carry little of the shoulder and elbow, which is what wrinkled the first version there), `widths.py`, `tune.py`, `crumple.py`. `armfield_v3.py` and `armfield.V3` keep the first version.
