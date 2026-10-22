# Correct-winding underarm checkpoint

GATE: Initial local-cloth-focused runtime FAIL. Its initial source PASS was invalid because the source raster selected back-facing triangles. Do not rely on the first source gate or first pixel-localization file.

GATE: Static49-face mask extension FAIL with corrected winding too. Across330views it creates new background in179views, entirely new holes in120views, max98holepixels and301totalnewbackgroundpixels. Keep mask2.

GATE: Corrected local-cloth-frontcull source coverage PASS; actual shader/LOD PENDING. This is a singleForehand1field, not whole-clothing completion.

The matrix palettes and rendererToRoot arrays in actual underarm-fit1 are bit-identical to source matrices17; the additive shape is100% and originalSleeve weights0. Runtime application was correct. Source winding was the discrepancy: normals align with cross products, so the software raster must keep positive screen-space area with its current camera basis/image Y direction. raster-front.c implements this. The corrected baseline and firstcandidate replay reproduce the actual tan strip.

Correct visible pixel rays at(375,498),(386,500),(365,492),(395,504) hit Body15928,6386,15929,6386 ahead of Top11424,11424,9123,5086 by21.55,20.02,25.33,20.69mm. Full coordinates/weights are in pixel-localization-frontcull.json. These are the negative-Z underarm side; the prior rays traced the opposed Body/back-facing cloth surface.

The single recommended next capture is local-cloth-frontcull/UnderarmTrace_Female.json. Source basis and vertexCount13932 are unchanged; one additiveForehand1anchor uses the existing28features, fullconfidence throughMSE.002 and zero by.04. Original mask2 and original sleeve-anchor family remain unchanged. No Body/rig/index/UV/weight edits.

A smooth plateau follows the exact facing cloth triangles behind13traced visible Body faces. Its edge correction keeps coincident UV aliases synchronized and spreads displacement across adjacent triangles when necessary to avoid fold reversals. Max posed displacement33.067mm, maxrest39.241mm.2956vertices move,2818by>1mm,2348by>20mm. This is wider than the first field, contained in the left garment (rest x−.213..−.054m,y1.045..1.357m,z−.099...123m). Shader shape and fold quality must be adjudicated from actual capture.

Correct-facing source result: all411targetstripepixels covered, zero triangle-normal reversals above1e-8m², zero new background pixels in either front/rear view. Front replaces468skinpixels with cloth and reveals2other skin pixels at an edge; rear has0newskinpixels. Final paired source images end-FRONTCULL.png. These checks do not certify shader shading, LOD or broad motion.

SHA256: 3a2fb33d9c2e318ff77f6903f085ba1695ea46c2d2ee3d9afb4f18de0b839abb.
