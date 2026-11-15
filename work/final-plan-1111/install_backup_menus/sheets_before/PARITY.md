# Lobby vs game (hero sync)

LOBBY = the app's SceneKit hero (GolfArcade/Unity/CharacterAssets, MatchHeroSurfaces); GAME = Unity drawing the same hero, same pose, same cameras and lights.
Mean sRGB of the hero pixels; ratio = lobby/game luminance; MAD = mean absolute difference per channel over the hero pixels (0-255).

| shot | lobby mean | game mean | lum ratio | MAD |
|---|---|---|---|---|
| tennis male_default_body | (154,112,114) | (156,113,114) | 0.986 | 5.7 |
| tennis male_default_feet | (114,109,128) | (116,111,130) | 0.979 | 5.7 |
| tennis male_default_head | (192,99,88) | (185,95,83) | 1.035 | 8.8 |
| tennis male_default_torso | (153,103,108) | (154,104,107) | 0.997 | 5.5 |
| tennis male_s1_body | (168,127,129) | (171,130,130) | 0.981 | 6.4 |
| tennis male_s1_feet | (128,125,144) | (131,128,147) | 0.976 | 6.2 |
| tennis male_s1_head | (203,111,99) | (197,108,95) | 1.025 | 9.7 |
| tennis male_s1_torso | (168,120,125) | (170,122,124) | 0.990 | 6.2 |
| tennis male_s2_body | (160,119,102) | (161,120,101) | 0.993 | 6.3 |
| tennis male_s2_feet | (109,107,99) | (112,109,100) | 0.982 | 5.5 |
| tennis male_s2_head | (211,116,94) | (200,111,87) | 1.052 | 12.1 |
| tennis male_s2_torso | (165,109,105) | (164,109,103) | 1.005 | 6.6 |
| tennis male_s3_body | (145,137,149) | (148,139,150) | 0.985 | 6.4 |
| tennis male_s3_feet | (175,155,143) | (180,159,145) | 0.976 | 8.1 |
| tennis male_s3_head | (95,112,165) | (92,108,157) | 1.031 | 8.1 |
| tennis male_s3_torso | (138,132,150) | (139,133,149) | 0.994 | 6.6 |
| tennis male_s4_body | (115,108,81) | (117,109,79) | 0.991 | 4.8 |
| tennis male_s4_feet | (99,72,73) | (101,73,71) | 0.989 | 4.8 |
| tennis male_s4_head | (119,147,80) | (117,142,74) | 1.036 | 7.4 |
| tennis male_s4_torso | (105,112,80) | (105,112,77) | 1.001 | 4.6 |
| tennis male_s5_body | (147,127,100) | (148,127,97) | 1.001 | 7.3 |
| tennis male_s5_feet | (128,120,119) | (131,122,118) | 0.985 | 9.0 |
| tennis male_s5_head | (179,143,76) | (168,134,69) | 1.071 | 11.4 |
| tennis male_s5_torso | (161,138,104) | (160,137,101) | 1.011 | 7.9 |
| tennis female_default_body | (179,160,135) | (183,163,135) | 0.982 | 7.0 |
| tennis female_default_feet | (176,155,142) | (180,158,143) | 0.980 | 8.2 |
| tennis female_default_head | (176,159,129) | (178,160,128) | 0.994 | 6.2 |
| tennis female_default_torso | (180,163,135) | (183,164,135) | 0.989 | 7.0 |
| tennis female_s1_body | (192,176,151) | (197,180,153) | 0.978 | 7.5 |
| tennis female_s1_feet | (189,171,159) | (194,175,161) | 0.977 | 8.6 |
| tennis female_s1_head | (189,175,145) | (193,177,146) | 0.987 | 7.0 |
| tennis female_s1_torso | (193,178,151) | (196,180,152) | 0.985 | 7.5 |
| tennis female_s2_body | (145,116,103) | (148,117,103) | 0.985 | 5.7 |
| tennis female_s2_feet | (104,96,89) | (106,97,88) | 0.989 | 5.4 |
| tennis female_s2_head | (187,142,124) | (188,143,123) | 0.993 | 7.1 |
| tennis female_s2_torso | (147,111,110) | (149,112,110) | 0.993 | 5.7 |
| tennis female_s3_body | (159,134,129) | (162,136,129) | 0.984 | 6.6 |
| tennis female_s3_feet | (167,139,125) | (171,142,126) | 0.982 | 8.0 |
| tennis female_s3_head | (149,126,128) | (151,127,126) | 0.995 | 5.3 |
| tennis female_s3_torso | (157,134,132) | (160,135,131) | 0.991 | 6.5 |
| tennis female_s4_body | (109,88,75) | (110,89,73) | 0.992 | 4.7 |
| tennis female_s4_feet | (85,55,56) | (86,54,53) | 1.008 | 4.7 |
| tennis female_s4_head | (134,122,100) | (135,121,97) | 1.001 | 4.9 |
| tennis female_s4_torso | (105,95,81) | (106,95,79) | 1.000 | 4.4 |
| tennis female_s5_body | (126,110,98) | (128,110,95) | 0.996 | 7.0 |
| tennis female_s5_feet | (109,100,100) | (111,100,98) | 0.995 | 8.6 |
| tennis female_s5_head | (133,113,95) | (131,112,92) | 1.015 | 5.6 |
| tennis female_s5_torso | (140,123,108) | (141,123,106) | 1.003 | 7.2 |
| golf male_default_body | (85,114,121) | (87,118,124) | 0.969 | 5.2 |
| golf male_default_feet | (76,78,94) | (79,82,98) | 0.955 | 7.4 |
| golf male_default_head | (81,164,165) | (82,167,166) | 0.986 | 5.6 |
| golf male_default_torso | (81,119,127) | (83,122,128) | 0.976 | 4.7 |
| golf female_default_body | (160,128,124) | (165,132,127) | 0.968 | 7.4 |
| golf female_default_feet | (132,122,124) | (140,128,128) | 0.947 | 9.6 |
| golf female_default_head | (186,127,120) | (187,128,120) | 0.989 | 8.8 |
| golf female_default_torso | (155,120,119) | (159,124,121) | 0.973 | 7.4 |
