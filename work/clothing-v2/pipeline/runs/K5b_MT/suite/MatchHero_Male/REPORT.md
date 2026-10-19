# Garment stress report: MatchHero_Male

Stress poses: 153 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 349328 skin pixels through cloth, in 140 poses
- GATE LAYERS: FAIL - 58294 garment pixels through an outer garment, in 40 poses
- by victim: {'body': 349328, 'Kit_Bottom': 57931, 'Kit_Shoe_R': 253, 'Kit_Sock_R': 69, 'Kit_Shoe_L': 41}
- by victim<coverer: {'body<Kit_Top': 167342, 'body<Kit_Sock_L': 125678, 'Kit_Bottom<Kit_Top': 57931, 'body<Kit_Sock_R': 41795, 'body<Kit_Bottom': 14513, 'Kit_Shoe_R<Kit_Sock_R': 253, 'Kit_Sock_R<Kit_Shoe_R': 69, 'Kit_Shoe_L<Kit_Sock_L': 41}
- HOLES (hidden skin seen through): 631794 px in 153 poses
  - holes split: background 337802, lining 109702, outer surface > 3 cm behind 184290

Before: tear 341530 px (103 poses), layer 52961 px (104 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Male_Emote_Thrust | 47 | elbow_L, elbow_R, hipabd_L | 12372 | 0 | {'body': 12372} |
| 1 | tennis__Male_Emote_Thrust | 31 | coverage, elbow_R, hipabd_L | 12127 | 0 | {'body': 12127} |
| 2 | tennis__Male_Intro_Pushups | 79 | hipflex_L, hipflex_R, knee_R | 10037 | 0 | {'body': 10037} |
| 3 | tennis__Male_Intro_Pushups | 71 | coverage, hipflex_L, hipflex_R | 7888 | 1225 | {'body': 7888, 'Kit_Bottom': 1215, 'Kit_Shoe_R': 10} |
| 4 | tennis__Male_Emote_Scuba | 123 | hipabd_L, hipabd_R, hipflex_L | 8313 | 155 | {'body': 8313, 'Kit_Bottom': 150, 'Kit_Shoe_R': 5} |
| 5 | tennis__Male_Serve | 64 | coverage, elbow_L, elbow_R | 5104 | 3178 | {'body': 5104, 'Kit_Bottom': 3178} |
| 6 | tennis__Male_Intro_Pushups | 10 | hipflex_L, hipflex_R, knee_L | 7694 | 301 | {'body': 7694, 'Kit_Bottom': 296, 'Kit_Shoe_R': 5} |
| 7 | tennis__Male_SliceApproach | 15 | across_R, coverage, hipflex_L | 7981 | 0 | {'body': 7981} |
| 8 | tennis__Male_Emote_Thrust | 15 | elbow_R, hipabd_R | 6417 | 0 | {'body': 6417} |
| 9 | tennis__Male_Emote_Thrust | 78 | hipabd_R, hipflex_L, hipflex_R | 5596 | 83 | {'body': 5596, 'Kit_Bottom': 83} |
| 10 | tennis__Male_Emote_Thrust | 86 | elbow_L, elbow_R, hipabd_L | 5552 | 96 | {'body': 5552, 'Kit_Bottom': 96} |
| 11 | tennis__Male_Emote_Thrust | 94 | elbow_L, elbow_R, hipabd_R | 5620 | 0 | {'body': 5620} |
