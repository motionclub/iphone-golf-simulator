# Animation safety continuation

Status: incomplete; staged only, no commits. **Read [phase2/PLAN.md](phase2/PLAN.md) and [its gate results](phase2/proof/GATE_RESULTS.md) first: they supersede the shoulder findings below.** Read `PLAN.md` and `proof/GATE_RESULTS.md` before interpreting the code as a completed fix.

The active user request explicitly covers both sports, body/garment bindings, animation/emote motion, facial reactions, hands, props, footwork and golf result pacing. It supersedes the old clothing-only scope. Preserve the locked identity and existing customization. Another chat was reverting character lighting; no production lighting/camera/map changes were made here.

## What remains critical

1. Female upper-arm/axilla source binding and garment armhole deformation. Actual Tennis and Golf captures reproduce the fault. Body/garment weight transfers and changing torso/arm blending exposed large skin webs and changed the silhouette. They were rejected under the repo's identity stop rule. The source body coverage mask is also worth auditing: V2 garments remove rest-space body triangles, which may conceal needed moving arm surfaces. This mask hypothesis is not yet tested.
2. Skirt deformation in floor poses, kneels and lunges. A CPU per-vertex projection trial destroyed layered cloth and cost ~64–69 ms. Do not enable it. Author garment weights/support/correctives with topology/layer awareness, preserving the garment itself.
3. Complete full-mesh clearance, especially locked-grip Backhand and Serve. `HeroPoseSafety` is an approximate torso/head volume solver. The final sweep still has 85 male and 12 female poses over its 1 mm residual criterion. Do not call the body impenetrable.
4. Validate female wrist twist/inversion and golf finger contact close-up. Flexion limiting and wrist spacing do not prove correct handedness or a finished grip.
5. Complete the visual gates for every user-listed motion, footwork, microanimation, facial expression, prop path and cap shadow. The table in GATE_RESULTS is authoritative.

## Retained code

- `HeroPoseSafety`, called from the displayed tennis pose and the golf pose pipeline, preserves segment lengths and locks sports wrists while moving elbows. It excludes the torso/head using six bone-local ellipsoids. Tennis skips redundant wrist-preserving elbow solves in physics substeps.
- `HeroPoseTransition` bridges golf's 90-degree root-coordinate change. Tennis keeps the outgoing full-body clip throughout reset fades.
- `TennisContactPresentation` flushes impact FX after the rendered rig and keeps events through later physics steps.
- Shared emote durations/time mapping, mouth/brow mood targets, reach-clip routing, footstep dust gating, golf putt response/lead-foot anchor/hand axial spacing, result timing and gallery idle changes.

## Reproduction

Work was validated in the isolated Unity project `/private/tmp/animation-safety-01a13e62` with Unity 6000.3.24f1. It was copied from the working project to avoid its editor lock. Latest retained script paths are listed in `modified-paths.json`.

Editor entry points:

- `GolfArcade.EditorTools.AnimationSafetyAudit.Run`: dense raw clip sweep, baked-mesh screenshots, arm proxy/segment/cost CSV. `ANIMATION_PROOF` sets output folder; optional `ANIMATION_ONLY`, `ANIMATION_FEMALE_ONLY=1`, `ANIMATION_SNAPSHOTS_ONLY=1`. Raw clips + solver are not the entire gameplay pipeline.
- `GolfArcade.EditorTools.AnimationSafetyFilm.Run`: live Tennis scene, selected female emotes and completion trace. `ANIMATION_FILM` output; `ANIMATION_MALE=1` for male.
- `GolfArcade.EditorTools.GolfAnimationSafetyFilm.Run`: live Golf scene, both heroes, driver/putter and emotes. Uses the actual private active golfer, not an arbitrary inactive preview returned by GetComponentInChildren. Cloned camera gameplay behaviours are disabled.

Focused tests:

- EditMode: `GolfArcade.Tests.AnimationSafetyTests`, `GolfArcade.Tests.TennisSpatialContactTests`.
- PlayMode: `GolfArcade.PlayTests.AnimationContactPresentationTests`, `GolfArcade.PlayTests.GolfAnimationFlowTests`, `GolfArcade.PlayTests.TennisSpatialContactPlayTests`.

The legacy `GolfPresentationTests.SwingToResultShowsStatsAndLetsBothGolfersEmoteUntilContinue` still fails a front-camera assertion on the unchanged routine-result camera path. Keep this reported. No camera changes or test weakening were made to hide it.

All rejected source trials are `.cs.txt` files, not compiled runtime code. `baseline/` is the start-of-task source snapshot; preserve unrelated existing staged work. Do not commit without authorization.
