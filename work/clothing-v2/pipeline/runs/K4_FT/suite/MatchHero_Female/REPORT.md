# Garment stress report: MatchHero_Female

Stress poses: 152 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 135934 skin pixels through cloth, in 151 poses
- GATE LAYERS: FAIL - 2011 garment pixels through an outer garment, in 34 poses
- by victim: {'body': 135934, 'Kit_Bottom': 1683, 'Kit_Top': 328}
- by victim<coverer: {'body<Kit_Top': 131995, 'body<Kit_Bottom': 3939, 'Kit_Bottom<Kit_Top': 1683, 'Kit_Top<Kit_Bottom': 328}
- HOLES (hidden skin seen through): 9392 px in 112 poses

Before: tear 352507 px (152 poses), layer 13 px (1 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Female_SliceApproach | 13 | across_R, coverage, hipflex_L | 4003 | 8 | {'body': 4003, 'Kit_Top': 8} |
| 1 | tennis__Female_Intro_Pushups | 79 | hipflex_L, hipflex_R, knee_L | 3481 | 0 | {'body': 3481} |
| 2 | tennis__Female_Emote_Thrust | 47 | hipabd_L, hipabd_R | 2872 | 10 | {'body': 2872, 'Kit_Top': 10} |
| 3 | tennis__Female_SliceApproach | 31 | across_R, coverage, elbow_L | 2797 | 0 | {'body': 2797} |
| 4 | tennis__Female_Emote_Thrust | 31 | hipabd_L, hipabd_R | 2773 | 8 | {'body': 2773, 'Kit_Top': 8} |
| 5 | tennis__Female_Overhead | 12 | across_L, armback_R, axilla_L | 2646 | 0 | {'body': 2646} |
| 6 | tennis__Female_Intro_Wave | 39 | elbow_R, trunk_side | 2580 | 0 | {'body': 2580} |
| 7 | tennis__Female_ForehandArmCorrected | 6 | across_R, elbow_L, elbow_R | 2518 | 0 | {'body': 2518} |
| 8 | tennis__Female_ForehandWide | 17 | coverage, elbow_R, hipflex_R | 2458 | 0 | {'body': 2458} |
| 9 | tennis__Female_Intro_Wave | 26 | elbow_R | 2437 | 0 | {'body': 2437} |
| 10 | tennis__Female_SplitToForehand | 5 | elbow_L, elbow_R, hipabd_L | 2115 | 0 | {'body': 2115} |
| 11 | tennis__Female_SplitToBackhand | 5 | hipabd_R, trunk_twist, waist | 2083 | 0 | {'body': 2083} |
