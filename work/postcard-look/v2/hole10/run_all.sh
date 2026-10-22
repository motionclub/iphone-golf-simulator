#!/bin/bash
# hole 10 Crater: the whole staged rebuild + every gate (Blender headless only, no Unity). Writes only under work/postcard-look/v2/hole10/ (stage/, stage_repro/, logs/, previews/, GATES_hole10.txt).
#   work/postcard-look/v2/hole10/run_all.sh        (about 60 s)
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
S=$R/work/postcard-look/v2/hole10
bash $S/tools/run_all.sh | tee $S/logs/run_all_output.txt
python3 $S/tools/summarize.py | tail -3
