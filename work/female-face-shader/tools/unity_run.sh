#!/bin/zsh
# tools/unity_run.sh <method> <logname> [ENV=VAL ...]  -- batch (graphics on) in the female-face clone, muted
method=$1; name=$2; shift 2
for kv in "$@"; do export "$kv"; done
export GOLF_MUTE=1
/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -projectPath $HOME/female-face-UnityClone \
  -executeMethod $method -quit -logFile /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-face-shader/logs/$name.log
echo "exit $?"
