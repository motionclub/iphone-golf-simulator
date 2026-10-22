# Dream Coast — revision 2

The user rejected the first pass as too similar to the existing game, with worse trees and improvement concentrated in the painted background. The user chose **dreamlike fantasy: spectacular landforms and surreal color**. This revision changes the golf pilot, authored hole12 / Cliffside's displayed hole04. Tennis remains on the first coastal pass; this revision does not claim a completed fantasy redesign of tennis.

## Delivered in the working game

- Real 3D stone arches, four suspended garden islands with miniature groves, brass inlays and flowing waterfall ribbons. They have translation parallax and cast structural shadows.
- Separately built white-and-brass lighthouse with modeled galleries, window frames, cornices and a halo crown. Existing lighthouse renderers are disabled before static batching; source collider meshes stay intact.
- Curved stone bridge supports, slender railing, and toned timber surfaces.
- Flowering tree kit rebuilt from branches and curved individual leaf meshes. The first pass's solid clump canopies are replaced.
- Quieter mowing bands, shorter turf blades, revised daylight direction, surface contrast and shadow composition.
- A scoped portrait tee camera adjustment: slightly farther back and higher on golf12 near the tee. Landscape, putting, other holes and flight logic retain their existing composition.
- The approved sky panorama remains. No new sky painting was used to stand in for the geometry changes.

## Evidence gates

- **GATE: Unity compile and rendered shader variants PASS.** Final scene capture and automatic-frame measurement have no C# or shader compile errors (`verify.json.results.json`).
- **GATE: Actual before/after proof PASS.** `proof/comparisons/01_previous_vs_dream.png`, `02_whole_hole.png` and `04_lighthouse.png` compare the rejected first pass against the new pass with matching cameras. `03_gameplay.png` uses newly captured original art with the same new tee camera on both sides. Animation/water phase can vary. Boards only label/resize actual Unity pixels.
- **GATE: Course physics PASS.** All 161 obstacle records and their hash match. All 14 collision meshes, transformed vertices/indices, and counts match the freshly captured baseline. Golf7 also matches. See paired `proof/{baseline-matched,final}/hole12_audit.json` / `hole07_audit.json`.
- **GATE: EditMode regression PASS.** 63/63 tests in `proof/regression.xml`.
- **GATE: Play-mode integration PASS.** `proof/play-check.xml` records the passing real-scene test. Checks source collider identity/transforms, obstacle equality, zero scenery colliders, ball visibility above controls, unchanged landscape camera, and full removal of pilot owners when leaving golf12.
- **GATE: Automatic-frame workload collection PASS.** Three consecutive sole-camera Metal frames agree with UnityStats: 116 draw calls, 45 SetPass, 4,706,722 submitted triangles at 900×1600. Includes shadow/render passes. See `proof/costs/hole12_tee.frame_costs.json`.
- **GATE: Physical-device FPS NOT MEASURED — user waived.** 60 target / 30 fallback remains. No 30/60 guarantee or thermal claim. No new device build/install in this revision.

## Budgets and limits

The static garden kit is 287,590 unique triangles in eight meshes/seven material families. Small flowers and distant groves do not cast realtime shadows; opaque arches/architecture and the primary planted trees do. Curved tree leaves are opaque geometry; no alpha foliage-card overdraw. Waterfalls are four transparent ribbons, 192 triangles total. Source budgets: `garden-budget.json`, `tree-budget.json`.

The final camera includes more of the world, so its 4.71 million submitted triangles should not be presented as an identical-view speed comparison with the first pass's 3.45 million. Draw counts alone do not measure shader time. Mobile frame pacing remains unmeasured.

This is a substantially different fantasy art candidate, not a claim of AAA parity or user approval. The existing playable islands remain the physics authority. The remote painted horizon is still a panorama. The larger environment additions are actual 3D geometry. Existing character/garment assets and weather behavior were not authored by this revision.
