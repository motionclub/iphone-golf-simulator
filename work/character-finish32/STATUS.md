# Character-only beautification — stage 1 in progress

User scope: character only. No map, world light/post, turf, or gameplay camera edits. Clothing colors remain customizable. Finish one stage, show actual render in chat, then continue without asking. Stage 1 male polo is NOT passed or promoted.

Normal launch remains unchanged: new male top is opt-in via VISUAL_TAILORED_POLO=1. The optional top bypasses old sleeve geometry/weights/anchors. Body, face, rig, animation sources and maps are unchanged by this pass. No native assets adopted yet.

Latest full source: Male_Polo_Refined.blend -> Unity/Assets/Resources/Tennis/KitsTailored/Male.fbx. Full source now 39,549 triangles after local shoulder subdivision and new body-surface binding. Refined capture completed: good resting fit, but SliceApproach still visibly fails. Resource restored to this source after rejecting CuffBind and SmoothBind.
Latest distance source is still Male_Polo_Distance.blend from the earlier Sleeve candidate (19,151 -> 10,532 tris, two-way rest error .936mm). It must be regenerated if full candidate is accepted. Runtime and exporter distance override are implemented, but current full/distance pair is not the same revision.

Accepted progress but not complete: folded collar, open neckline, new 2-button placket, neutral independently colored buttons, rebuilt fixed body-surface binding; original floaty raglan/cuff/hem overlay strips removed. Actual sleeve lining remains. Clothing uses neutral fine weave without stale construction maps. Light/dark/saturated palette controls verified visually in prior captures.

Key capture directories:
- baseline: current old top, studio diagnostic ACES .7, warm lights, SSAO off. Do not describe as normal game lighting.
- sleeve: clean candidate; all 33 tennis slots x5 front/rear, color swatches, close crop. Smooth but SliceApproach has sleeve clipping; EmoteScuba has tiny chest breakthrough. NOT PASS.
- distance: earlier Sleeve distance mesh, same review; scuba breakthrough larger. NOT PASS.
- court-before / court-after: current unmodified resort lighting and diagnostic camera, production default skin (BC9373), film=0, fill=.65. Candidate before further fixes; no world edits.
- collision-poses: 63 exact body/top matrix samples across SliceApproach, EmoteScuba, Serve, Forehand, IntroWave, IntroPushups, Backhand (9 samples each), with source snapshot at poses/male_intro.json.
- support: FAILED static fit expansion, wrinkled/torn shoulders. DO NOT ADOPT.
- finish: INVALID source capture (export failed; used previous Fold source); labeled INVALID_SOURCE.txt.

Useful scripts (all in this directory):
1. author_envelope.py: baseline top snapshot -> fixed body-surface binding and cloth clearance, x reflection into Blender.
2. author_fold.py / author_finish.py / author_clean.py: source collar reconstruction, drape relaxation, replaces placket/buttons, removes detached overlays. Clean source geometry looked promising.
3. author_sleeve.py: bounded 27mm sleeve extension with rebind, full 19,151 tris. Best visually clean source before remaining extreme-pose repairs.
4. build_lod.py: decimates Sleeve and enforces <=1.5mm two-way rest error. Need animated deformation error gate too.
5. solve_clearance.py and solve_support.py: FAILED optimizer experiments. The latter over-expanded underarms up to42mm because support correspondence differs by pose. Do not use these exports. Latest Refined source replaces them.
6. refine_binding.py: starts Sleeve, subdivides main shoulder edges >7mm in bounded region, rebinds whole shirt main to closest body triangle. No body/rig modification.

Runtime/editor edits backed up under before/ (baseline was already dirty from other chats):
MatchHeroLook.cs: optional candidate source swap + cloned TailoredPolo32 marker + materials; neutral candidate cloth surface.
HeroGarmentTailoring.cs: marker bypasses legacy fields.
HeroGarmentLOD.cs: matching candidate distance load and mesh/bone switching, owned mesh cleanup.
MatchHeroKit.cs: importer owns KitsTailored.
MatchHeroLockerExport.cs: distance candidate override before Collect.
VisualOverhaulCharacterCapture.cs: optional torso crops and garment swatches, actual SetKit public interface.

Current chat outputs /Users/adnanyonathan/Documents/Codex/2026-10-08/open/outputs/character-beautification/stage-01-polo contain Sleeve progress images. One actual male_current_intro.png shown in commentary with explicit progress/diagnostic label. No final stage completion claimed.


