#!/bin/zsh
# build_all2.sh : OVERHAUL build - solve the three new clips on both heroes (-> work/emotes/data/gen_*.npz), bake them into the working blends (work/emotes/export/blend, in place:
# the intro clips stay), export the 6 FBX into work/emotes/export/fbx (the EmoteWire source).  rollback/ holds the pre-overhaul FBX / npz / blends.
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
W=$R/work/emotes
J=$R/work/emote-overhaul
BP=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
B=/Applications/Blender.app/Contents/MacOS/Blender
mkdir -p $J/rollback/blend
for H in Male Female; do [ -f $J/rollback/blend/HeroBase_${H}_Emotes.blend ] || cp $W/export/blend/HeroBase_${H}_Emotes.blend $J/rollback/blend/; done
[ -f $J/rollback/data_fbx_male.json ] || cp $W/data/fbx_male.json $J/rollback/data_fbx_male.json
[ -f $J/rollback/data_fbx_female.json ] || cp $W/data/fbx_female.json $J/rollback/data_fbx_female.json
cd $W
for h in male female; do $B -b --factory-startup --python $J/scripts/emo_solve_all2.py -- $h 2>&1 | grep -E "SOLVED|Error|Traceback|File |line [0-9]+"; done
for h in male female; do
  H=$( [ $h = male ] && echo Male || echo Female )
  $B -b --factory-startup export/blend/HeroBase_${H}_Emotes.blend --python $J/scripts/bake_emotes2.py -- $h 2>&1 | grep -E "BAKE_DONE|Error|Traceback|File |line [0-9]+"
  $B -b --factory-startup export/blend/HeroBase_${H}_Emotes.blend --python $J/scripts/export_emotes2.py -- $h 2>&1 | grep -E "FBX_DONE|Error|Traceback|File |line [0-9]+"
done
