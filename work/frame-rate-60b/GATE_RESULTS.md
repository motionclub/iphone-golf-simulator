# FRAME_RATE_60B — gate results (chat 1, 2026-10-17)

Brief: `work/delegation-2026-10-17/01_60fps_everywhere.md` plus Adnan's addition, *60 fps at ≥ 1080p everywhere* (budget: `BUDGET.md`).
Nothing committed. Every Unity run was in an APFS clone, with `GOLF_MUTE=1` and the Editor audio master muted (`FR60BMute`, clone-only).

## Summary

| gate | result | evidence |
|---|---|---|
| INVENTORY | **PASS** | `INVENTORY.csv`: 294 clips (279 shipped) + 13 baked tracks / timed motions. Every row is 60 Hz or has a written reason. Open item (chat 4's file): `ReadyIdle` is still 30 Hz in `Unity/`; a 60 Hz candidate is ready |
| MATCH | **PASS** | golf ≤ 0.03 mm at shared frames, all other edits 0 mm (keys kept exactly). Copied emotes ≤ 0.6 mm vs their 60 Hz source |
| RUNTIME (Editor) | **PASS** | 1920×1080 Game view: median 59.9–60.1 fps in tennis intro, tennis match, golf intro, golf hole and plaza; 0 % of frames in the 30 fps slot |
| RUNTIME (device / AirPlay) | **NOT RUN** | no phone or AirPlay receiver in this session |
| RES_1080 (Editor) | **PASS** | all five scenes captured at exactly 1920×1080 at ≥ 58 median; render scale 1.0. The step-down's 0.85 render scale is removed, with a test |
| RES_1080 (device, AirPlay, lobby capture) | **NOT RUN** | code audit only: the TV renders at 1920×1080 (a larger TV is capped there, never lower), the phone renders natively, and SceneKit views use the screen's native scale |
| NO_STEP | **PASS** with chat 4's `ReadyIdle` candidate: 31/31 moving tracks. **FAIL** on today's `Unity/` for 2 tracks (tennis intro hand + racket = `ReadyIdle`, chat 4's file) | `proof/steps.jpg`, `proof/{before,after,runtime}/no_step*.json` |
| REGRESSION | **PASS** (failures same as before / not mine) | EditMode 598/604, golf PlayMode 24/28. Every failure is listed below with its cause |

Proof images sent to Adnan: `proof/res1080.jpg`, `proof/steps.jpg`.

## What changed

### Clips (assets: install with `scripts/install.sh install`, undo with `rollback`)
- **Golf hero** `Resources/Hero/golfer_{m,f}.fbx` + `_clips.json`: 60 fps, built by `scripts/golf60.py`, a fork of `work/swing-fix/scripts/splice_swings.py` run on the shipped FBX.
  - **Drive, IronSwing, HalfSwing, Chip:** `golf_swing.py`'s swings are continuous in time, so they are posed again every 1/60 s. At the old frames they equal the installed takes: verify 0.001–0.03 mm.
    - Between the old frames the club head now follows the real arc instead of the 30 Hz chord: up to **157–181 mm** apart at impact for Drive/Iron, 84 mm for the HalfSwing, 8–9 mm for the Chip.
  - **Putt, Idle, Wave, Cheer, FistPump:** their sources are 30 fps bakes; the Putt also predates the current `golf_swing.py` putt (re-posing it moved the head 22 mm, so it is not re-posed). Every installed key is kept (0.0 mm) and a monotone cubic fills each 1/60 s.
  - **Stale golf emotes replaced** (memory `golf-emotes-stale-clips`): Emote_Spike/Scuba/Thrust and Intro_Wave/BringIt/Pushups are now copied frame for frame from the current rev-37 match-hero clips at 60 Hz, and Walk/RunForward from the current 60 Hz match-hero clips (≤ 0.6 mm vs source).
    - Lengths are now the approved ones: Spike 3.2 s, Scuba 4.7 s, Thrust 3.5 s (the stale Oct 4 takes were all 2.0 s).
    - Fingers stay at rest, as before (no racket in golf).
  - `_clips.json`: fps 60, frames, top and impact doubled (the same seconds), so GolferView's timing is unchanged.
- **Shared rev-37 emotes** `Characters/MatchHeroes/<Sex>/<Sex>_{Emote_Spike,Emote_Scuba,Emote_Thrust,Intro_Wave,Intro_BringIt,Intro_Pushups}.fbx` (12 files): **header only**.
  - The files carried 60 Hz keys but said 30 fps, and Unity's *Resample Curves* resamples at the file's rate, so the game played them at 30 Hz (138 of 152 moving curves on 33 ms keys).
  - `scripts/fbx_timemode60.py` sets TimeMode to 60; all 540 curves are verified identical, key for key. The `.fbx.meta` `lastFrame` is doubled (`scripts/meta_double.py`).
- **Golf hole-12 cinematic** `Resources/Course/hole_12_cinematic.fbx` (the ball + trails the signature-shot intro plays): its source `.blend` is gone. `scripts/fbx_densify60.py` keeps every key and fills each 1/60 s with a monotone cubic (83,889 keys added), as a binary curve edit that leaves meshes and IDs untouched.
- Unity check after install (clone): every one of these is `clip_fps 60` with `moving_curves_at_30hz = 0` and unchanged lengths (`logs/inventory_raw_after.csv`).

### Code (edited in place in `Unity/` and `GolfArcade/`)
- `Scripts/Game/SignatureShot.cs`: the hole-12 shot file (ball, chase camera, wide camera and lens, sampled at 30 fps) is played on a Catmull-Rom curve through every sample instead of straight lines. The file's own frames are identical (0 m); the 30 Hz kinks are gone (`proof/hole12_track_check.json`, parity 10¹⁰ → 1.0).
- `Scripts/Game/FrameProbe.cs` (`FrameRate.Lift`): a 60 fps floor at boot and on every scene load, with vSync off. Before this, anything drawn before NativeSportsSession or GolfGame set a target ran at the phone default (30). A 120 target is left alone.
- `Scripts/Tennis/TennisQuality.cs`: `StepDown` no longer sets render scale 0.85, which drew a 1080p TV at 918 lines. It now trims shadow distance (to 25 m minimum) and LOD bias instead. `StepDown(asset)` overload added for the test.
- `Editor/MatchHeroLockerExport.cs`: RigClips +`forehand` (the loading screen's practice swing as 60 Hz bone tracks). The exporter already sampled every clip at 60 Hz (`ClipRate = 60`).
- `GolfArcade/Unity/CharacterModelPreview.swift`: the practice swing plays the `forehand` bone track when the export has it, and keeps the old 12-pose morph only as a fallback for older exports.
- `GolfArcade/Unity/ClubEnvironmentView.swift`: club room SceneKit view and SpriteKit cinemagraph go from 30 to 60 fps.
- `GolfArcade/Unity/ClubDesign.swift`: the `ClubBackdrop` TimelineView interval goes from 1/30 to 1/60.
- `GolfArcade/Unity/GolfController.swift`: the golf aim stick sends to Unity every 1/60 s instead of 1/30, so the aim line, marker and golfer on the TV no longer turn in steps.
- New tests and tools:
  - `Tests/EditMode/FrameRate60bEditTests.cs`: the step-down never lowers the resolution; every target ≥ 60.
  - `Tests/PlayMode/FrameRate60bTests.cs`: RuntimeHoldsSixty (1080p Game view) and NothingStepsAtThirty (Explicit; run windowed).
  - `Editor/FrameRate60bInventory.cs`: the clip survey.

### Not changed, with the reason
- `ReadyIdle` (both sexes) is chat 4's file (their B18).
  - Candidate: `readyidle60/` (all keys kept, monotone in-betweens, 60 fps header, meta doubled). It is offered in `REQUESTS.md` and was used in the "after" capture.
  - With it, the tennis intro hand goes from parity 3.52 to 1.07.
- The hidden tennis gameplay rig (`StandardCharacters`, 122 mixed clips) is not drawn. The legacy V4 golfer (`Resources/Golfer`, 18 clips) is a fallback only, and is the retarget source of `matchhero_golf.py`. `ForehandPolished` is not played (ArmCorrected replaces it).
- iOS *Critical* thermal state still caps at 30 (device protection). The fixed timestep is 50 Hz, but nothing visible moves in FixedUpdate (no Rigidbodies).
- The lobby re-export is not run (chat 6's job). The exporter is proved on one sex below.

## Gate details

### RUNTIME + RES_1080 (Editor, `proof/runtime/runtime.jsonl`, `proof/res1080.jpg`)
`FrameRate60bTests.RuntimeHoldsSixty`, windowed, muted, Game view fixed at 1920×1080, real time (no capture clock):

| scene | median fps | p05 fps | frames in 30 fps slot | render target | target fps | render scale |
|---|---|---|---|---|---|---|
| tennis intro | 60.1 | 49.2 | 0 % | 1920×1080 | 60 | 1.0 |
| tennis match (autoplay) | 59.9 | 49.9 | 0 % | 1920×1080 | 60 | 1.0 |
| golf intro (presentation) | 59.9 | 51.2 | 0 % | 1920×1080 | 60 | 1.0 |
| golf hole (aim, drive, flight) | 59.9 | 48.6 | 0 % | 1920×1080 | 60 | 1.0 |
| plaza | 59.9 | 58.9 | 0 % | 1920×1080 | 60 | 1.0 |

- A second run (`logs/capture_after.log`) happened while two other chats' Editors were running (load average 38–47). Its numbers (17–60 fps) measure the host, not the game, and are not used.
- This Mac's Editor is not the phone: the device budget is in `BUDGET.md`, and the device run is NOT RUN.

### NO_STEP (`scripts/no_step.py`, `proof/steps.jpg`)
- Fixed 60 Hz game clock. Every drawn frame records the camera, the look point, the ball, the racket or club, the right hand and the head.
- PASS = duplicate frames < 5 % and a parity ratio < 2.5 (median acceleration on one frame parity vs the other; straight lines between 1/30 s keys give one parity ~0).

| capture | failing tracks |
|---|---|
| before (the project with my changes backed out) | golf intro hand + head (30 Hz golf Idle), golf tee hand + head, tennis intro hand + racket (ReadyIdle): 6 |
| after, my changes only (`proof/runtime`) | tennis intro hand + racket (ReadyIdle, chat 4): 2 |
| after + chat 4's ReadyIdle candidate (`proof/after`) | **none (0 of 31 moving tracks)** |

Notes:
- The golf drive itself does not show the comb even before, because GolferView re-times the swing clip, so its 30 Hz chords don't land on alternate frames. Its gain is the 157–181 mm chord-vs-arc measurement above.
- The in-game hole-12 capture did not trigger the signature shot (the harness's `JumpToHole(12)` + presentation went to the tee intro). The signature track was checked from its data instead: `scripts/hole12_track_check.py`.

### MATCH (`golf/out/golf60_report_{m,f}.json`, `logs/timemode60.log`, `logs/densify_hole12.log`)
- Golf authored swings: 0.001–0.03 mm at shared frames, both sexes.
- Golf upsampled takes: 0.0 mm.
- Copied emotes vs their 60 Hz source: ≤ 0.605 mm.
- Rev-37 emotes and the hole-12 cinematic: curve keys identical by construction (asserted).
- Motion that differs by design:
  - the new in-betweens;
  - the golf emotes and intros, now the approved rev-37 clips instead of the stale Oct 4 ones (the brief's item 3).

### REGRESSION
- **EditMode, full suite (clone):** 598/604.
  - `NoCodeOutsideTheRegistryNamesAnOlderHero` and `TheOneTVFixtureWrittenBySwiftParsesAndIsValid`: the clone has no `GolfArcade/` or `proof/` beside it (known clone-only failures).
  - `HeroClearanceTests` ×4: chat 3's solver, which changed between my two clones.
    - The 2 `ProxyIsFitted…` tests fail identically on a baseline clone without my files.
    - The 2 `BuriedHands…` tests play `Emote_Slump`, which I did not touch.
- **New tests:** `FrameRate60bEditTests` 2/2, `FrameRate60bTests` 2/2.
- **PlayMode golf/presentation subset** (GolfAnimationFlow, GolferClip, HeroGolfer, SwingSmoothness, GolfMotionReady, GolfPresentation, PresentationFlow, GolferSelect): 24/28.
  - `MakingAGolfer`, `SwingToResultShowsStats…` and `EveryLookBuilds` fail identically with the original golfer files (`logs/playmode_golf_base4.xml`).
  - `MainCamerasRecord…` fails because its `WaitForEndOfFrame` cannot run in batch mode.
- **Native Swift:** `xcodebuild -scheme GolfArcade -destination generic/platform=iOS CODE_SIGNING_ALLOWED=NO build` → **BUILD SUCCEEDED**, with no errors or warnings in the four edited Swift files (`logs/xcode_build.log`). A simulator run was not possible: this Mac's CoreSimulator is older than Xcode needs.

### Lobby exporter (proved on one sex, not installed)
`MatchHeroLockerExport.Run` and `.RunGolf` (`MH_LOCKER_SEX=Male`, `MH_LOCKER_OUT=work/frame-rate-60b/lobby_probe/...`, after-clone): reports in `lobby_probe/{tennis,golf}/report.txt`. The outputs (150 MB) were deleted after reading.
- **Tennis:** every exported clip comes out at 60.00 Hz, including `ready` (2.2 s, 133 frames, from the chat-4 ReadyIdle candidate in this clone), `serve`, the six rev-37 emotes and the seven standard emotes.
  - The new `forehand` = `Male_ForehandArmCorrected` (1.2 s, 60 Hz base + cut guards, 697 samples).
  - `MatchHero_Male_Rig.lzfse` grows 104.0 → 109.8 MB.
- **Golf:** golfDrive/Iron/Half/Chip/Putt, idle, wave, cheer and fistPump all at 60.00 Hz, from the new golfer FBX (Drive 3.467 s, 209 frames base, 350 with cut guards).
- The lobby re-export into `GolfArcade/Unity/CharacterAssets` and the native parity check are **chat 6's** (`work/hero-sync/sync_heroes.sh`). Until then the lobby plays the old exports.
  - The practice swing falls back to the 12-pose morph until the `forehand` clip is in the export.

## Rebuild
```
Blender -b --factory-startup --python scripts/golf60.py -- --sex Male|Female --in Unity/Assets/Resources/Hero/golfer_<m|f>.fbx --emotes work/frame-rate-60b/emotes60/fbx --out work/frame-rate-60b/golf/out --gs blender/scripts
Blender -b --factory-startup --python scripts/fbx_timemode60.py -- <in.fbx> <out.fbx> ...      # 60 Hz keys in a 30 fps header
Blender -b --factory-startup --python scripts/fbx_densify60.py -- <in.fbx> <out.fbx> ...       # 30 fps bake, source gone
python3 scripts/meta_double.py <in.meta> <out.meta> ...
zsh scripts/install.sh install|rollback
zsh scripts/run_capture.sh before|after [test filter]; python3 scripts/no_step.py proof/<dir>; python3 scripts/proof_sheets.py work/frame-rate-60b
```

Pitfalls:
- `golf60.py` copies the golf emotes from the **installed** match-hero clips. If chat 4 or anyone changes Emote_Spike/Scuba/Thrust/Intro_*/Walk/RunForward, re-run it.
- Do not re-run `fetch_matchheroes.sh` for golf, or `matchhero_golf.py` (it rebuilds at 30 fps from stale sources).
- A file going 30 → 60 fps needs its `.fbx.meta` clip ranges doubled.
