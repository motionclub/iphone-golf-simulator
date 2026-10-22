#!/bin/zsh
# Put the chat-4 "after" state into the chat-4 Unity clone (never the real Unity/):
#   driver + inertia + grip polish from work/tennis-anim-integrity/src, the approved strokes resampled to 60 Hz (match60) with the
#   30 Hz table's contact / leftRelease times on the prefab slots (FrameRate60Wire), then the ForehandArmCorrected / BackhandArmCorrected rebuild.
set -e
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
C=${TAI_CLONE:-/Users/adnanyonathan/tai-films/UnityClone}
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
W=$REPO/work/tennis-anim-integrity
LOG=${1:-/Users/adnanyonathan/tai-films/install_clone}; mkdir -p $LOG
if [ "$2" != "ready-only" ]; then
cp $W/src/HeroTennisDriver.cs $W/src/HeroTennisInertia.cs $W/src/HeroGripPolish.cs $C/Assets/Scripts/Tennis/
mkdir -p $C/Assets/Editor/TAI $C/Assets/Scripts/TAI; cp $W/unity/Editor*/*.cs $C/Assets/Editor/TAI/; cp $W/unity/Runtime/*.cs $C/Assets/Scripts/TAI/
GOLF_MUTE=1 FR60_REPO=$REPO FR60_SOURCE=$W/match60/export/fbx/ FR60_TABLE=$REPO/work/frame-rate-60/clip_table_30_original.json \
  $U -batchmode -projectPath $C -executeMethod GolfArcade.EditorTools.FrameRate60Wire.Run -logFile $LOG/wire.log || { grep -n "error CS\|FR60" $LOG/wire.log | head -20; exit 1; }
grep -A40 "FR60 DONE" $LOG/wire.log | head -60 > $LOG/wire_summary.txt || true
GOLF_MUTE=1 $U -batchmode -projectPath $C -executeMethod GolfArcade.EditorTools.TennisArmStrokeBuild.Run -logFile $LOG/armbuild.log || { grep -n "error CS\|Exception" $LOG/armbuild.log | head -20; exit 1; }
cp /Users/adnanyonathan/tai-films/arm-stroke-build.txt $LOG/ 2>/dev/null || true
fi
# the rebuilt ForehandArmCorrected does not reproduce the approved one (9 cm male / 73 cm female racket tip at shared frames): install the
# approved 60 Hz-keyed ArmCorrected clips (work/frame-rate-60/backup_armcorrected, .anim content only; the installed .meta / GUID stay)
for f in $REPO/work/frame-rate-60/backup_armcorrected/*.anim; do cp $f $C/Assets/Resources/Tennis/Performance/; done
$W/prepare_extras.sh
GOLF_MUTE=1 $U -batchmode -projectPath $C -executeMethod GolfArcade.EditorTools.TennisAnimInstall.ExtractReadyIdle -logFile $LOG/ready60.log || { grep -n "error CS\|TAI install" $LOG/ready60.log | head; exit 1; }
grep "TAI install" $LOG/ready60.log | head -4
echo INSTALL_CLONE_DONE
