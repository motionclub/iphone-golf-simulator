#!/bin/bash
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
H=$R/work/postcard-look/v2/hole08/r6/yaw
k=$1
mkdir -p $H/k$k
HOLE08_YAW=$k /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python $R/blender/scripts/hole08_build.py -- --out $H/k$k > $H/k$k/build.log 2>&1
echo "k$k exit $?" 
