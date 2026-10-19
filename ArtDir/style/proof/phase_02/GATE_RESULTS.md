# Phase 2 — Resort and golf07 look-dev

GATE: CAPTURE PASS — all 7 capture tests passed; 57 world views and 52 hero views (44 supplied cases + all four heroes in both look-dev environments).
GATE: LOOK-DEV ACCEPTANCE FAIL — user review, cap-shadow face gates and sustained device cost remain open.

Blue acrylic court / green runoff now survive all late Resort material writers. The shared preset establishes stronger main-light shadows and three distance bands; world-space golf distances convert yards to metres. Active look-dev is restricted to Resort and golf07 at stage 2. Meshes, cameras, rigs, physics and gameplay were not changed.

Fixed scene ROI Lab-L P90–P10: Resort close **47.84→50.80**; golf07 tee **56.59→59.43**. Court sample changes from #007A82 to #007EBC. These are investigation metrics, not an artistic pass. Cloud animation differs between separate captures, so sky-box comparisons are not pixel-identical proofs.

`actual_unity_neutral_aces.jpg` is a same-frame tonemapper comparison. Adnan selected ACES from this actual comparison on 2026-10-15; the remaining presets use ACES on all tiers. `sheets/` contains 57 BEFORE | AFTER | REF sheets; `measurements.json` records hashes, ROI coordinates, displayed HSL and linear luminance. References r4/r5 panels are labeled crops, not rendered scenes.

Four-hero fixed-pose golf faces span L48.14–62.03, but normal golf cap close-ups remain L39.18/L43.35. Resort's female golf-kit look-dev is L42.10. These misses remain failures.

Raw: `/private/tmp/combined-style-compile/environment-before` and `/private/tmp/combined-style-compile/phase02-r4`; stage 2, High editor rendering, original scene mapper. No editor FPS claim. Production defaults remain unchanged while visual acceptance is open.
