#!/bin/zsh
# tennis_polo.sh <chat-5 run> <tag>: take chat 5's polo + shorts fit (Kit_Top / Kit_Bottom npz) into MG_MT with my round-8 shoes + socks,
# resume (cover + suite only), install the tennis hero into the clone, film + turnaround.
ME=${0:A:h:h}; P=$ME/../clothing-v2/pipeline; HV=$ME/../delegation-2026-10-17/heavy.sh; K=$1; T=$2; S=$ME/logs/polo_$T.log
export GOLF_MUTE=1 GP_SHOE_SKINW=1; unset GP_FOOT_ALL; R=$ME/out
echo "start $(date +%H:%M:%S) from $K" >> $S
cd $P; cp runs/$K/MatchHero_Male/Kit_Top.npz runs/$K/MatchHero_Male/Kit_Bottom.npz runs/MG_MT/MatchHero_Male/
./garment_fit MatchHero_Male npz:$R/MatchHero_Male/unity/Kit_Sock_L_final.npz@Kit_Sock_L npz:$R/MatchHero_Male/unity/Kit_Sock_R_final.npz@Kit_Sock_R npz:$R/MatchHero_Male/unity/Kit_Bottom_final.npz@Kit_Bottom dump:Kit_Top npz:$R/MatchHero_Male/unity/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:$R/MatchHero_Male/unity/Kit_Shoe_R_final.npz@Kit_Shoe_R run=MG_MT resume > logs/MG_MT_$T.log 2>&1
grep -E "resume|FIT DONE|Traceback|GATE" logs/MG_MT_$T.log >> $S; grep -h "by victim<\|HOLES" runs/MG_MT/suite/MatchHero_Male/REPORT.md >> $S
GP_STEP=.2 $ME/tools/install_batch.sh MatchHero_Male:MG_MT:$ME/out film=Serve,Overhead,RunForward,Thrust look=target >> $S 2>&1 || { echo "INSTALL FAILED" >> $S; exit 1; }
UNITY_PROJECT=$HOME/male-garments-UnityClone TURNAROUND_OUT=$ME/turn/${T}_refpack TURNAROUND_HEROES=MatchHero_Male TURNAROUND_LOOK=refpack TURNAROUND_VIDEO=0 $HV unity $ME/../model-turnaround/run.sh >> $S 2>&1 || echo "TURNAROUND FAILED" >> $S
echo "POLO DONE $(date +%H:%M:%S)" >> $S
