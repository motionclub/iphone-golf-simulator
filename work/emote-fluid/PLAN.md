# Fluidity polish plan — revision 10 candidate, revision 09 measured baseline

Status: FAIL. No revision 31 candidate is installed. Every gate keeps the prompt threshold. Shared exaggeration level: 6/10; translation pulses 0.94–1.06 of the spine chain, authored overshoot 12%, normally 3–6 source frames of settle, then measured again after retiming. Native visible settle is what F5 gates. Fingers overlap by one frame where contacts allow.

Adnan authorized READY-edge retiming while retaining endpoint poses and contacts. The trailing edge uses a smooth source-time ramp to the original endpoint and then holds it. Spike and Pushups additionally slow their first 0.15 seconds. Socket scales remain original while the separate exact-unit-scale clarification is pending.

Revision 10 uses original world foot/toe targets at 60 Hz, instead of the erroneous post-polish FK targets. Scuba right reach is at least 0.994 of arm length; hand yaw is preserved relative to the actual pelvis. Wave lower-hand settle is four source frames. Plank and Scuba pickup settle are three source frames. These are authored changes, not measured passes.

Reference rules: De Lotto — stagger body links; Seymour — follow-through; Kelly — overshoot/settle and holds that continue arriving momentum; Gibson — stretched arrivals, delayed head and timed pose accents; Fortnite — spine bone translation; Cooper — preserve the action and exaggerate its timing; Rosen — cubic continuity and damped transitions; Unity Damped Transform — separate translation/rotation damping. The supplied Vimeo page reports unable to play media; its authored process description is read but footage remains unverified.

## Numbers before the revision 10 corrections

| Hero/clip | F1 before→09 (≤2) | F2 moves | F3 linear/flat | F4 holds | F5 poses | F6 actions | F7 kink ≤60° | F8 exact scale delta | F9 L/R ≥6° | F11 mm/° ≤150/15 |
|---|---|---|---|---|---|---|---|---|---|---|
| male/Emote_Spike | 10→8 | 4/5 | 0/6 | 0/0 | 5/5 | 5/5 | 124.01 @ 51 | 3.57627869e-07 | 19.09/28.50 | 116.51/12.00 |
| male/Emote_Scuba | 8→9 | 2/3 | 0/0 | 0/0 | 2/3 | 3/3 | 173.52 @ 134 | 4.76837158e-07 | 28.35/28.83 | 107.10/6.02 |
| male/Emote_Thrust | 11→9 | 3/4 | 0/1 | 1/1 | 2/4 | 4/4 | 179.79 @ 29 | 4.76837158e-07 | 47.22/47.25 | 95.95/5.31 |
| male/Intro_Wave | 5→6 | 2/2 | 0/18 | 1/1 | 1/2 | 2/2 | 174.69 @ 39 | 3.57627869e-07 | 21.29/7.00 | 138.01/11.05 |
| male/Intro_BringIt | 7→8 | 3/4 | 0/16 | 0/1 | 3/4 | 4/4 | 156.97 @ 62 | 3.57627869e-07 | 11.34/20.66 | 35.38/4.55 |
| male/Intro_Pushups | 10→10 | 6/9 | 0/24 | 0/0 | 8/9 | 7/9 | 172.04 @ 10 | 4.76837158e-07 | 41.16/43.62 | 175.86/12.00 |
| female/Emote_Spike | 11→8 | 4/5 | 0/6 | 0/0 | 5/5 | 5/5 | 128.66 @ 8 | 4.76837158e-07 | 18.37/28.24 | 100.07/12.00 |
| female/Emote_Scuba | 10→8 | 2/3 | 0/1 | 0/0 | 2/3 | 3/3 | 173.67 @ 134 | 5.96046448e-07 | 28.36/28.80 | 103.20/12.00 |
| female/Emote_Thrust | 11→9 | 3/4 | 0/0 | 1/1 | 2/4 | 4/4 | 179.68 @ 29 | 3.57627869e-07 | 47.26/47.28 | 89.89/8.35 |
| female/Intro_Wave | 5→6 | 2/2 | 0/15 | 1/1 | 1/2 | 2/2 | 168.27 @ 39 | 4.76837158e-07 | 21.69/7.00 | 103.66/8.22 |
| female/Intro_BringIt | 7→8 | 3/4 | 0/15 | 0/1 | 3/4 | 4/4 | 165.16 @ 82 | 3.57627869e-07 | 11.76/18.63 | 33.53/7.79 |
| female/Intro_Pushups | 10→9 | 6/9 | 0/22 | 0/0 | 8/9 | 7/9 | 155.18 @ 10 | 3.57627869e-07 | 48.52/50.35 | 180.96/12.00 |

