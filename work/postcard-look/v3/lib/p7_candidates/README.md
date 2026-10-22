# Phase7 scratch handoff — overall art FAIL

Production libraries, hole scripts, installed PNGs and frozen stages were not edited. No Unity launch or install occurred. Every prior failed attempt remains in DECISIONS.md, candidate folders and logs.

The reviewable generator proposal is `golf_look_textures_proposed.patch`; `golf_look_textures_candidate.py` is its unapplied complete source. Actual proposed source was executed in memory by `verify_proposed_source.py`, with only scratch outputs. `bounded_v6_source/` contains its generated PNGs and exact source-gate records. `proposal_source_sha.json` records production/candidate/patch hashes.

| Measured gate | Result | Evidence |
|---|---|---|
| All six unchanged generator basalt gates | PASS | `bounded_v6_source/source_gates.json`; old profile deviation0.0003, zero glow in all five plain zones, old minimum edge window5.1%≥4 |
| Unchanged original BASALT_PRISMS | PASS | `bounded_v6_source/inherited_prisms.json`; glow4.0531%, bad component area0%,24components, horizontal run5.2734%, cross spacing4.0514m |
| Original H_GLOW_JOINTS on complete frozen Phase4 stage | PASS for this scratch texture | `frozen_stage_uv.json`;598ROCK objects, top glow0.02%≤0.5%, side1.96% within1.01–2.43%,30%side area with any glow, median old dash2.6m≥2.5 |
| Opt-out original generator compatibility at256 | PASS | Exact C/N/E array equality, max absolute delta0; no claim that the new default is byte-compatible |
| Three actual compact-column Blender views, unchanged proof pixel predicates | FAIL in all three views | vertical90.4%,84.9%,92.8%>80%; none selected away |
| Aggregate Blender network | PASS |28,948skeleton pixels,2,485junction clusters,8.5844junctions/100 |
| Other per-view Blender joint caps | PASS | coverage4.29/3.11/3.19%; rungs0/0/0.1%; base median23.3/22.4/25.1; base mean saturation0.049/0.065/0.051 |
| Actual Game-view candidate gates | UNVERIFIED | Production integration and Unity rendering remain unauthorized |
| Visual review | FAIL | Bright dense central fork knots hang on long narrow molten necks; face windows truncate the graph |

Three retained images: `bounded_v6/fixture/az0.png`, `az35.png`, `az-35.png`. Geometry comprises three actual compact3-row tiles:45columns,564vertices,372polygons,948triangles. These views use the decoded-map candidate; source proposal emits identical E pixels, C mean absolute change0.252levels/max2, N mean absolute change0.065levels/max29. The exact proposed output therefore still needs new native fixtures after authorized integration. Source-level PASS never substitutes for the recorded art FAILs.

One scratch UV-counter bug was corrected: uint8 decoded emission was initially compared to0.2 rather than divided by255. The incorrect counters are preserved in `result_attempt1_uint8_uv_counter.json`; corrected counters use the original normalized predicate and the same saved mesh UVs. This did not change geometry, frames, pixel measurements or their FAILs. The full frozen-stage sampling always used correctly normalized candidate bytes. Its first run used a fallback root-scale assumption; the final run repeats the original terrain-matrix SVD scale expression exactly. Both logs/results remain available.

Grass historical minimum-contrast conflicts remain FAIL. No candidate increases mowing above12%fairway/8%green. No original gate, threshold, GLOW_U, GLOW_EDGE, ZONES, PROFILE128 or verifier file changed.

## Next actual geometry/chart alternative

Question the independent per-face UV window architecture before another texture-only fork retry. A window starts near one hot line but exposes only part of its lateral branches; tall world-v density magnifies the remaining neck. Give two physically adjacent exposed side planes a continuous UV chart across their shared real column corner. Use actual world perimeter distances, a shared v phase and one existing glow corridor; leave the other side surfaces in the unchanged plain zones and all tops glow-free. This makes a complete fork cross a physical corner instead of ending at an arbitrary face chart boundary. Preserve every mesh and material slot.

A finite first density pair to test is uf0.38/vf0.32. Its unwarped geometric mean0.3487 is above the inherited1/3minimum, anisotropy1.1875 is below4, and the original dash estimate0.105×8/.32=2.625m remains≥2.5m. These are planning calculations, not UV or image PASSes. Do not globally raise v density to shorten all necks: the original median-dash gate would fail. Measure exact actual triangle density and every original full-stage UV/window/glow gate on resulting world geometry. Keep face- and area-weighted actual glow fractions inside original ranges; no empty zone lists, constants rebakes, altered component masks or mesh renaming. Repeat all three views and native Play proof. Hole10 scripts own any authorized chart implementation; shared texture retries alone are not the next proposed repair.

## Cliff same-budget feasibility

`cliff_array_columns_result.json` uses the exact2800existing H9 outline points and unchanged complete-chain predicate. Unequal alternating inward cutbacks reduce the14.844196m observed run to3.403690m≤4, with max cutback0.949983m and zero added points. The prior arc-periodic carve remains FAIL5.652701m. Both are array trials, not source geometry PASSes. See CLIFF_PLAN.md for required final clamp/fold/UV/scoring/budget checks. In particular, a shared all-bed cutback can create full-height joint steps: original strata statistics must be recomputed from the modified actual offsets, not retained from pre-carve Dd. Preserve the frozen staggered-joint predicates and report any resulting FAIL. No cliff library patch is authorized or applied yet.
