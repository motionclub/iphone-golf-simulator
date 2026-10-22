# Clothing beautification — active scope

Finish one garment at a time against the clothing references. Begin with the male polo, show an actual passing game render in chat, then continue without stopping for confirmation. Clothing colors are fully customizable; reference hues are never an acceptance requirement.

This pass covers garment geometry, silhouette, fit, collar/cuff/hem construction, seams, fabric materials, garment skin weights and garment-only deformation corrections. Preserve body, head, face, hair, skin materials, body weights, rig, animation sources, lights, cameras and maps. Existing scenes are fixed evaluation environments.

The earlier character-wide audit below is retained as context. Face, arms/hands, skin, character presentation and environment recommendations are deferred and are not authorized work for this clothes-only pass.

## Active garment order

1. Male tennis polo: collar, placket, shoulder and sleeve connection, cuffs, chest/waist drape, fabric and motion fit.
2. Female tennis polo: reference fit and stable sleeve/underarm construction.
3. Male tennis shorts: waistband, leg opening, hems, side seams and clean drape.
4. Female tennis skirt: waistband, pleats, flare, hem and motion coverage.
5. Golf garments one at a time: first polo, then trousers, then skirt.
6. Shoes and socks: uppers, laces, panels, soles, ribbing and garment-to-garment clearance.
7. Clothing consistency: light/dark/saturated customization, full/distance meshes, native export and actual clothing appearance in existing scenes.

A stage passes only after fit and construction match the reference intent, clothing remains clean in motion, and the accepted result is verified in the normal runtime and native path. Do not advance with holes, protruding repair panels, swollen folds or unvalidated opt-in assets.

Current status: male polo in progress. Folded collar, placket and buttons are improved; sleeve deformation still fails the motion gate. No garment has been declared complete or promoted.

## What is holding back the characters

| Finding | Evidence and implication |
|---|---|
| Clothing has a shape and deformation problem before a texture problem | Current polo collars stand away from the neck; shoulders and cuffs appear thick; shorts and skirts show broad dark dents and lose the reference's tailored folds. The female stroke capture exposes skin through the underarm. More weave cannot repair these shapes. |
| The existing garment repair has reached a structural limit | The clothing handoff identifies stretched source faces, incorrect cuff bone bindings and connector faces that fold back against their neighbors. Closing a skin strip still leaves a protruding triangular fold. Repair the garment construction and binding before adding another push-out layer. |
| Face form and feature integration remain unfinished | Latest court close-ups have smoother heads but thin or irregular lid edges, exposed eye shapes, weak mouth definition and uneven transitions around sockets and nose. The reference has integrated lids, shaped cheeks and chin, and a relaxed smile. These are visible differences; their exact remaining causes require component isolation. |
| Material polish is inconsistent between review and normal launch | Current Unity and native code activate stronger skin polish only when `VISUAL_CHARACTER_SKIN_POLISH=1`; the Oct 8 golf recording queue sets that flag. A strong review image therefore does not establish normal-launch appearance. The imported skin color conversion is already repaired in current Unity code and should be preserved. |
| Arms and hands have actual deformation defects | Prior wrist review still fails the doubled-wrist contour. The held structural diagnosis points to weight transfer around a shared pivot. Female finger analysis documents palm influence persisting at a finger joint and an edge stretching from 8.05 to 30.85 mm. These findings support targeted deformation work, not more skin gloss. |
| Character presentation is weaker than the map references | The latest golf capture gives the character less frame presence than the portrait reference. Court faces still have a pronounced dark side and limited soft highlight structure. Accepted camera-side fill improves brightness, but has not delivered the reference's full form and separation. Camera size, light, background contrast and pose need a controlled pass. |
| Progress is fragmented across components and render paths | The previous work board spread effort across faces, garment repair, venues, grass, motion and menus. Its gates explicitly retain visual failures. The progress gallery mixes newer face candidates, older map captures and a separate native revision. This makes the combined default character hard to assess. |

