#!/bin/zsh
# the Blender half of the pipeline (headless): build -> measure -> check -> export -> verify -> proofs.   ~6 minutes
set -e
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/hero-dressed
B=/Applications/Blender.app/Contents/MacOS/Blender
cd $W
mkdir -p logs data export proof
for t in male female; do
  G=$(python3 -c "print('$t'.capitalize())")
  $B -b --factory-startup ../match-anim-set/export/HeroBase_${G}_MatchAnims.blend --python scripts/build_dressed.py -- $t > logs/build_$t.log 2>&1
  $B -b --factory-startup ../tennis-shoes-fit/export/StandardKit_${G}.blend --python scripts/dump_kit_source.py -- $t > logs/kitsource_$t.log 2>&1
  $B -b --factory-startup export/HeroBase_${G}_Dressed.blend --python scripts/check_skin.py -- $t > logs/check_skin_$t.log 2>&1
  $B -b --factory-startup export/HeroBase_${G}_Dressed.blend --python scripts/measure_follow.py -- $t gate data/gate3_$t.json > logs/gate3_$t.log 2>&1
  $B -b --factory-startup export/HeroBase_${G}_Dressed.blend --python scripts/measure_follow.py -- $t sweep data/sweep_$t.json > logs/sweep_$t.log 2>&1
  $B -b --factory-startup export/HeroBase_${G}_Dressed.blend --python scripts/measure_follow.py -- $t sole data/sole_$t.json > logs/sole_$t.log 2>&1
  $B -b --factory-startup export/HeroBase_${G}_Dressed.blend --python scripts/export_kit_fbx.py -- $t > logs/export_$t.log 2>&1
  $B -b --factory-startup export/HeroBase_${G}_Dressed.blend --python scripts/dump_kit_poses.py -- $t > logs/kitpose_$t.log 2>&1
  $B -b --factory-startup --python scripts/verify_kit_fbx.py -- $t > logs/verify_kitfbx_$t.log 2>&1
done
python3 scripts/proofs_blender.py > logs/proofs_blender.log 2>&1
echo blender stage done
