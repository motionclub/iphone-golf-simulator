# Garment stress report: MatchHero_Female

Stress poses: 152 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 374340 skin pixels through cloth, in 152 poses
- GATE LAYERS: FAIL - 7946 garment pixels through an outer garment, in 96 poses
- by victim: {'body': 374340, 'Kit_Top': 7737, 'Kit_Bottom': 209}
- by victim<coverer: {'body<Kit_Top': 357740, 'body<Kit_Bottom': 16600, 'Kit_Top<Kit_Bottom': 7737, 'Kit_Bottom<Kit_Top': 209}
- HOLES (hidden skin seen through): 9600 px in 112 poses

Before: tear 352507 px (152 poses), layer 13 px (1 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Female_Overhead | 21 | armback_R, coverage, elbow_L | 8776 | 37 | {'body': 8776, 'Kit_Top': 37} |
| 1 | tennis__Female_ForehandShort | 3 | elbow_L, hipflex_R, knee_L | 5387 | 10 | {'body': 5387, 'Kit_Top': 10} |
| 2 | tennis__Female_SliceApproach | 23 | hipflex_R, knee_R, kneel | 5349 | 0 | {'body': 5349} |
| 3 | tennis__Female_Emote_Shock | 40 | coverage, elbow_L, elbow_R | 5287 | 0 | {'body': 5287} |
| 4 | moves__Emote_Shock | 40 | elbow_L, elbow_R, overhead | 5284 | 0 | {'body': 5284} |
| 5 | moves__Emote_Victory | 33 | elbow_L | 5235 | 0 | {'body': 5235} |
| 6 | tennis__Female_BackhandArmCorrected | 16 | across_L, hipabd_R, trunk_twist | 5079 | 138 | {'body': 5079, 'Kit_Top': 138} |
| 7 | moves__Emote_Shock | 9 | elbow_L, elbow_R | 5000 | 0 | {'body': 5000} |
| 8 | tennis__Female_Emote_Shock | 9 | coverage, elbow_L, elbow_R | 4994 | 0 | {'body': 4994} |
| 9 | tennis__Female_Emote_Shock | 31 | elbow_L, elbow_R, overhead | 4987 | 0 | {'body': 4987} |
| 10 | moves__Emote_Shock | 31 | elbow_L, elbow_R, overhead | 4979 | 0 | {'body': 4979} |
| 11 | moves__Emote_Shock | 17 | elbow_L, elbow_R, overhead | 4793 | 0 | {'body': 4793} |
