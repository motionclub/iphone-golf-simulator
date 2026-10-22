# POSTCARD_LOOK area I: measurements from the Game-view pixels (and the installed FBX)

Stills: `work/postcard-look/v2/unity_r3/stills9_c` (900x1600, pipeline asset **TennisURP**, quality level 2, Unity 6000.3.24f1). Masks: `proof/masks/` (PostcardProofMasks, same frames; ID render = exact per-material masks).
Mask statistics read `masks/<k>/<name>.full.png`; it equals the proof still except for animated water (table below). Thresholds: `measure.py` THRESH (the user's lines, the runtime gates' own limits). Re-run: `run_proof.sh metrics`.

## Gates

| gate | result | numbers |
|---|---|---|
| GRASS_HUE_GAMEVIEW hole08 | **PASS** | hole08_1_tee: central lower third mean #A7B742 h68.1 S0.638 V0.717; fairway+green px 701531 mean hue 69.0 (median 69.5), clipped(any ch>=250) 0.0%; hole08_2_approach: central lower third mean #A0B13F h68.8 S0.645 V0.695; fairway+green px 713760 mean hue 68.5 (median 69.0), clipped(any ch>=250) 0.1%; target fairway/green h60..76 (stills h64-73), clip <= 5% / info: hole08_3_arch rough 327729px h63.9 S0.532 V0.468 |
| GRASS_HUE_GAMEVIEW hole09 | **PASS** | hole09_1_tee: central lower third mean #93A443 h70.5 S0.591 V0.641; fairway+green px 861826 mean hue 70.0 (median 70.2), clipped(any ch>=250) 0.0%; hole09_2_approach: central lower third mean #85953E h71.0 S0.585 V0.583; fairway+green px 861814 mean hue 72.2 (median 72.4), clipped(any ch>=250) 0.0%; target fairway/green h60..76 (stills h64-73), clip <= 5% / info: hole09_3_ruin scrub 633839px h48.4 S0.351 V0.487 |
| GRASS_HUE_GAMEVIEW hole10 | **PASS** | hole10_1_tee: central lower third mean #A2B625 h68.2 S0.797 V0.714; fairway+green px 849959 mean hue 67.7 (median 67.9), clipped(any ch>=250) 0.7%; hole10_2_approach: central lower third mean #98A92B h68.1 S0.747 V0.664; fairway+green px 861930 mean hue 67.7 (median 67.8), clipped(any ch>=250) 0.0%; target fairway/green h60..76 (stills h64-73), clip <= 5% / info: hole10_3_lavarim rough 117050px h61.2 S0.665 V0.465 |
| NOT_FLAT_PER_STILL | **PASS** | (sd >= 12, largest colour cell <= 50%, address stills flat windows <= 15%; failing: none) hole08_1_tee: lower-60% lum sd 23.63, flat 8px windows 4.4%, largest colour cell 11%, 20 colour cells >= 1% ok / hole08_2_approach: lower-60% lum sd 24.19, flat 8px windows 3.9%, largest colour cell 11%, 21 colour cells >= 1% ok / hole08_3_arch: lower-60% lum sd 41.01, flat 8px windows 8.7% (landmark: info), largest colour cell 8%, 32 colour cells >= 1% ok / hole09_1_tee: lower-60% lum sd 16.44, flat 8px windows 3.7%, largest colour cell 22%, 16 colour cells >= 1% ok / hole09_2_approach: lower-60% lum sd 18.32, flat 8px windows 4.9%, largest colour cell 14%, 14 colour cells >= 1% ok / hole09_3_ruin: lower-60% lum sd 23.78, flat 8px windows 1.2% (landmark: info), largest colour cell 10%, 23 colour cells >= 1% ok / hole10_1_tee: lower-60% lum sd 23.12, flat 8px windows 0.4%, largest colour cell 13%, 16 colour cells >= 1% ok / hole10_2_approach: lower-60% lum sd 15.04, flat 8px windows 2.5%, largest colour cell 12%, 22 colour cells >= 1% ok / hole10_3_lavarim: lower-60% lum sd 39.63, flat 8px windows 12.9% (landmark: info), largest colour cell 15%, 24 colour cells >= 1% ok; flat baseline stills for contrast: hole08_layup sd 6.42 flat 99% cell 44%, hole08_midpad sd 6.58 flat 99% cell 32%, hole08_tee sd 4.18 flat 99% cell 58%, hole09_fairway sd 6.9 flat 99% cell 45%, hole09_ridge sd 0.44 flat 100% cell 60%, hole09_tee sd 1.48 flat 100% cell 65%, hole10_approach sd 0.65 flat 100% cell 64%, hole10_rim sd 4.55 flat 99% cell 57%, hole10_tee sd 1.57 flat 100% cell 63% |
| SHELF_NOT_LOUDEST | **PASS** | (shelf <= 10% of the brightest 2%, <= 1.3 x the open sea) hole08_1_tee: shelf 21 px (< 300: not measurable here) / hole08_2_approach: shelf 0 px (< 300: not measurable here) / hole08_3_arch: shelf 0 px (< 300: not measurable here) / hole09_1_tee: shelf 0 px (< 300: not measurable here) / hole09_2_approach: shelf 419 px = 0.03% of the frame, mean #1B566F h197.9 V0.435 lum 75.1, ocean beside it lum 87.8, ratio 0.855, shelf = 0.0% and turquoise = 0.0% of the brightest 2% (lum >= 231.4), brightest 2% is sky/other 100.0%, surf 0.0%, ocean 0.0% ok / hole09_3_ruin: shelf 394 px = 0.03% of the frame, mean #1A5D70 h192.9 V0.438 lum 80.4, ocean beside it lum 90.2, ratio 0.891, shelf = 0.0% and turquoise = 0.0% of the brightest 2% (lum >= 181.7), brightest 2% is sky/other 2.06%, surf 0.1%, ocean 0.0% ok |
| LAVA_ORANGE_AND_BRIGHT | **FAIL** | (in band >= 85%, G>=250 <= 5%, dark V<.40 <= 15%, mean V >= 0.7; crater.jpg pool (212,62,14) h15 S.93 V.83) hole10_1_tee: lava 4645 px (0.3% of frame) mean #BE522D h15.1 S0.763 V0.745, in band (h8-28 S>=.75 V>=.7) 65.1% (h+S only 65.2%), dark V<.40 1.8%, G>=250 0.0%, cream 0.00%, dark components 4 largest 28 px (0.60% of the lava) FAIL / hole10_2_approach: lava 177790 px (12.3% of frame) mean #DC5419 h18.1 S0.885 V0.863, in band (h8-28 S>=.75 V>=.7) 94.8% (h+S only 100.0%), dark V<.40 1.7%, G>=250 0.0%, cream 0.00%, dark components 138 largest 159 px (0.09% of the lava) ok / hole10_3_lavarim: lava 598099 px (41.5% of frame) mean #DA5319 h18.1 S0.884 V0.854, in band (h8-28 S>=.75 V>=.7) 92.6% (h+S only 100.0%), dark V<.40 2.9%, G>=250 0.0%, cream 0.00%, dark components 254 largest 3626 px (0.61% of the lava) ok |
| BASALT_JOINTS | **FAIL** | (glow <= 20% of the basalt, non-glow median lum <= 55.0, non-glow mean S <= 0.25, glow in vertical lines 50..80%, horizontal rungs <= 20%, branching joints >= 3.0 junctions per 100 skeleton px; crater.jpg basalt (26,25,29) S .10) hole10_1_tee: basalt 136143 px, non-glow mean #282325 h337.9 S0.128 V0.156 median lum 35.5, glow 1.8% of basalt in 151 components (vertical-line 92%, horizontal-rung 1%, blob 1%, median height 8 px x width 2 px), glow mean #863A26 h12.5 FAIL / hole10_2_approach: basalt 135547 px, non-glow mean #1C1819 h343.9 S0.17 V0.112 median lum 23.5, glow 2.1% of basalt in 90 components (vertical-line 93%, horizontal-rung 0%, blob 3%, median height 13 px x width 2 px), glow mean #99401C h17.2 FAIL / hole10_3_lavarim: basalt 360143 px, non-glow mean #201C1E h323.1 S0.118 V0.124 median lum 28.0, glow 1.5% of basalt in 155 components (vertical-line 97%, horizontal-rung 0%, blob 1%, median height 15 px x width 2 px), glow mean #A3401D h15.7 FAIL / joint network (all proof shots): 73 skeleton junction clusters on 5749 skeleton px = 1.27 per 100 px (>= 3.0; crater.jpg wall crops 8.3-8.8) FAIL |
| SMOKE_SOFT | **PASS** | (visible dLum p95 >= 8.0, max <= 110.0, edge step p99 <= 6.0 levels/px) hole10_1_tee: smoke changes 54105 px (3.76% of frame), /dLum/ median 10.13 p95 37.07 p99 54.36 max 63.28, edge step p99 3.05 levels/px over 4932 boundary px on a smooth backdrop (all boundary px: 7.43; info, boundary px with a clean backdrop within 4 px: p99 0.54 over 3439 px), plume mean #A86C60, see-through (info) backdrop detail kept 0.56 (corr 0.968, 7761 px) ok / hole10_2_approach: smoke changes 57293 px (3.98% of frame), /dLum/ median 42.35 p95 89.57 p99 94.28 max 101.57, edge step p99 1.02 levels/px over 2741 boundary px on a smooth backdrop (all boundary px: 1.46; info, boundary px with a clean backdrop within 4 px: p99 1.08 over 381 px), plume mean #5A5051, see-through (info) backdrop detail kept 0.517 (corr 0.906, 16901 px) ok / hole10_3_lavarim: smoke changes 69623 px (4.83% of frame), /dLum/ median 28.61 p95 54.89 p99 58.11 max 60.11, edge step p99 0.88 levels/px over 2808 boundary px on a smooth backdrop (all boundary px: 7.93; info, boundary px with a clean backdrop within 4 px: p99 0.66 over 2521 px), plume mean #88676B, see-through (info) backdrop detail kept None (corr None, None px) ok |
| NO_PLANT_ON_SEA | **PASS** | installed FBX, ray down from each plant base through every non-plant mesh: hole8: 809 PLANT_ objects (incl. 131 vines): 0 on the sea, 0 floating (no surface within 1 m under the base), support {'ROCK_OUTCROP': 83, 'TERRAIN_': 595}; vines judged by root: 123 attached (root <= 0.6 m from rock/ground), 8 root 0.6..0.86 m off ['PLANT_VINE_L.026', 'PLANT_VINE_L.041', 'PLANT_VINE_L.042', 'PLANT_VINE_M.053', 'PLANT_VINE_M.054', 'PLANT_VINE_M.055', 'PLANT_VINE_M.060', 'PLANT_VINE_M.061'], lowest vine tip 2.91 m above the sea / hole9: 400 PLANT_ objects (incl. 0 vines): 0 on the sea, 0 floating (no surface within 1 m under the base), support {'TERRAIN_': 400} / hole10: 210 PLANT_ objects (incl. 0 vines): 0 on the sea, 0 floating (no surface within 1 m under the base), support {'TERRAIN_': 210} |
| NO_ROCK_STRETCH_2X | **PASS** | installed FBX object scales (open-shell cliff / wall skins carry their stretch in the vertices: postcard_look_verify NO_ROCK_STRETCH_2X judges those): hole8: 83 ROCK_ objects, object scale 0.547..1.999, anisotropy max 1.875 (worst ROCK_OUTCROP_A.000), > 2x: 0 abs / 0 aniso, < 0.4: 0 / hole9: 298 ROCK_ objects, object scale 0.6..1.999, anisotropy max 1.346 (worst ROCK_SEASTACK_A.001), > 2x: 0 abs / 0 aniso, < 0.4: 0 / hole10: 457 ROCK_ objects, object scale 0.558..1.922, anisotropy max 1.286 (worst ROCK_CAIRN_A_BASALT.004), > 2x: 0 abs / 0 aniso, < 0.4: 0 |
| NO_FOAM_STRIP | **PASS** | installed FBX names / materials + surf patches in the aerials: hole8: foam-named objects [], foam materials [], legacy MAT_ [], LK_SURF slots 17 / hole9: foam-named objects [], foam materials [], legacy MAT_ [], LK_SURF slots 61 / hole10: foam-named objects [], foam materials [], legacy MAT_ [], LK_SURF slots None / hole09_2_approach: surf patches 3, longest 45 px = 2.8% of the frame height, surf 0.01% of the frame |
| PATH_UNDER_BALL | **PASS** | installed hole 8 FBX: 2 path meshes, 14506 up-facing vertices, height over the play surface max 1.15 cm / p99 1.15 cm / mean 0.56 cm (limit 1.5 cm, 0 above; game ball radius 5.49 cm; before: up to 11 cm) / hole08_1_tee: ball radius 16.4 px, visible 1150 / 844 expected px (ratio 1.361), ring {'fairway': 0.893}, ball lum 193.7 vs ring 171.6 / hole08_2_approach: ball radius 16.4 px, visible 1117 / 844 expected px (ratio 1.322), ring {'fairway': 0.891}, ball lum 187.1 vs ring 145.9 |

