# Animation safety — gate results, 2026-10-15

**GATE: Complete user checklist FAIL.** This is a staged implementation pass, not a character/animation release. The female shoulder/armhole and skirt failures remain visible. No source body, garment, skeleton, animation asset, map, light rig or production camera was replaced.

## Verified mechanics

- **GATE: Focused edit-mode tests PASS.** 10/10: shared emote playback budgets, monotonic Thrust retiming, two-bone length preservation, coordinate-change transition endpoints, six existing tennis spatial-contact tests. Evidence: `edit-tests.xml`.
- **GATE: Rendered tennis impact synchronization PASS.** Actual Tennis scene: the queued hit survives clearing the simulation's transient hitter, fires once, and aligns the ring with the rendered strings and the ball surface within 15 mm. Evidence: `focused-play-tests.xml`, `AnimationContactPresentationTests.cs`.
- **GATE: Tennis rally grading regression PASS.** Existing `RallyResolutionGradesSpacingAndAimsWithTiming` passed. Evidence: `initial-play-tests.xml`.
- **GATE: Golf result/emote flow PASS.** Actual Golf scene: routine result window is below one second; selected Pushups, Scuba and Spike hold the result until completion, return to Idle, then advance to Aim. Evidence: `focused-play-tests.xml`, `GolfAnimationFlowTests.cs`.
- **GATE: Sampled tennis emote completion PASS.** Wave, Shock, FistPump, Pushups and Defeat each finish and return to Ready. Evidence: `tennis-live/live-trace.csv`. This capture preceded adding the UpperChest proxy; it does not validate every final exclusion pose.
- **GATE: Scope preservation PASS.** Production changes are scripts/tests only. Character identity assets, outfit colors, maps, lights and gameplay-camera transforms are retained. Evaluation cameras are created only by editor proof fixtures.

## Visual and coverage gates still open

| User requirement | Gate | Evidence / limitation |
|---|---|---|
| Nothing passes through body or clothes | FAIL | Bone-local ellipsoids and arm/prop samples are approximate constraints. They do not test complete mesh/mesh intersection, skirt self-collision or all contact scenarios. |
| Female wave, inverse hand, human skin weights | FAIL | Wrist flexion is bounded, but `tennis-live/IntroWave_080.png` and `golf-live/female_Emote_Shock_080.png` show broken shoulder/armhole deformation. Wrist twist/inversion across the entire library remains unverified. |
| Backhand elbow hugs the front of the body | FAIL | Solver preserves wrist/contact and swivels elbows outside measured torso volumes. Full posed-skin/garment clearance and temporal continuity still need acceptance. |
| Skirt in Pushups, Defeat kneel, deep lunges | FAIL | `tennis-live/IntroPushups_080.png` and `EmoteDefeat_080.png`: layered skirt deformation still breaks. No rejected skirt correction is installed. |
| Racket versus visor/face in FistPump/Shock | FAIL | Sampled Shock is clear; a full prop-versus-headwear sweep and continuous video acceptance are still missing. |
| All emote/point-reset blends | FAIL | Outgoing tennis pose and golf coordinate-change blends are implemented; sampled completions and endpoint tests pass. Whole-library entry/exit continuity has not passed visual review. |
| Faces: blink, Shock, Victory, Defeat, JumpJoy, Slump | FAIL | Shared mouth/brow targets are implemented, with exact neutral geometry; all requested close-up expressions and blinks still need proof. |
| Serve wrist | FAIL | Pre-contact wrist cock implemented, zero adjustment at contact; full serve visual acceptance remains. |
| Thrust naturalness | FAIL | Timing is monotonic and less uniform; naturalness of the authored motion is not established by that test. |
| Balanced emote lengths | PASS | Shared 2.1–3.6 s budgets and actual completion checks. Long source clips are retimed rather than truncated. |
| Rapid reposition foot sliding and contextual slides/reach | FAIL | Ground-speed response is faster and existing short/wide/slice clips are routed by stroke context. Exhaustive foot-slip and new scenario microanimation work remain. |
| Grey smoke in emote view | FAIL | Rally-only footstep emissions implemented; no smoke in sampled emote captures. Full particle-source and transition coverage remains. |
| Golf face under cap | FAIL | No lighting change retained because the concurrent lighting chat was reverting its character lighting. Cap-shadow readability still needs review after that change. |
| Immediate energetic hole-out celebration | FAIL | Holed result now frames/reacts immediately; par uses FistPump. Need a captured actual hole-out and score-specific reaction review. |
| Golf putt backswing/weight | FAIL | Nonlinear load response and slower smoothing implemented; sampled putt shown in `golf-live`. Whole stroke weight/readability still needs acceptance. |
| Golf follow-through club clearance | FAIL | Sampled driver finish clears the head. Full shaft/neck/shoulder sweep still needed. |
| Golf hands/grip | FAIL | Shaft-axis spacing preserves each palm's lateral offset. Final finger/skin clearance and both-handed grip close-ups still needed. Initial golf-live captures predate the last axial-only correction. |
| Golf address/kneel/pushups/run-walk blends | FAIL | Root-orientation transition and shared mixer fades implemented; full named-transition coverage incomplete. |
| Female idle arms versus skirt | FAIL | Hip proxy contributes clearance, but the flared garment has no complete collision representation. |
| Golf lead-foot pivot | FAIL | Forefoot anchor retains the authored foot rotation; sampled finish shown. Quantitative no-slide proof through the downswing remains. |
| Stopped-ball wait | PASS (local result flow) | Routine window shortened to .65 s and tested. Network replay timing and all unusual trajectory tails are unchanged/unverified. |
| Tee-box opponents/gallery idle | FAIL | Actual gallery system now has asymmetric arm motion; full distance/readability proof still needed. |

