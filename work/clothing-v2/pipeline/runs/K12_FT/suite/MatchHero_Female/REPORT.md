# Garment stress report: MatchHero_Female

Stress poses: 152 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 60667 skin pixels through cloth, in 138 poses
- GATE LAYERS: FAIL - 1583 garment pixels through an outer garment, in 22 poses
- by victim: {'body': 60667, 'Kit_Bottom': 778, 'Kit_Top': 805}
- by victim<coverer: {'body<Kit_Top': 60667, 'Kit_Top<Kit_Bottom': 805, 'Kit_Bottom<Kit_Top': 778}
- HOLES (hidden skin seen through): 9444 px in 132 poses
  - holes split: background 7428, lining 1694, outer surface > 3 cm behind 322

Before: tear 352507 px (152 poses), layer 13 px (1 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Female_Emote_Thrust | 47 | hipabd_L, hipabd_R | 2580 | 0 | {'body': 2580} |
| 1 | tennis__Female_Emote_Thrust | 31 | hipabd_L, hipabd_R | 2494 | 0 | {'body': 2494} |
| 2 | moves__Emote_Victory | 33 | elbow_L | 1922 | 0 | {'body': 1922} |
| 3 | tennis__Female_Emote_Scuba | 104 | elbow_R, hipabd_R | 1834 | 0 | {'body': 1834} |
| 4 | tennis__Female_ForehandArmCorrected | 14 | elbow_L, lunge, trunk_twist | 1405 | 0 | {'body': 1405} |
| 5 | tennis__Female_BackhandWide | 14 | hipflex_L, knee_L, kneel | 1334 | 13 | {'body': 1334, 'Kit_Bottom': 13} |
| 6 | tennis__Female_ForehandWide | 17 | coverage, elbow_R, hipflex_R | 1313 | 0 | {'body': 1313} |
| 7 | tennis__Female_Emote_Spike | 24 | armback_R, elbow_R, trunk_side | 1228 | 55 | {'body': 1228, 'Kit_Bottom': 55} |
| 8 | tennis__Female_SplitToBackhand | 5 | hipabd_R, trunk_twist, waist | 1122 | 103 | {'body': 1122, 'Kit_Bottom': 103} |
| 9 | tennis__Female_Intro_Wave | 26 | elbow_R | 1145 | 0 | {'body': 1145} |
| 10 | moves__Emote_Victory | 77 | elbow_R | 1104 | 0 | {'body': 1104} |
| 11 | tennis__Female_Emote_Victory | 77 | elbow_R | 1099 | 0 | {'body': 1099} |
