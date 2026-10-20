#!/bin/zsh
# MicroF2 — reproduce the whole run from the staged MicroF1 blend (SHA 4450c644...).  Run from this directory:  zsh run_all.sh
# Needs: Blender 5.2.2 at /Applications/Blender.app, system python3 (numpy + Pillow), Blender's python3.13 (+ male-micro1i/pylib Pillow) for proof02.
set -e
cd "$(dirname "$0")"
B=/Applications/Blender.app/Contents/MacOS/Blender
BP=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13

# 0. start state (immutable copy) + dumps used by the analysis
[ "$(shasum -a 256 start/F1_STAGED.blend | cut -d' ' -f1)" = "4450c644a895fb5d2962ed76077770ea39af21de81482bb275d02510747f876e" ] || { echo "start blend SHA mismatch"; exit 1; }
$B -b --factory-startup --python tools/dump_mesh.py -- start/F1_STAGED.blend data/F1
python3 tools/variants.py                         # data/var_A_asbuilt.npz (F1 as built, assembled vertex order)  [needs data/b17_state.npz, work_assembled_vmap.json copied from F1]
$B -b --factory-startup --python tools/ul.py -- start/F1_STAGED.blend renders/f1pl "front,left,right,q3L,q3R" F1

# 1. the build: analytic chin/jaw rebuild (tools/geo2.py Head2) -> vertices slid along their own normals onto the new surface (tools/exp.py mesh_normal_delta)
python3 tools/make_final.py                        # -> data/var_final.npz, data/final_params.json
$B -b --factory-startup --python tools/assemble2.py -- start/F1_STAGED.blend data/var_final.npz export/HeroBase_Female_MicroF2_head_STAGED.blend export/assemble_report.json

# 2. gates
$B -b --factory-startup --python tools/dump_full.py -- export/HeroBase_Female_MicroF2_head_STAGED.blend data/dump/F2
$B -b --factory-startup --python tools/dump_full.py -- start/F1_STAGED.blend data/dump/F1
python3 tools/verify_f2.py | tee logs/verify_f2.txt                                   # topology / groups / tris / manifold / below-neck / zone / loops / folds vs F1
cp export/HeroBase_Female_MicroF2_head_STAGED.blend export/work_final.blend; cp data/trials/work_final_vmap.json export/work_final_vmap.json 2>/dev/null || cp data/work_assembled_vmap.json export/work_final_vmap.json
$B -b --factory-startup --python tools/verify_asm.py -- export/work_final.blend data/verify_asm_F2.json | tee logs/verify_asm_vs_ArtDir_start.txt   # body below the neck vs the ArtDir start blend
rm -f export/work_final.blend export/work_final_vmap.json
for N in F1:start/F1_STAGED.blend F2:export/HeroBase_Female_MicroF2_head_STAGED.blend; do T=${N%%:*}; BL=${N#*:}
  $B -b --factory-startup --python tools/sil_body.py -- $BL data/sil_body_$T.json proof/sil_$T | tee logs/sil_body_$T.txt
  $B -b --factory-startup --python tools/loops_audit.py -- $BL data/loops_audit_$T.json | grep -vE "^$|Blender|Read blend|quit|build date" > logs/loops_audit_$T.txt
done

# 3. export + proofs
$B -b --factory-startup --python tools/export_fbx.py -- export/HeroBase_Female_MicroF2_head_STAGED.blend export/HeroBase_Female_Body.fbx export/export_report.json
$BP tools/proof02.py export/HeroBase_Female_MicroF2_head_STAGED.blend proof/02_match_f_head_F2.png     # 16-crop plate | mesh | overlay sheet
python3 tools/make_proofs.py
python3 tools/lowiou.py F1=renders/f1pl:F1 F2=renders/final:F2
shasum -a 256 export/HeroBase_Female_MicroF2_head_STAGED.blend export/HeroBase_Female_Body.fbx ../../ArtDir/hero/base_lock/blender/HeroBase_Female.blend
