# Female shader pass — 2026-10-16 (PROMPT_SHADER_FIXES.md, this session)

Proof: proof/shader-pass/ (README lists every sheet). Candidate files: unity/{HeroLighting.hlsl, HeroFaceSkin.shader, TennisCharacter.shader, TennisCloth.shader, FemaleGarmentFinish.cs, FemaleShaderReview.cs} (= clone), native-shader/MatchHeroSurfaces.swift, native-shader/assets/*.json. Baseline backups: revisions/shader-pass-blender-20261016/.

- GATE: Visible material change, studio, Cream skin PASS — skin mean HSV saturation .290 -> .353 on the matched face crop; lit/shadow separation and jaw/underside form visible in studio-golf.jpg; blush quieter (pigment only).
- GATE: Selectable skin colours preserved PASS — Fair/Tan/Deep keep their own hue (relative tone maths, no fixed tan); saturation .250/.344/.355 -> .301/.422/.388; highlight clipping (>=250) not increased: .0434/.0281/.0272 -> .0438/.0265/.0129 (studio-tones.jpg).
- GATE: Eye depth without geometry change PASS — matched eye macro: iris bottom/top luminance ratio 0.90 -> 1.93 (lower caustic crescent, lid-shaded top), sclera mid 175 -> 156 (no longer clipping), sclera top 100 -> 77 (lid shadow). Eye size, placement, gaze, catchlights unchanged. Root cause found: the original-seam eye layers had NO lid frame (eyeCoord was 0, _FaceRole 0), so the earlier eye branch could not shade by position; FemaleGarmentFinish now measures a bind-pose frame (UV1 copy of that per-hero mesh, sclera centres, brow-up axis).
- GATE: Matte knit / fold response PASS (visual), metric neutral — polo sides fall into the colour's deeper hue with rounded falloff and soft grazing velvet; light/dark/saturated swatches readable (studio-swatches.jpg). Fine-texture std at the studio crop is unchanged (2.28 -> 2.20): the knit breakup is subtle by design (derivative-faded for phone distance). Missing collar stand / air gaps / fold geometry are garment-construction issues, not shader.
- GATE: Unchanged game environments PASS — matched Tennis (Tropical Open, seed 3108, same frames) and Golf (cliffside 12, forced Clear, 8 mph, impact frame 62 in both runs) captures; world lights/post/cameras untouched. In-game the change is smaller than in the studio (sun lighting), but consistent: warmer skin, richer cloth.
- GATE: Female regressions PASS — 17/17 Female EditMode tests in the clone (proof/shader-pass/female-tests.json).
- GATE: Native SceneKit port PASS (candidate) — compiles with the app sources; native lobby renders show the same lid/iris depth, skin and knit changes (native-lobby.jpg). Fresh female export: geometry/rig .lzfse byte-identical to production; manifests differ only in material keys (wrap, weaveNormal, weaveThread, normalStrength, smoothness, femaleSurface on pupil/limbal).
- GATE: Production install PASS — user approved the look; install_shader_pass_20261016.py installed 5 Unity files + GolfArcade/Unity/MatchHeroSurfaces.swift, merged only material keys into the 3 female manifests (46/46/39), refreshed VisualGolden provenance (0 stale look hashes, manifest hashes match); production files byte-equal to the reviewed mirrors; male payloads unchanged; native renderer rebuilt from production sources renders the reviewed result (mean diff ~1/255). Staged, not committed. Rollback: `python3 work/female-soulful/install_shader_pass_20261016.py --rollback` (backups + hashes in revisions/shader-pass-install-20261016/).
- GATE: Male rendering unchanged NOT RUN as images — static only: every new branch is behind _SkinFinish>1.5, _FemaleSurface, _FemaleEyeRole or the female-only FemaleGarmentFinish; male defaults untouched.
- GATE: Reference appearance AWAITING USER — substantial visible improvement measured above; the user owns acceptance. Remaining gaps: generated-reference faces have a smaller pupil/iris ratio and different proportions (geometry, out of scope); cap stitching still reads bright (trim mask shared with the patch); garment construction (collar stand, air gaps) belongs to the garment task.
- Phone performance: deferred by the user; no device claim.

--- Earlier results (superseded where conflicting) ---

# Shirt fixes gates — Claude, 2026-10-16 evening

- GATE: Golf polo binding continuity PASS — no layer/panel weight tears (largest remaining jump 0.58 across a 5 cm edge); stress severe-strain lower in every golf group; geometry audit 0 degenerate / 0 non-manifold (proof/combined-fixes/geometry-audit.json).
- GATE: Golf polo real game motion PASS (observed) — muted cliffside capture, full drive, proof/combined-fixes/golf-live-binder2/. Observed motions only, not a blanket no-clipping claim.
- GATE: Tennis tank serve/overhead chest poke-through FAIL — reduced (182→90 enclosed skin px over 9 frames; serve holes 3–4 → 1–3 small specks) but not eliminated; Run/Overhead gained one small speck each. proof/combined-fixes/tank-follow/.
- GATE: One general solution PASS — construction/weight-transfer and coverage rules only; no named-clip, frame-window or pose-bank logic; experimental top DQ/cloth/sleeve-sweep paths removed from runtime.
- GATE: Protected assets PASS — 18/18 skirt files unchanged; HeroPoseSafety, HeroGripPolish, HeroArmSkinning, HeroAccessories, HeroShoulderWeights unchanged; MatchHeroLook byte-identical to production; male untouched.
- GATE: Existing female tests PASS — 26/26 EditMode (FemaleDeformationTests, FemaleHeroAliveTests, HeroAccessoriesTests, CharacterLookTests).
- GATE: Native parity PASS (staging) — fresh tennis/Distance/golf exports, self-check max 0.0019 mm; real SceneKit renders incl. serve/jump/drive motion frames.
- GATE: Production install PASS — 18 Unity files + 41 native files + 3 goldens/provenance installed with before-hash guards and post-copy verification; male payloads unchanged; backups in revisions/production-install-20261016/.
- GATE: Production compile/tests NOT RUN — no second Unity Editor or Xcode test run; clone with identical runtime scripts (except shader-owned FemaleGarmentFinish) compiles and passes 26/26.
- GATE: Device performance NOT RUN — deferred by the user.

---

> Latest shader review: reference material appearance still FAILS. The previous pass is a subtle cleanup, not a completed reference match. See SHADER_REFERENCE_GAPS.md and proof/review/reference-vs-current-shaders.jpg. Older completion statements below are superseded.

# Implementation evidence

The user owns visual verification and requested images at each finished component. The expression requirements in START_HERE.md were superseded: retain the original face and restrained existing expressions.

- GATE: Original face/source preservation PASS — MatchHeroLook.cs, HeroFaceReferenceFit.cs and HeroFaceSkin.shader retain their original production hashes. No new mouth/teeth component.
- GATE: Separate garments PASS — four editable pattern-based Blender sources; separate top/bottom Unity meshes, approximately 19,800 triangles per piece.
- GATE: Game/native integration PASS — installed in the repository, including female native rig/morph exports and compressed maps. Original body/rig/clip assets, male assets, maps, cameras and lights preserved. No unexpected changes among 2,719 protected Unity files.
- GATE: Existing female regressions PASS — 17 passed, 0 failed, proof/female-tests-implemented.json. Native hero renderer compiles with the app's actual data/material/motion sources.
- GATE: Captured motion integration PASS — actual idle/wave/overhead celebration/recovery and full golf swing captured. Golf returned to Aim after 406 video frames, 627 flight simulation frames; 13.53 seconds, no audio, no flight compression. This is evidence of those observed motions, not a blanket no-clipping claim.

Appearance acceptance remains the user's judgment: proof/review/implemented-female-kits.jpg, polo-current.jpg, tennis-current.jpg, tennis-overhead.jpg and the muted comparison clips.

Phone performance was explicitly deferred by the user. Inherited body triangle count remains 68,476 rather than the nominal 35–50k target; identity was preserved instead of remeshing it. No target-device readiness claim.
