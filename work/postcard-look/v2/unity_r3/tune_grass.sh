#!/bin/bash
# usage: tune_grass.sh <prefix> <hole> "<HOLETINT spec>" ...   one Unity run per spec (grass board of one hole only, ~1 min)
R="$(cd "$(dirname "$0")/../../../.." && pwd)"; pre="$1"; hole="$2"; shift; shift; i=0
for t in "$@"; do i=$((i+1)); bash "$R/work/postcard-look/v2/runtime/run_smoke.sh" "${pre}$i" GOLF_LOOK_TUNE=1 GOLF_LOOK_GRASS_HOLE="$hole" GOLF_LOOK_HOLETINT="$t" > /dev/null 2>&1; echo "== $t ($pre$i)"; grep -E "GRASS_HUE_GAMEVIEW|GRASS_NO_CLIP|^INFO: GRASS" "$R/work/postcard-look/v2/runtime/smoke_${pre}$i.txt" | grep -v "^\[" | cut -c1-420; done
