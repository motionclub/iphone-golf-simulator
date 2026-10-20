#!/bin/zsh
# Rebuild every deliverable of work/match-anim-set from the stage blends (export/_stage/*_rig.blend and data/*.json, built once by
# build_rig.py -> racket_info.py -> leftgrip.py -> fix_bones.py -> foot_ground.py).  ~25 minutes on an M-series Mac.
set -e
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set
B=/Applications/Blender.app/Contents/MacOS/Blender
BP=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
cd $W
# 1. bake the 16 clips on both heroes
$B -b --factory-startup export/_stage/Male_rig.blend --python scripts/bake.py -- male &
$B -b --factory-startup export/_stage/Female_rig.blend --python scripts/bake.py -- female &
wait
# 2. measurements from the traces and from the evaluated meshes
for h in male female; do $BP scripts/verify_data.py $h; done
$B -b --factory-startup export/HeroBase_Male_MatchAnims.blend --python scripts/verify_blend.py -- male &
$B -b --factory-startup export/HeroBase_Female_MatchAnims.blend --python scripts/verify_blend.py -- female &
wait
# 3. FBX per clip + round trip
rm -rf export/fbx
$B -b --factory-startup export/HeroBase_Male_MatchAnims.blend --python scripts/export_fbx.py -- male &
$B -b --factory-startup export/HeroBase_Female_MatchAnims.blend --python scripts/export_fbx.py -- female &
wait
for h in male female; do $B -b --factory-startup --python scripts/verify_fbx.py -- ref $h; done
$B -b --factory-startup --python scripts/verify_fbx.py -- check male &
$B -b --factory-startup --python scripts/verify_fbx.py -- check female &
wait
# 4. proofs
rm -rf proof/_cells proof/_frames proof/_frames_annotated proof/_check
$B -b --factory-startup export/HeroBase_Male_MatchAnims.blend --python scripts/proofs.py -- male cells &
$B -b --factory-startup export/HeroBase_Female_MatchAnims.blend --python scripts/proofs.py -- female cells &
wait
python3 scripts/sheets.py
$B -b --factory-startup export/HeroBase_Male_MatchAnims.blend --python scripts/proofs.py -- male frames &
$B -b --factory-startup export/HeroBase_Female_MatchAnims.blend --python scripts/proofs.py -- female frames &
wait
python3 scripts/annotate.py male
python3 scripts/annotate.py female
$B -b --factory-startup --python scripts/proofs.py -- male encode &
$B -b --factory-startup --python scripts/proofs.py -- female encode &
wait
$B -b --factory-startup --python scripts/check_video.py -- male female
# 5. repo integrity + roll-up
python3 scripts/verify_repo.py
python3 scripts/finalize.py
