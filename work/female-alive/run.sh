#!/bin/zsh
# Fresh output directory required. Reproduce a muted female before/after comparison.
set -eu
repo=${0:A:h:h:h}
out=${1:?Usage: work/female-alive/run.sh /absolute/fresh/output}
[[ ! -e "$out" ]] || { print -u2 'Output must be fresh'; exit 1; }
clone=${ALIVE_UNITY_PROJECT:-$TMPDIR/female-alive-UnityClone}
[[ "$clone" != "$repo/Unity" ]] || { print -u2 'Use an isolated clone'; exit 1; }
[[ -d "$clone" ]] || cp -cR "$repo/Unity" "$clone"
for file in Assets/Scripts/Tennis/FemaleHeroAlive.cs Assets/Scripts/Tennis/MatchHeroLook.cs Assets/Scripts/Game/GolferView.cs Assets/Editor/FemaleAliveCapture.cs Assets/Tests/EditMode/FemaleHeroAliveTests.cs; do
  cp "$repo/Unity/$file" "$clone/$file"
  [[ ! -f "$repo/Unity/$file.meta" ]] || cp "$repo/Unity/$file.meta" "$clone/$file.meta"
done
unity=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
mkdir -p "$out/logs"
export GOLF_MUTE=1 FILM_AUDIO=0
for stage in before after; do
  export FEMALE_ALIVE=$([[ "$stage" == before ]] && print 0 || print 1)
  DREAM_WEATHER=Clear ALIVE_DETAIL=1 ALIVE_OUT="$out/$stage" "$unity" -batchmode -projectPath "$clone" -executeMethod GolfArcade.EditorTools.FemaleAliveCapture.Run -logFile "$out/logs/$stage-idle.log"
  DREAM_WEATHER=Gusty ALIVE_MODE=golf FILM_HOLE=1 FILM_COURSE=meadow FILM_WIND_MPH=13 FILM_WIND_DEGREES=-33 FILM_OUT="$out/$stage/golf" "$unity" -batchmode -projectPath "$clone" -executeMethod GolfArcade.EditorTools.FemaleAliveCapture.Run -logFile "$out/logs/$stage-golf.log"
  DREAM_WEATHER=Clear FILM_SEX=female FILM_MIN_SHOTS=3 FILM_MAX_ATTEMPTS=2 FILM_OUT="$out/$stage/rally" "$unity" -batchmode -projectPath "$clone" -executeMethod GolfArcade.EditorTools.CurrentTennisPointFilm.Run -logFile "$out/logs/$stage-rally.log"
done
unset FEMALE_ALIVE
"$unity" -batchmode -nographics -projectPath "$clone" -runTests -testPlatform EditMode -testFilter 'GolfArcade.Tests.FemaleHeroAliveTests;GolfArcade.Tests.FemaleDeformationTests' -testResults "$out/tests.xml" -logFile "$out/logs/tests.log"
