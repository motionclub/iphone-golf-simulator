# Contributing

1. Branch from `testing` using `feature/<short-name>`, `fix/<short-name>`, or `chore/<short-name>`.
2. Keep changes focused and include tests for deterministic swing or shot behavior.
3. Regenerate `GolfArcade.xcodeproj` after editing `project.yml`.
4. Open a pull request into `testing`; all required checks must pass before merge.
5. Promote tested releases from `testing` to `main` by pull request. Pull requests to `main` from every other branch are rejected by the `main-source-policy` check.

Direct pushes, force pushes, and branch deletion are disabled for `main` and `testing`, including for repository administrators.

## Checks and local testing

- `build-and-test` (required) compiles everything and runs the unit suite, `GolfArcadeTests`. It takes a few minutes; keep it green.
- `ui-tests` runs `SportsNavigationTests` and `MenuNavigationRegressionTests` on two parallel workers. They report on every pull request but do not block a merge, so a slow runner never holds development up. Fix them all the same.
- Locally, run the unit suite while you work and the UI class you touched before you open a pull request:

```bash
xcodebuild test -project GolfArcade.xcodeproj -scheme GolfArcade -only-testing:GolfArcadeTests -destination 'platform=iOS Simulator,name=iPhone 16 Pro'
```

UI tests drive the app with launch arguments: `-skipOnboarding` / `-forceOnboarding` / `-resetOnboarding`, `-golfControllerDesign` (the golf controller with no Unity; add `-golfControllerNotReady` or `-golfControllerLoading`), `-handheldCheck <sport>` (handheld play over a stand-in frame), `-controllerMenuCheck`, `-controllerPhaseCheck <phase>`, `-clubCloudOff` and `--lobby`. They are handy for development too.

Prefer waiting on state (`waitForExistence`, or polling a label or value) over fixed sleeps or `XCTNSPredicateExpectation`: a failed predicate evaluation captures a full accessibility snapshot, which is slow in the camera screen.
