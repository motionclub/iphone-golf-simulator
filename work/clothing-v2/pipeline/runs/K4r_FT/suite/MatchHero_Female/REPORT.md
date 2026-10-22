# Garment stress report: MatchHero_Female

Stress poses: 152 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 115714 skin pixels through cloth, in 146 poses
- GATE LAYERS: FAIL - 1601 garment pixels through an outer garment, in 35 poses
- by victim: {'body': 115714, 'Kit_Bottom': 1129, 'Kit_Top': 472}
- by victim<coverer: {'body<Kit_Top': 112245, 'body<Kit_Bottom': 3469, 'Kit_Bottom<Kit_Top': 1129, 'Kit_Top<Kit_Bottom': 472}
- HOLES (hidden skin seen through): 9453 px in 112 poses

Before: tear 352507 px (152 poses), layer 13 px (1 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Female_Intro_Pushups | 79 | hipflex_L, hipflex_R, knee_L | 3178 | 7 | {'body': 3178, 'Kit_Top': 7} |
| 1 | moves__Emote_Victory | 77 | elbow_R | 2703 | 0 | {'body': 2703} |
| 2 | tennis__Female_Emote_Victory | 77 | elbow_R | 2685 | 0 | {'body': 2685} |
| 3 | tennis__Female_SplitToBackhand | 13 | hipabd_R, hipflex_L, hipflex_R | 2261 | 108 | {'body': 2261, 'Kit_Bottom': 108} |
| 4 | moves__Emote_Victory | 33 | elbow_L | 2051 | 0 | {'body': 2051} |
| 5 | moves__Emote_Defeat | 49 | knee_L, knee_R, kneel | 1937 | 0 | {'body': 1937} |
| 6 | tennis__Female_Emote_Defeat | 49 | knee_L, knee_R, kneel | 1933 | 0 | {'body': 1933} |
| 7 | tennis__Female_Emote_Defeat | 57 | knee_L, knee_R, kneel | 1908 | 0 | {'body': 1908} |
| 8 | moves__Emote_Defeat | 57 | knee_L, knee_R, kneel | 1905 | 0 | {'body': 1905} |
| 9 | moves__Emote_Stomp | 10 | elbow_L, hipflex_R, knee_R | 1894 | 0 | {'body': 1894} |
| 10 | tennis__Female_Emote_Stomp | 10 | coverage, elbow_L, hipflex_R | 1866 | 0 | {'body': 1866} |
| 11 | tennis__Female_Emote_Scuba | 131 | hipabd_R, hipflex_L, hipflex_R | 1864 | 0 | {'body': 1864} |
