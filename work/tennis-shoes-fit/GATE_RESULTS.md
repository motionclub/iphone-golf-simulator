# TENNIS_SHOES_FIT - GATE_RESULTS

**GATE: TENNIS_SHOES_FIT PASS**

Shoes and the socks rebuilt on the two body blends named in the brief; nothing under ArtDir written, bodies read-only (SHA verified before and after), polo and bottom untouched.

| Gate | Result |
|---|---|
| FOOT_INSIDE | PASS |
| TOE_COVERED | PASS |
| HEEL_COVERED | PASS |
| NO_SKIN_GAP | PASS |
| SOLE_GROUNDED | PASS |
| MIRROR | PASS |
| OTHER_PIECES_UNCHANGED | PASS |
| BODY_UNCHANGED | PASS |
| ON_THESE_FEET | PASS |
| NO_ARMS_CAND | PASS |
| SOCKETS | PASS |

Numbers are measured on the assembled output blends (`export/StandardKit_Male.blend`, `export/StandardKit_Female.blend`), definitions in `GATE_DEFS_preregistered.md` (written before the final measurement run; one disclosed refinement, see below).

## Evidence

### FOOT_INSIDE - PASS
- male R: 1661 foot vertices (and 3310 triangle centroids) below the lowest collar point (103.6 mm): outside the shoe 0 (inside shoe material 0+0, not enclosed 0+0); nearest skin to shoe 4.87 mm (5th pct 7.93 mm); foot-vs-shoe triangle pairs 0; all 2004 leg vertices up to the highest collar point (158.1 mm): inside shoe material 0; sock vertices below the collar 1418: inside shoe material 0, not enclosed 0; sock inner wall >= 2.9 mm off the skin
- male L: 1661 foot vertices (and 3308 triangle centroids) below the lowest collar point (103.6 mm): outside the shoe 0 (inside shoe material 0+0, not enclosed 0+0); nearest skin to shoe 4.87 mm (5th pct 7.81 mm); foot-vs-shoe triangle pairs 0; all 2004 leg vertices up to the highest collar point (158.1 mm): inside shoe material 0; sock vertices below the collar 1428: inside shoe material 0, not enclosed 0; sock inner wall >= 2.55 mm off the skin
- male: layer intersections (triangle pairs): sock vs shoe 0/0, shoe vs body 0/0, sock vs body 0/0, shoe vertices inside sock material 0/0, left vs right shoe 0
- female R: 682 foot vertices (and 1367 triangle centroids) below the lowest collar point (87.4 mm): outside the shoe 0 (inside shoe material 0+0, not enclosed 0+0); nearest skin to shoe 4.63 mm (5th pct 7.36 mm); foot-vs-shoe triangle pairs 0; all 804 leg vertices up to the highest collar point (116.1 mm): inside shoe material 0; sock vertices below the collar 1100: inside shoe material 0, not enclosed 0; sock inner wall >= 4.2 mm off the skin
- female L: 684 foot vertices (and 1368 triangle centroids) below the lowest collar point (87.4 mm): outside the shoe 0 (inside shoe material 0+0, not enclosed 0+0); nearest skin to shoe 4.63 mm (5th pct 7.36 mm); foot-vs-shoe triangle pairs 0; all 803 leg vertices up to the highest collar point (116.1 mm): inside shoe material 0; sock vertices below the collar 1095: inside shoe material 0, not enclosed 0; sock inner wall >= 2.89 mm off the skin
- female: layer intersections (triangle pairs): sock vs shoe 0/0, shoe vs body 0/0, sock vs body 0/0, shoe vertices inside sock material 0/0, left vs right shoe 0

