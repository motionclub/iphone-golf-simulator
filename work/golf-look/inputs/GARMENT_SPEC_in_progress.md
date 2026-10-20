# Reusable tennis garment contract

White and black default kit, no branding. Colours come exclusively from runtime uniforms. Body, bones, clips and sockets are read-only. New garments use the existing six skinned piece names and seven semantic roles; no per-garment shader code.

## Files and channels

Resources/Tennis/HeroDetail/Kit_<Male|Female>_<Top|Bottom|SockL|SockR|ShoeL|ShoeR>_N.png: tangent-space RGB normal, +Y/OpenGL convention, imported as Unity NormalMap, linear, ASTC 8x8. No colour.

Matching _M.png: linear RGBA data; R = AO visibility (1 unoccluded, minimum 0.70), G = cavity/stitch visibility (1 uncreased), B = main/trim mix (0 main, 1 trim), A = fabric ID / 5. Import Default with alpha preserved, ASTC 8x8. No baked garment colour. Legacy _BaseMap is bypassed when N+M exist.

Top 2048², bottom and shoes 1024², socks 512². Target outer surface density: top 9–18 px/cm; bottom 6–14; shoes 8–20; socks 5–10. Report measured density and island occupancy; do not upscale without a memory budget. Non-overlapping UV islands, >=12 px gutter at 2048 (6 px at 1024, 3 px at 512), fill gutters by the nearest island, never dark empty space. Padding must be rechecked at distant mips. Bake the high construction surface over the low shell, with its UV tangents and a maximum 3 mm fold displacement.

## Fabric IDs

| ID | A byte | Surface | Smoothness | Charlie sheen | Detail |
|---|---|---|---|---|---|
| 0 | 0 | body pique / shorts knit | .10 | .55 | staggered pique, 8 threads/tile |
| 1 | 51 | collar, cuff, waist rib | .13 | .38 | fine rib, 12 ribs/tile |
| 2 | 102 | shoe upper mesh | .16 | .24 | open mesh, 8 cells/tile |
| 3 | 153 | rubber outsole / toe reinforcement | .04 | 0 | no weave, baked tread |
| 4 | 204 | foam midsole | .08 | 0 | no weave, faint baked texture |
| 5 | 255 | flat laces / drawcord | .10 | .18 | tight rib |

Shared Cloth_FabricAtlas.png is 512², ASTC 4x4, linear; quadrants: bottom-left pique, bottom-right rib, top-left mesh, top-right neutral. Each quadrant has an 8 px repeat gutter. RG = tangent slope normal, B = thread visibility with mean 1/1.28. Derivatives are calculated before frac; individual threads fade below 3 px/thread and disappear before 1.4 px/thread. Rubber/foam use no thread or weave normal. Knit alone gets grazing fuzz. WeaveAngle rotates both UVs and normal slopes (the old male 41-degree correction must remain for legacy UVs).

## Colour and API

SetKit keeps Kit_Shirt, Kit_ShirtTrim, Kit_Shorts, Kit_ShortsBand, Kit_Shoe, Kit_Sole, Kit_Sock. Main shader colour is lerp(_BaseColor, _TrimColor, M.B). Default main is sRGB .93 and default trim (.035,.035,.0401). A picked main follows KitTint: max(.93*pick, black floor). Its trim follows KitDerive: darken 35% if luminance >=.5, otherwise lighten 35% towards white, then KitTint. Shirt/shorts trim submeshes keep their role, and the main material receives the same trim uniform. Sole and socks retain the authored colour according to the existing API. Shoe accents in the upper mask follow the shoe pick; the separate outsole retains the default neutral trim.

## Drop-in garments and skins

Author the garment over the current read-only body; bind to the existing bone names, <=4 normalized weights, and use the existing kit renderer/socket names. Export the six kit pieces with the existing rig and no animation. Replace the appropriate N/M resources using the above names, fabric IDs and padding. Use the semantic role materials; runtime discovers N/M by sex+piece and sets all maps itself. A new skin colour or kit pick needs data only, never a new shader branch or material keyword. Whole garment swaps use the same prefab/renderer contract; selection/catalog data must register the new asset. No new bones. New silhouette detail <=6000 additional kit triangles per hero; resident kit maps including shared atlas <=6 MiB per hero.

## Proof conditions

Use ClothProofRig's fixed targets/cameras and real Tennis court lighting. Construction crops, four skirt views, all motion poses and phone shimmer film are mandatory. White L*: shirt 90–95, bottom 88–95; authored black trim 8–20. Folds must darken fixed lit crops 8–20%, never >30%. Device performance and compiled Metal instruction/sample counts must be measured, not inferred from shader source or Mac editor timing. The user's eye approval is a separate required gate.
