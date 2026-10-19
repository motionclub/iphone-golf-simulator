# Garment stress report: MatchHero_Male

Stress poses: 153 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 284398 skin pixels through cloth, in 153 poses
- GATE LAYERS: FAIL - 63047 garment pixels through an outer garment, in 86 poses
- by victim: {'body': 284398, 'Kit_Bottom': 62970, 'Kit_Shoe_R': 77}
- HOLES (hidden skin seen through): 760 px in 24 poses

Before: tear 342039 px (103 poses), layer 52961 px (104 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Male_Intro_Pushups | 79 | hipflex_L, hipflex_R, knee_R | 11745 | 0 | {'body': 11745} |
| 1 | tennis__Male_Emote_Thrust | 47 | elbow_L, elbow_R, hipabd_L | 11452 | 0 | {'body': 11452} |
| 2 | tennis__Male_Emote_Thrust | 31 | coverage, elbow_R, hipabd_L | 10997 | 0 | {'body': 10997} |
| 3 | tennis__Male_Intro_Pushups | 71 | coverage, hipflex_L, hipflex_R | 7998 | 781 | {'body': 7998, 'Kit_Bottom': 781} |
| 4 | tennis__Male_Intro_Pushups | 10 | hipflex_L, hipflex_R, knee_L | 8200 | 434 | {'body': 8200, 'Kit_Bottom': 434} |
| 5 | tennis__Male_Emote_Scuba | 123 | hipabd_L, hipabd_R, hipflex_L | 6948 | 413 | {'body': 6948, 'Kit_Bottom': 413} |
| 6 | tennis__Male_Emote_Defeat | 49 | knee_L, knee_R, kneel | 3197 | 3300 | {'body': 3197, 'Kit_Bottom': 3300} |
| 7 | tennis__Male_Emote_Defeat | 66 | knee_L, knee_R, kneel | 3178 | 3318 | {'body': 3178, 'Kit_Bottom': 3318} |
| 8 | moves__Emote_Defeat | 49 | knee_L, knee_R, kneel | 3198 | 3289 | {'body': 3198, 'Kit_Bottom': 3289} |
| 9 | moves__Emote_Defeat | 14 | knee_L, knee_R, kneel | 3094 | 3334 | {'body': 3094, 'Kit_Bottom': 3334} |
| 10 | tennis__Male_Emote_Defeat | 14 | knee_L, knee_R, kneel | 3100 | 3327 | {'body': 3100, 'Kit_Bottom': 3327} |
| 11 | tennis__Male_Emote_Defeat | 41 | knee_R, kneel | 3059 | 3343 | {'body': 3059, 'Kit_Bottom': 3343} |
