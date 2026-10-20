#!/bin/zsh
set -eu
root=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
stage=$1
for sex in male female; do
  for hand in rh lh; do
    for side in deuce ad; do
      female=0; lefty=0
      if [[ $sex == female ]]; then female=1; fi
      if [[ $hand == lh ]]; then lefty=1; fi
      name=$sex-$hand-$side
      echo "START $stage/$name"
      env SW_FEMALE=$female SW_LEFTY=$lefty SW_SIDE=$side SW_DURATION=20 SW_OUT="$root/work/serve-walk-arm/$stage/$name" /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -projectPath "$root/work/serve-walk-arm/UnityClone" -executeMethod GolfArcade.EditorTools.ServeWalkFilm.Run -logFile "$root/work/serve-walk-arm/logs/$stage-$name.log"
      /Users/adnanyonathan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 "$root/work/serve-walk-arm/scripts/proof.py" "$root/work/serve-walk-arm/$stage/$name" --film > "$root/work/serve-walk-arm/logs/$stage-$name-summary.log"
      echo "DONE $stage/$name"
    done
  done
done
