# GATE_RESULTS - EMOTES (2026-10-04)

## GATE: EMOTES FAIL

Definitions: `GATE_DEFS_preregistered.md` (written before the first run; one correction before it, listed in that file). Measured: the 12 exported FBX re-imported in Blender (`data/trace_*.npz`, `data/checks_anim.json`), the project files / Unity import log / in-game film traces (`data/checks_repo.json`), `data/protected_verify.json`. Every line is both heroes.

| line | clip | result | note |
|---|---|---|---|
| L1 | Emote_Scuba | PASS |  |
| P1 | Emote_Scuba | PASS |  |
| B1 | Emote_Scuba | PASS |  |
| R1 | Emote_Scuba | **FAIL** | fails on male+female: {"male": {"racket_hand_pos_m": 2.5288109106536417e-07, "racket_hand_deg": 0.05574618959151229, "hand_racket_const_dev": 4.408983519388343e-07}, "female": {"racket_hand_pos_m": 2.862419592186592e-07, "racket_hand_deg": 0.12326892806913155, "hand_racket_const_dev": 3.30337228793276e-07}} |
| F1 | Emote_Scuba | PASS |  |
| S1 | Emote_Scuba | PASS |  |
| S2 | Emote_Scuba | PASS |  |
| S3 | Emote_Scuba | PASS |  |
| S4 | Emote_Scuba | PASS |  |
| same timing (L1) | Emote_Scuba | PASS |  |
| L1 | Emote_Thrust | PASS |  |
| P1 | Emote_Thrust | PASS |  |
| B1 | Emote_Thrust | PASS |  |
| R1 | Emote_Thrust | **FAIL** | fails on male+female: {"male": {"racket_hand_pos_m": 1.914088812271525e-07, "racket_hand_deg": 0.0707274128834992, "hand_racket_const_dev": 2.632975161231954e-07}, "female": {"racket_hand_pos_m": 1.519626234052415e-07, "racket_hand_deg": 0.13031132759926256, "hand_racket_const_dev": 3.037559817009594e-07}} |
| F1 | Emote_Thrust | PASS |  |
| T1 | Emote_Thrust | PASS |  |
| T2 | Emote_Thrust | PASS |  |
| T3 | Emote_Thrust | PASS |  |
| T4 | Emote_Thrust | **FAIL** | fails on male+female: {"male": {"min_wrist_to_hips_m": 0.19208804108076372}, "female": {"min_wrist_to_hips_m": 0.1933906754692223}} |
| same timing (L1) | Emote_Thrust | PASS |  |
| L1 | Emote_Spike | PASS |  |
| P1 | Emote_Spike | PASS |  |
| B1 | Emote_Spike | PASS |  |
| R1 | Emote_Spike | PASS |  |
| F1 | Emote_Spike | PASS |  |
| K1 | Emote_Spike | PASS |  |
| K2 | Emote_Spike | PASS |  |
| K3 | Emote_Spike | PASS |  |
| K4 | Emote_Spike | PASS |  |
| K5 | Emote_Spike | PASS |  |
| same timing (L1) | Emote_Spike | PASS |  |
| L1 | Intro_Wave | PASS |  |
| P1 | Intro_Wave | PASS |  |
| B1 | Intro_Wave | PASS |  |
| R1 | Intro_Wave | **FAIL** | fails on female: {"female": {"racket_hand_pos_m": 9.996002811937585e-08, "racket_hand_deg": 0.12446966554845935, "hand_racket_const_dev": 2.7004980351907903e-07}} |
| F1 | Intro_Wave | PASS |  |
| W1 | Intro_Wave | PASS |  |
| W2 | Intro_Wave | PASS |  |
| same timing (L1) | Intro_Wave | PASS |  |
| L1 | Intro_BringIt | PASS |  |
| P1 | Intro_BringIt | PASS |  |
| B1 | Intro_BringIt | PASS |  |
| R1 | Intro_BringIt | **FAIL** | fails on male+female: {"male": {"racket_hand_pos_m": 2.4755668231600746e-07, "racket_hand_deg": 0.07708890130245259, "hand_racket_const_dev": 3.090560276586274e-07}, "female": {"racket_hand_pos_m": 1.6340398937062404e-07, "racket_hand_deg": 0.12483092982153692, "hand_racket_const_dev": 3.7335059688281547e-07}} |
| F1 | Intro_BringIt | PASS |  |
| C1 | Intro_BringIt | PASS |  |
| C2 | Intro_BringIt | PASS |  |
| C3 | Intro_BringIt | PASS |  |
| same timing (L1) | Intro_BringIt | PASS |  |
| L1 | Intro_Pushups | PASS |  |
| P1 | Intro_Pushups | PASS |  |
| B1 | Intro_Pushups | PASS |  |
| R1 | Intro_Pushups | PASS |  |
| F1 | Intro_Pushups | PASS |  |
| U1 | Intro_Pushups | PASS |  |
| U2 | Intro_Pushups | PASS |  |
| U3 | Intro_Pushups | PASS |  |
| U4 | Intro_Pushups | PASS |  |
| same timing (L1) | Intro_Pushups | PASS |  |
| N1 | all | PASS |  |
| N2 | all | PASS |  |
| G1 | all | PASS |  |
| G2 | all | PASS |  |
| G3 | all | PASS |  |
| X1 | all | PASS |  |
| X2 | all | **FAIL** | {"differences_by_other_sessions": ["Unity/Assets/Editor/GolfLookSmoke.cs", "Unity/Assets/Scripts/Course/GolfLook.cs"], "on_my_write_list": [], "inside_my_run_windows": ["Unity/Assets/Editor/GolfLookSmoke.cs"]} |

