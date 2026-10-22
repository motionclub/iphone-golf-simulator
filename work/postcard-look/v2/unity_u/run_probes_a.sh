#!/bin/bash
# AREA U: 5 probe runs of the CURRENT tree (K2 FigureExposure in place) -> golfer gates x5, hole-8 textured x5
R="$(cd "$(dirname "$0")/../../../.." && pwd)"; cd "$R"
for l in ua1 ua2 ua3 ua4 ua5; do
  bash work/postcard-look/v2/calibrate/tools/run_probe.sh $l > work/postcard-look/v2/unity_u/probe_$l.out 2>&1
done
echo done > work/postcard-look/v2/unity_u/probes_a_done.flag
