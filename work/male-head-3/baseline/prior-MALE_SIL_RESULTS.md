GATE: MALE_SIL FAIL

Authority: ONLY `male_body_bald.jpg`, front/back, **each ≤2.0%**, per the latest human instruction. This replaces the historical 5% PASS for the earlier candidate.

| Authority view | Difference pixels | Union pixels | Blender error | Unity error | Blender–Unity difference | 2% gate |
|---|---:|---:|---:|---:|---:|---|
| bald_front | 2,865 | 74,937 | 3.8232% | 3.9332% | 0.6669% | FAIL |
| bald_back | 2,743 | 74,117 | 3.7009% | 3.6568% | 0.6149% | FAIL |

Continued the existing `HeroBase_Male_Silhouette.blend`, revising only `Body_M` vertex coordinates. No remesh, replacement mesh, female work, hair, rig or face textures. METRIC scale 1; A-pose; height 1.702187 m; 24,578 vertices / 49,176 triangles. Connectivity, body transform/origin, all six locked reference cameras and three packed plates are unchanged. This second resumed head stage corrects anterior cranial depth, the lower facial plane and both anterior/posterior neck contours against fixed head-detail profile calipers. Body below the 1.36 m lower-neck transition is exactly unchanged from the stage-2 checkpoint; all X/Z coordinates are unchanged. Full head likeness and CHIN remain FAIL because surface curvature and transitions still differ visibly; cosmetic features are a separate appearance preview.

Metric: count(reference XOR render) / count(reference OR render), each in the original 1280×720 image. Reference masks are the frozen source-only masks; Blender alpha >127. No refitting of masks, cameras, origins or image scales. Multiangle sheet views are excluded from the numeric gate; their locked cameras remain packed.

The frozen front and reflected back masks disagree by 6.2479% in continuous world space. One closed mesh has a shared X/Z outline in these opposite orthographic views. The Jaccard triangle inequality places at least one continuous view at ≥3.1239%. This documents why a clean physical 2% fit conflicts with the authority pair. Native raster sampling adds boundary quantization, so this continuous bound is not presented as an exact impossibility proof for the separate native pixel gate. The actual gate remains the unchanged native XOR/union measurement above; the model is not claimed to attain the minimax optimum. Cameras, masks and reference images were not altered.

Proof: `01_silhouette_overlay_m.png`.
Saved blend SHA-256: `8da71e595209e5aaae165e509525406c6fac76d2df9b69148ac991bb7c2dcf3b`
