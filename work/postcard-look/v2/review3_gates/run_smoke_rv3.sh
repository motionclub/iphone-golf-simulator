#!/bin/bash
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
S=$R/work/postcard-look/v2/review3_gates
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
mkdir -p $S/shots
GOLF_LOOK_SMOKE_REPORT=$S/smoke_rv3.txt GOLF_LOOK_SMOKE_SHOTS=$S/shots $R/work/postcard-look/heavy.sh R-smoke-rv3 $U -batchmode -projectPath $R/Unity -executeMethod GolfArcade.EditorTools.GolfLookSmoke.Run -logFile $S/smoke_rv3.log
echo "exit $?" > $S/smoke_rv3.done
