#!/bin/zsh
# usage: ./pipeline_final.sh <params.json> [tag=final]
set -e
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-hands-fingers
P=$1; T=${2:-final}
./py.sh mkc.py $T $P
./blend.sh start/start_arms_candidate.blend write_blend_f.py data/cand_$T.npz export/HeroBase_Female_hands_candidate.blend | grep -E "WROTE"
./blend.sh export/HeroBase_Female_hands_candidate.blend dump_mesh.py data/dump_final.npz | grep DUMP
./blend.sh export/HeroBase_Female_hands_candidate.blend verify_blend_f.py data/mesh_start.npz data/verify_final.json | grep -c VERIFY
./py.sh audit_f.py data/dump_final.npz data/audit_final.json
./py.sh checks_f.py $P $T data/verify_final.json data/audit_final.json checks.json | tail -60
./py.sh make_delta.py data/cand_$T.npz export/hands_delta.npz
./blend.sh start/start_arms_candidate.blend merge_hands_delta.py export/hands_delta.npz data/merge_test.blend | grep MERGED
./blend.sh data/merge_test.blend dump_mesh.py data/dump_merge_test.npz | grep DUMP
./blend.sh export/HeroBase_Female_hands_candidate.blend export_fbx_f.py | tail -3
./blend.sh start/start_arms_candidate.blend fbx_verify_f.py | grep FBXV
shasum -a 256 export/HeroBase_Female_hands_candidate.blend export/HeroBase_Female_Body_hands.fbx export/hands_delta.npz start/start_arms_candidate.blend ../../ArtDir/hero/base_lock/blender/HeroBase_Female.blend
