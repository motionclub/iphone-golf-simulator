#!/bin/zsh
set -e
method=$1; log=$2; shift 2
while [[ ${FLUID_WAIT_XCODE:-1} == 1 ]] && pgrep -f "^/Applications/Xcode[^ ]*/Contents/Developer/usr/bin/xcodebuild |^xcodebuild " >/dev/null 2>&1; do sleep 15; done
opts=()
if [[ ${FLUID_NO_UPM:-0} == 1 ]]; then opts+=(-noUpm); fi
env "$@" /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode "${opts[@]}" -projectPath /private/tmp/emote-fluidity-unity-01a10d21 -executeMethod "$method" -logFile "$log"
