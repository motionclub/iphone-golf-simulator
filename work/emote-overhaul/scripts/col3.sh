#!/bin/zsh
# col3.sh <male|female> <clip> <frames-spec> [out.json] : the independent penetration gate (collide3.py: evaluated skin, single-layer, signed) on the dressed hero
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
tag=$1; clip=$2; spec=$3; out=$4
H=$( [ $tag = male ] && echo Male || echo Female )
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup $R/work/hero-dressed/export/HeroBase_${H}_Dressed.blend --python $R/work/emote-overhaul/scripts/collide3.py -- $tag $clip "$spec" $out 2>&1 | grep -E "^F[ 0-9]|^      |MAX_PEN|COLLIDE3_DONE|Error|Traceback|File |line [0-9]+"
