# Phase 2 Needle patch prepared in scratch

Prepared 2026-10-05. **NOT APPLIED. Phase 2 has not been executed.** This plan changes only `blender/scripts/hole08_look.py` after the parent authorizes Phase 2 following the recorded Phase 1 gate. No source or installed asset changed during preparation.

The reference and the fresh Phase 0 aerial have been viewed as images. The target is tall continuous tapered rock needles, irregular layered island skirts, a readable supported stone arch, and a broader fall with a soft splash cloud. The frozen 343-yard geometry, 6m play height and fixed cameras prevent the reference's compact elevated-island composition.

## First patch

1. Replace `L.build_cliff_skin(D, style="strata")` with `L.build_postcard_cliff(D, style="needle", seed=8)`. This uses the final Phase 1 API: five uneven beds, overhang 0.7m, undercut 0.55m, relief <=2.6m, and 25m visual chunks around every original terrain top loop. It adds non-collision `ROCK_SKIN_*` meshes and leaves the scoring outline, walls and top vertices intact. Preserve the existing ground snapshot and exact comparison.

2. This shared call automatically places vines. Remove this one automatic batch immediately, then generate the hole's existing support-checked `vines_on_skin` batch on the new skirt with spacing 4.0m, skip 0.20. The specialized H8 placement maintains lowest cluster z>=3.1m and checks the whole hanging run against the wall. Reusing it avoids overlapping automatic and specialized batches. Keep the waterfall's 6m exclusion disk and `PL.attach_vines` afterwards. Existing outcrop and arch vines remain. This is a real vine skirt on the new relief, not unsupported plants hidden inside a wall. Save surviving vine count and root-gap maximum.

3. Replace each old multi-rock `place_sea_stack` cluster with `PL.build_needle`. Use the actual semantic name `ROCK_NEEDLE_XX`; do not rename it to escape any verifier. Generate final dimensions at scale 1. Return the current `place_stack` info fields, with the needle alone in `objs` and surf objects in a separate `surf` list. Preserve `_stack_ok`, height<=18m, dry-land/water-ellipse exclusions and >=25yd centerline clearance. On a rejected attempt, remove both the needle and its foam, then regenerate a smaller base with the same seeded method rather than scaling a finished mesh. Keep the old finite attempt limit and raise an error when no valid footprint exists.

   Initial scenery locations and metre heights are below; these are H8 look configuration only, not design edits. Initial base width is `min(5.6, height/3.15)` to retain a real needle while giving the PCA gate the widest legitimate starting body. The shared generator measures and limits the base in its lowest 10%; the final base ratio must be recorded rather than inferred.

| Seed | x yards | d yards | height m | initial maximum base m |
|---|---:|---:|---:|---:|
| 1 | -22 | 128 | 14.0 | 4.444 |
| 2 | 44 | 112 | 16.0 | 5.079 |
| 3 | -28 | 172 | 13.0 | 4.127 |
| 4 | 49 | 190 | 15.5 | 4.921 |
| 5 | -40 | 236 | 11.0 | 3.492 |
| 6 | 34 | 320 | 16.5 | 5.238 |
| 7 | -52 | 345 | 17.0 | 5.397 |
| 8 | 30 | 362 | 14.5 | 4.603 |
| 9 | 16 | 398 | 17.6 | 5.587 |

   Frozen-camera projection is a placement estimate, **not a visibility PASS**. Seeds 1–4 project into the tee at >4% height above z6; seeds 6–9 project into the approach at >=5% height above z6. Actual silhouette masks and occlusion must prove two readable needles in each view. Preserve `NEEDLES_NOT_BEHIND_TARGETS` and the arch-opening visibility check. The higher central positions can be adjusted only as scenery if these checks fail.

4. H8 `crown_tufts` must select `ROCK_NEEDLE` too. Because `PL.tuftify_crowns` currently filters only legacy prefixes internally, call its underlying `PL.tuftify_shrubs` with exactly the crown defaults: `per=CROWN_TUFTS_PER`, kinds B/T/F, seed8, the existing four-times candidate budget, `height_range=CROWN_TUFT_H`, `top_only_m=CROWN_M`. This is H8-only recognition of the new semantic mesh. Keep the existing up-facing support pruning and >=40 surviving crown-tuft gate unchanged. If the shallow crowns cannot support 40, report that FAIL before changing legitimate plant placement or crown geometry.

5. Strengthen the existing support-checked masonry arch modestly: `ARCH_SCALE=1.30`, `ARCH_MOVE_X_YD=-4.0`, `OUTCROP_R_M=8.3`, and explicitly pass `depth_m=1.9` to `PL.build_masonry_arch`. The top remains capped at 17.4m by the existing height calculation. The shared arch already has bevelled masonry, varying courses, radial voussoirs, haunches and a fallen course. Keep its topology, 16-yaw outcrop search, whole-foot support test, supported fallen blocks, plant checks, fold smoothing and address-camera play visibility. No support threshold changes. If the larger footprint cannot fit, preserve the valid span and increase depth alone; explain that measured cap rather than accepting unsupported masonry.

