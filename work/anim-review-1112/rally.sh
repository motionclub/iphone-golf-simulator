#!/bin/bash
# rally.sh: 30 s autoplay rallies with the fixed grip, him and her (TAI film), after the emote films finish.
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; C=$HOME/unity-clones/anim-review/Unity; O=$R/work/anim-review-1112
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity; H=$R/work/delegation-2026-10-17/heavy.sh
until grep -q done $O/after_status.txt 2>/dev/null; do sleep 5; done
for sex in male female; do
  GOLF_MUTE=1 TAI_OUT=$O/films/rally_$sex TAI_SEX=$sex TAI_SECONDS=30 TAI_VIDEO=1 TAI_FFMPEG=$HOME/tai-films/ffmpeg $H unity $U -batchmode -projectPath $C -executeMethod GolfArcade.EditorTools.TennisAnimIntegrityFilm.Run -logFile $O/films/rally_$sex.log -screen-width 1280 -screen-height 720 < /dev/null
  echo "rally_$sex exit $?" >> $O/rally_status.txt
done
echo done >> $O/rally_status.txt
