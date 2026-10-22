# Serve walk arm: failing BEFORE reproduction

Current production code, unchanged animation files, real Tennis.unity campaign match and match male hero. Input enters only via ServeNudge; NativeControlled is enabled to prevent the keyboard's automatic toss. Graphics enabled, 60 simulated frames/second, PNG capture every second frame.

The initial 12-second run proves the failure. See before/male-rh-deuce/trace.csv and summary.json for exact per-frame numbers; the deepest walking-left frame exceeds 100 mm, with more than 20% of the 4,289 tossing-arm vertices inside the trunk. The worst vertices belong to LeftUpperArm. The left-side camera shows the entire upper-arm segment disappearing into the torso. Films: before/male-rh-deuce/game.mp4, front.mp4, left.mp4, top.mp4. The complete eight-case baseline is being recorded before any production pose change.

The target mismatch theory is confirmed, with two corrections: Match forces serveYaw to zero, so an extra serveYaw rotation is not the cause; and walking right also penetrates. The match carry point is the Serve clip's side-on palm, while the body and the preserved IK elbow pole come from Walk. TwoBone tries to reach that incompatible target, almost straightens the elbow, and directs the upper arm through the torso. The target also lags the visual body's yaw and root update because the game requests it before HeroTennisDriver.LateUpdate.

Measurement: actual body BakeMesh every frame; summed arm/trunk bone weight > 0.5. The trunk's 16,612 triangles are closed with three caps at its bone-region partition boundaries (248 boundary edges, zero unresolved/nonmanifold edges). Three parity rays vote on containment; exact closest original mesh triangles give depth, so synthetic caps cannot produce the reported distance. Both the measurement and the rendered disappearance must agree. Full method details are in each run's measurement.txt.

An additional existing limitation is visible in the code: HeroTennisDriver always targets LeftHand and plays right-handed match clips even when the gameplay actor is left-handed. The matrix will record the real behavior; it will not silently mirror a fixture.
