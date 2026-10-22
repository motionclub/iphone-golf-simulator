# Actual paired material review

Root serialized production installation and captured both sides at proof/reference-rebuild/character-material-adoption1 and character-material-adoption1-control. I inspected male/female front and threequarter candidate portraits and the matched front controls.

GATE: Unity compilation/render execution PASS. Both actual audit.txt files end CAPTURE PASS. Runtime logged 2 male and 3 female projected iris/sclera materials; no projection-registration warning was found. This is actual imported geometry, so the source-only projection concern has a valid visual check.

GATE: bounded eye/brow material transfer PASS. Both bodies now show readable warm radial brown iris rings in place of the very dark flat control rings. Sclera upper/outer transitions remain coherent; no offset texture or eye-proportion change is visible. Solid-brow pigment is matte; their existing default shape is unchanged. Eye-region mean absolute channel delta is 3.05/255 male and 4.65/255 female (large 380x135 px box; not an art-quality score).

GATE: substantial reference skin/color transformation FAIL. Warmth/roughness adoption is much smaller than the target gap. Sampled central-skin channel difference averages 1.54/255 male and 1.74/255 female; the response slightly reduces broad forehead/cheek highlights. Male beard-zone variation is barely readable. The reference has stronger modeled light, integrated lids/lips and a richer defined lower-face response that this bounded port does not supply.

GATE: default face portrait/reference fidelity FAIL. Matched controls confirm existing legacy failures are unchanged by the candidate: female double dark eye outlines, thin default brows, male black nostril sheets and detached flat lip paint. Public OriginalSeam portrait is still cleaner around these areas, but that source/animation candidate remains separate and opt-in.

Recommendation: accept only the proven iris/sclera + matte-brow material delta as an independent bounded improvement if root wishes. Do not present this as the character makeover being complete or imply the skin gap was resolved. Keep target comparisons on honest actual captures. No default/native/device acceptance follows from these studio photos. Open/closed blink and gaze, actual game-lighting appearance, and native surface parity remain untested here.
