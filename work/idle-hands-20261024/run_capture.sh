#!/bin/bash
# idle-hands 10-24: sync HubHeroAnimator.cs into the clone, then the Plaza idle capture for both sexes. Usage: run_capture.sh <label>
set -u
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; W=$R/work/idle-hands-20261024; C=$HOME/unity-clones/idle-turnaround
L=${1:?label}; OUT=$W/$L; mkdir -p $OUT/shots $OUT/sheets
cp $R/Unity/Assets/Scripts/Hub/HubHeroAnimator.cs $C/Assets/Scripts/Hub/HubHeroAnimator.cs
for F in ${SEXES:-0 1}; do
  IT_OUT=$OUT/shots IT_FEMALE=$F CHARACTER_LOD_FORCE=0 GOLF_MUTE=1 $R/work/delegation-2026-10-17/heavy.sh unity \
    /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -projectPath $C -runTests -testPlatform PlayMode \
    -testFilter GolfArcade.Tests.IdleTurnaroundCapture -testResults $OUT/results_$F.xml -logFile $OUT/unity_$F.log
  echo "sex $F exit $?"
done
python3 $R/work/idle-presentation-20261024/sheets.py $OUT/shots $OUT/sheets
cat $OUT/shots/m_report.txt $OUT/shots/f_report.txt