## Frame consistency (mask-run frame vs the proof still)

| shot | max channel diff | share of pixels with sum diff > 8 |
|---|---|---|
| hole08_1_tee | 1 | 0.00% |
| hole08_2_approach | 6 | 0.04% |
| hole08_3_arch | 240 | 6.02% |
| hole09_1_tee | 10 | 0.07% |
| hole09_2_approach | 21 | 0.70% |
| hole09_3_ruin | 15 | 3.82% |
| hole10_1_tee | 1 | 0.00% |
| hole10_2_approach | 0 | 0.00% |
| hole10_3_lavarim | 0 | 0.00% |

## Per shot

### hole08_1_tee
- central lower third: #A7B742 hue 68.1 S 0.638 V 0.717
- fairway (ID mask, lower 60%): 701531 px, mean #9DAE40 hue 69.0 (median 69.5, p10 65.2, p90 73.1) S 0.631 V 0.681, clipped 0.0%
- flatness: lower-60% luminance sd 23.63 (mean 161.3), flat 8 px windows 4.4%, colour cells >= 1%: 20, largest cell 11%, kinds {'fairway': 0.631, 'path': 0.157, 'cliff': 0.012, 'rock': 0.012, 'ocean': 0.016}
- shelf: `{"top2_lum_cut": 223.3, "top2_px": 28813, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.9207, "shelf_px": 21, "shelf_share_of_frame": 1e-05}`
- ball: `{"centre_px": [450, 952.3], "radius_px": 16.4, "expected_px": 844, "visible_px_in_1p3r_disc": 1150, "visible_ratio": 1.361, "ring_categories": {"fairway": 0.893}, "ball_lum_mean": 193.7, "ring_lum_mean": 171.6}`
- surf: `{"id_surf_px": 9, "id_surf_share_of_frame": 1e-05, "diff_surf_px": 35}`

