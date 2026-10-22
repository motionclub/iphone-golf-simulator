# GATE_RESULTS - emote overhaul (Spike / Scuba / Thrust)

**82 / 82 gate lines PASS** (6 FBX = 3 clips x 2 heroes). Definitions: `GATE_DEFS_preregistered.md` (written before the first run; three disclosed amendments at its end). Measured on the RE-IMPORTED FBX (`scripts/trace_fbx2.py`, `scripts/check_gates2.py`), the independent penetration run (`scripts/collide3.py`, Blender-evaluated skin) and the Unity clone (`proof/hold/*.json`, `film/*/triggers.json`).

Re-run everything: `scripts/run_all2.sh` (build -> FBX -> trace -> penetration -> gates, about 9 minutes), then `scripts/write_results.py`.

## Emote_Spike

| id | male | female | measured (male) | measured (female) |
|---|---|---|---|---|
| G1 | PASS | PASS | frames=97; expected=97; bones=53; objects=["Body_M", "ButtCap", "Face_M", "Grip"] | frames=97; expected=97; bones=53; objects=["Body_F", "ButtCap", "Face_F", "Grip"] |
| G2 | PASS | PASS | arm_dev=0.0; root_dev=0.0 | arm_dev=0.0; root_dev=0.0 |
| G3 | PASS | PASS | start_mean_deg=0.1192; start_max_deg=1.069; end_mean_deg=0.1192; end_max_deg=1.069 | start_mean_deg=0.0844; start_max_deg=0.5558; end_mean_deg=0.083; end_max_deg=0.5558 |
| G4 | PASS | PASS | slide_max_m=0.0; end_toe_max_m=0.0; mesh_min_z_m=0.0023 | slide_max_m=0.0; end_toe_max_m=0.0; mesh_min_z_m=0.0011 |
| G5 | PASS | PASS | worst_mm=0.0019 | worst_mm=0.0026 |
| G6 | PASS | PASS | racket_hand_pos_m=0.0; racket_hand_deg=0.0837; readyidle_floor_deg=0.0718; no_racket_animation=true | racket_hand_pos_m=0.0; racket_hand_deg=0.1288; readyidle_floor_deg=0.1352; no_racket_animation=true |
| G7 | PASS | PASS | frames_checked=97; frames_over_limit=0; worst_mm=18.0; worst_frame=0; over_limit_frames_mm=[] | frames_checked=97; frames_over_limit=0; worst_mm=9.8; worst_frame=20; over_limit_frames_mm=[] |
| G8 | PASS | PASS | max_correction_step_m=0.0147; max_swing_step_deg=0.4996; max_speed_added_m_s=0.3926; corrected_frames=93 | max_correction_step_m=0.008; max_swing_step_deg=0.4294; max_speed_added_m_s=0.1993; corrected_frames=95 |
| S1 | PASS | PASS | min_below_shoulder_m=0.4412; min_dist_to_racket_m=0.4666; max_rel_speed_m_s=1.054 | min_below_shoulder_m=0.3956; min_dist_to_racket_m=0.3202; max_rel_speed_m_s=1.0773 |
| S2 | PASS | PASS | downswing_s=0.2667; peak_tip_speed_m_s=28.7788 | downswing_s=0.2667; peak_tip_speed_m_s=28.1941 |
| S3 | PASS | PASS | contacts=3; contact_times=[1.2, 1.433, 1.967]; lowest_m=-0.0 | contacts=2; contact_times=[1.2, 1.967]; lowest_m=0.0 |
| S4 | PASS | PASS | trunk_flexion_at_contacts_deg=[62.6763, 60.4655] | trunk_flexion_at_contacts_deg=[63.4812, 59.2442] |
| S5 | PASS | PASS | first_lift_top_m=2.241; second_lift_top_m=1.4951; ratio=0.6672 | first_lift_top_m=2.1901; second_lift_top_m=1.5152; ratio=0.6918 |
| S6 | PASS | PASS | racket_tip_0p20_above_head_top_s=0.2667; max_tip_above_head_top_m=0.597 | racket_tip_0p20_above_head_top_s=0.2667; max_tip_above_head_top_m=0.5584 |

## Emote_Thrust

