# Far tree cells: moving-camera pop check

Excess = largest 16x16-block luminance jump in the played sequence beyond the full-mesh reference (0-255); a pop reads at > 12.
max far-vs-full = largest block difference between the far copy and the full mesh on the same frame.

swap frames = frames where a 16x16 block's played-vs-full difference appears or vanishes (> 8 vs < 2); swap max = that block's difference (the visible size of the swap).

| sequence | frames | swap frames | swap max | max excess (motion-confounded) | max far-vs-full |
|---|---|---|---|---|---|
| h07_dolly | 241 | 169 | 34.7 | 17.2 (frame 200) | 34.8 |
| h07_fly | 238 | 46 | 28.0 | 20.4 (frame 187) | 33.2 |
| h13_dolly | 241 | 177 | 32.9 | 32.3 (frame 10) | 32.9 |
| h13_fly | 238 | 73 | 29.0 | 16.0 (frame 21) | 29.0 |
| h17_dolly | 241 | 191 | 27.0 | 26.0 (frame 166) | 28.8 |
| h17_fly | 238 | 68 | 34.0 | 17.0 (frame 13) | 34.0 |
| h19_dolly | 241 | 98 | 31.5 | 21.7 (frame 190) | 38.4 |
| h19_fly | 238 | 41 | 28.7 | 9.7 (frame 34) | 30.7 |

## Logged swaps (Unity LOD selection replicated per frame; rect = the cell on screen)

Visible size = 95th percentile of 16x16-block |played - full| inside the cell rect on its far frame; > 12 reads as a pop.

| sequence | swaps in view | median size | max size | swaps > 12 |
|---|---|---|---|---|
| h07_dolly | 15 | 0.3 | 16.9 | 3 |
| h07_fly | 21 | 10.1 | 20.1 | 9 |
| h13_dolly | 9 | 0.1 | 9.3 | 0 |
| h13_fly | 9 | 5.5 | 11.6 | 0 |
| h17_dolly | 16 | 2.5 | 12.3 | 2 |
| h17_fly | 20 | 8.0 | 15.2 | 3 |
| h19_dolly | 18 | 0.9 | 16.5 | 4 |
| h19_fly | 18 | 0.6 | 12.5 | 1 |

All: 126 swaps in view, median 2.1, max 20.1, 22 above 12.

## Excluding camera cuts
swaps in view (excluding 29 at cuts): 98 median 1.0 p90 12.0 max 23.0 above12 9 above20 3 worst [(23.0, 'h19_dolly', 156, 134), (23.0, 'h07_dolly', 31, 86), (22.0, 'h19_dolly', 195, 128), (15.0, 'h17_dolly', 13, 88)]
