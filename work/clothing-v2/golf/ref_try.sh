#!/bin/zsh
# female tennis top vs sheet 09: golf/ref_try.sh <tag> ['{"design": overrides}']  -> golf/ref/<tag>.png (front, side, back, front-left on the body)
cd ${0:A:h:h}; mkdir -p golf/ref logs
B=/Applications/Blender.app/Contents/MacOS/Blender
TANK_DESIGN=${2:-'{}'} $B -b --factory-startup --python py/tank_ref.py -- golf/ref/$1.blend golf_top > logs/golfref_$1.log 2>&1; grep -E "TANKREF|Traceback|Error" logs/golfref_$1.log | head -3
CV2_TGT=0,-0.01,1.17 CV2_DIST=1.55 CV2_CLOTH=E07055 $B -b golf/ref/$1.blend --python py/look.py -- GolfKitHero_Female golf/ref $1 1 front,side,back,fl > logs/golfref_look_$1.log 2>&1; grep -E "Traceback" logs/golfref_look_$1.log
ls golf/ref/$1* | head
cd golf/ref && python3 ../../py/montage.py $1.png 4 $1_front.png $1_side.png $1_back.png $1_fl.png
