#!/bin/zsh
# 10-18: after the prefab patch was applied to the real tree, rerun MatchHeroLockerExport.RunDistance (crashed for chat 11 on Kit_Sock_L
# 3 bones / 2 bindposes) in an APFS clone of that tree. Waits until round 3's Blender fits are done (one heavy job at a time from this chat).
ME=${0:A:h:h}; REPO=${ME:h:h}; CL=$HOME/male-garments-VerifyClone; O=$ME/verify_rundistance
HV=$REPO/work/delegation-2026-10-17/heavy.sh; U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
export GOLF_MUTE=1
until grep -q -E "R3B DONE|FAILED" $ME/logs/r3b_summary.log 2>/dev/null; do sleep 20; done
# 10-18: the clone was cut ~00:46, inside a 00:45-00:50 window where HeroClearanceTests.cs lacked a using; re-copied from the tree 02:0x
rm -rf $O; mkdir -p $O/export $O/golden
echo "start $(date +%H:%M:%S)"
MH_LOCKER_FACE_PARITY=0 MH_LOCKER_OUT=$O/export MH_LOCKER_GOLDEN=$O/golden MH_LOCKER_REPORT=$O/report.txt \
  $HV unity $U -batchmode -nographics -quit -projectPath $CL -executeMethod GolfArcade.EditorTools.MatchHeroLockerExport.RunDistance -logFile $O/RunDistance.log
rc=$?; echo "exit $rc $(date +%H:%M:%S)"
grep -n -E "bindpose|Kit_Sock|Exception|error CS" $O/RunDistance.log | head -20
ls $O/export | wc -l
