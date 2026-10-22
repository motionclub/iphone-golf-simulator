#!/bin/bash
# usage: tune_tints.sh <prefix> "r,g,b" "r,g,b" ...   (GolfLookSmoke TUNE: Crater + smoke boards only, tint override in memory)
R="$(cd "$(dirname "$0")/../../../.." && pwd)"; pre="$1"; shift; i=0
for t in "$@"; do i=$((i+1)); bash "$R/work/postcard-look/v2/runtime/run_smoke.sh" "${pre}$i" GOLF_LOOK_TUNE=1 GOLF_LOOK_BASALT_TINT="$t" > /dev/null 2>&1; echo "== tint $t ($pre$i)"; grep -E "BASALT_NOT_GREEN|BASALT_RENDERS_DARK|BASALT_GLOW_ORANGE" "$R/work/postcard-look/v2/runtime/smoke_${pre}$i.txt" | grep -v "^\[" | cut -c1-330; done