## male/Emote_Spike

Approved story beats: [9, 27, 36, 45, 51, 59, 66, 84]. Planned impacts: [36, 59]. Fast swings: [[27, 36], [51, 59]]. Intended holds: []. Money pose: [36, 43]; required 6–12 frame hold and 2–4 frame exit remains unverified (FAIL).

| Action | Anticipation window | Pose / settle-end at 30 fps | Chain native peak targets | Squash/stretch |
|---|---|---|---|---|
| overhead wind-up | [6, 10] | 29 / 33 | Hips → Spine → Chest → Neck → Head: [18, 19, 20, 21, 22] | none |
| first slam | [22, 28] | 38 / 42 | Hips → Spine → Chest → Neck → Head: [32, 33, 34, 35, 36] | squash |
| smaller relift | [39, 45] | 51 / 54 | Hips → Spine → Chest → Neck → Head: [48, 49, 50, 51, 52] | none |
| second slam | [46, 52] | 59 / 62 | Hips → Spine → Chest → Neck → Head: [55, 56, 57, 58, 59] | squash |
| stand and glare | [60, 66] | 84 / 87 | Hips → Spine → Chest → Neck → Head: [75, 76, 77, 78, 79] | none |

Revision 09 failures to repair: F1 8 at frame 45; F7 124.01° at RightHand frame 51; F3 6 flat runs. Detailed measured per-action gaps, anticipation and settles remain in iterations/09/data/after/audit.json. Contacts and original story event frames override free motion. Original hand targets and orientation are retained at contact windows; free Wave/BringIt left arms use the FK curve layer. Feet are now constrained independently at 60 Hz. Every constraint is checked again on exported data and dressed skin.

## male/Emote_Scuba

Approved story beats: [6, 16, 27, 38, 49, 60, 71, 82, 93, 104, 120, 123, 132]. Planned impacts: [18, 123]. Fast swings: []. Intended holds: []. Money pose: [120, 123]; required 6–12 frame hold and 2–4 frame exit remains unverified (FAIL).

| Action | Anticipation window | Pose / settle-end at 30 fps | Chain native peak targets | Squash/stretch |
|---|---|---|---|---|
| enter nose-pinch and swim | [2, 8] | 18 / 22 | Hips → Spine → Chest → Neck → Head: [12, 13, 14, 15, 16] | none |
| lower to pickup | [99, 105] | 122 / 125 | Hips → Spine → Chest → Neck → Head: [112, 113, 114, 115, 116] | squash |
| rise with racket | [118, 124] | 131 / 134 | Hips → Spine → Chest → Neck → Head: [127, 128, 129, 130, 131] | stretch |

Revision 09 failures to repair: F1 9 at frame 136; F7 173.52° at LeftHand frame 134; F3 0 flat runs. Detailed measured per-action gaps, anticipation and settles remain in iterations/09/data/after/audit.json. Contacts and original story event frames override free motion. Original hand targets and orientation are retained at contact windows; free Wave/BringIt left arms use the FK curve layer. Feet are now constrained independently at 60 Hz. Every constraint is checked again on exported data and dressed skin.

## male/Emote_Thrust

Approved story beats: [13, 18, 26, 35, 43, 51, 66, 77, 91]. Planned impacts: []. Fast swings: []. Intended holds: [[20, 26], [37, 43], [51, 69], [77, 91]]. Money pose: [51, 63]; required 6–12 frame hold and 2–4 frame exit remains unverified (FAIL).

