#!/bin/bash
# FORM3 staging pipeline: params_final.json -> candidate -> blend -> verify -> dump -> audit -> native silhouettes -> FBX -> self-intersection -> weld check
set -e
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; W3=$R/work/male-hands-form3; BL=/Applications/Blender.app/Contents/MacOS/Blender
P="$(cat $W3/params_final.json)"
$W3/py.sh $W3/run_metrics.py final "$P" $W3/data/metrics_final.json | grep -E "tris|roi"
$W3/py.sh $W3/allmetrics.py final "$P" $W3/data/allmetrics_final.json >/dev/null
$W3/py.sh $W3/allmetrics.py FORM2 '{}' $W3/data/allmetrics_FORM2.json >/dev/null
cp -p $W3/baseline/HeroBase_Male_Silhouette.blend $W3/export/_work.blend
$BL -b $W3/export/_work.blend --python $W3/write_blend.py -- $W3/data/cand_final.npz $W3/export/HeroBase_Male_Silhouette_form3.blend $W3/data/removed_both.npy 2>&1 | grep -E "WROTE|Traceback|Error"
rm -f $W3/export/_work.blend
$BL -b $W3/export/HeroBase_Male_Silhouette_form3.blend --python $W3/verify_blend.py -- $W3/data/cand_final.npz $W3/data/mesh_cur.npz $W3/data/verify_final.json >/dev/null 2>&1
$BL -b $W3/export/HeroBase_Male_Silhouette_form3.blend --python $W3/dump_mesh.py -- $W3/data/mesh_staged.npz >/dev/null 2>&1
$W3/py.sh $W3/audit3.py $W3/data/mesh_staged.npz $W3/data/audit_final.json | grep -E "all_conditions|moved_outside|weld_ring_moved"
rm -rf $W3/proof/sil_native_after; mkdir -p $W3/proof/sil_native_after
$BL -b $W3/export/HeroBase_Male_Silhouette_form3.blend --python $W3/sil_native.py -- $W3/proof/sil_native_after 2>&1 | grep -E "SIL_NATIVE_DONE|Error"
$W3/py.sh $W3/sil_native_score.py $W3/proof/sil_native_before $W3/proof/sil_native_after | sed "s#$W3/##"
$BL -b --factory-startup --python $W3/export_fbx.py -- $W3/export/HeroBase_Male_Silhouette_form3.blend $W3/export/HeroBase_Male_Body_form3.fbx $W3/data/fbx_report_final.json 2>&1 | grep -E "fbx_sha256|imported_verts|imported_tris|max_nearest"
$BL -b --factory-startup --python $W3/selfisect3.py -- final $W3/data/selfisect_final.json 2>&1 | grep SELFISECT
$W3/py.sh $W3/weldcheck.py $W3/data/mesh_cur.npz $W3/data/weld_FORM2.json >/dev/null
$W3/py.sh $W3/weldcheck.py $W3/data/mesh_staged.npz $W3/data/weld_final.json
$W3/py.sh $W3/palmvol.py $W3/params_final.json | head -1
shasum -a 256 $W3/export/HeroBase_Male_Silhouette_form3.blend $W3/export/HeroBase_Male_Body_form3.fbx
