# Lobby vs game (hero sync)

LOBBY = the app's SceneKit hero (GolfArcade/Unity/CharacterAssets, MatchHeroSurfaces); GAME = Unity drawing the same hero, same pose, same cameras and lights.
Mean sRGB of the hero pixels; ratio = lobby/game luminance; MAD = mean absolute difference per channel over the hero pixels (0-255).

| shot | lobby mean | game mean | lum ratio | MAD |
|---|---|---|---|---|
| tennis male_default_body | (145,107,107) | (149,110,109) | 0.972 | 5.0 |
| tennis male_default_feet | (108,105,122) | (111,108,125) | 0.973 | 5.1 |
| tennis male_default_head | (178,89,76) | (182,92,76) | 0.978 | 4.3 |
| tennis male_default_torso | (142,98,100) | (146,100,101) | 0.979 | 4.5 |
| tennis male_s1_body | (158,123,122) | (164,127,125) | 0.966 | 6.0 |
| tennis male_s1_feet | (121,120,137) | (125,124,142) | 0.969 | 5.8 |
| tennis male_s1_head | (188,102,88) | (193,105,89) | 0.970 | 5.4 |
| tennis male_s1_torso | (157,116,117) | (162,119,120) | 0.971 | 5.5 |
| tennis male_s2_body | (150,113,94) | (155,117,96) | 0.971 | 5.2 |
| tennis male_s2_feet | (102,102,92) | (105,104,94) | 0.978 | 4.7 |
| tennis male_s2_head | (196,105,81) | (200,108,82) | 0.976 | 5.1 |
| tennis male_s2_torso | (153,102,96) | (157,105,98) | 0.976 | 4.8 |
| tennis male_s3_body | (142,131,136) | (147,135,139) | 0.969 | 5.9 |
| tennis male_s3_feet | (170,148,134) | (177,154,137) | 0.963 | 7.2 |
| tennis male_s3_head | (88,102,144) | (91,104,145) | 0.977 | 4.2 |
| tennis male_s3_torso | (134,124,134) | (138,128,136) | 0.973 | 5.5 |
| tennis male_s4_body | (110,99,73) | (113,101,72) | 0.977 | 4.3 |
| tennis male_s4_feet | (94,66,66) | (96,67,65) | 0.985 | 3.8 |
| tennis male_s4_head | (110,132,68) | (113,134,67) | 0.983 | 3.9 |
| tennis male_s4_torso | (98,101,72) | (100,102,70) | 0.983 | 3.9 |
| tennis male_s5_body | (137,116,90) | (141,120,90) | 0.972 | 5.8 |
| tennis male_s5_feet | (120,111,107) | (125,115,109) | 0.964 | 7.2 |
| tennis male_s5_head | (163,128,64) | (165,129,63) | 0.989 | 4.0 |
| tennis male_s5_torso | (150,126,94) | (153,129,94) | 0.978 | 5.7 |
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
| golf male_default_body | (75,105,110) | (79,110,113) | 0.959 | 5.1 |
| golf male_default_feet | (66,70,86) | (69,74,89) | 0.951 | 6.4 |
| golf male_default_head | (71,154,149) | (75,159,152) | 0.966 | 5.3 |
| golf male_default_torso | (72,110,114) | (75,114,117) | 0.964 | 4.5 |
| golf female_default_body | (155,122,116) | (162,128,121) | 0.954 | 7.2 |
| golf female_default_feet | (127,117,119) | (134,125,125) | 0.943 | 9.4 |
| golf female_default_head | (181,119,108) | (187,124,112) | 0.960 | 7.0 |
| golf female_default_torso | (149,113,110) | (155,119,114) | 0.955 | 6.7 |
