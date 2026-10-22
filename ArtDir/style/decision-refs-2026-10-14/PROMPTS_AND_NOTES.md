# Decision reference boards — 14 October 2026

Created with the built-in image_gen tool using the existing AI style references. These are appearance mockups, not game captures, exact shader comparisons, or evidence of an achieved frame rate. No Unity assets or settings were changed. Generated source images were preserved.

Confirmed: **60 fps on every tier, never 30.** Adnan selected **2B, 4B and 5B**. Decision 3 remains open because the generated examples did not show a useful visible difference. Show actual matched Unity renders before deciding the tonemapper. These choices record visual direction only; implementation has not been authorized.

| Decision | A | B | Board |
|---|---|---|---|
| 2 Court palette | Teal | Blue with green surround | [Compare](02_court_colors.png) |
| 3 Grading | Neutral style | ACES style | [Compare](03_color_grading.png) |
| 4 Focus | Sharp background | High-tier far blur | [Compare](04_background_focus.png) |
| 5 Materials | Simple color and sheen | Restrained material detail | [Compare](05_surface_detail.png) |

For decision 3, these illustrate a preference for cleaner/open versus more filmic/contrasty treatment. Exact Neutral versus ACES must be shown with matched HDR input in Unity. Grading and exposure can affect the result as much as the tonemapper choice.

For decision 4, retain crisp foreground and opposing players, ball, net and all playable court. The revised image corrects an initially over-blurred opponent. Blur is optional, High-only, and subordinate to 60 fps. Sharp live gameplay with optional presentation blur is also a valid choice; a still does not decide when an effect should run.

For decision 5, shader-family organization is invisible. This board compares the permitted surface detail: fine acrylic grain, short grass, ice depth and lava crust. Both styles can share six master families. A preference for B authorizes no implementation by itself.

AI comparisons can introduce small framing or geometry differences. Judge the labeled appearance variable; final proof must use the real game and current accepted camera.

## Prompt set

### 02_court_colors

Inputs: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/style/refs/r2.png`

```text
Use case: stylized-concept. Asset type: visual decision reference board, illustrative AI mockup, not a Unity capture or performance proof. Modern polished stylized sports game, soft plastic forms with rich but readable materials, classic Nintendo sports charm. Create a carefully aligned A/B comparison with two equal landscape images STACKED VERTICALLY, ample pixel resolution, thin neutral separators and simple readable labels on a clean dark header for each. Same scene, same framing, camera, geometry, props, hero identity/pose/outfit, sunlight direction and object placement within both variants. Do not redesign characters or add props. Copy the supplied reference closely. Each panel should retain the full wide camera composition rather than crop the foreground hero. Small footer exact text: 'CONCEPT COMPARISON - NOT A GAME CAPTURE'. Input image 1 is the layout, light, material-fidelity and camera reference. Decision 2, compare COURT PALETTE ONLY. Top label '2A - TEAL COURT'; top image: beautiful mid-bright turquoise-teal acrylic playing court, a slightly darker desaturated green-teal runoff, clean white regulation lines. Keep the teal family of the existing game but give it the SAME polished fidelity, visibility and lighting as the lower image. Bottom label '2B - BLUE COURT + GREEN SURROUND'; bottom image: saturated medium cobalt-blue acrylic playing area close to reference r2, quieter muted green/teal runoff, same exact white lines. Keep all scene colors outside playing court and runoff identical in both. Both alternatives must look equally finished, with identical surface grain and shine; this is a color choice, not an upgrade comparison. Keep palm trees, island backdrop, sea, cream paving, clouds and red-shirted player identical.
```

### 03_color_grading

Inputs: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/style/refs/r2.png`

```text
Use case: stylized-concept. Asset type: visual decision reference board, illustrative AI mockup, not a Unity capture or performance proof. Modern polished stylized sports game, soft plastic forms with rich but readable materials, classic Nintendo sports charm. Create a carefully aligned A/B comparison with two equal landscape images STACKED VERTICALLY, ample pixel resolution, thin neutral separators and simple readable labels on a clean dark header for each. Same scene, same framing, camera, geometry, props, hero identity/pose/outfit, sunlight direction and object placement within both variants. Do not redesign characters or add props. Copy the supplied reference closely. Each panel should retain the full wide camera composition rather than crop the foreground hero. Small footer exact text: 'CONCEPT COMPARISON - NOT A GAME CAPTURE'. Input image 1 is the scene to repeat, unchanged layout. Decision 3, compare the aesthetic of tone mapping. Top label '3A - NEUTRAL STYLE'; top image: clean, open shadows, direct vivid blue/green material colors, gentler overall contrast, bright pale clouds. Bottom label '3B - ACES STYLE'; bottom image: same scene and average exposure with a subtly more filmic contrast curve, somewhat deeper shadows and softer highlight rolloff; retain detail in cloud tops and keep true blue court blue. The difference must be subtle, plausible, perceptible and fair, not a heavy filter, NOT orange-and-teal grading, no black crush, no change of time of day. These are artistic approximations of tone mapping aesthetics; add clear subtitle below main title: 'ILLUSTRATIVE GRADING - EXACT RESULT NEEDS UNITY A/B'. Do not invent shader graphs or technical diagrams. All other aspects, sharpness, geometry and materials identical.
```

