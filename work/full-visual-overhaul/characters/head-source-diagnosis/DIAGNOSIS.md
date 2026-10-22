# Decisive head diagnosis — read only, 2026-10-07

Recommendation: replace the head / upper-neck skin with a coherent anatomical source, then stylize toward the approved male/female target. Stop layering paint/rim geometry onto the current head.

## Evidence

Canonical sources are `work/match-anim-set/export/HeroBase_Male_MatchAnims.blend` (Body_M + Face_M + Rig_Male) and `work/match-anim-set/export/HeroBase_Female_MatchAnims.blend` (Body_F + Face_F + Rig_Female). The rig construction input paths are recorded in `work/match-anim-set/scripts/common.py`: male `work/male-pelvis-form3/export/merged_fd04bc28.blend`; female `work/female-full-merge/export/HeroBase_Female_FULL_STAGED.blend`.

`source-topology.json` contains direct Blender mesh/material/boundary inspection. Original-source CPU renders alongside it show skin_only and original_face for both bodies, with only neutral diagnosis materials. They contain no runtime fairing/projection/custom shader.

Male Body: 33,196 verts, 33,484 polygons. Female Body: 22,123 verts, 23,531 polygons. Neither Body nor Face has a shape key. Face_M is a 3,578-vertex rigid Head-bone child with 13 material regions; Face_F is a 3,986-vertex rigid Head-bone child with 14. There are no face deformation modifiers.

The skin includes a coarse nose and closed mouth/lip bulges. It is not a featureless sphere. However the only head boundary components are the eye apertures (male 46 vertices each; female 128 each). No separate nostril or mouth aperture exists in the skin. Sclera, iris, pupils, catches, upper/lower lip pigment, mouth seam, nostril pigment, brows and thin eyelid lines are separate Face mesh regions. The eyelids are cut skin boundaries + thin separate liner surfaces rather than a rounded continuous upper/lower lid with closure anatomy.

## Three blockers

1. Source anatomy and appeal are insufficient. Original skin-only renders already show broad uneven cheek/jaw planes, simplistic mouth and thin cut eye holes. The target requires deliberate sculpted orbital/lid/lip/cheek volumes. Roughness/noise/normal changes cannot create them.
2. Runtime patch layers additionally damage the weak source. Actual Art7/32 has flatter lips/nose than original source and jagged rims. Existing numerical audit places 379/828 male rim vertices behind the body, worst 19.7 mm. Ray projection through eye apertures can hit the back head; filled-layer construction is not anatomical eyelid modeling.
3. No authored facial deformation foundation. The canonical body/face has zero morphs, and the 53-name rig omits jaw/eye bones. Blink/gaze/expression have consequently been synthesized through custom geometric layers and shader clipping. Replacement needs real blink/smile morphs on the continuous skin, plus fitted eyeballs.

## Replacement shortcuts

Official MakeHuman core base mesh, targets, proxies and exports are CC0; application code is AGPL, a separate license. Primary source: https://github.com/makehumancommunity/makehuman/blob/master/LICENSE.md . Direct base mesh: https://raw.githubusercontent.com/makehumancommunity/makehuman/master/makehuman/data/3dobjs/base.obj . Shape assets: https://github.com/makehumancommunity/makehuman/tree/master/makehuman/data/targets . MPFB supports head feature modeling, eye assets and export copies with expression shape keys; these offer a mature anatomical starting point, not a finished stylized target.

A bounded head-only replacement can retain current body clothing, 53/54 named skeletons, sports animation/contact tracks and skin selection IDs. Fit source to Head/Neck coordinates and stitch/blend at a controlled neck transition; fit actual eyeballs and modeled lids/lips, author blink/smile in Blender. Do not run the old HeroFaceCraft/HeroEyeRim/HeroActualLidFit/HeroHeadVolume layers on the replacement. Use a new simple face material and native morph/rig export contract. First acceptance should be a source neutral/clay + colored portrait against the exact target, followed by the same geometry in Unity; numerical export parity comes afterward.

No production Assets or native source files were edited in this diagnosis.
