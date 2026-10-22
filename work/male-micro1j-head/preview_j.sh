#!/bin/bash
# usage: preview_j.sh <tag> [views]   (needs data/V_<tag>.npy + N_<tag>.npy) -> final/<tag>.blend + r/ul_<tag>/*.png + r/cmp_<tag>_neck.png (start over variant)
set -e
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1j-head
cd $W; mkdir -p final
export PYTHONPATH=$W/pylib
B=/Applications/Blender.app/Contents/MacOS/Blender
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
TAG=$1; VIEWS=${2:-neck_side,neck_back,neck_qback,neck_front,neck_q,neck_q_lo,jaw_side,jaw_q}
$B -b --factory-startup --python apply_j.py -- data/V_$TAG.npy data/N_$TAG.npy final/$TAG.blend 2>&1 | grep -E "Error|Traceback" || true
$B -b --factory-startup --python unity_like_j.py -- final/$TAG.blend r/ul_$TAG $VIEWS 760 2>&1 | grep -E "Error|Traceback" || true
$PY - <<PYEOF
from PIL import Image, ImageDraw
names = '$VIEWS'.split(',')
rows = []
for d, lab in (('r/ul_start', 'START'), ('r/ul_$TAG', '$TAG')):
    ims = [Image.open('%s/%s.png' % (d, n)).convert('RGB').resize((500, 500), Image.LANCZOS) for n in names]
    row = Image.new('RGB', (500 * len(ims), 500))
    for i, im in enumerate(ims): ImageDraw.Draw(im).text((6, 4), lab + ' ' + names[i], fill=(255, 255, 0)); row.paste(im, (i * 500, 0))
    rows.append(row)
sheet = Image.new('RGB', (rows[0].width, 1000)); sheet.paste(rows[0], (0, 0)); sheet.paste(rows[1], (0, 500))
sheet.save('r/cmp_$TAG.png'); print(sheet.size)
PYEOF
echo "preview $TAG done"
