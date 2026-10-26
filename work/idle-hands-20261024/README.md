# idle-hands-20261024
Plaza idle hands fix + proof. Results and root causes: GATE_RESULTS.md.
Re-run: `run_capture.sh <label>` (SEXES="0 1" by default) syncs Unity/Assets/Scripts/Hub/HubHeroAnimator.cs into ~/unity-clones/idle-turnaround,
runs IdleTurnaroundCapture per sex through heavy.sh (GOLF_MUTE=1, CHARACTER_LOD_FORCE=0), then builds the 5 sheets.
`python3 compare.py <before shots> <after shots> <out>` builds the before/after sheets. Rounds r1-r6 were iterations; r7 = shipped values.
