# Far tree cells: moving-camera pop check

Excess = largest 16x16-block luminance jump in the played sequence beyond the full-mesh reference (0-255); a pop reads at > 12.
max far-vs-full = largest block difference between the far copy and the full mesh on the same frame.

swap frames = frames where a 16x16 block's played-vs-full difference appears or vanishes (> 8 vs < 2); swap max = that block's difference (the visible size of the swap).

| sequence | frames | swap frames | swap max | max excess (motion-confounded) | max far-vs-full |
|---|---|---|---|---|---|
| h07_dolly | 241 | 167 | 35.4 | 17.2 (frame 200) | 35.4 |
| h07_fly | 238 | 45 | 28.2 | 19.6 (frame 53) | 32.7 |
| h13_dolly | 241 | 175 | 33.2 | 32.6 (frame 10) | 33.2 |
| h13_fly | 238 | 74 | 29.0 | 16.0 (frame 21) | 29.0 |
| h17_dolly | 241 | 190 | 26.9 | 26.0 (frame 166) | 29.0 |
| h17_fly | 238 | 71 | 24.5 | 17.3 (frame 13) | 30.5 |
| h19_dolly | 241 | 195 | 34.9 | 22.7 (frame 6) | 47.6 |
| h19_fly | 238 | 58 | 34.6 | 13.6 (frame 39) | 34.6 |

## Logged swaps (Unity LOD selection replicated per frame; rect = the cell on screen)

Visible size = 95th percentile of 16x16-block |played - full| inside the cell rect on its far frame; > 12 reads as a pop.

| sequence | swaps in view | median size | max size | swaps > 12 |
|---|---|---|---|---|
| h07_dolly | 15 | 0.3 | 17.2 | 4 |
| h07_fly | 21 | 10.4 | 20.3 | 10 |
| h13_dolly | 9 | 0.1 | 9.5 | 0 |
| h13_fly | 9 | 5.1 | 11.6 | 0 |
| h17_dolly | 16 | 2.4 | 12.0 | 1 |
| h17_fly | 20 | 8.2 | 14.9 | 2 |
| h19_dolly | 16 | 8.4 | 23.8 | 6 |
| h19_fly | 17 | 2.9 | 14.4 | 2 |

All: 123 swaps in view, median 5.5, max 23.8, 25 above 12.

## Excluding camera cuts
31 swaps fell on a HoleIntro camera cut (mean frame change > 25/255, invisible). Remaining 93 swaps in view: median 2.0, p90 13.0, max 35.0; 11 above 12, 4 above 20 (pixel-level 95th percentile inside the cell rect).
Worst: [(35.0, 'h19_dolly', 224, 88), (23.0, 'h07_dolly', 31, 86), (21.0, 'h19_dolly', 187, 94), (21.0, 'h19_dolly', 106, 94), (16.0, 'h19_fly', 33, 111)]
