#!/bin/bash
# ab.sh <round>: his tennis point filmed with the arm probe (close-ups of the racket arm in the follow-through) under switches:
#   lod_default (the game as shipped), lod0 (CHARACTER_LOD_FORCE=0: full-detail garments at every distance), studio0 (HERO_STUDIO=0: the 11-11 body/tops).
# One Unity at a time through the job gate; uses final-plan-1111/anim/probe.sh's project copy.
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; W=$REPO/work/final-plan-1111; P=$REPO/work/polo-tear-1113
C=$HOME/unity-clones/final-plan-dev/Unity; U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity; H=$REPO/work/delegation-2026-10-17/heavy.sh
O=$P/$1; mkdir -p $O; export GOLF_MUTE=1
run() { local label=$1; shift
  [ -n "$ONLY" ] && ! echo " $ONLY " | grep -q " $label " && return
  rm -rf $O/$label; mkdir -p $O/$label; rm -f $C/Temp/UnityLockfile; local t=$(date +%s)
  env SHIRT_PROBE_OUT=$O/$label FILM_OUT=$O/film_$label FILM_SEX=male FILM_MIN_SHOTS=4 FILM_MAX_ATTEMPTS=2 "$@" \
    $H unity $U -batchmode -projectPath $C -executeMethod GolfArcade.EditorTools.CurrentTennisPointFilm.Run -logFile $O/$label.log -screen-width 1280 -screen-height 720
  echo "$label exit $? in $(( $(date +%s) - t )) s; pictures $(ls $O/$label | grep -c png); compile errors $(grep -c 'error CS' $O/$label.log)" | tee -a $O/status.txt
}
run lod_default
run lod0 CHARACTER_LOD_FORCE=0
run studio0 HERO_STUDIO=0
run shell_off HERO_SHELL=0
run corr_off GP_CORR_OFF=1
run cand $CAND_ENV
echo "AB $1 DONE" | tee -a $O/status.txt
