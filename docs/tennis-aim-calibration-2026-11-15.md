# Tennis aim calibration (Play → Calibration), 2026-11-15

Adnan: tennis aiming is unintuitive. Plan: he demonstrates how every shot should be aimed on his phone, the motion is recorded and
analysed, the range of ways people aim is derived, and aiming is made to work; swing timing then sets ball speed and contact quality.
This is step one: a **Calibration** entry that runs a practice court where the player swings at left / straight / right targets, learns
their racket angles, and records every take for analysis.

**Not yet tried on a phone and TV.** Verified in the simulator (see "Verification"). The phone currently has an older build; see
"Putting it on the phone".

## What the player sees

1. Play → tennis → **Calibration** (the TV menu's tennis modes list, between Training and Local play; also a row on the phone's Play list).
2. The usual setup: TV scan, TV delay, timing check, Ready.
3. The TV feeds one ball at a time to a target ring. The phone says which shot ("Forehand · LEFT") and how to hold the phone
   (forehand: screen faces the TV; backhand: back of the phone faces the TV).
4. **12 learning takes** (6 forehand, 6 backhand, each of left / straight / right twice) fit the player's racket angles. **12 checking
   takes** on fresh targets must land in the asked lane (5 of 6 per wing). A wing that fails is re-learned.
5. When it passes, the profile is saved (`tennis.aim.v1.<player>.<hand>` in UserDefaults) and every later match uses it
   (`SportsSession.start` → `motion.setAimProfile(storedAimProfile())`). Buttons: **Done**, **Stop**, **Start over** (forgets the saved profile).

## How it is wired

- The lesson logic (`TennisAimLesson`, `TennisAimWing.fit`, `TennisAimProfile`, in `SteeringFilter.swift`) and Unity's aim drill
  (`TennisAimPractice.cs`; commands `aimPractice` / `aimFeed`, events `aimLanding` / `aimMiss` in `NativeSportsSession.cs`) already
  existed. The code that **ran** the lesson was removed with the old tutorials (commit 70ac8b8191). It is restored in `SportsSession.swift`:
  `beginAimingSetup`, `queueAimFeed`, `receiveAimLanding`, `restartCalibration`, `finishCalibration`, plus the `aimLanding` event case.
- Entry points:
  - Unity menu: `MenuHud.cs` (tennis modes row `bay-tennis-calibration`), `MenuHud.Setup.cs` (preview text).
  - `HubSession.swift`: route `bay-tennis-calibration` → `TennisMenu.begin(MenuLaunch(mode: .calibration), skipMap: true)`; solo-locked with friends; loader label.
  - `TennisMenu.swift`: `MenuLaunch.Mode.calibration`, Play-list row `calibration`, back target `.main`. Unity gets plain `training` mode; the aim
    drill is switched on after Ready (`readyToPlay` → `beginAimingSetup`).
  - Phone screen: `CalibrationPanel` in `TennisPlayViews.swift` (shown while `calibrationMode` and playing).
- Every accepted or rejected take is written to `SportsDiagnostics.log` (Settings → Send diagnostics) with its raw face-angle trace:
  `aimcal take phase=capture|check wing=0|1 lane=-1|0|1 angle=… facing=… landingX=… legal=… accepted=… trace=ms:angle:rate,…`.
  `TennisAimSwing.trace` carries the last 1.2 s of face angle and gyro rate (`SportsMotion.faceTrace`).

## Analysing the takes

```bash
python3 -I Tools/aimcal_analyze.py SportsDiagnostics.log           # per wing: where left/straight/right sit, spread, best reading,
                                                                   # lane cut points relative to straight, checking-phase accuracy
python3 -I Tools/aimcal_analyze.py --json out.json SportsDiagnostics.log
python3 -I Tools/aimcal_analyze.py --selftest                      # synthetic takes, no phone
```

Today's game calls a swing left/right once the face is about 13.6° either side of the player's straight (aim 0.3 of 0.8, span 32°).
The report compares that with the cut points the player's own takes need, and which reading (confirm angle, angle at the gyro peak,
mean over the last 120 ms) separates the lanes best. That is the evidence for a fixed mapping that needs no per-player lesson.

## Verification (simulator, no phone)

