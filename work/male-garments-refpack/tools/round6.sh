#!/bin/zsh
# round 4 (10-18 04:3x): ENCLOSED shoes (shoe4 'enclose': the upper clears the cartoon foot top + 6 mm to the toe tip; hiding the forefoot under a
# low upper (GP_FOOT_ALL) opened real see-through gaps) -> socks re-trimmed (tennis crew, golf short) -> refits WITHOUT GP_FOOT_ALL
# (tennis: polo + shorts from chat 5's K5c_MT fit) -> one Unity install, turnarounds, metric renders. One heavy job at a time.
ME=${0:A:h:h}; CV=$ME/../clothing-v2; P=$CV/pipeline; LOG=$ME/logs/round6.log; S=$ME/logs/round6_summary.log
HV=$ME/../delegation-2026-10-17/heavy.sh; B=($HV blender /Applications/Blender.app/Contents/MacOS/Blender); export GOLF_MUTE=1; unset GP_FOOT_ALL
echo "start $(date +%H:%M:%S)" >> $S
$ME/tools/run_shoe4.sh MatchHero_Male male_tennis 2048 >> $LOG 2>&1 || { echo "SHOE tennis FAILED" >> $S; exit 1; }
$ME/tools/run_shoe4.sh GolfKitHero_Male male_golf 2048 >> $LOG 2>&1 || { echo "SHOE golf FAILED" >> $S; exit 1; }
for H in MatchHero_Male GolfKitHero_Male; do for sd in L R; do
  $B -b $ME/build/${H}_sock_$sd.blend --python $ME/tools/trim_sock.py -- $ME/build/${H}_shoe4_$sd.blend $ME/build/${H}_sock_${sd}_trim.blend .47 .015 >> $LOG 2>&1
  (cd $CV && CV2_OUT=$ME/out $B -b $ME/build/${H}_sock_${sd}_trim.blend --python py/export2.py -- $H Kit_Sock_$sd sock2 $ME/build/${H}_sock_${sd}_final.blend res=1024 wsmooth=4 >> $LOG 2>&1)
done
  (cd $CV && CV2_OUT=$ME/out CV2_PIECES=Kit_Sock_L,Kit_Sock_R,Kit_Shoe_L,Kit_Shoe_R $B -b --factory-startup --python py/maps.py -- $H >> $LOG 2>&1)
done
grep -E "SHOE4 .* R|TRIMSOCK|EXPORT2 Kit_Sock|Traceback" $LOG | tail -10 >> $S
echo "builds done $(date +%H:%M:%S)" >> $S
R=$ME/out; cd $P
rm -f runs/MG_MT/MatchHero_Male/Kit_{Sock,Shoe}_?.npz runs/MG_GM/GolfKitHero_Male/Kit_{Sock,Shoe}_?.npz
./garment_fit MatchHero_Male npz:$R/MatchHero_Male/unity/Kit_Sock_L_final.npz@Kit_Sock_L npz:$R/MatchHero_Male/unity/Kit_Sock_R_final.npz@Kit_Sock_R npz:$R/MatchHero_Male/unity/Kit_Bottom_final.npz@Kit_Bottom dump:Kit_Top npz:$R/MatchHero_Male/unity/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:$R/MatchHero_Male/unity/Kit_Shoe_R_final.npz@Kit_Shoe_R run=MG_MT resume > logs/MG_MT_r6.log 2>&1
grep -E "resume|FIT DONE|Traceback|GATE" logs/MG_MT_r6.log >> $S; grep -h "by victim<\|HOLES" runs/MG_MT/suite/MatchHero_Male/REPORT.md >> $S
GP_MAX_LIFT=.035 ./garment_fit GolfKitHero_Male npz:$R/GolfKitHero_Male/unity/Kit_Sock_L_final.npz@Kit_Sock_L npz:$R/GolfKitHero_Male/unity/Kit_Sock_R_final.npz@Kit_Sock_R npz:$R/GolfKitHero_Male/unity/Kit_Bottom_final.npz@Kit_Bottom npz:$R/GolfKitHero_Male/unity/Kit_Top_final.npz@Kit_Top npz:$R/GolfKitHero_Male/unity/Kit_Belt_final.npz@Kit_Belt npz:$R/GolfKitHero_Male/unity/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:$R/GolfKitHero_Male/unity/Kit_Shoe_R_final.npz@Kit_Shoe_R run=MG_GM resume > logs/MG_GM_r6.log 2>&1
grep -E "resume|FIT DONE|Traceback|GATE" logs/MG_GM_r6.log >> $S; grep -h "by victim<\|HOLES" runs/MG_GM/suite/GolfKitHero_Male/REPORT.md >> $S
for H in MatchHero_Male GolfKitHero_Male; do r=MG_MT; [[ $H == Golf* ]] && r=MG_GM
  for p in Kit_Sock_L Kit_Sock_R Kit_Shoe_L Kit_Shoe_R; do [[ -f runs/$r/$H/$p.npz ]] || { echo "FIT $H $p FAILED" >> $S; exit 1; }; done; done
echo "fits done $(date +%H:%M:%S)" >> $S
GP_STEP=.2 $ME/tools/install_batch.sh MatchHero_Male:MG_MT:$ME/out GolfKitHero_Male:MG_GM:$ME/out film=Serve,Overhead,RunForward,Drive,IronSwing look=target >> $LOG 2>&1 || { echo "INSTALL FAILED" >> $S; exit 1; }
grep -E "HIDE|perf|driver_ms" $LOG | tail -20 >> $S
for look in refpack swatch:1A1A1A,202020,262626; do tag=${look//[:,]/_}
  UNITY_PROJECT=$HOME/male-garments-UnityClone TURNAROUND_OUT=$ME/turn/r6_$tag TURNAROUND_HEROES=MatchHero_Male,GolfKitHero_Male TURNAROUND_LOOK=$look TURNAROUND_VIDEO=0 $HV unity $ME/../model-turnaround/run.sh >> $LOG 2>&1 || echo "TURNAROUND $look FAILED" >> $S
done
$ME/tools/metric_render.sh MatchHero_Male male_tennis out/MatchHero_Male/unity r6t >> $S 2>&1
$ME/tools/metric_render.sh GolfKitHero_Male male_golf out/GolfKitHero_Male/unity r6g >> $S 2>&1
echo "ROUND6 DONE $(date +%H:%M:%S)" >> $S
