# Shirt runtime audit 28 — read-only result

**Binding/morph/alias execution gate PASS on inspected existing captures. DQ shirt appearance FAIL.** No Unity/GPU run, production write, weight change or geometry algorithm was introduced.

The strongest counterexample to anchor stacking is the actual gusset-dq1 Female Forehand1 at0.4s: all ten TailoredSleeve weights are exactly0, LocalUnderarm is disabled, yet its front/rear actuals show the layered underarm slit. The CPU reconstruction of the installed helper reproduces all five actual baked Top dumps with max0.0008mm error. This rules out a mistaken root/output transform, duplicated GPU morph application or inaccurate source-only pose as the cause of these existing DQ actuals.

| Recorded Forehand sample/time | Total anchors | Max anchor effect under LBS / DQ | Max DQ effect with anchors disabled |
|---|---:|---:|---:|
|0 /0.0s|100%|51.98 /53.01mm|8.42mm|
|1 /0.4s|0%|0 /0mm|107.25mm|
|2 /0.8s|0.61%|0.45 /0.46mm|221.23mm|
|3 /1.2s|100%|52.03 /53.02mm|8.22mm|
|4 /contact0.66667s|34.61%|21.51 /21.94mm|39.06mm|

Thus large anchor deltas can affect Ready-like/intro poses, but the worst stress poses are already anchors-off/nearly-off. The current local DQ patch intentionally uses a different deformation from the LBS Body and pinned shirt boundary. Its actual free-region shifts reach107–221mm on those matrices. Profile maximumDisplacement0.04 is not read by the DQ evaluation, so it does not enforce the former40mm displacement bound. This is a concrete behavior change, not proof that DQ mathematics is implemented incorrectly. No adoption should infer acceptable tailoring from preservation of rotational volume alone.

## Exact runtime contract

Current preparation is HeroGarmentHemWeights.Apply → HeroGarmentTailoring.Apply. For Kit_Top, tailoring first applies HeroGarmentSleeveGeometry, then HeroGarmentAxillaWeights, then collar/tailoring geometry/normals, then HeroGarmentPoseCorrectives.Prepare. Prepare installs the existing ten sleeve-envelope morphs and optionally LocalUnderarm morphs. It does not change bone weights. There is no current source symbol named HeroTailoredSleeveWeights; the active weight field is HeroGarmentAxillaWeights. Hem weighting applies to golf Kit_Bottom only, not tennis Top.

HeroGarmentPoseCorrectives.Apply evaluates final skeleton directions, writes LocalFit controls (only VISUAL_UNDERARM_FIT=1), writes the TailoredSleeve blend controls, then calls optional Gusset. The live driver owns final evaluation; LateUpdate fallback excludes live driver actors. LOD selection happens before the final driver pose. Root's new editor-only anchors0 ablation correctly zeros envelope weights while retaining the Gusset call.

Gusset.State builds every output binding from p.boneIndices/p.weights, rather than from source.boneWeights at runtime. This could be a stale-profile hazard if source weights change later. It is **not stale now**: fresh root native exports (with gusset off, after current OwnMaterials/tailoring/axilla/preparation) match the profile's original source rows for Full13932 AND LOD11533 with0 changed vertices; maximum dense-bone L1 error2.83122e-7 is Float32 conversion. Canonical matrix17 Full source matches exactly (L1max0). Full/LOD geometry/topology/bone order checks also guard State construction; weight equality itself is not currently a runtime assert.

Morph application is once per region. Gusset preserves all named controls but zeros GPU position/normal/tangent morph deltas for free vertices, calculates those deltas on CPU, and skins the resulting output through its rigid root binding. Nonfree vertices retain GPU shape deltas and their original weights. Pose-weight capture and Activate preserve controls across mesh assignments. The exact actual reconstruction validates this split for the sampled poses.

All Full alias groups have identical dense bindings;0 alias groups straddle free/nonfree membership. Reconstructed posed alias gaps are zero to numerical precision in LBS and DQ for all sampled frames. Delta synchronization therefore does not split the existing Full true seam aliases in these captures. This does not claim that source garment topology has no overlapping shell/lining panels or inverted faces; the geometry specialist owns that diagnosis.

Full/LOD changes preserve separate canonical meshes, palettes and cached state. HeroGarmentLOD selects mesh and bones together; CanonicalSource unwraps dynamic gusset output; corrective indices refresh whenever sharedMesh changes; State.Activate copies current shape weights. Current Full/LOD source-weight equality was measured from fresh independent runtime exports. Cache ownership/reuse had its prior runtime gate; no new transition run was performed here.

## Inverse-LBS anchor compatibility and smallest controls

The sleeve geometry author explicitly computes bindTarget = inverse(weighted skin matrix) × authored posed target in work/full-visual-overhaul/garment-coverage/author-sleeve-geometry-9.py:144–145. The later weight-transition author rebases anchors using another exact inverse LBS matrix at author_weights.py:58. These deltas target LBS surfaces; applying them through DQ is not guaranteed to preserve their authored posed result. The measured ablation table quantifies that difference on current matrices, and demonstrates it is modest relative to the worst DQ-only shifts.

The smallest useful actual pair is the same Female Forehand0.4s with LocalFit0 and anchors0, DQ0 versus DQ1. Existing DQ1 already has both controls effectively off at that time. If the0.8s case is retained, its0.61% envelope is negligible and supplies the maximum221mm DQ stress example. Intro anchors0/1 with DQ0 can separately establish whether the accepted intro envelope causes a static fold; it should not be conflated with the DQ stress result.

Keep SleeveGeometry and Axilla weight preparation identical in this ablation. Disabling them changes the bind basis used by SleeveFit/Gusset geometry validation and would require a separately regenerated source/profile; bypassing their basis checks would produce an invalid comparison. Do not disable all HeroGarmentPoseCorrectives.Apply by early return, because that also skips Gusset. No broad new algorithm or whole shirt-fit claim follows from this audit.

Data: recorded-contract.json contains five exact four-way CPU controls; native-source-weight-contract.json contains current Full/LOD runtime binding comparisons. The scripts are reproducible read-only checks. DQ actuals inspected: proof/reference-rebuild/gusset-dq1/female_Forehand_1.png and _rear.png. No art pass is claimed.
