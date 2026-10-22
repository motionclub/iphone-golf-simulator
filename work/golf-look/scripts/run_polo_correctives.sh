#!/bin/bash
set -euo pipefail
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
B=/Applications/Blender.app/Contents/MacOS/Blender
W=work/golf-look
for sex in Male Female; do
 "$B" -b "$W/export/Golf_${sex}_Draft.blend" --python "$W/scripts/repair_polo_shell.py" -- "$sex" > "$W/logs/polo_lineage_final_${sex}.log" 2>&1
 "$B" -b "$W/export/Golf_${sex}_Draft.blend" --python "$W/scripts/retarget_proof.py" -- "$sex" > "$W/logs/retarget_lineage_final_${sex}.log" 2>&1
 "$B" -b "$W/export/Golf_${sex}_SwingProof.blend" --python "$W/scripts/build_polo_correctives.py" -- "$sex" > "$W/logs/build_polo_correctives_${sex}.log" 2>&1
done
