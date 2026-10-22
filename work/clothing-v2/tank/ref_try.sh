#!/bin/zsh
# female tennis top vs sheet 09: tank/ref_try.sh <tag> ['{"design": overrides}']  -> tank/ref/<tag>.png (front, side, back, front-left on the body)
cd ${0:A:h:h}; mkdir -p tank/ref logs
B=(${GP_HEAVY:-${0:A:h}/../../delegation-2026-10-17/heavy.sh} blender /Applications/Blender.app/Contents/MacOS/Blender)
TANK_DESIGN=${2:-'{}'} $B -b --factory-startup --python py/tank_ref.py -- tank/ref/$1.blend > logs/tankref_$1.log 2>&1; grep -E "TANKREF|Traceback|Error" logs/tankref_$1.log | head -3
CV2_TGT=0,-0.01,1.17 CV2_DIST=1.55 CV2_CLOTH=B9CC4C $B -b tank/ref/$1.blend --python py/look.py -- MatchHero_Female tank/ref $1 1 front,side,back,fl > logs/tankref_look_$1.log 2>&1; grep -E "Traceback" logs/tankref_look_$1.log
ls tank/ref/$1* | head
cd tank/ref && python3 ../../py/montage.py $1.png 4 $1_front.png $1_side.png $1_back.png $1_fl.png
