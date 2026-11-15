# Lobby vs game (hero sync)

LOBBY = the app's SceneKit hero (GolfArcade/Unity/CharacterAssets, MatchHeroSurfaces); GAME = Unity drawing the same hero, same pose, same cameras and lights.
Mean sRGB of the hero pixels; ratio = lobby/game luminance; MAD = mean absolute difference per channel over the hero pixels (0-255).

| shot | lobby mean | game mean | lum ratio | MAD |
|---|---|---|---|---|
| tennis male_default_body | (150,111,113) | (152,113,113) | 0.981 | 5.6 |
| tennis male_default_feet | (114,109,127) | (117,111,128) | 0.979 | 5.7 |
| tennis male_default_head | (186,97,86) | (178,97,85) | 1.017 | 8.7 |
| tennis male_default_torso | (148,102,106) | (149,103,106) | 0.990 | 5.4 |
| tennis male_s1_body | (164,126,128) | (167,130,129) | 0.976 | 6.3 |
| tennis male_s1_feet | (128,125,143) | (131,128,145) | 0.975 | 6.2 |
| tennis male_s1_head | (198,110,98) | (191,110,98) | 1.008 | 9.6 |
| tennis male_s1_torso | (164,119,123) | (165,121,124) | 0.984 | 6.1 |
| tennis male_s2_body | (157,117,101) | (158,120,101) | 0.983 | 5.9 |
| tennis male_s2_feet | (109,107,99) | (112,109,99) | 0.982 | 5.5 |
| tennis male_s2_head | (205,113,92) | (195,112,91) | 1.025 | 10.3 |
| tennis male_s2_torso | (160,107,103) | (159,108,103) | 0.992 | 6.0 |
| tennis male_s3_body | (144,134,145) | (148,137,145) | 0.982 | 6.3 |
| tennis male_s3_feet | (173,153,141) | (177,157,143) | 0.975 | 7.5 |
| tennis male_s3_head | (95,109,158) | (96,106,148) | 1.025 | 8.4 |
| tennis male_s3_torso | (137,129,144) | (139,130,143) | 0.991 | 6.4 |
| tennis male_s4_body | (114,105,80) | (116,106,80) | 0.990 | 5.2 |
| tennis male_s4_feet | (99,72,73) | (101,73,71) | 0.989 | 4.9 |
| tennis male_s4_head | (116,142,78) | (116,136,79) | 1.035 | 8.1 |
| tennis male_s4_torso | (102,107,78) | (104,107,78) | 1.000 | 5.1 |
| tennis male_s5_body | (143,123,98) | (144,124,99) | 0.993 | 7.2 |
| tennis male_s5_feet | (126,118,117) | (129,120,117) | 0.982 | 8.5 |
| tennis male_s5_head | (172,137,74) | (162,130,77) | 1.052 | 10.6 |
| tennis male_s5_torso | (155,133,102) | (155,132,103) | 1.001 | 7.7 |
| tennis female_default_body | (176,158,133) | (181,160,135) | 0.981 | 7.2 |
| tennis female_default_feet | (173,153,139) | (177,156,141) | 0.980 | 7.9 |
| tennis female_default_head | (174,157,127) | (177,158,129) | 0.992 | 6.5 |
| tennis female_default_torso | (177,159,133) | (180,161,134) | 0.988 | 7.2 |
| tennis female_s1_body | (189,173,149) | (194,177,152) | 0.977 | 7.7 |
| tennis female_s1_feet | (186,169,156) | (191,173,159) | 0.977 | 8.4 |
| tennis female_s1_head | (188,173,144) | (192,175,147) | 0.986 | 7.3 |
| tennis female_s1_torso | (190,175,149) | (194,177,151) | 0.984 | 7.7 |
| tennis female_s2_body | (144,114,102) | (147,117,102) | 0.980 | 5.7 |
| tennis female_s2_feet | (104,96,88) | (106,97,86) | 0.989 | 5.5 |
| tennis female_s2_head | (185,140,123) | (187,142,123) | 0.987 | 6.8 |
| tennis female_s2_torso | (145,109,108) | (147,111,108) | 0.987 | 5.6 |
| tennis female_s3_body | (157,132,127) | (161,134,126) | 0.983 | 6.6 |
| tennis female_s3_feet | (165,137,123) | (168,139,124) | 0.982 | 7.7 |
| tennis female_s3_head | (148,125,125) | (152,125,122) | 0.993 | 5.5 |
| tennis female_s3_torso | (155,132,128) | (158,133,127) | 0.989 | 6.5 |
| tennis female_s4_body | (107,86,74) | (110,87,72) | 0.992 | 5.0 |
| tennis female_s4_feet | (85,54,56) | (86,54,52) | 1.009 | 4.8 |
| tennis female_s4_head | (132,119,98) | (134,119,97) | 1.000 | 5.2 |
| tennis female_s4_torso | (103,92,79) | (105,92,78) | 0.998 | 4.8 |
| tennis female_s5_body | (124,107,96) | (125,108,95) | 0.993 | 7.0 |
| tennis female_s5_feet | (107,97,98) | (108,98,96) | 0.996 | 8.4 |
| tennis female_s5_head | (130,111,93) | (129,109,92) | 1.010 | 5.6 |
| tennis female_s5_torso | (137,119,105) | (137,120,105) | 0.999 | 7.1 |
| golf male_default_body | (84,111,117) | (91,114,119) | 0.964 | 6.0 |
| golf male_default_feet | (76,78,93) | (80,82,95) | 0.955 | 7.5 |
| golf male_default_head | (82,159,158) | (93,161,159) | 0.977 | 8.0 |
| golf male_default_torso | (80,115,122) | (87,117,123) | 0.970 | 5.8 |
| golf female_default_body | (157,126,122) | (161,131,125) | 0.965 | 7.5 |
| golf female_default_feet | (132,121,123) | (140,128,127) | 0.949 | 9.5 |
| golf female_default_head | (177,122,116) | (176,125,118) | 0.984 | 9.7 |
| golf female_default_torso | (150,118,117) | (154,122,119) | 0.968 | 7.5 |
