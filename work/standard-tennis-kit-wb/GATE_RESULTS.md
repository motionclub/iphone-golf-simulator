# STANDARD_TENNIS_KIT_WB - GATE_RESULTS (staged only; ArtDir and Unity project untouched)
Body SHA-256 (verified unchanged): male fd04bc28..2347, female 200dc3b9..85cd, arms candidate 573ab443..5e0 (fit ref only), body FBX HeroBase_Male_Body a36b2010.. unchanged.
No file under ArtDir was written by this work (newer ArtDir files belong to another chat: racket_classic kit).

| Gate | Result | Evidence |
|---|---|---|
| KIT_MATCH_REF | PASS (author reading, Adnan's eye final) | proof/REF_VS_BUILD_*.png. Disclosed deviations: polo is modelled TUCKED (hem hidden in waistband, as in refs 01/02); ref's 3 parallel diagonal sneaker side stripes NOT copied (would read as a brand stripe mark) - single quarter seam instead; no ribbed-knit sock texture (geometry cuff band only); shorts/polo are fitted (tiny clearance per brief), refs are looser |
| COLORWAYS W+B | PASS | every piece in White (1 material) and Black (black + white piping only: polo 1216/936, shorts 1220, skort 1210 piping faces; socks/shoes none) - proof/mesh_qa.json |
| NO_LOGOS | PASS | no image textures/images in kit blends, only MESH + empty sockets, 3 materials (FitRef_Grey, Std_White_Lit, Std_Black_Lit); proof/CLOSEUPS_NoLogo_*.png |
| FIT_NO_INTERSECT | PASS | proof/fit_results.json: min clearance male polo +3.2, shorts +4.55, socks +2.8, shoes +4.3 mm; female polo +3.0, skort +2.41, socks +2.6, shoes +5.5 mm; 0 negative verts, 0 overlapping triangle pairs vs authority + candidate bodies; polo/bottom/sock/shoe layering 0 overlaps; skin-coverage (waist, shoulders, feet) 0 uncovered. Caveat: candidate's hanging hands/cupped thumb excluded for the skort (hands rest on the hip) |
| SEPARATE_MESH | PASS | Kit_Top_Polo, Kit_Bottom_Shorts/Skort, Kit_Sock_L/R, Kit_Shoe_L/R as separate objects, identity transforms, no modifiers, body not exported |
| MALE_AND_FEMALE | PASS | male polo+shorts+socks+sneakers; female polo+skort+socks+sneakers (primary set fit to authority body; ArmsCandFit footwear set alt for the 573ab443 limbs) |
| EXPORT | PASS | export/StandardKit_{Male,Female}.blend + 6 FBX (scale 1, same flags as body FBX); round trip: positions <=0.0002 mm, normals <=0.05 deg, UV + custom normals kept (export/fbx_verify.json); Unity 6000.3.24f1 scratch import PASS (proof/unity_import_report.json); URP Lit mats staged in unity_stage/ |
| PROOF_SHEETS | PASS | proof/ONBODY_*.png, PIECES_*.png, CLOSEUPS_NoLogo_*.png, CLEARANCE_*.png, SECTIONS_*.png, REF_VS_BUILD_*.png |

## TRI (disclosed, white/black identical)
Male 52,557 = polo 12,944 + shorts 11,893 + socks 6,976 + shoes 20,744. Female 51,978 = polo 11,199 + skort 19,814 + socks 6,902 + shoes 14,063 (alt ArmsCandFit footwear set: 52,197).

## Known limits
- Static shells fitted to the bind pose; no rig/skin weights. Sockets Chest_Top/Hip_Bottom/Foot_L_Shoe/Foot_R_Shoe are empties in the kit blends only.
- 3 sub-1.5 mm non-manifold edges in sock toes (hidden in shoe). Female authority feet are the baseline placeholders (184 mm), hence the ArmsCandFit footwear alt.
- Rebuild: scripts/build_parts.sh, fit_all.py, assemble.py, export_fbx.py, render_proofs.py, compose_proofs.py, compose_refs.py.