### TOE_COVERED - PASS
- male R: longest toe tip at [0.1684, -0.2236, 0.0301]; inner wall of the upper +9.6 mm past it, outside of the shoe +19.3 mm past it (along the foot axis, toe-out 3.27 deg)
- male L: longest toe tip at [-0.1684, -0.2236, 0.0301]; inner wall of the upper +9.6 mm past it, outside of the shoe +19.3 mm past it (along the foot axis, toe-out -3.44 deg)
- male: skin samples below the cuff band reachable by a camera ray from the front sector: 0 (all sectors 0 of 467,200 rays)
- female R: longest toe tip at [0.1011, -0.1396, 0.0095]; inner wall of the upper +8.1 mm past it, outside of the shoe +17.6 mm past it (along the foot axis, toe-out 6.31 deg)
- female L: longest toe tip at [-0.1011, -0.1396, 0.0095]; inner wall of the upper +8.1 mm past it, outside of the shoe +17.6 mm past it (along the foot axis, toe-out -6.29 deg)
- female: skin samples below the cuff band reachable by a camera ray from the front sector: 0 (all sectors 0 of 204,419 rays)

### HEEL_COVERED - PASS
- male R: heel point at [0.2087, 0.0847, 0.0395]; inner wall of the upper +8.6 mm past it, outside of the shoe +18.3 mm past it (along the foot axis, toe-out 3.27 deg)
- male L: heel point at [-0.2083, 0.0846, 0.0395]; inner wall of the upper +8.7 mm past it, outside of the shoe +18.3 mm past it (along the foot axis, toe-out -3.44 deg)
- male: skin samples below the cuff band reachable by a camera ray from the rear sector: 0 (all sectors 0 of 467,200 rays)
- female R: heel point at [0.1133, 0.1036, 0.0441]; inner wall of the upper +8.1 mm past it, outside of the shoe +16.6 mm past it (along the foot axis, toe-out 6.31 deg)
- female L: heel point at [-0.1083, 0.1028, 0.0526]; inner wall of the upper +8.4 mm past it, outside of the shoe +16.8 mm past it (along the foot axis, toe-out -6.29 deg)
- female: skin samples below the cuff band reachable by a camera ray from the rear sector: 0 (all sectors 0 of 204,419 rays)

### NO_SKIN_GAP - PASS
- male: skin of both legs from the ground to 270 mm (sock top - 30 mm): 9,824 samples x 467,200 camera rays (24 azimuths x elevations -10/0/10/25/45 deg, 1 mm beam, exact ray-triangle): exposed 0
- male: informational, the cuff band itself (270-296 mm): 655 grazing samples seen from above through the open top edge of the sock (not next to the shoe)
- male R: sock top at z 301.8 mm = 143.7 mm above the HIGHEST collar point (198.1 mm above the lowest); sock continues 107.9 mm below the lowest collar point down to the insole (z -4.3 mm) -> sock-to-collar overlap 107.9 mm
- male L: sock top at z 301.8 mm = 143.7 mm above the HIGHEST collar point (198.1 mm above the lowest); sock continues 107.9 mm below the lowest collar point down to the insole (z -4.3 mm) -> sock-to-collar overlap 107.9 mm
- female: skin of both legs from the ground to 255 mm (sock top - 30 mm): 4,323 samples x 204,419 camera rays (24 azimuths x elevations -10/0/10/25/45 deg, 1 mm beam, exact ray-triangle): exposed 0
- female: informational, the cuff band itself (255-281 mm): 244 grazing samples seen from above through the open top edge of the sock (not next to the shoe)
- female R: sock top at z 286.7 mm = 170.6 mm above the HIGHEST collar point (199.3 mm above the lowest); sock continues 94.2 mm below the lowest collar point down to the insole (z -6.8 mm) -> sock-to-collar overlap 94.2 mm
- female L: sock top at z 286.7 mm = 170.6 mm above the HIGHEST collar point (199.3 mm above the lowest); sock continues 94.2 mm below the lowest collar point down to the insole (z -6.8 mm) -> sock-to-collar overlap 94.2 mm

### SOLE_GROUNDED - PASS
- male: sole bottom z L/R White -28.500/-28.500 mm, Black -28.500/-28.500 mm; tread bottom -30.500/-30.500 mm; lowest vertex of the shoe -30.500 mm (spread over all four 0.0000 mm)
- female: sole bottom z L/R White -23.500/-23.500 mm, Black -23.500/-23.500 mm; tread bottom -25.500/-25.500 mm; lowest vertex of the shoe -25.500 mm (spread over all four 0.0000 mm)

