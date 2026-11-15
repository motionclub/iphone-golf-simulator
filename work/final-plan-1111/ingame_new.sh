#!/bin/bash
# ingame_new.sh: real in-scene captures from the PROJECT COPY final-plan-dev with the studio preview loaded (HERO_STUDIO):
# menu, tennis court, golf, bowling. One Unity at a time through heavy.sh. Output: look/ingame_new/<job>/
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
W=$REPO/work/final-plan-1111; P=$HOME/unity-clones/final-plan-dev/Unity
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
run() { # name timeout "ENV=.. ENV=.." method
  name=$1; to=$2; envs=$3; method=$4; OUT=$W/look/ingame_new/$name; mkdir -p "$OUT"; envs=${envs//\{OUT\}/$OUT}
  rm -f "$P/Temp/UnityLockfile"; start=$(date +%s)
  ( env GOLF_MUTE=1 CHARACTER_LOD=0 HERO_STUDIO=$W/phase2/game_data $envs $REPO/work/delegation-2026-10-17/heavy.sh unity $UNITY -batchmode -projectPath "$P" -executeMethod $method -logFile $W/logs/ingame_new_$name.log ) &
  pid=$!; t=0
  while kill -0 $pid 2>/dev/null; do sleep 5; t=$((t+5)); if [ $t -ge $to ]; then echo "TIMEOUT $name"; pkill -f "projectPath $P"; sleep 3; pkill -9 -f "projectPath $P"; break; fi; done
  wait $pid 2>/dev/null
  echo "$name: $(find "$OUT" -type f | wc -l | tr -d ' ') files in $(( $(date +%s) - start )) s; studio meshes loaded: $(grep -c '\[HeroStudio\].*moved=' $W/logs/ingame_new_$name.log)"
}
run tennis_venue 600 "HERO_VENUE=resort HERO_VENUE_OUT={OUT}" GolfArcade.EditorTools.TennisVenueCapture.Run
run tennis_store 600 "APPSTORE_OUT={OUT}" GolfArcade.EditorTools.AppStoreCapture.RunTennis
run golf_store 600 "APPSTORE_OUT={OUT}" GolfArcade.EditorTools.AppStoreCapture.RunGolf
run bowl_tiki 600 "BOWL_VENUE=tiki BOWL_FILM_OUT={OUT} BOWL_FILM_STILLS=1 BOWL_FILM_SHOTS=1 BOWL_FILM_SECONDS=12" GolfArcade.EditorTools.BowlingFilm.Run
run hub_male 600 "APPSTORE_OUT={OUT} HUB_MALE=1" GolfArcade.EditorTools.HubStoreCapture.Run
run hub 600 "APPSTORE_OUT={OUT}" GolfArcade.EditorTools.HubStoreCapture.Run
echo "INGAME DONE"
# the golfer's body renderer is named "Body": its turnaround is taken again now that game_data has Body_52020.pos
rm -f "$P/Temp/UnityLockfile"
env GOLF_MUTE=1 CHARACTER_LOD=0 HERO_STUDIO=$W/phase2/game_data TURNAROUND_HEROES=GolfKitHero_Male TURNAROUND_OUT=$W/look/turnaround_new_golf TURNAROUND_VIDEO=0 $REPO/work/delegation-2026-10-17/heavy.sh unity $UNITY -batchmode -projectPath "$P" -executeMethod GolfArcade.EditorTools.HeroTurnaround.RunBatch -logFile $W/logs/turnaround_new_golf.log
echo "GOLF TURNAROUND DONE $(ls $W/look/turnaround_new_golf 2>/dev/null | wc -l)"
