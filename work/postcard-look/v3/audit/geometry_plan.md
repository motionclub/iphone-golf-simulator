# Scenery geometry plan after full source read

References and all three fresh installed Unity aerials were viewed. These are implementation candidates for the parent to execute in phase order, not completed gates.

## Phase 2 Needle

The frozen pads are separated by large water hazards, and their top heights are 6 m. Preserve every protected vertex and polygon. Improve island mass by extending open, stratified cladding below the existing side walls, varying inset/outset shelf depth and overhangs. Keep cladding out of scoring ground and preserve the old skin exposure and shape tests. Thick stacks should have a single continuous tapered mass with a low, small cap; use multiple distinct silhouettes at identity instance scale instead of stacked bulbs. Expand and regroup arch masonry outside the scoring footprint, retaining visible support and hanging vines. Waterfall footprint and broken foam can become broader and more irregular inside existing <=60 m² fall / <=8 m extent limits. Preserve surf's <=25% shoreline coverage, <=10 m white run and >=8 m gap limits. Change texture/UV path paving to broken slabs; terrain heights and path overlay's <=1.2 cm cap remain fixed.

## Phase 3 Split

The flat ridge must gain genuine elevated scenery geometry. Use grounded DRESS ridge outcrops with tilted scrub faces and irregular rock crests, leaving the safe route and all fairway/green/tee/bunker volumes clear. Current 2 m hummocks cannot approximate the reference's mountainous mass; place several larger ridge-scale crags whose bases intersect the frozen ground and whose tops remain nonplay scenery. Flat grass-coloured nonplay faces are capped at <10 m² per object and <20 m² total by the unchanged ONE_GREEN gate, so steep scrub slopes and rock tops are necessary. Shore sides need eroded open-shell relief and dark wet bases, not a smooth retaining wall. Cover >=80% outline through real cliff faces while leaving the frozen channel intact. Broken coves can be implied by side cladding below ground; do not cover or move the water-hazard boundary. Ruin needs larger aggregate silhouette and varied broken courses, but no unsupported pieces. Masonry is separately measured by connected stone components (<=20% unbroken cuboids). Bunker rims can receive thin rough material/UV and nearby dry plants, not shape edits.

## Phase 4 Crater

Replace full-height fence appearance with short, repeated but varied basalt tiers and cracks distributed over multiple angled facets. Visible columns must have actual 0.6–1.8 m diameter, independently measured after transform. Retain exact scoring sides and cladding exposure <=1% / connected exposed patch <=12 m². Pillar sides can gain deep scenery cladding below the frozen top; no grass top can move. Tee support should be a grounded basalt skirt/column body below the frozen square, not a flat narrow ribbon that fails rock-shape/stretch gates. Move or resize decorative cone/smoke only enough to show the summit from frozen cameras; retain plume readability >=1.5% in all required shots and soft-alpha borders. UV scale can reduce repeated lava worms without changing lava hue/structure thresholds.

## Performance and invariance

The imported FBX renderer count is large, but generic mesh merging is unsafe: plants require >=80% shared mesh instances, root-local sway colours, <=500 faces per plant (<120 tufts); rocks also <=500 faces. Static batching already exists in runtime and needs measurement. Legitimate simplification can reduce leaf faces, reduce distant repeated plant instances while retaining the same local visible density, coalesce open cladding sections, and share rock shapes. Do not rename closed rocks as cladding or merge distant plant islands to evade checks. The <=250k triangle gate remains stricter than the requested 300k, and is retained.

Exact proof now covers all six blends and all six FBXs with maximum delta 0 m, exact names/types/markers and canonical spatial triangle multiplicity. Re-run scoring_exact.py on staged final outputs before installation.

## Frozen-camera water ceiling

At original water z=0 m, infinite water with all removable scenery absent can occupy at most 3.75%, 4.18%, 1.29%, 3.36%, 2.26%, 15.68% of the six address frames. Even raising this ideal infinite plane to z=5.99 m (1 cm under the frozen lowest terrain) only reaches 5.00%, 5.38%, 1.86%, 6.17%, 2.30%, 17.75%. The first five address shots cannot reach >=15% water/lava while retaining these cameras and opaque scoring geometry. A raised lava plane would also violate unchanged CRATER_LAVA z<=3 m. This must be an honest framing FAIL, not water drawn over scoring land or a changed camera. See frozen_water_ceiling*.json/txt for exact 900x1600 pixel ray measurements.
