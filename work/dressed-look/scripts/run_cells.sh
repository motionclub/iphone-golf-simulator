#!/bin/zsh
# full-resolution proof cells for the four sheets (sequential: one EEVEE job at a time)
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/dressed-look
BL=/Applications/Blender.app/Contents/MacOS/Blender
mkdir -p $W/proof/raw
for pair in male:Male female:Female; do
  t=${pair%%:*}; N=${pair#*:}
  for c in White Black; do
    $BL -b $W/export/HeroBase_${N}_Dressed.blend --python $W/scripts/render_dressed.py -- $t $c $W/proof/raw --body source 2>&1 | grep -E "bbox|RENDER_DONE|Error|Traceback"
  done
done
echo CELLS_ALL_DONE
