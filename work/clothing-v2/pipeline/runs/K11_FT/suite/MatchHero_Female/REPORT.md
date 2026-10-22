# Garment stress report: MatchHero_Female

Stress poses: 152 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 78850 skin pixels through cloth, in 141 poses
- GATE LAYERS: FAIL - 614 garment pixels through an outer garment, in 11 poses
- by victim: {'body': 78850, 'Kit_Top': 157, 'Kit_Bottom': 457}
- by victim<coverer: {'body<Kit_Top': 78850, 'Kit_Bottom<Kit_Top': 457, 'Kit_Top<Kit_Bottom': 157}
- HOLES (hidden skin seen through): 9459 px in 132 poses
  - holes split: background 7428, lining 1694, outer surface > 3 cm behind 337

Before: tear 352507 px (152 poses), layer 13 px (1 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | moves__Emote_Victory | 33 | elbow_L | 2760 | 0 | {'body': 2760} |
| 1 | tennis__Female_Emote_Thrust | 47 | hipabd_L, hipabd_R | 2645 | 0 | {'body': 2645} |
| 2 | tennis__Female_Emote_Thrust | 31 | hipabd_L, hipabd_R | 2536 | 0 | {'body': 2536} |
| 3 | tennis__Female_Emote_Scuba | 104 | elbow_R, hipabd_R | 2104 | 0 | {'body': 2104} |
| 4 | moves__Emote_Stomp | 10 | elbow_L, hipflex_R, knee_R | 1992 | 0 | {'body': 1992} |
| 5 | tennis__Female_Emote_Stomp | 10 | coverage, elbow_L, hipflex_R | 1968 | 0 | {'body': 1968} |
| 6 | tennis__Female_Emote_Thrust | 93 | elbow_L, hipabd_L, hipabd_R | 1920 | 0 | {'body': 1920} |
| 7 | tennis__Female_Emote_Thrust | 84 | elbow_L, elbow_R, hipabd_L | 1757 | 0 | {'body': 1757} |
| 8 | tennis__Female_BackhandWide | 14 | hipflex_L, knee_L, kneel | 1637 | 0 | {'body': 1637} |
| 9 | tennis__Female_ForehandShort | 3 | elbow_L, hipflex_R, knee_L | 1606 | 0 | {'body': 1606} |
| 10 | tennis__Female_SplitToBackhand | 5 | hipabd_R, trunk_twist, waist | 1519 | 0 | {'body': 1519} |
| 11 | tennis__Female_SliceApproach | 23 | hipflex_R, knee_R, kneel | 1425 | 0 | {'body': 1425} |
