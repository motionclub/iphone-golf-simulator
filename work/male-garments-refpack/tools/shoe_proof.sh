#!/bin/zsh
# shoe_proof.sh <hero> <design> <tag> [extra render args]: render R shoe 6 views (ortho) + compose vs the sheet
cd ${0:A:h:h}
../delegation-2026-10-17/heavy.sh blender /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python tools/render_npz.py -- build/$3 out/$1/unity Kit_Shoe_R:ShoeR ortho=.40 os_front=.30 os_back=.30 dist=1.2 w=760 h=520 ${@:4} 2>&1 | grep -E "RENDERED|Error"
python3 tools/compose_shoe.py $2 build/$3 build/$3_vs.jpg "$2 $3 vs sheet"
