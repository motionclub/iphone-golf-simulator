#!/bin/zsh
# film.sh <FemaleTennisFilm|...> : copies work/female-match-swing/unity/*.cs into the review-1019 clone (an APFS clone of Unity/ at 17:33 10-19) and films through heavy.sh.
REPO=${0:A:h:h:h:h}; W=$REPO/work/female-match-swing; C=${CLONE:-$HOME/unity-clones/review-1019}
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
M=$1; OUT=$2; shift 2
mkdir -p $C/Assets/Editor/FemaleSwingLocal $W/logs
cp $W/unity/*.cs $C/Assets/Editor/FemaleSwingLocal/
env GOLF_MUTE=1 REVIEW_OUT=$OUT "$@" $REPO/work/delegation-2026-10-17/heavy.sh unity $UNITY -batchmode -projectPath $C -executeMethod GolfArcade.EditorTools.$M.Run -logFile $W/logs/$M.log
echo "unity exit $?"
grep "\[Female\|error CS\|Exception" $W/logs/$M.log | head -40
