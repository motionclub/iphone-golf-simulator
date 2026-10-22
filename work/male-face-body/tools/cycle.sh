#!/bin/zsh
# tools/cycle.sh <tag> [set]  : Blender apply+export (heavy.sh) -> install FBX + male C#/shaders into ~/male-face-UnityClone -> Unity mesh count + review renders
set -e
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-face-body
T=$1; SET=${2:-views}; C=$HOME/male-face-UnityClone/Assets
../delegation-2026-10-17/heavy.sh blender /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python tools/apply_m.py -- $T export > logs/apply_$T.log 2>&1
grep -E "NORMALS|EXPORT DONE|APPLY DONE|Error|Traceback" logs/apply_$T.log
cp export/Male_$T.fbx $C/Resources/Tennis/OriginalSeamBlinkFinish/Male.fbx
cp unity/HeroFaceReferenceFit.cs $C/Scripts/Tennis/HeroFaceReferenceFit.cs
for f in HeroFaceSkin.shader TennisCharacter.shader HeroLighting.hlsl; do [[ -f unity/$f ]] && cp unity/$f $C/Resources/Tennis/Shaders/$f; done
[[ -f unity/HeroSkinNormals.cs ]] && cp unity/HeroSkinNormals.cs $C/Scripts/Tennis/HeroSkinNormals.cs
cp unity/Male*.cs $C/Editor/
tools/unity_run.sh GolfArcade.EditorTools.MaleFaceMeshCount.Run meshcount_$T MESH_COUNT_OUT=$PWD/eval/meshcount_$T.txt
cat eval/meshcount_$T.txt
tools/unity_run.sh GolfArcade.EditorTools.MaleFaceReview.Run review_$T FACE_REVIEW_OUT=$PWD/unity_out/$T FACE_REVIEW_SET=$SET
echo CYCLE_DONE $T
