# Garment stress report: GolfKitHero_Female

Stress poses: 40 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 194225 skin pixels through cloth, in 40 poses
- GATE LAYERS: FAIL - 5358 garment pixels through an outer garment, in 31 poses
- by victim: {'body': 194225, 'Acc_GloveL': 5272, 'Kit_Bottom': 86}
- by victim<coverer: {'body<Kit_Top': 193893, 'Acc_GloveL<Kit_Top': 4364, 'Acc_GloveL<Kit_Bottom': 908, 'body<Kit_Bottom': 265, 'Kit_Bottom<Kit_Top': 86, 'body<Kit_Shoe_R': 58, 'body<Kit_Shoe_L': 9}
- HOLES (hidden skin seen through): 6229 px in 38 poses
  - holes split: background 15, lining 2043, outer surface > 3 cm behind 4171

Before: tear 427327 px (153 poses), layer 12736 px (128 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | moves__Emote_Shock | 25 | elbow_L, elbow_R | 8339 | 433 | {'body': 8339, 'Acc_GloveL': 433} |
| 1 | moves__Emote_Shock | 36 | elbow_L, elbow_R, lunge | 8298 | 204 | {'body': 8298, 'Acc_GloveL': 204} |
| 2 | moves__Emote_Shock | 15 | elbow_L, elbow_R, lunge | 8308 | 169 | {'body': 8308, 'Acc_GloveL': 169} |
| 3 | golf__FistPump | 73 | elbow_L, elbow_R, lunge | 6619 | 79 | {'body': 6619, 'Kit_Bottom': 10, 'Acc_GloveL': 69} |
| 4 | moves__Emote_Victory | 33 | elbow_L, knee_R, kneel | 6224 | 377 | {'body': 6224, 'Kit_Bottom': 5, 'Acc_GloveL': 372} |
| 5 | golf__HalfSwing | 25 | across_L, kneel | 6244 | 4 | {'body': 6244, 'Kit_Bottom': 4} |
| 6 | golf__Emote_Spike | 9 | across_R, coverage, elbow_L | 6176 | 47 | {'body': 6176, 'Kit_Bottom': 13, 'Acc_GloveL': 34} |
| 7 | moves__Emote_JumpJoy | 18 | elbow_L, elbow_R, knee_R | 4644 | 801 | {'body': 4644, 'Acc_GloveL': 801} |
| 8 | golf__IronSwing | 57 | elbow_L, hipabd_L, kneel | 5043 | 333 | {'body': 5043, 'Acc_GloveL': 333} |
| 9 | golf__Putt | 40 | across_R, elbow_L, elbow_R | 5059 | 232 | {'body': 5059, 'Kit_Bottom': 4, 'Acc_GloveL': 228} |
| 10 | golf__IronSwing | 49 | elbow_L, hipabd_L, kneel | 5031 | 194 | {'body': 5031, 'Acc_GloveL': 194} |
| 11 | golf__Putt | 7 | elbow_L, elbow_R, hipflex_L | 5061 | 156 | {'body': 5061, 'Kit_Bottom': 2, 'Acc_GloveL': 154} |
