#!/bin/zsh
# iterate.sh <male|female> : rebuild (solve + bake both blends), print the solver summary, run the dressed collision check
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-dip-jump
tag=$1; H=$( [ $tag = male ] && echo Male || echo Female )
zsh scripts/rebuild_dj.sh $tag 2>&1 | grep -v "^saved" | tail -8
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup export/preview/HeroBase_${H}_Dressed.blend --python scripts/penetrate_dj.py -- $tag data/pen_dj_$tag.json 2>&1 | grep -E "PEN|^   \("
