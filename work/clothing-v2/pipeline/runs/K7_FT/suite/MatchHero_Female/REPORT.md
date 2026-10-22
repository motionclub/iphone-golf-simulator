# Garment stress report: MatchHero_Female

Stress poses: 152 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 130573 skin pixels through cloth, in 148 poses
- GATE LAYERS: FAIL - 5201 garment pixels through an outer garment, in 50 poses
- by victim: {'body': 130573, 'Kit_Bottom': 4266, 'Kit_Top': 935}
- by victim<coverer: {'body<Kit_Top': 122161, 'body<Kit_Bottom': 8412, 'Kit_Bottom<Kit_Top': 4266, 'Kit_Top<Kit_Bottom': 935}
- HOLES (hidden skin seen through): 9518 px in 113 poses

Before: tear 352507 px (152 poses), layer 13 px (1 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Female_SliceApproach | 13 | across_R, coverage, hipflex_L | 3473 | 0 | {'body': 3473} |
| 1 | tennis__Female_Emote_Scuba | 123 | hipabd_L, hipabd_R, hipflex_L | 2597 | 344 | {'body': 2597, 'Kit_Bottom': 301, 'Kit_Top': 43} |
| 2 | tennis__Female_Emote_Spike | 39 | coverage, elbow_R, hipflex_L | 1976 | 373 | {'body': 1976, 'Kit_Bottom': 269, 'Kit_Top': 104} |
| 3 | moves__Emote_Victory | 33 | elbow_L | 2286 | 6 | {'body': 2286, 'Kit_Bottom': 6} |
| 4 | tennis__Female_Emote_Spike | 66 | hipflex_L, hipflex_R, kneel | 1885 | 358 | {'body': 1885, 'Kit_Bottom': 267, 'Kit_Top': 91} |
| 5 | tennis__Female_Emote_Spike | 58 | hipflex_L, hipflex_R, kneel | 1869 | 339 | {'body': 1869, 'Kit_Bottom': 247, 'Kit_Top': 92} |
| 6 | tennis__Female_Emote_Spike | 47 | hipflex_L, hipflex_R, kneel | 1802 | 379 | {'body': 1802, 'Kit_Bottom': 290, 'Kit_Top': 89} |
| 7 | moves__Emote_Defeat | 49 | knee_L, knee_R, kneel | 2167 | 0 | {'body': 2167} |
| 8 | tennis__Female_Emote_Defeat | 49 | knee_L, knee_R, kneel | 2166 | 0 | {'body': 2166} |
| 9 | tennis__Female_Emote_Scuba | 131 | hipabd_R, hipflex_L, hipflex_R | 2015 | 22 | {'body': 2015, 'Kit_Bottom': 2, 'Kit_Top': 20} |
| 10 | tennis__Female_Emote_Defeat | 57 | knee_L, knee_R, kneel | 2011 | 0 | {'body': 2011} |
| 11 | moves__Emote_Defeat | 57 | knee_L, knee_R, kneel | 2011 | 0 | {'body': 2011} |
