#!/bin/zsh
# round 2 (after the OOM): refit the trimmed socks (tennis) + the taller-tongue golf shoes, then Unity install, sheet-colour turnaround, lobby
ME=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-garments-refpack; P=$ME/../clothing-v2/pipeline; LOG=$ME/logs/round2.log; cd $P; export GP_FOOT_ALL=1
echo "fit MT $(date +%H:%M:%S)" >> $LOG
./garment_fit MatchHero_Male npz:/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-garments-refpack/out/MatchHero_Male/unity/Kit_Sock_L_final.npz@Kit_Sock_L npz:/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-garments-refpack/out/MatchHero_Male/unity/Kit_Sock_R_final.npz@Kit_Sock_R npz:/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-garments-refpack/out/MatchHero_Male/unity/Kit_Bottom_final.npz@Kit_Bottom dump:Kit_Top npz:/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-garments-refpack/out/MatchHero_Male/unity/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-garments-refpack/out/MatchHero_Male/unity/Kit_Shoe_R_final.npz@Kit_Shoe_R run=MG_MT resume > logs/MG_MT_r2.log 2>&1
grep -E "GATE|garment_fit\] done" logs/MG_MT_r2.log >> $LOG
echo "fit GM $(date +%H:%M:%S)" >> $LOG
./garment_fit GolfKitHero_Male dump:Kit_Bottom npz:/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-garments-refpack/out/GolfKitHero_Male/unity/Kit_Top_final.npz@Kit_Top npz:/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-garments-refpack/out/GolfKitHero_Male/unity/Kit_Belt_final.npz@Kit_Belt npz:/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-garments-refpack/out/GolfKitHero_Male/unity/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-garments-refpack/out/GolfKitHero_Male/unity/Kit_Shoe_R_final.npz@Kit_Shoe_R run=MG_GM resume > logs/MG_GM_r2.log 2>&1
grep -E "GATE|garment_fit\] done" logs/MG_GM_r2.log >> $LOG
echo "install $(date +%H:%M:%S)" >> $LOG
GP_STEP=.2 $ME/tools/install_batch.sh MatchHero_Male:MG_MT:$ME/out GolfKitHero_Male:MG_GM:$ME/out film=Serve,Overhead,RunForward,Drive,IronSwing look=target >> $LOG 2>&1 || { echo "INSTALL FAILED" >> $LOG; exit 1; }
echo "turnaround $(date +%H:%M:%S)" >> $LOG
UNITY_PROJECT=$HOME/male-garments-UnityClone TURNAROUND_OUT=$ME/turn/refpack2 TURNAROUND_HEROES=MatchHero_Male,GolfKitHero_Male TURNAROUND_LOOK=refpack TURNAROUND_VIDEO=0   $ME/../delegation-2026-10-17/heavy.sh unity $ME/../model-turnaround/run.sh >> $LOG 2>&1 || echo "TURNAROUND FAILED" >> $LOG
UNITY_PROJECT=$HOME/male-garments-UnityClone TURNAROUND_OUT=$ME/turn/dark2 TURNAROUND_HEROES=MatchHero_Male TURNAROUND_LOOK=swatch:1A1A1A,202020,262626 TURNAROUND_VIDEO=0   $ME/../delegation-2026-10-17/heavy.sh unity $ME/../model-turnaround/run.sh >> $LOG 2>&1 || echo "TURNAROUND2 FAILED" >> $LOG
echo "lobby $(date +%H:%M:%S)" >> $LOG
$ME/tools/lobby_sync.sh >> $LOG 2>&1 || echo "LOBBY FAILED" >> $LOG
echo "ROUND2 DONE $(date +%H:%M:%S)" >> $LOG