### hole08_2_approach
- central lower third: #A0B13F hue 68.8 S 0.645 V 0.695
- fairway (ID mask, lower 60%): 713760 px, mean #A5B541 hue 68.5 (median 69.0, p10 64.8, p90 72.5) S 0.64 V 0.711, clipped 0.1%
- flatness: lower-60% luminance sd 24.19 (mean 167.5), flat 8 px windows 3.9%, colour cells >= 1%: 21, largest cell 11%, kinds {'fairway': 0.637, 'path': 0.148, 'cliff': 0.011, 'rock': 0.013, 'ocean': 0.016}
- shelf: `{"top2_lum_cut": 229.4, "top2_px": 28826, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.005, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.909, "shelf_px": 0, "shelf_share_of_frame": 0.0}`
- ball: `{"centre_px": [450, 952.3], "radius_px": 16.4, "expected_px": 844, "visible_px_in_1p3r_disc": 1117, "visible_ratio": 1.322, "ring_categories": {"fairway": 0.891}, "ball_lum_mean": 187.1, "ring_lum_mean": 145.9}`
- surf: `{"id_surf_px": 0, "id_surf_share_of_frame": 0.0, "diff_surf_px": 0}`

### hole08_3_arch
- central lower third: #797B40 hue 61.3 S 0.479 V 0.481
- rough (ID mask, lower 60%): 327729 px, mean #737838 hue 63.9 (median 64.2, p10 57.1, p90 75.0) S 0.532 V 0.468, clipped 0.0%
- flatness: lower-60% luminance sd 41.01 (mean 110.4), flat 8 px windows 8.7%, colour cells >= 1%: 32, largest cell 8%, kinds {'rough': 0.228, 'masonry': 0.174, 'rock': 0.037, 'plant': 0.034, 'ocean': 0.112}
- shelf: `{"top2_lum_cut": 253.6, "top2_px": 31892, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.2018, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.798, "shelf_px": 0, "shelf_share_of_frame": 0.0}`
- surf: `{"id_surf_px": 0, "id_surf_share_of_frame": 0.0, "diff_surf_px": 0}`

