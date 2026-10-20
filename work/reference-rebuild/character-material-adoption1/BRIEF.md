# Existing default character material candidate 1

WORK ONLY; no Assets mutation or Unity invocation. One bounded candidate for root serialized actual validation.

Material-only transfer is viable. Eye13's direct ConfigureFeature call alone is **not** enough: its iris/sclera maps expect OriginalEyeLocal UVs authored only on the optional OriginalSeam features. This candidate derives that same planar eye projection as material uniforms on the existing default face, before gaze/closure in the shader. Positions, topology, UV buffers, normals, rig, face roles and blink code are unchanged.

- Skin: existing registered `_SkinResponse` = male 1 / female 2, `_Saturation` = 1. Selected/saved skin tone remains controlled by SetSkin; no automatic preset, lighting, post or AO change. The OriginalSeam Body pigment LUT is **not** transferred because its UV0 stores lip/seam masks absent on the default Body.
- Eyes: exact existing Eye13 relative iris/sclera LUTs and accepted warm-brown/ivory colors and response. Projection derives from actual current triangles; group all Iris/IrisIn parts so boundaries agree.
- Solid brows: accepted matte response and color. Legacy BrowSoft remains skin-following; lip/lid/nostril roles remain unchanged.
- New default-adoption candidate switch `VISUAL_ORIGINAL_MATERIAL=0` restores existing default material treatment. OriginalSeam / replacement pilots bypass this helper; their paths are untouched.

## Root integration

Apply MatchHeroLook.cs.patch and TennisCharacter.shader.patch to current production files (do not overwrite whole candidate copies). Copy HeroOriginalMaterial.cs into Unity/Assets/Scripts/Tennis and let Unity generate its meta. Apply the optional one-line VisualOverhaulCharacterCapture.cs.patch for matched response validation: its current swatch loop overwrites `_SkinResponse` for **both** A/B sides, hiding runtime response adoption. `VISUAL_CHARACTER_USE_MATERIAL_RESPONSE=1` keeps runtime material state during the otherwise-identical pigment photography. This flag defaults off, so existing capture behavior stays unchanged.

Run capture-material-adoption1.json with `VISUAL_ORIGINAL_SEAM=0`, `VISUAL_REFERENCE_HEAD=0`, `VISUAL_ORIGINAL_EYE_MATERIAL=1`, comparing new switch 1 vs 0. Expected actual outputs: male/female pigment front/threequarter + full/Intro. Root should additionally verify open and closed legacy blink + gaze to confirm texture stays on the eye and no role is disturbed. A gameplay-lighting photo is needed before default adoption; warm studio ACES photography does not certify gameplay appearance.

## Source evidence and limits

Read-only Blender projection audit reproduces accepted Eye13 UV mapping within max 0.000010982 UV units = 0.001406 texels at 128. Numeric tolerance is 0.002 texels; the first 0.00128-texel threshold was too strict for triangulated nonplanar male sclera, and is retained in the work history as an audit failure rather than an art failure. Source positions are not edited. Work-only-source-gate verifies production sources remain byte-identical to this agent's baseline and helper only writes material properties.

Actual Unity compilation, FBX-imported vertex splitting/normal coordinate registration, material response under game lighting, gaze/blink and matched captures remain PENDING. This does not reproduce reference facial anatomy, fine beard texture, lip integration, garment construction or broad soft lighting. The targets remain substantially beyond this bounded transfer.