## Failed legacy regression

`GolfPresentationTests.SwingToResultShowsStatsAndLetsBothGolfersEmoteUntilContinue` failed its initial front-facing result-camera assertion (dot .286, expected >.5). The unchanged routine-result path calls `FrameShotResult`, which restores the launch view; that assertion expects a dedicated front view. No production camera-layout change was made to satisfy it. The focused result/emote-flow regression passes. Keep the legacy failure visible; it was not waived or relabeled PASS.

The first new contact test also failed because its 80 mm center-distance threshold was smaller than the game's 100 mm visual ball radius. It now measures the ball **surface** against the strings within 15 mm, and passes. The initial result file is retained.

## Rejected deformation trials — identity stop

`rejected-axilla` shows a garment weight transfer reducing cloth flaps but revealing a large distorted underarm skin web. Other broader weights and torso/arm blend trials also failed. The CPU skirt projection trial collapsed layered cloth and cost approximately 64–69 ms per sampled pose. None is installed. Trial sources are preserved only as `.cs.txt` in `../experiments`.

Per AGENTS.md: “Stop for Adnan when identity/silhouette drifts.” These trials reached that stop. The remaining structural fix needs a reviewed shoulder/axilla binding correction and skirt deformation authoring, with the locked neutral shape preserved.

## Final dense sweep

Evidence: `final-pose-sweep/pose-sweep.csv`, `sweep-summary.json` and before/after PNGs. 2,588 samples, 32 sex/clip combinations, six torso/head volumes, raw authored poses sampled at 30 Hz. This is a diagnostic studio sweep, **not** a complete gameplay/contact/deformation test.

- **GATE: Bone-length preservation PASS.** Maximum segment error <0.00000045 m.
- **GATE: Proxy improvement PASS.** No sampled pose increased the arm-cost residual by more than 0.5 mm.
- **GATE: All-pose proxy clearance FAIL.** Male: 85 poses exceed 1 mm; maximum residual 94 mm. Female: 12 poses exceed 1 mm; maximum 22 mm. Worst cases are locked-grip Backhand/Serve. Residual is the square root of summed squared penetration samples, not a direct mesh penetration depth.
- **GATE: Mobile frame cost FAIL / unverified.** Median solve ~0.30–0.31 ms, desktop p95 ~2.02–2.44 ms; no iPhone profile. The final driver skips this wrist-preserving elbow solve in the repeated 120 Hz physics samples and applies it on the displayed pose.

The final sweep adds UpperChest coverage. It confirms the visual defects persist without installing any identity-changing weight experiment.

## Final retained-code regression

**GATE: Final focused play-mode regression PASS.** After UpperChest coverage and the physics-substep optimization, all three tests pass: rendered contact synchronization, golf routine-result/voluntary-emote flow, and existing tennis rally grading. Evidence: `retained-play-tests.xml`. This does not clear the visual failures above.

## Female continuation

See [phase2/GATE_RESULTS](../phase2/proof/GATE_RESULTS.md) for the retained shoulder/wave/stroke corrections and rejected skirt experiments. This later record supersedes the female shoulder findings above, without changing the incomplete status of the full checklist.
