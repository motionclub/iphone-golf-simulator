#!/bin/zsh
# run_trousers.sh <design.json> [steps=build,export,maps]: slim golf trousers (pants2 golf_male_trousers + PANTS_DESIGN overrides)
#   -> build/golf_trousers*.blend -> export2 (trousers2) -> Bottom N/M maps, into work/male-garments-refpack/out/GolfKitHero_Male/unity
set -e
ME=${0:A:h:h}; DJ=${1:A}; ST=${2:-build,export,maps}      # resolve BEFORE cd
cd $ME/../clothing-v2
B=($ME/../delegation-2026-10-17/heavy.sh blender /Applications/Blender.app/Contents/MacOS/Blender)
HERO=GolfKitHero_Male; export CV2_OUT=$ME/out; BL=$ME/build; T=$BL/golf_trousers
[[ $CV2_OUT == */male-garments-refpack/out ]] || { echo 'refusing: CV2_OUT not in male-garments-refpack'; exit 2; }
mkdir -p $CV2_OUT/$HERO/unity
if [[ $ST == *build* ]]; then
  PANTS_DESIGN="$(cat $DJ)" $B -b --factory-startup --python py/pants2.py -- $HERO golf_male_trousers $T.blend > $BL/pants2-golf.log 2>&1 || true
  grep -E "CAGE|FIT|LOOPS|PANTS" $BL/pants2-golf.log; grep -q Traceback $BL/pants2-golf.log && { grep -A12 Traceback $BL/pants2-golf.log; exit 1; }
fi
if [[ $ST == *export* ]]; then
  cp $T.blend ${T}_export.blend
  CV2_WSMOOTH=6 $B -b ${T}_export.blend --python py/export2.py -- $HERO Kit_Bottom trousers2 ${T}_final.blend > $BL/export2-golf-bottom.log 2>&1; grep -E "EXPORT2|Traceback" $BL/export2-golf-bottom.log
fi
if [[ $ST == *maps* ]]; then
  CV2_PIECES=Kit_Bottom $B -b --factory-startup --python py/maps.py -- $HERO > $BL/maps-golf-bottom.log 2>&1; grep -E "Kit_Bottom|Traceback|Error" $BL/maps-golf-bottom.log | head -6
fi
