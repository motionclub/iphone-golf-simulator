# POSTCARD_LOOK area I: measurements from the Game-view pixels (and the installed FBX)

Stills: `ArtDir/screenshots/golf_postcards/look` (900x1600, pipeline asset **TennisURP**, quality level 2, Unity 6000.3.24f1). Masks: `proof/masks/` (PostcardProofMasks, same frames; ID render = exact per-material masks).
Mask statistics read `masks/<k>/<name>.full.png`; it equals the proof still except for animated water (table below). Thresholds: `measure.py` THRESH (the user's lines, the runtime gates' own limits). Re-run: `run_proof.sh metrics`.

## Gates

| gate | result | numbers |
|---|---|---|
| GRASS_HUE_GAMEVIEW hole08 | **PASS** | hole08_1_tee: central lower third mean #A7B742 h68.1 S0.638 V0.717; fairway+green px 701531 mean hue 69.0 (median 69.5), clipped(any ch>=250) 0.1%; hole08_2_approach: central lower third mean #A0B13F h68.8 S0.645 V0.695; fairway+green px 713760 mean hue 68.5 (median 69.0), clipped(any ch>=250) 0.4%; target fairway/green h60..76 (stills h64-73), clip <= 5% / info: hole08_3_arch rough 326697px h63.9 S0.532 V0.469; hole08_aerial rough 17626px h60.7 S0.488 V0.535 |
| GRASS_HUE_GAMEVIEW hole09 | **PASS** | hole09_1_tee: central lower third mean #92A343 h70.5 S0.592 V0.64; fairway+green px 861826 mean hue 69.9 (median 70.1), clipped(any ch>=250) 0.0%; hole09_2_approach: central lower third mean #85943E h71.0 S0.585 V0.582; fairway+green px 861814 mean hue 72.2 (median 72.4), clipped(any ch>=250) 0.0%; target fairway/green h60..76 (stills h64-73), clip <= 5% / info: hole09_3_ruin scrub 633236px h48.4 S0.351 V0.487; hole09_aerial rough 54698px h68.7 S0.487 V0.505; hole09_aerial scrub 81262px h47.8 S0.33 V0.514 |
| GRASS_HUE_GAMEVIEW hole10 | **PASS** | hole10_1_tee: central lower third mean #A2B625 h68.2 S0.797 V0.713; fairway+green px 861855 mean hue 67.7 (median 67.9), clipped(any ch>=250) 1.4%; hole10_2_approach: central lower third mean #98A92B h68.1 S0.747 V0.664; fairway+green px 861930 mean hue 67.6 (median 67.8), clipped(any ch>=250) 0.0%; target fairway/green h60..76 (stills h64-73), clip <= 5% / info: hole10_3_lavarim rough 117934px h61.2 S0.665 V0.465; hole10_aerial rough 70285px h61.0 S0.681 V0.474 |
| NOT_FLAT_PER_STILL | **PASS** | (sd >= 12, largest colour cell <= 50%, address stills flat windows <= 15%; failing: none) hole08_1_tee: lower-60% lum sd 25.33, flat 8px windows 1.8%, largest colour cell 10%, 18 colour cells >= 1% ok / hole08_2_approach: lower-60% lum sd 26.03, flat 8px windows 1.3%, largest colour cell 10%, 22 colour cells >= 1% ok / hole08_3_arch: lower-60% lum sd 40.96, flat 8px windows 8.6% (landmark: info), largest colour cell 8%, 30 colour cells >= 1% ok / hole09_1_tee: lower-60% lum sd 19.06, flat 8px windows 0.2%, largest colour cell 19%, 16 colour cells >= 1% ok / hole09_2_approach: lower-60% lum sd 20.15, flat 8px windows 0.4%, largest colour cell 13%, 17 colour cells >= 1% ok / hole09_3_ruin: lower-60% lum sd 20.37, flat 8px windows 1.4% (landmark: info), largest colour cell 10%, 25 colour cells >= 1% ok / hole10_1_tee: lower-60% lum sd 25.07, flat 8px windows 0.1%, largest colour cell 12%, 17 colour cells >= 1% ok / hole10_2_approach: lower-60% lum sd 17.9, flat 8px windows 0.2%, largest colour cell 10%, 22 colour cells >= 1% ok / hole10_3_lavarim: lower-60% lum sd 39.26, flat 8px windows 6.6% (landmark: info), largest colour cell 15%, 24 colour cells >= 1% ok; flat baseline stills for contrast: hole08_layup sd 6.42 flat 99% cell 44%, hole08_midpad sd 6.58 flat 99% cell 32%, hole08_tee sd 4.18 flat 99% cell 58%, hole09_fairway sd 6.9 flat 99% cell 45%, hole09_ridge sd 0.44 flat 100% cell 60%, hole09_tee sd 1.48 flat 100% cell 65%, hole10_approach sd 0.65 flat 100% cell 64%, hole10_rim sd 4.55 flat 99% cell 57%, hole10_tee sd 1.57 flat 100% cell 63% |
| SHELF_NOT_LOUDEST | **PASS** | (shelf <= 10% of the brightest 2%, <= 1.3 x the open sea) hole08_aerial: shelf 3281 px = 0.23% of the frame, mean #225360 h192.2 V0.375 lum 73.4, ocean beside it lum 79.3, ratio 0.926, shelf = 0.0% and turquoise = 0.0% of the brightest 2% (lum >= 234.2), brightest 2% is sky/other 96.5%, surf 0.0%, ocean 3.5% ok / hole09_aerial: shelf 7992 px = 0.56% of the frame, mean #1C596E h195.4 V0.433 lum 77.8, ocean beside it lum 74.5, ratio 1.044, shelf = 0.0% and turquoise = 0.0% of the brightest 2% (lum >= 198.0), brightest 2% is sky/other 80.15%, surf 1.5%, ocean 0.0% ok / hole08_1_tee: shelf 21 px (< 300: not measurable here) / hole08_2_approach: shelf 0 px (< 300: not measurable here) / hole08_3_arch: shelf 0 px (< 300: not measurable here) / hole09_1_tee: shelf 0 px (< 300: not measurable here) / hole09_2_approach: shelf 419 px = 0.03% of the frame, mean #1B566F h197.9 V0.435 lum 75.1, ocean beside it lum 87.8, ratio 0.855, shelf = 0.0% and turquoise = 0.0% of the brightest 2% (lum >= 231.4), brightest 2% is sky/other 100.0%, surf 0.0%, ocean 0.0% ok / hole09_3_ruin: shelf 393 px = 0.03% of the frame, mean #1A5C6F h193.1 V0.436 lum 79.7, ocean beside it lum 92.5, ratio 0.862, shelf = 0.0% and turquoise = 0.0% of the brightest 2% (lum >= 165.2), brightest 2% is sky/other 2.93%, surf 0.2%, ocean 0.0% ok |
| LAVA_ORANGE_AND_BRIGHT | **PASS** | (in band >= 85%, G>=250 <= 5%, dark V<.40 <= 15%, mean V >= 0.7; crater.jpg pool (212,62,14) h15 S.93 V.83) hole10_1_tee: lava 4645 px (0.3% of frame) mean #D25222 h16.6 S0.84 V0.823, in band (h8-28 S>=.75 V>=.7) 92.4% (h+S only 99.4%), dark V<.40 1.2%, G>=250 0.0%, cream 0.00%, dark components 5 largest 9 px (0.19% of the lava) ok / hole10_2_approach: lava 177790 px (12.3% of frame) mean #DC5318 h17.9 S0.889 V0.862, in band (h8-28 S>=.75 V>=.7) 95.0% (h+S only 100.0%), dark V<.40 1.7%, G>=250 0.0%, cream 0.00%, dark components 130 largest 178 px (0.10% of the lava) ok / hole10_3_lavarim: lava 598099 px (41.5% of frame) mean #DB5319 h18.0 S0.885 V0.858, in band (h8-28 S>=.75 V>=.7) 93.4% (h+S only 100.0%), dark V<.40 2.5%, G>=250 0.0%, cream 0.00%, dark components 221 largest 1549 px (0.26% of the lava) ok / hole10_aerial (extra aerial, info): lava 486095 px (33.8% of frame) mean #DA531A h17.7 S0.881 V0.855, in band (h8-28 S>=.75 V>=.7) 94.1% (h+S only 100.0%), dark V<.40 1.7%, G>=250 0.0%, cream 0.00%, dark components 319 largest 250 px (0.05% of the lava) ok |
| BASALT_JOINTS | **FAIL** | (glow <= 20% of the basalt, non-glow median lum <= 55.0, non-glow mean S <= 0.25, glow in vertical lines <= 80% (not streak-only), horizontal rungs <= 20%, branching joints >= 3.0 junctions per 100 skeleton px; crater.jpg basalt (26,25,29) S .10) hole10_1_tee: basalt 136645 px, non-glow mean #282325 h337.9 S0.128 V0.156 median lum 35.5, glow 1.8% of basalt in 151 components (vertical-line 92%, horizontal-rung 1%, blob 1%, median height 8 px x width 2 px), glow mean #863A26 h12.6 FAIL / hole10_2_approach: basalt 135652 px, non-glow mean #1C1819 h343.9 S0.17 V0.112 median lum 23.5, glow 2.1% of basalt in 90 components (vertical-line 93%, horizontal-rung 0%, blob 3%, median height 13 px x width 2 px), glow mean #99401C h17.2 FAIL / hole10_3_lavarim: basalt 360209 px, non-glow mean #201C1E h323.1 S0.118 V0.124 median lum 28.0, glow 1.5% of basalt in 155 components (vertical-line 97%, horizontal-rung 0%, blob 1%, median height 15 px x width 2 px), glow mean #A3401D h15.7 FAIL / hole10_aerial (extra aerial, info): basalt 263948 px, non-glow mean #272225 h319.6 S0.113 V0.151 median lum 37.3, glow 1.0% of basalt in 150 components (vertical-line 97%, horizontal-rung 1%, blob 1%, median height 9 px x width 1 px), glow mean #8C3920 h13.7 FAIL / joint network (all proof shots): 73 skeleton junction clusters on 5752 skeleton px = 1.27 per 100 px (>= 3.0; crater.jpg wall crops 8.3-8.8) FAIL |
| SMOKE_SOFT | **PASS** | (visible dLum p95 >= 8.0, max <= 110.0, edge step p99 <= 6.0 levels/px) hole10_1_tee: smoke changes 53774 px (3.73% of frame), /dLum/ median 11.7 p95 36.86 p99 50.36 max 59.07, edge step p99 1.79 levels/px over 4788 boundary px on a smooth backdrop (all boundary px: 13.1; info, boundary px with a clean backdrop within 4 px: p99 0.58 over 3042 px), plume mean #A46A5E, see-through (info) backdrop detail kept 0.635 (corr 0.972, 8957 px) ok / hole10_2_approach: smoke changes 61666 px (4.28% of frame), /dLum/ median 43.42 p95 80.57 p99 88.64 max 93.92, edge step p99 0.99 levels/px over 2778 boundary px on a smooth backdrop (all boundary px: 1.1; info, boundary px with a clean backdrop within 4 px: p99 0.8 over 500 px), plume mean #584E4F, see-through (info) backdrop detail kept 0.493 (corr 0.933, 18972 px) ok / hole10_3_lavarim: smoke changes 64160 px (4.46% of frame), /dLum/ median 26.17 p95 49.03 p99 54.11 max 58.03, edge step p99 0.78 levels/px over 1958 boundary px on a smooth backdrop (all boundary px: 10.36; info, boundary px with a clean backdrop within 4 px: p99 0.66 over 1734 px), plume mean #846468, see-through (info) backdrop detail kept None (corr None, None px) ok / hole10_aerial (extra aerial, info): smoke changes 55988 px (3.89% of frame), /dLum/ median 14.37 p95 68.71 p99 79.78 max 87.78, edge step p99 1.12 levels/px over 5829 boundary px on a smooth backdrop (all boundary px: 2.36; info, boundary px with a clean backdrop within 4 px: p99 1.05 over 3769 px), plume mean #836158, see-through (info) backdrop detail kept 0.602 (corr 0.925, 6899 px) ok |
| NO_PLANT_ON_SEA | **PASS** | installed FBX, ray down from each plant base through every non-plant mesh: hole8: 809 PLANT_ objects (incl. 131 vines): 0 on the sea, 0 floating (no surface within 1 m under the base), support {'ROCK_OUTCROP': 83, 'TERRAIN_': 595}; vines judged by root: 123 attached (root <= 0.6 m from rock/ground), 8 root 0.6..0.86 m off ['PLANT_VINE_L.026', 'PLANT_VINE_L.041', 'PLANT_VINE_L.042', 'PLANT_VINE_M.053', 'PLANT_VINE_M.054', 'PLANT_VINE_M.055', 'PLANT_VINE_M.060', 'PLANT_VINE_M.061'], lowest vine tip 2.91 m above the sea / hole9: 376 PLANT_ objects (incl. 0 vines): 0 on the sea, 0 floating (no surface within 1 m under the base), support {'TERRAIN_': 376} / hole10: 210 PLANT_ objects (incl. 0 vines): 0 on the sea, 0 floating (no surface within 1 m under the base), support {'TERRAIN_': 210} |
| NO_ROCK_STRETCH_2X | **PASS** | installed FBX object scales (open-shell cliff / wall skins carry their stretch in the vertices: postcard_look_verify NO_ROCK_STRETCH_2X judges those): hole8: 83 ROCK_ objects, object scale 0.547..1.999, anisotropy max 1.875 (worst ROCK_OUTCROP_A.000), > 2x: 0 abs / 0 aniso, < 0.4: 0 / hole9: 298 ROCK_ objects, object scale 0.6..1.999, anisotropy max 1.346 (worst ROCK_SEASTACK_A.001), > 2x: 0 abs / 0 aniso, < 0.4: 0 / hole10: 457 ROCK_ objects, object scale 0.558..1.922, anisotropy max 1.286 (worst ROCK_CAIRN_A_BASALT.004), > 2x: 0 abs / 0 aniso, < 0.4: 0 |
| NO_FOAM_STRIP | **PASS** | installed FBX names / materials + surf patches in the aerials: hole8: foam-named objects [], foam materials [], legacy MAT_ [], LK_SURF slots 17 / hole9: foam-named objects [], foam materials [], legacy MAT_ [], LK_SURF slots 61 / hole10: foam-named objects [], foam materials [], legacy MAT_ [], LK_SURF slots None / hole08_aerial: surf patches 9, longest 57 px = 3.6% of the frame height, surf 0.20% of the frame / hole09_aerial: surf patches 14, longest 46 px = 2.9% of the frame height, surf 0.23% of the frame / hole09_2_approach: surf patches 3, longest 45 px = 2.8% of the frame height, surf 0.01% of the frame |
| PATH_UNDER_BALL | **PASS** | installed hole 8 FBX: 2 path meshes, 14506 up-facing vertices, height over the play surface max 1.15 cm / p99 1.15 cm / mean 0.56 cm (limit 1.5 cm, 0 above; game ball radius 5.49 cm; before: up to 11 cm) / hole08_1_tee: ball radius 16.4 px, visible 1159 / 844 expected px (ratio 1.372), ring {'fairway': 0.893}, ball lum 193.3 vs ring 171.5 / hole08_2_approach: ball radius 16.4 px, visible 1120 / 844 expected px (ratio 1.326), ring {'fairway': 0.891}, ball lum 187.7 vs ring 145.9 / hole08_4_pathball: ball radius 16.4 px, visible 1022 / 844 expected px (ratio 1.21), ring {'path': 0.837}, ball lum 193.5 vs ring 160.7 |

