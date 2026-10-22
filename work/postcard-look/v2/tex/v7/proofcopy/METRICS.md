# POSTCARD_LOOK area I: measurements from the Game-view pixels (and the installed FBX)

Stills: `work/postcard-look/v2/tex/v7/stills9` (900x1600, pipeline asset **TennisURP**, quality level 2, Unity 6000.3.24f1). Masks: `proof/masks/` (PostcardProofMasks, same frames; ID render = exact per-material masks).
Mask statistics read `masks/<k>/<name>.full.png`; it equals the proof still except for animated water (table below). Thresholds: `measure.py` THRESH (the user's lines, the runtime gates' own limits). Re-run: `run_proof.sh metrics`.

## Gates

| gate | result | numbers |
|---|---|---|
| GRASS_HUE_GAMEVIEW hole08 | **PASS** | hole08_1_tee: central lower third mean #A6B642 h68.6 S0.636 V0.716; fairway+green px 704044 mean hue 69.2 (median 69.6), clipped(any ch>=250) 0.0%; hole08_2_approach: central lower third mean #A0B13F h68.8 S0.645 V0.695; fairway+green px 713760 mean hue 68.5 (median 69.0), clipped(any ch>=250) 0.1%; target fairway/green h60..76 (stills h64-73), clip <= 5% / info: hole08_3_arch rough 206462px h61.0 S0.534 V0.505; hole08_aerial rough 16902px h60.3 S0.499 V0.536 |
| GRASS_HUE_GAMEVIEW hole09 | **PASS** | hole09_1_tee: central lower third mean #93A443 h70.5 S0.591 V0.641; fairway+green px 861826 mean hue 70.0 (median 70.2), clipped(any ch>=250) 0.0%; hole09_2_approach: central lower third mean #85953E h71.0 S0.585 V0.583; fairway+green px 861814 mean hue 72.2 (median 72.4), clipped(any ch>=250) 0.0%; target fairway/green h60..76 (stills h64-73), clip <= 5% / info: hole09_3_ruin scrub 648470px h48.5 S0.351 V0.486; hole09_aerial rough 54738px h68.7 S0.487 V0.505; hole09_aerial scrub 80917px h47.8 S0.33 V0.515 |
| GRASS_HUE_GAMEVIEW hole10 | **PASS** | hole10_1_tee: central lower third mean #9EB825 h70.6 S0.8 V0.721; fairway+green px 861855 mean hue 70.2 (median 70.4), clipped(any ch>=250) 0.9%; hole10_2_approach: central lower third mean #94AB2B h70.7 S0.75 V0.67; fairway+green px 861930 mean hue 70.3 (median 70.4), clipped(any ch>=250) 0.0%; target fairway/green h60..76 (stills h64-73), clip <= 5% / info: hole10_3_lavarim rough 117050px h61.7 S0.666 V0.465; hole10_aerial rough 70170px h61.5 S0.684 V0.474 |
| NOT_FLAT_PER_STILL | **PASS** | (sd >= 12, largest colour cell <= 50%, address stills flat windows <= 15%; failing: none) hole08_1_tee: lower-60% lum sd 23.59, flat 8px windows 4.8%, largest colour cell 11%, 20 colour cells >= 1% ok / hole08_2_approach: lower-60% lum sd 24.19, flat 8px windows 3.9%, largest colour cell 11%, 21 colour cells >= 1% ok / hole08_3_arch: lower-60% lum sd 40.66, flat 8px windows 9.5% (landmark: info), largest colour cell 8%, 28 colour cells >= 1% ok / hole09_1_tee: lower-60% lum sd 16.44, flat 8px windows 3.7%, largest colour cell 22%, 16 colour cells >= 1% ok / hole09_2_approach: lower-60% lum sd 18.32, flat 8px windows 4.9%, largest colour cell 14%, 14 colour cells >= 1% ok / hole09_3_ruin: lower-60% lum sd 23.43, flat 8px windows 0.4% (landmark: info), largest colour cell 11%, 21 colour cells >= 1% ok / hole10_1_tee: lower-60% lum sd 22.45, flat 8px windows 0.4%, largest colour cell 11%, 18 colour cells >= 1% ok / hole10_2_approach: lower-60% lum sd 15.14, flat 8px windows 2.4%, largest colour cell 9%, 24 colour cells >= 1% ok / hole10_3_lavarim: lower-60% lum sd 39.84, flat 8px windows 12.9% (landmark: info), largest colour cell 15%, 25 colour cells >= 1% ok; flat baseline stills for contrast: hole08_layup sd 6.42 flat 99% cell 44%, hole08_midpad sd 6.58 flat 99% cell 32%, hole08_tee sd 4.18 flat 99% cell 58%, hole09_fairway sd 6.9 flat 99% cell 45%, hole09_ridge sd 0.44 flat 100% cell 60%, hole09_tee sd 1.48 flat 100% cell 65%, hole10_approach sd 0.65 flat 100% cell 64%, hole10_rim sd 4.55 flat 99% cell 57%, hole10_tee sd 1.57 flat 100% cell 63% |
| SHELF_NOT_LOUDEST | **PASS** | (shelf <= 10% of the brightest 2%, <= 1.3 x the open sea) hole08_aerial: shelf 3281 px = 0.23% of the frame, mean #225360 h192.2 V0.375 lum 73.4, ocean beside it lum 79.3, ratio 0.926, shelf = 0.0% and turquoise = 0.0% of the brightest 2% (lum >= 234.2), brightest 2% is sky/other 96.5%, surf 0.0%, ocean 3.5% ok / hole09_aerial: shelf 7992 px = 0.56% of the frame, mean #1C596E h195.4 V0.433 lum 77.8, ocean beside it lum 74.5, ratio 1.044, shelf = 0.0% and turquoise = 0.0% of the brightest 2% (lum >= 198.0), brightest 2% is sky/other 79.59%, surf 1.5%, ocean 0.0% ok / hole08_1_tee: shelf 21 px (< 300: not measurable here) / hole08_2_approach: shelf 0 px (< 300: not measurable here) / hole08_3_arch: shelf 0 px (< 300: not measurable here) / hole09_1_tee: shelf 0 px (< 300: not measurable here) / hole09_2_approach: shelf 419 px = 0.03% of the frame, mean #1B566F h197.9 V0.435 lum 75.1, ocean beside it lum 87.7, ratio 0.856, shelf = 0.0% and turquoise = 0.0% of the brightest 2% (lum >= 231.4), brightest 2% is sky/other 100.0%, surf 0.0%, ocean 0.0% ok / hole09_3_ruin: shelf 390 px = 0.03% of the frame, mean #1A5C6F h193.1 V0.436 lum 79.7, ocean beside it lum 89.4, ratio 0.891, shelf = 0.0% and turquoise = 0.0% of the brightest 2% (lum >= 176.8), brightest 2% is sky/other 2.64%, surf 0.1%, ocean 0.0% ok |
| LAVA_ORANGE_AND_BRIGHT | **PASS** | (in band >= 85%, G>=250 <= 5%, dark V<.40 <= 15%, mean V >= 0.7; crater.jpg pool (212,62,14) h15 S.93 V.83) hole10_1_tee: lava 4645 px (0.3% of frame) mean #C24E1F h17.3 S0.841 V0.762, in band (h8-28 S>=.75 V>=.7) 92.1% (h+S only 100.0%), dark V<.40 1.4%, G>=250 0.0%, cream 0.00%, dark components 4 largest 21 px (0.45% of the lava) ok / hole10_2_approach: lava 179100 px (12.4% of frame) mean #DC5419 h18.2 S0.886 V0.864, in band (h8-28 S>=.75 V>=.7) 94.9% (h+S only 100.0%), dark V<.40 1.7%, G>=250 0.0%, cream 0.00%, dark components 138 largest 159 px (0.09% of the lava) ok / hole10_3_lavarim: lava 598558 px (41.6% of frame) mean #DA5319 h18.1 S0.885 V0.854, in band (h8-28 S>=.75 V>=.7) 92.6% (h+S only 100.0%), dark V<.40 2.9%, G>=250 0.0%, cream 0.00%, dark components 254 largest 3626 px (0.61% of the lava) ok / hole10_aerial (extra aerial, info): lava 486688 px (33.8% of frame) mean #D8541A h18.1 S0.878 V0.849, in band (h8-28 S>=.75 V>=.7) 94.0% (h+S only 100.0%), dark V<.40 1.9%, G>=250 0.0%, cream 0.00%, dark components 356 largest 220 px (0.05% of the lava) ok |
| BASALT_JOINTS | **PASS** | (glow <= 20% of the basalt, non-glow median lum <= 55.0, glow in vertical lines >= 50%, horizontal rungs <= 20%; crater.jpg basalt (26,25,29)) hole10_1_tee: basalt 144553 px, non-glow mean #381C1A h4.8 S0.534 V0.219 median lum 34.3, glow 2.8% of basalt in 247 components (vertical-line 90%, horizontal-rung 0%, blob 2%, median height 8 px x width 3 px), glow mean #82321B h13.3 ok / hole10_2_approach: basalt 134044 px, non-glow mean #291211 h2.3 S0.579 V0.16 median lum 21.0, glow 1.8% of basalt in 93 components (vertical-line 92%, horizontal-rung 1%, blob 2%, median height 13 px x width 3 px), glow mean #9C3B15 h16.7 ok / hole10_3_lavarim: basalt 359650 px, non-glow mean #2D1615 h1.7 S0.529 V0.178 median lum 25.7, glow 1.6% of basalt in 160 components (vertical-line 98%, horizontal-rung 0%, blob 1%, median height 15 px x width 2 px), glow mean #A03A16 h15.6 ok / hole10_aerial (extra aerial, info): basalt 263336 px, non-glow mean #361C1A h2.1 S0.512 V0.213 median lum 34.2, glow 1.3% of basalt in 197 components (vertical-line 97%, horizontal-rung 1%, blob 1%, median height 10 px x width 2 px), glow mean #883117 h13.9 ok |
| SMOKE_SOFT | **FAIL** | (visible dLum p95 >= 8.0, max <= 110.0, edge step p99 <= 6.0 levels/px) hole10_1_tee: smoke changes 41194 px (2.86% of frame), /dLum/ median 13.91 p95 35.93 p99 44.7 max 50.97, edge step p99 1.02 levels/px over 4673 boundary px on a smooth backdrop (all boundary px: 6.21), plume mean #BC7F74, see-through (info) backdrop detail kept 0.779 (corr 0.903, 662 px) ok / hole10_2_approach: smoke changes 96728 px (6.72% of frame), /dLum/ median 30.8 p95 117.45 p99 123.39 max 132.18, edge step p99 2.77 levels/px over 22930 boundary px on a smooth backdrop (all boundary px: 2.72), plume mean #5F4948, see-through (info) backdrop detail kept 0.355 (corr 0.803, 21132 px) FAIL / hole10_3_lavarim: smoke changes 78726 px (5.47% of frame), /dLum/ median 46.88 p95 75.82 p99 79.11 max 81.11, edge step p99 1.32 levels/px over 3235 boundary px on a smooth backdrop (all boundary px: 11.12), plume mean #947679, see-through (info) backdrop detail kept 0.924 (corr 0.959, 608 px) ok / hole10_aerial (extra aerial, info): smoke changes 78219 px (5.43% of frame), /dLum/ median 15.21 p95 107.48 p99 115.48 max 125.25, edge step p99 2.11 levels/px over 16490 boundary px on a smooth backdrop (all boundary px: 2.32), plume mean #8E655C, see-through (info) backdrop detail kept 0.454 (corr 0.877, 7888 px) FAIL |
| NO_PLANT_ON_SEA | **PASS** | installed FBX, ray down from each plant base through every non-plant mesh: hole8: 809 PLANT_ objects (incl. 131 vines): 0 on the sea, 0 floating (no surface within 1 m under the base), support {'ROCK_OUTCROP': 83, 'TERRAIN_': 595}; vines judged by root: 123 attached (root <= 0.6 m from rock/ground), 8 root 0.6..0.89 m off ['PLANT_VINE_L.026', 'PLANT_VINE_M.053', 'PLANT_VINE_M.054', 'PLANT_VINE_M.055', 'PLANT_VINE_M.056', 'PLANT_VINE_M.058', 'PLANT_VINE_M.061', 'PLANT_VINE_M.062'], lowest vine tip 2.91 m above the sea / hole9: 400 PLANT_ objects (incl. 0 vines): 0 on the sea, 0 floating (no surface within 1 m under the base), support {'TERRAIN_': 400} / hole10: 210 PLANT_ objects (incl. 0 vines): 0 on the sea, 0 floating (no surface within 1 m under the base), support {'TERRAIN_': 210} |
| NO_ROCK_STRETCH_2X | **PASS** | installed FBX object scales (open-shell cliff / wall skins carry their stretch in the vertices: postcard_look_verify NO_ROCK_STRETCH_2X judges those): hole8: 83 ROCK_ objects, object scale 0.547..1.999, anisotropy max 1.875 (worst ROCK_OUTCROP_A.000), > 2x: 0 abs / 0 aniso, < 0.4: 0 / hole9: 298 ROCK_ objects, object scale 0.6..1.999, anisotropy max 1.346 (worst ROCK_SEASTACK_A.001), > 2x: 0 abs / 0 aniso, < 0.4: 0 / hole10: 457 ROCK_ objects, object scale 0.558..1.922, anisotropy max 1.286 (worst ROCK_CAIRN_A_BASALT.004), > 2x: 0 abs / 0 aniso, < 0.4: 0 |
| NO_FOAM_STRIP | **PASS** | installed FBX names / materials + surf patches in the aerials: hole8: foam-named objects [], foam materials [], legacy MAT_ [], LK_SURF slots 17 / hole9: foam-named objects [], foam materials [], legacy MAT_ [], LK_SURF slots 61 / hole10: foam-named objects [], foam materials [], legacy MAT_ [], LK_SURF slots None / hole08_aerial: surf patches 9, longest 57 px = 3.6% of the frame height, surf 0.20% of the frame / hole09_aerial: surf patches 14, longest 46 px = 2.9% of the frame height, surf 0.23% of the frame / hole09_2_approach: surf patches 3, longest 45 px = 2.8% of the frame height, surf 0.01% of the frame |
| PATH_UNDER_BALL | **PASS** | installed hole 8 FBX: 2 path meshes, 14433 up-facing vertices, height over the play surface max 1.15 cm / p99 1.15 cm / mean 0.53 cm (limit 1.5 cm, 0 above; game ball radius 5.49 cm; before: up to 11 cm) / hole08_1_tee: ball radius 16.4 px, visible 1144 / 844 expected px (ratio 1.354), ring {'fairway': 0.893}, ball lum 193.0 vs ring 173.7 / hole08_2_approach: ball radius 16.4 px, visible 1117 / 844 expected px (ratio 1.322), ring {'fairway': 0.891}, ball lum 187.1 vs ring 145.9 / hole08_4_pathball: ball radius 16.4 px, visible 1022 / 844 expected px (ratio 1.21), ring {'path': 0.837}, ball lum 193.5 vs ring 160.7 |

