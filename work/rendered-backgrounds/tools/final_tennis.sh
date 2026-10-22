#!/bin/bash
# Final tennis verification: all three venues, full shots + perf A/B, gates into proof/<venue>.
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/rendered-backgrounds
for v in resort skyscraper volcano; do
  BG_PERF_AB=1 tools/capture_tennis.sh final/$v $v > logs/final_$v.txt 2>&1
  mkdir -p proof/$v; cp final/$v/${v}_capture.txt proof/$v/after_capture.txt
  python3 tools/gates.py $v before/${v}_1080 final/$v proof/$v/gates.json > proof/$v/gates.txt
done
echo FINAL_TENNIS_DONE
