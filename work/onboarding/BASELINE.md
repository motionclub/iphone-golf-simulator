# P0 baseline — 2026-10-06

Final authoritative verdict: P0.1 PASS (baseline recorded, including named pre-existing failures), P0.2 PASS. The initial pending observations below are retained as execution history. The check helper has 10 error diagnostics plus 1 warning, not 11 errors. The final full native summary and EditMode XML are authoritative.

Branch: newmapsandmenus. All foreign staged changes preserved. Full lists: baseline-staged.txt, baseline-unstaged.txt. Owned-file diffs saved individually before edits.

## Owned existing status
```
 M GolfArcade/Unity/SportsSession.swift
 M GolfArcade/Unity/TennisMenu.swift
 M GolfArcade/Unity/TennisPlayViews.swift
 M Unity/Assets/Scripts/Game/GolfGame.cs
 M Unity/Assets/Scripts/Game/NativeSportsSession.cs
 M Unity/Assets/Scripts/Tennis/TennisGame.cs
```
All other owned existing files are clean (full list in owned-existing.json; hashes in baseline-owned-hashes.json).

## Test results
- GolfArcadeTests: MCP request timed out after 300 seconds; xcodebuild continues its pre-existing recording tests. At this snapshot: 167 passed, 1 failed; NOT a complete result. Log: /Users/adnanyonathan/Library/Developer/XcodeBuildMCP/workspaces/ope-603affc411a6/logs/test_sim_2026-10-06T14-29-52-972Z_pid7332_14479eb1.log. Result bundle: P0_native.xcresult. Final counts will be appended after completion.
- Unity/Tools/check.sh: FAILED compilation, 10 pre-existing missing URP/Volume references, zero tests executed. P0_unity-check.log. Tool is unowned; NEEDS_OWNER.md.
- Unity Editor EditMode: PASS, 253 passed, 0 failed, 0 skipped. P0_editmode_retry.xml, P0_editmode_retry.log. Initial sandbox IPC restriction was resolved by an approved unsandboxed retry.

## Anchors and drift
Functions in the brief exist (exact file/function lines in baseline-anchors.txt). SportsHome routes at entry; current APIs accept Player edits and savePlayers; Game Center is async authenticate(present:). Existing public tennis MovePlayer auto-runs both touch and motion, no TennisActor/HeroTennisDriver change needed. Tutorial emits StepChanged/Finished; Swift tutorialStep and tutorialDone handlers exist.
GolfGame currently loads Course.Postcards(), a foreign change replacing Cliffside. NativeSportsSession owns multiplayer/emote additions; onboarding will add separate hunks. Native-only Simulator build cannot embed Unity, as documented in SportsLibrary/IOS-UNITY-INTEGRATION.md. Player has no supported headwear field, catalog has no headwear slot.

## Initial observation (superseded by final counts below)
The first snapshot could not certify complete baseline counts while the native suite was running. The helper remains failing; P0.1 requires recording its failure rather than repairing it. Final P0.1 and P0.2 verdicts below are authoritative.

## Final native baseline
{"result": "Failed", "totalTestCount": 419, "passedTests": 410, "failedTests": 8, "skippedTests": 1}

Failing cases:
- -[GolfArcadeTests.DressedHeroSnapshotTests testDefaultKitIsTheAuthoredWhiteKit]
- -[GolfArcadeTests.LockerMirrorTests testKitMaterialsSampleTheWeaveTheThreadMapAndTheSeamMap]
- -[GolfArcadeTests.LockerMirrorTests testSeamMapOrientationPutsTheDarkeningOnTheHemsAndCollar]
- -[GolfArcadeTests.LockerMirrorTests testShippedRigReproducesUnitysPoses]
- -[GolfArcadeTests.LockerMirrorTests testShirtIsNotOneFlatWhite]
- -[GolfArcadeTests.LockerMirrorTests testSoleIsDarkerAndRougherThanTheUpperAndIsNotRecoloured]
- -[GolfArcadeTests.LockerMirrorTests testWeaveTileIsMetresPerUvOverTheRolesTileSize]
- -[GolfArcadeTests.LockerTests testLockerOpensOnTheShelfAndTheGridFollowsTheTab]

P0_native_summary.json and P0_failures.json are authoritative final results. Original-build SportsNavigationTests: 0 passed, 1 failed, 2 skipped; P0_navigation_retry.xcresult.
