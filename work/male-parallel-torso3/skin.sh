#!/bin/bash
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-torso3
export PYTHONPATH=$PWD/../male-micro1i/pylib
for T in "$@"; do /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python rt.py -- data/V_$T.npy r/$T front,back 2>&1 | grep -E "Error|Traceback"; done
