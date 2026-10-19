#!/bin/bash
# After final_tennis.sh: all 16 golf holes (before + after) and the hub, gates into proof/.
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/rendered-backgrounds
while pgrep -f final_tennis.sh >/dev/null; do sleep 10; done
H=7,8,9,12,15,13,14,17,18,19,20,10,16,21,22,23
RENDERED_SKY=0 tools/capture_golf.sh before/golf_all $H > logs/final_golf_before.txt 2>&1
BG_PERF_AB=1 tools/capture_golf.sh final/golf $H > logs/final_golf.txt 2>&1
mkdir -p proof/golf
for h in ${H//,/ }; do hh=$(printf "%02d" $h); cp final/golf/hole${hh}_capture.txt proof/golf/hole${hh}_capture.txt 2>/dev/null
  python3 tools/gates.py hole$hh before/golf_all final/golf proof/golf/hole${hh}_gates.json > proof/golf/hole${hh}_gates.txt 2>&1; done
BG_PERF_AB=1 tools/capture_hub.sh final/hub > logs/final_hub.txt 2>&1
mkdir -p proof/hub; cp final/hub/hub_capture.txt proof/hub/after_capture.txt; python3 tools/gates.py hub before/hub_1080 final/hub proof/hub/gates.json > proof/hub/gates.txt
echo FINAL_REST_DONE
