# Female shoulder, hands, skirt and stroke continuation

User scope: continue female shoulder/hand deformation, skirt clipping, backhand and serve poses. Stage only; no commits. Existing identity, garment colors, map, light rigs and gameplay cameras remain fixed.

## Retained changes

- Diffuse shoulder/axilla skin weights along existing topology. Transfer inappropriate chest-panel arm influence to the ribcage. Preserve neutral vertices, normals, UVs, topology and bind matrices exactly.
- Add bounded shoulder-fold pose shapes that partially release at overhead reach. Bind the sleeveless female tennis tank to the torso; fit its raised-shoulder correction to evaluated body geometry. Replace obsolete garment pose corrections only; retain unrelated blend shapes and weights.
- Limit wave wrist flexion to 55 degrees and share palm-facing roll with the forearm. Update arm support transforms after grip polish.
- Strengthen elbow clearance and forward elbow preference. Give grips bounded travel away from contact, include fingers in free-grip clearance, and shift the pelvis under low two-handed strokes while retaining wrist and foot anchors. Tennis contact remains locked.
- Allow the free serve/toss hand to clear the torso while keeping the racket contact fixed. Existing serve wrist cock remains active.

## Skirt decision

The runtime skirt candidates are REJECTED and removed from Assets. They are preserved as noncompiled experiments with topology profiles and geometric audits. The last candidate still distorted the upper skirt in pushups and failed 8 of 84 sampled full-body triangle audits. No claim of collision-proof cloth is justified. The active game keeps the authored skirt mesh and binding; the retained arm/finger clearance also includes a female tennis skirt envelope.

Tests and passing shoulder pictures cannot certify the skirt. The repo rule, “Stop for Adnan when identity/silhouette drifts,” prevents accepting ballooned or folded-through fabric as a finished fix. Skirt repair needs a coherent garment construction/attachment solution before re-enabling a runtime surface solver.

## Proof and reproduction

`proof/GATE_RESULTS.md` is the acceptance record. Captures use the actual Tennis/Golf scenes in an isolated APFS clone, Unity 6000.3.24f1. Tennis emotes run through the live driver; backhand/serve film segments sample source poses continuously through the same post-processing. Those stroke pictures are pose proof, not ball-rally proof; gameplay contact is checked separately by tests.

`tools/deformation_mesh.py` validates dump length before reading. `tools/check_cloth.py` checks full body triangles against the outer skirt; crossing lengths are intersection-segment lengths, not penetration depth. It verifies reference rest positions and garment metadata topology. `tools/build_skirt_profile.py` reconstructs experiment profiles from existing Clothing V2 NPZ assets.

`proof/shoulder-fit-inputs.zip` contains the evaluated body/top inputs for `tools/fit_tank.py`; unzip to a temporary directory and run Blender in background with the tool and the directory/output paths after `--`. The generated ShoulderCloth bytes contain only two garment pose deltas; they do not replace body or garment rest geometry.

The overhead serve requires additional fitting. Fully compressing the axilla produced collapsed surface artifacts; fully releasing it exposed the source web. The retained bounded compromise is not a full overhead-shoulder visual PASS. A trial coverage-mask change did not solve the issue and was reverted.
