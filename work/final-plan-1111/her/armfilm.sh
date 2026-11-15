#!/bin/bash
# armfilm.sh <name> [ENV=..]: her and him walking (tennis kits) in the project copy: front, side, each arm close up, and arms.csv
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/final-plan-1111; C=$HOME/unity-clones/final-plan-dev/Unity
name=$1; shift; mkdir -p $W/her/$name; rm -f $C/Temp/UnityLockfile
env GOLF_MUTE=1 CHARACTER_LOD=0 HERO_STUDIO=$W/phase2/game_data FEMALE_WALK_CURL=0.8 AWF_OUT=$W/her/$name AWF_FRAMES=${AWF_FRAMES:-32} "$@" $W/../delegation-2026-10-17/heavy.sh unity /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -projectPath $C -executeMethod GolfArcade.EditorTools.ArmWalkFilm.Run -logFile $W/logs/her_$name.log
echo "$name exit $? files $(ls $W/her/$name | wc -l | tr -d ' ') errors $(grep -c 'error CS' $W/logs/her_$name.log)"