| Action | Anticipation window | Pose / settle-end at 30 fps | Chain native peak targets | Squash/stretch |
|---|---|---|---|---|
| first hip drive | [8, 14] | 18 / 21 | Hips → Spine → Chest → Neck → Head: [16, 17, 18, 19, 20] | none |
| second hip drive | [25, 31] | 35 / 38 | Hips → Spine → Chest → Neck → Head: [33, 34, 35, 36, 37] | none |
| third hip drive | [41, 47] | 51 / 54 | Hips → Spine → Chest → Neck → Head: [49, 50, 51, 52, 53] | none |
| strut arrival | [63, 69] | 79 / 83 | Hips → Spine → Chest → Neck → Head: [73, 74, 75, 76, 77] | none |

Revision 09 failures to repair: F1 9 at frame 63; F7 179.79° at RightHand frame 29; F3 1 flat runs. Detailed measured per-action gaps, anticipation and settles remain in iterations/09/data/after/audit.json. Contacts and original story event frames override free motion. Original hand targets and orientation are retained at contact windows; free Wave/BringIt left arms use the FK curve layer. Feet are now constrained independently at 60 Hz. Every constraint is checked again on exported data and dressed skin.

## male/Intro_Wave

Approved story beats: [12, 15, 21, 27, 33, 39, 47, 52]. Planned impacts: []. Fast swings: []. Intended holds: [[16, 39]]. Money pose: [36, 45]; required 6–12 frame hold and 2–4 frame exit remains unverified (FAIL).

| Action | Anticipation window | Pose / settle-end at 30 fps | Chain native peak targets | Squash/stretch |
|---|---|---|---|---|
| raise waving hand | [0, 6] | 12 / 15 | LeftUpperArm → LeftLowerArm → LeftHand: [9, 10, 11] | none |
| lower waving hand | [34, 40] | 47 / 50 | LeftUpperArm → LeftLowerArm → LeftHand: [43, 44, 45] | none |

Revision 09 failures to repair: F1 6 at frame 55; F7 174.69° at LeftHand frame 39; F3 18 flat runs. Detailed measured per-action gaps, anticipation and settles remain in iterations/09/data/after/audit.json. Contacts and original story event frames override free motion. Original hand targets and orientation are retained at contact windows; free Wave/BringIt left arms use the FK curve layer. Feet are now constrained independently at 60 Hz. Every constraint is checked again on exported data and dressed skin.

## male/Intro_BringIt

Approved story beats: [20, 26, 33, 41, 48, 56, 63, 71, 81]. Planned impacts: []. Fast swings: []. Intended holds: [[20, 70]]. Money pose: [63, 72]; required 6–12 frame hold and 2–4 frame exit remains unverified (FAIL).

| Action | Anticipation window | Pose / settle-end at 30 fps | Chain native peak targets | Squash/stretch |
|---|---|---|---|---|
| present challenge | [2, 8] | 20 / 24 | LeftUpperArm → LeftLowerArm → LeftHand: [14, 15, 16] | none |
| left step | [20, 26] | 33 / 36 | Hips → Spine → Chest → Neck → Head: [29, 30, 31, 32, 33] | none |
| right step | [41, 47] | 54 / 57 | Hips → Spine → Chest → Neck → Head: [50, 51, 52, 53, 54] | none |
| return to ready | [66, 72] | 79 / 82 | Hips → Spine → Chest → Neck → Head: [75, 76, 77, 78, 79] | none |

Revision 09 failures to repair: F1 8 at frame 26; F7 156.97° at RightHand frame 62; F3 16 flat runs. Detailed measured per-action gaps, anticipation and settles remain in iterations/09/data/after/audit.json. Contacts and original story event frames override free motion. Original hand targets and orientation are retained at contact windows; free Wave/BringIt left arms use the FK curve layer. Feet are now constrained independently at 60 Hz. Every constraint is checked again on exported data and dressed skin.