### hole09_1_tee
- central lower third: #93A443 hue 70.5 S 0.591 V 0.641
- fairway (ID mask, lower 60%): 861826 px, mean #97A744 hue 70.0 (median 70.2, p10 66.7, p90 73.8) S 0.591 V 0.655, clipped 0.0%
- flatness: lower-60% luminance sd 16.44 (mean 156.5), flat 8 px windows 3.7%, colour cells >= 1%: 16, largest cell 22%, kinds {'fairway': 0.801, 'rough': 0.02}
- shelf: `{"top2_lum_cut": 231.5, "top2_px": 28820, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.9994, "shelf_px": 0, "shelf_share_of_frame": 0.0}`
- ball: `{"centre_px": [450, 952.3], "radius_px": 16.4, "expected_px": 844, "visible_px_in_1p3r_disc": 1120, "visible_ratio": 1.326, "ring_categories": {"fairway": 0.891}, "ball_lum_mean": 193.2, "ring_lum_mean": 162.5}`
- surf: `{"id_surf_px": 0, "id_surf_share_of_frame": 0.0, "diff_surf_px": 0}`

### hole09_2_approach
- central lower third: #85953E hue 71.0 S 0.585 V 0.583
- fairway (ID mask, lower 60%): 861814 px, mean #849540 hue 72.2 (median 72.4, p10 68.4, p90 77.1) S 0.569 V 0.585, clipped 0.0%
- flatness: lower-60% luminance sd 18.32 (mean 139.4), flat 8 px windows 4.9%, colour cells >= 1%: 14, largest cell 14%, kinds {'fairway': 0.774, 'cliff': 0.029, 'ocean': 0.015}
- shelf: `{"top2_lum_cut": 231.4, "top2_px": 29051, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 1.0, "shelf_px": 419, "shelf_share_of_frame": 0.00029, "shelf_mean_rgb": [26.9, 85.8, 111.0], "shelf_hue": 197.9, "shelf_s": 0.758, "shelf_v": 0.435, "shelf_lum_mean": 75.1, "shelf_lum_p95": 79.0, "ocean_lum_mean": 87.8, "ocean_mean_rgb": [39.8, 96.6, 142.0], "shelf_vs_ocean_lum": 0.855, "turquoise_px_share_of_frame": 0.0042, "top2_share_turquoise": 0.0}`
- ball: `{"centre_px": [450, 952.3], "radius_px": 16.4, "expected_px": 844, "visible_px_in_1p3r_disc": 1082, "visible_ratio": 1.281, "ring_categories": {"fairway": 0.891}, "ball_lum_mean": 188.0, "ring_lum_mean": 123.8}`
- surf: `{"id_surf_px": 152, "id_surf_share_of_frame": 0.00011, "id_surf_components": 3, "id_surf_longest_px": 45, "id_surf_longest_share_of_frame_h": 0.028, "diff_surf_px": 312}`

