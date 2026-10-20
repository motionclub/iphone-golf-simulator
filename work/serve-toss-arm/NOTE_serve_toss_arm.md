# NOTE — SERVE_TOSS_ARM (2026-10-03)

Result: `GATE_RESULTS.md`. Request: the first seven frames after the ball leaves the belt (ball at the head, arms at the waist, racket sideways).

## Layout
* `GATE_DEFS_preregistered.md`, `GATE_RESULTS.md`, `checks.json`.
* `scripts/` — `serve_new.py` (the Serve keys, the same engine as work/serve-and-feet: work/match-anim-set kin / pose / clipkit / clips), `run_serve.py` (solve + the splice onto the job-start clip), `rebuild.sh <male|female>`, `build_and_check.sh` (both heroes, bake, measure, racket-in-body, gates 4-6, offline toss model), `check_blender_gates.py`, `check_game_gates.py <film dir>`, `check_files.py`, `sim_toss.py` (offline model of the game's toss arm), `measure.py`, `penetrate.py`, `achieved.py` (achieved vs commanded racket axes), `diff_bones.py`, `make_proof.py`, `enc.swift`, `unity_run.sh`, `read_trace.py`.
* `before/` — the job-start Serve (FBX + `gen_serve_*.npz`), `before_hashes.txt` in `data/`; `export/fbx/` — the two new FBX; `export/*.blend` — the baked working blends; `export/pristine/` — the job-start blends.
* `film_before2_<sex>/`, `film_after_<sex>/` — in-game stills (game camera, back, side) + `trace.csv` (60 Hz: clip time, ball, left/right hand, shoulder, elbow, head, strings), `gates.json`.
* Unity: `Unity/Assets/Editor/ServeTossFilm.cs` (new, Editor only: plays the first serve of a campaign match by the game's own ritual and writes the stills + trace). Run in an APFS clone of the project: `cp -c -R Unity <scratch>/UnityClone`, `scripts/unity_run.sh GolfArcade.EditorTools.ServeTossFilm.Run <log> ST_OUT=<dir> ST_FEMALE=0|1` (no `-quit`, needs graphics; waits while an xcodebuild runs).

## Rebuild
```bash
cd work/serve-toss-arm
zsh scripts/build_and_check.sh            # both heroes: solve, bake, gates 4-6 (needs before/gen_serve_*.npz)
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup export/HeroBase_Male_MatchAnims.blend --python scripts/export_fbx.py -- male Serve   # same for female
```
The FBX export is not byte-deterministic (two exports of the same motion differ in hash): the shipped files are the two that were played in the game (sha256 eb4a7ff6… male, c75f601e… female). The installed Serve is also copied into `work/serve-and-feet/export/fbx/` and its `data/clip_table_new.json` / `fbx_<hero>.json` (the job-start versions are in `work/serve-and-feet/data/before_serve_toss_arm/`); `work/serve-and-feet/scripts/finish_build.sh` would rebuild the OLD Serve from its own `serve_new.py`: Serve is built here now.

## Traps found
* **The hand is never behind the ball in the game.** `TossArm` pulls the left palm onto the ball every frame (the elbow is the two-bone solution), and the ball goes from the stance palm to the release palm on a straight line (smoothstep over the wind-up, 0.5 game s = 0.67 s at the serve pace). The arm shape in the game is therefore the geometry of that line, not the clip's own arm path: a hold point 0.53 m from the shoulder and a release point 0.63 m away, joined by a chord that passes 0.32 m from the shoulder = elbow folded to 105-120 deg in the middle. The clip's stance (frames 0-6) fixes the hold point, so only the release point can be moved.
* The arm solver raises the shoulder girdle with the arm: a wrist target at 1.0 arm length gives a 65 deg elbow, a straight arm needs a target at 1.2+ (the solver clamps to the straight arm).
* An elbow pole pointing down while the arm points up (pole parallel to the arm axis) flips the upper arm 136 deg in one frame; hold the pole out to the side.
* The right-arm tracker (Viterbi over elbow swivel x 3 wrist angles) has two wrist twist basins about 140 deg apart; the job-start clip and the new keys end in the same one (twist -60 to -90). A path that starts in the other (the stance) basin must cross over somewhere: let the commanded face turn gradually, and cross when the racket is near vertical. A stiffer tracker (higher `TRK_LAM`) picks the wrong basin for the whole hold.
* A change before 1.0 s moves the elbow branch of the follow-through (frames 53-65: elbow 38 cm, racket tip 55 cm different): the tail is taken from the job-start clip instead.
* The job-start clip itself has a one-frame wrist flip at frame 53 (160 deg bone step, in the follow-through) and a 42 deg left-upper-arm drop at frame 44 (the new clip drops the arm from straight-up, 73 deg in that frame); both are after the trophy and left as they were.
* Image n of `ServeTossFilm` is the n-th EVEN row of the trace while the hero is serving (`serving` = flow Hold / Toss or state Serve), not row/2.
