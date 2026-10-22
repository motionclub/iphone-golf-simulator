#!/bin/zsh
set -e
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-toss-jump
B=/Applications/Blender.app/Contents/MacOS/Blender
cd $W
for tag in male female; do
 H=$([[ $tag = male ]] && echo Male || echo Female)
 zsh scripts/rebuild_dj.sh $tag > logs/rebuild_${tag}.log 2>&1
 $B -b --factory-startup export/HeroBase_${H}_MatchAnims.blend --python scripts/export_fbx.py -- $tag Serve > logs/export_${tag}.log 2>&1
 $B -b --factory-startup --python scripts/trace_fbx.py -- $W/export/fbx/${H}_Serve.fbx $tag $W/data/candidate_${tag}.json > logs/trace_${tag}.log 2>&1
 $B -b --factory-startup export/preview/HeroBase_${H}_Dressed.blend --python scripts/penetrate_dj.py -- $tag $W/data/pen_candidate_${tag}.json > logs/pen_${tag}.log 2>&1
 $B -b --factory-startup ../serve-dip-jump/export/preview/HeroBase_${H}_Dressed.blend --python scripts/penetrate_dj.py -- $tag $W/data/pen_baseline_${tag}.json > logs/pen_base_${tag}.log 2>&1
 done

$B -b --factory-startup --python scripts/contact_scale_audit.py > logs/contact_scale.log 2>&1
python3 scripts/check_gates.py > logs/gates_final_fbx.log
