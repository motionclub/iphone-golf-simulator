#!/bin/zsh
set -e
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/serve-toss-jump
clone=$1
sex=$2
root=$3
female=0
if [[ $sex == female ]]; then female=1; fi
for spec in 0:0 1:26 2:53 3:79 4:106; do
 phase=${spec%%:*}
 delay=${spec##*:}
 capture=0
 if [[ $phase == 0 ]]; then capture=1; fi
 out=$PWD/$root/$sex/phase$phase
 log=$PWD/${root}_${sex}_phase${phase}.log
 SJ_OUT=$out SJ_FEMALE=$female SJ_CAPTURE=$capture SJ_ENTRY_DELAY=$delay SJ_TAIL=150 /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -projectPath $PWD/$clone -executeMethod GolfArcade.EditorTools.ServeJumpProof.Run -logFile $log
 python3 scripts/metrics_r3.py $out > $out/metrics.out
 print "PHASE_DONE $sex $phase"
done
