#!/bin/bash
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
C=$HOME/unity-clones/anim-review/Unity; O=$R/work/anim-review-1112
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity; H=$R/work/delegation-2026-10-17/heavy.sh
export GOLF_MUTE=1
for mode in ${MODES:-tennisall golfall}; do
  JF_MODE=$mode JF_OUT=$O/hands_$mode JF_FEMALE=0 $H unity $U -batchmode -projectPath $C -executeMethod GolfArcade.EditorTools.JoyFilm.Run -logFile $O/hands_$mode.log -screen-width 1280 -screen-height 720
  echo "$mode exit $?" >> $O/hands_status.txt
done
echo done >> $O/hands_status.txt
