#!/bin/bash
# ingame_installed.sh: real in-scene captures from the project copy AFTER the install was synced into it (no preview switches, the game's own
# level-of-detail): what the game project now renders.
# menu, tennis court, golf, bowling. One Unity at a time through heavy.sh. Output: look/ingame_installed/<job>/
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
W=$REPO/work/final-plan-1111; P=$HOME/unity-clones/final-plan-dev/Unity
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
run() { # name timeout "ENV=.. ENV=.." method
  name=$1; to=$2; envs=$3; method=$4; OUT=$W/look/ingame_installed/$name; mkdir -p "$OUT"; envs=${envs//\{OUT\}/$OUT}
  rm -f "$P/Temp/UnityLockfile"; start=$(date +%s)
  ( env GOLF_MUTE=1 $envs $REPO/work/delegation-2026-10-17/heavy.sh unity $UNITY -batchmode -projectPath "$P" -executeMethod $method -logFile $W/logs/ingame_installed_$name.log ) &
  pid=$!; t=0
  while kill -0 $pid 2>/dev/null; do sleep 5; t=$((t+5)); if [ $t -ge $to ]; then echo "TIMEOUT $name"; pkill -f "projectPath $P"; sleep 3; pkill -9 -f "projectPath $P"; break; fi; done
  wait $pid 2>/dev/null
  echo "$name: $(find "$OUT" -type f | wc -l | tr -d ' ') files in $(( $(date +%s) - start )) s; studio meshes loaded: $(grep -c '\[HeroStudio\].*moved=' $W/logs/ingame_installed_$name.log)"
}
run tennis_venue 600 "HERO_VENUE=resort HERO_VENUE_OUT={OUT}" GolfArcade.EditorTools.TennisVenueCapture.Run
run tennis_store 600 "APPSTORE_OUT={OUT}" GolfArcade.EditorTools.AppStoreCapture.RunTennis
run golf_store 600 "APPSTORE_OUT={OUT}" GolfArcade.EditorTools.AppStoreCapture.RunGolf
run bowl_tiki 600 "BOWL_VENUE=tiki BOWL_FILM_OUT={OUT} BOWL_FILM_STILLS=1 BOWL_FILM_SHOTS=1 BOWL_FILM_SECONDS=12" GolfArcade.EditorTools.BowlingFilm.Run
run hub_male 600 "APPSTORE_OUT={OUT} HUB_MALE=1" GolfArcade.EditorTools.HubStoreCapture.Run
run hub 600 "APPSTORE_OUT={OUT}" GolfArcade.EditorTools.HubStoreCapture.Run
echo "INGAME DONE"
rm -f "$P/Temp/UnityLockfile"
env GOLF_MUTE=1 TURNAROUND_OUT=$W/look/turnaround_installed TURNAROUND_VIDEO=0 $REPO/work/delegation-2026-10-17/heavy.sh unity $UNITY -batchmode -projectPath "$P" -executeMethod GolfArcade.EditorTools.HeroTurnaround.RunBatch -logFile $W/logs/turnaround_installed.log
echo "TURNAROUND DONE $(ls $W/look/turnaround_installed 2>/dev/null | wc -l)"
