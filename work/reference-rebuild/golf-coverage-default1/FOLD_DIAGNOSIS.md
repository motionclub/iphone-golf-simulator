# Remaining golf axilla fold — source diagnosis

This is a real folded/inverted skinning surface, with shading making it conspicuous. It is not just shirt color or material contrast.

Female Driver top actual image, near pixels (395,455), (400,459), (410,465): source camera reconstructed from the baked Body bounds and the capture harness's 34 degree lens / (2.5,.3,3.8) offset. Rays hit main-shirt faces 4399, 4400 and 3521 plus small detached faces 7033/7034/7005. Their canonical region is left side torso x about -0.131..-0.123m, y 1.15..1.21m, z 0..0.04m. See `female-driver-fold-rays.json` and `diagnose_fold.py` for the numerical evidence.

The main-shirt faces belong to the same 7,409-triangle connected surface, so deleting tiny detached fragments cannot remove their underlying fold. Their average skin weights combine about 36–47% LeftUpperArm with 47–52% Chest and 5–12% Spine. Their rest geometric-vs-shading-normal dot products are healthy (+.79 to +.97); at the swing, they turn opposite (-.70 to -.89 with uncorrected LBS normals). At these three face centroids, raw LBS and actual posed positions agree to within 1 micrometre: existing morphs are effectively not correcting this local fold.

Backface rendering fills the coverage hole but does not unfold these triangles. Merely recoloring fabric, flipping culling or smoothing shading will not reliably cure the torn-looking shape.

Small next deliverable: one localized golf corrective candidate on the existing Top and existing topology, constrained to the measured left side field, using the Driver top as a pilot. Unfold the main connected surface with a smooth boundary-fixed posed-space fairing; invert the existing skinning matrices into a single additive source anchor. Keep all outside positions/weights exact and preserve the cuff/placket/hem. A strict small displacement budget (e.g. <=12mm source; reject instead of expanding if insufficient), zero new reversals and zero new silhouette gaps should gate the source candidate before root's actual Unity capture. The same patch then needs all five golf club families sampled; do not promote based on the pilot alone.

This is a proposed bounded corrective, not an authored or accepted asset. No runtime or source Assets have been changed by this diagnosis. Rejected fragment pruning is not proposed again.
