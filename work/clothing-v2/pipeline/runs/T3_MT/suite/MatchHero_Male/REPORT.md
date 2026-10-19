# Garment stress report: MatchHero_Male

Stress poses: 40 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 131235 skin pixels through cloth, in 40 poses
- GATE LAYERS: FAIL - 1637 garment pixels through an outer garment, in 6 poses
- by victim: {'body': 131235, 'Kit_Bottom': 1595, 'Kit_Sock_R': 42}
- by victim<coverer: {'body<Kit_Top': 128961, 'Kit_Bottom<Kit_Top': 1595, 'body<Kit_Bottom': 1220, 'body<Kit_Sock_R': 597, 'body<Kit_Shoe_L': 353, 'body<Kit_Sock_L': 53, 'body<Kit_Shoe_R': 51, 'Kit_Sock_R<Kit_Shoe_R': 42}
- HOLES (hidden skin seen through): 13008 px in 40 poses
  - holes split: background 11, lining 7434, outer surface > 3 cm behind 5563

Before: tear 141589 px (105 poses), layer 1771 px (22 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Male_Intro_Pushups | 79 | hipflex_L, hipflex_R, knee_R | 8606 | 0 | {'body': 8606} |
| 1 | tennis__Male_Intro_Pushups | 71 | coverage, hipflex_L, hipflex_R | 7890 | 168 | {'Kit_Bottom': 150, 'body': 7890, 'Kit_Sock_R': 18} |
| 2 | tennis__Male_Intro_Pushups | 10 | hipflex_L, hipflex_R, knee_L | 7445 | 34 | {'body': 7445, 'Kit_Bottom': 18, 'Kit_Sock_R': 16} |
| 3 | tennis__Male_Emote_Scuba | 123 | hipabd_L, hipabd_R, hipflex_L | 5564 | 273 | {'body': 5564, 'Kit_Bottom': 265, 'Kit_Sock_R': 8} |
| 4 | tennis__Male_Emote_Shock | 16 | elbow_R, overhead | 5201 | 0 | {'body': 5201} |
| 5 | moves__Emote_Shock | 16 | elbow_R, overhead | 5199 | 0 | {'body': 5199} |
| 6 | moves__Emote_Shock | 24 | elbow_R, overhead, side_seam_L | 5053 | 0 | {'body': 5053} |
| 7 | tennis__Male_Emote_Shock | 24 | elbow_R, overhead, side_seam_L | 5048 | 0 | {'body': 5048} |
| 8 | moves__Emote_Shock | 8 | elbow_L, elbow_R, overhead | 4971 | 0 | {'body': 4971} |
| 9 | moves__Emote_Shock | 32 | elbow_R, overhead | 4923 | 0 | {'body': 4923} |
| 10 | tennis__Male_Emote_Shock | 38 | elbow_L, elbow_R, overhead | 4907 | 0 | {'body': 4907} |
| 11 | moves__Emote_Shock | 40 | elbow_L, elbow_R, overhead | 4885 | 0 | {'body': 4885} |
