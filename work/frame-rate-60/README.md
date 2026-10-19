# FRAME_RATE_60 (2026-10-16)

Problem: on AirPlay the game felt like 30 fps. Two causes, both fixed here (nothing committed).

## 1. The game dropped itself to 30 fps
`Unity/Assets/Scripts/Environment/LuminousCoastFrameBudget.cs` switched `Application.targetFrameRate` to 30 after 6 s of late frames and never came back
(Resort tennis, golf hole 12, dream environments; on by default). Now it keeps 60 and calls `TennisQuality.StepDown()` instead (a 120 Hz loop still falls to 60).
`LuminousCoastFrameBudgetTests` updated. iOS thermal cap in `ProjectSettings.asset`: Serious 30 -> 60, Critical 15 -> 30 (needs a new iOS build to take effect).

## 2. The character clips were baked at 30 fps
Unity joined 30 Hz keys with straight lines. Measured with `Unity/Assets/Editor/ClipRateProbe.cs` (`Survey`: key spacing of every hero clip).

Re-baked on a 1/60 s grid and INSTALLED (each checked against the approved 30 Hz clip at the shared frames):

| clips | where | shared-frame difference vs 30 Hz |
|---|---|---|
| Serve (both heroes) | `serve/` (fork of serve-dip-jump, sampling 60 Hz, authoring still 30 Hz frames) | hips 0 mm, bones p99 4 deg |
| Walk, RunForward/Left/Right | `feet/` (fork of serve-and-feet; cycles doubled to 66 / 34 frames) | 0.00 deg |
| 7 standard emotes, tennis + Free, Free Walk/Run | `emotes/` (fork of emote-standard; Tracks sampled twice per authoring frame) | max 0.1 deg (JumpJoy 1.1, Run 0.8) |

Install / undo: `zsh work/frame-rate-60/install_fbx.sh install|rollback`, then
`Unity -batchmode -nographics -quit -projectPath Unity -executeMethod GolfArcade.EditorTools.FrameRate60Wire.Reimport`.
The HeroMoves `.fbx.meta` clip ranges (`lastFrame`) are doubled by that script (a 30 Hz range would cut the clip in half).
Rollback sources are the original job folders (byte-identical to what was installed before).
Do NOT re-run `EmoteStandardWire`, `ServeAndFeetWire.CopyAndImport` or `MatchHeroImport.CopyAndImport` without the 60 Hz sources: they copy the 30 Hz files back.

## Match strokes (14 per hero): INSTALLED at 60 Hz (Adnan: "all 60 fps only")
Free re-solve at 60 Hz (`MA_FPS=60 MA_GRID=60` in work/match-anim-set/scripts; `MA_WORK=<copy>` for a scratch build), staged in `match-anim-set/` (fbx, data, clip_table_60.json), installed by `FrameRate60Wire.Run`
(also moves prefab contact/leftRelease: Forehand .650, ForehandWide .850, Return .417, VolleyBackhand .283, left releases) and `TennisArmStrokeBuild.Run` (played Forehand/Backhand ArmCorrected clips, originals in `backup_armcorrected/`).
Gates: the same as the 30 Hz build except RACKET_HELD VolleyBackhand (left hand 0.9 attached at one peak frame); FBX round trip 16/16 both heroes.
It is a different motion, not a smoother copy: the racket arm picks other branches than the approved 30 Hz solve (Forehand finish: racket up instead of wrapped; see `compare/`). 1-8 % of bone samples differ by >10 deg at shared frames,
racket speed spikes to 45-61 m/s. Rollback to the approved strokes: `FR60_REPO=<repo> FR60_SOURCE=work/match-anim-set/export/fbx/ FR60_TABLE=work/frame-rate-60/clip_table_30_original.json Unity ...FrameRate60Wire.Run`,
copy `backup_armcorrected/*` to `Resources/Tennis/Performance/`.
Still 30 Hz: ReadyIdle (the base model FBX, tiny sway), lobby SceneKit mirror (needs `work/hero-sync/sync_heroes.sh`), golf clips. emote-fluid clips (Spike/Scuba/Thrust/Intros) were already partly 60 Hz.

## Tests
EditMode 598/598. PlayMode (MatchHeroClipMap, SwingSmoothness, PlayerBase, ReceivingRegression, TennisMotionReference, GolferClip): all pass except
`MatchHeroClipMapTests` at "Male: Slice ... Expected Forehand, was ForehandShort" (stroke-to-clip mapping, fails identically on the 30 Hz strokes). `TennisGameplayTests` has 4 failures (visible arms, late swing returned, wide-ball chase, backhand string) that also fail identically on the 30 Hz strokes. Pinned contact times in MatchHeroClipMapTests updated to the 60 Hz table.
`AnimationContactPresentationTests` failed once on a shader-cache write (disk was full).

## Stroke comparison (2026-10-16)
`compare/*.jpg`: male Forehand / Backhand / Return, side and behind cameras, approved 30 fps clip (top, played with linear interpolation as the game does) vs the free 60 Hz re-solve (bottom),
same times, every 3/60 s. Forehand: the 60 Hz swing has a different racket path and finish (racket straight up instead of wrapped behind the head). Backhand: nearly identical.
Return: same shape, contact one frame earlier (0.417 vs 0.433 s). Rendered with `proofs_cmp.py` (a copy of match-anim-set/scripts/proofs.py plus a `compare` mode), not kept in the repo.
