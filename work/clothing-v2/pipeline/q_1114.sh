#!/bin/bash
# q_1114.sh (2026-11-14, Adnan: "resume pipeline"): re-fit his tennis polo and her tennis tank on the CURRENT bodies (HeroStudio 11-12).
#   1. wait for the menu re-export (same project copy), 2. dump both tennis heroes from the installed game into dump/ (the 10-17 dump kept as
#   dump_1017/), 3. new stress libraries, 4. full fits (fit + cover + 153-pose suite): N1_MT (male, GP_BULGE .10, 32 shapes, his other pieces'
#   weights kept) then N1_FT (female, limb root, GP_BULGE .06, 32 shapes, skirt + shoes kept). Every Unity / Blender launch goes through heavy.sh.
set -u
P=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/clothing-v2/pipeline; cd $P
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
C=$HOME/unity-clones/final-plan-dev/Unity; U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity; H=$REPO/work/delegation-2026-10-17/heavy.sh
L=$P/logs/q_1114; mkdir -p $L; export GOLF_MUTE=1
say() { echo "$(date +%H:%M:%S) $*" | tee -a $L/status.txt; }
while pgrep -f "sync_menus.sh" >/dev/null; do sleep 20; done
say "menu export finished; dumping"
cp $P/unity/GarmentPipelineDump.cs $C/Assets/Editor/GarmentPipelineDump.cs
cp $REPO/Unity/Assets/Editor/GarmentPipelineInstall.cs $C/Assets/Editor/GarmentPipelineInstall.cs
if [ ! -d $P/dump_1017 ]; then mv $P/dump $P/dump_1017; fi
mkdir -p $P/dump; rm -f $C/Temp/UnityLockfile
GP_OUT=$P/dump GP_HEROES=MatchHero_Male,MatchHero_Female FEMALE_ALIVE=0 $H unity $U -batchmode -projectPath $C \
  -executeMethod GolfArcade.EditorTools.GarmentPipelineDump.Run -logFile $L/dump.log
say "dump exit $? ; compile errors $(grep -c 'error CS' $L/dump.log); heroes $(ls $P/dump | tr '\n' ' ')"
[ -f $P/dump/MatchHero_Male/hero.json ] || { say "DUMP FAILED"; exit 1; }
for h in MatchHero_Male MatchHero_Female; do python3 gp/stress.py $h > $L/stress_$h.log 2>&1; say "stress $h exit $?"; done
GP_BULGE=.10 GP_SHAPES=32 ./garment_fit MatchHero_Male dump:Kit_Top dump:Kit_Bottom dump:Kit_Sock_L dump:Kit_Sock_R dump:Kit_Shoe_L dump:Kit_Shoe_R \
  keep=Kit_Bottom,Kit_Sock_L,Kit_Sock_R,Kit_Shoe_L,Kit_Shoe_R run=N1_MT > $L/N1_MT.log 2>&1
say "N1_MT exit $?"
GP_LIMB_ROOT=1 GP_BULGE=.06 GP_SHAPES=32 ./garment_fit MatchHero_Female dump:Kit_Top dump:Kit_Bottom dump:Kit_Shoe_L dump:Kit_Shoe_R \
  keep=Kit_Bottom,Kit_Shoe_L,Kit_Shoe_R run=N1_FT > $L/N1_FT.log 2>&1
say "N1_FT exit $?"
say "Q_1114 DONE"