## Frame consistency (mask-run frame vs the proof still)

| shot | max channel diff | share of pixels with sum diff > 8 |
|---|---|---|
| hole08_1_tee | 1 | 0.00% |
| hole08_2_approach | 11 | 0.18% |
| hole08_3_arch | 242 | 7.48% |
| hole09_1_tee | 14 | 0.12% |
| hole09_2_approach | 23 | 0.87% |
| hole09_3_ruin | 17 | 4.50% |
| hole10_1_tee | 26 | 0.00% |
| hole10_2_approach | 0 | 0.00% |
| hole10_3_lavarim | 0 | 0.00% |
| hole08_4_pathball | 1 | 0.00% |
| hole08_aerial | 226 | 2.77% |
| hole09_aerial | 86 | 7.15% |
| hole10_aerial | 0 | 0.00% |

## Per shot

### hole08_1_tee
- central lower third: #A6B642 hue 68.6 S 0.636 V 0.716
- fairway (ID mask, lower 60%): 704044 px, mean #9DAE40 hue 69.2 (median 69.6, p10 65.3, p90 73.2) S 0.63 V 0.682, clipped 0.0%
- flatness: lower-60% luminance sd 23.59 (mean 161.0), flat 8 px windows 4.8%, colour cells >= 1%: 20, largest cell 11%, kinds {'fairway': 0.633, 'path': 0.155, 'cliff': 0.012, 'rock': 0.013, 'ocean': 0.017}
- shelf: `{"top2_lum_cut": 223.3, "top2_px": 28808, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.9209, "shelf_px": 21, "shelf_share_of_frame": 1e-05}`
- ball: `{"centre_px": [450, 952.3], "radius_px": 16.4, "expected_px": 844, "visible_px_in_1p3r_disc": 1144, "visible_ratio": 1.354, "ring_categories": {"fairway": 0.893}, "ball_lum_mean": 193.0, "ring_lum_mean": 173.7}`
- surf: `{"id_surf_px": 9, "id_surf_share_of_frame": 1e-05, "diff_surf_px": 35}`

