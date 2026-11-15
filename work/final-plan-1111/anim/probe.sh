#!/bin/bash
# probe.sh <round>: the arm probe riding on the real tennis point, golf swing and bowling films in the project copy (one Unity at a
# time, through the job gate). Output: anim/<round>/<sport>/arms.csv + close-ups of the worst wrists, before and after the limits.
# Extra environment (ARM_LIMIT_*=..) passes straight through. PROBE_ONLY="tennis_f golf" runs a subset.
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; W=$REPO/work/final-plan-1111
C=$HOME/unity-clones/final-plan-dev/Unity; U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity; H=$REPO/work/delegation-2026-10-17/heavy.sh
round=$1; O=$W/anim/$round; mkdir -p $O $W/logs; export GOLF_MUTE=1
run() { # label method env...
  local label=$1 method=$2; shift 2
  [ -n "$PROBE_ONLY" ] && ! echo " $PROBE_ONLY " | grep -q " $label " && return
  rm -rf $O/$label $O/film_$label; mkdir -p $O/$label; rm -f $C/Temp/UnityLockfile; local t=$(date +%s)
  env ARM_PROBE_OUT=$O/$label "$@" $H unity $U -batchmode -projectPath $C -executeMethod $method -logFile $W/logs/anim_${round}_$label.log -screen-width 1280 -screen-height 720
  echo "$label exit $? in $(( $(date +%s) - t )) s; rows $(wc -l < $O/$label/arms.csv 2>/dev/null) pictures $(ls $O/$label | grep -c png) compile errors $(grep -c 'error CS' $W/logs/anim_${round}_$label.log)"
}
run tennis_f GolfArcade.EditorTools.CurrentTennisPointFilm.Run FILM_OUT=$O/film_tennis_f FILM_SEX=female FILM_MIN_SHOTS=4 FILM_MAX_ATTEMPTS=2
run tennis_m GolfArcade.EditorTools.CurrentTennisPointFilm.Run FILM_OUT=$O/film_tennis_m FILM_SEX=male FILM_MIN_SHOTS=4 FILM_MAX_ATTEMPTS=2
run golf GolfArcade.EditorTools.CurrentGolfSwingFilm.Run FILM_OUT=$O/film_golf FILM_AUDIO=0
run bowl GolfArcade.EditorTools.BowlingFilm.Run BOWL_FILM_OUT=$O/film_bowl BOWL_FILM_SHOTS=2 BOWL_FILM_SECONDS=45
echo "PROBE $round DONE"
