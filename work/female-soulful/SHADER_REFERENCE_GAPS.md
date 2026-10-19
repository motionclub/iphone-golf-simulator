# Shader appearance comparison — 2026-10-16

User: "why does it look almost the same? pull up the ref image and compare their shaders".

GATE: Reference material appearance FAIL. Shader implementation exists, but the achieved appearance is not close enough to the reference. Do not describe material work as basically finished or only awaiting final integration.

Proof: `proof/review/reference-vs-current-shaders.jpg`. Left crops are from reference sheet08 and the original clothes-with-weight board; right crops are from `proof/surfaces-current/golf_default_close.jpg`. Only cropping, resizing and comparison labels were applied. Source lighting, camera, skin selection and geometry differ, so this is an appearance comparison, not an isolated shader A/B. The original reference is generated imagery, with no inspectable shader implementation.

Visible gaps:
- Skin: reference has clearer broad satin highlights and richer light-to-shadow separation; current Unity face reads pale/chalky with broad even fill. Selected skin color and reference lighting also contribute; a fixed tan tint is not a general shader fix.
- Eyes: reference has greater depth and a more integrated glossy response; current iris/sclera read flatter and more graphic. Preserve original eye/head geometry and proportions.
- Fabric: reference shows matte knit breakup, rounded fold shading and clearer material separation at the collar/cuff; current polo is overly smooth and rubbery, with dark drawn-looking seam lines. Collar thickness, air gaps and fold geometry are separate construction issues; roughness alone cannot supply them.
- Cap: current seams are conspicuous while fabric response remains broad and smooth. Reference seams sit within a coherent cloth surface.

The preceding shader pass mainly reduced color cast, cavity contrast and fabric sheen. It did not establish the substantial reference-level improvement requested. Future work should compare one major material variable at a time while keeping original identity, selectable colors, production lighting/cameras/maps and accepted arm motion fixed. Skin satin, eye gloss and matte cloth must remain distinct. Use actual Unity renders for new proof; no generated replacement proof.

## Update — 2026-10-16 shader pass (proof/shader-pass/)
- Skin: female path now uses Lambert form + a terminator band in the picked tone's own saturated hue, a broad satin wash plus a soft core, tone-tinted hemispheric ambient, lower camera fill, female saturation floor .95 (the shared .74 pull to grey caused much of the chalky read) and quieter blush. Pale studio look was partly the review harness never applying a skin pick; the new harness uses the game default (Cream) and Fair/Tan/Deep.
- Eyes: the original-seam eye layers had no lid frame, so earlier eye shading could not vary by position. A bind-pose frame now drives upper-lid occlusion on every eye layer, socket corners, a lower-iris caustic and a sclera energy cut (sclera no longer clips).
- Fabric: matte Lambert + deep-hue terminator band, rounded volume toward the silhouette, Charlie velvet sheen, softer cavity/seam darkening, stronger filtered knit breakup. Rubber excluded from sheen.
- Status: substantial visible change measured; appearance acceptance is the user's. Not installed in production yet.