## male/Intro_Pushups

Approved story beats: [9, 13, 17, 28, 35, 41, 48, 55, 64, 70, 73, 82]. Planned impacts: [17, 28, 64, 73]. Fast swings: []. Intended holds: []. Money pose: [55, 63]; required 6–12 frame hold and 2–4 frame exit remains unverified (FAIL).

| Action | Anticipation window | Pose / settle-end at 30 fps | Chain native peak targets | Squash/stretch |
|---|---|---|---|---|
| set racket down | [0, 6] | 9 / 12 | Hips → Spine → Chest → Neck → Head: [6, 7, 8, 9, 10] | squash |
| reach floor | [8, 14] | 17 / 20 | Hips → Spine → Chest → Neck → Head: [15, 16, 17, 18, 19] | squash |
| extend plank | [12, 18] | 30 / 33 | Hips → Spine → Chest → Neck → Head: [23, 24, 25, 26, 27] | stretch |
| first pushup down | [23, 29] | 35 / 38 | Hips → Spine → Chest → Neck → Head: [32, 33, 34, 35, 36] | squash |
| first pushup up | [30, 36] | 41 / 44 | Hips → Spine → Chest → Neck → Head: [38, 39, 40, 41, 42] | stretch |
| second pushup down | [36, 42] | 48 / 51 | Hips → Spine → Chest → Neck → Head: [45, 46, 47, 48, 49] | squash |
| second pushup up | [43, 49] | 55 / 58 | Hips → Spine → Chest → Neck → Head: [52, 53, 54, 55, 56] | stretch |
| fold back | [51, 57] | 64 / 67 | Hips → Spine → Chest → Neck → Head: [60, 61, 62, 63, 64] | squash |
| stand after pickup | [68, 74] | 80 / 82 | Hips → Spine → Chest → Neck → Head: [77, 78, 79, 80, 81] | stretch |

Revision 09 failures to repair: F1 10 at frame 85; F7 172.04° at HeadTop frame 10; F3 24 flat runs. Detailed measured per-action gaps, anticipation and settles remain in iterations/09/data/after/audit.json. Contacts and original story event frames override free motion. Original hand targets and orientation are retained at contact windows; free Wave/BringIt left arms use the FK curve layer. Feet are now constrained independently at 60 Hz. Every constraint is checked again on exported data and dressed skin.

## female/Emote_Spike

Approved story beats: [9, 27, 36, 45, 51, 59, 66, 84]. Planned impacts: [36, 59]. Fast swings: [[27, 36], [51, 59]]. Intended holds: []. Money pose: [36, 43]; required 6–12 frame hold and 2–4 frame exit remains unverified (FAIL).

| Action | Anticipation window | Pose / settle-end at 30 fps | Chain native peak targets | Squash/stretch |
|---|---|---|---|---|
| overhead wind-up | [6, 10] | 29 / 33 | Hips → Spine → Chest → Neck → Head: [18, 19, 20, 21, 22] | none |
| first slam | [22, 28] | 38 / 42 | Hips → Spine → Chest → Neck → Head: [32, 33, 34, 35, 36] | squash |
| smaller relift | [39, 45] | 51 / 54 | Hips → Spine → Chest → Neck → Head: [48, 49, 50, 51, 52] | none |
| second slam | [46, 52] | 59 / 62 | Hips → Spine → Chest → Neck → Head: [55, 56, 57, 58, 59] | squash |
| stand and glare | [60, 66] | 84 / 87 | Hips → Spine → Chest → Neck → Head: [75, 76, 77, 78, 79] | none |

Revision 09 failures to repair: F1 8 at frame 45; F7 128.66° at RightHand frame 8; F3 6 flat runs. Detailed measured per-action gaps, anticipation and settles remain in iterations/09/data/after/audit.json. Contacts and original story event frames override free motion. Original hand targets and orientation are retained at contact windows; free Wave/BringIt left arms use the FK curve layer. Feet are now constrained independently at 60 Hz. Every constraint is checked again on exported data and dressed skin.

