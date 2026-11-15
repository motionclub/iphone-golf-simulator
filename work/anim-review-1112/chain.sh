#!/bin/bash
# Records the current emotes, tennis and bowling in the anim-review clone. Each step is one Unity launch through heavy.sh.
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
C=$HOME/unity-clones/anim-review/Unity
O=$R/work/anim-review-1112
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
H=$R/work/delegation-2026-10-17/heavy.sh
export GOLF_MUTE=1
step="${1:-all}"
if [[ $step == all || $step == emotes ]]; then
  JF_MODE=tennisall JF_OUT=$O/emotes JF_FEMALE=0 $H unity $U -batchmode -projectPath $C -executeMethod GolfArcade.EditorTools.JoyFilm.Run -logFile $O/emotes.log -screen-width 1280 -screen-height 720
  echo "emotes exit $?" >> $O/status.txt
fi
if [[ $step == all || $step == tennis ]]; then
  TAI_OUT=$O/tennis TAI_SEX=male TAI_SECONDS=30 TAI_VIDEO=1 TAI_FFMPEG=$HOME/tai-films/ffmpeg $H unity $U -batchmode -projectPath $C -executeMethod GolfArcade.EditorTools.TennisAnimIntegrityFilm.Run -logFile $O/tennis.log -screen-width 1280 -screen-height 720
  echo "tennis exit $?" >> $O/status.txt
fi
if [[ $step == all || $step == bowling ]]; then
  BOWL_FILM_OUT=$O/bowling BOWL_FILM_CPU=1 BOWL_FILM_PHONE=1 BOWL_FILM_SHOTS=3 BOWL_FILM_SECONDS=45 $H unity $U -batchmode -projectPath $C -executeMethod GolfArcade.EditorTools.BowlingFilm.Run -logFile $O/bowling.log -screen-width 1280 -screen-height 720
  echo "bowling exit $?" >> $O/status.txt
fi
echo done >> $O/status.txt
