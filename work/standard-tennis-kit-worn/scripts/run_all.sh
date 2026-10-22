#!/bin/bash
# full reproducible run: parts -> assemble -> FBX -> checks -> proofs -> sheets
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/standard-tennis-kit-worn
B=/Applications/Blender.app/Contents/MacOS/Blender
echo "== parts"; scripts/build_parts.sh 2>&1 | cut -c1-200
echo "== assemble"; for g in male female; do $B -b --factory-startup --python scripts/assemble.py -- $g 2>&1 | grep -E "tris|saved|Error|Trace" | cut -c1-200; done
echo "== fbx"; $B -b --factory-startup --python scripts/export_fbx.py 2>&1 | grep -E "^StdKit|Error|Trace"
echo "== checks"; for g in male female; do $B -b --factory-startup --python scripts/checks.py -- $g 2>&1 | grep -E "Error|Trace|File \"" ; done
echo "== proofs"; rm -f proof/raw/*.png; scripts/run_proofs.sh
echo "== sheets"; python3 scripts/compose_proofs.py 2>&1 | tail -2
echo ALL_DONE
