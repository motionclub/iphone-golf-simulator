# Lobby vs game (hero sync)

LOBBY = the app's SceneKit hero (GolfArcade/Unity/CharacterAssets, MatchHeroSurfaces); GAME = Unity drawing the same hero, same pose, same cameras and lights.
Mean sRGB of the hero pixels; ratio = lobby/game luminance; MAD = mean absolute difference per channel over the hero pixels (0-255).

| shot | lobby mean | game mean | lum ratio | MAD |
|---|---|---|---|---|
| tennis male_default_body | (150,113,111) | (155,116,113) | 0.969 | 8.0 |
| tennis male_default_feet | (117,113,126) | (120,116,127) | 0.981 | 9.1 |
| tennis male_default_head | (178,92,80) | (182,97,82) | 0.965 | 6.3 |
| tennis male_default_torso | (142,99,100) | (147,103,102) | 0.965 | 6.3 |
| tennis male_s1_body | (166,130,127) | (173,135,131) | 0.961 | 8.5 |
| tennis male_s1_feet | (133,130,142) | (138,135,146) | 0.968 | 8.7 |
| tennis male_s1_head | (190,106,92) | (196,111,96) | 0.961 | 7.4 |
| tennis male_s1_torso | (160,118,118) | (165,123,121) | 0.962 | 7.3 |
| tennis male_s2_body | (155,118,96) | (162,122,100) | 0.963 | 8.6 |
| tennis male_s2_feet | (108,108,92) | (115,111,97) | 0.964 | 9.9 |
| tennis male_s2_head | (198,110,87) | (202,114,89) | 0.973 | 6.6 |
| tennis male_s2_torso | (156,106,99) | (161,110,101) | 0.967 | 6.7 |
| tennis male_s3_body | (143,135,142) | (149,139,144) | 0.972 | 9.2 |
| tennis male_s3_feet | (175,156,144) | (181,160,145) | 0.977 | 12.3 |
| tennis male_s3_head | (89,105,146) | (95,108,147) | 0.965 | 6.3 |
| tennis male_s3_torso | (133,128,138) | (139,132,141) | 0.968 | 7.4 |
| tennis male_s4_body | (111,99,73) | (115,103,74) | 0.964 | 7.7 |
| tennis male_s4_feet | (95,65,65) | (97,69,66) | 0.953 | 8.9 |
| tennis male_s4_head | (113,134,71) | (117,136,72) | 0.982 | 5.3 |
| tennis male_s4_torso | (98,102,72) | (102,104,72) | 0.976 | 5.7 |
| tennis male_s5_body | (137,117,90) | (143,121,91) | 0.965 | 9.9 |
| tennis male_s5_feet | (121,111,108) | (130,118,112) | 0.942 | 13.3 |
| tennis male_s5_head | (165,131,67) | (167,132,67) | 0.992 | 5.6 |
| tennis male_s5_torso | (151,128,95) | (155,131,95) | 0.983 | 7.5 |
| tennis female_default_body | (174,155,127) | (187,166,138) | 0.933 | 13.1 |
| tennis female_default_feet | (171,149,133) | (184,162,145) | 0.921 | 14.6 |
| tennis female_default_head | (174,156,125) | (183,163,132) | 0.956 | 11.2 |
| tennis female_default_torso | (175,156,126) | (186,166,136) | 0.941 | 12.5 |
| tennis female_s1_body | (185,170,143) | (198,182,154) | 0.933 | 13.9 |
| tennis female_s1_feet | (182,165,149) | (197,179,162) | 0.924 | 15.3 |
| tennis female_s1_head | (185,171,141) | (195,179,149) | 0.952 | 12.4 |
| tennis female_s1_torso | (185,171,142) | (197,181,152) | 0.941 | 13.2 |
| tennis female_s2_body | (141,112,97) | (150,120,102) | 0.933 | 10.5 |
| tennis female_s2_feet | (99,92,82) | (108,99,84) | 0.923 | 8.9 |
| tennis female_s2_head | (185,140,120) | (191,147,127) | 0.952 | 12.5 |
| tennis female_s2_torso | (143,106,104) | (150,114,108) | 0.941 | 10.0 |
| tennis female_s3_body | (154,129,122) | (167,141,132) | 0.918 | 13.7 |
| tennis female_s3_feet | (163,133,117) | (176,146,129) | 0.915 | 14.8 |
| tennis female_s3_head | (148,125,124) | (161,135,131) | 0.925 | 13.5 |
| tennis female_s3_torso | (152,128,123) | (164,139,132) | 0.925 | 13.1 |
| tennis female_s4_body | (105,84,70) | (114,92,77) | 0.921 | 10.2 |
| tennis female_s4_feet | (81,50,51) | (89,57,55) | 0.889 | 8.6 |
| tennis female_s4_head | (134,121,98) | (141,126,105) | 0.954 | 11.6 |
| tennis female_s4_torso | (101,91,76) | (108,97,82) | 0.933 | 9.8 |
| tennis female_s5_body | (123,105,91) | (133,117,101) | 0.903 | 14.4 |
| tennis female_s5_feet | (103,92,90) | (116,106,102) | 0.877 | 15.9 |
| tennis female_s5_head | (133,113,93) | (138,120,101) | 0.945 | 13.4 |
| tennis female_s5_torso | (137,118,101) | (146,129,112) | 0.918 | 14.5 |
