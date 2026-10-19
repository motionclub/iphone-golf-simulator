# Garment stress report: MatchHero_Male

Stress poses: 153 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 145019 skin pixels through cloth, in 124 poses
- GATE LAYERS: FAIL - 27467 garment pixels through an outer garment, in 115 poses
- by victim: {'Kit_Bottom': 25045, 'body': 145019, 'Kit_Sock_L': 1114, 'Kit_Sock_R': 871, 'Kit_Shoe_R': 204, 'Kit_Shoe_L': 233}
- by victim<coverer: {'body<Kit_Top': 144881, 'Kit_Bottom<Kit_Top': 25045, 'Kit_Sock_L<Kit_Shoe_L': 1114, 'Kit_Sock_R<Kit_Shoe_R': 871, 'Kit_Shoe_L<Kit_Sock_L': 233, 'Kit_Shoe_R<Kit_Sock_R': 204, 'body<Kit_Shoe_L': 80, 'body<Kit_Shoe_R': 58}
- HOLES (hidden skin seen through): 193257 px in 153 poses

Before: tear 342039 px (103 poses), layer 52961 px (104 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Male_Intro_Pushups | 79 | hipflex_L, hipflex_R, knee_R | 9669 | 25 | {'body': 9669, 'Kit_Sock_L': 15, 'Kit_Sock_R': 10} |
| 1 | tennis__Male_Intro_Pushups | 71 | coverage, hipflex_L, hipflex_R | 8358 | 372 | {'body': 8358, 'Kit_Bottom': 344, 'Kit_Sock_L': 20, 'Kit_Shoe_R': 8} |
| 2 | tennis__Male_Intro_Pushups | 10 | hipflex_L, hipflex_R, knee_L | 8154 | 33 | {'body': 8154, 'Kit_Sock_L': 15, 'Kit_Shoe_R': 8, 'Kit_Bottom': 10} |
| 3 | tennis__Male_Emote_Scuba | 123 | hipabd_L, hipabd_R, hipflex_L | 6979 | 243 | {'body': 6979, 'Kit_Sock_L': 35, 'Kit_Bottom': 208} |
| 4 | tennis__Male_Emote_Thrust | 47 | elbow_L, elbow_R, hipabd_L | 6375 | 145 | {'body': 6375, 'Kit_Sock_L': 38, 'Kit_Sock_R': 38, 'Kit_Bottom': 69} |
| 5 | tennis__Male_Emote_Thrust | 31 | coverage, elbow_R, hipabd_L | 6195 | 149 | {'body': 6195, 'Kit_Sock_L': 34, 'Kit_Sock_R': 46, 'Kit_Bottom': 69} |
| 6 | tennis__Male_SliceApproach | 15 | across_R, coverage, hipflex_L | 5153 | 52 | {'body': 5153, 'Kit_Bottom': 52} |
| 7 | tennis__Male_Emote_Shock | 16 | elbow_R, overhead | 4422 | 554 | {'body': 4422, 'Kit_Bottom': 554} |
| 8 | moves__Emote_Shock | 16 | elbow_R, overhead | 4422 | 547 | {'body': 4422, 'Kit_Bottom': 547} |
| 9 | moves__Emote_Shock | 24 | elbow_R, overhead, side_seam_L | 4345 | 549 | {'body': 4345, 'Kit_Bottom': 549} |
| 10 | tennis__Male_Emote_Shock | 24 | elbow_R, overhead, side_seam_L | 4343 | 549 | {'body': 4343, 'Kit_Bottom': 549} |
| 11 | moves__Emote_Shock | 32 | elbow_R, overhead | 4162 | 592 | {'body': 4162, 'Kit_Bottom': 592} |
