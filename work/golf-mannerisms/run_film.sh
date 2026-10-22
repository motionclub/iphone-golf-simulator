#!/bin/zsh
# run_film.sh <male|female> <yards> : filmed hole-out pick-up in the APFS clone (frames in film/<sex>_<yards>yd)
SP=/private/tmp/claude-501/-Users-adnanyonathan-Documents-Codex-2026-09-20-wh-outputs-iphone-golf-simulator/4f98fd08-f66e-4647-a534-86537aaf4b4a/scratchpad
W=$(cd "$(dirname $0)" && pwd); S=$1; D=${2:-8}; F=$([ "$S" = female ] && echo 1 || echo 0)
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
while pgrep -f "^/Applications/Xcode[^ ]*/Contents/Developer/usr/bin/xcodebuild |^xcodebuild " > /dev/null 2>&1; do sleep 15; done
$W/../delegation-2026-10-17/heavy.sh unity env GOLF_MUTE=1 JF_FEMALE=$F JF_DIST=$D JF_OUT=$W/film/${S}_${D}yd $UNITY -batchmode -projectPath $SP/UnityClone -executeMethod GolfArcade.EditorTools.PickFilm.Run -logFile $W/logs/film_${S}_${D}.log
echo "unity exit $?"
