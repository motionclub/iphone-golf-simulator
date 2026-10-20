GATE: MALE_FORM FAIL

Latest direct user instruction: **each bald view ≤2.0%**. This supersedes the stored goal/brief’s older 5% rule. The 2% gate remains unmet.

| Authority view | Difference pixels | Union pixels | Blender error | Unity error | Blender–Unity difference | 2% gate |
|---|---:|---:|---:|---:|---:|---|
| bald_front | 2,831 | 75,001 | 3.7746% | 3.8826% | 0.6414% | FAIL |
| bald_back | 2,807 | 74,222 | 3.7819% | 3.7642% | 0.6001% | FAIL |

| Binary eye check | Flag | Evidence |
|---|---|---|
| ARMS_SIDE | PASS | Left/right profiles show closed rounded deltoid, upper-arm and forearm depth; wrist narrows continuously. No thin arm cards. |
| CHIN | FAIL | Old beard/stubble cap absent. Local jaw/under-chin/neck depth sculpt reduces surface ripples and retains the improved central reference profile. Lower-jaw curvature and neck transition remain visibly different in actual all-around Blender and saved Unity proof; no chin likeness PASS. |
| FEET_SIDE | PASS | Both profiles show a rounded toe box, sloped instep, ankle and heel; a broad low sole can plant on the ground. No old twisted slab. |
| SHOULDERS | PASS | Full rounded deltoid at both arm joins. Folded front/rear deltoid/torso triangles were locally unfolded; the previous horizontal cavity/crease is absent in front, back and three-quarter proof. |
| WAIST | PASS | Waist tapers below the chest and widens toward the hips without the former waist shelf/love-handle ridge. Front/back and three-quarter views reviewed. |

These flags cover the five requested geometry defects, reviewed in Blender and the actual saved Unity prefab. They are not a claim that the full face or hands match the finished plate; those remain unpolished.

Continued the existing `HeroBase_Male_Silhouette.blend`, revising only `Body_M` vertex coordinates. No remesh, replacement mesh, female work, hair, rig or face textures. METRIC scale 1; A-pose; height 1.702187 m; 24,578 vertices / 49,176 triangles. Connectivity, body transform/origin, all six locked reference cameras and three packed plates are unchanged. This fourth resumed stage repairs stretched distal-hand/thumb coordinates using verified existing vertex correspondence, a continuous wrist falloff, shared front/back palm/finger envelopes and reduced excessive distal-hand depth. All vertices outside the distal-hand region, including the head/neck, torso and legs, are exactly unchanged from this stage checkpoint. Full head likeness and CHIN remain FAIL; fingers remain an unfinished blockout. Cosmetic features are a separate appearance preview.

Fresh FBX export and independent Blender re-import verification: PASS, maximum coordinate difference 0.0002794 mm. Unity: importer scale 1, file scale 1, compression off, saved normals imported; one opaque plain grey URP Lit renderer, no hair. The main `HeroBase_Male` prefab uses this current FBX. All seven captures were taken in Play Mode and checked against their recorded SHA-256 values.

Foot contact: 318 vertices below 4 mm, lowest contact 2.472 mm. Female source, exports and prefabs retain their prerequisite hashes.

The frozen front and reflected back masks disagree by 6.2479% in continuous world space. One closed mesh has a shared X/Z outline in these opposite orthographic views. The Jaccard triangle inequality places at least one continuous view at ≥3.1239%. This documents why a clean physical 2% fit conflicts with the authority pair. Native raster sampling adds boundary quantization, so this continuous bound is not presented as an exact impossibility proof for the separate native pixel gate. The actual gate remains the unchanged native XOR/union measurement above; the model is not claimed to attain the minimax optimum. Cameras, masks and reference images were not altered.

Proof: `01_silhouette_overlay_m.png` (native pink/green disagreement); `01d_form_m.png` (five Blender body views plus details); `03_unity_m.png` (five actual Unity body views plus details); `01e_head_all_around_m.png` (eight head directions plus top). Side views inform the arm/foot eye checks and do not introduce a separate numeric silhouette gate.

Saved blend SHA-256: `d39c6c5e5157ff15428759c01eaa227a09ea1bcd4b0d1a51acfe4110795d2413`
Source and Unity FBX SHA-256: `5dd325f0a77c30605ffa2d78b4c6457dd13781664cf5b9d716e8390aa7e3565d`
Unity prefab SHA-256: `f65086bee4edcb9fca339ee58ba4f81a7a851e9428e95757f3354c43738a3338`
