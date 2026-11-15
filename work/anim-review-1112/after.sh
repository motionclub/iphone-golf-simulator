#!/bin/bash
# after.sh: films with the EMPTY HANDS fix (HERO_EMPTY_HANDS=0 rows = the same build with it off = before). One Unity per row.
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
C=$HOME/unity-clones/anim-review/Unity; O=$R/work/anim-review-1112
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity; H=$R/work/delegation-2026-10-17/heavy.sh
export GOLF_MUTE=1 JF_HUB_EMOTES_ONLY=1
run() { # label mode female emptyhands [K=V;K=V extra env]
  env $(echo "$5" | tr ';' ' ') HERO_EMPTY_HANDS=$4 JF_MODE=$2 JF_OUT=$O/films/$1 JF_FEMALE=$3 $H unity $U -batchmode -projectPath $C -executeMethod GolfArcade.EditorTools.JoyFilm.Run -logFile $O/films/$1.log -screen-width 1280 -screen-height 720
  echo "$1 exit $?" >> $O/after_status.txt
}
mkdir -p $O/films
ROWS_FILE=${ROWS_FILE:-$O/rows.txt}
while read -r label mode female empty extra; do [ -n "$label" ] && run $label $mode $female $empty "$extra" < /dev/null; done < "$ROWS_FILE"
echo done >> $O/after_status.txt
