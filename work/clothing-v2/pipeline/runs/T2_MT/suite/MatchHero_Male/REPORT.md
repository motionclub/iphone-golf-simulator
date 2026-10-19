# Garment stress report: MatchHero_Male

Stress poses: 40 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 133155 skin pixels through cloth, in 40 poses
- GATE LAYERS: FAIL - 2399 garment pixels through an outer garment, in 5 poses
- by victim: {'body': 133155, 'Kit_Bottom': 2357, 'Kit_Sock_R': 42}
- by victim<coverer: {'body<Kit_Top': 130881, 'Kit_Bottom<Kit_Top': 2357, 'body<Kit_Bottom': 1220, 'body<Kit_Sock_R': 597, 'body<Kit_Shoe_L': 353, 'body<Kit_Sock_L': 53, 'body<Kit_Shoe_R': 51, 'Kit_Sock_R<Kit_Shoe_R': 42}
- HOLES (hidden skin seen through): 12914 px in 40 poses
  - holes split: background 11, lining 7415, outer surface > 3 cm behind 5488

Before: tear 141589 px (105 poses), layer 1771 px (22 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Male_Intro_Pushups | 79 | hipflex_L, hipflex_R, knee_R | 9330 | 0 | {'body': 9330} |
| 1 | tennis__Male_Intro_Pushups | 71 | coverage, hipflex_L, hipflex_R | 8131 | 565 | {'body': 8131, 'Kit_Bottom': 547, 'Kit_Sock_R': 18} |
| 2 | tennis__Male_Intro_Pushups | 10 | hipflex_L, hipflex_R, knee_L | 7954 | 69 | {'body': 7954, 'Kit_Bottom': 53, 'Kit_Sock_R': 16} |
| 3 | tennis__Male_Emote_Scuba | 123 | hipabd_L, hipabd_R, hipflex_L | 5317 | 447 | {'body': 5317, 'Kit_Bottom': 439, 'Kit_Sock_R': 8} |
| 4 | tennis__Male_Emote_Shock | 16 | elbow_R, overhead | 5387 | 0 | {'body': 5387} |
| 5 | moves__Emote_Shock | 16 | elbow_R, overhead | 5386 | 0 | {'body': 5386} |
| 6 | moves__Emote_Shock | 24 | elbow_R, overhead, side_seam_L | 5219 | 0 | {'body': 5219} |
| 7 | tennis__Male_Emote_Shock | 24 | elbow_R, overhead, side_seam_L | 5214 | 0 | {'body': 5214} |
| 8 | moves__Emote_Shock | 8 | elbow_L, elbow_R, overhead | 5167 | 0 | {'body': 5167} |
| 9 | moves__Emote_Shock | 32 | elbow_R, overhead | 5103 | 0 | {'body': 5103} |
| 10 | tennis__Male_Emote_Shock | 38 | elbow_L, elbow_R, overhead | 5085 | 0 | {'body': 5085} |
| 11 | moves__Emote_Shock | 40 | elbow_L, elbow_R, overhead | 5044 | 0 | {'body': 5044} |
