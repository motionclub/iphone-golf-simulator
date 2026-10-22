#!/bin/zsh
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-face-body
while pgrep -f "tools/before.sh" >/dev/null; do sleep 15; done
../delegation-2026-10-17/heavy.sh blender /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python tools/snap_m.py -- ../jaw-sculpt-2026-10-12/Male_JawSculpt.blend $PWD/source_male_1017.npz > logs/snap.log 2>&1
grep SNAP logs/snap.log
