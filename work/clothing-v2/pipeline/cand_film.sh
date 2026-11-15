#!/bin/zsh
# cand_film.sh <run> [env...]: put runs/<run>/MatchHero_Male/Kit_Top.npz into the CLONE only (final-plan-dev) and film his serve there
# (work/polo-tear-1113/<run>/cand). The repo's Unity/ is never touched. 11-14 polo armpit.
set -e
P=${0:A:h}; cd $P; RUN=$1; shift
REPO=$P/../../..; C=$HOME/unity-clones/final-plan-dev/Unity; U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
OUTD=$P/out/_cand_$RUN; rm -rf $OUTD; mkdir -p $OUTD/MatchHero_Male
GP_OUT_DIR=$OUTD python3 gp/export.py MatchHero_Male runs/$RUN | tail -1
rm -f $C/Temp/UnityLockfile
GOLF_MUTE=1 GP_INSTALL_REST_TOL=0.1 GP_OUT=$OUTD GP_HEROES=MatchHero_Male $REPO/work/delegation-2026-10-17/heavy.sh unity $U -batchmode -quit -projectPath $C \
  -executeMethod GolfArcade.EditorTools.GarmentPipelineInstall.Run -logFile $OUTD/gpinstall.log > /dev/null 2>&1 || { grep -E "error CS|Exception" $OUTD/gpinstall.log | head; exit 1; }
head -2 $OUTD/install_report.txt
cd $REPO/work/polo-tear-1113; CAND_ENV="${*:-X_NONE=1}" ONLY=cand ./ab.sh $RUN > $RUN.out 2>&1; tail -2 $RUN/status.txt
