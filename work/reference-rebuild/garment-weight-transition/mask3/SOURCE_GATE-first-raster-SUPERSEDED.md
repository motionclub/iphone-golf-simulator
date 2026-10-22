# Exact underarm trace checkpoint

GATE: 49-face static mask extension FAIL. Do not promote `runtime-profiles/Tennis_Female.json` from this directory.

GATE: Forehand1 additive local cloth source replay PASS. Runtime/shader/LOD and other motions remain PENDING; no whole-clothing acceptance is claimed.

The pixel rays at (365,492) and (375,498) in actual mask2 Forehand1 strike canonical Body faces15924/15925, 17–20mm ahead of intact Top face5124. Those Body faces lie at rest x−.126..−.133m/y1.168..1.179m. An arm-influence corner at.531 causes the original torso all-corner mask threshold.45 to omit the triangles; axial sleeve coordinates.49..53 correctly prevent treating them as cuff interior. Lowering the height guard cannot solve this.

The obvious49-face completion of this torso/arm threshold fixed the Forehand1 stripe but failed330 exact perspective source views (33clips×5samples×front/rear):111 views contained entirely new background holes, max120pixels, and178 had some new background coverage, max271pixels. Exact per-face impact is saved. Some key stripe faces themselves cause small holes elsewhere, so broadening this static mask cannot be certified. The original mask2 stays in use.

The concrete replacement is `local-cloth-focused/UnderarmTrace_Female.json`:13932vertex exact source basis, one additive anchor `female_Forehand_1_UnderarmTrace`,28existing feature values, rest position and normal deltas. Original Top indices/UVs/weights, Body geometry/weights, rig and original sleeve anchors remain unchanged. It must be added independently after original sleeve interpolation. Do not insert its anchor into the original normalized anchor family.

A compact smooth field follows the exact Top faces behind the nine traced left-underarm Body faces. It is inverse-skinned to the exact rest basis. The field max is28mm posed/29.44mm rest.1833vertices have nonzero change,1207 exceed1mm and302 exceed25mm; all lie in the left lower-armhole/side-panel region. A local fold line search yields zero triangle-normal reversals above1e-8m² area. The final exact front/rear source check creates0new background pixels and0new skin pixels; it covers430previously visible skin pixels at front, including all231traced stripe pixels. This does not certify shader smoothness or cloth volume styling.

Recommended initial feature confidence is1 through mean squared distance.002, fading smoothly to0 at.04. Under full28feature matching the sole active captured sample is Forehand1; the next nearest captured pose is HitPerfect1 at.16776. Forehand2 andForehand4 are distinct at.31789/.58718 and remain outside this initial field.

Root should capture final shader/full and LOD Forehand1 before expanding. Subsequent reuse should be side-specific arm pose support, not simply wider28feature confidence: left upper-arm direction against spine/chest/shoulder corresponds to features[2,8,13]. Those three features identify similar arm configurations in Volley, ForehandShort and SplitToForehand that full-body28features reject. Twist/forearm terms must still be bounded and validated. `local-field-feature-study.json` records distances without widening the accepted candidate.

Further source experiments are parked: `local-cloth` used49face targets in both views and had triangle reversals; `local-cloth-three` has a clean isolatedForehand2 field but Forehand4 retains90target skin pixels. Neither is recommended for promotion. The front-facing-onlyForehand4 camera expansion was contaminated by distant back-side cloth hits, so subsequent authoring must use the nearest local underarm surface and explicit armhole topology, rather than arbitrary ray depth through the torso.
