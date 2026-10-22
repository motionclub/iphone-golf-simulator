#!/bin/zsh
# DRESSED_LOOK end to end (~15 min on the M5): sources + art-directory snapshots -> build both dressed blends -> evidence -> proofs -> gates.
# Everything is written under work/dressed-look/ only.
set -e
setopt null_glob          # zsh: an unmatched glob (no .blend1 files) must not abort the run
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/dressed-look
BL=/Applications/Blender.app/Contents/MacOS/Blender
S=$W/scripts
cd $W
# baselines are taken ONCE, before any work (a re-run must not replace them)
[ -f data/sources_before.json ] || python3 $S/verify_sources.py data/sources_before.json     # SHA-256 of the five source blends vs the brief
[ -f data/artdir_before.json ] || python3 $S/artdir_snapshot.py data/artdir_before.json     # read-only stat manifest + base_lock SHA-256
rm -f export/*.blend export/*.blend1
for t in male female; do $BL -b --factory-startup --python $S/build_dressed.py -- $t; done
for t in male female; do
  $BL -b --factory-startup --python $S/verify_dressed.py -- $t      # BODIES / KIT_SEPARATE / NO_REFIT / BOTH_COLORS / RACKET_IN_HAND evidence
  $BL -b --factory-startup --python $S/measure_fit.py -- $t         # CLIP / FLOAT measurement
done
$S/run_cells.sh                                                    # 32 proof cells (4 sheets x 8)
$S/run_turntables.sh                                               # 2 x 240-frame H.264 turntables (white kit)
python3 $S/compose_sheets.py                                       # 4 sheets
$BL -b --factory-startup --python $S/check_video.py -- data/video_check.json proof/Turntable_Male_White.mp4 proof/Turntable_Female_White.mp4
python3 $S/verify_sources.py data/sources_after.json
python3 $S/artdir_snapshot.py data/artdir_after.json
python3 $S/final_report.py                                         # gates -> checks.json + GATE_RESULTS.md
