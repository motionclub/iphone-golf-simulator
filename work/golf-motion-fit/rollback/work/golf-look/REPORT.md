# 30b active post-cloth checkpoint

G0 PASS — explicit user override confirms pushed course-only f18dc4a1; final cloth REPORT and GARMENT_SPEC read. PHASE_STATUS.md is superseded and untouched. Historical G0 WAITING reports in rollback are no longer authoritative.

Fresh source snapshot: 2,275 files with SHA-256 and independent Unity assets in data/post_cloth_baseline.json. BEFORE tennis: 126 PNGs in proof/post_cloth_before/tennis. BEFORE SceneKit locker: 10 PNGs in proof/post_cloth_before/locker/frames. BEFORE course: 32 frames + 24 exact semantic masks in proof/post_cloth_before/course_exact. Earlier fog-attenuated masks are retained but excluded.

## Current gate ledger

- G0 PASS: prerequisite override and immutable fresh snapshot.
- G1 FAIL: surfaces_r4 measured zero skin/eye clipping on eight chest views, white L*88.03–92.25 and dark trim L*8.83–17.14. Human rejected the loss of character shine; those numeric results do not establish an appearance pass. shine_repair_r1 restores authored material rim strength and a later highlight shoulder; fresh renders/measurements pending. Final golf outfit is not yet in Unity. shared_core_r3 was INVALID due a Metal literal syntax error and is excluded.
- G2 FAIL: common real sun/shadows retained; quantified angle and contact-shadow proof outstanding.
- G3 FAIL: Ground/Rock candidate rendered at phone resolution; outline distance field and filtered world stripes in place. Quantified contrast, all fringe rings and worst-cliff sheets outstanding.
- G4 FAIL: matched 3-second films and temporal comparison outstanding.
- G5 PASS for current source: logs/guards_resume_current.log passes all seven guards. Candidate changes materials only; final installed-source hashes/scoring/outlines must be rerun.
- G6 FAIL: revised draft construction is under review; duplicate placket boxes removed, skirts reworked, shoes/headwear refined. Final labelled crops and neutral maps outstanding.
- G7 FAIL: diagnostic warning samples still exceed 3 mm. Independent outer-face and construction diagnostics are underway. The earlier global fitter was rejected for spiky deformation. Restored undegraded male saddle panels bring visible kit to 94,748 triangles, below the male 97,839 limit; pose fit remains unverified. Headwear drift alone is not collision proof. Body/face/hair/rest rig identity passed in data/identity_swing_checkpoint.json before latest fit; must rerun after all changes.
- G8 FAIL: golf variant export, catalog/payload, colour grid and sport switching not yet certified.
- G9 FAIL: shared includes exist in candidate, no shader fork; final golf IDs/spec and adapter integration are pending verification.
- G10 FAIL overall: exact full-hero match mask comparison PASS at the pre-shine candidate, mean 0.00575–0.00848 byte and max 1 byte for four views, unchanged mask silhouettes. data/tennis_full_hero_diff.json records the numbers. Final shared-core rerun and tennis locker comparison are still required.
- G11 FAIL: optimized Metal AIR inventory surfaces_r7 is at/below matching URP Lit fragment variants (ground 48/3 plain and 62/5 golf vs Lit 49/3 and 82/7; rock 42/3 and 56/5). This is static IR/fetch evidence, not measured hardware ALU or frame time. Frozen diagnostic iPhone app build succeeded (logs/device_before_xcode.log). Device install failed for insufficient storage: 792,813,288 bytes required vs 620,502,664 available, additional 172,310,624 bytes. No device timing/draw/triangle pass claimed. Full texture maps/budgets and actual SRP validation remain open.
- G12 FAIL: final complete review package and Adnan approval outstanding.

## Candidate state

No production shader, course asset, kit, locker resource or protected gameplay file installed by this run. All render candidates live in candidate/ and isolation/PostClothUnity. Work stays under work/golf-look. No commit. No index changes by this run yet. Every replaced work input has rollback copies. Baseline Unity startup SearchDatabase exceptions and failed proof attempts are retained in logs; completed captures are distinguished by manifests.

Current source/scripts: scripts/prepare_shared_core.py, prepare_course_shaders.py, prepare_course_runtime.py, pack_course_rock.py, build_golf_draft.py, fit_top_weights.py, retarget_proof.py, resolve_pose_clearance.py, measure_swing_draft.py. Continue from these candidates; do not restart and do not edit stale PHASE_STATUS.md.

## Human appearance correction

Adnan rejected the loss of character shine in the progress images. The current course-lighting candidate is visually rejected despite low clipping statistics. Cause: an overly early highlight shoulder plus conflating a physical course rim-light intensity with the authored material rim response. Corrections are isolated in candidate/ and PostClothUnity; the frozen originals and production files remain untouched. Blender kit progress sheets use test face/materials and are not final Unity character appearance evidence.
