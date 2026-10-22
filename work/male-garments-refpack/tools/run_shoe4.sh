#!/bin/zsh
# run_shoe4.sh <hero> <design> [res]: build L + R (shoe4) -> export2 (detail shoe4) -> N / M maps, into work/male-garments-refpack/out/<hero>/unity
set -e
ME=${0:A:h:h}                      # resolve BEFORE cd (a relative $0 resolved after the cd wrote into clothing-v2/out once)
cd $ME/../clothing-v2
B=($ME/../delegation-2026-10-17/heavy.sh blender /Applications/Blender.app/Contents/MacOS/Blender)
HERO=$1; DES=$2; RES=${3:-1024}; export CV2_OUT=$ME/out; BL=$ME/build
[[ $CV2_OUT == */male-garments-refpack/out ]] || { echo 'refusing: CV2_OUT not in male-garments-refpack'; exit 2; }
mkdir -p $CV2_OUT/$HERO/unity $BL
for f in out/$HERO/unity/Kit_Sock_*_final.npz(N) out/$HERO/unity/cover.npz(N); do cp $f $CV2_OUT/$HERO/unity/ 2>/dev/null || true; done
for sd in L R; do
  $B -b --factory-startup --python py/shoe4.py -- $HERO $DES $sd $BL/${HERO}_shoe4_$sd.blend > $BL/shoe4-$HERO-$sd.log 2>&1; grep -E "SHOE4|Traceback" $BL/shoe4-$HERO-$sd.log
  $B -b $BL/${HERO}_shoe4_$sd.blend --python py/export2.py -- $HERO Kit_Shoe_$sd shoe4 $BL/${HERO}_shoe4_${sd}_final.blend res=$RES > $BL/export2-shoe4-$HERO-$sd.log 2>&1; grep -E "EXPORT2|Traceback" $BL/export2-shoe4-$HERO-$sd.log
done
CV2_PIECES=Kit_Shoe_L,Kit_Shoe_R $B -b --factory-startup --python py/maps.py -- $HERO > $BL/maps-shoe4-$HERO.log 2>&1; grep -E "Kit_Shoe|Traceback|Error" $BL/maps-shoe4-$HERO.log | head -6
