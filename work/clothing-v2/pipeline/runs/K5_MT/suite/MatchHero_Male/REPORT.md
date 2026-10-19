# Garment stress report: MatchHero_Male

Stress poses: 153 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 215557 skin pixels through cloth, in 153 poses
- GATE LAYERS: FAIL - 485176 garment pixels through an outer garment, in 153 poses
- by victim: {'body': 215557, 'Kit_Bottom': 484510, 'Kit_Shoe_L': 55, 'Kit_Sock_R': 565, 'Kit_Shoe_R': 46}
- by victim<coverer: {'Kit_Bottom<Kit_Top': 484510, 'body<Kit_Top': 170122, 'body<Kit_Sock_L': 21698, 'body<Kit_Bottom': 14261, 'body<Kit_Sock_R': 9476, 'Kit_Sock_R<Kit_Shoe_R': 565, 'Kit_Shoe_L<Kit_Sock_L': 55, 'Kit_Shoe_R<Kit_Sock_R': 46}
- HOLES (hidden skin seen through): 747985 px in 153 poses

Before: tear 342039 px (103 poses), layer 52961 px (104 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Male_Emote_Shock | 16 | elbow_R, overhead | 5140 | 7345 | {'body': 5140, 'Kit_Bottom': 7345} |
| 1 | moves__Emote_Shock | 16 | elbow_R, overhead | 5136 | 7346 | {'body': 5136, 'Kit_Bottom': 7346} |
| 2 | moves__Emote_Shock | 8 | elbow_L, elbow_R, overhead | 4942 | 7409 | {'body': 4942, 'Kit_Bottom': 7409} |
| 3 | moves__Emote_Shock | 24 | elbow_R, overhead, side_seam_L | 4971 | 7370 | {'body': 4971, 'Kit_Bottom': 7370} |
| 4 | tennis__Male_Emote_Shock | 24 | elbow_R, overhead, side_seam_L | 4967 | 7373 | {'body': 4967, 'Kit_Bottom': 7373} |
| 5 | moves__Emote_Shock | 32 | elbow_R, overhead | 4916 | 7378 | {'body': 4916, 'Kit_Bottom': 7378} |
| 6 | tennis__Male_Emote_Shock | 38 | elbow_L, elbow_R, overhead | 4847 | 7375 | {'body': 4847, 'Kit_Bottom': 7375} |
| 7 | moves__Emote_Shock | 40 | elbow_L, elbow_R, overhead | 4805 | 7365 | {'body': 4805, 'Kit_Bottom': 7365} |
| 8 | tennis__Male_Serve | 33 | elbow_L, elbow_R, side_seam_L | 3421 | 8070 | {'body': 3421, 'Kit_Bottom': 8070} |
| 9 | tennis__Male_Intro_Pushups | 79 | hipflex_L, hipflex_R, knee_R | 10201 | 859 | {'body': 10201, 'Kit_Bottom': 859} |
| 10 | tennis__Male_Serve | 41 | coverage, elbow_L, elbow_R | 3165 | 7668 | {'body': 3165, 'Kit_Bottom': 7668} |
| 11 | tennis__Male_Intro_Pushups | 71 | coverage, hipflex_L, hipflex_R | 6612 | 3591 | {'Kit_Bottom': 3591, 'body': 6612} |
