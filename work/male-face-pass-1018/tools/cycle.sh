#!/bin/zsh
# tools/cycle.sh <tag> [ENV=VAL ...] : copy the work shaders/scripts into ~/integration-work/face-pass and run MaleAuditRun (AUDIT_SETS default "views")
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work
P=$W/male-face-pass-1018; C=$HOME/integration-work/face-pass/Assets
tag=$1; shift
cp $P/unity/{HeroFaceSkin.shader,TennisCharacter.shader,HeroLighting.hlsl} $C/Resources/Tennis/Shaders/
cp $P/unity/{MaleFaceFinish.cs,MatchHeroLook.cs,HeroFaceReferenceFit.cs} $C/Scripts/Tennis/
cp $P/unity/{MaleFaceReview.cs,MaleAuditRun.cs} $C/Editor/
export AUDIT_SETS=views
for kv in "$@"; do export "$kv"; done
export GOLF_MUTE=1 AUDIT_OUT=$P/unity_out/$tag
$W/delegation-2026-10-17/heavy.sh unity /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -projectPath $HOME/integration-work/face-pass \
  -executeMethod GolfArcade.EditorTools.MaleAuditRun.Run -logFile $P/logs/$tag.log
echo "exit $? $tag"; ls $AUDIT_OUT; cat $AUDIT_OUT/errors.txt 2>/dev/null | head -5; grep -m3 "error CS\|Shader error" $P/logs/$tag.log
