#!/bin/zsh
# 10-18 bug repro: Adnan's phone build (integration snapshot work/phone-build-20261018/root) -> APFS clone ~/mg-snap-Clone (or $CL):
# tennis point film (male), golf film, Unity locker/lobby captures. Muted, one Unity job at a time through heavy.sh.
ME=${0:A:h:h}; HV=$ME/../delegation-2026-10-17/heavy.sh; U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
CL=${CL:-$HOME/mg-snap-Clone}; O=${O:-$ME/snapbug/before}; mkdir -p $O; export GOLF_MUTE=1
FILM_OUT=$O/tennis FILM_SEX=male HERO_VENUE=resort $HV unity $U -batchmode -projectPath $CL -executeMethod GolfArcade.EditorTools.CurrentTennisPointFilm.Run -logFile $O/tennis.log; echo "tennis exit $?"
FILM_OUT=$O/golf $HV unity $U -batchmode -projectPath $CL -executeMethod GolfArcade.EditorTools.CurrentGolfSwingFilm.Run -logFile $O/golf.log; echo "golf exit $?"
for sport in tennis golf; do
  LP_OUT=$O/locker_$sport LP_GOLF=$([[ $sport == golf ]] && echo 1 || echo 0) $HV unity $U -batchmode -quit -projectPath $CL -executeMethod GolfArcade.EditorTools.MatchHeroLockerExport.CaptureLobbyParity -logFile $O/locker_$sport.log; echo "locker $sport exit $?"
done
echo "SNAP DONE"
