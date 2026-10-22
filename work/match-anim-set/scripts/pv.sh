#!/bin/zsh
# preview a clip: pv.sh <male|female> <Clip> [every:N | t1,t2,...] [views] [cols]
# writes $SP/pv/<hero>_<Clip>_*.png (strip of the behind view, and of the side view) - read them with the image viewer
HERO=$1; CLIP=$2; SPEC=${3:-every:2}; VIEWS=${4:-behind,side}; COLS=${5:-10}
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
SP=/private/tmp/claude-501/-Users-adnanyonathan-Documents-Codex-2026-09-20-wh-outputs-iphone-golf-simulator/492aef3b-290a-4546-b8c6-d851d3c6cda6/scratchpad/pv
mkdir -p $SP; setopt null_glob; rm -f $SP/${HERO}_${CLIP}_*
H=$(python3 -c "print('$HERO'.capitalize())")
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup $REPO/work/match-anim-set/export/_stage/${H}_rig.blend --python $REPO/work/match-anim-set/scripts/anim_run.py -- $HERO sheet $CLIP $SP/${HERO}_${CLIP} $SPEC $VIEWS 2>&1 | grep -E "^CLIP|SHEET_DONE|Error|Traceback|line [0-9]+" | head -12
if [[ $VIEWS == *","* ]]; then
  python3 $REPO/work/match-anim-set/scripts/tile.py $SP/${HERO}_${CLIP}_sheet.json $SP/${HERO}_${CLIP}_behind.png $COLS behind
  python3 $REPO/work/match-anim-set/scripts/tile.py $SP/${HERO}_${CLIP}_sheet.json $SP/${HERO}_${CLIP}_side.png $COLS side
else
  python3 $REPO/work/match-anim-set/scripts/tile.py $SP/${HERO}_${CLIP}_sheet.json $SP/${HERO}_${CLIP}_one.png $COLS behind
fi
