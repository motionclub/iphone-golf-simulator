# Opponent follow-up — isolated v37 proof

The frozen full-matrix candidate v33 and its films remain the reported baseline for the gate table. They are not installed.

An additional opponent-only hand roll limit change from 30 to 75 degrees clears the remaining male RH deuce walking collision. The exact follow-up diff is OPPONENT_V37_FOLLOWUP.patch, relative to v33; no player code, game clocks, source clips or assets change.

The fresh 900-frame test `after_r2_v37_smoke/opponent-male-rh-deuce-walk` passes all measured gates for that case: G1 exactly 0.0 mm and zero inside vertices, held-ball distance <=3.5 cm, camera visibility thresholds, elbow/belt, smoothness, frame order and right-versus-left comparison. Wrist step max 2.9834 cm at f8; speed-change max 0.500848 m/s at f115. Fixture teleport exclusions retain the same reasons and frames as v33. The 3.609512 mm f301 and 3.422237 mm f302 overlaps are now both zero.

This is a one-case experiment, not a full final matrix or installation approval. Its CSV, source hashes and completion record are retained. The full v33 report is deliberately not relabeled PASS. After authorization of the locked player Refeed transition, combine the fixes and recapture every after case, input film and review film against the fresh production baseline before considering installation.

The 60-degree trial still penetrated 0.198220 mm. Moving the opponent carry outward by 2 cm cleared penetration but exceeded the elbow/smoothness limits immediately after a fixture reset; an extra reseed also failed smoothness. Those alternatives were rejected. The 75-degree roll preserves the existing wrist trajectory in this test and avoids those regressions.