### hole08_2_approach
- central lower third: #A0B13F hue 68.8 S 0.645 V 0.695
- fairway (ID mask, lower 60%): 713760 px, mean #A5B541 hue 68.5 (median 69.0, p10 64.8, p90 72.5) S 0.64 V 0.711, clipped 0.1%
- flatness: lower-60% luminance sd 24.19 (mean 167.5), flat 8 px windows 3.9%, colour cells >= 1%: 21, largest cell 11%, kinds {'fairway': 0.637, 'path': 0.148, 'cliff': 0.011, 'rock': 0.016, 'ocean': 0.016}
- shelf: `{"top2_lum_cut": 229.4, "top2_px": 28825, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.005, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.9091, "shelf_px": 0, "shelf_share_of_frame": 0.0}`
- ball: `{"centre_px": [450, 952.3], "radius_px": 16.4, "expected_px": 844, "visible_px_in_1p3r_disc": 1117, "visible_ratio": 1.322, "ring_categories": {"fairway": 0.891}, "ball_lum_mean": 187.1, "ring_lum_mean": 145.9}`
- surf: `{"id_surf_px": 0, "id_surf_share_of_frame": 0.0, "diff_surf_px": 0}`

### hole08_3_arch
- central lower third: #79794B hue 60.9 S 0.386 V 0.476
- rough (ID mask, lower 60%): 206462 px, mean #80813C hue 61.0 (median 61.1, p10 56.2, p90 68.6) S 0.534 V 0.505, clipped 0.0%
- flatness: lower-60% luminance sd 40.66 (mean 109.8), flat 8 px windows 9.5%, colour cells >= 1%: 28, largest cell 8%, kinds {'rough': 0.144, 'masonry': 0.175, 'rock': 0.123, 'plant': 0.034, 'ocean': 0.111}
- shelf: `{"top2_lum_cut": 253.6, "top2_px": 31868, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.2013, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.7985, "shelf_px": 0, "shelf_share_of_frame": 0.0}`
- surf: `{"id_surf_px": 0, "id_surf_share_of_frame": 0.0, "diff_surf_px": 0}`

