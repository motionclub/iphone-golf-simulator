# Garment stress report: MatchHero_Female

Stress poses: 152 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 472687 skin pixels through cloth, in 152 poses
- GATE LAYERS: FAIL - 10934 garment pixels through an outer garment, in 84 poses
- by victim: {'body': 472687, 'Kit_Bottom': 10745, 'Kit_Top': 189}
- by victim<coverer: {'body<Kit_Top': 409411, 'body<Kit_Bottom': 63276, 'Kit_Bottom<Kit_Top': 10745, 'Kit_Top<Kit_Bottom': 189}
- HOLES (hidden skin seen through): 9831 px in 120 poses

Before: tear 352507 px (152 poses), layer 13 px (1 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Female_Emote_Shock | 40 | coverage, elbow_L, elbow_R | 7997 | 0 | {'body': 7997} |
| 1 | moves__Emote_Shock | 40 | elbow_L, elbow_R, overhead | 7989 | 0 | {'body': 7989} |
| 2 | tennis__Female_Overhead | 21 | armback_R, coverage, elbow_L | 7871 | 22 | {'body': 7871, 'Kit_Top': 22} |
| 3 | moves__Emote_Shock | 31 | elbow_L, elbow_R, overhead | 7873 | 0 | {'body': 7873} |
| 4 | tennis__Female_Emote_Shock | 31 | elbow_L, elbow_R, overhead | 7870 | 0 | {'body': 7870} |
| 5 | tennis__Female_Emote_Shock | 9 | coverage, elbow_L, elbow_R | 7768 | 0 | {'body': 7768} |
| 6 | moves__Emote_Shock | 9 | elbow_L, elbow_R | 7765 | 0 | {'body': 7765} |
| 7 | tennis__Female_Emote_Shock | 17 | elbow_L, elbow_R, overhead | 7656 | 0 | {'body': 7656} |
| 8 | moves__Emote_Shock | 17 | elbow_L, elbow_R, overhead | 7656 | 0 | {'body': 7656} |
| 9 | tennis__Female_ForehandShort | 11 | across_R, armback_R, coverage | 7409 | 50 | {'body': 7409, 'Kit_Bottom': 50} |
| 10 | tennis__Female_ForehandWide | 28 | across_R, axilla_R, coverage | 6400 | 557 | {'body': 6400, 'Kit_Bottom': 528, 'Kit_Top': 29} |
| 11 | tennis__Female_Serve | 40 | axilla_L, coverage, elbow_L | 6825 | 18 | {'body': 6825, 'Kit_Top': 18} |
