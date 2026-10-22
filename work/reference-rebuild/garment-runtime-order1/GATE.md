# Runtime garment order 1

SOURCE gate: PASS. Tennis final-pose hook follows graph evaluation, post-process/contact IK and foot locks. Natural corrective fallback runs at1200; live driver-owned evaluation is single. Garment LOD selects at900 before driver1000. Manual Sample finalizes immediately. Golf runtime unchanged. Absolute blendshape Set calls do not accumulate geometry.

ACTUAL regression gate: PASS in root live-order.xml execution (both240frames/189moving/0stale, max0). Test filter GolfArcade.PlayTests.HeroGarmentRuntimeOrderTests.LiveDriverGarmentsUseThisFramesFinalPose. Two genders, enabled real driver,240 frames each, live Wave/Serve/Forehand triggers, >30 genuinely changing frames and zero stale final-pose corrective inputs. No manual Sample or corrective Apply in test. Work-only control copies reconstruct pre-fix three runtime files for root negative-control run; test is identical.

Garment visual integrity: FAIL/open. Ordering fixes stale live weights, not source sleeve intersections. Current profiles only ten Ready/Wave/Pushups anchors; old captured Serve/Forehand LBS oracle is exact but shows weak confidence and under-body sleeve geometry. Source weights/envelopes and full/LOD imports require actual visual motion coverage: golf5 clubs at address/top/impact/follow-through (both hands), tennis serve/forehand/backhand/volley/smash, walking/running/turns, all3intros/all3taunts and happy/sad reactions, including entry/return and both full/LOD. No source clothing/rig/physics timing changes here.

## Actual live regression result

Root ran `proof/reference-rebuild/garment-runtime-order1/live-order.xml`: PASS both bodies, each240frames/189moving frames,0stale corrective directions, maximum direction error0. Total command29.34s; test16.58s. This closes the live order gate; it does not certify garment surface integrity. Negative-control run was not required and not executed.
