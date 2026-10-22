# Garment stress report: MatchHero_Female

Stress poses: 152 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 183080 skin pixels through cloth, in 151 poses
- GATE LAYERS: FAIL - 14132 garment pixels through an outer garment, in 101 poses
- by victim: {'body': 183080, 'Kit_Bottom': 13727, 'Kit_Top': 405}
- by victim<coverer: {'body<Kit_Top': 119665, 'body<Kit_Bottom': 63415, 'Kit_Bottom<Kit_Top': 13727, 'Kit_Top<Kit_Bottom': 405}
- HOLES (hidden skin seen through): 9392 px in 112 poses

Before: tear 352507 px (152 poses), layer 13 px (1 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Female_Emote_Thrust | 93 | elbow_L, hipabd_L, hipabd_R | 5437 | 242 | {'body': 5437, 'Kit_Bottom': 234, 'Kit_Top': 8} |
| 1 | tennis__Female_Emote_Thrust | 84 | elbow_L, elbow_R, hipabd_L | 5270 | 220 | {'body': 5270, 'Kit_Bottom': 215, 'Kit_Top': 5} |
| 2 | tennis__Female_BackhandWide | 14 | hipflex_L, knee_L, kneel | 4638 | 509 | {'body': 4638, 'Kit_Bottom': 509} |
| 3 | tennis__Female_SplitToBackhand | 5 | hipabd_R, trunk_twist, waist | 4632 | 363 | {'body': 4632, 'Kit_Bottom': 363} |
| 4 | tennis__Female_Serve | 10 | elbow_L, elbow_R, hipflex_L | 4059 | 492 | {'body': 4059, 'Kit_Bottom': 492} |
| 5 | tennis__Female_Return | 7 | hipabd_R, hipflex_L, knee_L | 3860 | 424 | {'body': 3860, 'Kit_Bottom': 424} |
| 6 | tennis__Female_ForehandWide | 28 | across_R, axilla_R, coverage | 3851 | 329 | {'body': 3851, 'Kit_Bottom': 329} |
| 7 | tennis__Female_Emote_Scuba | 123 | hipabd_L, hipabd_R, hipflex_L | 4054 | 8 | {'body': 4054, 'Kit_Top': 8} |
| 8 | tennis__Female_Intro_Pushups | 71 | hipflex_L, hipflex_R, knee_L | 3785 | 0 | {'body': 3785} |
| 9 | tennis__Female_SplitToBackhand | 13 | hipabd_R, hipflex_L, hipflex_R | 3160 | 405 | {'body': 3160, 'Kit_Bottom': 405} |
| 10 | tennis__Female_Intro_Pushups | 10 | coverage, hipflex_L, hipflex_R | 3476 | 47 | {'body': 3476, 'Kit_Bottom': 3, 'Kit_Top': 44} |
| 11 | tennis__Female_ForehandArmCorrected | 26 | across_L, coverage, elbow_R | 3091 | 165 | {'body': 3091, 'Kit_Bottom': 165} |
