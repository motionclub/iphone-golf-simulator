#!/bin/zsh
# SHOE v3 (designed last, reference 05): build L + R -> export (manifest merged into $CV2_OUT, default out_gp/) -> N / M maps.
#   shoes/run_shoe3.sh <hero> <design>        e.g. MatchHero_Male male_tennis | GolfKitHero_Male male_golf
# Then fit + check + install through the garment pipeline: pipeline/garment_fit <hero> npz:out_gp/<hero>/unity/Kit_Shoe_L_final.npz ...
set -e
cd ${0:A:h:h}
B=(${GP_HEAVY:-${0:A:h}/../../delegation-2026-10-17/heavy.sh} blender /Applications/Blender.app/Contents/MacOS/Blender)
HERO=$1; DES=$2; export CV2_OUT=${CV2_OUT:-$PWD/out_gp}
mkdir -p $CV2_OUT/$HERO/unity logs
# the maps' ambient occlusion sees the worn socks too
for f in out/$HERO/unity/Kit_Sock_*_final.npz(N) out/$HERO/unity/cover.npz(N); do cp $f $CV2_OUT/$HERO/unity/ 2>/dev/null || true; done   # socks + today's cover: the AO must not see the hidden foot
for sd in L R; do
  $B -b --factory-startup --python py/shoe3.py -- $HERO $DES $sd shoes/${HERO}_shoe3_$sd.blend > logs/shoe3-$HERO-$sd.log 2>&1; grep -E "SHOE3|Traceback" logs/shoe3-$HERO-$sd.log
  $B -b shoes/${HERO}_shoe3_$sd.blend --python py/export2.py -- $HERO Kit_Shoe_$sd shoe3 shoes/${HERO}_shoe3_${sd}_final.blend res=1024 > logs/export2-shoe3-$HERO-$sd.log 2>&1; grep -E "EXPORT2|Traceback" logs/export2-shoe3-$HERO-$sd.log
done
CV2_PIECES=Kit_Shoe_L,Kit_Shoe_R $B -b --factory-startup --python py/maps.py -- $HERO > logs/maps-shoe3-$HERO.log 2>&1; grep -E "Kit_Shoe|Traceback" logs/maps-shoe3-$HERO.log | head -4
