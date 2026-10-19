# Garment stress report: MatchHero_Male

Stress poses: 153 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 142164 skin pixels through cloth, in 108 poses
- GATE LAYERS: FAIL - 431164 garment pixels through an outer garment, in 141 poses
- by victim: {'Kit_Bottom': 431067, 'body': 142164, 'Kit_Sock_R': 97}
- by victim<coverer: {'Kit_Bottom<Kit_Top': 431067, 'body<Kit_Top': 139414, 'body<Kit_Shoe_L': 1154, 'body<Kit_Sock_R': 901, 'body<Kit_Shoe_R': 407, 'body<Kit_Sock_L': 272, 'Kit_Sock_R<Kit_Shoe_R': 97, 'body<Kit_Bottom': 16}
- HOLES (hidden skin seen through): 47545 px in 153 poses
  - holes split: background 559, lining 30707, outer surface > 3 cm behind 16279

Before: tear 342039 px (103 poses), layer 52961 px (104 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Male_Intro_Pushups | 79 | hipflex_L, hipflex_R, knee_R | 10146 | 5795 | {'Kit_Bottom': 5795, 'body': 10146} |
| 1 | tennis__Male_Intro_Pushups | 71 | coverage, hipflex_L, hipflex_R | 7097 | 4558 | {'body': 7097, 'Kit_Bottom': 4540, 'Kit_Sock_R': 18} |
| 2 | tennis__Male_Intro_Pushups | 10 | hipflex_L, hipflex_R, knee_L | 7104 | 4008 | {'body': 7104, 'Kit_Bottom': 3992, 'Kit_Sock_R': 16} |
| 3 | tennis__Male_Emote_Victory | 11 | armback_R, elbow_R, hipflex_R | 0 | 10326 | {'Kit_Bottom': 10326} |
| 4 | moves__Emote_Victory | 11 | armback_R, elbow_R, hipflex_R | 0 | 10304 | {'Kit_Bottom': 10304} |
| 5 | tennis__Male_Emote_JumpJoy | 9 | hipflex_R, kneel | 0 | 9961 | {'Kit_Bottom': 9961} |
| 6 | moves__Emote_JumpJoy | 9 | hipflex_R, kneel | 0 | 9948 | {'Kit_Bottom': 9948} |
| 7 | tennis__Male_SliceApproach | 15 | across_R, coverage, hipflex_L | 4572 | 5131 | {'body': 4572, 'Kit_Bottom': 5131} |
| 8 | tennis__Male_ForehandWide | 9 | hipflex_R, kneel | 0 | 8518 | {'Kit_Bottom': 8518} |
| 9 | tennis__Male_SliceApproach | 30 | across_R, coverage, hipflex_L | 1507 | 6842 | {'body': 1507, 'Kit_Bottom': 6842} |
| 10 | tennis__Male_Emote_Scuba | 123 | hipabd_L, hipabd_R, hipflex_L | 5767 | 2529 | {'body': 5767, 'Kit_Bottom': 2521, 'Kit_Sock_R': 8} |
| 11 | tennis__Male_Emote_Victory | 23 | kneel | 0 | 8184 | {'Kit_Bottom': 8184} |
