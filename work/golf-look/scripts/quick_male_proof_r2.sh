#!/bin/bash
set -euo pipefail
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
B=/Applications/Blender.app/Contents/MacOS/Blender
W=work/golf-look
"$B" -b "$W/export/Golf_Male_Draft.blend" --python "$W/scripts/retarget_proof.py" -- Male > "$W/logs/retarget_crotch_r2_Male.log" 2>&1
"$B" -b "$W/export/Golf_Male_SwingProof.blend" --python "$W/scripts/render_draft.py" -- male "$W/proof/crotch_r2_Male.json" > "$W/logs/render_crotch_r2_Male.log" 2>&1
"$B" -b "$W/export/Golf_Male_SwingProof.blend" --python "$W/scripts/trace_pose_pixel.py" > "$W/logs/pose_pixel_trace_crotch_r2.log" 2>&1
"$B" -b --python "$W/scripts/verify_identity.py" > "$W/logs/identity_crotch_r2.log" 2>&1
