# Garment stress report: MatchHero_Male

Stress poses: 153 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 224534 skin pixels through cloth, in 147 poses
- GATE LAYERS: FAIL - 21537 garment pixels through an outer garment, in 55 poses
- by victim: {'body': 224534, 'Kit_Bottom': 21460, 'Kit_Shoe_R': 77}
- by victim<coverer: {'body<Kit_Top': 198482, 'Kit_Bottom<Kit_Top': 21460, 'body<Kit_Shoe_L': 10335, 'body<Kit_Bottom': 7961, 'body<Kit_Shoe_R': 7756, 'Kit_Shoe_R<Kit_Sock_R': 77}
- HOLES (hidden skin seen through): 556 px in 16 poses

Before: tear 342039 px (103 poses), layer 52961 px (104 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Male_Emote_Thrust | 47 | elbow_L, elbow_R, hipabd_L | 10977 | 0 | {'body': 10977} |
| 1 | tennis__Male_Intro_Pushups | 79 | hipflex_L, hipflex_R, knee_R | 10882 | 0 | {'body': 10882} |
| 2 | tennis__Male_Emote_Thrust | 31 | coverage, elbow_R, hipabd_L | 10527 | 0 | {'body': 10527} |
| 3 | tennis__Male_Intro_Pushups | 71 | coverage, hipflex_L, hipflex_R | 7269 | 1216 | {'body': 7269, 'Kit_Bottom': 1216} |
| 4 | tennis__Male_Intro_Pushups | 10 | hipflex_L, hipflex_R, knee_L | 7298 | 603 | {'body': 7298, 'Kit_Bottom': 603} |
| 5 | tennis__Male_Emote_Scuba | 123 | hipabd_L, hipabd_R, hipflex_L | 6352 | 422 | {'body': 6352, 'Kit_Bottom': 422} |
| 6 | tennis__Male_SliceApproach | 15 | across_R, coverage, hipflex_L | 5674 | 85 | {'body': 5674, 'Kit_Bottom': 85} |
| 7 | tennis__Male_ForehandOpen | 23 | across_L, across_R, hipflex_L | 1661 | 3958 | {'body': 1661, 'Kit_Bottom': 3958} |
| 8 | tennis__Male_Emote_Shock | 16 | elbow_R, overhead | 5293 | 0 | {'body': 5293} |
| 9 | moves__Emote_Shock | 16 | elbow_R, overhead | 5286 | 0 | {'body': 5286} |
| 10 | moves__Emote_Shock | 24 | elbow_R, overhead, side_seam_L | 5145 | 0 | {'body': 5145} |
| 11 | tennis__Male_Emote_Shock | 24 | elbow_R, overhead, side_seam_L | 5138 | 0 | {'body': 5138} |
