#!/bin/zsh
# iss.sh <hero> <Clip...>  : list problem frames
HERO=$1; shift
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
H=$(python3 -c "print('$HERO'.capitalize())")
for C in "$@"; do
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup $REPO/work/match-anim-set/export/_stage/${H}_rig.blend --python $REPO/work/match-anim-set/scripts/anim_run.py -- $HERO issues $C x 2>&1 | grep -E "^  t=|^ISSUES|Error|Traceback|line [0-9]+"
done
