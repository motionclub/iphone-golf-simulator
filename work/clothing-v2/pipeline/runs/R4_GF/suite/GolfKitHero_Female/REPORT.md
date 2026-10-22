# Garment stress report: GolfKitHero_Female

Stress poses: 153 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 427327 skin pixels through cloth, in 153 poses
- GATE LAYERS: FAIL - 12736 garment pixels through an outer garment, in 128 poses
- by victim: {'body': 427327, 'Acc_GloveL': 12379, 'Kit_Bottom': 356, 'Kit_Top': 1}
- by victim<coverer: {'body<Kit_Top': 419394, 'Acc_GloveL<Kit_Top': 9693, 'body<Kit_Bottom': 3415, 'Acc_GloveL<Kit_Bottom': 2686, 'body<Kit_Shoe_R': 2532, 'body<Kit_Shoe_L': 1986, 'Kit_Bottom<Kit_Top': 283, 'Kit_Bottom<Acc_GloveL': 73, 'Kit_Top<Acc_GloveL': 1}
- HOLES (hidden skin seen through): 55209 px in 140 poses
  - holes split: background 3693, lining 13100, outer surface > 3 cm behind 38416

Before: tear 225768 px (153 poses), layer 15811 px (117 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | moves__Emote_Shock | 25 | elbow_L, elbow_R | 10271 | 433 | {'body': 10271, 'Acc_GloveL': 433} |
| 1 | moves__Emote_Shock | 15 | elbow_L, elbow_R, lunge | 10229 | 169 | {'body': 10229, 'Acc_GloveL': 169} |
| 2 | moves__Emote_Shock | 36 | elbow_L, elbow_R, lunge | 10194 | 204 | {'body': 10194, 'Acc_GloveL': 204} |
| 3 | moves__Emote_Victory | 33 | elbow_L, knee_R, kneel | 7181 | 376 | {'body': 7181, 'Kit_Bottom': 4, 'Acc_GloveL': 372} |
| 4 | golf__FistPump | 73 | elbow_L, elbow_R, lunge | 7079 | 85 | {'body': 7079, 'Kit_Bottom': 16, 'Acc_GloveL': 69} |
| 5 | golf__HalfSwing | 25 | across_L, kneel | 6630 | 5 | {'body': 6630, 'Kit_Bottom': 5} |
| 6 | moves__Emote_JumpJoy | 36 | elbow_L, knee_R, kneel | 6286 | 165 | {'body': 6286, 'Acc_GloveL': 165} |
| 7 | moves__Emote_JumpJoy | 18 | elbow_L, elbow_R, knee_R | 5524 | 801 | {'body': 5524, 'Acc_GloveL': 801} |
| 8 | golf__Emote_Spike | 9 | across_R, coverage, elbow_L | 5973 | 45 | {'body': 5973, 'Acc_GloveL': 34, 'Kit_Bottom': 11} |
| 9 | golf__Putt | 40 | across_R, elbow_L, elbow_R | 5513 | 204 | {'body': 5513, 'Kit_Bottom': 4, 'Acc_GloveL': 200} |
| 10 | moves__Emote_Victory | 61 | coverage, elbow_L, elbow_R | 5688 | 0 | {'body': 5688} |
| 11 | golf__Putt | 7 | elbow_L, elbow_R, hipflex_L | 5388 | 229 | {'body': 5388, 'Kit_Bottom': 2, 'Acc_GloveL': 227} |
