#!/bin/zsh
# tools/review_state.sh <tag> <Female.fbx> <shader dir with HeroFaceSkin/TennisCharacter/HeroLighting> [set]  -> unity_out/<tag>
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-face-shader; C=$HOME/female-face-UnityClone/Assets
cp "$2" $C/Resources/Tennis/OriginalSeamBlinkFinish/Female.fbx
D=$3; [[ -f $D ]] && D=$(dirname $D)
cp $D/HeroFaceSkin.shader $D/TennisCharacter.shader $D/HeroLighting.hlsl $C/Resources/Tennis/Shaders/
cp $W/unity/FemaleFaceReview.cs $W/unity/FemaleFacePerf.cs $C/Editor/
if [[ "$4" == perf ]]; then $W/tools/unity_run.sh GolfArcade.EditorTools.FemaleFacePerf.Run perf_$1 FACE_PERF_OUT=$W/eval/perf_$1.txt
else $W/tools/unity_run.sh GolfArcade.EditorTools.FemaleFaceReview.Run review_$1 FACE_REVIEW_OUT=$W/unity_out/$1 FACE_REVIEW_SET=${4:-views}; fi
