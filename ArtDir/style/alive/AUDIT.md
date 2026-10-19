# Female alive audit — 2026-10-15

Baseline: current working-tree game in an isolated APFS Unity clone; female player, existing outfits, lighting and gameplay cameras. Muted 30 fps capture with 60 Hz simulation. `after/before/` contains full-resolution frames and traces; seconds below are relative to each clip. This is a qualitative screen-read audit, not a phone performance measurement.

| # | Principle | Baseline | Evidence / fastest opportunity |
|---|---|---|---|
| 1 | Never fully still | weak | Idle 0–8s: ready loop, but little independent chest/shoulder life. Golf 0–1s: address is held at fixed clip time. Add small breathing and asymmetric settling. |
| 2 | Eyes / attention | weak | Rally 9.8–14.7s: existing ball-following head; blink/gaze performer already installed. Golf 0–2s: fixed downward address attention, no eye-to-head target follow. Supplement with labeled front diagnostic footage; eyes cannot be judged from the rear gameplay camera. |
| 3 | Reactive faces | weak | Joy 0.4–2.4s / slump 0.5–3s: authored emotion poses; existing smile/sad morph driver. Wave has no happy-face mapping; golfer gets moods only from selected emotes. |
| 4 | Overlap / follow-through | weak | Wave 2.5–4s and joy 2.4–5s: clip blends return, garments settle exactly with the skeleton. Add independently damped garment motion. |
| 5 | Anticipation / settle | alive | Golf 1–2.1s: actual load, swing and follow-through. Rally 8.5–10.5s: serve wind-up and recovery. Preserve these authored contact timings. |
| 6 | Personality in timing | weak | Idle 0–8s has a generic even rhythm; joy and slump have distinct authored rhythms. Add a slow asymmetric idle beat, keeping emote choreography. |
| 7 | Moment-specific reactions | alive | Rally 14.75s: actual lost-point slump. Joy/slump test clips enter through the real emote API. Golf result face feedback can be more immediate without adding an animation delay. |
| 8 | Fabric moves | missing | Golf sleeve during 1–3s; skirt during joy 0.5–3s: skinning/fit corrections only, no inertial cloth lag. Highest-value addition. |
| 9 | Clothing thickness | alive | Existing pleats, hem and collar edges read in idle/emote and golf frames. Preserve garments and socket bindings; no remodeling. |
| 10 | Soft fabric shading | weak | Golf 0–2s / tennis idle: matte fabric and construction detail exist, but strong lighting and small screen size limit readability. Keep shader, colour controls and lights; avoid broad shading changes in this quick pass. |

## Chosen changes (four)

1. Female-only restrained breathing / asymmetric upper-body idle; zero additional root or foot motion, fade out before actions.
2. Golf eye target first, delayed bounded head follow; retain the tennis tracker and existing natural blinks.
3. Friendly wave face and brief golf outcome expressions through the existing face performer; do not change face geometry/identity or outcome timing.
4. Female top and skirt/skort secondary motion: tiny outward-only garment morphs, driven by independently damped chest/hip motion. Keep original assets, bindings, thickness, materials and existing correctives. No per-frame vertex processing or cloth solver.

Male behavior, body/face source meshes, rig, animation sources, outfits, palette persistence, maps, lights and gameplay camera are excluded. Compare identical gameplay/diagnostic views before and after. Stop on identity/silhouette drift. Phone 60 fps requires a device measurement; fixed-time editor captures cannot establish it.

## Result

The four selected additions are implemented for the female only. Controlled proof is in `after/female-alive-review.mp4`, `after/gameplay-sheet.jpg`, and `after/detail-sheet.jpg`. Baseline blink timing and authored actions remain intact; the wave gains a smile, idle gains independent upper-body motion, and garments lag then settle. All 7 focused tests pass; tennis physics/score traces and the golf landing are unchanged. Existing underarm fit defects remain in both versions. See `after/GATE_RESULTS.md`: visual/functional gates pass; phone 60 fps remains unmeasured (FAIL), despite a small measured editor CPU cost.