## Frame consistency (mask-run frame vs the proof still; the sea moves from run to run, so the right-hand columns leave the water pixels out)

| shot | max channel diff | share of pixels with sum diff > 8 | water share of the frame | max channel diff without water | share > 8 without water |
|---|---|---|---|---|---|
| hole08_1_tee | 1 | 0.00% | 2.0% | 0 | 0.00% |
| hole08_2_approach | 13 | 0.26% | 2.1% | 3 | 0.00% |
| hole08_3_arch | 244 | 8.24% | 11.9% | 12 | 0.00% |
| hole09_1_tee | 15 | 0.14% | 0.6% | 8 | 0.00% |
| hole09_2_approach | 25 | 0.94% | 1.9% | 19 | 0.00% |
| hole09_3_ruin | 17 | 5.46% | 10.0% | 14 | 0.00% |
| hole10_1_tee | 1 | 0.00% | 0.0% | 1 | 0.00% |
| hole10_2_approach | 0 | 0.00% | 0.0% | 0 | 0.00% |
| hole10_3_lavarim | 0 | 0.00% | 0.0% | 0 | 0.00% |
| hole08_4_pathball | 1 | 0.00% | 2.5% | 0 | 0.00% |
| hole08_aerial | 235 | 3.86% | 62.7% | 3 | 0.00% |
| hole09_aerial | 86 | 6.95% | 66.0% | 2 | 0.00% |
| hole10_aerial | 0 | 0.00% | 0.0% | 0 | 0.00% |

