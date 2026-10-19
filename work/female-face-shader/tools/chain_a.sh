#!/bin/zsh
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-face-shader
tools/review_state.sh sh6_rig export/Female_s4.fbx unity rig | tail -1
tools/review_state.sh f0b_tones unity/before/Female.fbx unity/before tones | tail -1
tools/review_state.sh before unity/before/Female.fbx unity/before perf | tail -1
tools/review_state.sh after export/Female_s4.fbx unity perf | tail -1
echo CHAIN_A_DONE