| id | male | female | measured (male) | measured (female) |
|---|---|---|---|---|
| G1 | PASS | PASS | frames=106; expected=106; bones=53; objects=["Body_M", "ButtCap", "Face_M", "Grip"] | frames=106; expected=106; bones=53; objects=["Body_F", "ButtCap", "Face_F", "Grip"] |
| G2 | PASS | PASS | arm_dev=0.0; root_dev=0.0 | arm_dev=0.0; root_dev=0.0 |
| G3 | PASS | PASS | start_mean_deg=0.1192; start_max_deg=1.069; end_mean_deg=0.1192; end_max_deg=1.069 | start_mean_deg=0.0844; start_max_deg=0.5558; end_mean_deg=0.0844; end_max_deg=0.5558 |
| G4 | PASS | PASS | slide_max_m=0.0; end_toe_max_m=0.0; mesh_min_z_m=0.0017 | slide_max_m=0.0; end_toe_max_m=0.0; mesh_min_z_m=0.0011 |
| G5 | PASS | PASS | worst_mm=0.0017 | worst_mm=0.0018 |
| G6 | PASS | PASS | racket_hand_pos_m=0.0; racket_hand_deg=0.0652; readyidle_floor_deg=0.0718; no_racket_animation=true | racket_hand_pos_m=0.0; racket_hand_deg=0.1301; readyidle_floor_deg=0.1352; no_racket_animation=true |
| G7 | PASS | PASS | frames_checked=106; frames_over_limit=0; worst_mm=18.0; worst_frame=0; over_limit_frames_mm=[] | frames_checked=106; frames_over_limit=0; worst_mm=2.8; worst_frame=0; over_limit_frames_mm=[] |
| G8 | PASS | PASS | max_correction_step_m=0.0078; max_swing_step_deg=0.3736; max_speed_added_m_s=0.1545; corrected_frames=39 | max_correction_step_m=0.0154; max_swing_step_deg=3.0311; max_speed_added_m_s=0.2021; corrected_frames=90 |
| T1 | PASS | PASS | pelvis_travel_m=[0.3587, 0.399, 0.42]; back_behind_ready_m=[0.1275, 0.13, 0.13] | pelvis_travel_m=[0.3587, 0.399, 0.42]; back_behind_ready_m=[0.1275, 0.13, 0.13] |
| T2 | PASS | PASS | frames_apart=[0, 0, 0] | frames_apart=[0, 0, 0] |
| T3 | PASS | PASS | crossed_lateral_m=[0.0864, 0.0864, 0.0864]; wrist_pelvis_dist_and_height_at_hits=[[0.3265704674452062, 0.40492757833148463, 0.3213408589363098], [0.32657038549239525, 0.4049264053559598, 0.3295658230781555], [0.3265705424900785, 0 | crossed_lateral_m=[0.0966, 0.1138, 0.0973]; wrist_pelvis_dist_and_height_at_hits=[[0.25197316953932586, 0.4151512853112153, 0.2869267463684082], [0.2849182368740194, 0.41515098439773973, 0.29709362983703613], [0.2519714561403224,  |
| T4 | PASS | PASS | max_chest_yaw_deg=0.215; max_head_yaw_deg=1.6019 | max_chest_yaw_deg=0.215; max_head_yaw_deg=1.6019 |
| T5 | PASS | PASS | min_knee_flexion_deg=29.043; min_toe_yaw_deg=44.385 | min_knee_flexion_deg=27.3912; min_toe_yaw_deg=46.7152 |
| T6 | PASS | PASS | head_pitch_p2p_deg=32.8508 | head_pitch_p2p_deg=32.8509 |

## Emote_Scuba

| id | male | female | measured (male) | measured (female) |
|---|---|---|---|---|
| G1 | PASS | PASS | frames=142; expected=142; bones=53; objects=["Body_M", "ButtCap", "Face_M", "Grip"] | frames=142; expected=142; bones=53; objects=["Body_F", "ButtCap", "Face_F", "Grip"] |
| G2 | PASS | PASS | arm_dev=0.0; root_dev=0.0 | arm_dev=0.0; root_dev=0.0 |
| G3 | PASS | PASS | start_mean_deg=0.1192; start_max_deg=1.069; end_mean_deg=0.2947; end_max_deg=2.0902 | start_mean_deg=0.0834; start_max_deg=0.5558; end_mean_deg=0.3482; end_max_deg=3.173 |
| G4 | PASS | PASS | slide_max_m=0.0; end_toe_max_m=0.0; mesh_min_z_m=0.0017 | slide_max_m=0.0; end_toe_max_m=0.0; mesh_min_z_m=0.0011 |
| G5 | PASS | PASS | worst_mm=0.0008 | worst_mm=0.0021 |
| G7 | PASS | PASS | frames_checked=142; frames_over_limit=0; worst_mm=18.0; worst_frame=0; over_limit_frames_mm=[] | frames_checked=142; frames_over_limit=0; worst_mm=5.9; worst_frame=127; over_limit_frames_mm=[] |
| G8 | PASS | PASS | max_correction_step_m=0.0319; max_swing_step_deg=9.76; max_speed_added_m_s=0.3706; corrected_frames=76 | max_correction_step_m=0.0097; max_swing_step_deg=0.1537; max_speed_added_m_s=0.1785; corrected_frames=53 |
| C1 | PASS | PASS | max_pad_to_nose_m=0.0045; mean_m=0.0045 | max_pad_to_nose_m=0.0045; mean_m=0.0045 |
| C2 | PASS | PASS | min_ahead_of_neck_m=0.3594; below_shoulder_range_m=[0.1438, 0.1966] | min_ahead_of_neck_m=0.3282; below_shoulder_range_m=[0.1228, 0.1729] |
| C3 | PASS | PASS | wrist_lateral_p2p_m=0.2702; period_s=0.7333; cycles=3.5 | wrist_lateral_p2p_m=0.2487; period_s=0.7333; cycles=3.5 |
| C4 | PASS | PASS | knee_lateral_p2p_m=0.1385; period_s=0.7333; feet_slide_m=0.0 | knee_lateral_p2p_m=0.1387; period_s=0.7333; feet_slide_m=0.0 |
| C5 | PASS | PASS | leaves_s=0.2; lowest_m_range=[-0.0, 0.0]; moved_m=0.0; min_dist_to_hand_m=0.0954 | leaves_s=0.2; lowest_m_range=[-0.0, 0.0]; moved_m=0.0; min_dist_to_hand_m=0.0995 |
| C6 | PASS | PASS | attach_frame=123; hand_to_racket_before_attach_m=0.0056; max_racket_jump_before_attach_m=0.0181; after_attach_deg=0.0767; readyidle_floor_deg=0.0718 | attach_frame=123; hand_to_racket_before_attach_m=0.0056; max_racket_jump_before_attach_m=0.0181; after_attach_deg=0.1309; readyidle_floor_deg=0.1352 |

## Unity (clone, then installed byte-identical)

* `EmoteWire` in the clone: the 6 new FBX import with lengths Spike 3.200, Thrust 3.500, Scuba 4.700 s on both prefabs (`work/emotes/logs/wire_report.txt`); prefabs unchanged byte for byte.
* `EmoteFilm` (real Tennis scene, game camera + front + side): all 3 emotes start, play and finish for both heroes; triggers: plain point 0 emotes, won game 1 emote, no emote on the next point, PlayTaunt works, intro hook works (`film/<hero>/triggers.json`, `film/<hero>/summary.txt`).
* `EmoteHoldCheck` (editor tool, the REAL `AwardPoint` flow, one fresh play session per case): a won game holds the next serve until the taunt is over; a plain point keeps the 2.4 s beat and plays no emote.  The game timers run at GameSpeed 1.2x real time, so the hold is (clip length + 0.4 s) x GameSpeed.

| case | hero | serve timer after the award (game s) | emote ended (real s) | next point (real s) | ok |
|---|---|---|---|---|---|
| EmoteScuba | male | 6.103 | 4.717 | 5.117 | True |
| EmoteThrust | male | 4.663 | 3.517 | 3.917 | True |
| EmoteSpike | male | 4.303 | 3.217 | 3.617 | True |
| none (plain point) | male | 2.383 | - | - | True |
| EmoteScuba | female | 6.103 | 4.717 | 5.117 | True |
| EmoteThrust | female | 4.663 | 3.517 | 3.917 | True |
| EmoteSpike | female | 4.303 | 3.217 | 3.617 | True |
| none (plain point) | female | 2.383 | - | - | True |

* Unity EditMode suite in the patched clone: 232 / 233 pass; the one failure, `TennisTutorialTests.KitColoursParseFromTheLaunchMessage`, fails identically with this job's C# changes removed (checked) - it is about kit colours.

## Extra, not gated: cloth enclosure (`scripts/collide4.py`, every frame, Blender-evaluated shirt / shorts)

An arm vertex counts as ENCLOSED when 15 of 16 rays hit the garment (it is inside the cloth, not beside it); the arm's own sleeve is excluded.  The READY pose itself has the right hand tucked under the shirt hem (9-23 vertices), so the first and last 0.30 s are listed separately.

| clip | hero | READY-edge frames: max enclosed | mid-clip frames with any | mid-clip max enclosed (of ~2000 vertices per arm) | where |
|---|---|---|---|---|---|
| Emote_Spike | male | 20 | 5 of 79 | 13 | shirt, shorts |
| Emote_Spike | female | 12 | 4 of 79 | 2 | shorts |
| Emote_Thrust | male | 22 | 0 of 88 | 0 |  |
| Emote_Thrust | female | 9 | 0 of 88 | 0 |  |
| Emote_Scuba | male | 24 | 4 of 124 | 5 | shirt, shorts |
| Emote_Scuba | female | 10 | 0 of 124 | 0 |  |

Reading: away from the READY edges the arms are never inside the cloth except for a few fingertip / hand vertices in a few frames where a hand brushes a hem (at most 13 vertices).
