# Lobby vs game (hero sync)

LOBBY = the app's SceneKit hero (GolfArcade/Unity/CharacterAssets, MatchHeroSurfaces); GAME = Unity drawing the same hero, same pose, same cameras and lights.
Mean sRGB of the hero pixels; ratio = lobby/game luminance; MAD = mean absolute difference per channel over the hero pixels (0-255).

| shot | lobby mean | game mean | lum ratio | MAD |
|---|---|---|---|---|
| tennis male_default_body | (144,106,106) | (148,109,108) | 0.973 | 5.0 |
| tennis male_default_feet | (107,103,122) | (110,106,125) | 0.974 | 5.0 |
| tennis male_default_head | (176,88,75) | (180,90,75) | 0.979 | 4.3 |
| tennis male_default_torso | (141,96,100) | (144,98,100) | 0.980 | 4.5 |
| tennis male_s1_body | (158,122,122) | (163,126,124) | 0.969 | 5.7 |
| tennis male_s1_feet | (121,119,137) | (125,123,141) | 0.971 | 5.6 |
| tennis male_s1_head | (188,101,87) | (192,104,88) | 0.973 | 5.1 |
| tennis male_s1_torso | (157,114,117) | (161,117,118) | 0.975 | 5.2 |
| tennis male_s2_body | (149,112,94) | (153,115,94) | 0.973 | 5.1 |
| tennis male_s2_feet | (102,101,92) | (104,103,93) | 0.980 | 4.7 |
| tennis male_s2_head | (195,105,81) | (198,107,81) | 0.978 | 4.9 |
| tennis male_s2_torso | (151,100,96) | (155,102,96) | 0.979 | 4.7 |
| tennis male_s3_body | (140,129,135) | (145,134,138) | 0.969 | 5.9 |
| tennis male_s3_feet | (169,147,133) | (175,153,137) | 0.964 | 7.2 |
| tennis male_s3_head | (86,101,143) | (89,103,144) | 0.978 | 4.1 |
| tennis male_s3_torso | (132,123,133) | (136,126,135) | 0.974 | 5.5 |
| tennis male_s4_body | (108,97,72) | (111,100,71) | 0.977 | 4.3 |
| tennis male_s4_feet | (93,65,66) | (94,66,64) | 0.986 | 3.8 |
| tennis male_s4_head | (108,130,67) | (111,132,65) | 0.984 | 3.8 |
| tennis male_s4_torso | (96,99,70) | (98,100,69) | 0.984 | 3.9 |
| tennis male_s5_body | (135,115,89) | (139,118,89) | 0.973 | 5.9 |
| tennis male_s5_feet | (119,110,106) | (124,114,108) | 0.965 | 7.3 |
| tennis male_s5_head | (161,126,63) | (163,128,61) | 0.990 | 4.0 |
| tennis male_s5_torso | (147,124,93) | (151,127,92) | 0.979 | 5.7 |
| tennis female_default_body | (177,157,132) | (184,163,135) | 0.967 | 7.4 |
| tennis female_default_feet | (174,153,138) | (182,159,142) | 0.959 | 8.8 |
| tennis female_default_head | (174,156,128) | (178,159,128) | 0.985 | 6.2 |
| tennis female_default_torso | (177,158,131) | (182,163,133) | 0.972 | 7.2 |
| tennis female_s1_body | (190,173,148) | (197,179,152) | 0.965 | 7.9 |
| tennis female_s1_feet | (187,169,155) | (195,176,160) | 0.959 | 9.2 |
| tennis female_s1_head | (188,172,144) | (193,176,145) | 0.980 | 7.0 |
| tennis female_s1_torso | (190,173,146) | (196,179,150) | 0.970 | 7.6 |
| tennis female_s2_body | (140,112,97) | (146,116,98) | 0.965 | 6.4 |
| tennis female_s2_feet | (100,93,80) | (105,96,81) | 0.963 | 6.2 |
| tennis female_s2_head | (182,140,122) | (187,143,123) | 0.981 | 6.7 |
| tennis female_s2_torso | (141,106,103) | (146,110,105) | 0.969 | 6.3 |
| tennis female_s3_body | (158,133,125) | (164,137,128) | 0.967 | 7.1 |
| tennis female_s3_feet | (166,137,122) | (173,143,125) | 0.960 | 8.6 |
| tennis female_s3_head | (152,128,126) | (155,130,125) | 0.988 | 5.7 |
| tennis female_s3_torso | (155,132,126) | (160,135,128) | 0.972 | 6.8 |
| tennis female_s4_body | (105,84,71) | (109,86,70) | 0.972 | 5.5 |
| tennis female_s4_feet | (81,50,51) | (84,52,49) | 0.968 | 5.3 |
| tennis female_s4_head | (133,118,98) | (135,119,97) | 0.993 | 5.2 |
| tennis female_s4_torso | (101,90,76) | (104,92,76) | 0.978 | 5.3 |
| tennis female_s5_body | (123,106,93) | (127,109,93) | 0.968 | 7.5 |
| tennis female_s5_feet | (104,94,93) | (110,98,94) | 0.953 | 9.4 |
| tennis female_s5_head | (128,110,93) | (130,110,91) | 0.999 | 5.2 |
| tennis female_s5_torso | (137,119,103) | (140,122,104) | 0.977 | 7.0 |
| golf male_default_body | (75,105,110) | (78,109,113) | 0.961 | 4.9 |
| golf male_default_feet | (66,70,85) | (69,73,88) | 0.951 | 6.4 |
| golf male_default_head | (70,153,148) | (74,157,151) | 0.968 | 5.1 |
| golf male_default_torso | (71,109,114) | (74,113,116) | 0.967 | 4.3 |
| golf female_default_body | (154,120,116) | (161,126,119) | 0.957 | 6.7 |
| golf female_default_feet | (126,116,118) | (134,123,123) | 0.944 | 9.1 |
| golf female_default_head | (180,118,108) | (186,123,111) | 0.961 | 6.7 |
| golf female_default_torso | (148,112,110) | (154,117,113) | 0.958 | 6.4 |
