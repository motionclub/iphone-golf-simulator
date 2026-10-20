GATE: MALE_FORM FAIL

Latest direct user instruction: **each bald view ≤2.0%**. This supersedes the stored goal/brief’s older 5% rule. The 2% gate remains unmet.

| Authority view | Difference pixels | Union pixels | Blender error | Unity error | Blender–Unity difference | 2% gate |
|---|---:|---:|---:|---:|---:|---|
| bald_front | 2,865 | 74,937 | 3.8232% | 3.9332% | 0.6669% | FAIL |
| bald_back | 2,743 | 74,117 | 3.7009% | 3.6568% | 0.6149% | FAIL |

| Binary eye check | Flag | Evidence |
|---|---|---|
| ARMS_SIDE | PASS | Left/right profiles show closed rounded deltoid, upper-arm and forearm depth; wrist narrows continuously. No thin arm cards. |
| CHIN | FAIL | The old beard/stubble cap is absent, and front throat/rear neck contour depth is closer to the fixed head-detail profile. Chin curvature, uneven jaw surface and neck/shoulder transition still differ visibly in all-around Blender and saved Unity captures; matching the sampled central calipers alone is insufficient for PASS. |
| FEET_SIDE | PASS | Both profiles show a rounded toe box, sloped instep, ankle and heel; a broad low sole can plant on the ground. No old twisted slab. |
| SHOULDERS | PASS | Full rounded deltoid at both arm joins. Folded front/rear deltoid/torso triangles were locally unfolded; the previous horizontal cavity/crease is absent in front, back and three-quarter proof. |
| WAIST | PASS | Waist tapers below the chest and widens toward the hips without the former waist shelf/love-handle ridge. Front/back and three-quarter views reviewed. |

These flags cover the five requested geometry defects, reviewed in Blender and the actual saved Unity prefab. They are not a claim that the full face or hands match the finished plate; those remain unpolished.

Continued the existing `HeroBase_Male_Silhouette.blend`, revising only `Body_M` vertex coordinates. No remesh, replacement mesh, female work, hair, rig or face textures. METRIC scale 1; A-pose; height 1.702187 m; 24,578 vertices / 49,176 triangles. Connectivity, body transform/origin, all six locked reference cameras and three packed plates are unchanged. This second resumed head stage corrects anterior cranial depth, the lower facial plane and both anterior/posterior neck contours against fixed head-detail profile calipers. Body below the 1.36 m lower-neck transition is exactly unchanged from the stage-2 checkpoint; all X/Z coordinates are unchanged. Full head likeness and CHIN remain FAIL because surface curvature and transitions still differ visibly; cosmetic features are a separate appearance preview.

Fresh FBX export and independent Blender re-import verification: PASS, maximum coordinate difference 0.0002794 mm. Unity: importer scale 1, file scale 1, compression off, saved normals imported; one opaque plain grey URP Lit renderer, no hair. The main `HeroBase_Male` prefab uses this current FBX. All seven captures were taken in Play Mode and checked against their recorded SHA-256 values.

Foot contact: 318 vertices below 4 mm, lowest contact 2.472 mm. Female source, exports and prefabs retain their prerequisite hashes.

The frozen front and reflected back masks disagree by 6.2479% in continuous world space. One closed mesh has a shared X/Z outline in these opposite orthographic views. The Jaccard triangle inequality places at least one continuous view at ≥3.1239%. This documents why a clean physical 2% fit conflicts with the authority pair. Native raster sampling adds boundary quantization, so this continuous bound is not presented as an exact impossibility proof for the separate native pixel gate. The actual gate remains the unchanged native XOR/union measurement above; the model is not claimed to attain the minimax optimum. Cameras, masks and reference images were not altered.

Proof: `01_silhouette_overlay_m.png` (native pink/green disagreement); `01d_form_m.png` (five Blender body views plus details); `03_unity_m.png` (five actual Unity body views plus details); `01e_head_all_around_m.png` (eight head directions plus top). Side views inform the arm/foot eye checks and do not introduce a separate numeric silhouette gate.

Saved blend SHA-256: `8da71e595209e5aaae165e509525406c6fac76d2df9b69148ac991bb7c2dcf3b`
Source and Unity FBX SHA-256: `5d871c49c07af3e0255fd7e56a37e91ddb06d1ddbdcd7c7fd78e20774477611a`
Unity prefab SHA-256: `f65086bee4edcb9fca339ee58ba4f81a7a851e9428e95757f3354c43738a3338`
