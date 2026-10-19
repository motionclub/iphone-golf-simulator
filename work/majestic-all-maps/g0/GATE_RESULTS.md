# G0 golf make-room: gate results (chat 10, round 1, 10-17)

All numbers come from `MajesticGolfBudget`:
- every player camera of every hole, re-posed from `audit/views_clear/hNN_cameras.json`;
- published render counters for the 1080p frame, Mac Editor, clone of Unity/;
- the "after" clone has the chat 10 layer installed with `MAM_WITH_LAYER=1`.

**Not device numbers.** The live-drive views (`drive*`) are excluded: their counter reads double (the breakdown sums to about half the total).

## What changed
- **Shadow proxies** (`Scripts/Majestic/MajesticBudget.cs`): tree and cliff batches cast from a vertex-clustered copy (`MajesticShadowOnly.shader`) and draw exactly as before.
- **Coastal instancer patch** (`tools/patch_g0_instancers.py`, shared file → chat 6): tree groups cast from a proxy.
- **Lite foliage kits** (`g0/blender/lite.py`): BotanicalKit and CoastalBotany with PINE/PALM/CONIFER/SHRUB at 45–75 % of their triangles, same names, UVs and colours.
  - Used at every distance, so no LOD switch and no pop-in.
  - Side by side: `g0/lite_compare.jpg`.

## Per hole (static views)
| hole | worst static view before → after (M) | median view before → after (M) | shadow pass Δ before → after (M) | coastal botany (M) |
|---|---|---|---|---|
| 7 | 2.58 → 2.12 | 0.82 → 0.61 | 0.53 → 0.42 | 0.00 → 0.00 |
| 8 | 2.13 → 1.97 | 0.71 → 0.57 | 0.51 → 0.35 | 0.00 → 0.00 |
| 9 | 2.55 → 2.27 | 1.22 → 0.90 | 0.64 → 0.34 | 0.00 → 0.00 |
| 10 | 1.87 → 1.81 | 0.43 → 0.40 | 0.37 → 0.00 | 0.00 → 0.00 |
| 12 | 5.66 → 3.80 | 2.47 → 1.62 | 1.91 → 0.34 | 3.13 → 1.66 |
| 13 | 2.21 → 3.12 | 1.08 → 0.71 | 0.54 → 0.00 | 0.00 → 0.00 |
| 14 | 1.82 → 1.86 | 0.63 → 0.59 | 0.31 → 0.33 | 0.00 → 0.00 |
| 15 | 2.55 → 1.95 | 1.28 → 0.67 | 0.51 → 0.29 | 0.00 → 0.00 |
| 16 | 2.41 → 2.19 | 0.78 → 0.69 | 0.43 → 0.00 | 0.00 → 0.00 |
| 17 | 2.81 → 2.08 | 0.99 → 0.63 | 0.49 → 0.36 | 0.00 → 0.00 |
| 18 | 1.53 → 1.45 | 0.37 → 0.30 | 0.37 → 0.29 | 0.00 → 0.00 |
| 19 | 2.61 → 2.55 | 0.88 → 0.83 | 0.46 → 0.38 | 0.00 → 0.00 |
| 20 | 1.85 → 1.84 | 0.58 → 0.52 | 0.35 → 0.31 | 0.00 → 0.00 |
| 21 | 1.79 → 1.75 | 0.65 → 0.52 | 0.26 → 0.25 | 0.00 → 0.00 |
| 22 | 1.93 → 1.86 | 0.67 → 0.60 | 0.30 → 0.26 | 0.00 → 0.00 |
| 23 | 1.85 → 2.01 | 0.65 → 0.58 | 0.38 → 0.58 | 0.00 → 0.00 |

**All static views:** median 0.78 → 0.62 M. Over the 1.0 M cap: 129 → 101 of 316.

## Gates
| Gate | Result | Evidence |
|---|---|---|
| G0_MEDIAN_VIEW ≤ 0.8 M | PASS | median 0.62 M |
| G0_ALL_VIEWS ≤ 1.0 M | FAIL | 101 of 316 static views still over. Fixed costs in every tee view: characters 0.61 M (off-limits to this chat; reported to the coordinator) and turf blades 0.48 M (golfer close-up grass, untouched so far) |
| G0_NO_LOOK_CHANGE (proxies, lite kits) | PASS (visual) | the proxies only cast; lite kits side by side in `g0/lite_compare.jpg`. In-game before/after frames come from the look rounds |
| G0_NO_POP | PASS (by construction) | no distance switch was added; flyover film still to record |
| G0_DEVICE_FPS | NOT RUN | no device run in this chat |