### hole09_3_ruin
- central lower third: #7C7556 hue 49.0 S 0.309 V 0.488
- scrub (ID mask, lower 60%): 633839 px, mean #7C7450 hue 48.4 (median 49.6, p10 42.9, p90 55.6) S 0.351 V 0.487, clipped 0.0%
- flatness: lower-60% luminance sd 23.78 (mean 121.7), flat 8 px windows 1.2%, colour cells >= 1%: 23, largest cell 10%, kinds {'rough': 0.041, 'scrub': 0.616, 'cliff': 0.02, 'masonry': 0.166, 'rock': 0.013, 'plant': 0.04, 'ocean': 0.088}
- shelf: `{"top2_lum_cut": 181.7, "top2_px": 28801, "top2_share_shelf": 0.0, "top2_share_surf": 0.0006, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.0206, "shelf_px": 394, "shelf_share_of_frame": 0.00027, "shelf_mean_rgb": [26.0, 93.4, 111.8], "shelf_hue": 192.9, "shelf_s": 0.767, "shelf_v": 0.438, "shelf_lum_mean": 80.4, "shelf_lum_p95": 81.9, "ocean_lum_mean": 90.2, "ocean_mean_rgb": [42.8, 98.6, 146.8], "shelf_vs_ocean_lum": 0.891, "turquoise_px_share_of_frame": 0.0033, "top2_share_turquoise": 0.0}`
- surf: `{"id_surf_px": 319, "id_surf_share_of_frame": 0.00022, "id_surf_components": 1, "id_surf_longest_px": 34, "id_surf_longest_share_of_frame_h": 0.021, "diff_surf_px": 340}`

