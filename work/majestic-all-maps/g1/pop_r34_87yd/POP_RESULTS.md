# Far tree cells: moving-camera pop check

Excess = largest 16x16-block luminance jump in the played sequence beyond the full-mesh reference (0-255); a pop reads at > 12.
max far-vs-full = largest block difference between the far copy and the full mesh on the same frame.

swap frames = frames where a 16x16 block's played-vs-full difference appears or vanishes (> 8 vs < 2); swap max = that block's difference (the visible size of the swap).

| sequence | frames | swap frames | swap max | max excess (motion-confounded) | max far-vs-full |
|---|---|---|---|---|---|
| h07_dolly | 241 | 238 | 48.9 | 35.2 (frame 222) | 60.3 |
| h07_fly | 238 | 67 | 37.3 | 27.4 (frame 28) | 41.7 |
| h13_dolly | 241 | 238 | 48.7 | 32.8 (frame 10) | 48.7 |
| h13_fly | 238 | 79 | 34.9 | 19.0 (frame 25) | 35.3 |
| h17_dolly | 241 | 235 | 57.1 | 39.7 (frame 208) | 57.1 |
| h17_fly | 238 | 73 | 45.1 | 33.2 (frame 30) | 49.1 |
| h19_dolly | 241 | 226 | 56.9 | 44.9 (frame 133) | 61.6 |
| h19_fly | 238 | 68 | 82.6 | 41.7 (frame 52) | 82.6 |