## Per shot

### hole08_1_tee
- central lower third: #A7B742 hue 68.1 S 0.638 V 0.717
- fairway (ID mask, lower 60%): 701531 px, mean #9DAE40 hue 69.0 (median 69.5, p10 65.1, p90 73.0) S 0.631 V 0.681, clipped 0.1%
- flatness: lower-60% luminance sd 25.33 (mean 161.3), flat 8 px windows 1.8%, colour cells >= 1%: 18, largest cell 10%, kinds {'fairway': 0.631, 'path': 0.157, 'cliff': 0.012, 'rock': 0.012, 'ocean': 0.016}
- shelf: `{"top2_lum_cut": 223.9, "top2_px": 28805, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.8376, "shelf_px": 21, "shelf_share_of_frame": 1e-05}`
- ball: `{"centre_px": [450, 952.3], "radius_px": 16.4, "expected_px": 844, "visible_px_in_1p3r_disc": 1159, "visible_ratio": 1.372, "ring_categories": {"fairway": 0.893}, "ball_lum_mean": 193.3, "ring_lum_mean": 171.5}`
- surf: `{"id_surf_px": 9, "id_surf_share_of_frame": 1e-05, "diff_surf_px": 35}`

### hole08_2_approach
- central lower third: #A0B13F hue 68.8 S 0.645 V 0.695
- fairway (ID mask, lower 60%): 713760 px, mean #A5B541 hue 68.5 (median 69.0, p10 64.7, p90 72.5) S 0.64 V 0.711, clipped 0.4%
- flatness: lower-60% luminance sd 26.03 (mean 167.4), flat 8 px windows 1.3%, colour cells >= 1%: 22, largest cell 10%, kinds {'fairway': 0.637, 'path': 0.148, 'cliff': 0.011, 'rock': 0.013, 'ocean': 0.016}
- shelf: `{"top2_lum_cut": 230.4, "top2_px": 28805, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0046, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.7808, "shelf_px": 0, "shelf_share_of_frame": 0.0}`
- ball: `{"centre_px": [450, 952.3], "radius_px": 16.4, "expected_px": 844, "visible_px_in_1p3r_disc": 1120, "visible_ratio": 1.326, "ring_categories": {"fairway": 0.891}, "ball_lum_mean": 187.7, "ring_lum_mean": 145.9}`
- surf: `{"id_surf_px": 0, "id_surf_share_of_frame": 0.0, "diff_surf_px": 0}`

