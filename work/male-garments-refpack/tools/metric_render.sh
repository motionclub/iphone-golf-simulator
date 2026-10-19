#!/bin/zsh
# metric_render.sh <hero> <design> <unity_dir> <tag>: six ortho views of Kit_Shoe_R on magenta + silhouette metric
cd ${0:A:h:h}
../delegation-2026-10-17/heavy.sh blender /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python tools/render_npz.py -- build/m_$4 $3 Kit_Shoe_R:ShoeR ortho=.40 os_front=.36 os_back=.36 os_top=.44 os_sole=.44 dist=1.2 w=760 h=520 samples=8 bg=FF00FF > /dev/null 2>&1
python3 tools/sil_metric.py $2 build/m_$4 build/sil_m_$4.png