### MIRROR - PASS
- male: right shoe reflected across x = 0 vs left shoe: max distance 0.00000 mm (both ways); a same-facing translated copy would differ by 28.88 mm; signed volume R 1518.21 cm3 / L 1518.21 cm3 (both positive = outward windings); length 345.33/345.33 mm; sole height 28.5/28.5 mm; tris 17678/17678
- female: right shoe reflected across x = 0 vs left shoe: max distance 0.00000 mm (both ways); a same-facing translated copy would differ by 26.92 mm; signed volume R 740.81 cm3 / L 740.81 cm3 (both positive = outward windings); length 277.19/277.19 mm; sole height 23.5/23.5 mm; tris 12910/12910

### OTHER_PIECES_UNCHANGED - PASS
- male Kit_Bottom_Shorts_M_Black: start 610cd446f18bb2a5...  output 610cd446f18bb2a5...  identical
- male Kit_Bottom_Shorts_M_White: start 97a83afeddd71b9c...  output 97a83afeddd71b9c...  identical
- male Kit_Top_Polo_M_Black: start c0f0b805460e8d6f...  output c0f0b805460e8d6f...  identical
- male Kit_Top_Polo_M_White: start 2c18d0642a15967d...  output 2c18d0642a15967d...  identical
- female Kit_Bottom_Skort_F_Black: start 136d992c35723df6...  output 136d992c35723df6...  identical
- female Kit_Bottom_Skort_F_White: start 0c40983d28dba38a...  output 0c40983d28dba38a...  identical
- female Kit_Top_Polo_F_Black: start d5b0464c91354362...  output d5b0464c91354362...  identical
- female Kit_Top_Polo_F_White: start c27677367685ddfb...  output c27677367685ddfb...  identical

### BODY_UNCHANGED - PASS
- male: body blend SHA before d6c4dcfb1150853a... == after d6c4dcfb1150853a... == expected d6c4dcfb1150853a...; FitRef copy in the output blend vs the source mesh: max vertex difference 0.0 mm, same triangles True; start kit blend SHA before ad07a7b9ba984b0f... after ad07a7b9ba984b0f...
- female: body blend SHA before a1d73a334f4dc180... == after a1d73a334f4dc180... == expected a1d73a334f4dc180...; FitRef copy in the output blend vs the source mesh: max vertex difference 0.0 mm, same triangles True; start kit blend SHA before f19a9c03789b7af3... after f19a9c03789b7af3...

### ON_THESE_FEET - PASS
- male: fit built and measured on merged_fd04bc28.blend SHA d6c4dcfb1150853a... (verified at build, assembly and check time)
- male: control - the START kit measured the same way on this body: foot vertices below the collar outside its shoe R 0 / L 0 (toe +9.5 mm, heel +8.7 mm)
- female: fit built and measured on HeroBase_Female_FULL_STAGED.blend SHA a1d73a334f4dc180... (verified at build, assembly and check time)
- female: control - the START kit measured the same way on this body: foot vertices below the collar outside its shoe R 250 / L 258 (toe -3.9 mm, heel -35.2 mm)
- scripts read only the two body blends above (kitlib.py has no other body path); the start kit blends are read only for the untouched pieces and for the control

### NO_ARMS_CAND - PASS
- male: objects/meshes/materials/collections whose name contains ArmsCand: []; FitRef objects ['FitRef_Body_M']; removed from the start blend: ['FitRef_Body_M'], collections []
- female: objects/meshes/materials/collections whose name contains ArmsCand: []; FitRef objects ['FitRef_Body_F']; removed from the start blend: ['FitRef_Body_F_ArmsCandidate', 'Kit_Shoe_L_ArmsCandFit_Black', 'Kit_Shoe_L_ArmsCandFit_White', 'Kit_Shoe_R_ArmsCandFit_Black', 'Kit_Shoe_R_ArmsCandFit_White', 'Kit_Sock_L_ArmsCandFit_Black', 'Kit_Sock_L_ArmsCandFit_White', 'Kit_Sock_R_ArmsCandFit_Black', 'Kit_Sock_R_ArmsCandFit_White', 'FitRef_Body_F'], collections ['Kit_Black_FitArmsCand', 'Kit_White_FitArmsCand']

