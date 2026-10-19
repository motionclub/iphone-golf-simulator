#!/bin/zsh
# build_shoe.sh <hero> <design> <side> <tag>  -> build/<tag>.blend + build/<tag>.npz (positions, faces, kinds, s4/h4) for the numpy previews
cd ${0:A:h:h}
CV=../clothing-v2
../delegation-2026-10-17/heavy.sh blender /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python $CV/py/shoe4.py -- $1 $2 $3 $PWD/build/$4.blend > build/$4.log 2>&1
grep -E "SHOE4|Traceback|Error" build/$4.log | head -5
../delegation-2026-10-17/heavy.sh blender /Applications/Blender.app/Contents/MacOS/Blender -b $PWD/build/$4.blend --python tools/blend2npz.py -- $PWD/build/$4.npz > build/$4.npz.log 2>&1
grep -E "NPZ|Traceback|Error" build/$4.npz.log | head -5
