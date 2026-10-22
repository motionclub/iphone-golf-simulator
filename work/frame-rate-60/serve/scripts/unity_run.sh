#!/bin/zsh
# unity_run.sh <method> <log> [ENV=val ...] : run a Unity batch method in the APFS clone of the project (never in the shared project). Waits while an xcodebuild is running (Burst crash).
SCR=/private/tmp/claude-501/-Users-adnanyonathan-Documents-Codex-2026-09-20-wh-outputs-iphone-golf-simulator/20d321cf-489d-4799-a4fe-fd1d628c6cd4/scratchpad
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
method=$1; log=$2; shift 2
while pgrep -f "^/Applications/Xcode[^ ]*/Contents/Developer/usr/bin/xcodebuild |^xcodebuild " > /dev/null 2>&1; do sleep 15; done
env "$@" $UNITY -batchmode -projectPath $SCR/UnityClone -executeMethod $method -logFile $log
echo "unity exit $?"
