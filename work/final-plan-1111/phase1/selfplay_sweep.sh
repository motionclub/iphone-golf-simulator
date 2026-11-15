#!/bin/bash
# selfplay_sweep.sh label "ENV=.. ENV=.." ...: real-game self-play (ZTennisFlightPlay.SelfPlay) per setting, on the dev project copy.
cd "$(dirname "$0")/.."
while [ $# -ge 2 ]; do
  label=$1; envs=$2; shift 2
  out=$PWD/phase1/selfplay/$label; mkdir -p "$out"; : > "$out/self_play.txt"
  env CLONE=final-plan-dev FUN_OUT="$out" $envs ./utest.sh selfplay-$label PlayMode "ZTennisFlightPlay.SelfPlay" 2>&1 | sed -n 1,2p
  echo "#### $label ($envs)"; grep -E "^==|points|WINNER|peak height|hit to hit" "$out/self_play.txt"
done
