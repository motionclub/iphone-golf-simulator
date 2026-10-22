# Tennis resort material candidate

Actual baseline: proof/full-visual-overhaul/tennis-worlds-pass-22/resort_1_gameplay.png, resort_14_reference_camera.png and resort_17_clubhouse_close.png, compared directly with outputs/visual-overhaul/after/tennis-resort-target.png.

Three bounded material gaps: grey/olive court instead of cyan acrylic; peach/washed architecture without stone/wood/glass separation; grey-blue sea and muted leaf hierarchy instead of turquoise/deep blue and golden-green leaf light.

Candidate: original court/runoff albedo and roughness recalibrated; original clubhouse atlas/gradient retained with distinct plaster, warm wood, terracotta and cool glazing responses; original leaf geometry retains deeper shaded greens and bounded sheen/backscatter; sea uses a richer cyan/blue palette. Existing renderer SSAO is consumed only at 0.30 indirect weight, with no direct-light multiplication. Other venue material response remains zero.

Court/net/contact/collision, all model XYZ/bind geometry, shared HeroLighting, renderer/post resources and cameras are unchanged. No new assets searched or generated.

GATE: Installation and Unity compile PASS. Actual seven-view capture completed with no shader/compile errors at proof/reference-rebuild/tennis-resort-material1.

GATE: Bounded material improvement PARTIAL. Same-camera gameplay court sample moved RGB75/136/137 to76/157/160; the cyan court reads livelier, stone/canvas less peach, leaf shadow hierarchy clearer. The actual clubhouse still has broad flat forms and paving highlights can clip under the current ungraded pipeline. The sea sample moved only85/133/171 to82/133/171 and still reads grey-blue. Full reference appearance FAIL; this pass must not be called complete.

The next bounded water2 candidate addresses demonstrated broad-ocean vertex fog and adds restrained existing-sky reflection. Capture config: work/reference-rebuild/capture-tennis-resort-material1.json. Optional control uses TENNIS_RESORT_MATERIALS_OFF=1 in a new process.