- `AimCalibrationTests` (new): plays all 24 takes through the real `SportsSession` (Unity's part simulated: the swing the phone read and
  the landing), checks the lesson completes, the profile is saved and correct, all 24 takes are in the log with traces; stale and
  malformed landings are ignored; the wrong grip does not count; a normal match never starts the lesson.
- `MenuBetaTests` (Play list has the row, tapping it launches `.calibration`), `HubSessionTests` (the bay route), `SportsIntegrationTests` (lesson maths).
- Unity: the aim drill's own PlayMode tests (`TennisGameplayImprovementPlayTests`) are unchanged. The Unity export with the new menu row
  built with 0 errors.
- `aimcal_analyze.py --selftest`.
- Last run (20:2x, simulator iPhone 17 Pro): `AimCalibrationTests` 3/3, `MenuBetaTests` 8/8; the earlier wider run (62 tests incl. `HubSessionTests`, `SportsIntegrationTests`) had one failure, a log-format check (trace offset truncated instead of rounded), now fixed.
- The phone app compiled for iphoneos (`BUILD SUCCEEDED`).

## Putting it on the phone

**The phone currently has the 19:55 install, a half-updated app that crashed on load three times. Replace it.** A fresh, complete build
is prepared and has not been installed (Adnan asked for no phone builds while he was away):

- `work/phone-build-20261115-aim/DerivedData/Build/Products/Debug-iphoneos/GolfArcade.app`, built 20:25, `BUILD SUCCEEDED`
  (`xcode-build.log`). It has today's Unity export with the Calibration row (confirmed in `global-metadata.dat`) and the Swift in this doc.
- To install: unlock the phone, make it reachable (USB cable, or Personal Hotspot with the Mac joined; guest Wi-Fi blocks it), free
  about 3.5 GB on the phone, then run `work/phone-build-20261115-aim/install.sh` (it waits for the phone, installs, launches).
- To rebuild first: `work/phone-build-20261115-aim/xcode.sh`; install only if `xcode-build.log` ends in `BUILD SUCCEEDED`.

Lessons from today: the 19:55 install ran after a **failed** build and put a half-updated app on the phone (it crashed on load).
`install.sh` must only run after `BUILD SUCCEEDED`. Another chat was removing the walkable plaza / `menuMode` from `HubSession.swift`,
`SportsHome.swift` and `SportsSession.swift` in the shared tree at the same time, so a clone must take all Swift files from one moment.


## Swing-direction aim (11-15, after the first device run)

Adnan, after calibrating on the phone: "it was determining where i was aiming based on where i was positioning my phone, not based
upon how i was swinging ... i could simply move my phone to the right, then swing and it would aim to that spot". That is how it
worked: the aim was the **racket face's heading** (which way the phone pointed), read every sample, and the practice court drew a live
aim ring following it before the swing. Unity locks the aim at the swing's confirmation, so wherever the phone pointed then won.
It also made local 1v1 (little room) and where the TV was scanned from matter far too much.

His 121 takes (`Tools/aimcal_analyze.py` on his log) back it up: forehand left/straight/right face angles overlapped heavily (left
-80..+13 deg, right -52..+59), 22-31 % of takes sat nearer another lane, and only 7/18 forehands and 9/14 backhands landed in the asked
lane. The 7 degree "tight cluster" rule in `TennisAimWing.fit` made the lesson repeat itself for 121 takes.

Now (`work/aim-swing-direction-1115/patch.py`, applied to the repo and the build clone):
- **Aim = the direction the phone travels through the swing** (`TennisSwingPath` in `SteeringFilter.swift`): CoreMotion's
  user acceleration turned into the room frame, summed from 80 ms before the stroke's onset, its heading relative to the TV. Updated
  while the stroke is under way and fixed when it is confirmed (when Unity locks the shot). Before a swing the aim is straight, so
  pointing or carrying the phone never aims. Position, scan spot and grip do not enter it.
- The calibration lesson learns each player's straight / left / right **swing directions** per wing (lane medians; a lane is only
  rejected when it is not clearly on its own side). Profiles are stored under `tennis.aim.v2.*`; the v1 face profiles are ignored.
- The practice court no longer draws the pointing-driven aim ring for motion play (`TennisGame.cs`, `aimsAhead`).
- Every take logs `angle` (swing direction) and `face` (racket face, for comparison), and the trace now carries the room
  acceleration (side, toward the TV), so the analyzer can compare the two readings and re-derive the direction offline (`path250`).