### hole09_1_tee
- central lower third: #93A443 hue 70.5 S 0.591 V 0.641
- fairway (ID mask, lower 60%): 861826 px, mean #97A744 hue 70.0 (median 70.2, p10 66.7, p90 73.8) S 0.591 V 0.655, clipped 0.0%
- flatness: lower-60% luminance sd 16.44 (mean 156.5), flat 8 px windows 3.7%, colour cells >= 1%: 16, largest cell 22%, kinds {'fairway': 0.801, 'rough': 0.02}
- shelf: `{"top2_lum_cut": 231.5, "top2_px": 28851, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.9994, "shelf_px": 0, "shelf_share_of_frame": 0.0}`
- ball: `{"centre_px": [450, 952.3], "radius_px": 16.4, "expected_px": 844, "visible_px_in_1p3r_disc": 1120, "visible_ratio": 1.326, "ring_categories": {"fairway": 0.891}, "ball_lum_mean": 193.2, "ring_lum_mean": 162.5}`
- surf: `{"id_surf_px": 0, "id_surf_share_of_frame": 0.0, "diff_surf_px": 0}`

### hole09_2_approach
- central lower third: #85953E hue 71.0 S 0.585 V 0.583
- fairway (ID mask, lower 60%): 861814 px, mean #849540 hue 72.2 (median 72.4, p10 68.4, p90 77.1) S 0.569 V 0.585, clipped 0.0%
- flatness: lower-60% luminance sd 18.32 (mean 139.4), flat 8 px windows 4.9%, colour cells >= 1%: 14, largest cell 14%, kinds {'fairway': 0.774, 'cliff': 0.029, 'ocean': 0.015}
- shelf: `{"top2_lum_cut": 231.4, "top2_px": 29065, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 1.0, "shelf_px": 419, "shelf_share_of_frame": 0.00029, "shelf_mean_rgb": [26.9, 85.8, 110.9], "shelf_hue": 197.9, "shelf_s": 0.757, "shelf_v": 0.435, "shelf_lum_mean": 75.1, "shelf_lum_p95": 79.0, "ocean_lum_mean": 87.7, "ocean_mean_rgb": [39.6, 96.6, 142.0], "shelf_vs_ocean_lum": 0.856, "turquoise_px_share_of_frame": 0.0041, "top2_share_turquoise": 0.0}`
- ball: `{"centre_px": [450, 952.3], "radius_px": 16.4, "expected_px": 844, "visible_px_in_1p3r_disc": 1082, "visible_ratio": 1.281, "ring_categories": {"fairway": 0.891}, "ball_lum_mean": 188.0, "ring_lum_mean": 123.8}`
- surf: `{"id_surf_px": 152, "id_surf_share_of_frame": 0.00011, "id_surf_components": 3, "id_surf_longest_px": 45, "id_surf_longest_share_of_frame_h": 0.028, "diff_surf_px": 312}`