## Continuation: sleeve deformation experiments

- CuffBind: rejected. Broad upper-arm binding exposed larger underarm gaps even at intro.
- SmoothBind: rejected. Locally smoothing the sharp torso/arm weight transition did not close the wide-reach opening and regressed scuba.
- diagnose_refined.py found nearest-body weights jump from ~.39 to ~.93 upper-arm influence across adjacent shirt points. Body/top skin matrices agree; no active body morph causes the discrepancy.
- author_pose_fit.py: one diagnostic corrective for male_SliceApproach_4 on the Refined imported basis. Actual Unity pose-probe closes the skin hole but has severe dark/striped sleeve shading; NOT PASS.
- author_pose_normals.py computes corrective normals in the final posed surface then transforms back to bind space. author_pose_thickness.py additionally separates inner/outer lining clearance (2/6mm). Both are diagnostic profiles, not production resources.
- Editor-only TailoredPoloPoseProbe.cs is invoked by the capture helper only when VISUAL_CHARACTER_TEST_PROFILE supplies an explicit JSON path. Exact basis position/count checks. Applies the named probe only at the matching diagnostic pose. This is NOT a production animation solution.
- Current optional Male.fbx restored from Male_Polo_Refined.blend. Distance remains older Sleeve basis; no promotion.
- Another chat runs AnimationCatalogFilm in the shared original Unity project. Do not interrupt it or mutate original Unity assets while it is capturing. A temporary compile error from its helper was already fixed by its owner; no change made here.
- Isolated APFS-copy review project: work/character-finish32/review-project/Unity. Review queue wrapper: work/character-finish32/review_queue.py. It has its own cache/lock and logs in review-project/work/full-visual-overhaul. Source copied at this checkpoint; candidate changes must be explicitly synced while that review queue is idle. Do not assume mirror stays current.
- pose-layer-queue.json (posed normals + thickness) is running in isolated review project at this checkpoint. Inspect its results/images next. Unity session 92044.

## Later continuation — current direction

The pose-correction approach is rejected for general motion. author_pose_welded.py successfully closes the one SliceApproach_4 hole while preserving UV seam aliases, but author_pose_motion.py (SliceApproach 3, 5, 8) diverges at compressed arm poses (rest-space deltas up to 0.8m). Do not install its profiles or promote it. Posed-normal and lining-thickness variants reduced some shading defects but did not solve the structural fit.

A scratch runtime profile experiment was made ONLY in the isolated review project by prepare_candidate_runtime.py. Its two edited runtime files were then restored from the original project before testing new panels. No candidate RBF profile was installed in Resources. Original runtime remains as previously recorded.

Current experiment is a rebuilt main shirt with continuous quad torso, shoulder yoke and lofted sleeves (shared sewn loops), turned hem/cuffs, and the existing authored collar/placket/buttons. Script rebuild_panels.py -> Panels failed (bad cuff angular correspondence and insufficient fit). rebuild_panels_fit.py -> PanelsFit corrected correspondence/clearance but failed badly in animation because its provisional analytic bone weights did not follow the shoulders. Latest rebuild_panels_bound.py -> Male_Polo_PanelsBound.blend transfers the actual nearest-body surface weights onto the new topology. Export is ONLY to review-project/Unity/Assets/Resources/Tennis/KitsTailored/Male.fbx. Main repo optional resource remains Refined; normal launch unchanged.

New panels are 4,408 source vertices / 6,805 triangles. Their fit/style is unproven; no PASS. Current panels-bound-queue.json is running in isolated review (exec session 77918). Inspect panels-bound/male_polo_front.png, male_SliceApproach_3.png, _4.png and EmoteScuba_5.png next.

Potential remaining details for this rebuilt source: inherited placket/buttons/collar may need reprojection to the new torso surface, since their old positions can be occluded. Source cloth normals and sleeve seam orientation also need visual inspection. Do not hide body triangles or change body/rig/motion to mask failures.

One automatic approval review timed out on a long Blender command. Retried once as a short Blender export after writing the script without escalation; retry succeeded. No approval remains pending or required.

The user-facing plan was tightened so stages 10–12 explicitly evaluate characters in fixed environments; it no longer proposes map, light-rig or camera edits for this task.


