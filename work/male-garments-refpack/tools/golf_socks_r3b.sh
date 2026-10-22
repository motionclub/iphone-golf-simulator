#!/bin/zsh
# 10-18 r3b: golf socks were skipped in round 3 (cov_cli new-piece bug, fixed by chat 5 at 01:58). Refit MG_GM with resume (only the socks
# get fitted; cover + suite redo), install the golf hero into the clone, golf turnaround. Waits for the RunDistance check (one heavy job at a time).
ME=${0:A:h:h}; REPO=${ME:h:h}; P=$REPO/work/clothing-v2/pipeline; HV=$REPO/work/delegation-2026-10-17/heavy.sh
LOG=$ME/logs/r3b_summary.log; export GOLF_MUTE=1 GP_FOOT_ALL=1; R=$ME/out
until grep -q "^exit" $ME/logs/verify_rundistance.log; do sleep 30; done
echo "start $(date +%H:%M:%S)" >> $LOG
cd $P
GP_MAX_LIFT=.035 ./garment_fit GolfKitHero_Male npz:$R/GolfKitHero_Male/unity/Kit_Sock_L_final.npz@Kit_Sock_L npz:$R/GolfKitHero_Male/unity/Kit_Sock_R_final.npz@Kit_Sock_R npz:$R/GolfKitHero_Male/unity/Kit_Bottom_final.npz@Kit_Bottom npz:$R/GolfKitHero_Male/unity/Kit_Top_final.npz@Kit_Top npz:$R/GolfKitHero_Male/unity/Kit_Belt_final.npz@Kit_Belt npz:$R/GolfKitHero_Male/unity/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:$R/GolfKitHero_Male/unity/Kit_Shoe_R_final.npz@Kit_Shoe_R run=MG_GM resume > logs/MG_GM_r3b.log 2>&1
grep -E "FIT DONE|Traceback|Error|GATE|by victim|garment_fit\] done" logs/MG_GM_r3b.log >> $LOG
[[ -f runs/MG_GM/GolfKitHero_Male/Kit_Sock_L.npz && -f runs/MG_GM/GolfKitHero_Male/Kit_Sock_R.npz ]] || { echo "SOCK FIT FAILED" >> $LOG; exit 1; }
echo "fit done $(date +%H:%M:%S)" >> $LOG
GP_STEP=.2 $ME/tools/install_batch.sh GolfKitHero_Male:MG_GM:$ME/out film=Drive,IronSwing,Chip look=target >> $LOG 2>&1 || { echo "INSTALL FAILED" >> $LOG; exit 1; }
UNITY_PROJECT=$HOME/male-garments-UnityClone TURNAROUND_OUT=$ME/turn/r3b_refpack TURNAROUND_HEROES=GolfKitHero_Male TURNAROUND_LOOK=refpack TURNAROUND_VIDEO=0 $HV unity $ME/../model-turnaround/run.sh >> $LOG 2>&1 || echo "TURNAROUND FAILED" >> $LOG
echo "R3B DONE $(date +%H:%M:%S)" >> $LOG
