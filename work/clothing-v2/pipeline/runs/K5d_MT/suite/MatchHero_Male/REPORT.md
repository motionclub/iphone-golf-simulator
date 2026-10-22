# Garment stress report: MatchHero_Male

Stress poses: 153 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 224897 skin pixels through cloth, in 136 poses
- GATE LAYERS: FAIL - 59694 garment pixels through an outer garment, in 50 poses
- by victim: {'body': 224897, 'Kit_Bottom': 57931, 'Kit_Shoe_R': 1704, 'Kit_Shoe_L': 54, 'Kit_Sock_R': 5}
- by victim<coverer: {'body<Kit_Top': 167342, 'Kit_Bottom<Kit_Top': 57931, 'body<Kit_Sock_L': 41780, 'body<Kit_Bottom': 14513, 'Kit_Shoe_R<Kit_Sock_R': 1704, 'body<Kit_Sock_R': 1262, 'Kit_Shoe_L<Kit_Sock_L': 54, 'Kit_Sock_R<Kit_Shoe_R': 5}
- HOLES (hidden skin seen through): 613057 px in 153 poses
  - holes split: background 333153, lining 107637, outer surface > 3 cm behind 172267

Before: tear 342039 px (103 poses), layer 52961 px (104 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Male_Intro_Pushups | 71 | coverage, hipflex_L, hipflex_R | 10277 | 1297 | {'body': 10277, 'Kit_Shoe_R': 82, 'Kit_Bottom': 1215} |
| 1 | tennis__Male_Emote_Scuba | 123 | hipabd_L, hipabd_R, hipflex_L | 10312 | 388 | {'body': 10312, 'Kit_Shoe_R': 238, 'Kit_Bottom': 150} |
| 2 | tennis__Male_Intro_Pushups | 10 | hipflex_L, hipflex_R, knee_L | 10165 | 380 | {'body': 10165, 'Kit_Shoe_R': 84, 'Kit_Bottom': 296} |
| 3 | tennis__Male_Intro_Pushups | 79 | hipflex_L, hipflex_R, knee_R | 10037 | 25 | {'body': 10037, 'Kit_Shoe_R': 25} |
| 4 | tennis__Male_Emote_Thrust | 47 | elbow_L, elbow_R, hipabd_L | 6837 | 28 | {'body': 6837, 'Kit_Shoe_R': 28} |
| 5 | tennis__Male_Emote_Thrust | 31 | coverage, elbow_R, hipabd_L | 6585 | 26 | {'body': 6585, 'Kit_Shoe_R': 26} |
| 6 | tennis__Male_Emote_Defeat | 49 | knee_L, knee_R, kneel | 2284 | 3903 | {'body': 2284, 'Kit_Bottom': 3903} |
| 7 | moves__Emote_Defeat | 49 | knee_L, knee_R, kneel | 2286 | 3898 | {'body': 2286, 'Kit_Bottom': 3898} |
| 8 | tennis__Male_Emote_Defeat | 57 | knee_R, kneel | 2225 | 3831 | {'body': 2225, 'Kit_Bottom': 3831} |
| 9 | tennis__Male_Emote_Shock | 16 | elbow_R, overhead | 5239 | 0 | {'body': 5239} |
| 10 | moves__Emote_Shock | 16 | elbow_R, overhead | 5230 | 0 | {'body': 5230} |
| 11 | moves__Emote_Shock | 24 | elbow_R, overhead, side_seam_L | 5083 | 0 | {'body': 5083} |
