#!/bin/zsh
# rebuild.sh <male|female> : pristine blend copy -> solve the Serve (serve_new.py) -> bake -> contact sheets (behind + front, the wind-up and toss frames)
set -e
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-toss-jump
BP=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
B=/Applications/Blender.app/Contents/MacOS/Blender
cd $W
tag=$1; H=$( [ $tag = male ] && echo Male || echo Female )
cp export/pristine/HeroBase_${H}_MatchAnims.blend export/HeroBase_${H}_MatchAnims.blend
$BP scripts/run_serve.py $tag > logs/gen_serve_${tag}.log 2>&1 || { tail -20 logs/gen_serve_${tag}.log; exit 1; }
tail -8 logs/gen_serve_${tag}.log
$B -b --factory-startup export/HeroBase_${H}_MatchAnims.blend --python scripts/bake_loco.py -- $tag Serve=serve > logs/bake_${tag}.log 2>&1
grep -E "BAKED|Error|Traceback" logs/bake_${tag}.log || true