### 04_background_focus

Inputs: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/style/refs/r2.png`

```text
Use case: stylized-concept. Asset type: visual decision reference board, illustrative AI mockup, not a Unity capture or performance proof. Modern polished stylized sports game, soft plastic forms with rich but readable materials, classic Nintendo sports charm. Create a carefully aligned A/B comparison with two equal landscape images STACKED VERTICALLY, ample pixel resolution, thin neutral separators and simple readable labels on a clean dark header for each. Same scene, same framing, camera, geometry, props, hero identity/pose/outfit, sunlight direction and object placement within both variants. Do not redesign characters or add props. Copy the supplied reference closely. Each panel should retain the full wide camera composition rather than crop the foreground hero. Small footer exact text: 'CONCEPT COMPARISON - NOT A GAME CAPTURE'. Input image 1 is the full same close shoulder resort camera to duplicate. Decision 4, depth of field. Top label '4A - SHARP BACKGROUND'; entire image naturally sharp, including distant island and palm fronds as in reference. Bottom label '4B - SUBTLE FAR BLUR (HIGH ONLY)'; keep foreground player, all of the tennis court, net, tape, lines, ball and opponent EXACTLY AS SHARP and readable as top. Apply gentle Gaussian-like far-background blur ONLY beyond the far boundary wall: distant islands, far skyline and very distant decorative foliage softly defocused, while broad cloud shapes remain legible. Tiny controlled effect, no giant bokeh circles, no portrait mode outline artifacts, no motion blur, no vignette change, no camera change. Show full scenes not zoomed in. Add subtitle: 'COURT, NET AND BALL STAY SHARP'. Both stills represent same instant, same colors and identical exposure.
```

### 05_surface_detail

Inputs: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/style/refs/r2.png`, `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/style/refs/r3.png`, `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/style/refs/r4.png`

```text
Use case: stylized-concept. Asset type: material direction comparison board for a modern charming stylized iPhone sports game. Clearly labeled concept reference, not a render or performance promise. Produce a neat high resolution 4 ROW by 2 COLUMN comparison grid, one shared unobtrusive dark column header over each column. Left column exact label '5A - SIMPLE COLOR + SHEEN'. Right column exact label '5B - RESTRAINED MATERIAL DETAIL'. Footer 'CONCEPT COMPARISON - NOT A GAME CAPTURE'. Input1 r2 reference court colors/lighting; input2 r3 reference grass; input3 r4 supplies the ice and lava panels. Four subject rows, each uses an IDENTICAL camera framing, silhouette, palette and lighting across both columns: row1 'ACRYLIC COURT': close ground view across blue tennis court, white sideline and cream paving edge. Left smooth soft-plastic blue surface with broad sheen only, right quiet fine acrylic aggregate, subtle roughness breakup and shallow paving relief, no cracks or excessive dirt. Row2 'TURF + FOLIAGE': golf fairway edge with rounded leafy bush beside it. Left calm broad painted turf bands and simplified foliage volumes, right same colors plus short restrained near-camera grass blades and soft leaf detail, no noisy shag carpet. Row3 'ICE + SNOW': low close view of ice pool bordered by a rounded snowbank. Left simple cyan glassy ice and smooth snow, right same shapes with subtle translucent-looking depth gradient, delicate sparse cracks and very quiet glints. Row4 'LAVA + BASALT': close basalt shore of an orange lava channel. Left simple orange emissive ribbon and smooth dark rock shapes, right same shapes with slowly-flowing-looking heat bands, dark cooling crust, gentle basalt relief and subtle warm bounce. Do not make left column deliberately ugly, faceted, underlit or outdated. Both are attractive polished stylized directions. Right should show restrained modern surface identity not photorealism. No SSR imagery, real volumetrics, raytracing claims or FPS claims. These are visible appearance choices; six master material families or code architecture are not themselves visible. Avoid characters and game UI in these tight material crops.
```

### Background-focus correction

```text
Use case: precise-object-edit. Edit this existing two-panel comparison board. Preserve every word of all existing labels, both-panel layout, camera framing, court geometry, hero identity/outfits/poses, colors and lighting. TOP PANEL must remain unchanged. BOTTOM PANEL: fix the current excessive depth-of-field effect. Restore the distant opposing tennis player, their face/head/body and all the space from foreground to the FAR BASELINE to the same clarity as in top panel. The opponent is part of gameplay and must be sharp. Net and court lines sharp. Keep existing nearby palms and court-side furnishings sharp. Reduce current background blur by about half; the distant island and mountain ridge behind the far wall can be gently softly out of focus, not the whole far half of court. Preserve crisp opposing player silhouette even against soft island. There should be no portrait segmentation halos and no blurry crowd at the far wall. The point is subtle modern far-background separation while EVERY gameplay element remains clear. Make no other changes. This is a corrected illustrative concept board, not a Unity capture.
```