### SOCKETS - PASS
- male: Kit_Shoe_L / Kit_Sock_L -> Foot_L_Shoe_<colour>, Kit_Shoe_R / Kit_Sock_R -> Foot_R_Shoe_<colour> (socket_name Foot_L_Shoe / Foot_R_Shoe), 16 pieces, all closed meshes with an identity world transform; the four foot sockets have an identity transform (they sat at [-0.18, 0.0, 0.09] / [0.18, 0.0, 0.09] in the start blend; nothing else moved); armature objects in the blend: [] (no foot bone exists)
- female: Kit_Shoe_L / Kit_Sock_L -> Foot_L_Shoe_<colour>, Kit_Shoe_R / Kit_Sock_R -> Foot_R_Shoe_<colour> (socket_name Foot_L_Shoe / Foot_R_Shoe), 16 pieces, all closed meshes with an identity world transform; the four foot sockets have an identity transform (they sat at [-0.125, 0.0, 0.08] / [0.125, 0.0, 0.08] in the start blend; nothing else moved); armature objects in the blend: [] (no foot bone exists)

## The brief's numbers (also flat in `checks.json` -> `summary`)

| | male | female |
|---|---|---|
| foot vertices below the collar outside the shoe (L / R) | 0 / 0 (of 1661 / 1661) | 0 / 0 (of 684 / 682) |
| collar rim height above the foot sole: min / mean / max (mm) | 103.6 / 125.5 / 158.1 | 87.4 / 99.7 / 116.1 |
| collar rim above the ground plane (mm): min / mean / max | 134.1 / 156.0 / 188.6 | 112.9 / 125.2 / 141.6 |
| toe overhang, inner wall / outside (mm), L / R | 9.6 / 9.6  and  19.3 / 19.3 | 8.1 / 8.1  and  17.6 / 17.6 |
| heel overhang, inner wall / outside (mm), L / R | 8.7 / 8.6  and  18.3 / 18.3 | 8.4 / 8.1  and  16.8 / 16.6 |
| sock-to-collar overlap (mm): min / sock above the highest collar point / sock below the lowest | 107.9 / 143.7 / 107.9 | 94.2 / 170.6 / 94.2 |
| polo / bottom mesh SHA unchanged | True / True | True / True |

## Foot landmarks measured on these bodies (body space, metres)

- male R: longest toe tip [0.1684, -0.2236, 0.0301], heel point [0.2087, 0.0847, 0.0395], instep high point [0.1922, -0.0664, 0.1325], instep/shin junction z 0.135, narrowest ankle z 0.18 (90.4 cm2), foot length 305.5 mm, toe-out 3.27 deg
- male L: longest toe tip [-0.1684, -0.2236, 0.0301], heel point [-0.2083, 0.0846, 0.0395], instep high point [-0.1912, -0.0664, 0.1325], instep/shin junction z 0.135, narrowest ankle z 0.18 (91.6 cm2), foot length 305.3 mm, toe-out -3.44 deg
- female R: longest toe tip [0.1011, -0.1396, 0.0095], heel point [0.1133, 0.1036, 0.0441], instep high point [0.1176, -0.0022, 0.0907], instep/shin junction z 0.095, narrowest ankle z 0.135 (37.6 cm2), foot length 240.4 mm, toe-out 6.31 deg
- female L: longest toe tip [-0.1011, -0.1396, 0.0095], heel point [-0.1083, 0.1028, 0.0526], instep high point [-0.1176, -0.0022, 0.0907], instep/shin junction z 0.095, narrowest ankle z 0.135 (37.6 cm2), foot length 240.2 mm, toe-out -6.29 deg

## What changed, and what was decided

