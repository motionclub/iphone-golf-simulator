#!/bin/zsh
# regen.sh <male|female> <walk|runf|runr|runl>...   : generate (numpy), bake into the working blend, render a side + quarter-front sheet into logs/sheets/
set -e
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/frame-rate-60/feet
BP=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
B=/Applications/Blender.app/Contents/MacOS/Blender
cd $W
tag=$1; shift
H=$( [ $tag = male ] && echo Male || echo Female )
specs=()
for c in "$@"; do
  $BP scripts/run_gait.py $c $tag | grep -v "calibrate iter" | tail -6
  case $c in walk) n=Walk;; runf) n=RunForward;; runr) n=RunRight;; runl) n=RunLeft;; esac
  specs+=("$n=$c")
done
$B -b --factory-startup export/HeroBase_${H}_MatchAnims.blend --python scripts/bake_loco.py -- $tag $specs 2>&1 | grep -E "BAKED|Error|Traceback" || true
for c in "$@"; do
  case $c in walk) n=Walk;; runf) n=RunForward;; runr) n=RunRight;; runl) n=RunLeft;; esac
  RES=${RES:-300x400} $B -b --factory-startup export/HeroBase_${H}_MatchAnims.blend --python scripts/render_sheet.py -- $tag $n logs/sheets/${c}_${tag} ${FR:-every:1} ${VIEWS:-side,q_front} 2>&1 | grep -E "SHEET_DONE|Error|Traceback" || true
  python3 scripts/tile_sheet.py logs/sheets/${c}_${tag}_cells.json logs/sheets/${c}_${tag}_${V:-v2}.png ${COLS:-6} "$n $tag ${V:-v2}"
done