### hole09_3_ruin
- central lower third: #7C7556 hue 49.0 S 0.304 V 0.485
- scrub (ID mask, lower 60%): 648470 px, mean #7C7450 hue 48.5 (median 49.7, p10 42.9, p90 55.7) S 0.351 V 0.486, clipped 0.0%
- flatness: lower-60% luminance sd 23.43 (mean 120.3), flat 8 px windows 0.4%, colour cells >= 1%: 21, largest cell 11%, kinds {'rough': 0.04, 'scrub': 0.636, 'cliff': 0.021, 'masonry': 0.153, 'rock': 0.014, 'plant': 0.037, 'ocean': 0.084}
- shelf: `{"top2_lum_cut": 176.8, "top2_px": 28807, "top2_share_shelf": 0.0, "top2_share_surf": 0.0008, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.0264, "shelf_px": 390, "shelf_share_of_frame": 0.00027, "shelf_mean_rgb": [25.9, 92.5, 111.1], "shelf_hue": 193.1, "shelf_s": 0.767, "shelf_v": 0.436, "shelf_lum_mean": 79.7, "shelf_lum_p95": 81.1, "ocean_lum_mean": 89.4, "ocean_mean_rgb": [41.4, 97.8, 146.4], "shelf_vs_ocean_lum": 0.891, "turquoise_px_share_of_frame": 0.0033, "top2_share_turquoise": 0.0}`
- surf: `{"id_surf_px": 306, "id_surf_share_of_frame": 0.00021, "id_surf_components": 1, "id_surf_longest_px": 33, "id_surf_longest_share_of_frame_h": 0.021, "diff_surf_px": 333}`

### hole10_1_tee
- central lower third: #9EB825 hue 70.6 S 0.8 V 0.721
- fairway (ID mask, lower 60%): 861855 px, mean #A3BC26 hue 70.2 (median 70.4, p10 67.9, p90 72.7) S 0.796 V 0.738, clipped 0.9%
- flatness: lower-60% luminance sd 22.45 (mean 171.9), flat 8 px windows 0.4%, colour cells >= 1%: 18, largest cell 11%, kinds {'fairway': 0.814, 'basalt': 0.1, 'smoke': 0.069}
- shelf: `{"top2_lum_cut": 216.5, "top2_px": 28813, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.0092, "shelf_px": 0, "shelf_share_of_frame": 0.0}`
- lava: `{"pixels": 4645, "share_of_frame": 0.0032, "mean_rgb": [194.3, 77.9, 30.8], "mean_hue": 17.3, "mean_s": 0.841, "mean_v": 0.762, "in_band_hue8_28_s75_v70": 0.9214, "in_band_hue_s_only": 1.0, "dark_v_lt_040": 0.0138, "dark_v_lt_025": 0.0, "v_median": 0.765, "g_ge_250": 0.0, "lum_mean": 99.2, "lum_p10": 78.3, "lum_p90": 132.1, "cream_min_ch_ge_230": 0.0, "dark_components": 4, "dark_largest_px": 21, "dark_median_px": 11, "dark_largest_share_of_lava": 0.0045, "dark_components_ge_400px": 0, "dark_median_elongation": 2.96, "frame_lum_mean": 151.2}`
- basalt: `{"pixels": 144553, "share_of_frame": 0.1004, "glow_px": 4095, "glow_coverage": 0.0283, "base_mean_rgb": [55.7, 28.4, 26.0], "base_hue": 4.8, "base_s": 0.534, "base_v": 0.219, "base_lum_median": 34.3, "base_lum_p90": 44.8, "base_lum_mean": 34.0, "base_s_median": 0.552, "glow_mean_rgb": [130.2, 49.8, 26.8], "glow_mean_hue": 13.3, "glow_cream_share": 0.0, "glow_components": 247, "glow_vertical_line_share": 0.896, "glow_horizontal_rung_share": 0.004, "glow_blob_share": 0.022, "glow_component_height_median_px": 8, "glow_component_width_median_px": 3, "glow_component_height_p90_px": 15}`
- smoke: `{"card_diff_mask_px": 43737, "changed_px_gt1p5": 41194, "frame_share_changed": 0.0286, "delta_lum_median": 13.91, "delta_lum_p95": 35.93, "delta_lum_p99": 44.7, "delta_lum_max": 50.97, "edge_band_px": 6519, "edge_band_px_on_smooth_backdrop": 4673, "edge_step_p99_all_boundary": 6.21, "edge_step_p99_levels_per_px": 1.02, "edge_step_max": 1.55, "smoke_pixel_mean_rgb": [187.6, 127.1, 116.0], "plume_mean_s": 0.38, "through_px": 662, "through_corr": 0.903, "transmission_est": 0.779}`
- ball: `{"centre_px": [450, 952.3], "radius_px": 16.4, "expected_px": 844, "visible_px_in_1p3r_disc": 1131, "visible_ratio": 1.339, "ring_categories": {"fairway": 0.893}, "ball_lum_mean": 152.1, "ring_lum_mean": 188.4}`
- surf: `{"id_surf_px": 0, "id_surf_share_of_frame": 0.0}`

