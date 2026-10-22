# Gate results — ears continuation

GATE: G1 PASS — 12 sheets exist: before and after, both heroes, front / 30-degree three-quarter / actual gameplay camera. Only frontal targets were supplied; the other sheets explicitly retain those frontal targets on the left.

[Proof](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/proof/G1-sheets.json)

GATE: G2 FAIL — Manual front overlays show deviations up to about 15%, exceeding ~5%. Eye heights/positions, male brow thickness, female nose dimensions and lip proportions still differ.

[Proof](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/proof/landmarks.json)

GATE: G3 FAIL — Skin and cheek shading are closer than the previous candidate, but the court shadow direction and nasal gradients still differ from the studio references. Five-pixel patch measurements show CIE76 differences up to 11.18; these include illumination differences.

[Proof](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/proof/skin-patches.json)

GATE: G4 FAIL — Blink, gaze and brow morphs run, but enlarged closed-lid frames retain small edge/shading artifacts, and the female jaw/neck boundary remains visually hard. Cannot certify the no-tearing/no-seam visual requirement. Topology/weights/binds are retained and no vertices below the head moved.

[Proof](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/after/male_idle_3s.mp4)

GATE: G5 PASS — The updated check.sh compiles. Current: 312 passed, 6 failed; isolated pre-ear source baseline with current shared code: 312 passed, 6 failed. Identical failures show no ear regression. Final Unity capture has zero C# or shader errors. The index contains only 8 face/head source files and their 8 metadata files.

[Proof](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/proof/check-comparison.json)

GATE: G6 FAIL — Not yet approved by Adnan. Agent review is not approval.

[Proof](/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match/proof/G6-approval.json)
