#!/bin/bash
# usage: render_graze.sh <tag...> : grazing-light pelvis views (rear, rear 3/4 x2, front) -> tmp/graze_<tags>.png
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-nape-pelvis-skin
export PYTHONPATH=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib
for t in "$@"; do
  SRC=data/V_$t.npy; [ $t = start ] && SRC=baseline/HeroBase_Male_Silhouette.blend
  GRAZE="-1,1.0,0.7" /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python rig.py -- $SRC r/${t}_gp 'yaw180_0.34_0.82_0_700_700_-5,yaw150_0.34_0.82_0_700_700_-20,yaw210_0.34_0.82_0_700_700_-20,yaw0_0.34_0.82_0_700_700_-15' clay 2>&1 | grep -E "Error|Traceback|bad"
done
unset PYTHONPATH
python3 - "$@" <<'PY'
import sys
from PIL import Image, ImageDraw
tags=sys.argv[1:]; n=['yaw180_0.34_0.82_0_700_700_-5','yaw150_0.34_0.82_0_700_700_-20','yaw210_0.34_0.82_0_700_700_-20','yaw0_0.34_0.82_0_700_700_-15']; Z=360
S=Image.new('RGB',(4*Z,len(tags)*Z+len(tags)*0),(20,20,20)); d=ImageDraw.Draw(S)
for j,t in enumerate(tags):
    for i,k in enumerate(n):
        S.paste(Image.open(f'r/{t}_gp/{k}.png').resize((Z,Z)),(i*Z,j*Z)); d.text((i*Z+4,j*Z+4),t+' '+k[:6],fill=(255,200,80))
S.save('tmp/graze_'+'_'.join(tags)+'.png'); print('tmp/graze_'+'_'.join(tags)+'.png',S.size)
PY
