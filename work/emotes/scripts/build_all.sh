#!/bin/zsh
# build_all.sh : solve every frame of the six clips on both heroes, bake them into the working blends, export the 12 FBX (about 2 minutes).
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
W=$R/work/emotes
BP=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
B=/Applications/Blender.app/Contents/MacOS/Blender
cd $W
for h in male female; do $BP scripts/emo_solve_all.py $h 2>&1 | grep -E "SOLVED|Error|Traceback"; done
for h in male female; do
  H=$( [ $h = male ] && echo Male || echo Female )
  cp $R/work/match-anim-set/export/HeroBase_${H}_MatchAnims.blend export/blend/HeroBase_${H}_Emotes.blend
  $B -b --factory-startup export/blend/HeroBase_${H}_Emotes.blend --python scripts/bake_emotes.py -- $h 2>&1 | grep -E "BAKE_DONE|Error|Traceback"
  $B -b --factory-startup export/blend/HeroBase_${H}_Emotes.blend --python scripts/export_emotes.py -- $h 2>&1 | grep -E "FBX_DONE|Error|Traceback"
done
