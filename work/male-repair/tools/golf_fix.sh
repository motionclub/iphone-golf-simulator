#!/bin/zsh
# tools/golf_fix.sh <tag> : restore the clone's golf male garment files from Unity/, run MaleRepairPolo (polo tail + belt), recompute the
# Bottom hide list in play mode (MR_HIDE), install it in the clone, then capture golf -> out/<tag>. One heavy job at a time.
ME=${0:A:h:h}; HV=$ME/../delegation-2026-10-17/heavy.sh; U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
CL=$HOME/unity-clones/male-repair; M=$ME/../../Unity/Assets; T=$1
for f in Characters/KitsV2/GolfKitHero_Male/Kit_Top.asset Characters/KitsV2/GolfKitHero_Male/Kit_Belt.asset Resources/Golf/KitsV2/Male/KitV2_Golf_Male_Belt_correctives.json Resources/Golf/KitsV2/Male/KitV2_Golf_Male_Bottom_hide.bytes; do cp $M/$f $CL/Assets/$f; done
cp $ME/unity/*.cs $CL/Assets/Editor/MaleRepair/
GOLF_MUTE=1 MR_OUT=$ME/build/$T $HV unity $U -batchmode -projectPath $CL -executeMethod GolfArcade.EditorTools.MaleRepairPolo.Run -logFile $ME/logs/polo_$T.log; echo "polo exit $?"
cat $ME/build/$T/polo_log.txt
MR_HIDE=1 $ME/tools/capture.sh hide_$T golf | tail -1; grep hide: $ME/out/hide_$T/golf/log.txt
cp $ME/out/hide_$T/golf/hide/KitV2_Golf_Male_Bottom_hide.bytes $CL/Assets/Resources/Golf/KitsV2/Male/ && cp $ME/out/hide_$T/golf/hide/KitV2_Golf_Male_Bottom_hide.bytes $ME/build/$T/
$ME/tools/capture.sh $T golf | tail -1
