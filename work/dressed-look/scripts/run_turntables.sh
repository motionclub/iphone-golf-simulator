#!/bin/zsh
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/dressed-look
BL=/Applications/Blender.app/Contents/MacOS/Blender
for pair in male:Male female:Female; do
  t=${pair%%:*}; N=${pair#*:}
  $BL -b $W/export/HeroBase_${N}_Dressed.blend --python $W/scripts/render_turntable.py -- $t $W/proof/Turntable_${N}_White.mp4 --frames 240 --res 1080 --samples 48 2>&1 | grep -E "TURNTABLE_DONE|Error|Traceback"
done
echo TURNTABLES_ALL_DONE
