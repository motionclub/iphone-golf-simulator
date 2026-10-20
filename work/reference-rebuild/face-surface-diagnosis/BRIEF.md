# Face surface diagnosis — one normal candidate

GATE: SOURCE STAGING PASS. GATE: ACTUAL UNITY ART PENDING. No production Assets, source meshes, native code or exports changed here.

Viewed actual `proof/reference-rebuild/character-skin-finish2-revision1/{female,male}_pigment_front.png` against the user target portraits first. Female nose/lips remain broad and blurry; male eye sockets/mouth corners show irregular planes; both have uneven cheek/jaw transitions. Earlier Blender `original-refinement/{female,male}_seam_pilot_front.png` already shows these defects under a different renderer and lights. That is evidence of an existing surface-form/pigment limitation, not proof that Unity's shader alone causes the gap. These source shots precede the accepted eye13/blink treatment and are diagnostic only.

The current pipeline:

- `HeroOriginalSeamAnatomy` loads OriginalSeamBlinkFinish, preserves the 53-bone mapping and original face proportions, uses relative lip/seam masks, and isolates blink normal deltas on unmoved vertices.
- `MatchHeroLook` opts this original-seam candidate into `HeroSkinNormals.Continuous` only through `VISUAL_CHARACTER_NORMALS=continuous` (the actual revision1 setting). SkinBump is zero, so this is not normal-map texture noise.
- `HeroHeadSurface` registers low-frequency warmth in bind space; it does not repair local geometry or normals.
- Revision1 pigment uses linear existing masks. `HeroSkinShade` now has one broad restrained lobe, .28 wrap and .82 ambient. Stronger contrast already failed because it highlighted existing uneven face planes.
- `HeroSkinNormals.Continuous` initially calculates area-weighted normals, then normalizes them and smooths equal-weight vertices within 8 mm. The latter operation loses represented surface area and therefore gives dense tessellation more influence.

A read-only Blender audit of the accepted BlinkFinish1 source establishes nonuniform tessellation inside that radius. Median local max/min represented-area ratio is 4.13 male / 4.33 female; 95th percentile 44.08 / 123.20. Replacing equal-vertex influence with represented area changes the unrestricted source field by mean 1.93° / 1.70°, 95th percentile 7.80° / 6.48°; 1,505 / 1,522 front points exceed 2°. Full numbers and exact input paths are in `density-audit.json`. This reproduces the field construction on source triangles only; it is not an audit of imported Unity triangles, the angular-cap result, GPU normals or pixels.

One candidate is staged: weight the existing continuous normal filter by each welded point's incident triangle area. Keep radius 8 mm, 20° correction cap, spatial mask and geometric normal construction. Keep all positions, triangles, bindposes, bones, weights, UVs and blendshape arrays cloned unchanged. No skin-tone, pigment, eye13, blink, lighting, shader or material change. This isolates tessellation bias without increasing smoothing radius or inventing face anatomy.

`VISUAL_CHARACTER_NORMAL_AREA=1` selects the work-only candidate with a separate cache. Flag 0 retains the existing continuous path. This patch does not change runtime defaults.

Root can apply `HeroSkinNormals.cs.patch` and optional `VisualOverhaulCharacterCapture.cs.patch` with `git apply -p0`. Both pass `git apply --check -p0` against the source read here. Full staged files and source hashes are included for review; do not copy them over newer unrelated edits.

`capture-two-front.json` requests exactly two front Ready pigment shots (male/female), matching actual revision1 camera, filmic lighting, skin swatches, finish1, eye13 and OriginalSeamBlinkFinish. The small editor capture patch only skips additional views in `VISUAL_CHARACTER_TWO_FRONT_ONLY=1`; it leaves default capture behavior unchanged. Compare with existing actual revision1 front shots. If an exact fresh control is needed, rerun this same configuration with NORMAL_AREA=0 and another output path, not a parameter matrix.

Actual adoption criteria: visibly smoother uninterrupted cheek/jaw lighting, no new nose/lip blur or lost form, same face identity/eye geometry. A two-shot result cannot establish posed-blink quality; existing blink shapes remain source-identical but any adoption should retain the already accepted blink verification. Do not claim target match from a source normal metric. The source nose/lip shape and interpolation may still be the dominant limit after this test.
