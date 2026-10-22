# Character lighting reversed — 2026-10-15

Adnan: “the characters look way worse now, need to be reversed only the character part” / “character lighting”.

GATE: CHARACTER SOURCE RESTORATION PASS — HeroLighting.hlsl, HeroFaceSkin.shader, TennisCharacter.shader, TennisCloth.shader and HeroLightingProfile.cs match the saved pre-pass files byte for byte. Existing earlier character work is preserved. No mesh, material asset, rig, animation or clothing geometry was reverted.
GATE: ENVIRONMENT PRESERVATION PASS — all five presets retain identical world arguments. All other environment/material/weather/FX source hashes match the staged candidate. Preset-owned hero fill/rim/ambient data is removed; the restored profile no longer consumes combined preset/weather state or enables the rejected lighting from the environment stage.
GATE: UNITY VERIFICATION PASS — 12 environment edit-mode checks and 7 activation/capture checks; 16 fresh hero views in Resort/hole7, including all four heroes in both environments. The pre-existing explicit hero look-dev flag remains independent; current restored captures use VISUAL_HERO_LIGHTING=0 and VISUAL_ENVIRONMENT_STAGE=7.
GATE: ART APPROVAL NOT CLAIMED — this is the requested reversal, not a new lighting treatment. World ACES, ambient and weather remain as staged, so exact pixels need not match pre-environment screenshots. Device testing remains deferred.

See restoration-audit.json for hashes and preserved world arguments; sheets/ and the two reversal.jpg files compare the rejected pass against the reversal. Actual Unity renders, no retouching. Raw: /private/tmp/combined-style-compile/character-lighting-reverted. Stage only; no commits.
