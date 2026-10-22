#!/bin/zsh
# tools/run.sh <tag> : one Unity launch in ~/integration-work/audit-male (clone of today's Unity/) -> unity_out/<tag>
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work
A=$W/male-audit-1018
export GOLF_MUTE=1 AUDIT_OUT=$A/unity_out/$1
$W/delegation-2026-10-17/heavy.sh unity /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -projectPath $HOME/integration-work/audit-male \
  -executeMethod GolfArcade.EditorTools.MaleAuditRun.Run -logFile $A/logs/$1.log
echo "exit $?"
