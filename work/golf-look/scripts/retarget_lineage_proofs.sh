#!/bin/bash
set -euo pipefail
R="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
cd "$R"
B="/Applications/Blender.app/Contents/MacOS/Blender"
W="work/golf-look"
for sex in Female Male; do
 "$B" -b "$W/export/Golf_${sex}_Draft.blend" --python "$W/scripts/retarget_proof.py" -- "$sex" > "$W/logs/retarget_lineage_${sex}.log" 2>&1
 "$B" -b "$W/export/Golf_${sex}_SwingProof.blend" --python "$W/scripts/measure_swing_draft.py" -- "$sex" > "$W/logs/deform_lineage_${sex}.log" 2>&1
 "$B" -b "$W/export/Golf_${sex}_SwingProof.blend" --python "$W/scripts/render_draft.py" -- "$(echo "$sex" | tr '[:upper:]' '[:lower:]')" "$W/proof/resume_fit2_${sex}.json" > "$W/logs/render_lineage_${sex}.log" 2>&1
done
"$B" -b --python "$W/scripts/verify_identity.py" > "$W/logs/identity_lineage.log" 2>&1
