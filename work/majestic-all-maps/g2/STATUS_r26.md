# Majestic all maps — coverage + structural round, status 2026-10-18 06:20 (chat 10)

Layer: `work/majestic-all-maps/unity/Assets` (clone-only; nothing in Unity/, nothing staged or committed).
Sheets: `g2/cover26_{cliffside,wildisles,magma}.jpg` (game above target, 16 holes x 5 reference views); earlier `g2/cover18_*`, `g2/cover23_*`.

## What this round added (coordinator 10-18: coverage first, kit, structural score)
| change | files |
|---|---|
| Ref-view-only capture for all 16 holes (`MAM_VIEWS=ref`) + wall probe (`MAM_PROBE=walls`) | Editor/MajesticHoleViews.cs |
| Island edges from the kit: CliffSkirt / ShoreBand / BlackSandShore + FoamStrip every 20 m along the traced coastlines (200 yd reach, LOD1 only) | MajesticCoastKit.cs, MajesticShore.cs (LastLines) |
| Lie-placed set pieces: 17 ice-fishing hut on the frozen lake, 20 brick bridges across the canals | MajesticCoastKit.cs |
| Green-back skyline: chat 2's island ring copied 180 deg about the hole at 85 %, rear half only | MajesticCourseKit.BackSkyline |
| Magma rough: "Course N Ash" swapped for cracked basalt with glowing seams (16, 21-23) | MajesticLavaGround.cs + Resources/Majestic/MajesticLavaGround.shader |
| Magma rock: caldera walls, basalt spire, obsidian arch, volcano darkened (readable FBX via Editor/MajesticKitImport.cs); volcano 2.1x at 950 yd on 21-23 so it clears the rim; spire no longer dragged onto the 23 tee | MajesticHoleKit.cs, MajesticKit.Darken/KeepLod |
| Sky: Magma warm dusk, Wild Isles golden horizon (RenderedSky.Current.Look overrides, restored on switch-off) | MajesticCourseKit.Haze |
| Denser tee-corner beds | MajesticScatter.cs |

Root cause worth remembering: from round 13 to 19 the wall `Darken` call sat behind a `//` on the same line (an edit appended it after a comment), so every wall test in between measured nothing. Found with the probe.

## Structural score (tools/checklist.py; verdicts `g2/verdicts_r26.json`, table `g2/SCORE_r26.md`)
**442 / 640** (r23: 424). Cliffside 146/200, Wild Isles 147/240, Magma 149/200.
| item | r26 |
|---|---|
| subject (named focal point of the view) | 59/80 |
| skyline layers | 66/80 |
| sky / hour | 60/80 |
| palette family | 79/80 |
| near dressing | **22/80** |
| mid dressing | 52/80 |
| water / lava edge | **30/80** |
| no empty view | 74/80 |

## Perf (MajesticGolfBudget, 16 holes, 316 static views)
| | r1 | r26 |
|---|---|---|
| median view tris | 0.62 M | **0.806 M — G0_MEDIAN (<= 0.8) FAIL by 6 k** |
| views > 1 M | 101 | 117 — G0_ALL_VIEWS FAIL (characters 0.61 M + turf 0.48 M fixed costs, as before) |
| worst view | 3.80 M (h12 tee) | 3.92 M (h12 tee: the course's own GolfCoastalInstances 1.66 M) |
Not verified yet: one more trim (coast reach 200 -> 170 yd, or the back skyline on Cliffside only) should clear the median; needs a budget run.

## Largest open gaps (by structural count)
1. Near-corner dressing (22/80): the targets fill the near corners with beds and shrubs; ours stop at the rough edge because the fairway lie fills the frame. Needs either narrower visual fairway edges near the camera or rough-edge beds that the game allows in play.
2. Water / lava edge seen (30/80): many views (h07 R, h15, h12 off-line) are blocked by pine walls or turf rises; the coast is there but not in frame.
3. Wild Isles hero subjects (needs NEW assets, not in the 34-piece kit): gnarled canopy trees + glowing mushrooms (14), snow-laden pines + snow peaks + frozen fall (17), red mesa walls with strata (18), jungle density (19).
4. Upper sky stays blue on Wild Isles (golden only at the horizon): needs a golden profile in chat 2's RenderedSky (patch request).

## Game issues seen (not mine; for the owning chats)
- h18 flyOpen: the HoleIntro flyover camera starts inside the mesa.
- Floating gameplay labels are large in some views (h19 offR "Temple aperture", h20 "Petal cut").
- h16 offL: a black hazard block fills the view.

## Install (for chat 6, unchanged rule: patches, no commits from here)
Layer files under `unity/Assets/Scripts/Majestic/` (+ Editor/MajesticKitImport.cs, Resources/Majestic shaders + Kit), `tools/patch_majestic_hooks.py`, `tools/patch_g0_instancers.py`, lite FBX from `g0/blender/lite/`. MajesticKitImport makes 5 kit FBX readable (caldera walls, spire, arch, volcano).
