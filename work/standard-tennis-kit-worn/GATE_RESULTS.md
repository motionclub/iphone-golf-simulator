# STANDARD_TENNIS_KIT_WORN - GATE_RESULTS (staged only: nothing under ArtDir written, no body edit, no racket edit)

**GATE: STANDARD_TENNIS_KIT_WORN PASS**

Starting point: work/standard-tennis-kit-wb (tucked polo, ~3 mm shrink-wrap, skirt hem z 0.70 with the liner showing below it). Rebuilt in work/standard-tennis-kit-worn/ with the same SDF-fit pipeline, 
sock/shoe designs kept; every piece is now a closed double-walled shell, the polo is untucked, the bottom carries a lofted contrasting waistband, the female skirt is mid-thigh.

| Gate | Result |
|---|---|
| UNTUCKED_HEM | PASS |
| WAISTBAND_CONTRAST | PASS |
| SKIRT_COVERS | PASS |
| WORN_SHELL | PASS |
| NO_SKIN_FLASH | PASS |
| NO_LOGOS | PASS |
| BODY_SHA_UNCHANGED | PASS |
| SWAPPABLE | PASS |
| EXPORT | PASS |
| PROOFS | PASS |

## Evidence

### UNTUCKED_HEM - PASS
- male: polo hem overlaps the band top 15.85-20.11 mm (mean 17.61); polo<->bottom overlapping triangle pairs 0; polo inner wall stands 1.51 mm outside the band; 19.89-24.15 mm of the band visible below the hem; top and bottom are separate objects (fused=False)
- female: polo hem overlaps the band top 15.79-19.8 mm (mean 17.84); polo<->bottom overlapping triangle pairs 0; polo inner wall stands 2.06 mm outside the band; 20.2-24.21 mm of the band visible below the hem; top and bottom are separate objects (fused=False)

### WAISTBAND_CONTRAST - PASS
- male: white kit = fabric Std_White_Lit [0.93, 0.93, 0.93] + band Std_Black_Lit [0.035, 0.035, 0.04] (black on white); black kit = fabric Std_Black_Lit + band Std_White_Lit (white on black); band = 2880 faces on Kit_Bottom_Shorts_M_White (slot 2), polo uses no band slot; band 40.0 mm tall
- female: white kit = fabric Std_White_Lit [0.93, 0.93, 0.93] + band Std_Black_Lit [0.035, 0.035, 0.04] (black on white); black kit = fabric Std_Black_Lit + band Std_White_Lit (white on black); band = 2880 faces on Kit_Bottom_Skort_F_White (slot 2), polo uses no band slot; band 40.0 mm tall

### SKIRT_COVERS - PASS
- outer skirt hem z 0.6289 = 55% of the way from crotch (z 0.8000000000000004) to knee (z 0.4900000000000001): mid-thigh is z 0.645; the previous skirt hem was z 0.700
- inner-short (liner) hem z 0.7291 -> skirt is 100.3 mm longer than the inner shorts
- ray test: 4593 liner faces x 433268 camera rays (elevations [-5, 0, 8, 22, 40] deg, every 15 deg of azimuth), a face counts as visible only if a 1.0 mm beam (5 exact rays) reaches it first: visible faces = 0
- disclosed: 1 face/view pair(s) where a single zero-width centre ray slips through a ~0.3 mm slit between the waistband's bottom edge and the skirt's top lap but no 1 mm beam can ([{'face': 3018, 'el': 40, 'az': 120.0, 'centroid': [-0.1002, 0.0791, 0.9493], 'tag': 'liner_rim0'}]); a camera pixel is ~2 mm wide at the proof distance, and the render test below shows 0 liner pixels
- render test (liner painted magenta, 4 elevations x 12 azimuths per kit): magenta pixels White 0 / Black 0 at 0/+8/+22 deg; below the horizon (-12 deg) 0/0; positive control (skirt hidden) shows the liner
- informational: looking UP under the hem from [-45, -30, -15] deg the inside of any skirt is visible (1643 liner faces); not a proof view