### hole08_3_arch
- central lower third: #7A7A40 hue 61.0 S 0.478 V 0.48
- rough (ID mask, lower 60%): 326697 px, mean #737838 hue 63.9 (median 64.2, p10 57.1, p90 75.0) S 0.532 V 0.469, clipped 0.0%
- flatness: lower-60% luminance sd 40.96 (mean 110.0), flat 8 px windows 8.6%, colour cells >= 1%: 30, largest cell 8%, kinds {'rough': 0.227, 'masonry': 0.179, 'rock': 0.036, 'plant': 0.033, 'ocean': 0.114}
- shelf: `{"top2_lum_cut": 253.7, "top2_px": 29040, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.2236, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.7761, "shelf_px": 0, "shelf_share_of_frame": 0.0}`
- surf: `{"id_surf_px": 0, "id_surf_share_of_frame": 0.0, "diff_surf_px": 0}`

### hole09_1_tee
- central lower third: #92A343 hue 70.5 S 0.592 V 0.64
- fairway (ID mask, lower 60%): 861826 px, mean #97A744 hue 69.9 (median 70.1, p10 66.6, p90 73.6) S 0.592 V 0.656, clipped 0.0%
- flatness: lower-60% luminance sd 19.06 (mean 156.6), flat 8 px windows 0.2%, colour cells >= 1%: 16, largest cell 19%, kinds {'fairway': 0.801, 'rough': 0.02}
- shelf: `{"top2_lum_cut": 231.6, "top2_px": 28803, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.9997, "shelf_px": 0, "shelf_share_of_frame": 0.0}`
- ball: `{"centre_px": [450, 952.3], "radius_px": 16.4, "expected_px": 844, "visible_px_in_1p3r_disc": 1111, "visible_ratio": 1.315, "ring_categories": {"fairway": 0.891}, "ball_lum_mean": 197.3, "ring_lum_mean": 171.2}`
- surf: `{"id_surf_px": 0, "id_surf_share_of_frame": 0.0, "diff_surf_px": 0}`

### hole09_2_approach
- central lower third: #85943E hue 71.0 S 0.585 V 0.582
- fairway (ID mask, lower 60%): 861814 px, mean #849540 hue 72.2 (median 72.4, p10 68.3, p90 77.0) S 0.569 V 0.585, clipped 0.0%
- flatness: lower-60% luminance sd 20.15 (mean 139.4), flat 8 px windows 0.4%, colour cells >= 1%: 17, largest cell 13%, kinds {'fairway': 0.774, 'cliff': 0.029, 'ocean': 0.015}
- shelf: `{"top2_lum_cut": 231.4, "top2_px": 29106, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 1.0, "shelf_px": 419, "shelf_share_of_frame": 0.00029, "shelf_mean_rgb": [26.9, 85.8, 110.9], "shelf_hue": 197.9, "shelf_s": 0.757, "shelf_v": 0.435, "shelf_lum_mean": 75.1, "shelf_lum_p95": 79.0, "ocean_lum_mean": 87.8, "ocean_mean_rgb": [39.7, 96.6, 142.0], "shelf_vs_ocean_lum": 0.855, "turquoise_px_share_of_frame": 0.0042, "top2_share_turquoise": 0.0}`
- ball: `{"centre_px": [450, 952.3], "radius_px": 16.4, "expected_px": 844, "visible_px_in_1p3r_disc": 1081, "visible_ratio": 1.279, "ring_categories": {"fairway": 0.891}, "ball_lum_mean": 187.7, "ring_lum_mean": 123.9}`
- surf: `{"id_surf_px": 152, "id_surf_share_of_frame": 0.00011, "id_surf_components": 3, "id_surf_longest_px": 45, "id_surf_longest_share_of_frame_h": 0.028, "diff_surf_px": 312}`

