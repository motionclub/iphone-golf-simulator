#!/bin/zsh
# rr2.sh <male|female> <clip> <frames-spec> <views> <cols> [WxH] : render poses of an OVERHAUL clip (emo_clips2) on the dressed hero and tile them -> $SP/<clip>_<tag>.png
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
SP=/private/tmp/claude-501/-Users-adnanyonathan-Documents-Codex-2026-09-20-wh-outputs-iphone-golf-simulator/eea79e4e-5588-4d3e-bf82-e62668519187/scratchpad/rr
mkdir -p $SP; tag=$1; clip=$2; spec=$3; views=$4; cols=$5; res=${6:-360x480}
H=$( [ $tag = male ] && echo Male || echo Female )
setopt null_glob; rm -f $SP/${clip}_${tag}_*.png
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup $R/work/hero-dressed/export/HeroBase_${H}_Dressed.blend --python $R/work/emote-overhaul/scripts/emo_render2.py -- $tag $clip "$spec" $views $SP $res 2>&1 | grep -E "RENDERED|Error|Traceback|line [0-9]+|File " | head -20
python3 $R/work/emotes/scripts/emo_tile.py $SP/${clip}_${tag}_cells.json $SP/${clip}_${tag}.png $cols
