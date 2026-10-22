# Male reference pack, gates (2026-10-17)

- SHEETS: PASS. 14 sheets present, incl. dedicated tennis-shoe (13) and golf-shoe (14) detail sheets with six views each
  (lateral, medial, front, back, top, sole); golf sole shows the spike layout.
- FORMAT: PASS. Same header/subtitle/footer/view-label format, background and neutral studio light as the female pack.
- IDENTITY: PASS by review (bald adult man, broad rounded-square face, straight dark brows, brown eyes, firm jaw, athletic build,
  as in the locked plates); no hair, beard, slimming or age change. Adnan ACCEPTED 2026-10-17; handed to garment-pipeline the same day.
- PROMPTS + MANIFEST: PASS. `GENERATION_PROMPTS.json` (exact prompts, model/quality/resolution, references, job ids,
  credits) and `MANIFEST.json` (sizes + SHA-256).
- REPAIRS: 08, 11 and 12 were regenerated once. The first 08 and 12 copied the plate's full-body layout; the first 11 lost the
  kit colours. The rejected first tries are kept outside the pack (`work/female-face-shader/male-pack/dl/*_first.png`).
- Known limits: 01-06 are 1024x688 (medium/1k), below the female pack's 1536x1024; detail sheets are 2048x1360. Elevation
  sheets 05/06 show only a mild camera-height change. Generated images are not calibrated cameras.
- Cost: ~14 credits on the connected image service (Higgsfield, GPT Image 2.5 medium).

## Addendum 2026-10-17 (chat 11): sheets 15-17
- NO_CLOTHES_BODY: PASS. 15 (cardinal) + 16 (obliques), bald, plain grey base body, same format. 15 regenerated once (first try
  too muscular vs the plate; rejected copy in `work/male-face-body/refgen/dl/15_try1.png`).
- FACE_DETAIL: PASS. 17 = 6 panels incl. jaw/chin, lips and jaw+lips profile close-ups; same face/skin as 07.
- IDENTITY: PASS by review (same bald man, brows, eyes, nose, jaw); Adnan to confirm.
- BODY DECISION: Adnan 2026-10-17 kept the locked plate body; sheets 15/16 are not a body-proportion target (chat 11 GATE_RESULTS: BODY =
  matches the locked plate, by Adnan's decision).
