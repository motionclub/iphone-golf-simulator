# Far tree cells: moving-camera pop check

Excess = largest 16x16-block luminance jump in the played sequence beyond the full-mesh reference (0-255); a pop reads at > 12.
max far-vs-full = largest block difference between the far copy and the full mesh on the same frame.

| sequence | frames | max excess | frames > 12 | max far-vs-full |
|---|---|---|---|---|
| h07_dolly | 241 | 35.3 (frame 222) | 71 | 60.7 |
| h07_fly | 238 | 27.0 (frame 28) | 26 | 37.7 |
| h13_dolly | 241 | 30.5 (frame 10) | 119 | 50.6 |
| h13_fly | 238 | 18.3 (frame 50) | 17 | 33.7 |
| h17_dolly | 241 | 27.8 (frame 98) | 106 | 50.1 |
| h17_fly | 238 | 30.8 (frame 22) | 48 | 50.2 |
| h19_dolly | 241 | 26.4 (frame 4) | 44 | 53.3 |
| h19_fly | 238 | 21.9 (frame 53) | 19 | 56.6 |