- Copy: the phone says "The direction you swing aims, not where the phone points."

Not yet measured on the phone: how cleanly real swings separate by direction, and whether 80 ms lead / confirmation timing is the
best window. The next calibration log answers both (`aimcal_analyze.py`: compare `confirm` vs `face` vs `path250`).

## Not done

- No phone or TV run: the Unity drill + real swings + the TV ring have not been seen together.
- The fixed (no-lesson) mapping itself: waits on real takes and the analyser's report.
- Timing → ball speed and contact quality are unchanged (already built 10-24 / 10-26).

## Fix 2 (11-16): inverted left/right, straight lane unreachable

Adnan after the first swing-direction build: "left and right are inverted, and its not feasible to aim center court".
His 27 takes (log pulled with `devicectl device copy from --domain-type appDataContainer ... Documents/SportsDiagnostics.log`):

- **Inverted**: CoreMotion reports acceleration = gravity + userAcceleration with gravity (0,0,-1) g for a phone lying flat,
  the opposite sign to the real acceleration. Integrating userAcceleration as-is gave a velocity pointing backwards
  (most takes read 120..180 deg), which also mirrors left/right. Negated, the velocity runs face-first (the way the
  hitting face points, as a racket moves) in most takes. Fixed in `TennisSwingPath.roomAcceleration`.
- **Straight unreachable**: the straight lane was +-13.6 deg, and slow readings (the turn out of the backswing,
  under ~1 m/s) or backward ones were thrown to a full side. Now a swing under 1 m/s or more than 100 deg from the TV has
  no direction (it goes straight), and straight is everything up to half way to each side lane (15..30 deg; +-25 deg
  uncalibrated, `TennisAimWing.standard` = 0 / -50 / +50). Learned side lanes must be >= 24 deg from straight.
- Replaying his 27 takes: the old build put 9 in the asked lane, the new rules 16; asked-straight forehands 3/11 -> 9/11.
  The misses are mostly takes where he swung the opposite way on purpose to beat the inversion.
- Profiles move to `tennis.aim.v3.*` (v2 was learned inverted).
- New log line per swing, `aimcal post locked=<angle> ms:dir:speed=...`: where the swing direction goes in the 200 ms after
  the shot locks. In his takes the hand was often still slow (1-3 m/s) at confirmation, so the lock may be early; this line
  says whether a later lock would read the swing better.
- Patch: `work/aim-swing-direction-1115/patch2.py` (after patch.py); pipeline `pipeline2.sh` (tests, Release build, install).

## Calibration crash (11-16 14:55)

Adnan: "calibration crashes the game". Phone log pulled 14:57 (no crash report for it; the only JetsamEvent that day, 13:02, killed Instagram):
- 14:55:03 `launch tennis bay=bay-tennis-calibration footprint=2143MB left=1232MB`, then nothing: no `loaded tennis`, no memory warning.
- The successful calibration load the night before (23:57, same Unity build): launch at 2007 MB, memory warnings at 3115-3126 MB,
  `loaded tennis footprint=3182MB left=193MB`. The app's limit is about 3375 MB (footprint + left), so the load peaks within ~200 MB of it.
- 14:55 started 136 MB higher, which uses up most of that margin: most likely the same per-process memory kill as 10-26 party golf
  (those leave no .ips). Fix 2 changed only aim maths and a log line; it does not change memory.
- Not confirmed: needs the phone's unified log (`sudo log collect --device-udid ...`, look for JETSAM_REASON_MEMORY_PERPROCESSLIMIT).
- Fix options: cut the tennis load peak (what is resident from the hub during the load), and/or the Increased Memory Limit
  entitlement (`com.apple.developer.kernel.increased-memory-limit`, not in GolfArcade.entitlements today).
- **Prepared 11-16 (not installed, phone unreachable):** `work/aim-swing-direction-1115/patch3.py` adds the Increased Memory Limit
  entitlement (repo + build clone). Release build `BUILD SUCCEEDED`; the app signature and the provisioning profile both carry
  `com.apple.developer.kernel.increased-memory-limit`, and the profile includes his phone. Install: `work/phone-build-20261115-aim/install-release.sh`
  (waits for the phone). Check on device: the `launch tennis ... left=` figure should be far above ~1.2 GB.
  Not done: cutting the load peak itself (Unity side, needs a re-export).