* **Start kit measured first.** On these bodies the START female shoes leave 250 / 258 foot vertices outside (62 / 67 inside the wall), the heel 35 mm and the toes 4 mm outside the cavity (the old fit was made to 200dc3b9's 183 mm placeholder foot; the real foot is 240 mm). The START male shoes already enclose his foot (0 outside, toe +9.5 mm, heel +8.7 mm): his feet are bit-identical to the body they were fit to (max vertex difference 0.0 mm below z 0.70). They were re-derived on this SHA anyway: same last, now built around the union of both feet so the left shoe is the exact mirror of the right.
* **Sock: the whole sock mesh was rebuilt, not only the cuff.** The female start sock stood up to 63 mm off the new legs and clipped the new heel/toes, so a cuff-only swap could not have fixed it. Same design (2 mm knit wall, ribbed cuff stands 1.4 mm proud, cuff ring), same names, slots, parents. The male sock came out vertex-identical to the start one (max difference 0.0 mm) because his leg did not change.
* **Collar** raised to the ankle (design heights side / back / front: female 90 / 114 / 117 mm, male 108 / 131 / 137 mm above the foot sole; start kit: female 76 / 91 / 101, male 88 / 106 / 118; realised rim mean 100 mm female / 125 mm male, instep-to-shin junction at 95 / 135 mm), smooth padded roll along a smoothed rim path; roll and tongue are pushed off the sock so no triangle of sock and shoe intersect.
* **Materials:** Std_White_Lit / Std_Black_Lit only. Sole + tread now use the piping slot (white on both kits): invisible on the white kit, a white sole on the black kit.
* **Sockets:** the four foot sockets were moved to an identity transform as the brief says (they sat at (+-0.125, 0, 0.08) female / (+-0.18, 0, 0.09) male). Kit meshes keep an identity world transform, so nothing moved visually. Neither body has an armature, so there is no foot bone to move.
* **FitRef** in each output blend is now a copy of THIS job's body (vertex-identical to the source), the old 200dc3b9 / arms-candidate reference bodies and every `*_ArmsCandFit_*` shoe/sock (objects, meshes, collections) were deleted.
* **Sole heights** unchanged from the start kit (female 23.5 mm, male 28.5 mm below the foot sole; tread 2 mm more), the ground plane convention stays z = -sole height.
* **Disclosed refinement of NO_SKIN_GAP:** the first run counted 244 exposed samples (female), all 6-18 mm below the sock top, seen from above through the open end of the sock. The zone was narrowed from `sock top - 4 mm` to `sock top - 30 mm` (below the cuff band); the cuff band is reported separately. Recorded in `GATE_DEFS_preregistered.md`.
* Not done (not asked): FBX/Unity export of the new shoes, the two `HeroBase_*_Dressed.blend` files in work/dressed-look still carry the old shoes, no ArtDir write.

## Untouched

- artdir_model_files_modified_since_job_start: 0 
- racket_files_modified_since_job_start: 0 
- body_dirs_model_files_modified_since_job_start: 0 
- kit_worn_model_files_modified_since_job_start: 0 
- dressed_look_model_files_modified_since_job_start: 0 

## Triangles

- male: Kit_Sock_L 6270, Kit_Sock_R 6270, Kit_Shoe_L 17678, Kit_Shoe_R 17678
- female: Kit_Sock_L 5082, Kit_Sock_R 5082, Kit_Shoe_L 12910, Kit_Shoe_R 12910

## Files

* `export/StandardKit_Male.blend`, `export/StandardKit_Female.blend` (+ `manifest_*.json`), `start/` = untouched copies of the start blends (SHA verified)
* `proof/FEET_<Hero>_<White|Black>.png` close-ups (both feet, side / front / heel / low 3/4), `proof/CUTAWAY_<Hero>.png` sections, `proof/BEFORE_AFTER_<Hero>.png`, `proof/CONTEXT_<Hero>.png`, raw cells in `proof/raw/`, `proof/checks.json`
* output blend SHA-256: male `a7e3d343563371586f4eabd36ea44b9072d7a46acd6b667ed3e363296bc7426d`, female `87514133967ca9cc85dd1450f5961f41cb37750db87118eeeccd58dce8a2677d` (each re-save of a blend changes its bytes; the geometry hashes above are the stable identity)
* rebuild: `scripts/run_all.sh`