#!/bin/bash
# Starts the trailer film server (private clone) for one scene:  server.sh Tennis [venue]
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
W=$R/work/trailer-1112; C=$HOME/unity-clones/trailer/Unity
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity; H=$R/work/delegation-2026-10-17/heavy.sh
rm -f $W/stage/ready.txt $W/stage/done.txt $W/stage/cmd.json $C/Temp/UnityLockfile
export GOLF_MUTE=1 MAJESTIC_WEATHER=0 CHARACTER_LOD=0 TR_SCENE=${1:-Tennis} TR_DIR=$W/stage
[ -n "$2" ] && export HERO_VENUE=$2 BOWL_VENUE=$2
exec $H unity $U -batchmode -projectPath $C -executeMethod GolfArcade.EditorTools.TrailerFilm.Run -logFile $W/stage/unity.log -screen-width 1280 -screen-height 720