### hole09_3_ruin
- central lower third: #7A7354 hue 49.0 S 0.31 V 0.479
- scrub (ID mask, lower 60%): 633236 px, mean #7C7451 hue 48.4 (median 49.5, p10 42.9, p90 55.6) S 0.351 V 0.487, clipped 0.0%
- flatness: lower-60% luminance sd 20.37 (mean 118.3), flat 8 px windows 1.4%, colour cells >= 1%: 25, largest cell 10%, kinds {'rough': 0.041, 'scrub': 0.613, 'cliff': 0.02, 'masonry': 0.115, 'rock': 0.064, 'plant': 0.027, 'ocean': 0.096}
- shelf: `{"top2_lum_cut": 165.2, "top2_px": 28810, "top2_share_shelf": 0.0, "top2_share_surf": 0.0016, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.0293, "shelf_px": 393, "shelf_share_of_frame": 0.00027, "shelf_mean_rgb": [25.9, 92.5, 111.1], "shelf_hue": 193.1, "shelf_s": 0.767, "shelf_v": 0.436, "shelf_lum_mean": 79.7, "shelf_lum_p95": 81.1, "ocean_lum_mean": 92.5, "ocean_mean_rgb": [46.4, 100.6, 147.9], "shelf_vs_ocean_lum": 0.862, "turquoise_px_share_of_frame": 0.0032, "top2_share_turquoise": 0.0}`
- surf: `{"id_surf_px": 329, "id_surf_share_of_frame": 0.00023, "id_surf_components": 1, "id_surf_longest_px": 33, "id_surf_longest_share_of_frame_h": 0.021, "diff_surf_px": 351}`

### hole10_1_tee
- central lower third: #A2B625 hue 68.2 S 0.797 V 0.713
- fairway (ID mask, lower 60%): 861855 px, mean #A7BA26 hue 67.7 (median 67.9, p10 65.3, p90 70.3) S 0.793 V 0.73, clipped 1.4%
- flatness: lower-60% luminance sd 25.07 (mean 171.5), flat 8 px windows 0.1%, colour cells >= 1%: 17, largest cell 12%, kinds {'fairway': 0.8, 'basalt': 0.095, 'plant': 0.015, 'smoke': 0.075}
- shelf: `{"top2_lum_cut": 221.6, "top2_px": 28800, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.0088, "shelf_px": 0, "shelf_share_of_frame": 0.0}`
- lava: `{"pixels": 4645, "share_of_frame": 0.0032, "mean_rgb": [209.9, 82.2, 33.5], "mean_hue": 16.6, "mean_s": 0.84, "mean_v": 0.823, "in_band_hue8_28_s75_v70": 0.9236, "in_band_hue_s_only": 0.994, "dark_v_lt_040": 0.0116, "dark_v_lt_025": 0.0, "v_median": 0.827, "g_ge_250": 0.0, "lum_mean": 105.9, "lum_p10": 82.2, "lum_p90": 142.7, "cream_min_ch_ge_230": 0.0, "dark_components": 5, "dark_largest_px": 9, "dark_median_px": 6, "dark_largest_share_of_lava": 0.0019, "dark_components_ge_400px": 0, "dark_median_elongation": 1.7, "frame_lum_mean": 150.3}`
- basalt: `{"pixels": 136645, "share_of_frame": 0.0949, "glow_px": 2434, "glow_coverage": 0.0178, "base_mean_rgb": [39.9, 34.8, 36.7], "base_hue": 337.9, "base_s": 0.128, "base_v": 0.156, "base_lum_median": 35.5, "base_lum_p90": 47.2, "base_lum_mean": 36.0, "base_s_median": 0.105, "glow_mean_rgb": [133.5, 58.1, 38.2], "glow_mean_hue": 12.6, "glow_cream_share": 0.0, "glow_skeleton_px": 1356, "glow_junction_clusters": 35, "glow_components": 151, "glow_vertical_line_share": 0.925, "glow_horizontal_rung_share": 0.006, "glow_blob_share": 0.009, "glow_component_height_median_px": 8, "glow_component_width_median_px": 2, "glow_component_height_p90_px": 15}`
- smoke: `{"card_diff_mask_px": 54938, "changed_px_gt1p5": 53774, "frame_share_changed": 0.0373, "delta_lum_median": 11.7, "delta_lum_p95": 36.86, "delta_lum_p99": 50.36, "delta_lum_max": 59.07, "edge_clean_backdrop_px": 3042, "edge_step_p99_clean_backdrop_info": 0.58, "edge_band_px": 6225, "edge_band_px_on_smooth_backdrop": 4788, "edge_step_p99_all_boundary": 13.1, "edge_step_p99_levels_per_px": 1.79, "edge_step_max": 28.97, "smoke_pixel_mean_rgb": [164.4, 106.1, 94.4], "plume_mean_s": 0.38, "through_px": 8957, "through_corr": 0.972, "transmission_est": 0.635}`
- ball: `{"centre_px": [450, 952.3], "radius_px": 16.4, "expected_px": 844, "visible_px_in_1p3r_disc": 1125, "visible_ratio": 1.331, "ring_categories": {"fairway": 0.893}, "ball_lum_mean": 172.2, "ring_lum_mean": 187.6}`
- surf: `{"id_surf_px": 0, "id_surf_share_of_frame": 0.0}`