## female/Emote_Scuba

Approved story beats: [6, 16, 27, 38, 49, 60, 71, 82, 93, 104, 120, 123, 132]. Planned impacts: [18, 123]. Fast swings: []. Intended holds: []. Money pose: [120, 123]; required 6–12 frame hold and 2–4 frame exit remains unverified (FAIL).

| Action | Anticipation window | Pose / settle-end at 30 fps | Chain native peak targets | Squash/stretch |
|---|---|---|---|---|
| enter nose-pinch and swim | [2, 8] | 18 / 22 | Hips → Spine → Chest → Neck → Head: [12, 13, 14, 15, 16] | none |
| lower to pickup | [99, 105] | 122 / 125 | Hips → Spine → Chest → Neck → Head: [112, 113, 114, 115, 116] | squash |
| rise with racket | [118, 124] | 131 / 134 | Hips → Spine → Chest → Neck → Head: [127, 128, 129, 130, 131] | stretch |

Revision 09 failures to repair: F1 8 at frame 105; F7 173.67° at LeftHand frame 134; F3 1 flat runs. Detailed measured per-action gaps, anticipation and settles remain in iterations/09/data/after/audit.json. Contacts and original story event frames override free motion. Original hand targets and orientation are retained at contact windows; free Wave/BringIt left arms use the FK curve layer. Feet are now constrained independently at 60 Hz. Every constraint is checked again on exported data and dressed skin.

## female/Emote_Thrust

Approved story beats: [13, 18, 26, 35, 43, 51, 66, 77, 91]. Planned impacts: []. Fast swings: []. Intended holds: [[20, 26], [37, 43], [51, 69], [77, 91]]. Money pose: [51, 63]; required 6–12 frame hold and 2–4 frame exit remains unverified (FAIL).

| Action | Anticipation window | Pose / settle-end at 30 fps | Chain native peak targets | Squash/stretch |
|---|---|---|---|---|
| first hip drive | [8, 14] | 18 / 21 | Hips → Spine → Chest → Neck → Head: [16, 17, 18, 19, 20] | none |
| second hip drive | [25, 31] | 35 / 38 | Hips → Spine → Chest → Neck → Head: [33, 34, 35, 36, 37] | none |
| third hip drive | [41, 47] | 51 / 54 | Hips → Spine → Chest → Neck → Head: [49, 50, 51, 52, 53] | none |
| strut arrival | [63, 69] | 79 / 83 | Hips → Spine → Chest → Neck → Head: [73, 74, 75, 76, 77] | none |

Revision 09 failures to repair: F1 9 at frame 63; F7 179.68° at RightHand frame 29; F3 0 flat runs. Detailed measured per-action gaps, anticipation and settles remain in iterations/09/data/after/audit.json. Contacts and original story event frames override free motion. Original hand targets and orientation are retained at contact windows; free Wave/BringIt left arms use the FK curve layer. Feet are now constrained independently at 60 Hz. Every constraint is checked again on exported data and dressed skin.

## female/Intro_Wave

Approved story beats: [12, 15, 21, 27, 33, 39, 47, 52]. Planned impacts: []. Fast swings: []. Intended holds: [[16, 39]]. Money pose: [36, 45]; required 6–12 frame hold and 2–4 frame exit remains unverified (FAIL).

| Action | Anticipation window | Pose / settle-end at 30 fps | Chain native peak targets | Squash/stretch |
|---|---|---|---|---|
| raise waving hand | [0, 6] | 12 / 15 | LeftUpperArm → LeftLowerArm → LeftHand: [9, 10, 11] | none |
| lower waving hand | [34, 40] | 47 / 50 | LeftUpperArm → LeftLowerArm → LeftHand: [43, 44, 45] | none |

Revision 09 failures to repair: F1 6 at frame 55; F7 168.27° at LeftHand frame 39; F3 15 flat runs. Detailed measured per-action gaps, anticipation and settles remain in iterations/09/data/after/audit.json. Contacts and original story event frames override free motion. Original hand targets and orientation are retained at contact windows; free Wave/BringIt left arms use the FK curve layer. Feet are now constrained independently at 60 Hz. Every constraint is checked again on exported data and dressed skin.

