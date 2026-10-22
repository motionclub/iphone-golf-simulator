# Majestic all maps — density/variety + perf round, status 2026-10-18 12:50 (chat 10)

Sheets: `g2/cover32_{cliffside,wildisles,magma}.jpg` (game above target, 16 holes x 5 reference views); tee before/after `g2/check32.jpg` (r27 | r32 | target).
Layer only (`work/majestic-all-maps/unity/Assets`); nothing staged or committed.

## Changes this round (coordinator / Adnan 10-18)
| item | change | file |
|---|---|---|
| density + variety, 10-30 yd edge band | layered beds: low blooms in front, ferns / small shrubs in the middle, tall shrubs / broad bushes at the back, small rock accents; 5 bloom colours (coral, gold, white, violet, pink), two per bed; biome swaps (Magma ferns + dark rock, 18 cactus, 17 no blooms). Clustered: a bed every tee-side spot (1.6x fuller within 25 yd) and every third corridor spot, single tufts between. All instanced per camera. | MajesticScatter.Bed / Place |
| bed plants hold to ~75 yd | thinning priority .45 for bed plants; everything else thins 35 -> 100 yd | MajesticScatter |
| pines past ~80 m | every resort tree cell (`RESORT_BOTANICAL_n_PINE/PALM/OAK_NEAR`) gets a LODGroup whose far level is a colour-preserving clustered copy (cell 0.9 yd, trunk and crown never merge), switching at ~87 yd; saves 75-416 k tris per hole on 7, 13, 15, 16, 17, 19, 21-23 | MajesticBudget.FarTrees / ClusterVisual |
| coast reach | 200 -> 170 yd | MajesticCoastKit |

## Perf (MajesticGolfBudget, 16 holes, 316 static views)
| | r1 | r26 | **r32** |
|---|---|---|---|
| median view | 0.62 M | 0.806 M | **0.760 M — G0_MEDIAN (<= 0.8) PASS** |
| views > 1 M | 101 | 117 | 113 — G0_ALL_VIEWS FAIL (characters 0.61 M + turf 0.48 M fixed costs, unchanged) |
| worst view | 3.80 M (h12 tee) | 3.92 M | 3.97 M (h12 tee; the course's own GolfCoastalInstances 1.66 M) |
Note: r32 logged h13 tee at 4.65 M with draws 632 / set-pass 258, double every other run (325 / 136); that is the known double-count read of the counters, the real value is ~2.3 M as in r1-r31.
Not covered: POP_IN of the far tree cells needs a moving capture (stills cannot show a pop); the switch is at ~87 yd on cells of 48 yd.

## Structural score (g2/verdicts_r32.json -> g2/SCORE_r32.md): 444 / 640
Cliffside 146/200, Wild Isles 149/240, Magma 149/200. Near dressing 24/80 (binary item; the variety gain is not counted by it), water edge in frame 30/80.

## Open
- Resolved (Adnan 10-18): the pine walls on holes 7 and 15 stay as they are (details in g2/WATER_EDGE.md).
- Wild Isles hero subjects need new assets (gnarled canopy trees 14, snow-laden pines + peaks 17, mesa walls 18).
- Golden upper sky on Wild Isles needs a golden profile in chat 2's RenderedSky.
- Game issues for owners: h18 flyover camera inside the mesa; big floating labels (h19, h20); h16 off-line hazard block.

## Addendum 10-18 13:55 — far tree cells pop check (moving camera)
Method: MajesticHoleViews `MAM_PROBE=pop` flies the real HoleIntro flyover (238 frames) and a low fairway dolly (241 frames) on holes 7, 13, 17, 19, rendering every frame as played and with the far cells forced to the full mesh, HUD hidden; Unity logs every far-cell LOD switch with its screen rectangle (replicated LOD selection). `tools/pop_check.py` sizes each swap as the 95th-percentile |played - full| inside the cell on its far frame; swaps on a HoleIntro camera cut are excluded (invisible).
| run | far switch | swaps in view | median | p90 | max | > 12/255 | > 20/255 | median view tris |
|---|---|---|---|---|---|---|---|---|
| r35 | 130 yd, cluster .65 yd | 93 | 2.0 | 13.0 | 35.0 | 11 | 4 | 0.781 M |
| **r36** | 130 yd pines/oaks, 195 yd palms | 98 | **1.0** | 12.0 | 23.0 | 9 | 3 | **0.791 M** |
(r34 at 87 yd / cluster .9 yd showed tier-merged blobs swapping in the flyover; its image-only metric was confounded by motion, so the swap log replaced it.)
Verdict: POP_IN mostly PASS — median swap 1/255; 3 swaps of 98 reach 20-23/255 (pines on the 7 and 19 dollies at 86-134 yd; the low dolly is close to what the ball-follow camera sees, so these can show in play). Further reduction trades directly against the 0.8 M median (0.791 now). Videos: g1/pop_r36/h*_fly_played.webp.
Counter note: r32/r36 logged some tee views at exactly double draws (13, 15, 19 tee); real values unchanged.
Pine walls on holes 7 and 15: kept as they are (Adnan, 10-18).
Far tree swaps accepted as they are (Adnan, 10-18): 130 yd pines/oaks, 195 yd palms, cluster .65 yd.
