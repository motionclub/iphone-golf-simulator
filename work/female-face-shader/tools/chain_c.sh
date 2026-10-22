#!/bin/zsh
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-face-shader
B=/Applications/Blender.app/Contents/MacOS/Blender
(cd tools; $B -b --factory-startup --python export_female.py -- ../scratch/s13.blend ../export/Female_s13.fbx 2>&1 | grep DONE; $B -b --factory-startup --python measure.py -- ../scratch/s13.blend s13 2>&1 | grep DONE)
cp scratch/s13.blend export/Female_FaceShader_s13.blend
cp export/Female_s13.fbx ~/female-face-UnityClone/Assets/Resources/Tennis/OriginalSeamBlinkFinish/Female.fbx
tools/unity_run.sh GolfArcade.EditorTools.FemaleFaceMeshCount.Run count_s13 MESH_COUNT_OUT=$PWD/eval/meshcount_s13.txt >/dev/null; cat eval/meshcount_s13.txt
tools/review_state.sh final export/Female_s13.fbx unity views | tail -1
tools/review_state.sh final_rig export/Female_s13.fbx unity rig | tail -1
tools/review_state.sh final_tones export/Female_s13.fbx unity tones | tail -1
tools/native.sh final 2>&1 | tail -8
echo CHAIN_C_DONE