## female/Intro_BringIt

Approved story beats: [20, 26, 33, 41, 48, 56, 63, 71, 81]. Planned impacts: []. Fast swings: []. Intended holds: [[20, 70]]. Money pose: [63, 72]; required 6–12 frame hold and 2–4 frame exit remains unverified (FAIL).

| Action | Anticipation window | Pose / settle-end at 30 fps | Chain native peak targets | Squash/stretch |
|---|---|---|---|---|
| present challenge | [2, 8] | 20 / 24 | LeftUpperArm → LeftLowerArm → LeftHand: [14, 15, 16] | none |
| left step | [20, 26] | 33 / 36 | Hips → Spine → Chest → Neck → Head: [29, 30, 31, 32, 33] | none |
| right step | [41, 47] | 54 / 57 | Hips → Spine → Chest → Neck → Head: [50, 51, 52, 53, 54] | none |
| return to ready | [66, 72] | 79 / 82 | Hips → Spine → Chest → Neck → Head: [75, 76, 77, 78, 79] | none |

Revision 09 failures to repair: F1 8 at frame 26; F7 165.16° at HeadTop frame 82; F3 15 flat runs. Detailed measured per-action gaps, anticipation and settles remain in iterations/09/data/after/audit.json. Contacts and original story event frames override free motion. Original hand targets and orientation are retained at contact windows; free Wave/BringIt left arms use the FK curve layer. Feet are now constrained independently at 60 Hz. Every constraint is checked again on exported data and dressed skin.

## female/Intro_Pushups

Approved story beats: [9, 13, 17, 28, 35, 41, 48, 55, 64, 70, 73, 82]. Planned impacts: [17, 28, 64, 73]. Fast swings: []. Intended holds: []. Money pose: [55, 63]; required 6–12 frame hold and 2–4 frame exit remains unverified (FAIL).

| Action | Anticipation window | Pose / settle-end at 30 fps | Chain native peak targets | Squash/stretch |
|---|---|---|---|---|
| set racket down | [0, 6] | 9 / 12 | Hips → Spine → Chest → Neck → Head: [6, 7, 8, 9, 10] | squash |
| reach floor | [8, 14] | 17 / 20 | Hips → Spine → Chest → Neck → Head: [15, 16, 17, 18, 19] | squash |
| extend plank | [12, 18] | 30 / 33 | Hips → Spine → Chest → Neck → Head: [23, 24, 25, 26, 27] | stretch |
| first pushup down | [23, 29] | 35 / 38 | Hips → Spine → Chest → Neck → Head: [32, 33, 34, 35, 36] | squash |
| first pushup up | [30, 36] | 41 / 44 | Hips → Spine → Chest → Neck → Head: [38, 39, 40, 41, 42] | stretch |
| second pushup down | [36, 42] | 48 / 51 | Hips → Spine → Chest → Neck → Head: [45, 46, 47, 48, 49] | squash |
| second pushup up | [43, 49] | 55 / 58 | Hips → Spine → Chest → Neck → Head: [52, 53, 54, 55, 56] | stretch |
| fold back | [51, 57] | 64 / 67 | Hips → Spine → Chest → Neck → Head: [60, 61, 62, 63, 64] | squash |
| stand after pickup | [68, 74] | 80 / 82 | Hips → Spine → Chest → Neck → Head: [77, 78, 79, 80, 81] | stretch |

Revision 09 failures to repair: F1 9 at frame 85; F7 155.18° at HeadTop frame 10; F3 22 flat runs. Detailed measured per-action gaps, anticipation and settles remain in iterations/09/data/after/audit.json. Contacts and original story event frames override free motion. Original hand targets and orientation are retained at contact windows; free Wave/BringIt left arms use the FK curve layer. Feet are now constrained independently at 60 Hz. Every constraint is checked again on exported data and dressed skin.
