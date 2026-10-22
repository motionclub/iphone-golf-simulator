#!/bin/zsh
# MicroF3 -- reproduce the whole run from the staged MicroF1 blend (SHA 4450c644...).  Run from this directory:  zsh run_f3.sh        (SKIP_FIT=0 zsh run_f3.sh  re-solves the contour fit, ~4 min)
# Needs: Blender 5.2.2 at /Applications/Blender.app, system python3 (numpy + Pillow), Blender's python3.13 (+ male-micro1i/pylib Pillow) for proof02.
set -e
cd "$(dirname "$0")"
B=/Applications/Blender.app/Contents/MacOS/Blender
BP=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
[ "$(shasum -a 256 start/F1_STAGED.blend | cut -d' ' -f1)" = "4450c644a895fb5d2962ed76077770ea39af21de81482bb275d02510747f876e" ] || { echo "F1 start blend SHA mismatch"; exit 1; }
[ "$(shasum -a 256 start/F2_STAGED.blend | cut -d' ' -f1)" = "bb629a65b4e64e64fad6e5ab07b8c1e8875ec5acbb0f61667d81ee9717daf3e9" ] || { echo "F2 start blend SHA mismatch"; exit 1; }
mkdir -p data/dump logs export proof renders

# 0. plate measurements used by the build
python3 tools/lip_measure.py > logs/lip_measure.txt                      # data/lip_plate_raw.json (lip borders per column from the front plate)
[ "${SKIP_FIT:-1}" = "0" ] && python3 tools/fit_contour.py --solve | tee logs/fit_contour.txt     # data/fit_contour.json: loft half-width row + bowl/blend refit to the plate's smooth jaw contour (otherwise the stored file is used)

# 1. jaw build (analytic Head2 with the F3 smoothness fixes, vertices slid along their own normals) + analytic shading normals
python3 tools/make_f3.py | tee logs/make_f3.txt                          # -> data/var_f3.npz, data/anorm_f3.npz, data/f3_params.json
# 2. assembly: positions, custom shading normals, paint follows the skin, lip paint rebuilt from the plate-measured plan curves (tools/lips3.py)
$B -b --factory-startup --python tools/assemble3.py -- start/F1_STAGED.blend data/var_f3.npz data/anorm_f3.npz export/HeroBase_Female_MicroF3_head_STAGED.blend export/assemble_report.json | grep -vE "^$|Blender 5|Read blend|build date|quit" | tee logs/assemble3.txt
# 3. gates
$B -b --factory-startup --python tools/dump_full.py -- start/F1_STAGED.blend data/dump/F1 >/dev/null
$B -b --factory-startup --python tools/dump_full.py -- start/F2_STAGED.blend data/dump/F2 >/dev/null
$B -b --factory-startup --python tools/dump_full.py -- export/HeroBase_Female_MicroF3_head_STAGED.blend data/dump/F3 >/dev/null
python3 tools/verify_f3.py | tee logs/verify_f3.txt
cp export/HeroBase_Female_MicroF3_head_STAGED.blend export/work_final.blend; cp data/work_assembled_vmap.json export/work_final_vmap.json
$B -b --factory-startup --python tools/verify_asm.py -- export/work_final.blend data/verify_asm_F3.json | grep -vE "^$|Blender 5|Read blend|build date|quit" | tee logs/verify_asm_vs_ArtDir_start.txt
rm -f export/work_final.blend export/work_final_vmap.json
for N in F1:start/F1_STAGED.blend F2:start/F2_STAGED.blend F3:export/HeroBase_Female_MicroF3_head_STAGED.blend; do T=${N%%:*}; BL=${N#*:}
  $B -b --factory-startup --python tools/sil_body.py -- $BL data/sil_body_$T.json proof/sil/sil_$T 2>&1 | grep -E "^(front|back) rows" | tee logs/sil_body_$T.txt
done
$B -b --factory-startup --python tools/loops_audit.py -- export/HeroBase_Female_MicroF3_head_STAGED.blend data/loops_audit_F3.json 2>&1 | grep -vE "^$|Blender|Read blend|quit|build date" > logs/loops_audit_F3.txt
$B -b --factory-startup --python tools/lips_audit.py -- export/HeroBase_Female_MicroF3_head_STAGED.blend data/lips_audit_F3.json 2>&1 | grep -E "strip|front-ray|plan" | tee logs/lips_audit_F3.txt
python3 tools/jaw_audit.py | tee logs/jaw_audit.txt

# 4. export + proofs
$B -b --factory-startup --python tools/export_fbx.py -- export/HeroBase_Female_MicroF3_head_STAGED.blend export/HeroBase_Female_Body.fbx export/export_report.json | grep EXPORT_JSON | tee logs/export_fbx.txt
$BP tools/proof02.py export/HeroBase_Female_MicroF3_head_STAGED.blend proof/03_match_f_head_F3.png | tail -3
python3 tools/make_proofs3.py
python3 tools/plots3.py
python3 tools/lip_colors.py renders/proof3ba/F2_front.png renders/proof3ba/F3_front.png | tee logs/lip_tones.txt
shasum -a 256 export/HeroBase_Female_MicroF3_head_STAGED.blend export/HeroBase_Female_Body.fbx ../../ArtDir/hero/base_lock/blender/HeroBase_Female.blend
