#!/bin/zsh
# usage: rr.sh tag  -> builds blend from out.npy, renders sheet
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-arms-form2
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b start/start_torso_plus_limbs.blend --python apply_blend.py -- out.npy iter_$1.blend >/dev/null 2>&1
for v in front side q3F back q3B; do :; done
$B -b iter_$1.blend --python render_views.py -- proof/it_$1 1.1 0.95 studio front,side,q3F,back 700x900 >/dev/null 2>&1
