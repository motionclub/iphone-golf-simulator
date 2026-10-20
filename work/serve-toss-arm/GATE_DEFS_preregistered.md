# GATE DEFINITIONS — SERVE_TOSS_ARM (written 2026-10-03 before the new clips were played in the game)

Scope (from the request): the toss only. Re-key the LEFT arm and the RIGHT shoulder / upper arm / forearm / hand of the Serve, male first, female by the same keys (the rig solver puts them on each skeleton by bone name). Legs, hips, root, walk and the three runs stay. Nothing after the trophy is keyed (the chest "punch" is not touched). Export only `Male_Serve.fbx` and `Female_Serve.fbx`.

Reply contract: `GATE: SERVE_TOSS_ARM PASS` only if every line below passes; otherwise `FAIL` plus the failed lines. Thresholds are fixed here; a failing number is reported, not loosened.

Terms (all from the in-game trace `ServeTossFilm`, 60 Hz, hero-local metres, y up; the match hero serving by the game's own ritual, ball from `game.BallPosition`):
* **ball in the hand** = from the first frame of the film until the game leaves PlayerServeHold (the release).
* **T_H** = the first frame the ball is at or above the head bone's height, while the left hand still holds it or just after the release.
* **flexL** = 180 deg minus the angle shoulder-elbow-wrist of the left arm (0 = straight). **elev** = elevation of the racket axis, right wrist -> strings centre.
* **hoop** = strings centre.

Gates:
1. **LEFT_ARM_RISES_WITH_BALL.** At T_H: left wrist y >= head y - 0.15 m; flexL <= 70 deg; flexL(T_H) <= flexL(T_H - 0.10 s) - 15 deg (the arm is straightening); right wrist y >= right shoulder y - 0.30 m (the racket hand is not left at the belt). At T_H + 0.15 s: flexL <= 25 deg and left wrist y >= head y + 0.10 m. FAIL if the ball is at the head and the left wrist is still below head y - 0.15 m.
2. **RACKET_TURNS_WITH_THE_ARM.** At T_H: elev >= 45 deg. At the first frame with flexL <= 25 deg and left wrist above the head: elev >= 60 deg, hoop y >= head y + 0.15 m, horizontal distance hoop-head <= 0.70 m (hoop up beside the head). No dwell at the waist: no run of more than 8 consecutive frames (0.13 s) between the start of the wind-up and T_H with |elev| <= 15 deg while the right wrist is below the right shoulder by more than 0.20 m.
3. **BALL_STAYS_IN_THE_HAND.** On every frame from the start of the film to the release the distance ball centre - left wrist <= 0.22 m (the hand goes where the ball goes, nothing is left behind).
4. **LEGS_HIPS_ROOT_UNTOUCHED.** In Blender, Male and Female Serve, new vs job-start clip (`before/gen_serve_*.npz`): every bone that is not a shoulder / upper arm / lower arm / hand / finger bone has max rotation difference <= 0.05 deg on every frame; Hips location difference <= 1e-6 m; all bones are identical on frames 0-6 and 46-75 (the stance and everything from the racket drop on: the punch is not keyed).
5. **NO_POPS.** In Blender, Male and Female, frames 0-41: no racket-tip step > 300 mm between consecutive frames; no left / right upper arm, lower arm or hand bone step > 60 deg between consecutive frames (the job-start clip has a 1318 mm tip step and an 81 deg hand step at frame 16).
6. **NO_RACKET_IN_BODY.** In Blender, Male and Female, frames 7-71: no racket vertex lies more than 3 mm inside the deformed body + face mesh (frames 4-6 and 72-75 have a 7-14 mm thigh touch in the job-start clip and are unchanged).
7. **ONLY_TWO_FILES_CHANGED.** Against the hashes taken at the start of the job (`data/before_hashes.txt`): in `Unity/Assets/Characters/MatchHeroes/` only `Male/Male_Serve.fbx` and `Female/Female_Serve.fbx` differ, no `.meta` differs, the other 8 clip FBX are byte-identical; every `.cs` under `Unity/Assets/Scripts/` is byte-identical (no code change); the walk and the three run FBX in `work/serve-and-feet/export/fbx/` are byte-identical.
8. **PROOF_CLIPS.** A new in-game clip exists for both sexes (`film/serve_toss_male.mp4`, `film/serve_toss_female.mp4`, 30 fps, game camera with HUD, and a second angle), starting with the ball in the hand and the arms at the belt, running through the toss and the contact; the three-frame check of the request (the first frames show the ball at the head with the arms down, or the racket sideways) is read off the contact sheets `proof/*_sheet.jpg` and the numbers of gates 1-3 on the same frames.

## Amendment 1 (2026-10-03, written after running gates 1-3 on the JOB-START clip and before any result of the new clip existed)
Gate 3 as written ("from the start of the film") also covers the bounce ritual, where the ball leaves the palm on purpose (0.78 m on frame 198 of the job-start film, which is the bounce). The intent was the toss: **gate 3 is measured from the first wind-up frame (prepare > 0) to the release**. Nothing else changes. Gate 8's mp4 start is the last bounce / the first wind-up frame minus 0.5 s ("from the ball in the hand").
