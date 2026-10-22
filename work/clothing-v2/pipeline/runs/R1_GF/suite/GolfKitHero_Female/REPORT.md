# Garment stress report: GolfKitHero_Female

Stress poses: 153 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 585522 skin pixels through cloth, in 153 poses
- GATE LAYERS: FAIL - 13031 garment pixels through an outer garment, in 138 poses
- by victim: {'body': 585522, 'Acc_GloveL': 12467, 'Kit_Bottom': 507, 'Kit_Top': 57}
- by victim<coverer: {'body<Kit_Top': 577487, 'Acc_GloveL<Kit_Top': 9790, 'body<Kit_Bottom': 3505, 'Acc_GloveL<Kit_Bottom': 2677, 'body<Kit_Shoe_R': 2532, 'body<Kit_Shoe_L': 1986, 'Kit_Bottom<Kit_Top': 434, 'Kit_Bottom<Acc_GloveL': 73, 'Kit_Top<Acc_GloveL': 57, 'body<Acc_GloveL': 12}
- HOLES (hidden skin seen through): 55244 px in 140 poses
  - holes split: background 3693, lining 13105, outer surface > 3 cm behind 38446

Before: tear 225768 px (153 poses), layer 15811 px (117 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | moves__Emote_Shock | 25 | elbow_L, elbow_R | 14600 | 445 | {'body': 14600, 'Acc_GloveL': 445} |
| 1 | moves__Emote_Shock | 36 | elbow_L, elbow_R, lunge | 14439 | 220 | {'body': 14439, 'Acc_GloveL': 220} |
| 2 | moves__Emote_Shock | 15 | elbow_L, elbow_R, lunge | 14445 | 183 | {'body': 14445, 'Acc_GloveL': 183} |
| 3 | moves__Emote_Victory | 33 | elbow_L, knee_R, kneel | 10372 | 393 | {'body': 10372, 'Acc_GloveL': 373, 'Kit_Bottom': 20} |
| 4 | moves__Emote_JumpJoy | 18 | elbow_L, elbow_R, knee_R | 9784 | 774 | {'body': 9784, 'Acc_GloveL': 774} |
| 5 | golf__FistPump | 73 | elbow_L, elbow_R, lunge | 9756 | 76 | {'body': 9756, 'Kit_Bottom': 7, 'Acc_GloveL': 69} |
| 6 | moves__Emote_Victory | 61 | coverage, elbow_L, elbow_R | 9547 | 0 | {'body': 9547} |
| 7 | moves__Emote_Victory | 53 | elbow_L, elbow_R, knee_R | 9402 | 0 | {'body': 9402} |
| 8 | moves__Emote_Victory | 41 | elbow_L, elbow_R, knee_R | 9377 | 0 | {'body': 9377} |
| 9 | moves__Emote_Victory | 69 | coverage, elbow_L, elbow_R | 9364 | 5 | {'body': 9364, 'Kit_Bottom': 5} |
| 10 | golf__Drive | 59 | elbow_L, hipabd_L, kneel | 8358 | 80 | {'body': 8358, 'Acc_GloveL': 70, 'Kit_Bottom': 10} |
| 11 | golf__IronSwing | 57 | elbow_L, hipabd_L, kneel | 8033 | 345 | {'body': 8033, 'Acc_GloveL': 333, 'Kit_Bottom': 12} |
