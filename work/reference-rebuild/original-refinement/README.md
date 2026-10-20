# Original facial seam pilot (work only)

Source: canonical HeroBase male/female MatchAnims Blender files, not the parked CC0 heads. Original canonical options remain unchanged; the separately flagged candidate is installed for comparisons.

`refine_original_seams.py` creates `Male_OriginalSeamPilot.blend` and `Female_OriginalSeamPilot.blend`, with `Body` and rigged `ReferenceFeatures` on the exact existing 53-bone hierarchy. Original Body positions and weights have zero measured change. Eye, iris and pupil coordinates are unchanged. The source includes the original neck/body; no graft or anatomy replacement.

Changes:

- Three connected inset rows join each existing eye-hole boundary to the actual unchanged Sclera surface. These are skin topology, not disconnected runtime overlays. Original boundary positions are retained; the inward aperture inset is 1 mm.
- Original duplicated lid-line/lower-lid/crease, lip, seam, nostril and artificial Catch meshes are excluded from ReferenceFeatures. Physical eye reflections replace the Catch geometry. One original brow volume remains, depth-fitted to the skin (under 0.7 mm movement).
- The existing lip and nostril LOOP labels drive feathered `SkinPigment` vertex colors on Body for the Blender preview. UV0 additionally carries continuous lip and seam/nose mask amounts. The optional game helper supplies a 64×64 linear multiplier texture to the existing BaseMap slot; the selected BaseColor remains the user's skin tone. Pigment follows actual skin, not a projected surface strip. No shared shader edits are required.
- Work-pilot Body normals use smooth geometric normals instead of the old custom split normals. No source positions, rig rests, contacts, loadout or game data changed.

Visual result: the female double dark liner and separated lip/nostril paint are removed. The original eyelid edge and source cheek/mouth lumps remain visible, especially male upper-eye corners; these are not certified as reference-quality geometry. The reference comparison is intentionally shown beside the unchanged facial anatomy.

At parent direction, exported optional resources are installed at Resources/Tennis/OriginalSeam/Male|Female.fbx. `VISUAL_ORIGINAL_SEAM=1` selects them; both original defaults and the separate CC0 flag remain intact. The model bypasses the old face overlay/closure stack and HeadVolume. The existing continuous-normal diagnostic can still run when explicitly selected. HeroHeadSurface registers Sclera into Body bind coordinates through exact skinned inverse binds. No blink/smile shape is authored in this open-face seam pilot; it is not final performance-ready. Root owns actual Unity compilation/render validation.

Reproduce with Blender (CPU, four threads): `Blender -b --threads 4 --python work/reference-rebuild/original-refinement/refine_original_seams.py` from repository root. `seam-pilot-manifest.json` records exact source paths, contour points, zero-position/weight assertions and append dimensions.

## Connected blink candidate

`author_connected_blink.py` loads the accepted seam source and authors Body-connected eyelid motion. It uses two independent morph targets for one blink parameter: `Hero_Blink_Half` (physical 50% closure) and `Hero_Blink` (100%). Weights are `half=max(0,1-abs(2*b-1))`, `full=max(0,2*b-1)`. The feature renderer uses the same names/weights, recessing only Sclera/Iris/Pupil/Limbal/Catch at closure; brows remain exact. The open body, eye features, rig, skin pigment and 0% model remain unchanged. There is no added closure renderer or duplicate rim.

Sources: `Male_OriginalSeamBlink.blend` and `Female_OriginalSeamBlink.blend`; export with `export_connected_blink.py` using the canonical metre/FBX_SCALE_ALL preset. `connected-blink-manifest.json` lists changed-region counts and actual displacement metrics. Source front/threequarter images at 0/50/100 show closed skin without white eye fragments. Male closed crease retains small uneven skin highlights; actual Unity 0/25/50/75/100 must be judged before visual acceptance. This is not a final visual PASS.

## Eye/brow material A/B

`author_eye_material.py` loads the accepted open source6, adds eye-local UVs to existing Iris/Sclera polygon regions, and exports separate `Male|Female_OriginalSeamEyeMaterial.fbx`. Source Body and ReferenceFeatures positions, topology, normals, weights and rig are unchanged. The maps are relative multipliers: a broad warm iris mid-ring with restrained dark edges; subtle warm upper/outer sclera falloff. No starburst, new geometry, pupil-size change or skin-palette change. Brow roughness is explicit.

Optional runtime: `VISUAL_ORIGINAL_SEAM=1` with `VISUAL_ORIGINAL_EYE_MATERIAL=1` selects `Resources/Tennis/OriginalSeamEyeMaterial`. Without the eye flag the accepted source6 resource stays selected. `HeroOriginalSeamAnatomy.ConfigureFeature` applies the same deterministic relative maps through the existing BaseMap slot and makes brows matte. Root owns the actual matched-portrait A/B and visual acceptance.

Blink diagnostics are parked after actual blink10/11 rejection. Accepted no-morph source6 FBXs were restored; all blink work files remain for diagnosis. Runtime normal isolation fixed the global shaded-face regression but did not produce accepted lid closure. No default model promotion, gaze/native integration or visual-completion claim follows from the material A/B.

Actual eye13 paired render gate: root inspected `proof/reference-rebuild/character-eyes13` against `character-eyes13-control`, accepted matte brows and richer graded iris as a small positive. User-facing plate: `outputs/reference-check/eye-material-progress.jpg` in the chat output directory. Source provenance/SHA256 and honest scope are recorded in `eye-material-actual-gate.json`. This is not full reference-character acceptance. The accepted eye treatment becomes default only within explicitly selected OriginalSeam; `VISUAL_ORIGINAL_EYE_MATERIAL=0` retains the control treatment.
