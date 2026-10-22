# Garment stress report: MatchHero_Female

Stress poses: 152 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 126415 skin pixels through cloth, in 147 poses
- GATE LAYERS: FAIL - 2956 garment pixels through an outer garment, in 52 poses
- by victim: {'body': 126415, 'Kit_Top': 275, 'Kit_Bottom': 2681}
- by victim<coverer: {'body<Kit_Top': 119846, 'body<Kit_Bottom': 6569, 'Kit_Bottom<Kit_Top': 2681, 'Kit_Top<Kit_Bottom': 275}
- HOLES (hidden skin seen through): 9410 px in 113 poses

Before: tear 352507 px (152 poses), layer 13 px (1 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Female_Emote_Thrust | 93 | elbow_L, hipabd_L, hipabd_R | 4092 | 58 | {'body': 4092, 'Kit_Bottom': 53, 'Kit_Top': 5} |
| 1 | tennis__Female_Emote_Thrust | 84 | elbow_L, elbow_R, hipabd_L | 3858 | 66 | {'body': 3858, 'Kit_Bottom': 61, 'Kit_Top': 5} |
| 2 | tennis__Female_SplitToBackhand | 5 | hipabd_R, trunk_twist, waist | 3607 | 144 | {'body': 3607, 'Kit_Bottom': 144} |
| 3 | tennis__Female_BackhandWide | 14 | hipflex_L, knee_L, kneel | 3552 | 167 | {'body': 3552, 'Kit_Bottom': 167} |
| 4 | tennis__Female_Serve | 10 | elbow_L, elbow_R, hipflex_L | 3317 | 156 | {'body': 3317, 'Kit_Bottom': 156} |
| 5 | tennis__Female_SplitToBackhand | 13 | hipabd_R, hipflex_L, hipflex_R | 2952 | 141 | {'body': 2952, 'Kit_Bottom': 141} |
| 6 | tennis__Female_Return | 7 | hipabd_R, hipflex_L, knee_L | 2781 | 135 | {'body': 2781, 'Kit_Bottom': 135} |
| 7 | tennis__Female_Emote_Spike | 24 | armback_R, elbow_R, trunk_side | 2589 | 0 | {'body': 2589} |
| 8 | moves__Emote_Defeat | 49 | knee_L, knee_R, kneel | 2336 | 0 | {'body': 2336} |
| 9 | tennis__Female_Intro_Wave | 39 | elbow_R, trunk_side | 2335 | 0 | {'body': 2335} |
| 10 | tennis__Female_Emote_Defeat | 49 | knee_L, knee_R, kneel | 2335 | 0 | {'body': 2335} |
| 11 | moves__Emote_Victory | 33 | elbow_L | 2328 | 5 | {'body': 2328, 'Kit_Top': 5} |
