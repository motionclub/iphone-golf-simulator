# Garment stress report: MatchHero_Female

Stress poses: 152 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 91830 skin pixels through cloth, in 147 poses
- GATE LAYERS: FAIL - 939 garment pixels through an outer garment, in 10 poses
- by victim: {'body': 91830, 'Kit_Top': 559, 'Kit_Bottom': 380}
- by victim<coverer: {'body<Kit_Top': 91250, 'body<Kit_Bottom': 580, 'Kit_Top<Kit_Bottom': 559, 'Kit_Bottom<Kit_Top': 380}
- HOLES (hidden skin seen through): 9827 px in 132 poses

Before: tear 352507 px (152 poses), layer 13 px (1 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Female_Emote_Thrust | 47 | hipabd_L, hipabd_R | 3217 | 0 | {'body': 3217} |
| 1 | tennis__Female_Emote_Thrust | 31 | hipabd_L, hipabd_R | 3075 | 0 | {'body': 3075} |
| 2 | tennis__Female_ForehandArmCorrected | 26 | across_L, coverage, elbow_R | 2376 | 0 | {'body': 2376} |
| 3 | tennis__Female_Emote_Scuba | 123 | hipabd_L, hipabd_R, hipflex_L | 1643 | 595 | {'Kit_Top': 359, 'body': 1643, 'Kit_Bottom': 236} |
| 4 | tennis__Female_Emote_Defeat | 49 | knee_L, knee_R, kneel | 2115 | 0 | {'body': 2115} |
| 5 | moves__Emote_Defeat | 49 | knee_L, knee_R, kneel | 2106 | 0 | {'body': 2106} |
| 6 | moves__Emote_Defeat | 57 | knee_L, knee_R, kneel | 1974 | 0 | {'body': 1974} |
| 7 | tennis__Female_Emote_Defeat | 57 | knee_L, knee_R, kneel | 1969 | 0 | {'body': 1969} |
| 8 | tennis__Female_Emote_Victory | 77 | elbow_R | 1722 | 0 | {'body': 1722} |
| 9 | tennis__Female_Emote_Defeat | 24 | knee_R, kneel | 1656 | 0 | {'body': 1656} |
| 10 | moves__Emote_Victory | 77 | elbow_R | 1655 | 0 | {'body': 1655} |
| 11 | moves__Emote_Defeat | 24 | knee_R, kneel | 1652 | 0 | {'body': 1652} |
