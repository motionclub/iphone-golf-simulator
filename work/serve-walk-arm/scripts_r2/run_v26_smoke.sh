#!/bin/zsh
set -eu
root=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
for spec in male-walk female-control; do
 sex=${spec%-*}; suffix=${spec#*-}; female=0; control=0; [[ $sex == female ]] && female=1; [[ $suffix == control ]] && control=1
 env SW_IMAGES=0 SW_ROLE=opponent SW_FEMALE=$female SW_SIDE=deuce SW_CONTROL_ONLY=$control SW_OUT="$root/work/serve-walk-arm/smoke_r2/v26-opponent-$spec" /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -projectPath "$root/work/serve-walk-arm/CandidateR2Clone" -executeMethod GolfArcade.EditorTools.ServeWalkFilm.Run -logFile "$root/work/serve-walk-arm/logs_r2/v26-opponent-$spec.log"
done
