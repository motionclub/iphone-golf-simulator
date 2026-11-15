#!/bin/zsh
# sync_menus.sh: the iOS menu / locker / lobby heroes re-exported from the installed game project (work/hero-sync/sync_heroes.sh for
# tennis, tennis distance and golf, then the bowling kit heroes, which that script does not cover). Uses the plan's project copy and the gate.
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; W=$REPO/work/final-plan-1111
export UNITY=$W/unity_gated.sh HERO_SYNC_CLONE=$HOME/unity-clones/final-plan-dev/Unity GOLF_MUTE=1
rm -f $HERO_SYNC_CLONE/Temp/UnityLockfile
zsh $REPO/work/hero-sync/sync_heroes.sh || { echo "SYNC FAILED"; exit 1; }
echo "== bowling kit heroes"
BO=$W/menus_bowling_export; rm -rf $BO; mkdir -p $BO
MH_LOCKER_FACE_PARITY=0 MH_LOCKER_OUT=$BO MH_LOCKER_REPORT=$W/logs/menus_bowling_report.txt $UNITY -batchmode -nographics -quit -projectPath $HERO_SYNC_CLONE -executeMethod GolfArcade.EditorTools.MatchHeroLockerExport.RunBowling -logFile $W/logs/menus_bowling.log || { echo "BOWLING EXPORT FAILED"; exit 1; }
n=0; for f in $BO/*.*; do t=$REPO/GolfArcade/Unity/CharacterAssets/${f:t}; [[ -f $t ]] || continue; cmp -s $f $t || { cp $f $t; echo "  updated ${f:t}"; n=$((n+1)); }; done   # (only files the app already ships: the bowling swing frames are not installed)
echo "  $n bowling file(s) changed"; echo "MENUS SYNC DONE"
