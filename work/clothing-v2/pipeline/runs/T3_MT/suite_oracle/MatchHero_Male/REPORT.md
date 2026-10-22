# Garment stress report: MatchHero_Male

Stress poses: 40 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 132658 skin pixels through cloth, in 40 poses
- GATE LAYERS: FAIL - 2073 garment pixels through an outer garment, in 8 poses
- by victim: {'body': 132658, 'Kit_Bottom': 2031, 'Kit_Sock_R': 42}
- by victim<coverer: {'body<Kit_Top': 130384, 'Kit_Bottom<Kit_Top': 2031, 'body<Kit_Bottom': 1220, 'body<Kit_Sock_R': 597, 'body<Kit_Shoe_L': 353, 'body<Kit_Sock_L': 53, 'body<Kit_Shoe_R': 51, 'Kit_Sock_R<Kit_Shoe_R': 42}
- HOLES (hidden skin seen through): 12866 px in 40 poses
  - holes split: background 11, lining 7482, outer surface > 3 cm behind 5373

Before: tear 141589 px (105 poses), layer 1771 px (22 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Male_Intro_Pushups | 79 | hipflex_L, hipflex_R, knee_R | 8615 | 0 | {'body': 8615} |
| 1 | tennis__Male_Intro_Pushups | 71 | coverage, hipflex_L, hipflex_R | 7844 | 151 | {'Kit_Bottom': 133, 'body': 7844, 'Kit_Sock_R': 18} |
| 2 | tennis__Male_Intro_Pushups | 10 | hipflex_L, hipflex_R, knee_L | 7398 | 26 | {'body': 7398, 'Kit_Bottom': 10, 'Kit_Sock_R': 16} |
| 3 | tennis__Male_Emote_Scuba | 123 | hipabd_L, hipabd_R, hipflex_L | 6025 | 404 | {'body': 6025, 'Kit_Bottom': 396, 'Kit_Sock_R': 8} |
| 4 | tennis__Male_Emote_Shock | 16 | elbow_R, overhead | 5204 | 0 | {'body': 5204} |
| 5 | moves__Emote_Shock | 16 | elbow_R, overhead | 5200 | 0 | {'body': 5200} |
| 6 | tennis__Male_Emote_Thrust | 47 | elbow_L, elbow_R, hipabd_L | 5060 | 0 | {'body': 5060} |
| 7 | moves__Emote_Shock | 24 | elbow_R, overhead, side_seam_L | 5055 | 0 | {'body': 5055} |
| 8 | tennis__Male_Emote_Shock | 24 | elbow_R, overhead, side_seam_L | 5048 | 0 | {'body': 5048} |
| 9 | moves__Emote_Shock | 8 | elbow_L, elbow_R, overhead | 4973 | 0 | {'body': 4973} |
| 10 | moves__Emote_Shock | 32 | elbow_R, overhead | 4923 | 0 | {'body': 4923} |
| 11 | tennis__Male_Emote_Shock | 38 | elbow_L, elbow_R, overhead | 4907 | 0 | {'body': 4907} |
