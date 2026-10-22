#!/bin/zsh
# shoulder_cmp.sh tag... : close-up shading sheet (rows=tags)
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-arms-form2
B=/Applications/Blender.app/Contents/MacOS/Blender
rows=()
for t in "$@"; do
  f=iter_$t.blend; [ $t = base ] && f=start/start_torso_plus_limbs.blend
  $B -b $f --python render_views.py -- proof/sh_$t 1.2 0.50 clay_studio.exr front,q3F,side,q3B,back 450x450 0.17 >/dev/null 2>&1
done
python3 - "$@" <<'PY'
import sys
from PIL import Image
tags=sys.argv[1:]
s=Image.new('RGB',(450*5,450*len(tags)),'white')
for r,t in enumerate(tags):
    for k,v in enumerate(('front','q3F','side','q3B','back')):
        s.paste(Image.open(f'proof/sh_{t}_{v}.png').convert('RGB'),(k*450,r*450))
s.save('proof/sh_cmp.png')
PY
