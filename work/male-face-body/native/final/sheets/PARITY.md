# Lobby vs game (hero sync)

LOBBY = the app's SceneKit hero (GolfArcade/Unity/CharacterAssets, MatchHeroSurfaces); GAME = Unity drawing the same hero, same pose, same cameras and lights.
Mean sRGB of the hero pixels; ratio = lobby/game luminance; MAD = mean absolute difference per channel over the hero pixels (0-255).

| shot | lobby mean | game mean | lum ratio | MAD |
|---|---|---|---|---|
| tennis male_default_body | (148,111,110) | (154,116,113) | 0.965 | 6.5 |
| tennis male_default_feet | (114,112,125) | (119,116,129) | 0.963 | 7.3 |
| tennis male_default_head | (178,92,80) | (182,96,82) | 0.968 | 5.6 |
| tennis male_default_torso | (142,99,100) | (146,103,102) | 0.969 | 5.4 |
| tennis male_s1_body | (164,129,126) | (170,134,130) | 0.963 | 7.3 |
| tennis male_s1_feet | (130,128,141) | (135,133,146) | 0.962 | 7.9 |
| tennis male_s1_head | (191,106,92) | (196,110,95) | 0.964 | 6.5 |
| tennis male_s1_torso | (159,118,118) | (165,123,121) | 0.967 | 6.1 |
| tennis male_s2_body | (154,117,98) | (160,121,100) | 0.963 | 6.9 |
| tennis male_s2_feet | (107,106,95) | (113,110,97) | 0.959 | 7.6 |
| tennis male_s2_head | (199,111,87) | (202,114,89) | 0.975 | 6.1 |
| tennis male_s2_torso | (155,106,99) | (161,110,101) | 0.969 | 5.9 |
| tennis male_s3_body | (142,134,141) | (148,139,144) | 0.965 | 7.6 |
| tennis male_s3_feet | (173,154,142) | (181,161,147) | 0.960 | 9.9 |
| tennis male_s3_head | (89,105,146) | (94,108,147) | 0.970 | 5.6 |
| tennis male_s3_torso | (134,128,138) | (139,131,141) | 0.971 | 6.4 |
| tennis male_s4_body | (110,101,75) | (114,104,75) | 0.970 | 6.0 |
| tennis male_s4_feet | (93,68,68) | (97,70,68) | 0.967 | 6.7 |
| tennis male_s4_head | (113,134,71) | (117,136,71) | 0.981 | 4.9 |
| tennis male_s4_torso | (98,101,72) | (102,104,72) | 0.973 | 5.0 |
| tennis male_s5_body | (140,120,93) | (144,123,93) | 0.973 | 7.6 |
| tennis male_s5_feet | (126,116,113) | (131,121,115) | 0.964 | 10.3 |
| tennis male_s5_head | (165,131,67) | (167,132,66) | 0.990 | 5.5 |
| tennis male_s5_torso | (151,128,96) | (155,131,96) | 0.978 | 6.7 |
| tennis female_default_body | (174,155,127) | (180,160,130) | 0.967 | 7.1 |
| tennis female_default_feet | (171,149,132) | (178,155,137) | 0.959 | 8.2 |
| tennis female_default_head | (173,156,125) | (176,157,125) | 0.988 | 6.0 |
| tennis female_default_torso | (174,156,126) | (179,161,129) | 0.972 | 6.8 |
| tennis female_s1_body | (185,170,143) | (192,176,147) | 0.963 | 8.1 |
| tennis female_s1_feet | (182,165,149) | (191,173,155) | 0.956 | 9.0 |
| tennis female_s1_head | (185,171,141) | (189,174,143) | 0.980 | 7.1 |
| tennis female_s1_torso | (185,171,142) | (191,176,146) | 0.968 | 7.7 |
| tennis female_s2_body | (140,111,96) | (144,114,98) | 0.975 | 5.5 |
| tennis female_s2_feet | (97,91,81) | (99,92,83) | 0.982 | 5.0 |
| tennis female_s2_head | (184,139,120) | (187,141,120) | 0.983 | 6.4 |
| tennis female_s2_torso | (141,105,103) | (144,107,105) | 0.981 | 5.3 |
| tennis female_s3_body | (154,129,122) | (160,133,124) | 0.968 | 6.7 |
| tennis female_s3_feet | (163,133,117) | (170,139,120) | 0.959 | 7.9 |
| tennis female_s3_head | (148,125,124) | (150,126,123) | 0.991 | 5.1 |
| tennis female_s3_torso | (152,128,123) | (157,132,125) | 0.973 | 6.4 |
| tennis female_s4_body | (105,84,70) | (108,86,69) | 0.985 | 4.4 |
| tennis female_s4_feet | (81,50,51) | (82,50,48) | 0.999 | 3.8 |
| tennis female_s4_head | (134,121,98) | (135,121,96) | 0.997 | 4.8 |
| tennis female_s4_torso | (101,91,76) | (102,92,74) | 0.991 | 4.1 |
| tennis female_s5_body | (123,105,90) | (127,108,91) | 0.972 | 6.7 |
| tennis female_s5_feet | (103,92,90) | (108,96,91) | 0.960 | 8.0 |
| tennis female_s5_head | (133,112,93) | (133,112,91) | 1.003 | 4.8 |
| tennis female_s5_torso | (137,118,101) | (140,121,101) | 0.978 | 6.5 |