### WORN_SHELL - PASS
- male: every piece a closed manifold (0 boundary / 0 non-manifold / 0 inconsistent edges): True; wall thickness median mm {'Kit_Top_Polo_M': 3.0, 'Kit_Bottom_Shorts_M': 3.0, 'Kit_Sock_L': 2.0, 'Kit_Sock_R': 2.0, 'Kit_Shoe_L': 3.6, 'Kit_Shoe_R': 3.6} (5th-percentile wall over every part 1.98 mm); polo waist/hip inner clearance min 9.65 mm (median 13.31); bottom min 6.08 mm; vertices inside the body 0; triangles intersecting the body 0
- female: every piece a closed manifold (0 boundary / 0 non-manifold / 0 inconsistent edges): True; wall thickness median mm {'Kit_Top_Polo_F': 3.0, 'Kit_Bottom_Skort_F': 2.0, 'Kit_Sock_L': 2.0, 'Kit_Sock_R': 2.0, 'Kit_Shoe_L': 3.6, 'Kit_Shoe_R': 3.6} (5th-percentile wall over every part 1.74 mm); polo waist/hip inner clearance min 7.77 mm (median 14.34); bottom min 6.4 mm; vertices inside the body 0; triangles intersecting the body 0
- disclosed: female polo, hidden rib/sleeve crevice (hanging arm 34 mm off the ribs): min 0.5 mm (median 11.05), never negative - relaxed on purpose, see polo.py

### NO_SKIN_FLASH - PASS
- male: 2880 skin samples between z 0.895 and 1.05 x 125792 camera rays ([-10, 0, 10, 25] deg elevation, 15 deg azimuth steps, 1 mm beam, exact ray-triangle): exposed 0
- female: 2970 skin samples between z 0.925 and 1.085 x 122665 camera rays ([-10, 0, 10, 25] deg elevation, 15 deg azimuth steps, 1 mm beam, exact ray-triangle): exposed 0

### NO_LOGOS - PASS
- male: images in blend [], image-texture materials [], text objects [], object types ['EMPTY', 'MESH'], part vocabulary has no logo/text/brand part (48 tags: tone-on-tone seams, piping, buttons, laces)
- female: images in blend [], image-texture materials [], text objects [], object types ['EMPTY', 'MESH'], part vocabulary has no logo/text/brand part (53 tags: tone-on-tone seams, piping, buttons, laces)

### BODY_SHA_UNCHANGED - PASS
- male: fd04bc28.. before == fd04bc28.. after
- female: 200dc3b9.. before == 200dc3b9.. after
- female_arms_candidate: 573ab443.. before == 573ab443.. after

### SWAPPABLE - PASS
- male: sockets ['Chest_Top', 'Foot_L_Shoe', 'Foot_R_Shoe', 'Hip_Bottom']; every piece parented to its socket (True), identity world transform True, distinct mesh data True, top/bottom fused False; hierarchy survives the FBX round trip True
- female: sockets ['Chest_Top', 'Foot_L_Shoe', 'Foot_R_Shoe', 'Hip_Bottom']; every piece parented to its socket (True), identity world transform True, distinct mesh data True, top/bottom fused False; hierarchy survives the FBX round trip True

### EXPORT - PASS
- male: StandardKit_Male.blend (19.7 MB, sha ad07a7b9ba..)
- female: StandardKit_Female.blend (9.4 MB, sha f19a9c0378..)
- StdKit_Male_White.fbx: 3.22 MB, 6 meshes + 4 socket empties, 87554 tris, scale 1 m (max object scale deviation 0.0), round-trip max vertex error 0.0001 mm, normals max 0.115 deg, UVs kept
- StdKit_Male_Black.fbx: 3.22 MB, 6 meshes + 4 socket empties, 87554 tris, scale 1 m (max object scale deviation 0.0), round-trip max vertex error 0.0001 mm, normals max 0.115 deg, UVs kept
- StdKit_Female_White.fbx: 2.85 MB, 6 meshes + 4 socket empties, 77380 tris, scale 1 m (max object scale deviation 0.0), round-trip max vertex error 0.0001 mm, normals max 0.097 deg, UVs kept
- StdKit_Female_Black.fbx: 2.85 MB, 6 meshes + 4 socket empties, 77380 tris, scale 1 m (max object scale deviation 0.0), round-trip max vertex error 0.0001 mm, normals max 0.097 deg, UVs kept
- StdKit_Female_White_ArmsCandFit.fbx: 2.9 MB, 6 meshes + 4 socket empties, 78826 tris, scale 1 m (max object scale deviation 0.0), round-trip max vertex error 0.0001 mm, normals max 0.097 deg, UVs kept
- StdKit_Female_Black_ArmsCandFit.fbx: 2.9 MB, 6 meshes + 4 socket empties, 78826 tris, scale 1 m (max object scale deviation 0.0), round-trip max vertex error 0.0001 mm, normals max 0.097 deg, UVs kept
- Unity 6000.3.24f1 scratch import (outside the repo): PASS - scale 1, hierarchy under the sockets, UV + normals, world bounds vs Blender < 1 mm (proof/unity_import_report.json)

