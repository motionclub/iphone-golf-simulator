# Hero lighting FIX_PROMPT — corrected experiment

GATE: CAPTURE PASS — 10/10 scratch tests; 344 hero frames (336 main / 168 gameplay plus 8 four-hero look-dev views).
GATE: VISUAL FAIL — not accepted for shipping/default activation.

- Whole-hero gameplay HSV saturation mean **0.6377**, target ≥0.62: aggregate PASS. Individual shots remain listed.
- Detail **11.721** Lab-L Laplacian RMS, provisional target ≥6.8. The prompt did not define its estimator; this is not a calibrated match to that original number.
- Silhouette **66/168** at dL≥15, target ≥110: FAIL (combined plan requires all 168).
- Face L45–65 **44/268** visible-face shots: FAIL. Mask-hidden faces are not treated as passing.
- Darkest 5% mean L **2.387**; only **41/168** gameplay shots in L3–12: FAIL.
- World-only paired comparison: worst per-shot mean absolute RGB difference **0.030531/255**, excluding a 31px dilated hero silhouette. No world lighting changed during this hero-only run; minute temporal/render differences remain.
- Lobby parity and physical-device cost are not newly passed by these captures.

`fix-gates.json` names every failed face, silhouette and shadow shot. `metrics.json` contains the paired original/after measurements. The four-column sheets also include the previous flat test and the supplied reference; no render was retouched.

Raw lossless frames: `/private/tmp/hero-lighting-lookdev/after2`. Same-frame baseline turns off the experiment, restoring fill .12. Hero-only source used hardcoded ambient .12/.60, equivalent to the later profile default. Environment stages were disabled. Capture test success does not establish artistic acceptance.
