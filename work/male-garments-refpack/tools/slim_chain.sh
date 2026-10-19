#!/bin/zsh
# after fit_gm_trousers.sh: install the golf male set (slim trousers) in ~/male-garments-UnityClone, refpack turnaround, compare to sheet 03
ME=${0:A:h:h}; LOG=$ME/logs/slim_chain.log; cd $ME
echo "install $(date +%H:%M:%S)" >> $LOG
GP_STEP=.2 tools/install_batch.sh GolfKitHero_Male:MG_GM:$ME/out steps=cv2,install,perf >> $LOG 2>&1 || { echo "INSTALL FAILED" >> $LOG; exit 1; }
echo "turnaround $(date +%H:%M:%S)" >> $LOG
rm -rf turn/slim
UNITY_PROJECT=$HOME/male-garments-UnityClone TURNAROUND_OUT=$ME/turn/slim TURNAROUND_HEROES=GolfKitHero_Male TURNAROUND_LOOK=refpack TURNAROUND_VIDEO=0 \
  $ME/../delegation-2026-10-17/heavy.sh unity $ME/../model-turnaround/run.sh >> $LOG 2>&1 || { echo "TURNAROUND FAILED" >> $LOG; exit 1; }
python3 tools/compose_full.py 03-golf-cardinal-master turn/slim/GolfKitHero_Male/ready_full proof/unity/golf_unity_vs_03.jpg \
  "sheet 03 (left of each pair) vs UNITY in-game render, slim trousers v3 (game shaders, rest pose, sheet example colours)" >> $LOG 2>&1
echo "SLIM CHAIN DONE $(date +%H:%M:%S)" >> $LOG
