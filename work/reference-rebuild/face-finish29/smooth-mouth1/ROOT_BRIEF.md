# Smooth mouth correction: frozen candidate

The actual Face29 studio portrait exposed pointed/slit-like mouth highlights. This correction removes the physical seam recess and smooths only the local original mouth depth/normals. Upper/lower relief is broad and reduced to 1.8/2.4 mm. The existing lip pigment fields are registered to smooth continuous source-loop fits, preserving accepted LUT hue; seam peak .35 and sigma1.3 mm replace the old scattered nearest-three-point field (.46, .6 mm). Nose/cheek field remains the same as Face29.

Matched source portraits now show continuous natural mouth shading. Unity actual art is pending; source preview improvement is not adoption.

Source and FBX preserve 53 bones/rest/hierarchy, topology/weights/groups, X/Z, Eye13 features and shapes, all active blink vertex positions and all shape deltas. Only local mouth UV/color and normals change. The bounded mask gate records exact changes, with all UV/color outside the mouth exact. Full blink closure remains zero visible eye rays across both sexes’ Ready/Serve/Forehand/IntroWave recorded sample2. Existing male Serve nose/cheek occlusion changes remain documented.

Normal limitation: original encoded custom normals outside the mouth are retained, but evaluated Body eyelid normals still differ up to .50° male /1.26° female because local normal-space evaluation depends on the changed surrounding surface. Do not describe evaluated eyelid normals as exact. Eye13 feature normals/geometry and Body active blink positions/deltas remain unchanged. Actual blinks/lighting must be reviewed.

Frozen files: Male_OriginalFaceFinish29Smooth1.{blend,fbx} and Female_OriginalFaceFinish29Smooth1.{blend,fbx}. Hashes in ROOT_REVIEW_INPUT.json match active OriginalSeamBlinkFinish Assets when root began the actual run. No more source edits.

Reproduction scripts are work-only: stage-smooth-mouth.py generates build-smooth-mouth.py from the recorded Face29 recipe, then build/export. verify-fbx-roundtrip.py, verify-mouth-bounds.py and verify-blink-regression.py audit the candidate; render-source-preview.py creates matched CPU source portraits. No Unity/Assets writes or GPU run by this agent.

Actual smooth1 review: both front/threequarter portraits, both full blink fronts and resort15 viewed. The pointed mouth slits are absent; continuous shape is ready. Lips remain faint/blurred, especially female and resort, so definition is HOLD pending root’s bounded SkinPigmentUV2 palette. No source edit before that test. Important correction: current Unity TennisCharacter.shader overrides the LUT with the same weak male/female/dark palette as native; the earlier active native-vs-Unity mismatch claim is retracted. The accepted LUT coefficients used in source preview are not the active Unity pigment branch.
