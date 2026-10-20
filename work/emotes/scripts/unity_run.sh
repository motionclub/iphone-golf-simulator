#!/bin/zsh
# unity_run.sh <method> <log> [ENV=val ...] : run a Unity batch method in the APFS clone of the project (never in the shared project). Waits while an xcodebuild runs (Burst crash).
SP=/private/tmp/claude-501/-Users-adnanyonathan-Documents-Codex-2026-09-20-wh-outputs-iphone-golf-simulator/840886d1-2e8b-483d-a69e-a5f66b9907fd/scratchpad
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
method=$1; log=$2; shift 2
while pgrep -f "^/Applications/Xcode[^ ]*/Contents/Developer/usr/bin/xcodebuild |^xcodebuild " > /dev/null 2>&1; do sleep 15; done
s=$(date '+%Y-%m-%d %H:%M:%S')
env EW_REPO=$R "$@" $UNITY -batchmode -projectPath $SP/UnityClone -executeMethod $method -logFile $log
rc=$?
echo "$s | $(date '+%Y-%m-%d %H:%M:%S') | rc=$rc | unity $method (clone)" >> $R/work/emotes/logs/runs.log
echo "unity exit $rc"
