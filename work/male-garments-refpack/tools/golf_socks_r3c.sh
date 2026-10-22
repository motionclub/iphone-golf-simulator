#!/bin/zsh
# 10-18 r3c: golf crew socks (top .288) poked through the slim trousers (205k layer px in MG_GM r3b) -> short male_golf sock (top .170),
# rebuild + trim + export + maps, refit MG_GM (socks only, resume), install golf into the clone, golf turnaround.
ME=${0:A:h:h}; REPO=${ME:h:h}; CV=$REPO/work/clothing-v2; P=$CV/pipeline; HV=$REPO/work/delegation-2026-10-17/heavy.sh
B=($HV blender /Applications/Blender.app/Contents/MacOS/Blender); LOG=$ME/logs/r3c.log; S=$ME/logs/r3c_summary.log
export GOLF_MUTE=1; H=GolfKitHero_Male   # 10-18 02:3x: chat 5 default foot rule = shoe surface above the skin (no GP_FOOT_ALL)
until grep -q "^exit" $ME/logs/verify_rundistance.log; do sleep 20; done   # one heavy job at a time from this chat
echo "start $(date +%H:%M:%S)" >> $S
for sd in L R; do
  (cd $CV && SOCK_FRONT_CUT=.62 $B -b --factory-startup --python py/sock2.py -- $H male_golf $sd $ME/build/${H}_sock_$sd.blend >> $LOG 2>&1)
  $B -b $ME/build/${H}_sock_$sd.blend --python $ME/tools/set_roles.py -- $ME/build/${H}_sock_$sd.blend Kit_Shorts >> $LOG 2>&1
  $B -b $ME/build/${H}_sock_$sd.blend --python $ME/tools/trim_sock.py -- $ME/build/${H}_shoe4_$sd.blend $ME/build/${H}_sock_${sd}_trim.blend .47 .015 >> $LOG 2>&1
  (cd $CV && CV2_OUT=$ME/out $B -b $ME/build/${H}_sock_${sd}_trim.blend --python py/export2.py -- $H Kit_Sock_$sd sock2 $ME/build/${H}_sock_${sd}_final.blend res=1024 wsmooth=4 >> $LOG 2>&1)
done
(cd $CV && CV2_OUT=$ME/out CV2_PIECES=Kit_Sock_L,Kit_Sock_R $B -b --factory-startup --python py/maps.py -- $H >> $LOG 2>&1)
grep -E "SOCK2|TRIMSOCK|EXPORT2 Kit_Sock|ROLES|Traceback" $LOG | tail -10 >> $S
R=$ME/out; cd $P; rm -f runs/MG_GM/$H/Kit_Sock_?.npz
GP_MAX_LIFT=.035 ./garment_fit $H npz:$R/$H/unity/Kit_Sock_L_final.npz@Kit_Sock_L npz:$R/$H/unity/Kit_Sock_R_final.npz@Kit_Sock_R npz:$R/$H/unity/Kit_Bottom_final.npz@Kit_Bottom npz:$R/$H/unity/Kit_Top_final.npz@Kit_Top npz:$R/$H/unity/Kit_Belt_final.npz@Kit_Belt npz:$R/$H/unity/Kit_Shoe_L_final.npz@Kit_Shoe_L npz:$R/$H/unity/Kit_Shoe_R_final.npz@Kit_Shoe_R run=MG_GM resume > logs/MG_GM_r3c.log 2>&1
grep -E "FIT DONE|Traceback|Error|GATE|by victim|garment_fit\] done" logs/MG_GM_r3c.log >> $S
[[ -f runs/MG_GM/$H/Kit_Sock_L.npz && -f runs/MG_GM/$H/Kit_Sock_R.npz ]] || { echo "SOCK FIT FAILED" >> $S; exit 1; }
GP_STEP=.2 $ME/tools/install_batch.sh $H:MG_GM:$ME/out film=Drive,IronSwing,Chip look=target >> $S 2>&1 || { echo "INSTALL FAILED" >> $S; exit 1; }
UNITY_PROJECT=$HOME/male-garments-UnityClone TURNAROUND_OUT=$ME/turn/r3c_refpack TURNAROUND_HEROES=$H TURNAROUND_LOOK=refpack TURNAROUND_VIDEO=0 $HV unity $ME/../model-turnaround/run.sh >> $S 2>&1 || echo "TURNAROUND FAILED" >> $S
echo "R3C DONE $(date +%H:%M:%S)" >> $S
