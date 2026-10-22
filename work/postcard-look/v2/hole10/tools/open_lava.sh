#!/bin/bash
# open_lava.sh STAGE_BLEND LOGFILE : mask renders of the staged blend (and, once, of round1/hole_10_round1.blend) + the H_OPEN_LAVA gate line
S=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/hole10
B=/Applications/Blender.app/Contents/MacOS/Blender
mk() { # blend outdir
  rm -rf "$2"; mkdir -p "$2"
  $B -b "$1" --python $S/tools/render_views.py -- --shots $S/landmarks_with_aerial.json --out "$2" --only aerial,aerial2,aerial3,aerial4 --res 1600x900 --mask --samples 1 > /dev/null 2>&1
  python3 $S/tools/mask_stats.py "$2" "$2/shares.json" > "$2/shares.txt"
}
[ -f $S/round1/mask/shares.json ] || mk $S/round1/hole_10_round1.blend $S/round1/mask
[ -f $S/round2/mask/shares.json ] || mk $S/round2/hole_10_round2.blend $S/round2/mask
mk "$1" $S/stage_masks
cat $S/round1/mask/shares.txt | sed 's/^/round1 /' > "$2"
cat $S/round2/mask/shares.txt | sed 's/^/round2 /' >> "$2"
cat $S/stage_masks/shares.txt | sed 's/^/stage  /' >> "$2"
python3 $S/tools/open_lava_gate.py $S/stage_masks/shares.json $S/round1/mask/shares.json $S/round2/mask/shares.json | tee -a "$2"
