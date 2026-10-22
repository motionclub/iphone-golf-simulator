# Local female forehead repair

Source defect confirmed. The ellipse cap had a smooth mathematical blend but created a shallow forward bulge in front depth. At central forehead heights1.610–1.615m, measured curvature changed sign; at1.620m the surface slope fell to0.01 instead of the original0.15. The authored normal differed from the resulting geometric profile by up to9.7degrees. The runtime continuous-normal helper exposed this bulge; it did not create a discrete seam.

READY work-only candidate: Female_OriginalFaceFinish30Forehead.blend / .fbx, with hashes in STAGED_EXPORT.json. Starts from final Ears source, without the separate eyelid operation. repair.py reproduces it using broad.npz (original pre-cap positions). The repair restores the smooth original front-depth profile locally while retaining the exact rounded cap X/Z silhouette. Derivative-matched forehead normals are recomputed. Depth movement max2.367mm; X/Z change0; topology/weights/rig/UV/colors unchanged; all shape states receive the same positional delta. Active eyelid positions remain exactly unchanged, active eyelid normals equal to float precision (max3.4e-16 vector difference), no eyelid shapes changed.

Postrepair profile has positive curvature throughout the former band, and normal error is around1.3degrees there. profiles.json stores original broad / current ears / repaired measurements. Matched diagnostic satin CPU previews forehead_before.png and forehead_after.png were reviewed: smooth local transition and preserved rounded outline; no new visible source defect. Actual map render is still required before promotion.

Composition: apply the READY female eyelid operation to this candidate using face-finish30-lids/apply-lids.py exactly as for composed-ears. Its originalprefix contract remains valid (Female22891 prefix, totalBody34366). Male source remains the accepted Ears source unchanged. Runtime coherent blink-normal fix remains root-owned and required independently of this forehead correction.

No production writes or GPU use by this lane.
