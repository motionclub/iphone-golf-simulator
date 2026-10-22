#!/bin/zsh
set -eu
repo=${0:A:h:h:h}
clone=$TMPDIR/female-alive-UnityClone
unity=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
out=$repo/ArtDir/style/alive/after
cp "$repo/Unity/Assets/Scripts/Tennis/FemaleHeroAlive.cs" "$clone/Assets/Scripts/Tennis/"
cp "$repo/Unity/Assets/Editor/FemaleAliveCapture.cs" "$clone/Assets/Editor/"
export GOLF_MUTE=1 FILM_AUDIO=0
DREAM_WEATHER=Clear ALIVE_DETAIL=1 ALIVE_OUT="$out/after-final" "$unity" -batchmode -projectPath "$clone" -executeMethod GolfArcade.EditorTools.FemaleAliveCapture.Run -logFile "$repo/work/female-alive/logs/after-final.log"
DREAM_WEATHER=Gusty ALIVE_MODE=golf FILM_HOLE=1 FILM_COURSE=meadow FILM_WIND_MPH=13 FILM_WIND_DEGREES=-33 FILM_OUT="$out/after-final/golf" "$unity" -batchmode -projectPath "$clone" -executeMethod GolfArcade.EditorTools.FemaleAliveCapture.Run -logFile "$repo/work/female-alive/logs/after-golf-final.log"
DREAM_WEATHER=Clear FILM_SEX=female FILM_MIN_SHOTS=3 FILM_MAX_ATTEMPTS=2 FILM_OUT="$out/after-final/rally" "$unity" -batchmode -projectPath "$clone" -executeMethod GolfArcade.EditorTools.CurrentTennisPointFilm.Run -logFile "$repo/work/female-alive/logs/after-rally-final.log"
"$unity" -batchmode -nographics -projectPath "$clone" -runTests -testPlatform EditMode -testFilter 'GolfArcade.Tests.FemaleHeroAliveTests;GolfArcade.Tests.FemaleDeformationTests' -testResults "$out/tests-final.xml" -logFile "$repo/work/female-alive/logs/tests-final.log"
