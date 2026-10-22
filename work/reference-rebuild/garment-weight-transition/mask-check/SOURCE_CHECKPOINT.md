# Tennis polo coverage checkpoint

The original polo is topologically continuous at the failing sleeve/axilla. Physical-welded triangle audit (10 micrometre rest-position weld) finds zero female boundaries and no male axilla/sleeve boundary. The male has 45 small boundary edges confined to waist height .948–.962 m. No triangle degeneracy occurs in the six Serve/Forehand samples per character. See original-top-boundary-audit.json.

The current outfit-specific render mask removes 6,284 male / 2,892 female Body faces. Editable base Body, vertex positions, weights, bindposes and all original garment geometry remain intact. Face mapping to both default-source and current-matrix-canonical Body was verified from physical triangle coordinates, not vertex counts; all requested faces matched at 10 micrometre coordinate precision.

runtime-profiles/Tennis_{Male,Female}.json uses garmentVertexCount 15401/13932, expectedRemovedFaceCount 6284/2892 and removedTriangleRootPositions (nine hero-root-metre coordinates per triangle). manifest.json records the exact file hashes. These are optional runtime test inputs, not visually accepted production masks.

The first mask comparison deliberately simulated CullBack using Cycles Backfacing transparency. It introduces small black source-render artifacts that did not appear in previous opaque smooth source plates; it is not an actual Unity shader result. In opaque source shading, the same original mask removes most of the large male Serve strip. Root actual two-sided-only test does not remove the strip, because the intersecting Body is still rendered. The next actual gate is paired mask-only versus mask plus correctly faced two-sided cloth. The expanded2 source branch lowered the axilla height guard but changed zero mask faces; it is preserved as evidence, not presented as a new repair.

The independent 330-pose/four-view binary raster records changes to the Body+Top union silhouette. Such losses include desirable removal of skin bulges beyond the cloth silhouette; union loss alone does not prove a backdrop hole or severed arm. Evaluate material-aware visual continuity of arms, neck, cuffs and shirt silhouette in real game captures. No whole-body silhouette equality is required for a clothing mask.

The sewn-panel branch is preserved separately under ../sewn-panel. It improves raised-arm coverage but introduces authored seam/overlap concerns and has not been accepted or installed. Do not combine its topology with the original mask runtime profile without rebuilding all correspondence and garment checks.
