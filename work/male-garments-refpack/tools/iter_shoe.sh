#!/bin/zsh
# iter_shoe.sh <hero> <design> <tag> ['<json SHOE_DESIGN overrides>']: right shoe only, into a scratch CV2_OUT, six views, silhouette metric
set -e
ME=${0:A:h:h}; cd $ME/../clothing-v2
B=($ME/../delegation-2026-10-17/heavy.sh blender /Applications/Blender.app/Contents/MacOS/Blender)
H=$1; DES=$2; TAG=$3; export SHOE_DESIGN=${4:-}; export CV2_OUT=$ME/iter_out
mkdir -p $CV2_OUT/$H/unity; cp $ME/out/$H/unity/cover.npz $CV2_OUT/$H/unity/ 2>/dev/null || true
$B -b --factory-startup --python py/shoe4.py -- $H $DES R $ME/build/it_$TAG.blend > $ME/build/it_$TAG.log 2>&1; grep -E "Traceback|Error" $ME/build/it_$TAG.log && exit 1
$B -b $ME/build/it_$TAG.blend --python py/export2.py -- $H Kit_Shoe_R shoe4 $ME/build/it_${TAG}_final.blend res=1024 > /dev/null 2>&1
CV2_PIECES=Kit_Shoe_R $B -b --factory-startup --python py/maps.py -- $H > /dev/null 2>&1
unset SHOE_DESIGN
cd $ME; ../delegation-2026-10-17/heavy.sh blender /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python tools/render_npz.py -- build/it_$TAG iter_out/$H/unity Kit_Shoe_R:ShoeR ortho=.40 os_front=.36 os_back=.36 os_top=.44 os_sole=.44 dist=1.2 w=760 h=520 samples=16 bg=FF00FF \
  $([[ $H == Golf* ]] && echo trim_Kit_Shoe=1E2A44 base_Kit_Shoe=EFEBE2) > /dev/null 2>&1
python3 tools/sil_metric.py $DES build/it_$TAG build/sil_it_$TAG.png
