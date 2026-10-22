#!/bin/zsh
# run_pickup.sh <male|female> : build Emote_PickUp (free) and print the hand/trunk diagnostics
cd "$(dirname $0)/scripts"
HB=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/delegation-2026-10-17/heavy.sh
T=$1; BL=../blend/$([ $T = male ] && echo Male || echo Female)_Std.blend
$HB blender /Applications/Blender.app/Contents/MacOS/Blender -b $BL --python build.py -- $T clip_pickup none 2>&1 | grep -E "REPLAY|INFO |MIN_BODY|BUILD_DONE|Error|Traceback|line [0-9]"
