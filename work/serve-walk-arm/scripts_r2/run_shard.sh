#!/bin/zsh
set -eu
root=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
clone=$1; stage=$2; shard=$3; n=0
for role in player opponent; do
 for sex in male female; do
  for side in deuce ad; do
   for control in 0 1; do
    if (( n % 3 == shard )); then
     female=0; [[ $sex == female ]] && female=1
     suffix=walk; [[ $control == 1 ]] && suffix=control
     name=$role-$sex-rh-$side-$suffix
     env SW_IMAGES=0 SW_ROLE=$role SW_FEMALE=$female SW_SIDE=$side SW_CONTROL_ONLY=$control SW_OUT="$root/work/serve-walk-arm/$stage/$name" /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -projectPath "$root/work/serve-walk-arm/$clone" -executeMethod GolfArcade.EditorTools.ServeWalkFilm.Run -logFile "$root/work/serve-walk-arm/logs_r2/$stage-$name.log"
    fi
    n=$((n+1))
   done
  done
 done
done
