#!/bin/zsh
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
tag=$1; clip=$2; spec=$3; out=$4
H=$( [ $tag = male ] && echo Male || echo Female )
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup $R/work/hero-dressed/export/HeroBase_${H}_Dressed.blend --python $R/work/emote-overhaul/scripts/collide4.py -- $tag $clip "$spec" $out 2>&1 | grep -E "^F[ 0-9]|MAX_ENC|COLLIDE4_DONE|Error|Traceback|File |line [0-9]+"
