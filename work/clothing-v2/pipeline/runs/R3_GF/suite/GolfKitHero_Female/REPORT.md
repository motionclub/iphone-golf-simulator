# Garment stress report: GolfKitHero_Female

Stress poses: 153 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 431127 skin pixels through cloth, in 153 poses
- GATE LAYERS: FAIL - 13243 garment pixels through an outer garment, in 141 poses
- by victim: {'body': 431127, 'Acc_GloveL': 12658, 'Kit_Bottom': 585}
- by victim<coverer: {'body<Kit_Top': 423097, 'Acc_GloveL<Kit_Top': 9971, 'body<Kit_Bottom': 3512, 'Acc_GloveL<Kit_Bottom': 2687, 'body<Kit_Shoe_R': 2532, 'body<Kit_Shoe_L': 1986, 'Kit_Bottom<Kit_Top': 512, 'Kit_Bottom<Acc_GloveL': 73}
- HOLES (hidden skin seen through): 55222 px in 140 poses
  - holes split: background 3693, lining 13100, outer surface > 3 cm behind 38429

Before: tear 225768 px (153 poses), layer 15811 px (117 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | moves__Emote_Shock | 25 | elbow_L, elbow_R | 9779 | 438 | {'body': 9779, 'Acc_GloveL': 438} |
| 1 | moves__Emote_Shock | 15 | elbow_L, elbow_R, lunge | 9639 | 169 | {'body': 9639, 'Acc_GloveL': 169} |
| 2 | moves__Emote_Shock | 36 | elbow_L, elbow_R, lunge | 9571 | 205 | {'body': 9571, 'Acc_GloveL': 205} |
| 3 | golf__FistPump | 73 | elbow_L, elbow_R, lunge | 7137 | 85 | {'body': 7137, 'Kit_Bottom': 16, 'Acc_GloveL': 69} |
| 4 | golf__HalfSwing | 25 | across_L, kneel | 6768 | 6 | {'body': 6768, 'Kit_Bottom': 6} |
| 5 | golf__IronSwing | 57 | elbow_L, hipabd_L, kneel | 6428 | 345 | {'body': 6428, 'Acc_GloveL': 333, 'Kit_Bottom': 12} |
| 6 | golf__Drive | 59 | elbow_L, hipabd_L, kneel | 6635 | 77 | {'body': 6635, 'Acc_GloveL': 67, 'Kit_Bottom': 10} |
| 7 | golf__Drive | 51 | elbow_L, hipabd_L, kneel | 6230 | 75 | {'body': 6230, 'Acc_GloveL': 66, 'Kit_Bottom': 9} |
| 8 | golf__IronSwing | 49 | elbow_L, hipabd_L, kneel | 6058 | 222 | {'body': 6058, 'Acc_GloveL': 212, 'Kit_Bottom': 10} |
| 9 | golf__Putt | 53 | elbow_L, elbow_R, hipflex_L | 6081 | 148 | {'body': 6081, 'Kit_Bottom': 11, 'Acc_GloveL': 137} |
| 10 | moves__Emote_JumpJoy | 18 | elbow_L, elbow_R, knee_R | 5294 | 801 | {'body': 5294, 'Acc_GloveL': 801} |
| 11 | moves__Emote_Victory | 33 | elbow_L, knee_R, kneel | 5707 | 373 | {'body': 5707, 'Acc_GloveL': 373} |