### hole10_1_tee
- central lower third: #A2B625 hue 68.2 S 0.797 V 0.714
- fairway (ID mask, lower 60%): 849959 px, mean #A7BA26 hue 67.7 (median 67.9, p10 65.4, p90 70.4) S 0.793 V 0.731, clipped 0.7%
- flatness: lower-60% luminance sd 23.12 (mean 171.1), flat 8 px windows 0.4%, colour cells >= 1%: 16, largest cell 13%, kinds {'fairway': 0.782, 'path': 0.03, 'basalt': 0.095, 'smoke': 0.075}
- shelf: `{"top2_lum_cut": 216.2, "top2_px": 28826, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.0096, "shelf_px": 0, "shelf_share_of_frame": 0.0}`
- lava: `{"pixels": 4645, "share_of_frame": 0.0032, "mean_rgb": [190.1, 81.5, 45.1], "mean_hue": 15.1, "mean_s": 0.763, "mean_v": 0.745, "in_band_hue8_28_s75_v70": 0.6512, "in_band_hue_s_only": 0.6521, "dark_v_lt_040": 0.0181, "dark_v_lt_025": 0.0, "v_median": 0.745, "g_ge_250": 0.0, "lum_mean": 102.0, "lum_p10": 82.1, "lum_p90": 133.4, "cream_min_ch_ge_230": 0.0, "dark_components": 4, "dark_largest_px": 28, "dark_median_px": 12, "dark_largest_share_of_lava": 0.006, "dark_components_ge_400px": 0, "dark_median_elongation": 2.12, "frame_lum_mean": 150.5}`
- basalt: `{"pixels": 136143, "share_of_frame": 0.0945, "glow_px": 2426, "glow_coverage": 0.0178, "base_mean_rgb": [39.9, 34.8, 36.7], "base_hue": 337.9, "base_s": 0.128, "base_v": 0.156, "base_lum_median": 35.5, "base_lum_p90": 47.2, "base_lum_mean": 36.0, "base_s_median": 0.106, "glow_mean_rgb": [133.6, 58.1, 38.2], "glow_mean_hue": 12.5, "glow_cream_share": 0.0, "glow_skeleton_px": 1353, "glow_junction_clusters": 35, "glow_components": 151, "glow_vertical_line_share": 0.925, "glow_horizontal_rung_share": 0.006, "glow_blob_share": 0.009, "glow_component_height_median_px": 8, "glow_component_width_median_px": 2, "glow_component_height_p90_px": 15}`
- smoke: `{"card_diff_mask_px": 56289, "changed_px_gt1p5": 54105, "frame_share_changed": 0.0376, "delta_lum_median": 10.13, "delta_lum_p95": 37.07, "delta_lum_p99": 54.36, "delta_lum_max": 63.28, "edge_clean_backdrop_px": 3439, "edge_step_p99_clean_backdrop_info": 0.54, "edge_band_px": 6493, "edge_band_px_on_smooth_backdrop": 4932, "edge_step_p99_all_boundary": 7.43, "edge_step_p99_levels_per_px": 3.05, "edge_step_max": 21.47, "smoke_pixel_mean_rgb": [168.0, 107.7, 96.0], "plume_mean_s": 0.39, "through_px": 7761, "through_corr": 0.968, "transmission_est": 0.56}`
- ball: `{"centre_px": [450, 952.3], "radius_px": 16.4, "expected_px": 844, "visible_px_in_1p3r_disc": 1129, "visible_ratio": 1.336, "ring_categories": {"fairway": 0.893}, "ball_lum_mean": 171.8, "ring_lum_mean": 188.2}`
- surf: `{"id_surf_px": 0, "id_surf_share_of_frame": 0.0}`

