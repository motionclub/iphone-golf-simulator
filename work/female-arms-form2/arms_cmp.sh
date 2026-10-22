#!/bin/zsh
# arms_cmp.sh tag... : arm close-ups, rows=tags, cols=front,q3F,side,q3B,back
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-arms-form2
B=/Applications/Blender.app/Contents/MacOS/Blender
for t in "$@"; do
  f=iter_$t.blend; [ $t = base ] && f=start/start_torso_plus_limbs.blend
  $B -b $f --python render_views.py -- proof/ac_$t 1.07 0.66 clay_studio.exr front,q3F,side,q3B,back 400x520 0.16 >/dev/null 2>&1
done
python3 - "$@" <<'PY'
import sys
from PIL import Image
tags=sys.argv[1:]
s=Image.new('RGB',(400*5,520*len(tags)),'white')
for r,t in enumerate(tags):
    for k,v in enumerate(('front','q3F','side','q3B','back')):
        s.paste(Image.open(f'proof/ac_{t}_{v}.png').convert('RGB'),(k*400,r*520))
s.save('proof/arms_cmp.png')
PY
