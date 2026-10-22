# Garment stress report: GolfKitHero_Female

Stress poses: 153 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 768075 skin pixels through cloth, in 152 poses
- GATE LAYERS: FAIL - 13341 garment pixels through an outer garment, in 125 poses
- by victim: {'body': 768075, 'Acc_GloveL': 13193, 'Kit_Bottom': 148}
- by victim<coverer: {'body<Kit_Top': 760414, 'Acc_GloveL<Kit_Top': 10550, 'body<Kit_Bottom': 3143, 'Acc_GloveL<Kit_Bottom': 2643, 'body<Kit_Shoe_R': 2532, 'body<Kit_Shoe_L': 1986, 'Kit_Bottom<Kit_Top': 75, 'Kit_Bottom<Acc_GloveL': 73}
- HOLES (hidden skin seen through): 55268 px in 140 poses
  - holes split: background 3693, lining 13113, outer surface > 3 cm behind 38462

Before: tear 225768 px (153 poses), layer 15811 px (117 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | moves__Emote_Shock | 25 | elbow_L, elbow_R | 13427 | 362 | {'body': 13427, 'Acc_GloveL': 362} |
| 1 | moves__Emote_Shock | 36 | elbow_L, elbow_R, lunge | 13375 | 168 | {'body': 13375, 'Acc_GloveL': 168} |
| 2 | moves__Emote_Shock | 15 | elbow_L, elbow_R, lunge | 13365 | 158 | {'body': 13365, 'Acc_GloveL': 158} |
| 3 | moves__Emote_Victory | 33 | elbow_L, knee_R, kneel | 10047 | 424 | {'body': 10047, 'Acc_GloveL': 424} |
| 4 | golf__Putt | 40 | across_R, elbow_L, elbow_R | 10078 | 186 | {'body': 10078, 'Kit_Bottom': 4, 'Acc_GloveL': 182} |
| 5 | moves__Emote_JumpJoy | 18 | elbow_L, elbow_R, knee_R | 9184 | 734 | {'body': 9184, 'Acc_GloveL': 734} |
| 6 | golf__IronSwing | 6 | across_R, elbow_L, elbow_R | 9802 | 2 | {'body': 9802, 'Kit_Bottom': 2} |
| 7 | golf__Putt | 23 | elbow_L, elbow_R, hipflex_L | 9728 | 31 | {'body': 9728, 'Acc_GloveL': 31} |
| 8 | golf__Putt | 7 | elbow_L, elbow_R, hipflex_L | 9320 | 263 | {'body': 9320, 'Acc_GloveL': 263} |
| 9 | golf__Putt | 15 | elbow_L, elbow_R, hipflex_L | 9118 | 227 | {'body': 9118, 'Acc_GloveL': 227} |
| 10 | golf__Putt | 31 | elbow_L, elbow_R, hipflex_L | 8966 | 176 | {'body': 8966, 'Acc_GloveL': 176} |
| 11 | golf__HalfSwing | 25 | across_L, kneel | 9138 | 0 | {'body': 9138} |
