#!/bin/bash
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; S=$R/work/postcard-look/v2/review3_gates/r3; U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
POSTCARD_IMPORT_REPORT=$S/importcheck.txt $R/work/postcard-look/heavy.sh R3-importcheck $U -batchmode -projectPath $R/Unity -executeMethod GolfArcade.EditorTools.PostcardImportCheck.Run -logFile $S/logs/importcheck.log
echo "importcheck exit $?" > $S/importcheck.done
GOLF_LOOK_SMOKE_REPORT=$S/smoke.txt GOLF_LOOK_SMOKE_SHOTS=$S/shots $R/work/postcard-look/heavy.sh R3-smoke $U -batchmode -projectPath $R/Unity -executeMethod GolfArcade.EditorTools.GolfLookSmoke.Run -logFile $S/logs/smoke.log
echo "smoke exit $?" > $S/smoke.done
