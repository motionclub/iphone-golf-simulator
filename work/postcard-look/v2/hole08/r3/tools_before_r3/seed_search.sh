#!/bin/bash
# usage: seed_search.sh FIRST LAST  -- builds hole 8 into scratch/seedN with --sea-seed N and runs the verifier's foam / surf / shelf gates; stops at the first full pass
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
B=/Applications/Blender.app/Contents/MacOS/Blender
for sd in $(seq $1 $2); do
  d=$R/work/postcard-look/v2/hole08/scratch/seed$sd; mkdir -p $d
  $B -b --factory-startup --python $R/blender/scripts/hole08_build.py -- --out $d --sea-seed $sd > $d.log 2>&1; rc=$?
  g=$($B -b --factory-startup --python $R/work/postcard-look/v2/gates/tools/run_gate.py -- 8 $d/hole_08.blend g_no_foam_strip,g_surf,g_shelf_thin 2>&1 | grep '^RG' | cut -c1-150 | tr '\n' '|')
  echo "seed $sd build_rc=$rc $g"
  if [ $rc -eq 0 ] && ! echo "$g" | grep -q FAIL; then echo "SEED_OK $sd"; break; fi
done