### hole10_2_approach
- central lower third: #94AB2B hue 70.7 S 0.75 V 0.67
- fairway (ID mask, lower 60%): 861930 px, mean #93A82E hue 70.3 (median 70.4, p10 67.6, p90 72.7) S 0.726 V 0.66, clipped 0.0%
- flatness: lower-60% luminance sd 15.14 (mean 154.9), flat 8 px windows 2.4%, colour cells >= 1%: 24, largest cell 9%, kinds {'fairway': 0.665, 'basalt': 0.093, 'lava': 0.124, 'smoke': 0.112}
- shelf: `{"top2_lum_cut": 186.4, "top2_px": 28805, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.0093, "shelf_px": 0, "shelf_share_of_frame": 0.0}`
- lava: `{"pixels": 179100, "share_of_frame": 0.1244, "mean_rgb": [220.2, 84.2, 25.1], "mean_hue": 18.2, "mean_s": 0.886, "mean_v": 0.864, "in_band_hue8_28_s75_v70": 0.9486, "in_band_hue_s_only": 1.0, "dark_v_lt_040": 0.0169, "dark_v_lt_025": 0.0, "v_median": 0.871, "g_ge_250": 0.0, "lum_mean": 108.9, "lum_p10": 85.3, "lum_p90": 146.9, "cream_min_ch_ge_230": 0.0, "dark_components": 138, "dark_largest_px": 159, "dark_median_px": 10, "dark_largest_share_of_lava": 0.0009, "dark_components_ge_400px": 0, "dark_median_elongation": 9.99, "frame_lum_mean": 126.5}`
- basalt: `{"pixels": 134044, "share_of_frame": 0.0931, "glow_px": 2423, "glow_coverage": 0.0181, "base_mean_rgb": [40.8, 18.1, 17.2], "base_hue": 2.3, "base_s": 0.579, "base_v": 0.16, "base_lum_median": 21.0, "base_lum_p90": 32.8, "base_lum_mean": 22.9, "base_s_median": 0.595, "glow_mean_rgb": [156.0, 58.6, 21.1], "glow_mean_hue": 16.7, "glow_cream_share": 0.0, "glow_components": 93, "glow_vertical_line_share": 0.92, "glow_horizontal_rung_share": 0.007, "glow_blob_share": 0.02, "glow_component_height_median_px": 13, "glow_component_width_median_px": 3, "glow_component_height_p90_px": 31}`
- smoke: `{"card_diff_mask_px": 88066, "changed_px_gt1p5": 96728, "frame_share_changed": 0.0672, "delta_lum_median": 30.8, "delta_lum_p95": 117.45, "delta_lum_p99": 123.39, "delta_lum_max": 132.18, "edge_band_px": 33141, "edge_band_px_on_smooth_backdrop": 22930, "edge_step_p99_all_boundary": 2.72, "edge_step_p99_levels_per_px": 2.77, "edge_step_max": 5.18, "smoke_pixel_mean_rgb": [95.1, 72.7, 72.0], "plume_mean_s": 0.326, "through_px": 21132, "through_corr": 0.803, "transmission_est": 0.355}`
- ball: `{"centre_px": [450, 952.3], "radius_px": 16.4, "expected_px": 844, "visible_px_in_1p3r_disc": 1113, "visible_ratio": 1.317, "ring_categories": {"fairway": 0.909}, "ball_lum_mean": 130.5, "ring_lum_mean": 154.1}`
- surf: `{"id_surf_px": 0, "id_surf_share_of_frame": 0.0}`

### hole10_3_lavarim
- central lower third: #D34D16 hue 17.5 S 0.894 V 0.826
- fairway (ID mask, lower 60%): 15556 px, mean #A0B832 hue 71.1 (median 71.4, p10 68.6, p90 74.0) S 0.729 V 0.723, clipped 0.2%
- green (ID mask, lower 60%): 114 px, mean #99A930 hue 67.9 (median 67.8, p10 66.2, p90 69.9) S 0.714 V 0.663, clipped 0.0%
- rough (ID mask, lower 60%): 117050 px, mean #747728 hue 61.7 (median 62.1, p10 58.8, p90 65.1) S 0.666 V 0.465, clipped 0.0%
- flatness: lower-60% luminance sd 39.84 (mean 97.8), flat 8 px windows 12.9%, colour cells >= 1%: 25, largest cell 15%, kinds {'fairway': 0.012, 'rough': 0.081, 'basalt': 0.25, 'lava': 0.416, 'smoke': 0.123}
- shelf: `{"top2_lum_cut": 164.8, "top2_px": 28984, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.5897, "top2_share_other_or_sky": 0.0134, "shelf_px": 0, "shelf_share_of_frame": 0.0}`
- lava: `{"pixels": 598558, "share_of_frame": 0.4157, "mean_rgb": [217.7, 83.2, 25.0], "mean_hue": 18.1, "mean_s": 0.885, "mean_v": 0.854, "in_band_hue8_28_s75_v70": 0.9263, "in_band_hue_s_only": 1.0, "dark_v_lt_040": 0.0287, "dark_v_lt_025": 0.0, "v_median": 0.867, "g_ge_250": 0.0, "lum_mean": 107.6, "lum_p10": 81.6, "lum_p90": 150.1, "cream_min_ch_ge_230": 0.0, "dark_components": 254, "dark_largest_px": 3626, "dark_median_px": 10, "dark_largest_share_of_lava": 0.0061, "dark_components_ge_400px": 8, "dark_median_elongation": 5.9, "frame_lum_mean": 86.5}`
- basalt: `{"pixels": 359650, "share_of_frame": 0.2498, "glow_px": 5657, "glow_coverage": 0.0157, "base_mean_rgb": [45.4, 22.1, 21.4], "base_hue": 1.7, "base_s": 0.529, "base_v": 0.178, "base_lum_median": 25.7, "base_lum_p90": 39.3, "base_lum_mean": 27.0, "base_s_median": 0.6, "glow_mean_rgb": [160.3, 58.0, 22.1], "glow_mean_hue": 15.6, "glow_cream_share": 0.0, "glow_components": 160, "glow_vertical_line_share": 0.98, "glow_horizontal_rung_share": 0.0, "glow_blob_share": 0.007, "glow_component_height_median_px": 15, "glow_component_width_median_px": 2, "glow_component_height_p90_px": 36}`
- smoke: `{"card_diff_mask_px": 76542, "changed_px_gt1p5": 78726, "frame_share_changed": 0.0547, "delta_lum_median": 46.88, "delta_lum_p95": 75.82, "delta_lum_p99": 79.11, "delta_lum_max": 81.11, "edge_band_px": 4459, "edge_band_px_on_smooth_backdrop": 3235, "edge_step_p99_all_boundary": 11.12, "edge_step_p99_levels_per_px": 1.32, "edge_step_max": 2.54, "smoke_pixel_mean_rgb": [147.8, 118.1, 120.9], "plume_mean_s": 0.214, "through_px": 608, "through_corr": 0.959, "transmission_est": 0.924}`
- surf: `{"id_surf_px": 0, "id_surf_share_of_frame": 0.0}`

