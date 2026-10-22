#!/bin/zsh
# sheet.sh <male|female> <name> <frames> <views> [cols] : render a sheet of the baked Serve from export/ into sheets/<name>_<tag>.png
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-toss-arm
B=/Applications/Blender.app/Contents/MacOS/Blender
cd $W; mkdir -p sheets/tmp
tag=$1; name=$2; frames=$3; views=$4; cols=${5:-6}
H=$( [ $tag = male ] && echo Male || echo Female )
RES=${RES:-300x400} $B -b --factory-startup export/HeroBase_${H}_MatchAnims.blend --python scripts/render_sheet.py -- $tag Serve sheets/tmp/${name}_${tag} $frames $views 2>&1 | grep -E "SHEET_DONE|Error|Traceback"
python3 scripts/tile_sheet.py sheets/tmp/${name}_${tag}_cells.json sheets/${name}_${tag}.png $cols "$tag Serve $name"
