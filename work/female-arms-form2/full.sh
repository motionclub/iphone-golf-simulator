#!/bin/zsh
# full.sh tag : build, apply, metrics renders + sheet
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-arms-form2
B=/Applications/Blender.app/Contents/MacOS/Blender
python3 arm_model.py out.npy || exit 1
$B -b start/start_torso_plus_limbs.blend --python apply_blend.py -- out.npy iter_$1.blend >/dev/null 2>&1
$B -b iter_$1.blend --python rend_plate.py -- proof/m1_$1 1 >/dev/null 2>&1
python3 armmetrics.py proof/m1_$1 | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['front_arms_xor_pct'],d['back_arms_xor_pct'],d['consensus_mean_fb']['ratio'],d['outer_edge_dev_mm'])"
$B -b iter_$1.blend --python rend_plate.py -- proof/pl_$1 3 >/dev/null 2>&1; python3 cmp_sheet.py proof/pl_$1 proof/cmp_$1.png
