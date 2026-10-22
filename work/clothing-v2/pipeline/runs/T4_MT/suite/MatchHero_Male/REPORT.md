# Garment stress report: MatchHero_Male

Stress poses: 40 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 68299 skin pixels through cloth, in 38 poses
- GATE LAYERS: FAIL - 2303 garment pixels through an outer garment, in 5 poses
- by victim: {'body': 68299, 'Kit_Bottom': 2261, 'Kit_Sock_R': 42}
- by victim<coverer: {'body<Kit_Top': 66025, 'Kit_Bottom<Kit_Top': 2261, 'body<Kit_Bottom': 1220, 'body<Kit_Sock_R': 597, 'body<Kit_Shoe_L': 353, 'body<Kit_Sock_L': 53, 'body<Kit_Shoe_R': 51, 'Kit_Sock_R<Kit_Shoe_R': 42}
- HOLES (hidden skin seen through): 11278 px in 40 poses
  - holes split: background 11, lining 7430, outer surface > 3 cm behind 3837

Before: tear 141589 px (105 poses), layer 1771 px (22 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Male_Intro_Pushups | 79 | hipflex_L, hipflex_R, knee_R | 8719 | 0 | {'body': 8719} |
| 1 | tennis__Male_Intro_Pushups | 71 | coverage, hipflex_L, hipflex_R | 7994 | 615 | {'body': 7994, 'Kit_Bottom': 597, 'Kit_Sock_R': 18} |
| 2 | tennis__Male_Intro_Pushups | 10 | hipflex_L, hipflex_R, knee_L | 6936 | 116 | {'body': 6936, 'Kit_Bottom': 100, 'Kit_Sock_R': 16} |
| 3 | tennis__Male_Emote_Scuba | 123 | hipabd_L, hipabd_R, hipflex_L | 4853 | 436 | {'body': 4853, 'Kit_Bottom': 428, 'Kit_Sock_R': 8} |
| 4 | tennis__Male_SliceApproach | 15 | across_R, coverage, hipflex_L | 4087 | 0 | {'body': 4087} |
| 5 | tennis__Male_Emote_Spike | 28 | elbow_R, trunk_side | 3848 | 0 | {'body': 3848} |
| 6 | tennis__Male_ForehandWide | 17 | coverage, hipflex_R, knee_L | 2573 | 0 | {'body': 2573} |
| 7 | tennis__Male_ForehandShort | 13 | armback_R, coverage, elbow_R | 1969 | 0 | {'body': 1969} |
| 8 | tennis__Male_Serve | 41 | coverage, elbow_L, elbow_R | 1837 | 0 | {'body': 1837} |
| 9 | tennis__Male_ForehandOpen | 14 | across_L, across_R, coverage | 1828 | 0 | {'body': 1828} |
| 10 | tennis__Male_Serve | 24 | axilla_L, elbow_L, elbow_R | 1799 | 0 | {'body': 1799} |
| 11 | tennis__Male_Serve | 33 | elbow_L, elbow_R, side_seam_L | 1665 | 0 | {'body': 1665} |
