# Garment stress report: MatchHero_Female

Stress poses: 152 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 62685 skin pixels through cloth, in 139 poses
- GATE LAYERS: FAIL - 1583 garment pixels through an outer garment, in 24 poses
- by victim: {'body': 62685, 'Kit_Top': 541, 'Kit_Bottom': 1042}
- by victim<coverer: {'body<Kit_Top': 62685, 'Kit_Bottom<Kit_Top': 1042, 'Kit_Top<Kit_Bottom': 541}
- HOLES (hidden skin seen through): 9495 px in 135 poses
  - holes split: background 7428, lining 1694, outer surface > 3 cm behind 373

Before: tear 352507 px (152 poses), layer 13 px (1 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Female_Emote_Thrust | 47 | hipabd_L, hipabd_R | 2703 | 0 | {'body': 2703} |
| 1 | tennis__Female_Emote_Thrust | 31 | hipabd_L, hipabd_R | 2596 | 0 | {'body': 2596} |
| 2 | tennis__Female_ForehandShort | 3 | elbow_L, hipflex_R, knee_L | 1698 | 10 | {'body': 1698, 'Kit_Bottom': 10} |
| 3 | tennis__Female_BackhandWide | 14 | hipflex_L, knee_L, kneel | 1334 | 0 | {'body': 1334} |
| 4 | tennis__Female_Intro_Wave | 26 | elbow_R | 1311 | 0 | {'body': 1311} |
| 5 | moves__Emote_Victory | 33 | elbow_L | 1268 | 0 | {'body': 1268} |
| 6 | tennis__Female_Intro_Wave | 39 | elbow_R, trunk_side | 1258 | 0 | {'body': 1258} |
| 7 | tennis__Female_SplitToBackhand | 5 | hipabd_R, trunk_twist, waist | 1177 | 0 | {'body': 1177} |
| 8 | tennis__Female_Emote_Thrust | 93 | elbow_L, hipabd_L, hipabd_R | 1131 | 0 | {'body': 1131} |
| 9 | tennis__Female_Emote_Stomp | 23 | hipflex_L, kneel | 1114 | 5 | {'body': 1114, 'Kit_Top': 4, 'Kit_Bottom': 1} |
| 10 | moves__Emote_Stomp | 23 | kneel | 1101 | 0 | {'body': 1101} |
| 11 | tennis__Female_Emote_Thrust | 84 | elbow_L, elbow_R, hipabd_L | 1077 | 0 | {'body': 1077} |
