# Resort coconut crown finish1

GATE: WORK-ONLY SOURCE SILHOUETTE PASS.
GATE: ACTUAL RESORT APPEARANCE / LOD / PERFORMANCE PENDING ROOT CAPTURE.

One deliverable: fuller opaque coconut crowns in the existing resort palm placements. The target has connected, broad arching crowns; the old distant tennis palms read as separated strands. This source uses the approved golf-canopy20 arch design, adapted to tennis proportions after its original twelve-frond distant representation failed a matched tennis source review. Root actual golf closeups then showed angular sawtooth blades, so coarse strip outlines were rejected. Tennis near and far now share eighteen frond axes, with many slim smoothly curved folded featherlets. No new generic botany system was introduced.

Source proof at the same height 12.5m / crown-radius scale 4.65m, camera, lighting and runtime palette:
- Near crown occupied pixels 47,095 → 56,777 (+20.6%).
- Far crown occupied pixels 42,744 → 57,315 (+34.1%).
- Near 20,252tri versus 31,876 old (−36.5%). Far 15,108tri versus 14,284 old (+5.8%). These are mesh counts, not measured runtime cost. Extra distant blade samples deliberately prioritize graceful curves and full crown silhouette; source far vertices rise from 8,068 to 13,496.
- Both keep 18 frond axes, with 22/20 featherlet pairs and 7/6 curved blade samples. Widths .037/.043 provide fullness with many slim leaves rather than wide planar slabs. Each blade gains a transverse fold and smooth longitudinal arch / downturned tip. Source near world width changes 0.6%; near/far candidate widths differ 0.3%.
- Source proof: before-near-crown.png, candidate-near-crown.png, before-far-crown.png, candidate-far-crown.png. Fixed ROI alpha measurement is in coverage.json. Blender source lighting does not establish actual Unity shading acceptance.

Precise integration package:
1. Root can apply resort-palm-runtime.patch against current TennisVenueArt.cs. Only the BotanicalBatch constructor and last-loaded resource override change.
2. Import TennisResortPalmFinish1.fbx with supplied .meta to Unity/Assets/Resources/Tennis/Premium/. Import readable meshes, globalScale1, useFileUnits/useFileScale1, normals imported, no colliders. Editable .blend and build-canopy.py are work-only source.
3. Pilot via TENNIS_RESORT_PALM_FINISH1=1; flag0 keeps old source. Resource override also requires Resort venue. Missing resource preserves old palms. Mesh roles PALM/PALM_FAR, seven named semantic materials, leaf UV2.x=.90 and wind weights match the existing botanical reader. Existing TennisBotanical CullOff and front-face normals support the deliberate open leaf rims.

Small actual capture gate: capture-gate.json requests matched before/candidate gameplay1, reference14 and clubhouse17 only. Require visibly fuller outer crowns at left/right framing, no foliage over ball-flight corridor, unchanged tree roots/radii/heights/yaws and original spatial-pocket/LOD thresholds. Compare near/far movement through one actual LOD transition; reject a visible crown-size/frond-layout snap or harsh rectangular distant leaf highlights. Require unchanged court/net/collider/actor gameplay contract, no errors and no unexpected renderer count rise. Actual capture performance and phone measurements remain pending the root's wider task.

Source static contractPASS: Add/Append/Build from the first placement method through the end of the file are byte-unchanged. All existing palm placement calls, order, height/radius/yaw, court/net/physics, broadleaf/understory sources and non-resort venues are unchanged. Existing materials, accepted water3 and architectural-relief1 are untouched. This agent made no Unity Assets edits or Unity runs. This is a bounded resort source candidate, not acceptance of the full three-venue overhaul.
