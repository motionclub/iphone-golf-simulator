# Garment stress report: MatchHero_Female

Stress poses: 152 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 117657 skin pixels through cloth, in 144 poses
- GATE LAYERS: FAIL - 5259 garment pixels through an outer garment, in 38 poses
- by victim: {'body': 117657, 'Kit_Bottom': 4253, 'Kit_Top': 1006}
- by victim<coverer: {'body<Kit_Top': 108257, 'body<Kit_Bottom': 9400, 'Kit_Bottom<Kit_Top': 4253, 'Kit_Top<Kit_Bottom': 1006}
- HOLES (hidden skin seen through): 9454 px in 133 poses
  - holes split: background 7428, lining 1699, outer surface > 3 cm behind 327

Before: tear 352507 px (152 poses), layer 13 px (1 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | moves__Emote_Victory | 77 | elbow_R | 2758 | 0 | {'body': 2758} |
| 1 | tennis__Female_Emote_Victory | 77 | elbow_R | 2742 | 0 | {'body': 2742} |
| 2 | tennis__Female_Emote_Spike | 39 | coverage, elbow_R, hipflex_L | 2362 | 221 | {'body': 2362, 'Kit_Bottom': 173, 'Kit_Top': 48} |
| 3 | moves__Emote_Victory | 33 | elbow_L | 2512 | 0 | {'body': 2512} |
| 4 | tennis__Female_Emote_Spike | 66 | hipflex_L, hipflex_R, kneel | 2248 | 246 | {'body': 2248, 'Kit_Bottom': 207, 'Kit_Top': 39} |
| 5 | tennis__Female_Emote_Spike | 58 | hipflex_L, hipflex_R, kneel | 2271 | 217 | {'body': 2271, 'Kit_Bottom': 165, 'Kit_Top': 52} |
| 6 | tennis__Female_Emote_Spike | 47 | hipflex_L, hipflex_R, kneel | 2147 | 238 | {'body': 2147, 'Kit_Bottom': 207, 'Kit_Top': 31} |
| 7 | tennis__Female_Emote_Scuba | 123 | hipabd_L, hipabd_R, hipflex_L | 1897 | 354 | {'body': 1897, 'Kit_Top': 265, 'Kit_Bottom': 89} |
| 8 | tennis__Female_Emote_Defeat | 49 | knee_L, knee_R, kneel | 2153 | 0 | {'body': 2153} |
| 9 | moves__Emote_Defeat | 49 | knee_L, knee_R, kneel | 2151 | 0 | {'body': 2151} |
| 10 | tennis__Female_Emote_Scuba | 115 | coverage, hipabd_L, hipabd_R | 1729 | 319 | {'body': 1729, 'Kit_Bottom': 257, 'Kit_Top': 62} |
| 11 | moves__Emote_Defeat | 57 | knee_L, knee_R, kneel | 2003 | 0 | {'body': 2003} |
