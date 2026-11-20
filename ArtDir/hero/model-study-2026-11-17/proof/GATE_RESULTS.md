# Male Match Hero model study

**GATE: SCHEMATIC DELIVERY PASS.** Front, profile and back views show the same refreshed male tennis kit. The companion sheet gives close views of the polo armhole, shorts and court shoe.

**GATE: IDENTITY REVIEW PASS.** The [identity comparison](identity-comparison.jpg) shows the locked bald plate, the installed Unity face and the concept. The concept follows the Unity face, cap and athletic silhouette. Use the existing head mesh and the locked base for exact anatomy and scale.

**GATE: PRODUCTION MESH VALIDATION FAIL.** The images are concept views. Measured front and back overlays, armhole behavior at serve contact, and triangle counts require a built mesh.

## Build notes

- Reuse the male hero’s head, face and body proportions. Keep the complete bald head and the cap as a separate piece.
- Give the polo its own shoulder, sleeve and body panels. Treat the illustrated gusset as an inset into the underarm seam. Check sleeve clearance at toss, contact and follow-through. Keep the placket shallow and the fabric matte.
- Preserve the above-knee shorts and crew socks. Keep the shorts’ waistband, pocket openings and hem legible at phone distance.
- Keep the white court shoe silhouette with a lower rounded toe and clean heel. Bake fine stitch and tread detail. Preserve the separate garment slots and existing palette controls.

## Reference inputs

- Male bald authority plate archived in `ArtDir/style/alive/male-reference-pack-2026-10-17/sources/male_body_plain.jpg`. Its SHA-256 matches the locked plate hash in `ArtDir/hero/base_lock/plate-measurements.json`.
- Build identity from the male tennis full front and face front Unity captures under `work/final-plan-1111/look/turnaround_installed/MatchHero_Male/`.

## Built-in ImageGen prompts

### Turnaround

```text
Use case: identity-preserve. Transform input image 1, the existing Motion Club male tennis character render, into a clean production model turnaround for the SAME hero refreshed for a new model build. Image 2 is the face close-up to lock his identity exactly. Image 3 is the approved bald body proportion reference. Use the exact model's recognizable dark thick straight brows, inset brown eyes, warm tan skin with matte soft-plastic finish, natural moderately long nose, small relaxed neutral lips, lower cheek volume, defined tapered jaw, broad neck, ears, solid athletic body, full-sized hands, and white cap with dark navy curved brim. Same human age and face shape as input 1 and 2. Keep shoulder width, arms, waist and leg proportions from input, grounded compact toy-athlete scale. Do not redesign the face, eyes, eyebrows, head or silhouette. No hair. No superhuman musculature, no giant head, no new player.

Make a 3:2 landscape technical sheet, polished neutral warm-grey studio background with minimal pale drafting lines. Three aligned full-body views, same scale and horizontal floor datum: front, exact right side in profile, and exact back. The hero stands in the same relaxed shallow A-pose in every view, open natural hands and feet parallel. Entire silhouette visible in each view, including toes, wide margins. Center focus on the full-height renders, no props. Use the recognizable blue tennis polo, off-white above-knee shorts, cream ribbed crew socks, white tennis sneakers, same cap. This is a cleaned-up production version of his original kit: modest collar roll with short placket, softly tailored shoulder and sleeve with a little ease at the underarm, matte cotton piqué with fine low-contrast texture, woven shorts with defined hem, clean heel counter and slightly lower round athletic toe on the shoes. Keep the blue/white role and the original cuts. No badges or logos. Render as smoothly shaded 3D game art, similar to supplied renders with gentle neutral fill. Restrained signal-blue labels. Use only this exact text: title "MOTION CLUB / MATCH HERO"; subheading "MALE TENNIS MODEL STUDY"; view labels "FRONT", "PROFILE", "BACK". No other characters, face inserts, decorative numbering, technical measurements, or extra text.
```

### Construction

```text
Use case: identity-preserve. Edit the supplied Motion Club male tennis model turnaround into a companion production design sheet for the exact same hero, focusing on enlarged details of his existing outfit. Preserve the established solid athletic proportions and same blue polo, white shorts, white low-top court shoe. Same warm-grey background, blue sans-serif typography and matte 3D stylized game-art appearance as the input. A landscape 3:2 clean modeling board, three equal columns, one closeup in each. Use thin restrained drafting leader lines and show enough room around each part to inspect its shape.

Left column: three-quarter torso detail from cropped neck to waistband on the same athlete. One arm raised sideways with a softly bent elbow to reveal the blue polo's intact armpit seam. Show the armhole seam flowing around the shoulder cap into a small same-blue diamond-shaped gusset under the arm, lightly outlined by actual stitching, with visible ease. Preserve the curved collar fold, short narrow placket and cuff of the input. This is a technical close-up, the head is outside the crop. Middle column: realistic stylized rendition of the matching off-white tennis shorts, isolated front three-quarter view, simple elastic waistband with subtle topstitch, a pair of discreet slash pockets and a folded hem. Right column: isolated side three-quarter view of the matching all-white tennis sneaker, short rounded toe, crisp curved heel counter and a continuous cushioned sole with a thin molded outsole. No logos. The details should look manufacturable and easy to model. Use only these exact text strings: title "MATCH HERO / CONSTRUCTION"; left label "POLO UNDERARM"; middle label "SHORTS"; right label "COURT SHOE". No measurements, mesh wireframes, numbers, extra text, extra shoes or props.
```