The process problem is that bounded fixes keep advancing while the whole component remains visually unfinished. Compilation, mathematical correctness, a closed hole, or a brighter face can pass independently while the result still misses the target. Completion must be tied to the visible reference features and to the actual launch path.

See [the visual comparison](/Users/adnanyonathan/Documents/Codex/2026-10-08/open/outputs/character-beautification/comparison.md), [clothing handoff](/Users/adnanyonathan/Documents/Codex/2026-10-08/open/outputs/character-beautification/evidence/clothing-handoff.md), [garment order gate](/Users/adnanyonathan/Documents/Codex/2026-10-08/open/outputs/character-beautification/evidence/clothing-order-gate.md), [material review](/Users/adnanyonathan/Documents/Codex/2026-10-08/open/outputs/character-beautification/evidence/material-review.md), [wrist review](/Users/adnanyonathan/Documents/Codex/2026-10-08/open/outputs/character-beautification/evidence/wrist-review.md), [finger diagnosis](/Users/adnanyonathan/Documents/Codex/2026-10-08/open/outputs/character-beautification/evidence/finger-diagnosis.md), and [capture provenance](/Users/adnanyonathan/Documents/Codex/2026-10-08/open/outputs/character-beautification/evidence/capture-provenance.json). Historical reports support their bounded findings; they do not establish the state of every current asset.

## Clothing customization

Clothing color is fully customizable. Reference colors identify garments only and are not acceptance requirements. Preserve the existing picker, saved colors, tint and trim roles. Author color-neutral fabric detail and validate every finished garment in white, charcoal and saturated colors so folds and seams remain readable. Never bake a reference hue into garment textures or geometry.

## Working rules

1. Keep one component active. Finish its geometry, deformation and material in that order. Within the component, change one cause per comparison.
2. Lock the rest of the character, camera and lighting during a comparison. Keep an accepted baseline and one candidate, with mesh, material, flag, rig and camera records.
3. Test a tiny diagnostic first. Expand to motion and other views only after the main visible defect improves. If two controlled candidates do not improve it, revisit the structural diagnosis rather than repeat the same parameter adjustment.
4. Review the actual imported asset in Unity. Source renders explain defects; they do not close the game appearance gate.
5. Require both reference fidelity and motion integrity. Closing an underarm gap with an ugly fold fails. Stronger highlights on a lumpy face fail.
6. Promote accepted work to the normal launch path and verify its native equivalent before marking the component complete. An opt-in experiment remains an experiment.
7. Freeze the accepted component, record its remaining limitations, and move to the next. Later changes must retain its comparison views.

Your current request explicitly includes clothing and character presentation. It supersedes the older repository instruction deferring clothes. Preserve the locked character identities and body proportions. Rebuild garment regions where necessary; avoid replacing the whole character. The plan changes no production assets.

## Establish the baseline

Before implementation, capture the current default male and female in a neutral stage, the resort court and Cliffside hole 12. Capture the polished review configuration separately and label its flags. Use the same saved animation time and camera for before and after.

Record both close detail and a normal full-frame gameplay view at the intended phone aspect ratio. Preserve an unscaled display at the expected viewing size; enlargement is diagnostic only. Make dedicated reference-matching poses for comparisons, while keeping the normal gameplay cameras as separate acceptance views.

Create a small set of comparison views: neutral front, three-quarter and profile; outfit front and back; tennis ready and stroke; golf address and swing top; one real blink; and a short turn or motion clip. Record source and shader hashes and resolved runtime flags. Existing Oct 8 evidence is useful history, but it is not a freshly frozen baseline.

## Character only scope update

Adnan clarified on October 8 that this execution is character-only. Preserve maps, turf, world post-processing, world light rigs and gameplay cameras. Retain the observations about missing post, compensating lights, muted turf, wide framing and hero/world separation as context for later environment work. Existing maps are fixed test environments here. Character materials, mesh fit, deformation, face, and character-specific presentation remain in scope. The map stages below are deferred where they would change the environment or camera; assess the completed character in those maps without changing them.

## Sequential execution

