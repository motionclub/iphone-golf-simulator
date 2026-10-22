# Continuous golf wrist review

GATE: source continuity PASS. Runtime / skinned appearance NOT TESTED here. Candidate remains opt-in with `VISUAL_GOLF_WRIST_ROLL=1`.

Apply `HeroGripPolish.cs.patch` alongside the separate `authored-preservation/HeroGripPolish.cs.patch`. This patch replaces only `ApplyGolfWristRoll` and adds a scalar eighth-power helper. It intentionally removes the old per-wrist cache reads; the separate authored-preservation patch owns the 37-transform outer idempotence cache and sampled-finger ordering. Do not replace root's complete file with this snapshot after merging other edits.

## What broke

The old global integer search compared disconnected minima at -45 and +45 degrees. Tiny source-pose changes changed the winner: the recorded Male Drive Left boundary at 2.44188755 seconds jumped 87 degrees / 68.881 mm at the wrist and 72.468 mm at the elbow. The final 40 mm elbow rejection introduced another output-to-zero jump. Projecting the old elbow into each new shoulder/wrist plane could also change the elbow pole rapidly near a straight arm.

## Deterministic correction

The new method computes one regularized local Gauss–Newton step from the sampled pose, using the derivative of forearm/palm alignment under a shaft roll. A smooth `tanh` limits that signed step. It never compares separate minima or reads previous frame output. A symmetric zero-gradient pose stays unchanged; this is intentionally a local correction.

The hand and every already-posed descendant move by one rigid rotation around the unchanged shaft. Digit local positions/rotations/scales are untouched. The source elbow plane is transported by the shortest rotation of the shoulder-to-wrist direction. The exact two-bone triangle then supplies the elbow position. Both segment lengths remain fixed. The club world position and rotation are explicitly restored after the arm application; existing rig scales are uniform.

## Continuous translation bound

Use model metres. Let a/b be original segment lengths, d the shoulder-to-wrist distance, rho the wrist radius about the shaft, and L = 0.04 m. The reachable radial interval is (|a-b|, a+b). Set q0 to half the smaller distance from d to either endpoint.

For any wrist displacement q <= q0, d' lies in [d-q0, d+q0]. Define l(x) = (a²-b²+x²)/(2x), r(x) = sqrt(a²-l(x)²), and alpha(x) = acos(l(x)/a). On that interval, rMin is the smaller endpoint radius and lPrime is the larger endpoint absolute derivative of l. The elbow displacement is bounded by a times the change in forward angle plus the change in alpha. Thus:

```
K = a * (1 / sqrt(d²-q0²) + lPrime / rMin)
|elbow shift| <= K * q
```

The forward-angle term uses asin(q/d) <= q / sqrt(d²-q0²). The alpha derivative is |l'|/r. The interval is reachable by construction, so both terms are finite away from a degenerate source arm.

The roll cap is the inverse eighth-power norm of four rates:

```
1/(pi/4), rho/L, rho/q0, rho*K/L
```

It is no greater than any individual limit. Since orbit displacement q <= rho*|roll|, this bounds wrist and elbow shifts by L while staying inside the reachable interval. `tanh` and the 35–50-degree activation only shrink that cap. No final pose is rejected. At a degenerate source arm q0 tends to zero and the allowed correction tends to zero; the zero-margin/zero-radius guards handle that exact undefined triangle. Eighth powers are normalized by the largest rate before evaluation to avoid float overflow.

## Recorded evidence

`python3 work/reference-rebuild/golf-wrist29/continuous-review/dense-check.py` evaluates all 10,550 recorded samples across both sexes, five golf clips and both hands, plus 10,610 subframe probes (all source interval midpoints and the old reported discontinuity locations). Source is the accepted pre-roll native tracks, not a new animation bake.

- Maximum wrist / elbow shifts: 22.960 / 23.002 mm.
- Maximum wrist / elbow correction changes across 0.2 microseconds: 0.000580 / 0.001078 mm.
- Random seek-order difference: exactly zero.
- Segment length and all sampled digit radial shaft-contact errors: below 3e-13 mm in the double-precision oracle.
- No recorded angle regressions beyond floating-point error. Mean improvement across active samples: 5.677 degrees.

The report distinguishes genuine neighboring-source motion from discontinuities. Maximum neighboring correction movement still reaches 11.33 mm at the wrist over the source sampling interval; it is continuous source-dependent motion, not a claim of constant correction velocity. Full report: `continuous-source-evidence.json`.

The bounded correction does not remove the 120–134-degree extreme source wrist bends. Female right-hand address poses improve very little because the source arm is near its geometric reach limit. These are material appearance limitations, not passed art gates. Root must merge authored-finger preservation, run the small actual capture, and check the skinned wrist shape / club / finger appearance before deciding whether to pursue or reject the candidate.
