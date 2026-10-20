#!/bin/bash
# close-up cells of the DELIVERABLE blends: both heroes, both feet, side/front/heel/q3, White + Black  -> proof/raw/feet_<g>_<cw>_<R|L>_<view>.png
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/tennis-shoes-fit
B=/Applications/Blender.app/Contents/MacOS/Blender
mkdir -p $W/proof/raw
cd $W
for g in male female; do
  G=$( [ $g = male ] && echo Male || echo Female )
  if [ $g = male ]; then D=1.0; else D=0.82; fi
  for cw in White Black; do
    for foot in R L; do
      VDIST=$D VTZ=0.095 VRES=640,640 $B -b --factory-startup --python scripts/view_blend.py -- export/StandardKit_$G.blend $g $cw proof/raw/feet_${g}_${cw}_${foot} feet$foot --parts shoes,socks 2>&1 | grep -E "Error|Trace|File \"" 
    done
  done
done
echo CELLS_DONE
