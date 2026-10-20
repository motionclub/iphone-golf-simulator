# Phase 10

| Gate | Result | Proof / exact check |
|---|---|---|
| P10.1 | FAIL(BLOCKED-OWNER) | P10_native_summary.json: 434 total, 422 passed, 9 failed, 3 skipped. Native-only suite has 431 tests: 422 pass, same 8 baseline failing cases, 1 skip (includes 12 new passing unit tests). SportsNavigation: unchanged baseline 1 fail, 2 skip. P10_editmode.xml: 257 pass, 0 fail vs baseline 253/253. P10_check_comparison.txt: same 10 compiler errors. Real touched PlayMode tests fail; no successful complete tutorial / no-new-PlayMode-failure comparison can be certified. |
| P10.2 | FAIL(BLOCKED-OWNER) | P10_devices.json shows the paired iPhone. Required build/export scripts would regenerate shared locked assets/projects. Isolated project attempts preserved in P10_isolated-device-build.log and P10_isolated-device-retry.log; first relative project-reference failure corrected, second failed at IL2CPP IPC sandbox permission. Current export predates this tutorial work; no stale app installed. Owner-produced current export is required. |
| P10.3 | FAIL(BLOCKED-OWNER) | 1,664 foreign paths were staged at baseline; none removed. Own code adds exactly 33 paths. All original shared-file foreign hunks preserved (P10_foreign-hunks-preserved.json); owned whitespace check passes. Native test fixtures regenerate unowned screenshot/video outputs (P10_new-unowned-working-paths.txt). No unrelated code was intentionally edited or staged. |

Full regression command: test_sim `-only-testing:GolfArcadeTests -only-testing:GolfArcadeUITests/SportsNavigationTests -resultBundlePath work/onboarding/P10_native.xcresult`. MCP timed out at 300s, but actual xcodebuild finished; final xcresult summary is authoritative.

Final staged source compiles: isolated `xcodebuild build-for-testing` with original header/plist/entitlement settings → P10_final-build.log, TEST BUILD SUCCEEDED. Final focused tests and partial setup recording are listed in FINAL_RESULT.md.
