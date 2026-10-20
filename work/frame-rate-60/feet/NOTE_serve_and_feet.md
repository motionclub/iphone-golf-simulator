# NOTE — SERVE_AND_FEET (2026-10-03)

What is here, how to rebuild it, and the traps. Result: `GATE_RESULTS.md` (FAIL: NO_SLIDE_SUBSTITUTE share 41.6 % > 20 %; FROM_WATCH media rule and BALL_UNCHANGED hash list fail only because of other sessions' files).

## Layout
* `WATCH.md` — the two videos, in order; `GATE_DEFS_preregistered.md` — written before the clips; `checks.json` / `GATE_RESULTS.md` — results.
* `export/HeroBase_{Male,Female}_MatchAnims.blend` — copies of the match-anim-set blends + 5 new actions (old Serve kept as `Serve_old`, never exported); `export/fbx/` — 10 FBX (Serve, Walk, RunForward, RunLeft, RunRight).
* `scripts/` — the engine of work/match-anim-set is imported read-only (`kin`, `pose.Solver`, `clipkit`, `clips`); `loco.py` (hero, foot skinning, calibration), `gait.py` (walk, runs), `serve_new.py` (every key carries a `S3.*` token that names a WATCH step), `run_*.py`, `bake_loco.py`, `verify_blend.py`, `verify_clear.py`, `export_fbx.py`, `make_table.py`, `run_blend_model.py` (planted foot of a blend of run clips), `analyze_proof.py`, `check_gates.py`, `make_proof_sheets.py`.
* Unity: `Unity/Assets/Editor/ServeAndFeetWire.cs` (copies the FBX, hash-checked against `data/clip_table_new.json`; sets Serve / Walk / RunForward / RunLeft / RunRight slots, serve times, speeds, reverse pivot on both prefabs and nothing else), `ServeAndFeetProof.cs` (Play-mode proof), 11 hunks in `HeroTennisDriver.cs` (`data/HeroTennisDriver.diff`; reverting them gives the job-start SHA ca9c675a exactly), one line each in `MatchHeroImport.cs` and `MatchHeroBuild.cs`.

## Rebuild
```bash
cd work/serve-and-feet
zsh scripts/finish_build.sh                       # pristine blend copy -> 5 clips x 2 heroes -> bake -> verify_blend -> FBX -> data/clip_table_new.json
/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13 scripts/make_table.py   # also writes runReversePivot (needs data/verify_blend_*.json)
# Unity (no other Unity / xcodebuild running on the project):
env SF_REPO=$PWD/../.. Unity -batchmode -nographics -quit -projectPath ../../Unity -executeMethod GolfArcade.EditorTools.ServeAndFeetWire.Run
env SF_REPO=$PWD/../.. SF_PROOF_OUT=$PWD/proof Unity -batchmode -projectPath ../../Unity -executeMethod GolfArcade.EditorTools.ServeAndFeetProof.Run   # ~5 min, needs graphics, no -quit
python3.13 scripts/analyze_proof.py && python3 scripts/make_proof_sheets.py && python3.13 scripts/check_gates.py
```
`SF_DIAG=walk|run` (with `SF_PROOF_OUT` elsewhere) runs the per-frame foot diagnostics (toe / ankle positions, lock state, pace ratio, smoothing offset). A rebuild of the prefabs with `Golf Arcade/Match Heroes/Build Prefabs` now keeps these clips.

## Traps found
* **Game pace.** `TennisGame.GameSpeed` 1.2 (rally) and `TennisRules.ServePace` 0.75 (serve hold / toss, rival serve) scale the simulation; `actor.Speed` is per game second. Anything that matches a clip to the ground has to use the real displacement.
* **120 Hz steps.** The actor moves in 1/120 s steps; at 0.75 pace a 60 fps frame has 2, 1, 2, 1 steps. Measuring a world toe speed per frame on that is noise of ±0.3 m/s at a walk.
* **Blends.** Forward-time F + R/L blends are slide-free (speed 0.985 V, angle = 90° × weight); a reversed forward run blended with a forward-time lateral clip cancels the leg swing. Use the reversed opposite lateral clip. The L1 weights fwd/(side+fwd) are close to angle/90 but not equal.
* **Frame 0 of the Serve** must already hold the ball (the implicit start key was the ReadyIdle left hand, 10 cm higher: it read as a dip).
* **Strings-to-ball gap** on the frame the log fires on includes the launched ball (0.35 m). Read it at the instant the time-to-contact reaches 0 (`ContactGap` in the proof).
* **Toe-bone "slide"** (the driver's `FootSkate`, toe within 15 mm of the floor) counts the heel strike / toe-off roll; walking cannot get under ~15 % on it, and the 15 stroke clips are a third of the moving frames at 61 %.
* The proof needs `Time.captureFramerate = 60`; start Unity batch without `-quit` for Play-mode scripts (`-quit` ends the batch before the script runs). Never overlap Unity with xcodebuild (Burst crash); `scripts/unity_run.sh` waits.
* Real project vs clone: the proof was first run in an APFS clone (`cp -c`) of the project, then the wire tool and a full proof were run on the real project when nothing else held it; backups of the MatchHeroes folder and both prefabs were taken before.

## Open
* NO_SLIDE_SUBSTITUTE needs the stroke clips' footwork (not in scope: other 15 clips untouched) or a different metric (heel and toe both low) to pass.
* Diagonal runs away from the net change family at 100° / 80° (R ↔ reversed L): a short cross-fade with leg mush at that angle.
* Run speeds above ~6.5 m/s hit the 2.0× rate cap and slide.
