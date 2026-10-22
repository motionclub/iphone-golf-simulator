# Golf wrist29 ordering-only revision2

GATE: Source rigid grip preservation PASS. Actual appearance PENDING; opt-in remains default0.

The original lower-arm segment already points at the hand (maximum .03956 degrees / .000456 mm source noise). Original weights are monotonic. The original source independently solves elbow poles and rotates hands with the shaft; the resulting forearm/palm kink is large. The bounded shaft roll improves that angle without moving the Club or changing original mesh, weights, bone count, rest identity, or contact timing.

Revision1 failed actual appearance: solving digits again after hand roll opened the grip. This revision removes that failed solver. Existing canonical fingers and FitDigits operate in the authored hand frame first; the bounded hand roll is last. It rotates every Hand/finger matrix rigidly around the actual shaft, preserving original baseline radius and shaft station. Golf review LateUpdate skips re-curling; the already-installed synchronous GolferView.Evaluate hook remains. A complete arm/hand/Club output matrix guard precedes any digit reset.

CPU proof uses the actual tiny control Body source vertices, weights, and matrices after baseline closure. Eight hand cases cover both sexes, Driver address/top. Maximum true distal pad radius change is 4.86e-13 mm; maximum rigid carry error is 6.89e-13 mm. This mathematical preservation is not an actual appearance gate and does not improve the baseline grip's existing errors. Mixed forearm/hand wrist weights intentionally deform with the new arm pose.

Apply HeroGripPolish.cs.patch with git apply -p0; it is incremental to installed revision1. Keep its GolferView hook. Use capture-config.json firstTinyPass Driver address/top, accepted face flags, studio0, pose dumps and diagnostics. Compare candidate against tiny-control images because the capture's before/after stamps may both follow synchronous correction. Pass only if wrists improve, fingers stay wrapped, Club unchanged, and elbow motion stays reasonable. If passed, extend to Driver/Putter contact and remaining clubs/landmarks before default adoption.

No Assets, production files, Unity, or GPU touched by this lane.
