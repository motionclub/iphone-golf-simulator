#!/bin/zsh
# rr.sh <male|female> <clip> <frames-spec> <views> <cols> [WxH]   : render poses of a clip on the dressed hero and tile them -> $SP/<clip>_<tag>.png
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
SP=/private/tmp/claude-501/-Users-adnanyonathan-Documents-Codex-2026-09-20-wh-outputs-iphone-golf-simulator/840886d1-2e8b-483d-a69e-a5f66b9907fd/scratchpad/rr
mkdir -p $SP; tag=$1; clip=$2; spec=$3; views=$4; cols=$5; res=${6:-360x480}
H=$( [ $tag = male ] && echo Male || echo Female )
setopt null_glob; rm -f $SP/${clip}_${tag}_*.png
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup $R/work/hero-dressed/export/HeroBase_${H}_Dressed.blend --python $R/work/emotes/scripts/emo_render.py -- $tag $clip "$spec" $views $SP $res 2>&1 | grep -E "RENDERED|Error|Traceback|line [0-9]+|File " | head -20
python3 $R/work/emotes/scripts/emo_tile.py $SP/${clip}_${tag}_cells.json $SP/${clip}_${tag}.png $cols
