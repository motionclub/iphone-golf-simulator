# Garment stress report: MatchHero_Male

Stress poses: 153 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 141589 skin pixels through cloth, in 105 poses
- GATE LAYERS: FAIL - 1771 garment pixels through an outer garment, in 22 poses
- by victim: {'body': 141589, 'Kit_Bottom': 1674, 'Kit_Sock_R': 97}
- by victim<coverer: {'body<Kit_Top': 136823, 'body<Kit_Bottom': 2032, 'Kit_Bottom<Kit_Top': 1674, 'body<Kit_Shoe_L': 1154, 'body<Kit_Sock_R': 901, 'body<Kit_Shoe_R': 407, 'body<Kit_Sock_L': 272, 'Kit_Sock_R<Kit_Shoe_R': 97}
- HOLES (hidden skin seen through): 47998 px in 153 poses
  - holes split: background 559, lining 30172, outer surface > 3 cm behind 17267

Before: tear 342039 px (103 poses), layer 52961 px (104 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Male_Intro_Pushups | 79 | hipflex_L, hipflex_R, knee_R | 9439 | 0 | {'body': 9439} |
| 1 | tennis__Male_Intro_Pushups | 71 | coverage, hipflex_L, hipflex_R | 7393 | 87 | {'Kit_Bottom': 69, 'body': 7393, 'Kit_Sock_R': 18} |
| 2 | tennis__Male_Intro_Pushups | 10 | hipflex_L, hipflex_R, knee_L | 7083 | 37 | {'body': 7083, 'Kit_Bottom': 21, 'Kit_Sock_R': 16} |
| 3 | tennis__Male_Emote_Scuba | 123 | hipabd_L, hipabd_R, hipflex_L | 6036 | 480 | {'body': 6036, 'Kit_Bottom': 472, 'Kit_Sock_R': 8} |
| 4 | tennis__Male_Emote_Shock | 16 | elbow_R, overhead | 5201 | 0 | {'body': 5201} |
| 5 | moves__Emote_Shock | 16 | elbow_R, overhead | 5199 | 0 | {'body': 5199} |
| 6 | moves__Emote_Shock | 24 | elbow_R, overhead, side_seam_L | 5053 | 0 | {'body': 5053} |
| 7 | tennis__Male_Emote_Shock | 24 | elbow_R, overhead, side_seam_L | 5048 | 0 | {'body': 5048} |
| 8 | moves__Emote_Shock | 8 | elbow_L, elbow_R, overhead | 4971 | 0 | {'body': 4971} |
| 9 | moves__Emote_Shock | 32 | elbow_R, overhead | 4923 | 0 | {'body': 4923} |
| 10 | tennis__Male_Emote_Shock | 38 | elbow_L, elbow_R, overhead | 4907 | 0 | {'body': 4907} |
| 11 | moves__Emote_Shock | 40 | elbow_L, elbow_R, overhead | 4885 | 0 | {'body': 4885} |
