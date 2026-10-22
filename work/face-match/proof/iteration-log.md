# Comparison decisions

All listed stages are saved under work/face-match. Each stage has six unretouched source comparison sheets and source capture logs. The tested code is snapshotted alongside each set; the complete per-run source hashes are under work/full-visual-overhaul.

- before: untouched runtime baseline, both prohibited flags unset.
- 01-head: retain broader male cranial/jaw contour.
- 02-eyes: reject pinched centreline; 02b/02c retain continuous orbital correction and fixed camera registration.
- 03-brows: retain less bulky female brows and darker brown hue.
- 04-nose: reject worried brow/bridge distortion.
- 05-mouth: retain wider male mouth.
- 06-skin through 11-lip-form: retain continuous lip contour, smaller-radius lip normals, restrained lip volume and softer area-weighted face normals; the intermediate variants show why hard masks and sharp normals were discarded.
- 12-eyelid: reject detached projected eyeliner arcs.
- 13-eye-shading / 14-tone-lip-softness: retain eye gradient, warmer face response and female tonal adjustment. Motion proof exposed closed-lid normal artifacts.
- 15-blink-normals through 17-closure: retain production normal correction, bounded differential normal transport, and neutral still expressions. Not a clean visual blink PASS.
- 18-lid-boundary: retain pigment registered to the actual skinned eye-hole boundary. It follows lid motion; upper-lid shape remains different from the targets.
- 19-nose: retain lifted/widened female nose and reduced under-nose darkness. The added artificial nostril spots were subsequently removed after final review because they detached visually from the nasal form.
- 20-geometric-normals: reject full geometric normals/smaller filter; worsened cheek ridges and closed-lid shading. Restore 12 mm area filter with 45 degree cap.
- 21-smile: retain slightly higher female mouth with lifted corners.
- 22-eye-width: retain wider male apertures, nearer the measured reference width.
- 23-pigment-closure: retain darker irises and more visible male stubble; deeper eye recession did not remove every corner artifact. Final stubble mask was restricted above the neck.
- 24-review: retain as audit of the rejected nostril-pigment spots. No generated or retouched proof pixels.
- pass1-after (formerly after): first candidate, no painted nostril spots; both debug flags unset; all angles and 90 frames per hero captured again.

These are local improvements over the baseline, not a declaration that the reference quality was reached. The nasal geometry, eyelid silhouettes, thin closed-lid artifacts and lighting mismatch remain visible. Native SceneKit locker rendering has not been updated or verified in this pass.

## Continuation requested by Adnan

- 25-cheekbones: retain broad, small malar support below the outer eyes. Eye/brow anchors are unchanged.
- 26-male-ears: reject; although more of the auricle was visible, a negative local Jacobian exposed a fold at the attachment.
- 26b-ear-attachment: retain wider/gentler deformation support. Minimum male Jacobian 0.505, no vertices below the head changed; existing inner ear structure reads more clearly.
- 27-nose-relief: reject the sharper tip/nostril relief. Retain only the smaller ear-normal filter that makes existing cartilage readable.
- 28-nose-planes: rounded male nasal planes are closer; female blend is too strong.
- 28b-nose-transition: restrict the deformation above the mouth and lower the female blend, retained after rendered comparison; keeps the original lip surface and more female nasal volume.
- 29-skin-diffusion: warmer shadow response improves sampled cheek colors but brightens lips/lit planes too much.
- 29b-skin-contrast: retain transmission mainly on shaded planes, with lip protection and preserved lit-plane response.
- 30-male-complexion: retain corrected stubble placement above the upper lip and along the lower cheeks. The previous upper-lip region was registered too low.
- 31-nasal-cavities: retain small male cavity pigment at the revised nasal base; reject the female pigment trial, which looked detached.
- after (continuation): all six current sheets plus both 90-frame motion sequences re-rendered with both prohibited flags UNSET.

## Ears-only continuation

- ear-before: preserved the preceding accepted candidate's six sheets, raw stills, source snapshots and clips before ear edits.
- 32-ear-position: male auricle turns forward 28 degrees with lowered placement; female 25-degree trial exposes the bowl but makes the upper contour too wide.
- 33-ear-bowl: reduce female angle to 20 degrees and recess its nearly planar inner surface; retain the clearer bowl, then refine its fold.
- 34-ear-folds: retain a shallower cartilage ridge/tragus around the female recess and tighter local normal filtering for both auricles. Topology, weights and bind poses remain identical.
- 35-ear-contour: retain the rounded female upper outline and registered warmth. Reject the widened female lobe, which reads too flat at its bottom. Male front silhouette needs more upper roundness and less central width.
- 36-ear-normal-continuity: reject the raised normal-angle cap because it does not clearly repair the jagged attachment crease. Both heroes rendered with no compile/shader errors, but Unity stalled during shutdown; the owned trial process was terminated with SIGTERM. This rejected trial is not used as successful final validation.
- 37-ear-shape-review: both three-second clips and all six views render successfully. Retain the female tapered lobe; reject the additional male outline shaping/lowering because the measured outer contour is worse than the earlier 33/34 candidate. Restore the male 28-degree orientation and 10 mm weighted lowering from that closer trial.
- after (ears): final six views and both 90-frame clips re-rendered successfully, exit 0 and no C# or shader errors. The sampled image-left outer contour error falls from 4.37 to 3.78 sheet pixels for male and 8.27 to 4.33 for female; this limited contour check does not certify inner anatomy or overall fidelity. Both flags are unset. Mesh topology/weights/bind poses are unchanged, with positive local Jacobians and zero below-head vertex edits. The source hashes in the final capture match the actual staged index.