| Stage | Sole focus | Work and completion condition |
|---|---|---|
| 1 | Male polo | Match collar roll and points, placket and buttons, shoulder seam, sleeve length and opening, chest ease and waist drape. Author broad intentional folds before fine fabric detail. The result must read as a tailored polo under fixed light, then remain clean through ready, wave, serve and forehand. |
| 2 | Female polo | Apply the construction standard to her reference fit. Rebuild the damaged cuff and underarm connection and correct binding. Complete ready, forehand and raised-arm coverage without skin strips, spikes, reversed folds or swollen sleeves. Native export must represent the accepted posed result. |
| 3 | Male shorts | Preserve readable leg openings, waistband, hem and side seam; replace dented shading and excessive deformation with deliberate cloth volume. Finish before starting the skirt. |
| 4 | Female tennis skirt | Match pleat spacing, flare, waistband and hem weight. Hold the silhouette during turns and strokes, retain coverage and remove dark triangular collapse. |
| 5 | Golf garments individually | Finish one golf polo first, then trousers, then the golf skirt. Keep the tennis garments frozen. Golf uses separate meshes and correctives; a tennis underarm repair cannot certify golf fit. Check address, swing top, impact and follow-through. |
| 6 | Shoes and socks | Finish a reference sneaker with rounded upper, readable panel separation, laces and sole; then its variants. Give socks soft ribbing and a clean cuff. Preserve ground contact and ankle clearance in motion. |
| 7 | Male face | First establish socket and eyelid fit, cheek, nose, chin and mouth form under neutral material. Preserve identity. Then tune warm satin skin, restrained lower-face pigment and glossy eyes. Finish relaxed expression, gaze, and blink at 0, 25, 50, 75 and 100 percent. |
| 8 | Female face | Finish her lid outline, eye seating, cheek and jaw transitions, nose, lips and gentle smile against her reference. Preserve her distinct proportions. Validate the same blink and gaze set, with no serrated creases or patchy shading. |
| 9 | Arms and hands | Repair elbow and forearm transitions first, wrist band second, then finger binding and grip. The contour must remain solid and continuous throughout tennis and golf motion. Preserve racket and club transforms and contact timing. Show consecutive frames, not a favorable still. |
| 10 | Character material and presentation consistency | Use the completed character to tune character-owned skin, cloth, eye and hair materials. Evaluate highlights, friendly facial readability and silhouette in the existing resort court. Preserve the environment, world lights, post-processing, background and gameplay camera. |
| 11 | Golf character verification | Evaluate the approved character on existing Cliffside views: face and arm readability, light/dark garments, contact at the feet and current camera transitions. Repair character defects only; record environmental limitations separately for later work. |
| 12 | Character consistency and performance | Verify the same accepted character in normal launch, locker, lobby, introductions and gameplay across existing venues. Complete full/distance mesh, animation, native export and device checks for the changed character assets. No venue changes. |

The first deliverable is one finished male polo, not a partial improvement across every outfit. For each garment, finish shape before motion, motion before fabric response, and fabric response before additional colors or variants. During face stages, finish open-eye form before blink, then surface response. World lighting, post-processing and gameplay-camera changes are deferred; character evaluations use their existing settings.

## First implementation brief

**Target:** the red polo in the male character sheet. **Active asset:** male tennis top only. **Fixed controls:** head, skin, body, shorts, rig, lighting, camera and environment.

1. Trace the actual runtime top back through `MatchHeroLook`, the fitted resource, sleeve shortening, tailoring, weights and pose correctives. Identify which changes alter the reference silhouette. Save the resolved mesh and pose before any edit.
2. Render front, three-quarter and side in a pose comparable to the character sheet. Evaluate collar stand-off, shoulder volume, cuff thickness, sleeve opening, placket and waist ease independently.
3. Isolate one defect with neutral material. Reauthor that garment region in the source when construction or binding is wrong. Preserve the accepted rig and body. Remove a redundant runtime adjustment only after the source fix reproduces its intended function.
4. Reimport and compare the exact views. When silhouette and drape pass, check the ready pose and short raised-arm sequence. Repair garment weights and pose corrections locally rather than changing the player's motion to hide the issue.
5. Tune cloth response: subtle fine weave, broad highlights, deliberate seam relief and controlled fold shadow. The collar and cuff must still read at gameplay size; the texture should not produce visible stripes or shimmer.
6. Carry the accepted top through the native exporter and normal launch. Deliver reference, baseline and candidate views; collar and cuff detail; a real motion clip; normal gameplay; and honest PASS or FAIL lines for fit, deformation, surface and adoption.