### hole08_4_pathball
- central lower third: #B9A677 hue 42.9 S 0.357 V 0.724
- fairway (ID mask, lower 60%): 108783 px, mean #BECC49 hue 66.7 (median 66.9, p10 63.8, p90 69.8) S 0.643 V 0.802, clipped 1.2%
- flatness: lower-60% luminance sd 35.41 (mean 165.1), flat 8 px windows 20.3%, colour cells >= 1%: 20, largest cell 7%, kinds {'fairway': 0.218, 'path': 0.564, 'cliff': 0.016, 'rock': 0.013, 'ocean': 0.022}
- shelf: `{"top2_lum_cut": 224.2, "top2_px": 28817, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.7847, "shelf_px": 37, "shelf_share_of_frame": 3e-05}`
- ball: `{"centre_px": [450, 952.3], "radius_px": 16.4, "expected_px": 844, "visible_px_in_1p3r_disc": 1022, "visible_ratio": 1.21, "ring_categories": {"path": 0.837}, "ball_lum_mean": 193.5, "ring_lum_mean": 160.7}`
- surf: `{"id_surf_px": 13, "id_surf_share_of_frame": 1e-05, "diff_surf_px": 52}`

### hole08_aerial
- central lower third: #0B4576 hue 207.2 S 0.91 V 0.463
- fairway (ID mask, lower 60%): 34578 px, mean #A8B750 hue 69.1 (median 69.4, p10 65.9, p90 73.3) S 0.563 V 0.718, clipped 0.0%
- green (ID mask, lower 60%): 1811 px, mean #AEBB73 hue 71.3 (median 72.2, p10 67.9, p90 73.5) S 0.385 V 0.735, clipped 0.0%
- rough (ID mask, lower 60%): 16902 px, mean #888944 hue 60.3 (median 60.8, p10 56.8, p90 64.6) S 0.499 V 0.536, clipped 0.0%
- flatness: lower-60% luminance sd 30.01 (mean 77.0), flat 8 px windows 58.9%, colour cells >= 1%: 21, largest cell 27%, kinds {'fairway': 0.024, 'rough': 0.012, 'cliff': 0.014, 'ocean': 0.614}
- shelf: `{"top2_lum_cut": 234.2, "top2_px": 28910, "top2_share_shelf": 0.0, "top2_share_surf": 0.0002, "top2_share_fall": 0.0, "top2_share_ocean": 0.0347, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.965, "shelf_px": 3281, "shelf_share_of_frame": 0.00228, "shelf_mean_rgb": [33.6, 83.0, 95.7], "shelf_hue": 192.2, "shelf_s": 0.649, "shelf_v": 0.375, "shelf_lum_mean": 73.4, "shelf_lum_p95": 100.6, "ocean_lum_mean": 79.3, "ocean_mean_rgb": [41.3, 85.8, 127.3], "shelf_vs_ocean_lum": 0.926, "turquoise_px_share_of_frame": 0.0024, "top2_share_turquoise": 0.0}`
- surf: `{"id_surf_px": 2839, "id_surf_share_of_frame": 0.00197, "id_surf_components": 9, "id_surf_longest_px": 57, "id_surf_longest_share_of_frame_h": 0.036, "diff_surf_px": 3117}`

