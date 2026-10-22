#!/bin/zsh
# finish_build.sh : rebuild the five clips for both heroes, verify, export the FBX, write the table the Unity wiring reads.
set -e
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-and-feet
BP=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
B=/Applications/Blender.app/Contents/MacOS/Blender
cd $W
scripts/build_all.sh
for t in male female; do H=$( [ $t = male ] && echo Male || echo Female ); $B -b --factory-startup export/HeroBase_${H}_MatchAnims.blend --python scripts/export_fbx.py -- $t > logs/fbx_${t}.log 2>&1 & done; wait
grep -h "FBX_DONE\|Error" logs/fbx_*.log
$BP scripts/make_table.py > /dev/null
shasum -a 256 export/fbx/*.fbx > data/fbx_sha256.txt
echo finished
