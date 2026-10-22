#!/bin/zsh
# tools/unity_run.sh <method> <logname> [ENV=VAL ...]  -- batch (graphics on) in ~/male-face-UnityClone, muted, through heavy.sh
method=$1; name=$2; shift 2
for kv in "$@"; do export "$kv"; done
export GOLF_MUTE=1
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work
$W/delegation-2026-10-17/heavy.sh unity /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -projectPath $HOME/male-face-UnityClone \
  -executeMethod $method -quit -logFile $W/male-face-body/logs/$name.log
echo "exit $?"
