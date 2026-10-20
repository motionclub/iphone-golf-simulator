#!/bin/bash
# usage: run3.sh <tag> '<json overrides for form3a.py>' : solve + evaluate (gate metric, sil, depth, creases) + skin render + closeups
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-torso3
export PYTHONPATH=$PWD/../male-micro1i/pylib
B=/Applications/Blender.app/Contents/MacOS/Blender; PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
T=$1; $PY form3a.py $T "${2:-{\}}" 2>&1 | grep -v "^  iter" | tail -6
./evq3.sh $T
