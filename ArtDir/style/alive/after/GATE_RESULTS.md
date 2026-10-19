# Female alive — quick-pass gates (2026-10-15)

GATE: FEMALE-ONLY IMPLEMENTATION PASS
- Male exclusion test passes. Runtime attachment requires `look.female`; no male assets were edited.
- 472 protected source assets (FBX, clips, prefabs, scenes, materials, shaders, camera files) match their starting SHA-256 values. `protected-assets.json`.
- Existing garments, sockets, bindings, colour controls, face identity and authored emote/stroke clips retained.

GATE: IDLE / FACE / ATTENTION PASS
- Final idle: new layer weight 1 throughout; no repeated head-position sample at the trace's 0.01 mm precision. Added breath is under 1 degree, asymmetric spine sway under 0.65 degree. It stops before contact actions and returns after emotes.
- Existing blink timing retained; observed closure reaches 99.57%. Wave smile now ramps to 100% of the existing smile morph, then returns to zero. Joy/slump choreography and expressions retained.
- Existing tennis ball tracker retained. Golf gains immediate eye attention and bounded delayed head follow (16° yaw / 10° pitch), with no root/foot offset; authored emotes retain head ownership. Golf face reactions use the existing outcome/putt state; no extra game delay.
- See `telemetry-summary.json`, `evidence/`, and the muted diagnostic comparisons. Diagnostic cameras are editor-only proof views, explicitly labeled; gameplay cameras are unchanged.

GATE: FABRIC OVERLAP / PRESERVATION PASS
- Two independent spring weights per top/skirt; chest, hip and upper-arm movement excites them. No per-frame mesh upload or cloth solver.
- Verified maximum outward movement: top 5 mm; skirt/skort 10 mm. Original mesh vertices, indices, UVs, bones and bindposes retained; waist/collar regions pinned. Existing corrective morphs retained.
- Wave cloth weight peaks at 0.635, joy at 0.973, then settles below 0.10. Light idle flutter remains.
- Before/after sheets and sampled action/return frames show no new visible clipping or identity drift. Existing underarm garment/skin boundaries remain visible in both versions; this pass does not repair those. This is visual comparison, not an exhaustive collision proof.

GATE: GAMEPLAY / REGRESSIONS PASS
- 7/7 focused EditMode tests pass (`tests-final.xml`), including existing backhand/serve contact, neutral skirt binding, shoulder and wave-wrist regressions.
- Tennis: all 1,272 trace rows match exactly for ball position, player position, score, rally count and phase (`gameplay-parity.json`).
- Golf: unchanged impact frame 62, 7.0 s shot, and rest position (63.83980485892345, 205.2366109077439); matched 13 mph wind at −33°. Both captures have 314 video frames.

GATE: MUTED PROOF PASS
- 31 H.264 clips, all with zero audio streams (`media-audit.json`).
- Start with `female-alive-review.mp4` (27 s). `gameplay-sheet.jpg` and `detail-sheet.jpg` provide the before/after sheets. Individual `compare-*` films retain full takes; `before-*` and `after-*` are separate originals.
- Simulated at 60 Hz, encoded at 30 fps; this is captured Unity gameplay, not a phone recording. Tennis weather fixed to Clear; golf uses the same Gusty environment/wind. No lighting/scene/camera assets edited.

GATE: PHONE 60 FPS FAIL — NOT MEASURED
- Editor marker: 990 samples, mean 0.008310 ms, max 0.030626 ms for the added runtime layer on Apple M5. This excludes GPU work and is not an iPhone frame-rate certificate.
- An on-device run of the rebuilt app is still required to close this gate. No claim of measured phone 60 fps.

GATE: STAGE ONLY PASS
- Explicit source, test, audit and proof paths staged. No commit, push, stash or checkout.
- Raw frame folders and exploratory captures are local working evidence; the staged MP4s, sheets and traces are the review deliverable.
