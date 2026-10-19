# Female continuation — gate results

Status: **partial / full request FAIL**. Retained shoulder, wrist and stroke corrections are staged without commits. Runtime skirt experiments are rejected and absent from Unity/Assets.

| Gate | Result | Evidence / scope |
|---|---|---|
| Neutral body preservation | PASS | `ShoulderRepairPreservesTheExactNeutralSurfaceAndNormalizedWeights`: exact vertices, normals, UVs, triangles and bind matrices; normalized weights; imported source untouched. |
| Female tennis wave shoulder/armhole | PASS | `retained-IntroWave_080.png` and side view, compared with the previous pass's `../../proof/tennis-live/IntroWave_080.png`. Chest fabric no longer follows the waving upper arm. Raised-arm correction is pose-dependent. |
| Female wave wrist flexion | PASS | 61 sampled source poses; final maximum 55.00006° against 55.01° tolerance. Regression also checks wrist anchor invariance. |
| Backhand/wide-backhand/serve contact | PASS | Exact contact tests retain racket-hand position within 0.01 mm and rotation within 0.05°; two-hand contact also retains the left wrist. Gameplay contact tests check rendered racket/ball timing. |
| Bone lengths | PASS | All 1,335 female samples; maximum segment-length change 0.000328 mm. |
| Backhand/serve full clearance | FAIL | Proxy residual maxima: backhand 3.45 mm, wide backhand 5.03 mm, serve 0.383 mm. Elbow/grip improvements do not establish an impenetrable body. Full-overhead shoulder/armhole fitting also remains visually imperfect; do not interpret the contact test as a visual serve PASS. The proxy metric is the square root of summed squared sampled depths, not a full-mesh maximum penetration depth. |
| Skirt kneel/pushup/lunge clearance and silhouette | FAIL | Last surface candidate failed 8/84 full-body triangle captures and visibly distorted the upper skirt in deep transitions. See `edges-rejected-intersections.json` and `rejected-skirt-*` pictures. Candidate removed; authored skirt and bindings remain active. Retained hand/finger avoidance includes a skirt envelope but does not repair fabric deformation. |
| Golf female polo armhole | FAIL | `retained-golf-female_Intro_Wave_080.png` retains the pre-existing sleeve/axilla wing. Golf shirt fitting was not certified by the tennis tank correction. |
| Target iPhone performance | FAIL — no device proof | Desktop pose solver p95 3.43 ms in this diagnostic sweep; this is not a phone budget or frame-time certification. Rejected cloth timings do not describe the active game. |
| Original complete checklist | FAIL | Full emote, clothing, reach-recovery and golf visual acceptance remains open; prior handoff still applies except for the shoulder findings superseded here. |

## Tests

- `edit-tests.xml`: 14/14 passed, including the final wave correction ordering.
- `play-tests.xml`: 3/3 passed: animation/contact presentation, golf animation flow, tennis spatial contact.
- The older unrelated `GolfPresentationTests.SwingToResultShowsStatsAndLetsBothGolfersEmoteUntilContinue` camera-direction failure remains recorded in the first pass. No production camera changes or test-threshold changes were made.

## What the images prove

The retained Tennis captures come from the actual game scene with live emotes. Backhand/serve captures use continuous manual pose sampling through the driver, so they establish the rig pose, not a completed rally. Golf captures use the actual golf scene and character builder. Dedicated proof cameras do not modify gameplay camera assets, map geometry or world lighting.

`retained-pose-sweep.csv` and `pose-summary.json` contain the final 30 Hz female sweep. `retained-live-trace.csv` records the full retained tennis sequence before the final sub-degree wrist re-clamp; the final wave-only trace is saved separately. Captures of rejected skirt experiments are labelled explicitly.

The stage is not an approval of the failed cloth silhouette. Per AGENTS.md, “Stop for Adnan when identity/silhouette drifts”: ballooning, detached waist edges and triangle crossings were rejected rather than installed.
