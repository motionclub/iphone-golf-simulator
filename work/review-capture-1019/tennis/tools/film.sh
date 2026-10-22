#!/bin/zsh
# film.sh <golf|tennis> : copies the review harness into ~/unity-clones/review-1019 (an APFS clone of Unity/ with every uncommitted
# change, 2026-10-19 17:33) and films through heavy.sh, batch mode, muted. Frames land in ~/review-1019-frames/<what>.
REPO=${0:A:h:h:h:h}; W=$REPO/work/review-capture-1019; C=$HOME/unity-clones/review-1019
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
what=$1; shift
mkdir -p $C/Assets/Editor/ReviewLocal $W/logs
cp $W/tools/unity/*.cs $C/Assets/Editor/ReviewLocal/
case $what in golf) M=GolfArcade.EditorTools.ReviewGolfFilm.Run;; tennis) M=GolfArcade.EditorTools.ReviewTennisFilm.Run;; plaza) M=GolfArcade.EditorTools.ReviewPlazaStills.Run;; esac
rm -rf $HOME/review-1019-frames/$what
env GOLF_MUTE=1 REVIEW_OUT=$HOME/review-1019-frames/$what "$@" $REPO/work/delegation-2026-10-17/heavy.sh unity $UNITY -batchmode -projectPath $C -executeMethod $M -logFile $W/logs/$what.log
echo "unity exit $?"
grep "\[Review\|error CS\|Exception" $W/logs/$what.log | head -40
