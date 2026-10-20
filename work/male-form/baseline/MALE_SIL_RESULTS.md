GATE: MALE_SIL PASS

**Authority for this gate: ONLY `male_body_bald.jpg`, front and back. Each must have symmetric difference / union ≤ 5.0%.**

| Authority view | Difference pixels | Union pixels | Error / union | Gate |
|---|---:|---:|---:|---|
| bald_front | 3,301 | 75,213 | 4.3889% | PASS |
| bald_back | 2,662 | 74,141 | 3.5905% | PASS |

Continued from the saved Micro1 `HeroBase_Male_Silhouette.blend`; no regeneration or remesh. The existing male mesh was named `Body_M`, and only its vertex coordinates were revised. Shoulder/arm contours were narrowed where excessive, with crown, inner-thigh and heel contour corrections. Depth coordinates, topology, object transforms/origin, six camera transforms/origins/scales, packed references and grey material are unchanged.

Height: 1.703571 m. Unit system: METRIC, scale 1. A-pose. Vertices: 24,578; triangles: 49,176 (unchanged). Maximum vertex displacement: 32.99 mm.

No female, Unity, hair, stubble, textures, rig or face polish. Facial shading visible in the overlay is the source photograph; native blockout renders are plain grey.

Proof: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/base_lock/proof/01_silhouette_overlay_m.png`
Saved continuation: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/base_lock/blender/HeroBase_Male_Silhouette.blend`

Frozen source masks and alpha cutoff are unchanged. Error = count(reference XOR render) / count(reference OR render), measured in the full native 1280×720 images. Source-only mask extraction excludes floor shadows and labels, fills enclosed shading holes, and uses +7.5 sRGB levels against row-border background. Boundary uncertainty is approximately 1–2 source pixels. No candidate render changes a reference mask, origin or scale.

| Diagnostic view (excluded from gate) | Error / union |
|---|---:|
| sheet_front | 7.2238% |
| sheet_back | 7.2622% |
| left | 5.5531% |
| right | 6.3728% |

The multiangle cameras and references remain locked and packed. Their measurements are informational and do not determine this gate.

Continuation source SHA-256: `e2059ffc42c53cacbd6aa7d483fdef468080c9f5ee4985f8d2a26055ebde0b10`
Saved mesh connectivity SHA-256: `d7cc011b2a202b2fdc92e1506096663e1ab7bfad612f0ecc40a2cff565e1d1f9`
Saved blend SHA-256: `320b90eaddc8df8fb73e6701d03969c30efaa6ab777f738b1fadf685b40ae5ab`

Saved-file verification: PASS. Reopened blend renders exactly match the proof pixels; independently recomputed primary errors are front 3301 / 75213 = 4.3888689455% and back 2662 / 74141 = 3.5904560230%. Camera/reference transforms, mesh origin, depth coordinates and connectivity match the Micro1 baseline.
