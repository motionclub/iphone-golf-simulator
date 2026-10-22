#!/bin/zsh
set -eu
repo=${0:A:h:h:h}
clone=$TMPDIR/female-alive-UnityClone
unity=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
out=$repo/ArtDir/style/alive/after
cp "$repo/Unity/Assets/Scripts/Tennis/FemaleHeroAlive.cs" "$clone/Assets/Scripts/Tennis/"
cp "$repo/Unity/Assets/Editor/FemaleAliveCapture.cs" "$clone/Assets/Editor/"
cp "$repo/Unity/Assets/Tests/EditMode/FemaleHeroAliveTests.cs" "$clone/Assets/Tests/EditMode/"
export GOLF_MUTE=1 FILM_AUDIO=0
DREAM_WEATHER=Clear ALIVE_DETAIL=1 ALIVE_OUT="$out/after-matched" "$unity" -batchmode -projectPath "$clone" -executeMethod GolfArcade.EditorTools.FemaleAliveCapture.Run -logFile "$repo/work/female-alive/logs/after-matched.log"
DREAM_WEATHER=Gusty ALIVE_MODE=golf FILM_HOLE=1 FILM_COURSE=meadow FILM_OUT="$out/after/golf" "$unity" -batchmode -projectPath "$clone" -executeMethod GolfArcade.EditorTools.FemaleAliveCapture.Run -logFile "$repo/work/female-alive/logs/after-golf.log"
DREAM_WEATHER=Clear FEMALE_ALIVE=0 FILM_SEX=female FILM_MIN_SHOTS=3 FILM_MAX_ATTEMPTS=2 FILM_OUT="$out/before-matched/rally" "$unity" -batchmode -projectPath "$clone" -executeMethod GolfArcade.EditorTools.CurrentTennisPointFilm.Run -logFile "$repo/work/female-alive/logs/before-rally-matched.log"
DREAM_WEATHER=Clear FILM_SEX=female FILM_MIN_SHOTS=3 FILM_MAX_ATTEMPTS=2 FILM_OUT="$out/after-matched/rally" "$unity" -batchmode -projectPath "$clone" -executeMethod GolfArcade.EditorTools.CurrentTennisPointFilm.Run -logFile "$repo/work/female-alive/logs/after-rally.log"
"$unity" -batchmode -nographics -projectPath "$clone" -runTests -testPlatform EditMode -testFilter 'GolfArcade.Tests.FemaleHeroAliveTests;GolfArcade.Tests.FemaleDeformationTests' -testResults "$out/tests.xml" -logFile "$repo/work/female-alive/logs/tests.log"
