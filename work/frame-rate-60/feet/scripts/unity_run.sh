#!/bin/zsh
# unity_run.sh <method> <log> [ENV=val ...] : run a Unity batch method in the APFS clone of the project (never in the shared project: another session may hold it).
# Waits while an xcodebuild is running (Unity's Burst crashes with SIGSEGV when the two overlap).
SCR=/private/tmp/claude-501/-Users-adnanyonathan-Documents-Codex-2026-09-20-wh-outputs-iphone-golf-simulator/b01646cf-fd03-44e2-8013-9dfb663ca268/scratchpad
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
method=$1; log=$2; shift 2
while pgrep -f "^/Applications/Xcode[^ ]*/Contents/Developer/usr/bin/xcodebuild |^xcodebuild " > /dev/null 2>&1; do sleep 15; done
env SF_REPO=$REPO "$@" $UNITY -batchmode ${NOGFX:+-nographics} ${QUIT:+-quit} -projectPath $SCR/UnityClone -executeMethod $method -logFile $log
echo "unity exit $?"
