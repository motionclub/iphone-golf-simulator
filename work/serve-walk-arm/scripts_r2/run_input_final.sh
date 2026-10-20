#!/bin/zsh
set -eu
root=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
for sex in male female; do
 for side in deuce ad; do
  female=0; [[ $sex == female ]] && female=1
  env SW_INPUT_PATH=adapter SW_IMAGES=1 SW_DURATION=9 SW_FEMALE=$female SW_SIDE=$side SW_OUT="$root/work/serve-walk-arm/input_r2_v30/$sex-rh-$side" /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -projectPath "$root/work/serve-walk-arm/InputR2Clone" -executeMethod GolfArcade.EditorTools.ServeWalkFilm.Run -logFile "$root/work/serve-walk-arm/logs_r2/input-r2-v30-$sex-$side.log"
 done
done
