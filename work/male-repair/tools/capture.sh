#!/bin/zsh
# tools/capture.sh <tag> [tennis golf] : male hero captures in ~/unity-clones/male-repair (one Unity launch per sport, via heavy.sh)
ME=${0:A:h:h}; HV=$ME/../delegation-2026-10-17/heavy.sh; U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
CL=$HOME/unity-clones/male-repair; TAG=$1; shift; SPORTS=($@); (( $#SPORTS )) || SPORTS=(tennis golf)
mkdir -p $CL/Assets/Editor/MaleRepair && cp $ME/unity/MaleRepairCapture.cs $CL/Assets/Editor/MaleRepair/
export GOLF_MUTE=1 DREAM_WEATHER=Clear
for sp in $SPORTS; do
  MR_SPORT=$sp MR_OUT=$ME/out/$TAG/$sp $HV unity $U -batchmode -projectPath $CL -executeMethod GolfArcade.EditorTools.MaleRepairCapture.Run -logFile $ME/logs/${TAG}_$sp.log
  echo "$sp exit $?"
done
