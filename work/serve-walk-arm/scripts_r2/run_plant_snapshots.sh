#!/bin/zsh
set -eu
root=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
clone=$1
stage=$2
for role in player opponent; do
 for sex in male female; do
  female=0; [[ $sex == female ]] && female=1
  env SW_IMAGES=0 SW_PLANT_SNAPSHOT=1 SW_FEMALE=$female SW_ROLE=$role SW_OUT="$root/work/serve-walk-arm/$stage/$role-$sex-rh-deuce" /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -projectPath "$root/work/serve-walk-arm/$clone" -executeMethod GolfArcade.EditorTools.ServeWalkFilm.Run -logFile "$root/work/serve-walk-arm/logs_r2/$stage-$role-$sex.log"
 done
done
