#!/bin/bash
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
H=$R/work/postcard-look/v2/hole08/r6
k=$1
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python $H/tools/shots.py -- $H/yaw/k$k/hole_08.blend $H/yaw/k$k/img $H/../landmarks.json hole08_arch > $H/yaw/k$k/shot.log 2>&1
echo "shot k$k $?"
