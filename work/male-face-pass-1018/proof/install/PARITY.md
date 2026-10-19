# Lobby vs game (hero sync)

LOBBY = the app's SceneKit hero (GolfArcade/Unity/CharacterAssets, MatchHeroSurfaces); GAME = Unity drawing the same hero, same pose, same cameras and lights.
Mean sRGB of the hero pixels; ratio = lobby/game luminance; MAD = mean absolute difference per channel over the hero pixels (0-255).

| shot | lobby mean | game mean | lum ratio | MAD |
|---|---|---|---|---|
| tennis male_default_body | (149,111,109) | (154,115,111) | 0.966 | 5.8 |
| tennis male_default_feet | (113,110,122) | (118,114,126) | 0.964 | 6.3 |
| tennis male_default_head | (181,93,80) | (185,97,81) | 0.970 | 5.5 |
| tennis male_default_torso | (145,101,100) | (150,104,102) | 0.970 | 5.3 |
| tennis male_s1_body | (162,127,124) | (169,133,128) | 0.961 | 6.8 |
| tennis male_s1_feet | (127,126,138) | (132,131,142) | 0.962 | 7.0 |
| tennis male_s1_head | (191,106,91) | (196,110,94) | 0.963 | 6.6 |
| tennis male_s1_torso | (160,119,117) | (166,123,121) | 0.964 | 6.3 |
| tennis male_s2_body | (156,118,97) | (162,123,99) | 0.964 | 6.1 |
| tennis male_s2_feet | (108,107,93) | (113,112,96) | 0.960 | 6.4 |
| tennis male_s2_head | (200,110,85) | (204,113,87) | 0.975 | 6.0 |
| tennis male_s2_torso | (157,106,98) | (162,110,99) | 0.967 | 5.9 |
| tennis male_s3_body | (147,137,141) | (153,141,144) | 0.968 | 6.4 |
| tennis male_s3_feet | (178,157,143) | (185,163,147) | 0.964 | 8.2 |
| tennis male_s3_head | (91,106,146) | (97,108,147) | 0.970 | 5.4 |
| tennis male_s3_torso | (138,129,138) | (143,133,140) | 0.971 | 6.2 |
| tennis male_s4_body | (114,103,77) | (119,106,77) | 0.968 | 5.2 |
| tennis male_s4_feet | (98,71,70) | (103,74,71) | 0.960 | 5.6 |
| tennis male_s4_head | (116,136,72) | (119,138,72) | 0.983 | 4.6 |
| tennis male_s4_torso | (102,104,74) | (105,106,74) | 0.975 | 4.9 |
| tennis male_s5_body | (142,122,95) | (147,126,96) | 0.971 | 6.6 |
| tennis male_s5_feet | (128,118,115) | (134,123,118) | 0.959 | 8.8 |
| tennis male_s5_head | (167,133,68) | (169,134,68) | 0.990 | 4.9 |
| tennis male_s5_torso | (155,132,99) | (158,134,99) | 0.980 | 6.3 |
| tennis female_default_body | (179,159,132) | (186,165,136) | 0.966 | 7.4 |
| tennis female_default_feet | (176,154,138) | (184,161,143) | 0.958 | 8.9 |
| tennis female_default_head | (177,159,129) | (181,161,130) | 0.983 | 6.4 |
| tennis female_default_torso | (179,160,131) | (184,165,134) | 0.971 | 7.1 |
| tennis female_s1_body | (190,174,148) | (198,181,153) | 0.962 | 8.4 |
| tennis female_s1_feet | (188,170,155) | (196,178,161) | 0.956 | 9.7 |
| tennis female_s1_head | (189,174,145) | (195,178,147) | 0.976 | 7.5 |
| tennis female_s1_torso | (190,175,147) | (196,181,151) | 0.967 | 8.0 |
| tennis female_s2_body | (142,114,97) | (148,118,100) | 0.963 | 6.5 |
| tennis female_s2_feet | (101,94,80) | (106,98,82) | 0.960 | 6.4 |
| tennis female_s2_head | (185,142,123) | (189,145,124) | 0.978 | 6.9 |
| tennis female_s2_torso | (142,108,104) | (147,112,106) | 0.967 | 6.4 |
| tennis female_s3_body | (160,134,126) | (166,139,129) | 0.966 | 7.1 |
| tennis female_s3_feet | (168,138,122) | (176,144,126) | 0.959 | 8.7 |
| tennis female_s3_head | (155,131,127) | (159,132,127) | 0.987 | 5.7 |
| tennis female_s3_torso | (158,133,127) | (163,137,129) | 0.971 | 6.9 |
| tennis female_s4_body | (108,86,72) | (112,89,72) | 0.971 | 5.5 |
| tennis female_s4_feet | (84,52,52) | (87,54,51) | 0.967 | 5.4 |
| tennis female_s4_head | (137,122,100) | (139,122,99) | 0.992 | 5.2 |
| tennis female_s4_torso | (103,92,78) | (107,94,77) | 0.977 | 5.2 |
| tennis female_s5_body | (126,108,94) | (130,112,96) | 0.967 | 7.3 |
| tennis female_s5_feet | (107,96,94) | (113,101,97) | 0.952 | 9.2 |
| tennis female_s5_head | (133,113,96) | (134,114,94) | 0.997 | 5.1 |
| tennis female_s5_torso | (140,121,105) | (144,124,106) | 0.976 | 6.9 |
| golf male_default_body | (79,112,116) | (87,118,120) | 0.944 | 7.2 |
| golf male_default_feet | (71,75,90) | (79,82,94) | 0.921 | 9.1 |
| golf male_default_head | (75,160,154) | (83,164,158) | 0.962 | 6.7 |
| golf male_default_torso | (75,117,120) | (82,122,124) | 0.950 | 6.5 |
| golf female_default_body | (155,122,116) | (162,128,121) | 0.954 | 7.2 |
| golf female_default_feet | (127,117,119) | (134,125,125) | 0.943 | 9.4 |
| golf female_default_head | (181,119,108) | (187,124,112) | 0.960 | 7.0 |
| golf female_default_torso | (149,113,110) | (155,119,114) | 0.955 | 6.7 |
