# Lobby vs game (hero sync)

LOBBY = the app's SceneKit hero (GolfArcade/Unity/CharacterAssets, MatchHeroSurfaces); GAME = Unity drawing the same hero, same pose, same cameras and lights.
Mean sRGB of the hero pixels; ratio = lobby/game luminance; MAD = mean absolute difference per channel over the hero pixels (0-255).

| shot | lobby mean | game mean | lum ratio | MAD |
|---|---|---|---|---|
| tennis male_default_body | (150,112,111) | (155,116,113) | 0.967 | 5.6 |
| tennis male_default_feet | (117,113,126) | (121,117,130) | 0.966 | 6.1 |
| tennis male_default_head | (178,93,80) | (183,96,82) | 0.968 | 5.6 |
| tennis male_default_torso | (142,99,100) | (147,103,102) | 0.970 | 5.2 |
| tennis male_s1_body | (166,130,127) | (172,135,131) | 0.965 | 6.3 |
| tennis male_s1_feet | (132,130,142) | (138,135,147) | 0.965 | 6.7 |
| tennis male_s1_head | (191,106,93) | (196,110,95) | 0.965 | 6.4 |
| tennis male_s1_torso | (160,118,118) | (165,122,121) | 0.968 | 5.9 |
| tennis male_s2_body | (154,118,96) | (160,122,98) | 0.966 | 5.9 |
| tennis male_s2_feet | (108,108,92) | (113,112,94) | 0.962 | 6.3 |
| tennis male_s2_head | (199,111,87) | (202,114,89) | 0.976 | 5.8 |
| tennis male_s2_torso | (156,106,99) | (161,110,101) | 0.970 | 5.7 |
| tennis male_s3_body | (143,135,142) | (149,140,146) | 0.967 | 6.4 |
| tennis male_s3_feet | (175,156,144) | (182,162,149) | 0.964 | 8.3 |
| tennis male_s3_head | (89,105,146) | (95,108,148) | 0.969 | 5.4 |
| tennis male_s3_torso | (134,128,138) | (138,131,141) | 0.971 | 6.1 |
| tennis male_s4_body | (111,99,73) | (115,102,73) | 0.968 | 5.2 |
| tennis male_s4_feet | (95,65,65) | (99,68,65) | 0.959 | 5.7 |
| tennis male_s4_head | (114,134,71) | (117,136,71) | 0.982 | 4.7 |
| tennis male_s4_torso | (98,102,72) | (102,104,72) | 0.975 | 4.8 |
| tennis male_s5_body | (137,117,90) | (142,121,91) | 0.970 | 6.8 |
| tennis male_s5_feet | (121,111,108) | (127,116,111) | 0.957 | 9.2 |
| tennis male_s5_head | (165,131,67) | (167,132,66) | 0.990 | 5.2 |
| tennis male_s5_torso | (151,128,95) | (155,131,95) | 0.980 | 6.4 |
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