6. Widen the waterfall top from 4.2 to 4.8m; reduce widen from 1.5 to 1.35 so the bottom stays 6.48m, within the unchanged 8m plan-extent cap. Keep the current ballistic reach search and reject every intersecting vertex. Increase the sheet sampling to 10 columns/16 rows only if needed for silhouette continuity. Use a 4.0m-radius foam footprint initially. The entire LK_FALL connected sheet must remain <=60m2 and near vertical, with valid descending UVs and the same shore contact gate.

7. Add two small crossed soft spray cards at the fall foot, each 3.0m wide and 1.5m high, bases z0.10, using LK_SURF and `WATER_FALL_MIST_XX`. Give the cards a genuine feathered vertex-alpha profile (zero rim, approximately 0.35 peak); colour R is a fixed phase, G/B zero. Map their vertical UVs at the Surf 8m physical density and v descending with z. Do not let `assign_uvs` remap them to degenerate horizontal UVs. Keep their plan bounds inside the existing 4m base-surf patch. These cards remain counted by whitewater rules; no renamed smoke or low-opacity blanket around the coast. Measure NO_FOAM_STRIP and waterfall UV correlation on the actual blend and imported FBX. If the surf texture reads as hard crossed planes, revise the local geometry/alpha or report mist FAIL; do not call an unseen card a success.

## Measured checks before any acceptance

The old staged H8 has 231,432 triangles with 18,568 below the unchanged 250,000 verifier cap. New individual needles are approximately 451 triangles each and replace the old multi-piece clusters. The new cliff adds real geometry; extra vines and mist consume the saved margin. This is an estimate, not a budget PASS. Keep all face caps and plant sharing intact. If over budget, first remove duplicate vine batches and old redundant stack rocks; next cheapen far filler tufts through the existing method. Do not lower required fringe counts/coverage, support rules or texture detail thresholds.

For every new needle, record actual final height, lowest-10%-section maximum base width, height/base, width90/width10, flat-cap share, scale singular values, and the unchanged verifier's PCA `r3`. The legacy signature contains only BUILDERS, so a new needle may fall under the unknown closed-rock PCA rule: `r3>=0.15`. Scale1 alone does not prove that rule. If it fails, H8-only real geometry correction may widen the continuous middle body while retaining a narrow crown and height/base>=3.0; do not edit a verifier or disguise the mesh. Record the pre-correction and post-correction values. The candidate body must still look like one tall eroded needle, not a bulbous set of stacked tiers.

After the authorized patch: rebuild into `v3/hole08/stage/`, save local look gates, run the unchanged verifier against both staged blend and FBX, then run the independent exact scoring audit with `POSTCARD_SCORING_STAGE_ROOT=work/postcard-look/v3`, `POSTCARD_SCORING_HOLES=8`, `POSTCARD_SCORING_OUTPUT_STEM=scoring_exact_p2`. The audit must return 0.000m for all protected vertices and markers in both formats. Preserve the 14 protected meshes/9 markers exact set and topology. Save the actual aerial next to the reference; save tee/approach/arch masks and counts. No install happens during P2 preparation.

## Phase 0 difference disposition to re-score from fresh images

| P0 rank | Planned resolution / remaining constraint |
|---|---|
| 1 Dark mow bands | Phase 1 shared texture repair; measure actual MOW_BAND_CONTRAST on H8, do not infer from file edits. |
| 2 Low separated slabs | New irregular skirts/overhangs add island mass; scoring height, layout length and gaps remain frozen. Full reference silhouette remains different. |
| 3 Boardlike cliff bands | Five uneven eroded beds and short irregular relief blocks replace the old skin. Measure longest straight outline run and inspect actual aerial. |
| 4 Tiny arch | Width/depth increase while support and 18m cap remain; global course length prevents reference-relative scale. Save actual pixel height. |
| 5 Bulbous stacks | Replace clusters with nine single continuous eroded needles and shallow crowns; actual aspect/taper/PCA checks required. |
| 6 Thin fall | Broader top, bounded base, soft local mist; frozen 6m island makes it shorter than reference. |
| 7 Sparse vines | More support-checked vines on new skirts; their lowest cluster >=3.1m limits curtain depth. Inspect at proof resolution. |
| 8 Ocean ovals/surf | Phase 1 water/Surf repairs plus three broken patches per needle; strict foam length/gap/cov caps retain sparse shoreline surf. |
| 9 Regular path lane | Preserve exact flush path geometry and prior seam repairs; shared Path texture repair can change its visual broken-stone read. Cannot raise it into slabs under the ball. |
| 10 Warm flattening fog | Lighting/camera code frozen. Preserve atmosphere; report actual remaining fog/depth difference. |

Two conflicts remain explicit. Goal 2.2 requests UV scrolling, while unchanged SHADERS_STATIC forbids GolfSurf clock/texture offset. The H8 geometry patch keeps static sheets; UV scrolling is unimplemented and must be reported until an authorized coherent solution passes the original gates. Goal 5.1 requests >=15% sea in both fixed address frames: ideal unobstructed sea at z0 has only 3.752708% tee and 4.180417% approach; even z5.99 just below frozen ground yields 4.998333%/5.384306%. New scenery can only occlude this water. These are evidence-backed framing FAILs, not thresholds to relax or grass to hide under fake sea.
