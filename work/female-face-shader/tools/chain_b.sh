#!/bin/zsh
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-face-shader
tools/review_state.sh final export/Female_s5.fbx unity views | tail -1
tools/review_state.sh final_rig export/Female_s5.fbx unity rig | tail -1
tools/native.sh final 2>&1 | tail -8
echo CHAIN_B_DONE
