#!/bin/zsh
# NATIVE gate (clone only, nothing written to the repo): lobby export of the clone's heroes -> scratch CharacterAssets copy -> SceneKit
# lobby render vs Unity capture, using work/hero-sync's own tools.  native.sh [Run|RunGolf]
set -e
P=${0:A:h}; REPO=${P:h:h:h}; SYNC=$REPO/work/hero-sync
HV=${GP_HEAVY:-$REPO/work/delegation-2026-10-17/heavy.sh}
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
CL=${GP_CLONE:-$HOME/garments-UnityClone}; JOB=${1:-Run}; SPORT=$([[ $JOB == RunGolf ]] && echo golf || echo tennis)
N=$P/native; O=$N/$SPORT; rm -rf $O $N/unity/$SPORT $N/lobby/$SPORT; mkdir -p $O/export $O/golden $O/assets $O/logs $N/unity/$SPORT $N/lobby/$SPORT
export GOLF_MUTE=1
MH_LOCKER_FACE_PARITY=0 MH_LOCKER_OUT=$O/export MH_LOCKER_GOLDEN=$O/golden MH_LOCKER_REPORT=$O/logs/report.txt \
  $HV unity $U -batchmode -nographics -quit -projectPath $CL -executeMethod GolfArcade.EditorTools.MatchHeroLockerExport.$JOB -logFile $O/logs/export.log
LP_OUT=$N/unity/$SPORT LP_GOLF=$([[ $SPORT == golf ]] && echo 1 || echo 0) \
  $HV unity $U -batchmode -quit -projectPath $CL -executeMethod GolfArcade.EditorTools.MatchHeroLockerExport.CaptureLobbyParity -logFile $O/logs/capture.log
cp -c -R $REPO/GolfArcade/Unity/CharacterAssets/. $O/assets/; cp $O/export/*.* $O/assets/
[[ -x $P/native/lobby_render ]] || swiftc -swift-version 6 -O -parse-as-library $SYNC/lobby_render.swift $REPO/GolfArcade/Unity/MatchHeroData.swift $REPO/GolfArcade/Unity/MatchHeroSurfaces.swift \
    $REPO/GolfArcade/Unity/MatchHeroMotion.swift -framework SceneKit -framework AppKit -framework Metal -o $P/native/lobby_render
if [[ $SPORT == golf ]]; then LP_ASSETS=$O/assets LP_GOLF=1 $P/native/lobby_render $N/lobby/$SPORT default; else LP_ASSETS=$O/assets LP_DISTANCE=1 $P/native/lobby_render $N/lobby/$SPORT; fi 2>&1 | grep -iv warning | tail -5
python3 $SYNC/compare.py $N $N/sheets || true; ls $N/sheets | head
echo "NATIVE $SPORT done -> $O"
