# App Review 2026-11-07 (1.0 (18)) and phone-only fixes

User asks, 2026-11-07:
1. Guideline 5: CallKit must not be active in China.
2. Remove ARKit if it is not used. (Guideline 4.2.1 was cut off in the pasted message.)
3. Phone-only menu: words cover the hero, the hero is hard to see, zoom out a bit.
4. Phone-only golf plays differently from AirPlay: the camera can't fly up to see where the shot goes, and the aim is far more sensitive.

| Gate | Result | Proof |
|---|---|---|
| No CallKit in the app: `CallWatcher` reads FaceTime calls from GroupActivities' `GroupStateObserver`, not CXCallObserver | PASS | Simulator build: `otool -L` has no CallKit, `nm -u` finds 0 `CXCall` symbols; no `import CallKit` left in the repo |
| Swift app builds (GolfArcade, iOS Simulator) | PASS | xcodebuild BUILD SUCCEEDED |
| ARKit removed (branch `app-review-11-07-no-arkit`; the ARKit version is backed up on `app-review-11-07-with-arkit`, 557302ba) | PASS: clean Simulator build links no ARKit, CallKit or RealityKit (`otool -L`, `nm -u`: no swiftARKit / AR classes). Unity-iPhone.xcodeproj links no ARKit either | see right |
| Same tennis functions without ARKit: TV found by the camera (AVFoundation + the same Vision search), direction, level and stillness from the motion sensors, TV delay from the same flash probe on AVFoundation frames (host-clock timestamps), camera off from Ready on | PASS in unit tests and build; NOT run on a phone with a TV | SportsIntegrationTests, SportsScreenFinderTests, SportsDelayProbeTests |
| Lob/slice `lift` from the motion sensors (`SportsVerticalTravel`: gyro-gated sensor offset, leaky double integration, 5 cm dead band, restart at Ready and after every stroke) | PASS in simulation: 25 cm raise reads .21 (lob), 20 cm .16 (no lob), 8 cm dip -.066 (slice), 3 cm 0, wobble and sensor offsets 0. NOT tuned on real swings | SportsVerticalTravelTests (5) |
| Not kept | Side-to-side court position (never switched on: `ManualRallyMovement` is never set) and the LiDAR distance readout during the scan | — |
| Handheld golf: the pad is the TV sheet's joystick: x turns the aim at 1.5 x 28 deg/s (0.2x putting), 0.2 dead zone, y looks up the hole; ▲ holds the fly-up view, ▼ comes back | PASS | `NativeGolfFlowTests.HandheldStickTurnsAtTheSheetsRateAndLooksUpTheHole`; `proof/handheld_look_up.jpg` (address, stick up, let go) |
| With a TV nothing changes (the Swift pad still points the line on the map; Unity's sheet still drives its own stick) | PASS (code path unchanged when `phonePlay` is false) | — |
| Phone-only menu: the hero has the top of the screen, the menu's 16:9 frame sits under him, the app's Back is in the bottom 17 % | PASS | `proof/menu_before_after.jpg` (first frame = before) |
| No words over the hero on the phone (name plate and +JOIN tile hidden there; INVITE FRIENDS stays in the list) | PASS | same |
| Hero head to toe, clear of the Dynamic Island, a little wider lens than the TV (36 deg vs 32 deg) | PASS | same |
| The venue plate is cropped for the phone's lens instead of stretched (identical on a 16:9 TV) | PASS | same |
| Layout rule shared by Unity and Swift (`HubWorld.PhoneMenuView` / `MenuTouchPad`), with a band fallback for short screens | PASS | `PhoneMenuLayoutTests` x3 |
| Existing menu/phone tests | PASS | MenuPointerTests 5 pass + 1 skip (film, ML_OUT unset); HubPhoneOnlyTests 4/4; HandheldLayoutTests 3/3 |
| `NativeGolfFlowTests.PhoneCommandsAimChangeClubsPauseAndLaunchWithoutCalibration` | FAIL, already failing before these changes: it puts the session in touch mode, and touch mode stopped passing swing samples to golf on 10-22 | — |

Not checked:
- No run on a device. The Unity iOS export still has to be rebuilt for the Unity changes.
- The Swift footer under the phone menu is type-checked only. The Simulator check (`-phoneMenuCheck <frame.jpg>`) needs Simulator access.
- The menu's words are still the TV layout scaled to the phone's width, so the small lines are about 5 pt. A portrait menu layout would be its own job.

Captures: `Unity/Assets/Tests/PlayMode/PhoneMenuCapture.cs` with `PM_OUT=<dir>` (iPhone 15 Pro frame, Dynamic Island drawn in, app footer as a placeholder).
