#!/bin/bash
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/rendered-backgrounds
BG_PERF_AB=1 tools/capture_golf.sh final/golf2 10,17,21,22,23 > logs/final_golf2.txt 2>&1
for h in 10 17 21 22 23; do cp final/golf2/hole${h}_*.png final/golf/ ; cp final/golf2/hole${h}_capture.txt final/golf/; cp final/golf2/hole${h}_capture.txt proof/golf/hole${h}_capture.txt
  python3 tools/gates.py hole$h before/golf_all final/golf proof/golf/hole${h}_gates.json > proof/golf/hole${h}_gates.txt 2>&1; done
for h in 07 08 09 12 13 14 15 16 18 19 20; do python3 tools/gates.py hole$h before/golf_all final/golf proof/golf/hole${h}_gates.json > proof/golf/hole${h}_gates.txt 2>&1; done
tools/final_tennis.sh
echo FINAL_FIX_DONE