### hole10_2_approach
- central lower third: #98A92B hue 68.1 S 0.747 V 0.664
- fairway (ID mask, lower 60%): 861930 px, mean #97A72E hue 67.6 (median 67.8, p10 64.8, p90 70.2) S 0.724 V 0.654, clipped 0.0%
- flatness: lower-60% luminance sd 17.9 (mean 154.7), flat 8 px windows 0.2%, colour cells >= 1%: 22, largest cell 10%, kinds {'fairway': 0.665, 'basalt': 0.094, 'lava': 0.123, 'smoke': 0.112}
- shelf: `{"top2_lum_cut": 192.0, "top2_px": 28805, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.0061, "shelf_px": 0, "shelf_share_of_frame": 0.0}`
- lava: `{"pixels": 177790, "share_of_frame": 0.1235, "mean_rgb": [219.9, 82.9, 24.5], "mean_hue": 17.9, "mean_s": 0.889, "mean_v": 0.862, "in_band_hue8_28_s75_v70": 0.9502, "in_band_hue_s_only": 1.0, "dark_v_lt_040": 0.0169, "dark_v_lt_025": 0.0, "v_median": 0.867, "g_ge_250": 0.0, "lum_mean": 107.8, "lum_p10": 84.6, "lum_p90": 146.0, "cream_min_ch_ge_230": 0.0, "dark_components": 130, "dark_largest_px": 178, "dark_median_px": 8, "dark_largest_share_of_lava": 0.001, "dark_components_ge_400px": 0, "dark_median_elongation": 1290.99, "frame_lum_mean": 125.4}`
- basalt: `{"pixels": 135652, "share_of_frame": 0.0942, "glow_px": 2880, "glow_coverage": 0.0212, "base_mean_rgb": [28.5, 23.6, 24.9], "base_hue": 343.9, "base_s": 0.17, "base_v": 0.112, "base_lum_median": 23.5, "base_lum_p90": 34.9, "base_lum_mean": 24.8, "base_s_median": 0.125, "glow_mean_rgb": [153.3, 63.8, 27.9], "glow_mean_hue": 17.2, "glow_cream_share": 0.0, "glow_skeleton_px": 1468, "glow_junction_clusters": 20, "glow_components": 90, "glow_vertical_line_share": 0.926, "glow_horizontal_rung_share": 0.0, "glow_blob_share": 0.028, "glow_component_height_median_px": 13, "glow_component_width_median_px": 2, "glow_component_height_p90_px": 32}`
- smoke: `{"card_diff_mask_px": 59433, "changed_px_gt1p5": 61666, "frame_share_changed": 0.0428, "delta_lum_median": 43.42, "delta_lum_p95": 80.57, "delta_lum_p99": 88.64, "delta_lum_max": 93.92, "edge_clean_backdrop_px": 500, "edge_step_p99_clean_backdrop_info": 0.8, "edge_band_px": 3760, "edge_band_px_on_smooth_backdrop": 2778, "edge_step_p99_all_boundary": 1.1, "edge_step_p99_levels_per_px": 0.99, "edge_step_max": 1.43, "smoke_pixel_mean_rgb": [88.3, 77.9, 79.0], "plume_mean_s": 0.11, "through_px": 18972, "through_corr": 0.933, "transmission_est": 0.493}`
- ball: `{"centre_px": [450, 952.3], "radius_px": 16.4, "expected_px": 844, "visible_px_in_1p3r_disc": 1116, "visible_ratio": 1.321, "ring_categories": {"fairway": 0.909}, "ball_lum_mean": 151.1, "ring_lum_mean": 153.7}`
- surf: `{"id_surf_px": 0, "id_surf_share_of_frame": 0.0}`

