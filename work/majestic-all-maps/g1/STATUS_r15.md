# G1-G3 look rounds 4-15 — status 2026-10-17 22:45 (chat 10)

Layer: unity/Assets (clone-only, nothing in Unity/, nothing staged). Sheets: g1/progress_r4.jpg … progress_r13.jpg (r4 | r13 | target = the cumulative before/after).

## Fixed (root causes)
| gap | cause | fix (file) |
|---|---|---|
| sea / far islands washed grey | EnvironmentLook depth layers 90/280/900 m blend up to 72 % to RenderedSky's grey horizon | per-course layers + fog lean each frame, restored on switch-off (MajesticCourseKit.Haze) |
| corridor beds invisible, boulder in the rough | beds 8-25 yd out; boulders in Z1 | Z1 low beds 3-12 yd, boulders only Z2 22-55 yd (MajesticScatter) |
| scatter culled for the wrong camera | LateUpdate + Camera.main | per-camera draw on beginCameraRendering |
| no dressing in the tee view | lie filter: everything near the tee is "fairway" | tee-side beds may use fairway lie within 8 yd of the tee point |
| Magma "striped sky" | caldera ring x1.9 tall | x0.6, readable mesh + darkened basalt, LOD1 only, lava fall every other wall, orange FX glow (MajesticHoleKit, MajesticKit, MajesticFX, Editor/MajesticKitImport) |
| Magma turf yellow (hue 65 vs 88) | warm + magenta grade | Temperature -10, Tint -4 (MajesticCourses) |
| Magma starry night / ash grey | Night .3; chat 2 profile AshOvercast .42 | Night .08; AshOvercast .12 + SunsetOverride .85 via RenderedSky.Current.Look (reversible) |
| Wild Isles midday | RenderedSky ignores chat 9's _Sunset; colour follows real sun | SunsetOverride .6 + sun at -25 deg / 8 deg (in frame) |

## Perf (MajesticGolfBudget, 8 holes, 158 static views)
| | r1 | r13 (dense) | r15 (thinned) |
|---|---|---|---|
| median view tris | 0.61 M | 1.09 M | **0.75 M (G0_MEDIAN <= 0.8 PASS)** |
| views > 1 M | 57 | 83 | 62 (G0_ALL_VIEWS FAIL, as before: characters 0.61 M + turf 0.48 M fixed) |
Scatter: per-instance random distance thinning, all kept < 45 yd, 10 % by 140 yd, 3 px size cull.

## Objective score
REF_MATCH 2-5 / 40 across rounds (the AI targets carry far more micro-detail; detail_ratio is the failing term). NO_EMPTY_VIEW 23-28 / 40. Not a PASS.

## Still open (next builds, each bigger than a tweak)
1. Magma ground: the targets' glowing lava-crack basalt off the fairway (needs a ground/decal shader pass on Magma rough).
2. Hole 17 alpine: snow-laden pines + snow banks (kit asset or tree material variant).
3. Golden clouds / sky detail on Wild Isles (RenderedBackdrop cloud tint is chat 2's file -> patch request).
4. Foliage density/variety near the corridor at the targets' level within the 0.8 M median.
5. Holes 9, 14, 15, 16, 18, 19, 22, 23 not yet looked at with the r15 layer.
6. Final gates (NO_VOID, POP_IN, READABILITY, device PERF) + install patch for chat 6.
