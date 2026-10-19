#!/bin/zsh
# onbody.sh <hero> <tag> [views] [target] [ortho]: my shoes (out/) + today's other garments (clothing-v2/out) on the dumped body
cd ${0:A:h:h}
H=$1; T=$2; V=${3:-front:0:3,side:90:3,q34:35:8,sideL:-90:3}; TG=${4:-0,-0.02,.20}; OR=${5:-.75}
O=../clothing-v2/out/$H/unity; DD=../clothing-v2/pipeline/dump/$H
P=(Kit_Shoe_R:ShoeR Kit_Shoe_L:ShoeL)
for x in ${=EXTRA:-}; do P+=($x); done
if [[ $H == MatchHero_Male ]]; then P+=("${SOCKDIR:-$O}|Kit_Sock_R:SockR" "${SOCKDIR:-$O}|Kit_Sock_L:SockL" "${BOTDIR:-$O}|Kit_Bottom:Bottom" "${TOPDIR:-$O}|Kit_Top:Top")
else P+=("${BOTDIR:-$O}|Kit_Bottom:Bottom" "${TOPDIR:-$O}|Kit_Top:Top" "${BELTDIR:-$O}|Kit_Belt:Belt"); fi
../delegation-2026-10-17/heavy.sh blender /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python tools/render_npz.py -- build/$T out/$H/unity $P body=$DD mode=views views=$V target=$TG ortho=$OR dist=3 w=900 h=640 ${=ARGS:-} 2>&1 | grep -E "RENDERED|Error|Trace"
python3 - <<PY
from PIL import Image
v='$V'.split(','); ims=[Image.open('build/${T}_%s.png'%x.split(':')[0]) for x in v]
n=len(ims); c=Image.new('RGB',(900*min(n,2),640*((n+1)//2)))
for i,im in enumerate(ims): c.paste(im,((i%2)*900,(i//2)*640))
c.save('build/$T.jpg',quality=88)
PY