### hole10_3_lavarim
- central lower third: #DC5419 hue 18.2 S 0.885 V 0.864
- fairway (ID mask, lower 60%): 15948 px, mean #A4B732 hue 68.6 (median 68.9, p10 66.1, p90 71.6) S 0.726 V 0.719, clipped 0.1%
- green (ID mask, lower 60%): 119 px, mean #9AA530 hue 65.7 (median 65.7, p10 64.0, p90 67.5) S 0.706 V 0.646, clipped 0.0%
- rough (ID mask, lower 60%): 117934 px, mean #757728 hue 61.2 (median 61.6, p10 58.4, p90 64.6) S 0.665 V 0.465, clipped 0.0%
- flatness: lower-60% luminance sd 39.26 (mean 98.2), flat 8 px windows 6.6%, colour cells >= 1%: 24, largest cell 15%, kinds {'fairway': 0.012, 'rough': 0.082, 'basalt': 0.25, 'lava': 0.415, 'smoke': 0.123}
- shelf: `{"top2_lum_cut": 163.1, "top2_px": 29342, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.5586, "top2_share_other_or_sky": 0.0143, "shelf_px": 0, "shelf_share_of_frame": 0.0}`
- lava: `{"pixels": 598099, "share_of_frame": 0.4153, "mean_rgb": [218.8, 83.3, 25.1], "mean_hue": 18.0, "mean_s": 0.885, "mean_v": 0.858, "in_band_hue8_28_s75_v70": 0.9344, "in_band_hue_s_only": 1.0, "dark_v_lt_040": 0.0248, "dark_v_lt_025": 0.0, "v_median": 0.867, "g_ge_250": 0.0, "lum_mean": 107.9, "lum_p10": 81.9, "lum_p90": 150.9, "cream_min_ch_ge_230": 0.0, "dark_components": 221, "dark_largest_px": 1549, "dark_median_px": 11, "dark_largest_share_of_lava": 0.0026, "dark_components_ge_400px": 9, "dark_median_elongation": 7.62, "frame_lum_mean": 86.1}`
- basalt: `{"pixels": 360209, "share_of_frame": 0.2501, "glow_px": 5325, "glow_coverage": 0.0148, "base_mean_rgb": [31.6, 27.9, 30.2], "base_hue": 323.1, "base_s": 0.118, "base_v": 0.124, "base_lum_median": 28.0, "base_lum_p90": 40.9, "base_lum_mean": 28.9, "base_s_median": 0.125, "glow_mean_rgb": [162.7, 63.9, 29.1], "glow_mean_hue": 15.7, "glow_cream_share": 0.0, "glow_skeleton_px": 2928, "glow_junction_clusters": 18, "glow_components": 155, "glow_vertical_line_share": 0.972, "glow_horizontal_rung_share": 0.0, "glow_blob_share": 0.01, "glow_component_height_median_px": 15, "glow_component_width_median_px": 2, "glow_component_height_p90_px": 32}`
- smoke: `{"card_diff_mask_px": 62194, "changed_px_gt1p5": 64160, "frame_share_changed": 0.0446, "delta_lum_median": 26.17, "delta_lum_p95": 49.03, "delta_lum_p99": 54.11, "delta_lum_max": 58.03, "edge_clean_backdrop_px": 1734, "edge_step_p99_clean_backdrop_info": 0.66, "edge_band_px": 2379, "edge_band_px_on_smooth_backdrop": 1958, "edge_step_p99_all_boundary": 10.36, "edge_step_p99_levels_per_px": 0.78, "edge_step_max": 1.78, "smoke_pixel_mean_rgb": [132.3, 100.2, 104.4], "plume_mean_s": 0.248}`
- surf: `{"id_surf_px": 0, "id_surf_share_of_frame": 0.0}`

### hole08_4_pathball
- central lower third: #B9A677 hue 42.9 S 0.357 V 0.724
- fairway (ID mask, lower 60%): 108783 px, mean #BECC49 hue 66.6 (median 66.8, p10 63.5, p90 69.8) S 0.643 V 0.801, clipped 2.9%
- flatness: lower-60% luminance sd 35.62 (mean 165.1), flat 8 px windows 20.3%, colour cells >= 1%: 20, largest cell 7%, kinds {'fairway': 0.218, 'path': 0.564, 'cliff': 0.016, 'rock': 0.012, 'ocean': 0.021}
- shelf: `{"top2_lum_cut": 224.9, "top2_px": 28800, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.6617, "shelf_px": 37, "shelf_share_of_frame": 3e-05}`
- ball: `{"centre_px": [450, 952.3], "radius_px": 16.4, "expected_px": 844, "visible_px_in_1p3r_disc": 1022, "visible_ratio": 1.21, "ring_categories": {"path": 0.837}, "ball_lum_mean": 193.5, "ring_lum_mean": 160.7}`
- surf: `{"id_surf_px": 13, "id_surf_share_of_frame": 1e-05, "diff_surf_px": 52}`

### hole08_aerial
- central lower third: #0B4576 hue 207.2 S 0.909 V 0.463
- fairway (ID mask, lower 60%): 34586 px, mean #A8B850 hue 69.1 (median 69.4, p10 65.9, p90 73.3) S 0.564 V 0.721, clipped 0.0%
- green (ID mask, lower 60%): 1812 px, mean #AEBC73 hue 71.3 (median 72.0, p10 67.8, p90 73.4) S 0.387 V 0.738, clipped 0.0%
- rough (ID mask, lower 60%): 17626 px, mean #888846 hue 60.7 (median 60.9, p10 56.9, p90 65.9) S 0.488 V 0.535, clipped 0.0%
- flatness: lower-60% luminance sd 30.11 (mean 77.1), flat 8 px windows 58.8%, colour cells >= 1%: 21, largest cell 27%, kinds {'fairway': 0.024, 'rough': 0.012, 'cliff': 0.014, 'ocean': 0.614}
- shelf: `{"top2_lum_cut": 234.2, "top2_px": 28911, "top2_share_shelf": 0.0, "top2_share_surf": 0.0002, "top2_share_fall": 0.0, "top2_share_ocean": 0.0348, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.965, "shelf_px": 3281, "shelf_share_of_frame": 0.00228, "shelf_mean_rgb": [33.6, 83.0, 95.7], "shelf_hue": 192.2, "shelf_s": 0.649, "shelf_v": 0.375, "shelf_lum_mean": 73.4, "shelf_lum_p95": 100.7, "ocean_lum_mean": 79.3, "ocean_mean_rgb": [41.3, 85.8, 127.3], "shelf_vs_ocean_lum": 0.926, "turquoise_px_share_of_frame": 0.0024, "top2_share_turquoise": 0.0}`
- surf: `{"id_surf_px": 2839, "id_surf_share_of_frame": 0.00197, "id_surf_components": 9, "id_surf_longest_px": 57, "id_surf_longest_share_of_frame_h": 0.036, "diff_surf_px": 3117}`

