#!/bin/bash
# windowed (PlayMode capture needs real frames), muted
A=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/visual-audit-1110
P=$HOME/unity-clones/visual-audit-a; OUT=$A/shots/menus; mkdir -p $OUT
echo "$(date +%H:%M:%S) START menus" >> $A/logs/progress.log
( GOLF_MUTE=1 MS_OUT=$OUT $A/../delegation-2026-10-17/heavy.sh unity /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -projectPath $P -runTests -testPlatform PlayMode -testFilter GolfArcade.Tests.MenuAllCapture -testResults $OUT/results.xml -logFile $A/logs/menus.log ) &
pid=$!; t=0; while kill -0 $pid 2>/dev/null; do sleep 5; t=$((t+5)); [ $t -ge 700 ] && { pkill -f "projectPath $P"; break; }; done
echo "$(date +%H:%M:%S) END menus files=$(ls $OUT | wc -l | tr -d ' ') (${t}s)" >> $A/logs/progress.log