### PROOFS - PASS
- 14 of 14 sheets present in proof/: ONBODY_Male.png, ONBODY_Female.png, WAIST_Male.png, WAIST_Female.png, HEM_Female.png, LINER_MASK_Female.png, EXPLODED_Male.png, EXPLODED_Female.png, OBJECT_ID_Male.png, OBJECT_ID_Female.png, SECTIONS_Male.png, SECTIONS_Female.png, CLEARANCE_Male.png, CLEARANCE_Female.png
- proof/checks.json

## TRI per piece (white == black)

| piece | male | female |
|---|---|---|
| Kit_Top_Polo | 22298 | 19408 |
| Kit_Bottom | 21032 | 25646 |
| Kit_Sock_L | 6270 | 5812 |
| Kit_Sock_R | 6270 | 5800 |
| Kit_Shoe_L | 15880 | 10328 |
| Kit_Shoe_R | 15804 | 10386 |
| **total** | **87554** (was 52,557) | **77380** (was 51,978) |

## Min clearance to the authority body (mm)

| piece | male all / inner | female all / inner |
|---|---|---|
| Kit_Top_Polo | 7.0 / 7.0 | 0.5 / 0.5 |
| Kit_Bottom | 6.08 / 11.11 | 6.4 / 6.8 |
| Kit_Sock_L | 2.55 / 2.55 | 2.55 / 2.55 |
| Kit_Sock_R | 2.9 / 2.9 | 2.91 / 2.91 |
| Kit_Shoe_L | 4.86 / 4.86 | 5.12 / 5.12 |
| Kit_Shoe_R | 4.89 / 4.89 | 5.35 / 5.35 |

## Disclosed limits

- Triangle count is up 67 % (male) / 49 % (female): every piece is now a closed shell with an inner wall; the inner walls are the cheapest place to decimate if the budget needs it.
- Female polo: where the hanging arm sits ~34 mm off the ribs the two shell offsets cannot both stay at full ease (they fuse into one membrane and the sleeve cut tears the side wall). The torso side wall (8.5 mm) and the sleeve inner side (3.5 mm) are relaxed in that hidden crevice only; its minimum inner clearance is 0.5 mm, never negative.
- Visible band: 40 mm band; the polo hem covers its top 15.8-20 mm and the fabric laps its bottom 5.5 mm, so 20-24 mm of contrast colour shows between shirt and bottom.
- Looking UP under the skirt hem from below the horizon shows the inside of the skirt (as with any skirt); the proof views and the camera range -5..+40 deg are fully covered.
- Male shorts legs are now two separate tubes (the previous kit fused them into one trunk).
- Female socks/sneakers are still fit to the authority body's placeholder feet (as before); an ArmsCandFit footwear set is carried over in StdKit_Female_*_ArmsCandFit.fbx.
- Static shells fitted to the bind pose; no rig/skin weights; sockets are empties parenting identity-transform meshes.

Untouched check: ArtDir files modified since this job started: 226 {'.txt': 6, '.jpg': 20, '.png': 200} - all proof images / prompt notes written by the other chats that share this repo; model files (.blend/.fbx/.obj/...) modified under ArtDir: 0; the only ArtDir paths this job's scripts reference are the two READ-ONLY authority body files (SHA unchanged); classic-tennis-racket files modified: 0.

Rebuild: scripts/run_all.sh (parts -> assemble -> FBX -> checks -> proofs -> sheets) then scripts/final_report.py.