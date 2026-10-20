#!/bin/bash
# usage: look.sh <tag> : Face_M rebuilt blend + unity-like plate-framed views + gestalt sheets (front|q3L|q3R|left) and face close-ups
set -e
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i
export PYTHONPATH=$PWD/pylib
B=/Applications/Blender.app/Contents/MacOS/Blender
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
TAG=$1
$B -b --factory-startup --python apply_preview.py -- data/V_$TAG.npy final/$TAG.blend 1 2>&1 | grep -E "Error|Traceback" || true
$B -b --factory-startup --python unity_like.py -- final/$TAG.blend r/$TAG/ul plate_front,plate_q3L,plate_q3R,plate_left,face_front,face_threequarter,face_profile,head_front,head_threequarter,ear_side,eye_front 900 2>&1 | grep -E "Error|Traceback" || true
$PY gestalt.py r/$TAG/ul r/$TAG/ul/gestalt_a.png front,q3L
$PY gestalt.py r/$TAG/ul r/$TAG/ul/gestalt_b.png q3R,left
$PY - <<PYEOF
from PIL import Image
names = ['face_front', 'face_threequarter', 'face_profile']
ims = [Image.open('r/$TAG/ul/%s.png' % n).convert('RGB').resize((600, 600), Image.LANCZOS) for n in names]
sheet = Image.new('RGB', (1800, 600))
for i, im in enumerate(ims): sheet.paste(im, (i * 600, 0))
sheet.save('r/$TAG/ul/sheet.png')
PYEOF
echo "look $TAG done"
