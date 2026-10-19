#!/bin/zsh
# round 3 (10-18): silhouette-pass shoes + golf socks (trouser colour) -> refits -> Unity install, turnarounds, metric renders, lobby
set -e
ME=${0:A:h:h}; CV=$ME/../clothing-v2; P=$CV/pipeline; LOG=$ME/logs/round3.log; HV=$ME/../delegation-2026-10-17/heavy.sh; B=($HV blender /Applications/Blender.app/Contents/MacOS/Blender)
echo "start $(date +%H:%M:%S)" >> $LOG
$ME/tools/run_shoe4.sh MatchHero_Male male_tennis 2048 >> $LOG 2>&1
$ME/tools/run_shoe4.sh GolfKitHero_Male male_golf 2048 >> $LOG 2>&1
# golf socks: the crew sock on the golf hero, roles -> Kit_Shorts (it reads as the trouser leg and follows the trouser colour pick)
for sd in L R; do
  (cd $CV && SOCK_FRONT_CUT=.62 $B -b --factory-startup --python py/sock2.py -- GolfKitHero_Male male_crew $sd $ME/build/GolfKitHero_Male_sock_$sd.blend >> $LOG 2>&1)
  $B -b $ME/build/GolfKitHero_Male_sock_$sd.blend --python $ME/tools/set_roles.py -- $ME/build/GolfKitHero_Male_sock_$sd.blend Kit_Shorts >> $LOG 2>&1
done
for H in MatchHero_Male GolfKitHero_Male; do for sd in L R; do
  $B -b $ME/build/${H}_sock_$sd.blend --python $ME/tools/trim_sock.py -- $ME/build/${H}_shoe4_$sd.blend $ME/build/${H}_sock_${sd}_trim.blend .47 .015 >> $LOG 2>&1
  (cd $CV && CV2_OUT=$ME/out $B -b $ME/build/${H}_sock_${sd}_trim.blend --python py/export2.py -- $H Kit_Sock_$sd sock2 $ME/build/${H}_sock_${sd}_final.blend res=1024 wsmooth=4 >> $LOG 2>&1)
done
  (cd $CV && CV2_OUT=$ME/out CV2_PIECES=Kit_Sock_L,Kit_Sock_R,Kit_Shoe_L,Kit_Shoe_R $B -b --factory-startup --python py/maps.py -- $H >> $LOG 2>&1)
done
grep -E "SHOE4 .* R|TRIMSOCK|EXPORT2 Kit_Sock|ROLES|Traceback" $LOG | tail -12 >> $ME/logs/round3_summary.log
echo "builds done $(date +%H:%M:%S)" >> $LOG
cd $P; export GP_FOOT_ALL=1; R=$ME/out
rm -f runs/MG_MT/MatchHero_Male/Kit_Sock_?.npz runs/MG_MT/MatchHero_Male/Kit_Shoe_?.npz runs/MG_GM/GolfKitHero_Male/Kit_Shoe_?.npz
./garment_fit MatchHero_Male npz:$R/MatchHero_Male/unity/Kit_Sock_L_final.npz@Kit_Sock_L npz:$R/MatchHero_Male/unity/Kit_Sock_R_final.npz@Kit_Sock_R npz:$R/MatchHero_Male/unity/Kit_Bottom_final.npz@Kit_Bottom dump:Kit_Top npz:$R/MatchHero_Male/unity/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:$R/MatchHero_Male/unity/Kit_Shoe_R_final.npz@Kit_Shoe_R run=MG_MT resume > logs/MG_MT_r3.log 2>&1
grep -E "GATE|garment_fit\] done" logs/MG_MT_r3.log >> $LOG
GP_MAX_LIFT=.035 ./garment_fit GolfKitHero_Male npz:$R/GolfKitHero_Male/unity/Kit_Sock_L_final.npz@Kit_Sock_L npz:$R/GolfKitHero_Male/unity/Kit_Sock_R_final.npz@Kit_Sock_R npz:$R/GolfKitHero_Male/unity/Kit_Bottom_final.npz@Kit_Bottom npz:$R/GolfKitHero_Male/unity/Kit_Top_final.npz@Kit_Top npz:$R/GolfKitHero_Male/unity/Kit_Belt_final.npz@Kit_Belt npz:$R/GolfKitHero_Male/unity/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:$R/GolfKitHero_Male/unity/Kit_Shoe_R_final.npz@Kit_Shoe_R run=MG_GM resume > logs/MG_GM_r3.log 2>&1
grep -E "GATE|garment_fit\] done" logs/MG_GM_r3.log >> $LOG
echo "fits done $(date +%H:%M:%S)" >> $LOG
GP_STEP=.2 $ME/tools/install_batch.sh MatchHero_Male:MG_MT:$ME/out GolfKitHero_Male:MG_GM:$ME/out film=Serve,Overhead,RunForward,Drive,IronSwing look=target >> $LOG 2>&1 || { echo "INSTALL FAILED" >> $LOG; exit 1; }
for look in refpack swatch:1A1A1A,202020,262626; do tag=${look//[:,]/_}
  UNITY_PROJECT=$HOME/male-garments-UnityClone TURNAROUND_OUT=$ME/turn/r3_$tag TURNAROUND_HEROES=MatchHero_Male,GolfKitHero_Male TURNAROUND_LOOK=$look TURNAROUND_VIDEO=0 $HV unity $ME/../model-turnaround/run.sh >> $LOG 2>&1 || echo "TURNAROUND $look FAILED" >> $LOG
done
$ME/tools/metric_render.sh MatchHero_Male male_tennis out/MatchHero_Male/unity r3t >> $LOG 2>&1
$ME/tools/metric_render.sh GolfKitHero_Male male_golf out/GolfKitHero_Male/unity r3g >> $LOG 2>&1
echo "ROUND3 DONE $(date +%H:%M:%S)" >> $LOG
