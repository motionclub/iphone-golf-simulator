# Garment stress report: MatchHero_Male

Stress poses: 153 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 186095 skin pixels through cloth, in 136 poses
- GATE LAYERS: FAIL - 63171 garment pixels through an outer garment, in 51 poses
- by victim: {'body': 186095, 'Kit_Bottom': 63088, 'Kit_Shoe_R': 83}
- by victim<coverer: {'body<Kit_Top': 182662, 'Kit_Bottom<Kit_Top': 63088, 'body<Kit_Bottom': 3414, 'Kit_Shoe_R<Kit_Sock_R': 83, 'body<Kit_Shoe_L': 10, 'body<Kit_Shoe_R': 9}
- HOLES (hidden skin seen through): 32957 px in 152 poses

Before: tear 342039 px (103 poses), layer 52961 px (104 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Male_Intro_Pushups | 79 | hipflex_L, hipflex_R, knee_R | 9900 | 5 | {'body': 9900, 'Kit_Bottom': 5} |
| 1 | tennis__Male_Intro_Pushups | 71 | coverage, hipflex_L, hipflex_R | 7577 | 1343 | {'body': 7577, 'Kit_Bottom': 1343} |
| 2 | tennis__Male_Intro_Pushups | 10 | hipflex_L, hipflex_R, knee_L | 7374 | 749 | {'body': 7374, 'Kit_Bottom': 749} |
| 3 | tennis__Male_Emote_Thrust | 47 | elbow_L, elbow_R, hipabd_L | 6896 | 84 | {'body': 6896, 'Kit_Bottom': 84} |
| 4 | tennis__Male_Emote_Thrust | 31 | coverage, elbow_R, hipabd_L | 6720 | 100 | {'body': 6720, 'Kit_Bottom': 100} |
| 5 | tennis__Male_Emote_Scuba | 123 | hipabd_L, hipabd_R, hipflex_L | 6238 | 42 | {'body': 6238, 'Kit_Bottom': 42} |
| 6 | tennis__Male_Emote_Shock | 16 | elbow_R, overhead | 5211 | 0 | {'body': 5211} |
| 7 | moves__Emote_Shock | 16 | elbow_R, overhead | 5209 | 0 | {'body': 5209} |
| 8 | moves__Emote_Shock | 24 | elbow_R, overhead, side_seam_L | 5020 | 0 | {'body': 5020} |
| 9 | tennis__Male_Emote_Shock | 24 | elbow_R, overhead, side_seam_L | 5013 | 0 | {'body': 5013} |
| 10 | moves__Emote_Shock | 32 | elbow_R, overhead | 4992 | 0 | {'body': 4992} |
| 11 | moves__Emote_Shock | 8 | elbow_L, elbow_R, overhead | 4986 | 0 | {'body': 4986} |
