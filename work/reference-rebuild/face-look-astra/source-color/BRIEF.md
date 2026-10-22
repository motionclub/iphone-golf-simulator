# Source-default skin color repair

GATE: cause verified from current source and exported material values. GATE: patch applicability PASS. GATE: actual corrected default + selected-tone review PENDING; root owns Unity capture.

The first real resort portraits used no selected skin override. `TennisVenueCapture.Capture` called `SelectCharacter` and never `SetPlayerLook`; the hero therefore used imported OriginalSeam skin material values. In `refine_original_seams.py`, those values are authored directly into Blender Principled Base Color: male linear (.50,.29,.17), female (.66,.40,.25). Exported Unity Body look values are the same triples. `OnShader` copied those raw triples into the sRGB-authored `_BaseColor` property, effectively decoding them again in linear rendering. The eye importer already handled this distinction in `ConfigureFeature`, but skin had no corresponding conversion.

`source-color.patch` converts only imported OriginalSeam skin defaults with `Color.gamma` during material initialization. The reference values become sRGB BC9373 / D4AA89. `SetSkin` is untouched and subsequently writes caller-selected sRGB tones exactly; no shader lighting, skin palette, diffuse multiplier or brightness change is needed. `authoredSkin` and the default `skinTone` field receive the same conversion so relative paint/state stay coherent. `OwnMaterials` is guarded by `skinMaterials != null`, so the conversion occurs once per hero instance.

Native materials already consume sRGB look.color. Fresh Unity exports will contain corrected default colors automatically. Native `CharacterModelPreview` normally supplies its selected skin via picks, which remains unchanged.

`capture-tone.patch` adds optional `HERO_VENUE_CHARACTER_SKIN` selection through `SetPlayerLook` and a `skin-light-audit.txt` recording source/default, selected override, active `_BaseColor`, PlayerLook presence, SkinPolish, PresentationFill and FilmResponse. No override leaves the current default path intact. `map-color-queue.json` renders two real map shots for each sex under corrected defaults and under the same EA8D71/FBAE8F selected colors used by the studio proofs.

Keep current regional material and map fill while assessing this corrected comparison. The initial resort female nose hotspot and forehead band cannot yet justify another lobe change because the base color mismatch exaggerated specular contrast. Full eye/geometry art acceptance remains owned by root's final integrated proof.
