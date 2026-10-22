# Failing BEFORE reproduction

Male RH deuce: 105.2082 mm ARM-in-TRUNK at frame 129 (2.150 s), 23.78177% inside at that frame, dominant bone LeftUpperArm. Female RH deuce: 78.70114 mm at frame 143 (2.383 s), 17.39927% inside at that frame, LeftUpperArm. These are actual moving-left frames after the input stops while the game decelerates.

The target mismatch theory is confirmed: a Serve-derived hold target and inherited elbow pole do not fit the Walk body, pulling the upper arm through the trunk. Match sets serveYaw to zero, so the extra serveYaw rotation is not the cause, and the right walk also penetrates. The target is requested before the driver’s visual yaw/root update, adding a frame mismatch.

- Exact male front still: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/before/male-rh-deuce/worst-front_00129.png`
- Exact male left still: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/before/male-rh-deuce/worst-left_00129.png`
- Exact female front still: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/before/female-rh-deuce/worst-front_00143.png`
- Exact female left still: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-walk-arm/before/female-rh-deuce/worst-left_00143.png`

All 16 requested cases have a BEFORE trace and film. The candidate clears player walking penetration but fails the full gate; see report/GATE_RESULTS.md and report/matrix.json. No production carry fix is installed.
