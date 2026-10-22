# One bounded skin revision

Work only. Patch against the currently integrated skin-finish2 candidate. Apply both patches with git apply -p0; MatchHeroLook's existing opt-in hook remains unchanged.

- Preserve continuous linear lip/seam masks instead of saturating their upper range with smoothstep. Restrained lip tint: male (.99,.83,.80), female (.99,.76,.74); seam (.80,.67,.64), all relative to selected BaseColor and multiplied by the actual partial source weights.
- Moderate form contrast: SH ambient .82 (was .70), wrap .28 (was .20). Preserve candidate's quiet cheek pigment and shadow floor.
- Reduce broad specular peak .105 to .075; remove narrow .012 lobe, which picked out malformed surface details.

No anatomy, normals, skeleton, weights, source masks, blendshapes, vertex stage, texture/sampler/pass or other surface role change. Shader default remains opt-in 0. Generic control lighting is exact.

Run capture-skin-finish2-revision1.json: same source/camera/lighting as corrected finish2, exactly candidate1/control0. The original corrected control is also visually comparable; the duplicated job is for an exact postrevision control if desired. Adoption requires cleaner lip transitions, softer male mouth/socket planes, and readable warm skin without loss of form. The source lips and blink folds may still prevent the requested target polish.
