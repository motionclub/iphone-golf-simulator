# Garment stress report: MatchHero_Female

Stress poses: 152 (worst frames per region from every clip + coverage), 24 views each, noise filter 3x3 opening.

- GATE TEARS: FAIL - 85257 skin pixels through cloth, in 145 poses
- GATE LAYERS: FAIL - 837 garment pixels through an outer garment, in 17 poses
- by victim: {'body': 85257, 'Kit_Top': 249, 'Kit_Bottom': 588}
- by victim<coverer: {'body<Kit_Top': 85257, 'Kit_Bottom<Kit_Top': 588, 'Kit_Top<Kit_Bottom': 249}
- HOLES (hidden skin seen through): 9444 px in 132 poses
  - holes split: background 7428, lining 1694, outer surface > 3 cm behind 322

Before: tear 352507 px (152 poses), layer 13 px (1 poses)

| # | clip | frame | why | tear | layer | by |
|---|---|---|---|---|---|---|
| 0 | tennis__Female_Emote_Thrust | 47 | hipabd_L, hipabd_R | 2764 | 0 | {'body': 2764} |
| 1 | tennis__Female_Emote_Thrust | 31 | hipabd_L, hipabd_R | 2628 | 0 | {'body': 2628} |
| 2 | moves__Emote_Victory | 33 | elbow_L | 2422 | 0 | {'body': 2422} |
| 3 | moves__Emote_Victory | 77 | elbow_R | 2321 | 0 | {'body': 2321} |
| 4 | tennis__Female_Emote_Victory | 77 | elbow_R | 2293 | 0 | {'body': 2293} |
| 5 | moves__Emote_Stomp | 10 | elbow_L, hipflex_R, knee_R | 2003 | 0 | {'body': 2003} |
| 6 | tennis__Female_Emote_Stomp | 10 | coverage, elbow_L, hipflex_R | 2001 | 0 | {'body': 2001} |
| 7 | tennis__Female_Emote_Thrust | 93 | elbow_L, hipabd_L, hipabd_R | 1675 | 0 | {'body': 1675} |
| 8 | tennis__Female_ForehandShort | 3 | elbow_L, hipflex_R, knee_L | 1662 | 0 | {'body': 1662} |
| 9 | moves__Emote_FistPump | 11 | elbow_L, hipflex_L, knee_L | 1642 | 0 | {'body': 1642} |
| 10 | tennis__Female_BackhandWide | 14 | hipflex_L, knee_L, kneel | 1637 | 0 | {'body': 1637} |
| 11 | tennis__Female_Emote_FistPump | 11 | coverage, elbow_L, hipflex_L | 1599 | 0 | {'body': 1599} |