**59 / 65 lines PASS.**

## The failed lines, as measured

* **R1 Emote_Scuba** - fails on male+female: {"male": {"racket_hand_pos_m": 2.5288109106536417e-07, "racket_hand_deg": 0.05574618959151229, "hand_racket_const_dev": 4.408983519388343e-07}, "female": {"racket_hand_pos_m": 2.862419592186592e-07, "racket_hand_deg": 0.12326892806913155, "hand_racket_const_dev": 3.30337228793276e-07}}
* **R1 Emote_Thrust** - fails on male+female: {"male": {"racket_hand_pos_m": 1.914088812271525e-07, "racket_hand_deg": 0.0707274128834992, "hand_racket_const_dev": 2.632975161231954e-07}, "female": {"racket_hand_pos_m": 1.519626234052415e-07, "racket_hand_deg": 0.13031132759926256, "hand_racket_const_dev": 3.037559817009594e-07}}
* **T4 Emote_Thrust** - fails on male+female: {"male": {"min_wrist_to_hips_m": 0.19208804108076372}, "female": {"min_wrist_to_hips_m": 0.1933906754692223}}
* **R1 Intro_Wave** - fails on female: {"female": {"racket_hand_pos_m": 9.996002811937585e-08, "racket_hand_deg": 0.12446966554845935, "hand_racket_const_dev": 2.7004980351907903e-07}}
* **R1 Intro_BringIt** - fails on male+female: {"male": {"racket_hand_pos_m": 2.4755668231600746e-07, "racket_hand_deg": 0.07708890130245259, "hand_racket_const_dev": 3.090560276586274e-07}, "female": {"racket_hand_pos_m": 1.6340398937062404e-07, "racket_hand_deg": 0.12483092982153692, "hand_racket_const_dev": 3.7335059688281547e-07}}
* **X2 all** - {"differences_by_other_sessions": ["Unity/Assets/Editor/GolfLookSmoke.cs", "Unity/Assets/Scripts/Course/GolfLook.cs"], "on_my_write_list": [], "inside_my_run_windows": ["Unity/Assets/Editor/GolfLookSmoke.cs"]}

## What the failed lines are (evidence, not a re-grade - the lines above keep their FAIL)

* **R1 (Scuba, Thrust, Wave, BringIt): racket vs Hand_Racket <= 0.01 deg in the re-imported FBX.** The positions agree to 2.5e-7 m; the rotation differs by 0.05 - 0.13 deg. That is the noise floor of this FBX pipeline: Blender bakes the bone-parented racket nodes (Hand_Racket, Racket_Classic, Grip, ButtCap, StringBed carry baked curves in every clip FBX, also in clips this job did not write). The same measure on shipped clips: Male_Forehand 0.079 deg, Male_ReadyIdle 0.074 deg, Female_Forehand 0.137 deg, Female_ReadyIdle 0.134 deg (`data/r1_noise_floor.json`), so no clip can meet 0.01 deg through this exporter (`export_emotes.py` clears the racket animation data in the four clips, which changed nothing). In the game the racket is exactly on the hand: in-game grip-to-hand distance 0.0000 m for all eight emote clips x heroes (G2 PASS). I did not change the line.
* **T4 (Thrust): each wrist >= 0.22 m from the Hips head in EVERY frame.** The READY pose the clip starts and ends on has its racket wrist 0.187 m (male) / 0.189 m (female) from the Hips head (the ReadyIdle clip itself), so frame 0 can never pass. Inside the thrust window (frames 11-47) the minimum is 0.418 m (male) / 0.406 m (female): no hand comes near the pelvis. I did not change the line.
* **X2 (untouched): a protected file was written inside one of my run windows.** Another session is working on the golf look: `Unity/Assets/Scripts/Course/GolfLook.cs` and `Unity/Assets/Editor/GolfLookSmoke.cs` changed during this job (GolfLook.cs 15:31:47, then again later; GolfLookSmoke.cs 15:28 and later). At the last verify the file inside a run window of mine is `GolfLookSmoke.cs` (the verifier reports whichever protected file has an mtime in a window). Every Unity run of this job ran in an APFS CLONE of the project (`scratchpad/UnityClone`), never in the shared project; the clone's copy of GolfLook.cs is byte-identical to the job-start baseline (sha256 cf456807...) while the real file differs and changed again while this job ran, so the changes were not made by this job. No protected file is on this job's write list. The line is FAIL by its own wording and stays FAIL.

## Numbers worth reading

* male: Scuba pinch 1.50 s, knee maxima 2; Thrust hips p-p 0.189 m (run: 0.052 m), pitch swing 30 deg; Spike peak wrist 14.3 m/s (down 10.8), fold 48 deg, racket off the hand 0.60 s, hands on hips 0.57 s, head shake 38 deg; Wave crossings 6, p-p 61 deg; BringIt tuck peaks 3, racket head max 1.53 m/s; Pushups floor 1.60 s, racket off the hand 1.97 s.
* female: Scuba pinch 1.50 s, knee maxima 2; Thrust hips p-p 0.189 m (run: 0.052 m), pitch swing 30 deg; Spike peak wrist 13.7 m/s (down 10.0), fold 48 deg, racket off the hand 0.60 s, hands on hips 0.63 s, head shake 38 deg; Wave crossings 4, p-p 45 deg; BringIt tuck peaks 3, racket head max 1.73 m/s; Pushups floor 1.60 s, racket off the hand 1.97 s.

Reply contract: `GATE: EMOTES FAIL` - failed lines: R1 Emote_Scuba, R1 Emote_Thrust, T4 Emote_Thrust, R1 Intro_Wave, R1 Intro_BringIt, X2 all
