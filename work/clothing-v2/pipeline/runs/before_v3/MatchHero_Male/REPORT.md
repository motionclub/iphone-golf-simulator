# Garment stress report: MatchHero_Male

Stress poses: 153 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 341530 skin pixels through cloth, in 103 poses
- GATE LAYERS: FAIL - 52961 garment pixels through an outer garment, in 104 poses
- by victim: {'Kit_Bottom': 50307, 'body': 341530, 'Kit_Sock_L': 1239, 'Kit_Sock_R': 948, 'Kit_Shoe_R': 214, 'Kit_Shoe_L': 253}
- by victim<coverer: {'body<Kit_Top': 339820, 'Kit_Bottom<Kit_Top': 50307, 'Kit_Sock_L<Kit_Shoe_L': 1239, 'Kit_Sock_R<Kit_Shoe_R': 948, 'body<Kit_Bottom': 816, 'body<Kit_Sock_R': 511, 'Kit_Shoe_L<Kit_Sock_L': 253, 'Kit_Shoe_R<Kit_Sock_R': 214, 'body<Kit_Sock_L': 194, 'body<Kit_Shoe_L': 109, 'body<Kit_Shoe_R': 80}
- HOLES (hidden skin seen through): 246986 px in 153 poses

Before: tear 342039 px (103 poses), layer 52961 px (104 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | moves__Emote_Shock | 40 | elbow_L, elbow_R, overhead | 11961 | 389 | {'body': 11961, 'Kit_Bottom': 389} |
| 1 | tennis__Male_Emote_Shock | 38 | elbow_L, elbow_R, overhead | 11935 | 396 | {'body': 11935, 'Kit_Bottom': 396} |
| 2 | moves__Emote_Shock | 32 | elbow_R, overhead | 11990 | 332 | {'body': 11990, 'Kit_Bottom': 332} |
| 3 | moves__Emote_Shock | 16 | elbow_R, overhead | 12048 | 269 | {'body': 12048, 'Kit_Bottom': 269} |
| 4 | tennis__Male_Emote_Shock | 16 | elbow_R, overhead | 12040 | 269 | {'body': 12040, 'Kit_Bottom': 269} |
| 5 | tennis__Male_Emote_Shock | 24 | elbow_R, overhead, side_seam_L | 12000 | 229 | {'body': 12000, 'Kit_Bottom': 229} |
| 6 | moves__Emote_Shock | 24 | elbow_R, overhead, side_seam_L | 11996 | 229 | {'body': 11996, 'Kit_Bottom': 229} |
| 7 | moves__Emote_Victory | 62 | axilla_L, axilla_R, elbow_R | 12001 | 0 | {'body': 12001} |
| 8 | tennis__Male_Emote_Victory | 62 | axilla_L, axilla_R, elbow_R | 11965 | 0 | {'body': 11965} |
| 9 | tennis__Male_Emote_Victory | 70 | axilla_L, axilla_R, elbow_L | 11918 | 0 | {'body': 11918} |
| 10 | tennis__Male_Serve | 33 | elbow_L, elbow_R, side_seam_L | 11595 | 317 | {'body': 11595, 'Kit_Bottom': 317} |
| 11 | moves__Emote_Victory | 70 | axilla_L, axilla_R, elbow_L | 11857 | 0 | {'body': 11857} |
