#!/bin/zsh
# tools/review.sh <outtag> <set> [set ...] : copy male C#/shaders/editor tools into the clone (FBX stays) and run MaleFaceReview per set
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-face-body
T=$1; shift; C=$HOME/male-face-UnityClone/Assets
cp unity/HeroFaceReferenceFit.cs $C/Scripts/Tennis/HeroFaceReferenceFit.cs
for f in HeroFaceSkin.shader TennisCharacter.shader HeroLighting.hlsl; do cp unity/$f $C/Resources/Tennis/Shaders/$f; done
cp unity/Male*.cs $C/Editor/
for S in "$@"; do
  tools/unity_run.sh GolfArcade.EditorTools.MaleFaceReview.Run review_${T}_$S FACE_REVIEW_OUT=$PWD/unity_out/${T}_$S FACE_REVIEW_SET=$S
done
echo REVIEW_DONE $T