### hole10_2_approach
- central lower third: #98A92B hue 68.1 S 0.747 V 0.664
- fairway (ID mask, lower 60%): 861930 px, mean #97A72E hue 67.7 (median 67.8, p10 65.0, p90 70.3) S 0.723 V 0.654, clipped 0.0%
- flatness: lower-60% luminance sd 15.04 (mean 154.7), flat 8 px windows 2.5%, colour cells >= 1%: 22, largest cell 12%, kinds {'fairway': 0.665, 'basalt': 0.094, 'lava': 0.123, 'smoke': 0.112}
- shelf: `{"top2_lum_cut": 186.2, "top2_px": 28804, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.0097, "shelf_px": 0, "shelf_share_of_frame": 0.0}`
- lava: `{"pixels": 177790, "share_of_frame": 0.1235, "mean_rgb": [220.2, 84.3, 25.4], "mean_hue": 18.1, "mean_s": 0.885, "mean_v": 0.863, "in_band_hue8_28_s75_v70": 0.9484, "in_band_hue_s_only": 1.0, "dark_v_lt_040": 0.0169, "dark_v_lt_025": 0.0, "v_median": 0.867, "g_ge_250": 0.0, "lum_mean": 108.9, "lum_p10": 85.3, "lum_p90": 146.9, "cream_min_ch_ge_230": 0.0, "dark_components": 138, "dark_largest_px": 159, "dark_median_px": 10, "dark_largest_share_of_lava": 0.0009, "dark_components_ge_400px": 0, "dark_median_elongation": 9.99, "frame_lum_mean": 125.5}`
- basalt: `{"pixels": 135547, "share_of_frame": 0.0941, "glow_px": 2880, "glow_coverage": 0.0212, "base_mean_rgb": [28.5, 23.6, 24.9], "base_hue": 343.9, "base_s": 0.17, "base_v": 0.112, "base_lum_median": 23.5, "base_lum_p90": 34.9, "base_lum_mean": 24.8, "base_s_median": 0.125, "glow_mean_rgb": [153.3, 63.8, 27.9], "glow_mean_hue": 17.2, "glow_cream_share": 0.0, "glow_skeleton_px": 1468, "glow_junction_clusters": 20, "glow_components": 90, "glow_vertical_line_share": 0.926, "glow_horizontal_rung_share": 0.0, "glow_blob_share": 0.028, "glow_component_height_median_px": 13, "glow_component_width_median_px": 2, "glow_component_height_p90_px": 32}`
- smoke: `{"card_diff_mask_px": 55146, "changed_px_gt1p5": 57293, "frame_share_changed": 0.0398, "delta_lum_median": 42.35, "delta_lum_p95": 89.57, "delta_lum_p99": 94.28, "delta_lum_max": 101.57, "edge_clean_backdrop_px": 381, "edge_step_p99_clean_backdrop_info": 1.08, "edge_band_px": 3827, "edge_band_px_on_smooth_backdrop": 2741, "edge_step_p99_all_boundary": 1.46, "edge_step_p99_levels_per_px": 1.02, "edge_step_max": 1.56, "smoke_pixel_mean_rgb": [90.0, 79.6, 80.8], "plume_mean_s": 0.109, "through_px": 16901, "through_corr": 0.906, "transmission_est": 0.517}`
- ball: `{"centre_px": [450, 952.3], "radius_px": 16.4, "expected_px": 844, "visible_px_in_1p3r_disc": 1110, "visible_ratio": 1.314, "ring_categories": {"fairway": 0.909}, "ball_lum_mean": 151.4, "ring_lum_mean": 153.8}`
- surf: `{"id_surf_px": 0, "id_surf_share_of_frame": 0.0}`

