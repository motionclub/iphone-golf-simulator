# 30b active post-cloth checkpoint

G0 PASS — explicit user override confirms pushed course-only f18dc4a1; final cloth REPORT and GARMENT_SPEC read. PHASE_STATUS.md is superseded and untouched. Historical G0 WAITING reports in rollback are no longer authoritative.

Fresh source snapshot: 2,275 files with SHA-256 and independent Unity assets in data/post_cloth_baseline.json. BEFORE tennis: 126 PNGs in proof/post_cloth_before/tennis. BEFORE SceneKit locker: 10 PNGs in proof/post_cloth_before/locker/frames. BEFORE course: 32 frames + 24 exact semantic masks in proof/post_cloth_before/course_exact. Earlier fog-attenuated masks are retained but excluded.

## Current gate ledger

- G0 PASS: prerequisite override and immutable fresh snapshot.
- G1 FAIL: shared_core_r2 has 0% skin/eye clipping on all eight chest views, holes 8–10 white median L*90.11–92.25. surfaces_r1 retains zero clipping and dark trim L*8.83–17.14; hole 7 white L*86.76 <88. Next profile uses legacy cloth exposure 8. No final golf outfit in Unity yet. shared_core_r3 is INVALID due a Metal literal syntax error, fixed in subsequent candidate; never treated as PASS.
- G2 FAIL: common real sun/shadows retained; quantified angle and contact-shadow proof outstanding.
- G3 FAIL: Ground/Rock candidate rendered at phone resolution; outline distance field and filtered world stripes in place. Quantified contrast, all fringe rings and worst-cliff sheets outstanding.
- G4 FAIL: matched 3-second films and temporal comparison outstanding.
- G5 PASS for current source: logs/guards_resume_current.log passes all seven guards. Candidate changes materials only; final installed-source hashes/scoring/outlines must be rerun.
- G6 FAIL: revised draft construction is under review; duplicate placket boxes removed, skirts reworked, shoes/headwear refined. Final labelled crops and neutral maps outstanding.
- G7 FAIL: diagnostic warning samples still exceed 3 mm. Garment-only fitter and independent measurements underway. Headwear drift alone is not collision proof. Body/face/hair/rest rig identity passed in data/identity_swing_checkpoint.json before latest fit; must rerun after all changes.
- G8 FAIL: golf variant export, catalog/payload, colour grid and sport switching not yet certified.
- G9 FAIL: shared includes exist in candidate, no shader fork; final golf IDs/spec and adapter integration are pending verification.
- G10 FAIL: two portrait match whole images <=1 byte max after initial shared extraction; landscape match whole max30 needs exact full-hero masks; final before/after tennis locker comparison pending. No overall G10 PASS claimed.
- G11 FAIL: original course counters exceed limits, not stable device stats. Metal compile succeeded for first course render but final comparable ALU/fetch inventory, device timing, draw/triangle budgeting and compressed outfit maps outstanding. Physical paired iPhone 17 Pro Max is available for verification; no device pass claimed.
- G12 FAIL: final complete review package and Adnan approval outstanding.

## Candidate state

No production shader, course asset, kit, locker resource or protected gameplay file installed by this run. All render candidates live in candidate/ and isolation/PostClothUnity. Work stays under work/golf-look. No commit. No index changes by this run yet. Every replaced work input has rollback copies. Baseline Unity startup SearchDatabase exceptions and failed proof attempts are retained in logs; completed captures are distinguished by manifests.

Current source/scripts: scripts/prepare_shared_core.py, prepare_course_shaders.py, prepare_course_runtime.py, pack_course_rock.py, build_golf_draft.py, fit_top_weights.py, retarget_proof.py, resolve_pose_clearance.py, measure_swing_draft.py. Continue from these candidates; do not restart and do not edit stale PHASE_STATUS.md.
