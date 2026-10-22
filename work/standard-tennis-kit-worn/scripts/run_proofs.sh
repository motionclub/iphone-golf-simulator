#!/bin/bash
# all proof renders (raw cells -> proof/raw), sequential; then compose_proofs.py builds the sheets
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/standard-tennis-kit-worn
B=/Applications/Blender.app/Contents/MacOS/Blender
for g in male female; do
  for m in onbody waist exploded ids sections clearance; do
    $B -b --factory-startup --python scripts/render_proofs.py -- $g $m 2>&1 | grep -E "done|Error|Trace|File \"|KeyError" | sed "s/^/[$g $m] /"
  done
done
for m in hem liner_mask; do
  $B -b --factory-startup --python scripts/render_proofs.py -- female $m 2>&1 | grep -E "done|Error|Trace|File \"|KeyError" | sed "s/^/[female $m] /"
done
echo ALL_PROOF_RENDERS_DONE