## How a stage passes

Every stage needs three visual comparisons: reference against a comparable game view, baseline against candidate with identical settings, and candidate at normal gameplay size. Include a short motion capture where the component deforms. Mark any remaining visible failure explicitly.

For clothes, the gate requires the reference construction and fit, clean silhouette, coherent folds, no visible holes or clipping, and stable material detail. For faces, require recognizable approved identity, integrated features, a friendly relaxed expression, clean blink and gaze, and soft highlights without exposing lumps. For arms, require continuous volume and natural joint transitions while preserving grips. For character evaluations on maps, assess readable form and color, grounding and silhouette under the unchanged environment; document environmental limitations without changing them.

Use geometry measurements to diagnose penetration, stretch and seam errors. Do not treat them as a score for beauty. Proposed acceptance views and stage gates must be established with the new baseline; no new visual PASS is claimed by this audit.

Maintain a per-stage record containing accepted asset hashes, resolved flags, reference views, motion proof and a rollback. Validate the real full/LOD switch and native appearance wherever applicable. Desktop appearance and physical iPhone performance are distinct checks; record the target phone budget before final device acceptance.

## Technical evidence to retain

The current stronger skin response is controlled in [HeroLightingProfile](/Users/adnanyonathan/Documents/Codex/2026-10-08/open/outputs/character-beautification/evidence/HeroLightingProfile.cs), [HeroLighting](/Users/adnanyonathan/Documents/Codex/2026-10-08/open/outputs/character-beautification/evidence/HeroLighting.hlsl) and [native surfaces](/Users/adnanyonathan/Documents/Codex/2026-10-08/open/outputs/character-beautification/evidence/MatchHeroSurfaces.swift). [Recording settings](/Users/adnanyonathan/Documents/Codex/2026-10-08/open/outputs/character-beautification/evidence/gameplay-capture-settings.json) enable it explicitly. These snapshots explain the default versus review discrepancy; enabling the flag alone does not finish skin quality.

[Garment tailoring](/Users/adnanyonathan/Documents/Codex/2026-10-08/open/outputs/character-beautification/evidence/HeroGarmentTailoring.cs) and [sleeve geometry](/Users/adnanyonathan/Documents/Codex/2026-10-08/open/outputs/character-beautification/evidence/HeroGarmentSleeveGeometry.cs) modify geometry while retaining much of the source topology and binding. Together with the failed connector evidence, this makes source construction and weight repair the next justified intervention. It does not prove every garment needs replacement.

The [wrist diagnosis](/Users/adnanyonathan/Documents/Codex/2026-10-08/open/outputs/character-beautification/evidence/wrist-diagnosis.md) proposes a structural candidate that has not been visually validated. The [finger diagnosis](/Users/adnanyonathan/Documents/Codex/2026-10-08/open/outputs/character-beautification/evidence/finger-diagnosis.md) likewise reports source improvement with residual regressions. Use these as starting hypotheses, not finished repairs. The [native gate](/Users/adnanyonathan/Documents/Codex/2026-10-08/open/outputs/character-beautification/evidence/native-adoption-gate.json) accepted a bounded earlier revision while explicitly retaining face, wrist and shirt limitations.

All supplied pictures are exact copies of existing captures or references. [The evidence manifest](/Users/adnanyonathan/Documents/Codex/2026-10-08/open/outputs/character-beautification/evidence/manifest.json) records their origins and hashes. This plan is based on image and source inspection; no new game build or fresh render was produced for it.
