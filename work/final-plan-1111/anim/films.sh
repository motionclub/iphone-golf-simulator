#!/bin/bash
# films.sh <round>: every animation of both heroes on the INSTALLED game (the project copy is synced from the shared project first), one
# Unity at a time through heavy.sh. Film tools: the game's own (GolfMotionFilm, BowlingFilm) and two borrowed read-only from the
# "Emotes and sports animations" chat's copy (JoyFilm: emotes / plaza; TennisAnimIntegrityFilm: a real match, both heroes side on).
# The arm probe rides along without pictures (numbers only). ONLY="tennis_match golf_swing" runs a subset.
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; W=$REPO/work/final-plan-1111
C=$HOME/unity-clones/final-plan-dev/Unity; U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity; H=$REPO/work/delegation-2026-10-17/heavy.sh
FF=$HOME/tai-films/ffmpeg; O=$W/anim/$1; mkdir -p $O; export GOLF_MUTE=1
rsync -a $HOME/unity-clones/anim-review/Unity/Assets/Editor/Review/ $C/Assets/Editor/Review/
rsync -a $HOME/unity-clones/anim-review/Unity/Assets/Scripts/TAI/ $C/Assets/Scripts/TAI/
run() {
  local label=$1 method=$2; shift 2
  [ -n "$ONLY" ] && ! echo " $ONLY " | grep -q " $label " && return
  rm -rf $O/$label $O/${label}_probe; rm -f $C/Temp/UnityLockfile; local t=$(date +%s)
  env ARM_PROBE_OUT=$O/${label}_probe ARM_PROBE_MAX=0 "$@" $H unity $U -batchmode -projectPath $C -executeMethod $method -logFile $O/$label.log -screen-width 1280 -screen-height 720
  echo "$label exit $? in $(( $(date +%s) - t )) s, compile errors $(grep -c 'error CS' $O/$label.log)" | tee -a $O/status.txt
}
run tennis_match    GolfArcade.EditorTools.TennisAnimIntegrityFilm.Run TAI_OUT=$O/tennis_match TAI_SEX=male TAI_SECONDS=45 TAI_VIDEO=1 TAI_FFMPEG=$FF
run tennis_emotes_m GolfArcade.EditorTools.JoyFilm.Run JF_MODE=tennisall JF_FEMALE=0 JF_OUT=$O/tennis_emotes_m
run tennis_emotes_f GolfArcade.EditorTools.JoyFilm.Run JF_MODE=tennisall JF_FEMALE=1 JF_OUT=$O/tennis_emotes_f
run golf_swing      GolfArcade.EditorTools.GolfMotionFilm.Run GMF_OUT=$O/golf_swing
run golf_emotes_m   GolfArcade.EditorTools.JoyFilm.Run JF_MODE=golfall JF_FEMALE=0 JF_OUT=$O/golf_emotes_m
run golf_emotes_f   GolfArcade.EditorTools.JoyFilm.Run JF_MODE=golfall JF_FEMALE=1 JF_OUT=$O/golf_emotes_f
run bowling         GolfArcade.EditorTools.BowlingFilm.Run BOWL_FILM_OUT=$O/bowling BOWL_FILM_SHOTS=4 BOWL_FILM_SECONDS=70
run plaza_m         GolfArcade.EditorTools.JoyFilm.Run JF_MODE=huball JF_FEMALE=0 JF_OUT=$O/plaza_m
run plaza_f         GolfArcade.EditorTools.JoyFilm.Run JF_MODE=huball JF_FEMALE=1 JF_OUT=$O/plaza_f
echo "FILMS $1 DONE" | tee -a $O/status.txt
