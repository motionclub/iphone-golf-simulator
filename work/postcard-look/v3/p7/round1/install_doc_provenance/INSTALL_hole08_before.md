# H8 Needle Phase 2 staged candidate — 2026-10-05

Stage is frozen at build attempt 2, not installed. Builder 47/47PASS and raw unchanged verifier 100/100PASS. Exact scoring is 0m in both formats. Fresh aerial/renderer masks remain pending; LOOK_STILLS_TEXTURED is SKIPPED in the raw verifier and recorded as FAIL (unmeasured) in GATES_hole08.md. Goal 2.2 UV scroll remains unimplemented under unchanged SHADERS_STATIC.

## Final stage

```
4a87585f56b8e61497b2772d4c9bf6666c1509e6f080a1f860e3445988302433  work/postcard-look/v3/hole08/stage/hole_08.fbx.meta
c0e9e67c1b247c39ed7dcafd98458494f39e1f13bbfddf2c0b819ea74986779d  work/postcard-look/v3/hole08/stage/hole_08.blend
4c2034a345d85ae65a70b56a686255f4412304fd908211af35c1eb503175cf9c  work/postcard-look/v3/hole08/stage/hole_08.fbx
```

241,625 triangles,1,812 mesh objects,1,816 objects. Geometry fingerprint dd14f22eae75dc6a. The unchanged verifier cap is250,000; the Phase 6 cap is300,000. Actual tee drawCalls and SetPass calls are unmeasured and must be measured in Unity; mesh count is not a draw-call PASS.

Final source/lib sha list: lib_sha_final.txt. Look PNG sha list: look_png_sha_final.txt. These identify the actual frozen inputs at this last build; shared libs/PNGs were not edited in P2. P2 source changes are only hole08_build.py and hole08_look.py. Source gate predicates/constants in look_gates and postcard_look_verify.py are unchanged.

## Installation in Phase 6

The parent must point install_holes.py LIBLISTS at work/postcard-look/v3/hole08/lib_sha_final.txt, then use run_proof.sh pre/install. Install the staged hole_08.blend and hole_08.fbx only. Preserve the installed fbx.meta exactly; the generated staging meta must not be copied. No installation or Unity work was done by this agent in P2.

## Resulting scenery

Nine continuous eroded ROCK_NEEDLE meshes (scale1),height11–17.6m, actual height/base3.15–3.74; PCA r3.162–.193, taper width90/width10.20–.31. Semantic ROCK_NEEDLE handling is explicit in H8's crown placement:70 supported crown tufts. Twenty layered skirt chunks clad100% of shore at midheight; relief sd.81m;99 supported wall vines. Wider4.8m fall has6.48m foot and two feathered local spray cards inside the existing4m splash footprint. Actual waterfall verification41m2 near-vertical sheet and valid descending UVs; foam remains within unchanged caps.

Arch uses the previous9.144m clear span with stronger1.9m depth, on an8.3m supported rock; all12 foot vertices have support within0.04m. The attempted1.30 span had real clear windows but failed the unchanged arch test's pier framing window; exact scratch diagnosis justified reverting only span. The enlarged grassy bank reduces bare-rock share in the frozen arch foreground to0.0%, and its smoothed fold remains under the original cap.

The first-cut mesh extends under the fairway. A material-only transition shades298/514 faces under/within.35m of the fairway as LK_FAIRWAY, with outer collar LK_ROUGH. All scoring vertices/polygons/names/transforms are exactly preserved. Exact audit includes14 protected meshes and9 markers, with max vertex and marker deltas0.000m in staged blend and staged FBX; FBX uses exact spatial triangle multisets and unique world positions to account for UV splits, without epsilon.

## Evidence and remaining work

- build_attempt1.log and verify_attempt1.json/log preserve the three real failures: local MOW_PATTERN, local ARCH_SLAB_COVERED, and verifier NEEDLE_ARCH in both formats.
- arch_profile_diagnosis.json and arch_regenerate_diagnosis.json explain the arch correction without relaxing its gate.
- build_attempt 2.log and builder_gates_final.json record47/47PASS.
- verify_final.json/log record raw100/100PASS on staged blend and FBX.
- ../audit/scoring_exact_p2.json/txt record exact scoring0m.
- GATES_hole08.md includes every gate with measured details and honestly flags the skipped still gate.
- patch_plan.md preserves the initial prepared plan; actual arch span was reverted after measurement.

Next: parent renders the frozen stage at reference aerial and address cameras, measures two visible needles per address view, saves side-by-side and re-scores ranked differences. A full P2/P5 framing PASS cannot be inferred from geometry. Ideal unobstructed sea coverage at z0 is only3.752708% tee/4.180417% approach (15% required), and at z5.99 is4.998333%/5.384306%; preserve these honest FAILs.

## P2 final binary result: FAIL

The required parent Unity render attempt failed to compile due to protected concurrent Hero Editor errors in MatchHeroLockerExport.cs (line131 ReadSources missing; line141 method-group comparison). Fresh tee/approach/aerial and side-by-side are unavailable. No protected code was edited. P2_RESULT.md and ranked_rescore.json explain all ten actual geometry changes/remaining differences without inventing a visual re-score. Required-still verification is recorded separately in verify_required.json/log.