## Latest user steering: clothes only
The user explicitly narrowed scope to clothes. No face/body/skin/hair/lighting/camera/map work. Garment geometry, garment weights/deformation, materials, seams and clothing customization remain in scope. No body or rig edits have been made in this pass. Male polo remains stage 1 and NOT passed/promoted.

Latest experiments: PanelsBound and two-sided rendering both FAIL (real severe shoulder penetration, not culling). DQ volume probe on Refined improves SliceApproach_4 but FAILS compressed 3/8 and produces huge bind-space deltas; reject. Latest mirror asset is Male_Polo_InnerPanels.blend (Refined + 7,998-triangle static body-conforming inner clothing panels). Its inner-panels capture is finished; it FAILS because lining edges extend beyond cuffs, and some holes remain. Do not adopt. Original optional full resource remains Refined. All jobs finished; no active tool sessions.

## Current continuation — clothing coverage diagnosis
Latest candidates Lining, Surface, StableShell and exact-pose StableProbe all FAIL and must not be adopted. Matched thin lining did not repair motion. Direct body-surface shell fit also penetrates and loses drape. Stable garment weights avoid near-singular LBS (critical smallest singular value improves from ~0.05 to >0.40) but the single-frame collision corrections still cause protruding/torn folds. No runtime corrective installed.

Important new finding: the review harness forced VISUAL_GARMENT_COVERAGE=0, while production has authored per-outfit coverage. Reenabling it revealed its male profile is stale: 7064/7072 existing physical faces match; the exact-match guard therefore omits none. reconcile_existing_coverage.py filters only obsolete references (8), adds zero covered faces, and changes the temporary mirror profile garment count to Refined (22883). This remains isolated, not a production repair yet. Existing original body assets/weights are unchanged. New coverage-reconciled capture is running. The plan now distinguishes complete source body preservation from existing authored outfit coverage; do not expand coverage to conceal garment defects.
Mirror Male.fbx restored to Refined from original optional resource. Mirror Tennis/GarmentCoverage/Tennis_Male.json is now the temporary reconciled candidate profile; original profile remains untouched. No agents or native adoption.

## Breakthrough diagnostic — sleeve twist (latest)
The full-body / flat nearest-weight route was not sufficient. The isolated swing-only sleeve target (`solve_twist_probe.py`) produces clean sleeve volume in SliceApproach 3, 4 and 8, unlike prior collision/weight approaches. It discards upper-arm axial twist for the GARMENT target only: derive swing from the parent Shoulder's transported rest arm axis to actual upper-arm axis, preserving actual joint pivot; all body bone transforms/motion remain untouched. The target uses original Refined weights. The source (`Male_Polo_TwistProbe.blend`) increases dominant garment weights to .70 only abs x>.10, z1.10..1.42 to avoid ill-conditioned inverse LBS; static GPU morph deltas restore the desired posed garment from that stable basis.

`solve_twist_field.py` tapers twist cancellation at the torso: max(smooth(abs x;.145,.215),smooth(z;1.17,1.30)). `solve_twist_torso.py` additionally projects a bounded side-torso region onto the currently visible body surface with 6mm clearance. Three exact-pose `twist-torso/` front captures look substantially clean; not a stage pass and not general animation proof. Rear has to be reviewed thoroughly. These exact probes are editor-only and cannot ship by themselves.

`twist-motion-data/` has 561 matrices (33 tennis slots x17). An isolated mirror-only `VISUAL_CHARACTER_CLOTH_MATRIX_ONLY` flag was added to capture helper to skip per-pose image rendering when gathering matrices. `build_twist_motion_profile.py` combines these with 63 older critical samples (624 total), generates target deltas/normals, saves `twist-motion-targets.npz`, and selects 96 rotation/translation feature anchors (max feature RMS .5205; accuracy not yet certified). Bone feature set: Spine, UpperChest, LeftShoulder, LeftUpperArm, RightShoulder, RightUpperArm; skin matrices relative Chest, first two rotation columns + translation*5, 54 values. `twist-motion-profile.json` was initially220MB because float32 tolist preserved long decimal strings; a Python compaction is running at this checkpoint (session51847), round7 and zero <5e-7. This is diagnostic source data, not a final mobile resource footprint.

