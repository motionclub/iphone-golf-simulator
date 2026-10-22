#!/bin/zsh
# build_and_check.sh : rebuild the Serve for both heroes (serve_new.py + run_serve.py splice) -> bake -> measure + racket-in-body + gates 4-6 -> offline toss model
set -e
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-toss-jump
B=/Applications/Blender.app/Contents/MacOS/Blender
for t in male female; do zsh scripts/rebuild.sh $t | tail -1; done
for t in male female; do H=$( [ $t = male ] && echo Male || echo Female )
  $B -b --factory-startup export/HeroBase_${H}_MatchAnims.blend --python scripts/measure.py -- $t data/measure_final_$t.json >/dev/null 2>&1 &
  $B -b --factory-startup export/HeroBase_${H}_MatchAnims.blend --python scripts/penetrate.py -- $t data/pen_final_$t.json > logs/pen_final_$t.log 2>&1 &
  $B -b --factory-startup export/HeroBase_${H}_MatchAnims.blend --python scripts/sim_toss.py -- $t 2>&1 | grep "SIM Serve" &
done; wait
python3 scripts/check_blender_gates.py
