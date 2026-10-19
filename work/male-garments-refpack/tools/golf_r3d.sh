#!/bin/zsh
# 10-18 r3d: r3c (short golf socks) under chat 5's new height-map foot rule showed the bare forefoot over the low shoe upper -> refit MG_GM with
# GP_FOOT_ALL=1 (all foot skin inside the shoe footprint hidden; socks + trousers cover the ankle), install golf into the clone, turnaround.
ME=${0:A:h:h}; REPO=${ME:h:h}; P=$REPO/work/clothing-v2/pipeline; HV=$REPO/work/delegation-2026-10-17/heavy.sh; S=$ME/logs/r3d_summary.log
export GOLF_MUTE=1 GP_FOOT_ALL=1; H=GolfKitHero_Male; R=$ME/out
echo "start $(date +%H:%M:%S)" >> $S
cd $P; rm -f runs/MG_GM/$H/Kit_Sock_?.npz
GP_MAX_LIFT=.035 ./garment_fit $H npz:$R/$H/unity/Kit_Sock_L_final.npz@Kit_Sock_L npz:$R/$H/unity/Kit_Sock_R_final.npz@Kit_Sock_R npz:$R/$H/unity/Kit_Bottom_final.npz@Kit_Bottom npz:$R/$H/unity/Kit_Top_final.npz@Kit_Top npz:$R/$H/unity/Kit_Belt_final.npz@Kit_Belt npz:$R/$H/unity/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:$R/$H/unity/Kit_Shoe_R_final.npz@Kit_Shoe_R run=MG_GM resume > logs/MG_GM_r3d.log 2>&1
grep -E "FIT DONE|Traceback|Error|GATE|by victim|HOLES|garment_fit\] done" logs/MG_GM_r3d.log >> $S
grep -h "by victim<\|HOLES" runs/MG_GM/suite/$H/REPORT.md >> $S
[[ -f runs/MG_GM/$H/Kit_Sock_L.npz && -f runs/MG_GM/$H/Kit_Sock_R.npz ]] || { echo "SOCK FIT FAILED" >> $S; exit 1; }
GP_STEP=.2 $ME/tools/install_batch.sh $H:MG_GM:$ME/out film=Drive,IronSwing,Chip look=target >> $S 2>&1 || { echo "INSTALL FAILED" >> $S; exit 1; }
UNITY_PROJECT=$HOME/male-garments-UnityClone TURNAROUND_OUT=$ME/turn/r3d_refpack TURNAROUND_HEROES=$H TURNAROUND_LOOK=refpack TURNAROUND_VIDEO=0 $HV unity $ME/../model-turnaround/run.sh >> $S 2>&1 || echo "TURNAROUND FAILED" >> $S
echo "R3D DONE $(date +%H:%M:%S)" >> $S
