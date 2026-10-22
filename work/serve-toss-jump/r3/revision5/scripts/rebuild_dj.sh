#!/bin/zsh
# rebuild_dj.sh <male|female> : solve the Serve (serve_dj.py / run_dj.py) -> bake into the EXPORT blend (pristine copy) and into the dressed PREVIEW blend (kit + racket 1.3x for renders / checks)
set -e
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-toss-jump
BP=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
B=/Applications/Blender.app/Contents/MacOS/Blender
cd $W
tag=$1; H=$( [ $tag = male ] && echo Male || echo Female )
cp export/pristine/HeroBase_${H}_MatchAnims.blend export/HeroBase_${H}_MatchAnims.blend
cp ../hero-dressed/export/HeroBase_${H}_Dressed.blend export/preview/HeroBase_${H}_Dressed.blend
$BP scripts/run_dj.py $tag > logs/gen_serve_${tag}.log 2>&1 || { tail -30 logs/gen_serve_${tag}.log; exit 1; }
tail -9 logs/gen_serve_${tag}.log
$BP scripts/smooth_right.py $tag >> logs/gen_serve_${tag}.log 2>&1
$BP scripts/smooth_path_r3.py $tag >> logs/gen_serve_${tag}.log 2>&1
$BP scripts/limit_wrist_r3.py $tag >> logs/gen_serve_${tag}.log 2>&1
$B -b --factory-startup export/preview/HeroBase_${H}_Dressed.blend --python scripts/clear_selected_r3.py -- $tag > logs/clear_selected_${tag}.log 2>&1
$B -b --factory-startup export/HeroBase_${H}_MatchAnims.blend --python scripts/bake_loco.py -- $tag Serve=serve > logs/bake_${tag}.log 2>&1
$B -b --factory-startup export/preview/HeroBase_${H}_Dressed.blend --python scripts/bake_loco.py -- $tag Serve=serve > logs/bake_prev_${tag}.log 2>&1
grep -E "BAKED|Error|Traceback" logs/bake_${tag}.log logs/bake_prev_${tag}.log || true