MIRROR ONLY new `Assets/Scripts/Tennis/TailoredPoloDeformation.cs`: opt-in VISUAL_TAILORED_MOTION_PROFILE path, exact basis validation, static morphs, nearest4 feature interpolation (exact anchor shortcut), no per-frame vertex rewrite. Injected mirror HeroGarmentTailoring Tailored marker branch -> Prepare, HeroTennisDriver FinalizeGarments -> Apply, MatchHeroLockerExport two pose-finalization sites -> Apply. No original runtime change from these experiments. Source no player-build profile yet (Load returns null outside editor); not promoted. `twist-runtime-queue.json` is ready but NOT STARTED. Next: finish profile compaction, run this runtime queue, inspect critical and other motions, then improve interpolation/footprint and validate LOD/native before any adoption. Mirror current Male.fbx=TwistProbe; mirror coverage profile is reconciled7064faces, count22883. Original optional Male remains Refined; original coverage7072 unchanged.

## Latest runtime outcome and next diagnosis
`twist-runtime/` (96 nearest-pose anchors) compiles and reproduces exact critical anchors but is REJECTED: `twist-interpolation-report.json` shows520/624 frames >2mm error, max104.8mm. Do not adopt RBF/nearest4 motion profile. Its mirror class backup is TailoredPoloDeformation.RBF.rejected.cs in work only.

Current new route is a direct affine-matrix morph basis, avoiding pose interpolation and inverse mixed skin matrices. Fixed garment-only mesh is bound to EXISTING Chest (body original53bone rig unchanged). Original garment weights are represented in static morph basis. Actual and swing-only upper-arm channels split weights by the spatial twist field. Controls are current skin matrices relative Chest, affine elements minus identity; a linear projection compresses to96fixed shapes. Playback only updates morph weights. No per-frame vertex-buffer changes or added bones. Existing native export format serializes fixed morph targets and their per-clip control tracks; native validation/performance still NOT DONE.

`build_matrix_source.py` starts Refined and adds bounded9mm side ease at abs x .105..225,z1.07..1.31, source5946vertices changed. Saves Male_Polo_MatrixSource.blend; mirror Male.fbx currently THIS SOURCE. Imported vertex count22885 (2more normal/UV splits than Refined),39,549tris. Mirror coverage profile count updated22885, same7064existingfaces. Original optional Male stillRefined22883, original coverage7072unchanged.

`build_matrix_profile.py` constructs156affine controls (12per controlled real/virtual bone). Uses624motion samples to compress the FIXED geometry basis (not nearest-pose interpolation):96shapes maxpositionerror0.21483mm,maxnormalvectorerror.004876 vs direct analytic target across624samples. Outputs matrix-profile.json149.6MB (diagnostic JSON, not final mobile resource), matrix-profile-basis.npz, matrix-profile-report.json. Rank72would have1.60mm position/.0623normalerror; rank60 4.94mm. Never claim final footprint/performance from these source files.

Mirror TailoredPoloDeformation.cs now contains this MATRIX implementation. Explicit editor env VISUAL_TAILORED_MATRIX_PROFILE. Profile stores controls/basis/projection. Prepare validates exact positions/count, sets garment weights to existingChest1, adds fixed morphs. Apply computes actual skin matrices plus swing-only virtualarm matrices, relativeChest affine controls, then matrix projection -> blend weights. Hook sites in mirror Tailoring/Driver/Exporter unchanged from prior prototype. Load returnsnull in player build; no production integration yet.

`matrix-runtime/` capture completed clean compile. Sleeves remain coherent in Slice3, intro andServe, but source9mm side expansion causes a flap/skin collision in EmoteScuba5 and tiny Slice3 sidepeek. Thus NOT ART PASS. SVDnumericalaccuracy != fit/pass. Next should remove/reduce this sourceease and refine twist transmission at the sleeve/torso seam or add garment-only contact morphs. Don't expandbodycoverage tohide defects.

`inspect_torso_twist.py` (session25625 at write checkpoint) compares exact twist-field vs twist-torso projection to find original arm-weight masses/rest positions at remaining collisionpoints. It reads prior Refined basis. Could test a twist-cancellation field based on original upper-arm garment mass rather than broad xyz ORfield, to stop transmitting twist correction into side torso. For cheap exactpose tests, restore Male_Polo_TwistProbe.blend to MIRROR (stableweights source22883); coverage countback22883; env VISUAL_CHARACTER_TEST_PROFILE exactpose helper; no VISUAL_TAILORED_MATRIX_PROFILE. Mirror MatrixSource22885 cannot use older22883probes. All Unity jobs finished, no active jobs except inspect diagnostic if not yet polled. No stage passed, no original/native adoption.
