#!/bin/zsh
# tools/perf.sh before|after : install that state into the clone, run MaleFacePerf (1920x1080, MSAA 4, 400 frames)
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-face-body
S=$1; C=$HOME/male-face-UnityClone/Assets
if [[ $S == before ]]; then D=unity/before; F=export/before/Male.fbx; else D=unity; F=export/Male_s13.fbx; fi
cp $F $C/Resources/Tennis/OriginalSeamBlinkFinish/Male.fbx; cp $D/HeroFaceReferenceFit.cs $C/Scripts/Tennis/
for f in HeroFaceSkin.shader TennisCharacter.shader HeroLighting.hlsl; do cp $D/$f $C/Resources/Tennis/Shaders/$f; done
cp unity/Male*.cs $C/Editor/
tools/unity_run.sh GolfArcade.EditorTools.MaleFacePerf.Run perf_$S FACE_PERF_OUT=$PWD/eval/perf_$S.txt
cat eval/perf_$S.txt
