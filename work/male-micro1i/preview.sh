#!/bin/bash
# usage: preview.sh <tag> [facem=0|1]   (needs data/V_<tag>.npy) -> final/<tag>.blend + r/<tag>/{panels,clay,nrm,photo}
set -e
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i
export PYTHONPATH=$PWD/pylib
B=/Applications/Blender.app/Contents/MacOS/Blender
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
TAG=$1; FM=${2:-1}
$B -b --factory-startup --python apply_preview.py -- data/V_$TAG.npy final/$TAG.blend $FM 2>&1 | grep -E "saved|Error|Traceback" || true
$B -b --factory-startup --python ../male-micro1h/render_panels.py -- final/$TAG.blend r/$TAG/panels 2>&1 | grep -E "Error|Traceback" || true
$B -b --factory-startup --python clay_views.py -- final/$TAG.blend r/$TAG/clay 2>&1 | grep -E "Error|Traceback" || true
$B -b --factory-startup --python normals_render.py -- final/$TAG.blend r/$TAG/nrm 2>&1 | grep -E "Error|Traceback" || true
$B -b --factory-startup --python photo.py -- r/$TAG/nrm r/$TAG/photo 2>&1 | grep -E "light|Error|Traceback" || true
$PY - <<PYEOF
from PIL import Image
names = ['f', 'q41', 'q41_lo', 'prof', 'f_lo', 'q41_hi', 'q60', 'f_hi']
ims = [Image.open('r/$TAG/clay/%s.png' % n).convert('RGB') for n in names]
W, H = ims[0].size
sheet = Image.new('RGB', (W * 4, H * 2))
for i, im in enumerate(ims): sheet.paste(im, ((i % 4) * W, (i // 4) * H))
sheet = sheet.resize((sheet.width * 2 // 3, sheet.height * 2 // 3), Image.LANCZOS); sheet.save('r/$TAG/clay/sheet.png')
PYEOF
echo "preview $TAG done"
