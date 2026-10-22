# Garment stress report: GolfKitHero_Female

Stress poses: 40 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 214038 skin pixels through cloth, in 40 poses
- GATE LAYERS: FAIL - 5444 garment pixels through an outer garment, in 31 poses
- by victim: {'body': 214038, 'Acc_GloveL': 5345, 'Kit_Bottom': 99}
- by victim<coverer: {'body<Kit_Top': 213689, 'Acc_GloveL<Kit_Top': 4442, 'Acc_GloveL<Kit_Bottom': 903, 'body<Kit_Bottom': 282, 'Kit_Bottom<Kit_Top': 99, 'body<Kit_Shoe_R': 58, 'body<Kit_Shoe_L': 9}
- HOLES (hidden skin seen through): 7496 px in 40 poses
  - holes split: background 86, lining 2043, outer surface > 3 cm behind 5367

Before: tear 427327 px (153 poses), layer 12736 px (128 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | moves__Emote_Shock | 25 | elbow_L, elbow_R | 11374 | 445 | {'body': 11374, 'Acc_GloveL': 445} |
| 1 | moves__Emote_Shock | 36 | elbow_L, elbow_R, lunge | 11509 | 225 | {'body': 11509, 'Acc_GloveL': 225} |
| 2 | moves__Emote_Shock | 15 | elbow_L, elbow_R, lunge | 11448 | 188 | {'body': 11448, 'Acc_GloveL': 188} |
| 3 | moves__Emote_Victory | 61 | coverage, elbow_L, elbow_R | 7145 | 0 | {'body': 7145} |
| 4 | moves__Emote_JumpJoy | 18 | elbow_L, elbow_R, knee_R | 6334 | 776 | {'body': 6334, 'Acc_GloveL': 776} |
| 5 | moves__Emote_Victory | 69 | coverage, elbow_L, elbow_R | 6953 | 0 | {'body': 6953} |
| 6 | golf__FistPump | 73 | elbow_L, elbow_R, lunge | 6702 | 83 | {'body': 6702, 'Kit_Bottom': 14, 'Acc_GloveL': 69} |
| 7 | moves__Emote_Victory | 53 | elbow_L, elbow_R, knee_R | 6702 | 0 | {'body': 6702} |
| 8 | moves__Emote_Victory | 41 | elbow_L, elbow_R, knee_R | 6584 | 0 | {'body': 6584} |
| 9 | golf__Emote_Spike | 9 | across_R, coverage, elbow_L | 6340 | 47 | {'body': 6340, 'Kit_Bottom': 13, 'Acc_GloveL': 34} |
| 10 | golf__HalfSwing | 25 | across_L, kneel | 6200 | 6 | {'body': 6200, 'Kit_Bottom': 6} |
| 11 | moves__Emote_JumpJoy | 28 | coverage, elbow_L, elbow_R | 5537 | 325 | {'body': 5537, 'Acc_GloveL': 325} |
