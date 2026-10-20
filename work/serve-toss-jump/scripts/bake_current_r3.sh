#!/bin/zsh
set -e
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-toss-jump
tag=$1
H=Male
if [[ $tag == female ]]; then H=Female; fi
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --factory-startup export/preview/HeroBase_${H}_Dressed.blend --python scripts/clear_selected_r3.py -- $tag > r3/revision10/clear_${tag}.log 2>&1
$B -b --factory-startup export/HeroBase_${H}_MatchAnims.blend --python scripts/bake_loco.py -- $tag Serve=serve > r3/revision10/bake_${tag}.log 2>&1
$B -b --factory-startup export/preview/HeroBase_${H}_Dressed.blend --python scripts/bake_loco.py -- $tag Serve=serve > r3/revision10/preview_${tag}.log 2>&1
$B -b --factory-startup export/HeroBase_${H}_MatchAnims.blend --python scripts/export_fbx.py -- $tag Serve > r3/revision10/export_${tag}.log 2>&1
$B -b --factory-startup export/preview/HeroBase_${H}_Dressed.blend --python scripts/penetrate_dj.py -- $tag r3/revision10/pen_${tag}.json Serve > r3/revision10/pen_${tag}.log 2>&1
