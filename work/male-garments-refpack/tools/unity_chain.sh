#!/bin/zsh
# male-garments: everything Unity, in order, each launch through heavy.sh (1 Unity machine-wide). Waits for both fits.
ME=${0:A:h:h}; REPO=${ME:h:h}; P=$REPO/work/clothing-v2/pipeline; CL=$HOME/male-garments-UnityClone; LOG=$ME/logs/chain.log
HV=$REPO/work/delegation-2026-10-17/heavy.sh
mkdir -p $ME/logs; echo "chain start $(date +%H:%M:%S)" >> $LOG
until grep -q "^GM" $P/logs/MG.done 2>/dev/null; do sleep 30; done
grep -E "garment_fit\] done" $P/logs/MG_MT.log $P/logs/MG_GM.log >> $LOG
# the tennis polo keeps its mesh: only its maps change (single collar tip, plain cuffs)
cp $ME/out/MatchHero_Male/unity/Top_N.png $CL/Assets/Resources/Tennis/KitsV2/Male/KitV2_Tennis_Male_Top_N.png
cp $ME/out/MatchHero_Male/unity/Top_M.png $CL/Assets/Resources/Tennis/KitsV2/Male/KitV2_Tennis_Male_Top_M.png
echo "install $(date +%H:%M:%S)" >> $LOG
GP_STEP=.2 $ME/tools/install_batch.sh MatchHero_Male:MG_MT:$ME/out GolfKitHero_Male:MG_GM:$ME/out \
  film=Serve,Overhead,RunForward,ForehandWide,Drive,IronSwing,Emote_Thrust,Intro_Pushups,Emote_Victory look=target >> $LOG 2>&1 || { echo "INSTALL FAILED" >> $LOG; exit 1; }
for look in refpack swatch:F2F2F2,F4F4F4,F6F6F6 swatch:1A1A1A,202020,262626 swatch:E0262B,1E5BE0,1FB04A; do
  tag=${look//[:,]/_}; echo "turnaround $look $(date +%H:%M:%S)" >> $LOG
  UNITY_PROJECT=$CL TURNAROUND_OUT=$ME/turn/$tag TURNAROUND_HEROES=MatchHero_Male,GolfKitHero_Male TURNAROUND_LOOK=$look TURNAROUND_VIDEO=0 \
    $HV unity $REPO/work/model-turnaround/run.sh >> $LOG 2>&1 || echo "TURNAROUND $look FAILED" >> $LOG
  cp $REPO/work/model-turnaround/logs/turnaround.log $ME/logs/turnaround_$tag.log 2>/dev/null
done
echo "lobby $(date +%H:%M:%S)" >> $LOG
$ME/tools/lobby_sync.sh >> $LOG 2>&1 || echo "LOBBY FAILED" >> $LOG
echo "CHAIN DONE $(date +%H:%M:%S)" >> $LOG
