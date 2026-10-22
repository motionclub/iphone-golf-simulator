# Garment stress report: MatchHero_Female

Stress poses: 152 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 431935 skin pixels through cloth, in 152 poses
- GATE LAYERS: FAIL - 12720 garment pixels through an outer garment, in 84 poses
- by victim: {'body': 431935, 'Kit_Bottom': 12466, 'Kit_Top': 254}
- by victim<coverer: {'body<Kit_Top': 368558, 'body<Kit_Bottom': 63377, 'Kit_Bottom<Kit_Top': 12466, 'Kit_Top<Kit_Bottom': 254}
- HOLES (hidden skin seen through): 10682 px in 123 poses

Before: tear 352507 px (152 poses), layer 13 px (1 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Female_ForehandWide | 28 | across_R, axilla_R, coverage | 7380 | 329 | {'body': 7380, 'Kit_Bottom': 329} |
| 1 | tennis__Female_Intro_Pushups | 79 | hipflex_L, hipflex_R, knee_L | 7274 | 10 | {'body': 7274, 'Kit_Bottom': 10} |
| 2 | tennis__Female_ForehandShort | 11 | across_R, armback_R, coverage | 6465 | 15 | {'body': 6465, 'Kit_Bottom': 15} |
| 3 | tennis__Female_Serve | 23 | axilla_L, coverage, elbow_L | 6293 | 105 | {'body': 6293, 'Kit_Bottom': 87, 'Kit_Top': 18} |
| 4 | tennis__Female_ForehandArmCorrected | 14 | elbow_L, lunge, trunk_twist | 6297 | 28 | {'body': 6297, 'Kit_Bottom': 28} |
| 5 | tennis__Female_Serve | 32 | axilla_L, elbow_L, elbow_R | 6020 | 0 | {'body': 6020} |
| 6 | tennis__Female_Serve | 40 | axilla_L, coverage, elbow_L | 5979 | 0 | {'body': 5979} |
| 7 | tennis__Female_ForehandOpen | 23 | across_L, across_R, coverage | 5820 | 121 | {'body': 5820, 'Kit_Bottom': 121} |
| 8 | tennis__Female_Overhead | 12 | across_L, armback_R, axilla_L | 5907 | 0 | {'body': 5907} |
| 9 | tennis__Female_ForehandArmCorrected | 6 | across_R, elbow_L, elbow_R | 5848 | 52 | {'body': 5848, 'Kit_Bottom': 52} |
| 10 | tennis__Female_Emote_Shock | 40 | coverage, elbow_L, elbow_R | 5528 | 0 | {'body': 5528} |
| 11 | moves__Emote_Shock | 40 | elbow_L, elbow_R, overhead | 5509 | 0 | {'body': 5509} |
