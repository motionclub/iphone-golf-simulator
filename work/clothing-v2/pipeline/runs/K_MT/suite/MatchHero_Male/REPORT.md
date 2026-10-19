# Garment stress report: MatchHero_Male

Stress poses: 153 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 198228 skin pixels through cloth, in 139 poses
- GATE LAYERS: FAIL - 73304 garment pixels through an outer garment, in 54 poses
- by victim: {'body': 198228, 'Kit_Bottom': 73226, 'Kit_Shoe_R': 78}
- by victim<coverer: {'body<Kit_Top': 194096, 'Kit_Bottom<Kit_Top': 73226, 'body<Kit_Bottom': 4118, 'Kit_Shoe_R<Kit_Sock_R': 78, 'body<Kit_Shoe_R': 9, 'body<Kit_Shoe_L': 5}
- HOLES (hidden skin seen through): 30524 px in 152 poses

Before: tear 342039 px (103 poses), layer 52961 px (104 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Male_Emote_Thrust | 47 | elbow_L, elbow_R, hipabd_L | 11018 | 84 | {'body': 11018, 'Kit_Bottom': 84} |
| 1 | tennis__Male_Emote_Thrust | 31 | coverage, elbow_R, hipabd_L | 10598 | 100 | {'body': 10598, 'Kit_Bottom': 100} |
| 2 | tennis__Male_Intro_Pushups | 79 | hipflex_L, hipflex_R, knee_R | 10678 | 0 | {'body': 10678} |
| 3 | tennis__Male_Intro_Pushups | 71 | coverage, hipflex_L, hipflex_R | 7646 | 1216 | {'body': 7646, 'Kit_Bottom': 1216} |
| 4 | tennis__Male_Intro_Pushups | 10 | hipflex_L, hipflex_R, knee_L | 7373 | 603 | {'body': 7373, 'Kit_Bottom': 603} |
| 5 | tennis__Male_Emote_Scuba | 123 | hipabd_L, hipabd_R, hipflex_L | 6248 | 47 | {'body': 6248, 'Kit_Bottom': 47} |
| 6 | tennis__Male_SliceApproach | 15 | across_R, coverage, hipflex_L | 5669 | 0 | {'body': 5669} |
| 7 | tennis__Male_Emote_Shock | 16 | elbow_R, overhead | 5293 | 0 | {'body': 5293} |
| 8 | moves__Emote_Shock | 16 | elbow_R, overhead | 5286 | 0 | {'body': 5286} |
| 9 | moves__Emote_Shock | 24 | elbow_R, overhead, side_seam_L | 5146 | 0 | {'body': 5146} |
| 10 | tennis__Male_Emote_Shock | 24 | elbow_R, overhead, side_seam_L | 5139 | 0 | {'body': 5139} |
| 11 | moves__Emote_Shock | 8 | elbow_L, elbow_R, overhead | 5057 | 0 | {'body': 5057} |