### hole10_3_lavarim
- central lower third: #D34D16 hue 17.5 S 0.894 V 0.826
- fairway (ID mask, lower 60%): 15556 px, mean #A4B732 hue 68.6 (median 68.8, p10 66.1, p90 71.5) S 0.726 V 0.717, clipped 0.1%
- green (ID mask, lower 60%): 114 px, mean #99A430 hue 65.8 (median 65.8, p10 64.3, p90 67.6) S 0.705 V 0.642, clipped 0.0%
- rough (ID mask, lower 60%): 117050 px, mean #757628 hue 61.2 (median 61.6, p10 58.4, p90 64.6) S 0.665 V 0.465, clipped 0.0%
- flatness: lower-60% luminance sd 39.63 (mean 97.9), flat 8 px windows 12.9%, colour cells >= 1%: 24, largest cell 15%, kinds {'fairway': 0.012, 'rough': 0.081, 'basalt': 0.25, 'lava': 0.415, 'smoke': 0.123}
- shelf: `{"top2_lum_cut": 164.8, "top2_px": 29146, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.5862, "top2_share_other_or_sky": 0.0132, "shelf_px": 0, "shelf_share_of_frame": 0.0}`
- lava: `{"pixels": 598099, "share_of_frame": 0.4153, "mean_rgb": [217.7, 83.3, 25.3], "mean_hue": 18.1, "mean_s": 0.884, "mean_v": 0.854, "in_band_hue8_28_s75_v70": 0.9263, "in_band_hue_s_only": 1.0, "dark_v_lt_040": 0.0287, "dark_v_lt_025": 0.0, "v_median": 0.867, "g_ge_250": 0.0, "lum_mean": 107.6, "lum_p10": 81.6, "lum_p90": 150.1, "cream_min_ch_ge_230": 0.0, "dark_components": 254, "dark_largest_px": 3626, "dark_median_px": 10, "dark_largest_share_of_lava": 0.0061, "dark_components_ge_400px": 8, "dark_median_elongation": 5.9, "frame_lum_mean": 86.1}`
- basalt: `{"pixels": 360143, "share_of_frame": 0.2501, "glow_px": 5325, "glow_coverage": 0.0148, "base_mean_rgb": [31.6, 27.9, 30.2], "base_hue": 323.1, "base_s": 0.118, "base_v": 0.124, "base_lum_median": 28.0, "base_lum_p90": 40.9, "base_lum_mean": 28.9, "base_s_median": 0.125, "glow_mean_rgb": [162.7, 63.9, 29.1], "glow_mean_hue": 15.7, "glow_cream_share": 0.0, "glow_skeleton_px": 2928, "glow_junction_clusters": 18, "glow_components": 155, "glow_vertical_line_share": 0.972, "glow_horizontal_rung_share": 0.0, "glow_blob_share": 0.01, "glow_component_height_median_px": 15, "glow_component_width_median_px": 2, "glow_component_height_p90_px": 32}`
- smoke: `{"card_diff_mask_px": 66970, "changed_px_gt1p5": 69623, "frame_share_changed": 0.0483, "delta_lum_median": 28.61, "delta_lum_p95": 54.89, "delta_lum_p99": 58.11, "delta_lum_max": 60.11, "edge_clean_backdrop_px": 2521, "edge_step_p99_clean_backdrop_info": 0.66, "edge_band_px": 3220, "edge_band_px_on_smooth_backdrop": 2808, "edge_step_p99_all_boundary": 7.93, "edge_step_p99_levels_per_px": 0.88, "edge_step_max": 1.47, "smoke_pixel_mean_rgb": [135.5, 103.0, 106.6], "plume_mean_s": 0.248}`
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