### hole09_aerial
- central lower third: #07376B hue 211.4 S 0.932 V 0.421
- fairway (ID mask, lower 60%): 47868 px, mean #8A9C48 hue 73.0 (median 73.6, p10 69.1, p90 77.6) S 0.537 V 0.613, clipped 0.0%
- green (ID mask, lower 60%): 1880 px, mean #96A854 hue 72.6 (median 72.7, p10 69.5, p90 76.5) S 0.499 V 0.66, clipped 0.0%
- rough (ID mask, lower 60%): 54738 px, mean #788142 hue 68.7 (median 69.0, p10 65.5, p90 72.2) S 0.487 V 0.505, clipped 0.0%
- scrub (ID mask, lower 60%): 80917 px, mean #837A58 hue 47.8 (median 48.0, p10 45.3, p90 51.0) S 0.33 V 0.515, clipped 0.0%
- flatness: lower-60% luminance sd 36.5 (mean 72.4), flat 8 px windows 64.1%, colour cells >= 1%: 15, largest cell 32%, kinds {'fairway': 0.037, 'rough': 0.05, 'scrub': 0.076, 'cliff': 0.043, 'ocean': 0.641}
- shelf: `{"top2_lum_cut": 198.0, "top2_px": 29041, "top2_share_shelf": 0.0, "top2_share_surf": 0.0147, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.7959, "shelf_px": 7992, "shelf_share_of_frame": 0.00555, "shelf_mean_rgb": [28.1, 89.3, 110.4], "shelf_hue": 195.4, "shelf_s": 0.745, "shelf_v": 0.433, "shelf_lum_mean": 77.8, "shelf_lum_p95": 100.2, "ocean_lum_mean": 74.5, "ocean_mean_rgb": [38.0, 80.0, 127.7], "shelf_vs_ocean_lum": 1.044, "turquoise_px_share_of_frame": 0.0065, "top2_share_turquoise": 0.0}`
- surf: `{"id_surf_px": 3273, "id_surf_share_of_frame": 0.00227, "id_surf_components": 14, "id_surf_longest_px": 46, "id_surf_longest_share_of_frame_h": 0.029, "diff_surf_px": 3561}`

### hole10_aerial
- central lower third: #BF661E hue 26.7 S 0.841 V 0.749
- fairway (ID mask, lower 60%): 122877 px, mean #9EB62A hue 70.5 (median 70.6, p10 68.0, p90 73.3) S 0.773 V 0.716, clipped 0.1%
- green (ID mask, lower 60%): 4129 px, mean #9FAE32 hue 67.4 (median 66.8, p10 65.5, p90 70.1) S 0.712 V 0.683, clipped 0.0%
- rough (ID mask, lower 60%): 70170 px, mean #777926 hue 61.5 (median 61.9, p10 58.9, p90 64.3) S 0.684 V 0.474, clipped 0.0%
- flatness: lower-60% luminance sd 46.1 (mean 102.6), flat 8 px windows 2.5%, colour cells >= 1%: 29, largest cell 11%, kinds {'fairway': 0.085, 'rough': 0.049, 'basalt': 0.183, 'lava': 0.338, 'smoke': 0.159}
- shelf: `{"top2_lum_cut": 183.1, "top2_px": 28858, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.0007, "shelf_px": 0, "shelf_share_of_frame": 0.0}`
- lava: `{"pixels": 486688, "share_of_frame": 0.338, "mean_rgb": [216.4, 83.5, 26.3], "mean_hue": 18.1, "mean_s": 0.878, "mean_v": 0.849, "in_band_hue8_28_s75_v70": 0.9403, "in_band_hue_s_only": 1.0, "dark_v_lt_040": 0.0189, "dark_v_lt_025": 0.0, "v_median": 0.859, "g_ge_250": 0.0, "lum_mean": 107.7, "lum_p10": 83.5, "lum_p90": 147.7, "cream_min_ch_ge_230": 0.0, "dark_components": 356, "dark_largest_px": 220, "dark_median_px": 11, "dark_largest_share_of_lava": 0.0005, "dark_components_ge_400px": 0, "dark_median_elongation": 3.14, "frame_lum_mean": 96.4}`
- basalt: `{"pixels": 263336, "share_of_frame": 0.1829, "glow_px": 3375, "glow_coverage": 0.0128, "base_mean_rgb": [54.3, 27.5, 26.5], "base_hue": 2.1, "base_s": 0.512, "base_v": 0.213, "base_lum_median": 34.2, "base_lum_p90": 45.0, "base_lum_mean": 33.1, "base_s_median": 0.591, "glow_mean_rgb": [135.8, 49.0, 22.7], "glow_mean_hue": 13.9, "glow_cream_share": 0.0, "glow_components": 197, "glow_vertical_line_share": 0.971, "glow_horizontal_rung_share": 0.007, "glow_blob_share": 0.013, "glow_component_height_median_px": 10, "glow_component_width_median_px": 2, "glow_component_height_p90_px": 18}`
- smoke: `{"card_diff_mask_px": 73670, "changed_px_gt1p5": 78219, "frame_share_changed": 0.0543, "delta_lum_median": 15.21, "delta_lum_p95": 107.48, "delta_lum_p99": 115.48, "delta_lum_max": 125.25, "edge_band_px": 21954, "edge_band_px_on_smooth_backdrop": 16490, "edge_step_p99_all_boundary": 2.32, "edge_step_p99_levels_per_px": 2.11, "edge_step_max": 5.26, "smoke_pixel_mean_rgb": [142.1, 100.7, 91.8], "plume_mean_s": 0.362, "through_px": 7888, "through_corr": 0.877, "transmission_est": 0.454}`
- ball: `{"centre_px": [1089.9, 3280.8], "radius_px": 3.12, "expected_px": 30, "visible_px_in_1p3r_disc": 0, "visible_ratio": 0.0, "ring_categories": {}}`
- surf: `{"id_surf_px": 0, "id_surf_share_of_frame": 0.0}`

## Flat baseline stills (the paused pass, for contrast)

| still | lower-60% lum sd | flat windows |
|---|---|---|
| hole08_layup.jpg | 6.42 | 99% |
| hole08_midpad.jpg | 6.58 | 99% |
| hole08_tee.jpg | 4.18 | 99% |
| hole09_fairway.jpg | 6.9 | 99% |
| hole09_ridge.jpg | 0.44 | 100% |
| hole09_tee.jpg | 1.48 | 100% |
| hole10_approach.jpg | 0.65 | 100% |
| hole10_rim.jpg | 4.55 | 99% |
| hole10_tee.jpg | 1.57 | 100% |
