# Presentation implementation verification

Updated October 8, 2026. Brief: `ArtDir/ui/34_GAME_PRESENTATION_RESEARCH.md`, revision 2. Plan: `ArtDir/ui/35_GAME_PRESENTATION_EXECUTION_PLAN.md`.

## Implemented behavior

- Native loading cover appears before Unity boot. Loading reflects scene work and target-camera readiness, with solo/multiplayer read minimums, cached equipped portraits, readable names, missing-player status, stalled-load actions and readable tip carryover.
- Shared cut policy supports Full / Short / Off, completed first-view persistence, thermal/Low fallback, bounded timing, cancellation and consumed skip input. Native preferences flow through the existing session bridge.
- Tennis intro adapters use 7.2 / 3.5 second budgets; ordinary reactions and aces cannot be extended by equipped emotes. Boundary precedence prevents stacked celebrations. Final results wait for input.
- Golf uses bounded venue/walk-on/address adapters, preserves calibration, retains hole information, and offers Overview without changing the shot. Reaction and boundary budgets replace long automatic holds; optional native replays do not delay readiness.
- Multiplayer uses required-competitor readiness and a scheduled shared run clock, short shared introductions and bounded reactions. Spectators do not block loading. A 20-second stall offers Keep waiting / Leave.
- Native exit cover precedes teardown and destination reveal. Cue cancellation and music ducking are wired through the presentation stinger interface.

These are functional changes using existing camera paths and actors. The authored camera, framing, animation and audio polish described in P4–P7 has not passed acceptance.

## Prerequisite verdict

**GATE: visual prerequisites FAIL.** The actual High-tier tennis camera reports `post=True`; the actual High-tier golf camera reports `post=False`. Evidence: `UnityReview/Library/Captures/presentation-prerequisites/{Tennis,Golf}-post.txt` and actual editor-rendered stills in that directory. The audit test passed because it recorded the active cameras; that does not make the recorded golf visual prerequisite pass. Lighting/contact-shadow/turf approval remains unverified. Per P0, cinematic visual tuning is held until this dependency passes. Character sources, maps, lighting and accepted gameplay camera destinations were preserved.

## Completed checks

| Check | Result | Evidence |
|---|---|---|
| Native final targeted suite | 71 passed, 0 failed: 27 multiplayer, 40 sports integration, 4 loading/rematch tests | `native-complete-tests.xcresult`, `native-complete-tests.log` |
| Final Unity iOS export | Succeeded 234s errors=0 warnings=23 -> /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/presentation/UnityBuild/Builds/iOS | `ios-export-final.log` |
| Final integrated iPhoneOS Release build | PASS; unsigned, not installed; debug symbols disabled for review | `integrated-release-final.log`, `build_verdict.json` |
| Unity EditMode policy + multiplayer rules | 34 passed, 0 failed | `editor-policy.xml` |
| Final rendered review after repeat-policy fixes | 6 passed, 0 failed (24 recorded scenarios + 5 flow checks) | `film-editor-retry.xml` |
| Rendered PlayMode flow suite | 4 passed, 0 failed | `final-flow.xml` |
| Rendered eight-launch matrix + consumed golf motion | 2 passed, 0 failed | `final-launch.xml` |
| Twenty ordinary/ace reactions with emote/hold attempts | Maximum 1.4514 seconds | `UnityReview/Library/Captures/presentation-prerequisites/L5_point_to_serve.json` |
| Native loading card snapshot | Passed | Earlier snapshot run and `review/loading-*.png` |
| Broad native menu/campaign suite | 92 passed, 2 failed | Tutorial/navigation expectations in `testEveryScreenIsReachableFromTheTitle` and `testTheTutorialUnlocksEverythingElseInASport`; baseline execution not established |
| Plain Mono full harness | 309 passed, 4 failed | Two Unity JSON internal-call failures and two campaign-balance null references. Native/editor suites above are separate results |

The 20-point sample uses fixed simulation steps divided by gameplay speed, not physical-device wall-clock measurements. The earlier aggregate eight-launch matrix timed out at its 180-second test budget; the retry gives the whole matrix 600 seconds while retaining the production first-render deadline. The retry passed: all eight launch combinations reached an actually rendered target camera; the golf Overview skip test also passed and requires a quiet pose before shot tracking resumes. The two-test run is recorded in `final-launch.xml`. The final frozen source exported successfully in 234 seconds with zero errors and 23 warnings. The integrated unsigned iPhoneOS Release build passed. Signing and physical-device installation were not performed.

## Acceptance ledger

Missing proof is FAIL under the repository's binary-gate policy. FAIL below distinguishes incomplete acceptance from a demonstrated implementation defect.

| Gate | Verdict | Evidence and remaining work |
|---|---|---|
| G1 covered startup/exit | FAIL | Native cover implementation and model tests pass; integrated phone/TV frame checks are missing |
| G2 truthful readiness and ≤0.35 s eligible transition | FAIL | Fake progress removed; fake-clock read/readiness tests pass; actual integrated load telemetry is missing |
| G3 complete capture matrix | FAIL | Native loading stills and editor game stills exist; scripted editor/component recordings are supporting evidence; integrated applicable L1–L8 videos remain missing |
| G4 beat budgets and control release | FAIL | Pure budgets and four rendered flows pass; 20-point maximum 1.4514 s; full integrated beat telemetry is missing |
| G5 safe skip and retained information | FAIL | Director skip cleanup, tennis Off and unchanged golf Overview pass; complete motion/touch/phone/TV skip matrix is missing |
| G6 camera handoff | FAIL | Existing destination cameras retained and eased adapters implemented; target-size camera delta/frame measurements are missing |
| G7 hero size and face holds | FAIL | Visual tuning held; target-size measurements missing |
| G8 multiplayer synchronization | FAIL | Scheduled-clock and readiness tests pass; actual two-device tennis and two/four-device golf ≤300 ms proof missing |
| G9 shipping visual conditions | FAIL | Golf High camera has post-processing disabled; opt-in visual flags explicitly disabled for the final rendered launch retry/build |
| G10 user video approval | FAIL | Complete integrated videos have not been supplied for approval |

## Phase status

P0 baseline recorded and camera prerequisite failure documented. P1–P3 functional implementation and targeted verification are complete; integrated acceptance remains open. P4–P7 timing/state adapters and cues are implemented, with authored visual/audio integration held or unverified. P8 targeted verification and the final unsigned integrated build are complete. Integrated physical phone/TV acceptance remains open; further recording was waived by the user.

Unsupported doubles are explicitly excluded: tennis currently supports two active competitors, while golf supports four. Normal gameplay remains on the external display with the phone as controller; phone game renders are explicit benchmark scenarios.

The paired iPhone has Developer Mode enabled but reports disconnected transport and unavailable developer services. There is no device-capture PASS from this run. Do not use the existing stale main Unity export as proof of these changes.

## Final wrap-up

The user waived further recording. Existing completed Unity Editor clips are retained in the output recordings folder with an explicit source manifest. The native simulator component capture test passed (1 test, 204.112 seconds), using scripted readiness and peer fixtures. These recordings do not establish real device/TV coverage, multiplayer synchronization, audio mixing or performance acceptance.
