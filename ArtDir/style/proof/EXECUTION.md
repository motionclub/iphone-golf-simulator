# Combined style execution — 2026-10-15

**Update — character lighting reversed at Adnan’s request (2026-10-15).** The five character-lighting files are restored to their pre-pass versions and environment presets no longer enable or tune hero lighting. World lighting, ACES, haze, weather/materials and FX remain staged. Earlier hero comparisons below are historical rejected results. See [reversal evidence](character-lighting-reverted/GATE_RESULTS.md).

**Staged candidate; visual acceptance FAIL. No commits.** ACES is selected for both tiers. Device testing is deferred by Adnan. The look remains opt-in (`VISUAL_ENVIRONMENT_STAGE=7`; individual hero correction: `VISUAL_HERO_LIGHTING=1`). Default stage0 retains the original rollout state.

The hero correction uses .35 off-axis fill, .15 shadow floor, .12 ambient minimum with .60 saturation cap, the .60/.95 skin shoulder, a bounded .20 face bounce and a key-scaled rim capped at .35. Each of five world presets owns hero fill/rim/ambient values. Weather reads the existing blends, adjusts turf chroma and hero ambient/exposure, and preserves authoritative wind and restoration timing. Six master materials retain specialist shaders. Effects reuse existing pools and the native reduced-motion preference.

| Phase | Implementation / evidence | Remaining gates |
|---|---|---|
| Hero fix first | [Initial 344-view correction](../character-lighting/after2/GATE_RESULTS.md), then bounded face and weather refinements; final matrix below | Brightness, silhouette, lobby parity and darkest values do not pass everywhere |
|1 — Contract | [Gates](phase_01/GATE_RESULTS.md); corrected color roles, units, ownership, 60 fps target | Visual/device acceptance not implied |
|2 — Look-dev | [Gates](phase_02/GATE_RESULTS.md); 57 world + 52 hero views,  actual Unity Neutral/ACES comparison | ACES chosen; visual gates remain open |
|3 — Materials | [Gates](phase_03/GATE_RESULTS.md); six exact shader-default/pass/keyword parity checks, 57+52 views | Full tier cost and motion shimmer unmeasured |
|4 — Presets | [Gates](phase_04/GATE_RESULTS.md); five owners, 57+52 views; hub painted sky preserved |29/36 measurable faces, 16/22 silhouettes pass |
|5 — Weather | [Gates](phase_05/GATE_RESULTS.md); 57+52 views, 12 transition stills; coastal/snow/ash restore and wind checks pass |29/36 faces, 12/22 silhouettes; audio/network/device untested |
|6 — Effects | [Gates](phase_06/GATE_RESULTS.md); 57+52 views, 9 recipe sheets, 18 timestamped clips; reduced-motion counts/random-sequence checks pass | Simultaneous coverage/audio/haptics/device untested; visuals FAIL |
|7 — Full roster | [Gates](phase_07/GATE_RESULTS.md); 111 world + 344 hero views,  2 grounded hole 14 diagnostics |216/268 faces, 52/168 silhouettes, 19/268 lobby parity, 13/168 darkest 5% pass; device deferred |

Final hero saturation mean is 0.6823; detail RMS mean 12.223 (estimator provisional). Per-shot failures are retained in [combined-gates.json](phase_07/combined-gates.json). The next visual work needs to reconcile near-black garment shadows, face-to-lobby consistency and silhouette separation without increasing flat fill or washing out the world. The current candidate is not enabled by default.

Validation: 52 focused edit-mode tests; 9 existing gameplay/weather/camera tests; coastal/snow/ash transition/restore test; 9 FX recipes with stable pools; reduced-motion random-sequence/count check; High/Low ACES/bloom/DOF/no-fog parity; grounded hole 14 diagnostic; 10-case final activation-order suite. All seven full-matrix capture methods passed; two outdated activation expectations in that XML are documented and retained, then corrected in the dedicated suite.

No physical-device FPS result exists. The separate signed Style Audit build lost its device connection during installation and predates the final refinements; it is not final-performance evidence. No geometry, mesh, rig, animation-source, physics rule, event timing or production camera framing was changed by this pass.

Use [review entry](REVIEW.md), [reproduction instructions](tools/RUN_CAPTURE.md), [weather ownership](tools/WEATHER_CONTRACT.md) and [FX event routes](tools/FX_EVENT_CONTRACT.md). Raw scratch roots: /private/tmp/hero-lighting-lookdev and /private/tmp/combined-style-compile. Historical phase proofs are not relabeled as final-source captures; repairs and later test-only fixes are recorded in provenance.