### hole09_aerial
- central lower third: #07376B hue 211.4 S 0.931 V 0.421
- fairway (ID mask, lower 60%): 47868 px, mean #8B9D48 hue 73.0 (median 73.6, p10 69.1, p90 77.6) S 0.538 V 0.616, clipped 0.0%
- green (ID mask, lower 60%): 1880 px, mean #97A954 hue 72.6 (median 72.6, p10 69.5, p90 76.4) S 0.5 V 0.662, clipped 0.0%
- rough (ID mask, lower 60%): 54698 px, mean #788142 hue 68.7 (median 69.0, p10 65.5, p90 72.2) S 0.487 V 0.505, clipped 0.0%
- scrub (ID mask, lower 60%): 81262 px, mean #837A58 hue 47.8 (median 48.0, p10 45.3, p90 51.0) S 0.33 V 0.514, clipped 0.0%
- flatness: lower-60% luminance sd 36.54 (mean 72.4), flat 8 px windows 64.1%, colour cells >= 1%: 15, largest cell 32%, kinds {'fairway': 0.037, 'rough': 0.05, 'scrub': 0.076, 'cliff': 0.043, 'ocean': 0.641}
- shelf: `{"top2_lum_cut": 198.0, "top2_px": 28803, "top2_share_shelf": 0.0, "top2_share_surf": 0.0149, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.8015, "shelf_px": 7992, "shelf_share_of_frame": 0.00555, "shelf_mean_rgb": [28.1, 89.3, 110.4], "shelf_hue": 195.4, "shelf_s": 0.745, "shelf_v": 0.433, "shelf_lum_mean": 77.8, "shelf_lum_p95": 100.2, "ocean_lum_mean": 74.5, "ocean_mean_rgb": [38.0, 80.0, 127.7], "shelf_vs_ocean_lum": 1.044, "turquoise_px_share_of_frame": 0.0065, "top2_share_turquoise": 0.0}`
- surf: `{"id_surf_px": 3273, "id_surf_share_of_frame": 0.00227, "id_surf_components": 14, "id_surf_longest_px": 46, "id_surf_longest_share_of_frame_h": 0.029, "diff_surf_px": 3561}`

### hole10_aerial
- central lower third: #BF641E hue 26.1 S 0.845 V 0.748
- fairway (ID mask, lower 60%): 122881 px, mean #A3B62A hue 68.2 (median 68.3, p10 65.6, p90 71.1) S 0.769 V 0.712, clipped 0.1%
- green (ID mask, lower 60%): 4132 px, mean #A1AE36 hue 66.5 (median 66.4, p10 65.3, p90 68.0) S 0.689 V 0.682, clipped 0.0%
- rough (ID mask, lower 60%): 70285 px, mean #787927 hue 61.0 (median 61.4, p10 58.6, p90 63.8) S 0.681 V 0.474, clipped 0.0%
- flatness: lower-60% luminance sd 45.56 (mean 102.7), flat 8 px windows 1.8%, colour cells >= 1%: 26, largest cell 13%, kinds {'fairway': 0.085, 'rough': 0.049, 'basalt': 0.183, 'lava': 0.338, 'smoke': 0.159}
- shelf: `{"top2_lum_cut": 183.7, "top2_px": 28801, "top2_share_shelf": 0.0, "top2_share_surf": 0.0, "top2_share_fall": 0.0, "top2_share_ocean": 0.0, "top2_share_lava": 0.0, "top2_share_other_or_sky": 0.0007, "shelf_px": 0, "shelf_share_of_frame": 0.0}`
- lava: `{"pixels": 486095, "share_of_frame": 0.3376, "mean_rgb": [218.0, 82.6, 26.0], "mean_hue": 17.7, "mean_s": 0.881, "mean_v": 0.855, "in_band_hue8_28_s75_v70": 0.9411, "in_band_hue_s_only": 1.0, "dark_v_lt_040": 0.017, "dark_v_lt_025": 0.0, "v_median": 0.863, "g_ge_250": 0.0, "lum_mean": 107.3, "lum_p10": 83.0, "lum_p90": 146.8, "cream_min_ch_ge_230": 0.0, "dark_components": 319, "dark_largest_px": 250, "dark_median_px": 10, "dark_largest_share_of_lava": 0.0005, "dark_components_ge_400px": 0, "dark_median_elongation": 3.4, "frame_lum_mean": 96.1}`
- basalt: `{"pixels": 263948, "share_of_frame": 0.1833, "glow_px": 2569, "glow_coverage": 0.0097, "base_mean_rgb": [38.6, 34.2, 37.2], "base_hue": 319.6, "base_s": 0.113, "base_v": 0.151, "base_lum_median": 37.3, "base_lum_p90": 46.9, "base_lum_mean": 35.4, "base_s_median": 0.128, "glow_mean_rgb": [140.0, 57.0, 32.4], "glow_mean_hue": 13.7, "glow_cream_share": 0.0, "glow_skeleton_px": 1524, "glow_junction_clusters": 10, "glow_components": 150, "glow_vertical_line_share": 0.971, "glow_horizontal_rung_share": 0.01, "glow_blob_share": 0.011, "glow_component_height_median_px": 9, "glow_component_width_median_px": 1, "glow_component_height_p90_px": 16}`
- smoke: `{"card_diff_mask_px": 56415, "changed_px_gt1p5": 55988, "frame_share_changed": 0.0389, "delta_lum_median": 14.37, "delta_lum_p95": 68.71, "delta_lum_p99": 79.78, "delta_lum_max": 87.78, "edge_clean_backdrop_px": 3769, "edge_step_p99_clean_backdrop_info": 1.05, "edge_band_px": 6457, "edge_band_px_on_smooth_backdrop": 5829, "edge_step_p99_all_boundary": 2.36, "edge_step_p99_levels_per_px": 1.12, "edge_step_max": 2.36, "smoke_pixel_mean_rgb": [130.9, 97.0, 88.0], "plume_mean_s": 0.249, "through_px": 6899, "through_corr": 0.925, "transmission_est": 0.602}`
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
