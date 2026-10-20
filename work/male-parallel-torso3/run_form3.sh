#!/bin/bash
# Re-runnable FORM3 pipeline: build -> stage blend+FBX -> audit -> renders -> gates.  usage: ./run_form3.sh [tag]
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-torso3
export PYTHONPATH=$PWD/../male-micro1i/pylib
B=/Applications/Blender.app/Contents/MacOS/Blender; PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
T=${1:-FORM3}
python3 -c "import json; json.dump({'$T': {}}, open('spec_$T.json','w'))"
$PY fast3.py spec_$T.json base_FORM3.json || exit 1
$B -b --factory-startup --python make_blend.py -- baseline/HeroBase_Male_Silhouette.blend data/V_$T.npy export/HeroBase_Male_Silhouette_form3.blend 2>&1 | grep -E "MAKE_BLEND|Error|Traceback"
$B -b --factory-startup --python-exit-code 1 --python export_fbx.py -- export/HeroBase_Male_Silhouette_form3.blend export/HeroBase_Male_Body_form3.fbx export/export_form3.json 2>&1 | grep -E "max_nearest|imported_tris|Error|Traceback"
$B -b --factory-startup --python audit_torso.py -- export/HeroBase_Male_Silhouette_form3.blend proof/male-torso-form3-audit.json r/audit_form3 2>&1 | grep -E "AUDIT_TORSO_DONE|Error|Traceback"
$B -b --factory-startup --python selfisect3.py -- export/HeroBase_Male_Silhouette_form3.blend proof/selfisect_form3.json 2>&1 | grep -E "SELFISECT|Error|Traceback"
./evq3.sh $T 2>&1 | tail -8
./yaws.sh $T
$B -b --factory-startup --python rake.py -- data/V_$T.npy r/${T}k q3f,back,left 2>&1 | grep -E "Error|Traceback"
$PY finalize_form3.py $T 2>&1 | grep -v Warn | cut -c1-400
shasum -a 256 export/HeroBase_Male_Silhouette_form3.blend export/HeroBase_Male_Body_form3.fbx
