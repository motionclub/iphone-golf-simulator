# Garment stress report: GolfKitHero_Female

Stress poses: 40 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 146431 skin pixels through cloth, in 40 poses
- GATE LAYERS: FAIL - 6919 garment pixels through an outer garment, in 34 poses
- by victim: {'body': 146431, 'Acc_GloveL': 6690, 'Kit_Bottom': 220, 'Kit_Top': 9}
- by victim<coverer: {'body<Kit_Top': 145656, 'Acc_GloveL<Kit_Top': 5782, 'Acc_GloveL<Kit_Bottom': 908, 'body<Kit_Bottom': 708, 'Kit_Bottom<Kit_Top': 220, 'body<Kit_Shoe_R': 58, 'Kit_Top<Acc_GloveL': 9, 'body<Kit_Shoe_L': 9}
- HOLES (hidden skin seen through): 6229 px in 38 poses
  - holes split: background 15, lining 2043, outer surface > 3 cm behind 4171

Before: tear 427327 px (153 poses), layer 12736 px (128 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | moves__Emote_Shock | 25 | elbow_L, elbow_R | 7415 | 835 | {'body': 7415, 'Acc_GloveL': 835} |
| 1 | moves__Emote_Shock | 36 | elbow_L, elbow_R, lunge | 7274 | 517 | {'body': 7274, 'Acc_GloveL': 517} |
| 2 | moves__Emote_Shock | 15 | elbow_L, elbow_R, lunge | 7297 | 435 | {'body': 7297, 'Acc_GloveL': 435} |
| 3 | golf__Emote_Spike | 9 | across_R, coverage, elbow_L | 6177 | 34 | {'body': 6177, 'Acc_GloveL': 34} |
| 4 | golf__IronSwing | 57 | elbow_L, hipabd_L, kneel | 5431 | 392 | {'body': 5431, 'Kit_Bottom': 9, 'Acc_GloveL': 383} |
| 5 | golf__Drive | 59 | elbow_L, hipabd_L, kneel | 5655 | 84 | {'body': 5655, 'Kit_Bottom': 11, 'Acc_GloveL': 73} |
| 6 | golf__IronSwing | 49 | elbow_L, hipabd_L, kneel | 5238 | 202 | {'body': 5238, 'Acc_GloveL': 192, 'Kit_Bottom': 10} |
| 7 | golf__Drive | 51 | elbow_L, hipabd_L, kneel | 5339 | 80 | {'body': 5339, 'Acc_GloveL': 72, 'Kit_Bottom': 8} |
| 8 | golf__FistPump | 73 | elbow_L, elbow_R, lunge | 5276 | 78 | {'body': 5276, 'Kit_Bottom': 9, 'Acc_GloveL': 69} |
| 9 | golf__HalfSwing | 25 | across_L, kneel | 5222 | 8 | {'body': 5222, 'Kit_Bottom': 8} |
| 10 | golf__HalfSwing | 17 | across_L, elbow_R, kneel | 4854 | 19 | {'body': 4854, 'Kit_Bottom': 19} |
| 11 | golf__Cheer | 25 | axilla_L, axilla_R, elbow_L | 4051 | 307 | {'body': 4051, 'Acc_GloveL': 307} |
