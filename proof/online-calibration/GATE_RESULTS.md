# Online tennis calibration — 2026-10-14

Implementation is complete in the native app sources. This is simulator and deterministic protocol proof, not a claim of a successful internet match on physical phones. No device installation, Unity export, commit, or deployment was performed.

## Implemented flow

Each competing phone opens its own direction setup immediately after match launch. Its opponent's renderer no longer controls whether the calibration prompt is visible. A one-second stable hold sets direction, with visual progress and a success haptic; one Ready tap captures centre. Native setup can complete before the local renderer is ready. The local first-frame cover lifts independently, while the actual match still requires both rendered courts, both completed controllers and the connection check.

The host accepts completed calibration during loading and retains it when entering the calibration phase. Loaded/calibrated reports retry until acknowledged. Loaded retries carry a stable report ID, so duplicates cannot clear Ready; genuine renderer reloads still require calibration. Repeated first-frame events within a native session do not announce a new renderer. A missed start message can be requested again. Both phones use the same scheduled three-second countdown. Connection grading starts during loading.

Setup shows each player's actual progress, specific sensor problems, manual direction/retry/touch alternatives, loading recovery, weak-link Play anyway for the host, and Leave. The TV repeats setup instructions. The controller-only phone does not receive a TV loading cover over its controls. Remote Quick Match requires this phone's display before matchmaking. Friends play requires one display per player unless the host explicitly selects Sharing a TV. Nearby defaults to shared-screen play. Immediate rematches may reuse direction only while the original AR/IMU tracking is still live, recent and normal; Ready still captures centre again. The retained sensors stop after ten seconds if no rematch starts.

## Gates

- GATE: BUILD PASS — simulator native build and subsequent test builds succeeded.
- GATE: INDEPENDENT_SETUP PASS — production phone-root snapshot shows the direction prompt while the opponent is loading. Local Ready is accepted before the local renderer is ready.
- GATE: EARLY_CALIBRATION PASS — both controllers can complete before either court renders; loading completion retains both acknowledgements and schedules one start per runtime.
- GATE: LOST_AND_DUPLICATE_MESSAGES PASS — dropped calibration is retried, lost loaded acknowledgements do not invalidate Ready, and missing run messages recover onto the same clock.
- GATE: REAL_RELOAD PASS — a new runtime load invalidates its prior calibration; retry machinery cannot falsely mark it ready again. A repeated first-frame event preserves calibration.
- GATE: PARALLEL_CONNECTION_CHECK PASS — a steady connection measured while courts load remains accepted when the last court finishes.
- GATE: SCREEN_REQUIREMENTS PASS — remote players require a display each; explicit Sharing a TV enables controller-only split-screen roles; Quick Match without a local display fails before search/authentication.
- GATE: REGRESSION PASS — 147 checks passed in the combined multiplayer, menu, campaign, hub party and UI run. After the last production edit, 103 multiplayer/menu checks passed, including the new repeated-renderer-event regression. The final two UI checks also passed. No failed or skipped tests in these successful runs.
- GATE: VISUAL_LAYOUT PASS — native hosted phone/TV screenshots reviewed, including direction, hold progress, Ready, waiting, countdown, sensor recovery, larger Dynamic Type, display requirements and screen sharing. Party controls have reserved space above the setup content. Recovery content remains scrollable.
- GATE: FULL_MOTION_PROOF FAIL — the simulator screen recorder did not reliably capture the short-lived test windows or every setup transition. Diagnostic recordings and extracted frames are retained in `work/online-calibration/`; they are not accepted motion or performance proof. Screenshots above are actual UIKit/SwiftUI renders with explicitly supplied fixture sensor/network state.
- GATE: TWO_PHYSICAL_PHONES_OVER_INTERNET FAIL — not run. Real Game Center connectivity, AirPlay routing, camera/IMU calibration speed, haptics, retained tracking on rematch, and sustained device frame rate remain unverified by this simulator session. Online field ship is not declared PASS.

## Evidence

- `setup-preview.jpg`: direction → Ready → countdown overview.
- `online-setup-direction-phone.png`: full production phone-root setup while the opponent is loading.
- `online-setup-hold-phone.png`, `online-setup-ready-phone.png`, `online-setup-waiting-phone.png`, `online-setup-countdown-phone.png`, `online-setup-receive-phone.png`.
- `online-setup-recovery-phone.png`, `online-setup-recovery-large-text.png`.
- `online-setup-direction-tv.png`, `online-display-required.png`, `online-sharing-tv.png`.
- `test-summary.json`: compact tool-confirmed results.
- Result bundles: `/private/tmp/tennis-calibration-final.xcresult`, `/private/tmp/tennis-calibration-render-ready-regression.xcresult`, `/private/tmp/tennis-calibration-visible-ui.xcresult`.
- Task-only before copies and patches: `work/online-calibration/before/`, `work/online-calibration/patches/`. Pre-existing staged and unstaged work was preserved.

## Remaining field check

Install the same updated integrated native build on two physical iPhones with separate Game Center accounts and separate networks, with each phone connected to its own display. Delay one phone's court load and confirm the other still sets direction and taps Ready; confirm the delayed phone gets its own prompt, both show the countdown and reach the first serve. Repeat with a dark room/camera permission failure, a genuine reconnect, an immediate rematch, and Nearby with one shared TV. Save both phones' SportsDiagnostics logs. A single internet match is insufficient evidence for the 3–5 second setup target; measure repeated attempts after sensors become ready.
