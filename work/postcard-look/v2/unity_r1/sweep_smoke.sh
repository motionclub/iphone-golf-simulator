#!/bin/bash
# usage: sweep_smoke.sh <label-prefix> "r,g,b,gain,emission,lit,fogshare" ...   (bash, not zsh)
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
p="$1"; shift; i=0
for v in "$@"; do
  i=$((i+1))
  bash $R/work/postcard-look/v2/runtime/run_smoke.sh ${p}$i GOLF_LOOK_TUNE=1 GOLF_LOOK_SMOKE=$v > $R/work/postcard-look/v2/unity_r1/run_${p}$i.log 2>&1
  echo "== ${p}$i  $v"; grep -E "INFO: SMOKE|GATE: SMOKE" $R/work/postcard-look/v2/runtime/smoke_${p}$i.txt | sed -E 's/\(_Color.*_FogShare/(FogShare/' | cut -c1-330
done
