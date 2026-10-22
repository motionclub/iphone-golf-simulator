# Shirt diagnostic handoff — held at root request

Current opt-in candidate: **connect4, ART FAIL**. Default stays off. No further implementation or GPU queue requested. Root owns Assets/Unity; this lane changed only this work folder.

The broad pink underarm strips are closed in focused actual Full intro/Forehand .4/.8/contact captures, but the raised-arm silhouette retains a protruding triangular fold and Forehand has unnatural overlapping creases. No broad motion, LOD art, golf applicability, native-port, or ownership acceptance is claimed.

## Exact remaining geometry

`remaining-connect4-fold.json` maps actual intro pixels x545–581/y410–445 to actual baked face IDs, profile face IDs, vertices, normal angles and canonical origins.

- **Lining connector profile17762 / actual16434**, vertices7765,7510,14572: largest identified protruding fold region (124 pixels). Original torso boundary vertices7765/7510 connect to a Body-bound lining vertex; posed edge69.0mm. This is a new connector, not a missing original face.
- **Outer connector profile18845 / actual17517**, vertices10280,7641,15064: original boundary normal versus connector-face angles164°/157° at the two original vertices. This directly demonstrates that the retained boundary folds back against the new panel in this pose.
- **Copied Body outer profile18496/18498**, vertices15054/15117/15327 and15327/15117/15120: canonical Body faces15925/15926. Second edge reaches188.5mm. The corresponding actual panel positions match the prescribed Body surface within0.0006mm, so this is genuine stretched anatomical/connector geometry, not a runtime transform mismatch.
- Retained original shirt faces3698,804,803,3688/3697 are also visible in this tight region, with posed edges33–77mm. They have not been smoothed or replaced.

`region_female_*.png` label the earlier cuff2 actual geometry by retained source, copied Body shell/lining, connectors and mirrored cuff. `actual-ridge.json`, `actual-intro-ridge.json` are earlier detailed traces; current exact trace is the connect4 file above.

## Proven repairs and rejected paths

Original skin strip: continuous front-facing cloth fell13–30mm behind Body. Source faces stretched20–45mm edges into213–311mm sleeve-to-torso chords. DQ, full-Top DQ, and anchor ablations did not fix this. The coherent Body shoulder band closes the broad strip at about2ms, down from original121ms.

A distinct malformed left cuff used Chest/Spine/UpperLeg bindings beside94–96%UpperArm vertices; its edges reached267mm. The candidate replaces it from the intact right cuff with mirrored bone roles. Recorded cuff maximum edge is13.8mm in Forehand .4s and18.5mm or less in targeted poses.

My original new connector authoring incorrectly inferred shell/lining from perimeter: the damaged left inner sleeve loop was longer than the outer. Connect4 fixes pairing using authored-normal orientation;393Full/765LOD faces changed, with positions, bone bindings and Body bindings identical. All eight connection orientation cosines are positive>=.961. This removes the crossed sheet pairing but does not resolve the remaining pose-dependent fold listed above.

Normal-map-strength0 actual made little difference. Smooth Body shading-normal ablation had exact0.0m position parity but produced a worse dark streak: **rejected**. Use main helper, not `smooth-normal-ablation/`.

## Staged artifacts

- `HeroGarmentGusset.cs`, `HeroGarmentGussetLifetime.cs`
- `UnderarmGusset_Female_Full.json`:16748v/21858tri,2413 CPU vertices
- `UnderarmGusset_Female_LOD.json`:14268v/18564tri,2408 CPU vertices
- `connector4-sha256.json`, `connector-layer-repair.json`, `connector4-targeted.json`
- `ownership-exact-counts.patch`: updates gate expectations to this exact topology; does not relax gates. Not applied by this lane.
- `minimum-diagnostic-queue.json`: prepared at prior root request, **do not run while hold is active**. Full+LOD three-pose diagnostic, full ownership gate, separate golf Driver address/top.

Golf is **unaffected and separate**: `HeroGarmentPoseCorrectives` exits for golfKit; `HeroGolfer` loads Golf/Fitted_Female_Top (6935v/10115tri) and Male_Top (12920v/18683tri), using GolfGarmentCorrectives. Tennis source profiles cannot be reused. Existing current golf dumps are `proof/reference-rebuild/golf-wrist29-revision1-candidate/poses`.

Native export remains unsupported for this candidate until its posed-surface evaluator is mirrored. Exporting a mutable CPU rest-state snapshot as fixed LBS would be incorrect.
