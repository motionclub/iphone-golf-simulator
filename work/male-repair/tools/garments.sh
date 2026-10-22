#!/bin/zsh
# tools/garments.sh <tag> : MaleRepairGarments.Run (batch, no play mode) in ~/unity-clones/male-repair -> build/<tag>
ME=${0:A:h:h}; HV=$ME/../delegation-2026-10-17/heavy.sh; U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
CL=$HOME/unity-clones/male-repair; mkdir -p $CL/Assets/Editor/MaleRepair && cp $ME/unity/*.cs $CL/Assets/Editor/MaleRepair/
GOLF_MUTE=1 MR_OUT=$ME/build/$1 $HV unity $U -batchmode -projectPath $CL -executeMethod GolfArcade.EditorTools.MaleRepairGarments.Run -logFile $ME/logs/garments_$1.log
echo "exit $?"
