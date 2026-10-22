#!/bin/bash
# AREA U final Unity evidence on the FINAL code: staged importcheck, installed importcheck, smoke, and 5 probe runs (golfer gates twice+, hole-8 textured x5)
R="$(cd "$(dirname "$0")/../../../.." && pwd)"; cd "$R"
V=work/postcard-look/v2
bash $V/unity_u/run_importcheck_staged.sh us2 > $V/unity_u/importcheck_us2.run.txt 2>&1
bash $V/runtime/run_importcheck.sh u3 > $V/unity_u/importcheck_u3.run.txt 2>&1
bash $V/runtime/run_smoke.sh u3 > $V/unity_u/smoke_u3.run.txt 2>&1
for l in uf1 uf2 uf3 uf4 uf5; do bash $V/calibrate/tools/run_probe.sh $l > $V/unity_u/probe_$l.out 2>&1; done
echo done > $V/unity_u/final_unity_done.flag
