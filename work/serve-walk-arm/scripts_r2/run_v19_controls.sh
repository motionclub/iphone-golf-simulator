#!/bin/zsh
set -eu
root=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
for spec in opponent-male opponent-female player-female; do
 role=${spec%-*}; sex=${spec#*-}; female=0; [[ $sex == female ]] && female=1
 env SW_IMAGES=0 SW_ROLE=$role SW_FEMALE=$female SW_SIDE=deuce SW_CONTROL_ONLY=1 SW_DURATION=8 SW_OUT="$root/work/serve-walk-arm/smoke_r2/v19-$spec-control" /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -projectPath "$root/work/serve-walk-arm/CandidateR2Clone" -executeMethod GolfArcade.EditorTools.ServeWalkFilm.Run -logFile "$root/work/serve-walk-arm/logs_r2/v19-$spec-control.log"
done
