# Garment stress report: GolfKitHero_Female

Stress poses: 40 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 313279 skin pixels through cloth, in 40 poses
- GATE LAYERS: FAIL - 4587 garment pixels through an outer garment, in 32 poses
- by victim: {'body': 313279, 'Acc_GloveL': 4484, 'Kit_Bottom': 103}
- by victim<coverer: {'body<Kit_Top': 313045, 'Acc_GloveL<Kit_Top': 3576, 'Acc_GloveL<Kit_Bottom': 908, 'body<Kit_Bottom': 167, 'Kit_Bottom<Kit_Top': 103, 'body<Kit_Shoe_R': 58, 'body<Kit_Shoe_L': 9}
- HOLES (hidden skin seen through): 347672 px in 39 poses
  - holes split: background 20782, lining 23478, outer surface > 3 cm behind 303412

Before: tear 427327 px (153 poses), layer 12736 px (128 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | moves__Emote_Shock | 25 | elbow_L, elbow_R | 13207 | 558 | {'body': 13207, 'Acc_GloveL': 558} |
| 1 | moves__Emote_Shock | 15 | elbow_L, elbow_R, lunge | 11132 | 93 | {'body': 11132, 'Acc_GloveL': 93} |
| 2 | golf__HalfSwing | 25 | across_L, kneel | 11206 | 3 | {'body': 11206, 'Kit_Bottom': 3} |
| 3 | moves__Emote_Shock | 36 | elbow_L, elbow_R, lunge | 10904 | 169 | {'body': 10904, 'Acc_GloveL': 169} |
| 4 | golf__IronSwing | 57 | elbow_L, hipabd_L, kneel | 9342 | 330 | {'body': 9342, 'Kit_Bottom': 3, 'Acc_GloveL': 327} |
| 5 | golf__Putt | 7 | elbow_L, elbow_R, hipflex_L | 9644 | 2 | {'body': 9644, 'Kit_Bottom': 2} |
| 6 | golf__IronSwing | 49 | elbow_L, hipabd_L, kneel | 9310 | 183 | {'body': 9310, 'Kit_Bottom': 4, 'Acc_GloveL': 179} |
| 7 | golf__Putt | 40 | across_R, elbow_L, elbow_R | 9439 | 9 | {'body': 9439, 'Kit_Bottom': 4, 'Acc_GloveL': 5} |
| 8 | golf__Putt | 15 | elbow_L, elbow_R, hipflex_L | 9193 | 1 | {'body': 9193, 'Kit_Bottom': 1} |
| 9 | golf__Putt | 23 | elbow_L, elbow_R, hipflex_L | 9124 | 2 | {'body': 9124, 'Kit_Bottom': 2} |
| 10 | golf__Putt | 31 | elbow_L, elbow_R, hipflex_L | 9020 | 1 | {'body': 9020, 'Kit_Bottom': 1} |
| 11 | golf__HalfSwing | 17 | across_L, elbow_R, kneel | 8966 | 5 | {'body': 8966, 'Kit_Bottom': 5} |
