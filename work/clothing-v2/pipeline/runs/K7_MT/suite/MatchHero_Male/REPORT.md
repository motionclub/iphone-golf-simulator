# Garment stress report: MatchHero_Male

Stress poses: 153 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 144109 skin pixels through cloth, in 108 poses
- GATE LAYERS: FAIL - 8530 garment pixels through an outer garment, in 36 poses
- by victim: {'body': 144109, 'Kit_Bottom': 8433, 'Kit_Sock_R': 97}
- by victim<coverer: {'body<Kit_Top': 139343, 'Kit_Bottom<Kit_Top': 8433, 'body<Kit_Bottom': 2032, 'body<Kit_Shoe_L': 1154, 'body<Kit_Sock_R': 901, 'body<Kit_Shoe_R': 407, 'body<Kit_Sock_L': 272, 'Kit_Sock_R<Kit_Shoe_R': 97}
- HOLES (hidden skin seen through): 48321 px in 153 poses
  - holes split: background 559, lining 30767, outer surface > 3 cm behind 16995

Before: tear 342039 px (103 poses), layer 52961 px (104 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Male_Intro_Pushups | 79 | hipflex_L, hipflex_R, knee_R | 10146 | 8 | {'Kit_Bottom': 8, 'body': 10146} |
| 1 | tennis__Male_Intro_Pushups | 71 | coverage, hipflex_L, hipflex_R | 7042 | 1233 | {'Kit_Bottom': 1215, 'body': 7042, 'Kit_Sock_R': 18} |
| 2 | tennis__Male_Intro_Pushups | 10 | hipflex_L, hipflex_R, knee_L | 7091 | 101 | {'body': 7091, 'Kit_Bottom': 85, 'Kit_Sock_R': 16} |
| 3 | tennis__Male_Emote_Scuba | 123 | hipabd_L, hipabd_R, hipflex_L | 5936 | 100 | {'body': 5936, 'Kit_Bottom': 92, 'Kit_Sock_R': 8} |
| 4 | tennis__Male_Emote_Shock | 16 | elbow_R, overhead | 5206 | 0 | {'body': 5206} |
| 5 | moves__Emote_Shock | 16 | elbow_R, overhead | 5201 | 0 | {'body': 5201} |
| 6 | tennis__Male_Emote_Thrust | 47 | elbow_L, elbow_R, hipabd_L | 5081 | 0 | {'body': 5081} |
| 7 | moves__Emote_Shock | 24 | elbow_R, overhead, side_seam_L | 5063 | 0 | {'body': 5063} |
| 8 | tennis__Male_Emote_Shock | 24 | elbow_R, overhead, side_seam_L | 5061 | 0 | {'body': 5061} |
| 9 | moves__Emote_Shock | 8 | elbow_L, elbow_R, overhead | 4975 | 0 | {'body': 4975} |
| 10 | moves__Emote_Shock | 32 | elbow_R, overhead | 4939 | 0 | {'body': 4939} |
| 11 | tennis__Male_Emote_Shock | 38 | elbow_L, elbow_R, overhead | 4912 | 0 | {'body': 4912} |
